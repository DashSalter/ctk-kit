"""懒加载滚动列表。

为什么不用 ``CTkScrollableFrame`` 直接塞卡片：上百张卡片时，一次建完要几秒，
切页面会明显卡住。这里的分批策略是——

1. 首屏只建 ``first_batch`` 张，先把页面显示出来；
2. 滚到接近底部、且手停下来 ``load_delay_ms`` 之后，再补 ``load_more`` 张；
3. 首屏没铺满窗口时自动补，直到铺满或补完。

滚动条的两个坑（都踩过）：

- ``CTkScrollbar.set()`` 内部会调 ``update_idletasks()``，而它**会立刻执行
  idle 回调**——所以加载任务必须用 ``after(1, ...)`` 定时器，不能用
  ``after_idle``，否则会在 ``set()`` 里递归建卡。
- scrollregion 变化后 Tk 会回放一次 ``yscrollcommand(0, 1)``，用回调参数判断
  「滚到底」会误判，必须读 ``canvas.yview()`` 的真实值。

滚动条外观：内容不足一屏时把滑块涂成背景色（视觉上消失，但**布局宽度不变**）。
不要用 ``grid_remove`` 隐藏——canvas 会变宽，卡片跟着拉伸一下，看起来像抖。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional

import customtkinter as ctk

from . import tokens as T
from .layout import empty_hint
from .theme import color_of, repaint_native

# ``render_card(parent, item)``：建一张卡片并返回其顶层控件。
RenderCard = Callable[[tk.Misc, Any], tk.Misc]
# ``key_of(item) -> 可哈希的签名``：用于判断数据是否变化。
KeyOf = Callable[[Any], Any]


class LazyList(tk.Frame):
    """竖向懒加载列表。

    参数:
        master: 父容器。
        render_card: 回调 ``render_card(parent, item) -> widget``，返回一张卡片
            的顶层控件。卡片自己要负责外观，这里只负责把它 ``pack`` 进列表。
        key_of: ``key_of(item) -> tuple``，用于判断数据是否变化。默认取
            ``repr``；数据量大时建议换成
            ``lambda item: (item["id"], item["updated_at"])``。
        first_batch: 首屏一次建多少张，默认 12。
        load_more: 每次追加多少张，默认 8。
        load_delay_ms: 滚到底后等多久再追加（毫秒），默认 90——让手停下来。
        load_threshold: 可滚动区滚到多少比例触发追加，默认 0.92。
        gap: 卡片上下的外边距，默认 ``(0, 10)``。
        padx: 卡片左右留白（给滚动条让位），默认 ``(0, 8)``。
    """

    def __init__(
        self,
        master: tk.Misc,
        render_card: RenderCard,
        *,
        key_of: Optional[KeyOf] = None,
        first_batch: int = 12,
        load_more: int = 8,
        load_delay_ms: int = 90,
        load_threshold: float = 0.92,
        gap: tuple[int, int] = (0, 10),
        padx: tuple[int, int] = (0, 8),
    ) -> None:
        super().__init__(master, bg=color_of(T.COLOR_BG), highlightthickness=0)
        self.render_card: RenderCard = render_card
        self.key_of: KeyOf = key_of or repr
        self.first_batch: int = first_batch
        self.load_more: int = load_more
        self.load_delay_ms: int = load_delay_ms
        self.load_threshold: float = load_threshold
        self.gap: tuple[int, int] = gap
        self.padx: tuple[int, int] = padx

        self._items: list[Any] = []
        self._shown: int = 0
        self._loading: bool = False
        self._load_job: Optional[str] = None
        self._suppress: bool = False
        self._signature: Optional[tuple] = None
        self._empty_box: Optional[tk.Frame] = None
        self._scrollbar_visible: Optional[bool] = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas: tk.Canvas = tk.Canvas(
            self, highlightthickness=0, bg=color_of(T.COLOR_BG), bd=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar: ctk.CTkScrollbar = ctk.CTkScrollbar(
            self,
            command=self.canvas.yview,
            width=T.SCROLLBAR_WIDTH,
            fg_color="transparent",
            button_color=T.COLOR_SCROLLBAR,
            button_hover_color=T.COLOR_SCROLLBAR_HOVER,
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self._on_scroll)

        self.inner: tk.Frame = tk.Frame(self.canvas, bg=color_of(T.COLOR_BG))
        self._window: int = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw"
        )

        self.inner.bind("<Configure>", self._sync_scrollregion)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # 滚轮：控件在 canvas 里是独立窗口，事件不会冒泡到父容器，
        # 所以统一在 toplevel 上挂一个，按指针位置判断该不该由自己滚动。
        self._alive: bool = True
        self.bind_all("<MouseWheel>", self._on_wheel, add="+")

    # ------------------------------------------------------------------ #
    #  对外接口
    def render(
        self,
        items: list[Any],
        *,
        empty_title: str = "这里还没有内容",
        empty_detail: str = "",
        force: bool = False,
    ) -> None:
        """重画列表。数据没变时直接返回，避免每次切页都重建控件。

        参数:
            items: 数据列表，原样交给 ``render_card``。
            empty_title: 列表为空时的主提示。
            empty_detail: 列表为空时的补充说明。
            force: 为 ``True`` 时忽略签名缓存，强制重建。
        """
        signature = (ctk.get_appearance_mode(), tuple(self.key_of(i) for i in items))
        if not force and signature == self._signature:
            return
        self._signature = signature
        self._items = list(items)
        self._shown = 0
        self._suppress = True
        self._refresh_colors()
        self._clear_cards()

        if not items:
            self._suppress = False
            box = empty_hint(self.inner, empty_title, empty_detail)
            box.pack(pady=70)
            self._empty_box = box
            return

        self._append(self.first_batch)
        self._suppress = False
        # 滚动条位置留到下一帧再算：set() 会同步布局，放在这里会拖慢首帧
        self.after(1, self._refresh_scroll)

    def show_hint(self, title: str, detail: str = "") -> None:
        """只显示一条提示（例如「还没有备份」），不占列表数据。

        参数:
            title: 主提示。
            detail: 补充说明，可为空。
        """
        signature = ("hint", ctk.get_appearance_mode(), title)
        if signature == self._signature:
            return
        self._signature = signature
        self._items = []
        self._shown = 0
        self._suppress = True
        self._refresh_colors()
        self._clear_cards()
        self._empty_box = empty_hint(self.inner, title, detail)
        self._empty_box.pack(pady=70)
        self.canvas.yview_moveto(0)
        self._suppress = False

    def invalidate(self) -> None:
        """丢掉缓存标记，下次 render 一定重建（主题切换后调用）。"""
        self._signature = None

    @property
    def cards(self) -> list[tk.Misc]:
        """当前已建出的卡片控件（副本，改动它不会影响列表）。"""
        return list(self.inner.winfo_children())

    def flush(self) -> None:
        """一次性补齐所有卡片（测试、导出时用）。"""
        self._cancel_load()
        self._append(len(self._items) - self._shown)

    def scroll_units(self, steps: int) -> None:
        """按「行」滚动；steps>0 向下，steps<0 向上。

        一格滚轮固定滚 60px（约 0.75 张卡片），比 tk 默认的 3px 顺手。
        """
        self.canvas.yview_scroll(steps * 60, "units")

    def _on_wheel(self, event: tk.Event) -> Optional[str]:
        """只滚动指针所在的列表；其它区域的滚轮不归这里管。"""
        if not self._alive or not self._owns(event.widget):
            return None
        self.scroll_units(-1 if event.delta > 0 else 1)
        return "break"

    def _owns(self, widget: Optional[tk.Misc]) -> bool:
        """``widget`` 是否在本列表的控件树里。"""
        node: Optional[tk.Misc] = widget
        while node is not None:
            if node is self:
                return True
            node = getattr(node, "master", None)
        return False

    def destroy(self) -> None:
        """停止滚轮绑定后销毁。"""
        self._alive = False
        super().destroy()

    # ------------------------------------------------------------------ #
    #  内部
    def _append(self, count: int) -> None:
        """从 ``_shown`` 处继续建 ``count`` 张卡。"""
        end = min(self._shown + count, len(self._items))
        if end <= self._shown:
            return
        # 建卡期间暂停滚动回调：每加一张都会触发 scrollregion 变化，而
        # CTkScrollbar 每次 set 都要整条重绘（实测是布局耗时的大头）。
        self._loading = True
        self.canvas.configure(yscrollcommand="")
        for item in self._items[self._shown : end]:
            card = self.render_card(self.inner, item)
            card.pack(fill="x", pady=self.gap, padx=self.padx)
        self._shown = end
        self._sync_scrollregion()
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.after(1, self._refresh_scroll)

    def _refresh_scroll(self) -> None:
        """同步滚动条位置，并在空闲后检查要不要补卡。"""
        first, last = self.canvas.yview()
        self.scrollbar.set(first, last)
        self._sync_scrollbar()
        self._loading = False
        self.after(150, self._check_fill)

    def _sync_scrollbar(self) -> None:
        """内容装得下时把滑块涂成背景色（布局宽度不变）。"""
        box = self.canvas.bbox("all")
        content = (box[3] - box[1]) if box else 0
        visible = content > self.canvas.winfo_height() + 1
        if visible == self._scrollbar_visible:
            return
        self._scrollbar_visible = visible
        bg = color_of(T.COLOR_BG)
        self.scrollbar.configure(
            fg_color=bg,
            button_color=color_of(T.COLOR_SCROLLBAR) if visible else bg,
            button_hover_color=color_of(T.COLOR_SCROLLBAR_HOVER) if visible else bg,
        )

    def _check_fill(self) -> None:
        """窗口较高、首屏没铺满时补一批。

        放在定时器里：Tk 要跑完一次事件循环才会更新内层 Frame 的尺寸，
        这时 bbox 才是准的。
        """
        if self._shown >= len(self._items):
            return
        box = self.canvas.bbox("all")
        content = (box[3] - box[1]) if box else 0
        # 差得多才补：多建一批要重新布局整页，代价比底部一小条空白高得多
        if content > self.canvas.winfo_height() * 0.8:
            return
        self._append(self.load_more)

    def _load_more(self) -> None:
        """定时器回调：追加下一批。"""
        self._load_job = None
        self._append(self.load_more)

    def _on_scroll(self, first: str, last: str) -> None:
        """canvas 的 yscrollcommand 回调。"""
        if self._suppress:
            return
        self.scrollbar.set(first, last)
        if self._loading or self._shown >= len(self._items):
            return
        # 不信回调参数：scrollregion 刚变时会回放一次 (0, 1)
        current = self.canvas.yview()
        if float(current[1]) < self.load_threshold:
            return
        self._schedule_load()

    def _schedule_load(self) -> None:
        """滚到底后等手停下再补下一批，避免边滚边排版造成顿挫。"""
        if self._load_job is not None:
            self.after_cancel(self._load_job)
        self._load_job = self.after(self.load_delay_ms, self._load_more)

    def _cancel_load(self) -> None:
        """取消还没触发的追加任务。"""
        if self._load_job is not None:
            self.after_cancel(self._load_job)
            self._load_job = None

    def _clear_cards(self) -> None:
        """清空内层卡片并复位滚动位置。"""
        self._loading = False
        self._cancel_load()
        for child in self.inner.winfo_children():
            child.destroy()
        self._empty_box = None
        self.canvas.yview_moveto(0)
        self._sync_scrollregion()

    def _refresh_colors(self) -> None:
        """主题切换后刷新原生 tk 控件的底色（见 theme.repaint_native）。"""
        bg = color_of(T.COLOR_BG)
        for widget in (self, self.canvas, self.inner):
            repaint_native(widget, bg)
        self._scrollbar_visible = None
        self._sync_scrollbar()

    def _sync_scrollregion(self, _event: Optional[tk.Event] = None) -> None:
        """把 canvas 的可滚动区域更新为内容包围盒。"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event: tk.Event) -> None:
        """canvas 宽度变化时让内层 Frame 跟着变宽。"""
        self.canvas.itemconfigure(self._window, width=event.width)
        self.after(1, self._sync_scrollbar)
