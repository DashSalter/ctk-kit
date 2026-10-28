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
        item_height: 固定卡片高度（含 ``gap``）。给定时开启虚拟滚动：只把
            视口附近的卡片放上布局，滚出视口的卡片保留在内存里复用，滚回来
            直接重新放上去，不销毁、不重建。适合几千条数据的列表；要求
            ``render_card`` 返回的卡片高度固定（例如自己 ``pack_propagate(False)``
            并设置 ``height``），否则卡片会互相叠压。
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
        item_height: Optional[int] = None,
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
        #: 固定卡片高度（含间距）。给定时开启虚拟滚动：只把视口附近的卡片
        #: 放上布局，滚过去的卡片留在内存里复用，不销毁，回滚时直接放回来。
        self.item_height: Optional[int] = item_height

        self._items: list[Any] = []
        self._shown: int = 0
        self._loading: bool = False
        self._load_job: Optional[str] = None
        self._suppress: bool = False
        self._signature: Optional[tuple] = None
        self._empty_box: Optional[tk.Frame] = None
        self._scrollbar_visible: Optional[bool] = None
        #: 虚拟模式：索引 -> 已建卡片（卡片不销毁，只在视口外 place_forget）。
        self._built: dict[int, tk.Misc] = {}
        self._range: Optional[tuple[int, int]] = None
        self._resize_job: Optional[str] = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas: tk.Canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bg=color_of(T.COLOR_BG),
            bd=0,
            # 1 单位 = 1px，滚轮按 units 滚时才有确定步长（默认 0 时 1 单位≈视口 1/10）
            yscrollincrement=1,
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

        if self.item_height is not None:
            self._layout_virtual()
            self._suppress = False
            self.after(1, self._refresh_scroll)
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
        """当前已建出的卡片控件（副本，改动它不会影响列表）。

        虚拟模式下返回所有建过的卡片（含视口外未布局的），按索引排序。
        """
        if self.item_height is not None:
            return [self._built[index] for index in sorted(self._built)]
        return list(self.inner.winfo_children())

    def flush(self) -> None:
        """一次性补齐所有卡片（测试、导出时用）。

        虚拟模式下只建卡、不改变视口，所以耗时也只和卡片总数有关。
        """
        if self.item_height is not None:
            for index in range(len(self._items)):
                self._ensure_card(index)
            self._sync_window(force=True)
            return
        self._cancel_load()
        self._append(len(self._items) - self._shown)

    def reset(self) -> None:
        """回到首屏：只保留 ``first_batch`` 张卡并把滚动位置归零。

        适合页面被隐藏时调用。已展开几百张卡时，控件数量会让重新显示
        或窗口缩放明显变慢；缩回首屏后重排成本就回到常数级。

        虚拟模式下卡片本来就只布局视口附近，所以这里只把滚动位置归零，
        已建卡片全部保留复用，不会重建。
        """
        if not self._items:
            return
        if self.item_height is not None:
            self.canvas.yview_moveto(0)
            self._sync_window(force=True)
            return
        self._signature = None
        self.render(self._items, force=True)

    def scroll_units(self, steps: int) -> None:
        """按「行」滚动；steps>0 向下，steps<0 向上。

        一格滚轮固定滚 60px（约 0.75 张卡片），比 tk 默认的 3px 顺手。
        canvas 构造时把 ``yscrollincrement`` 定成 1，所以 1 个单位就是 1px；
        否则默认值 0 会让 1 个单位约等于视口的十分之一，滚一下直接跳半页。
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
        self._cancel_resize()
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
        if self.item_height is not None:
            content = len(self._items) * self.item_height * self._card_scale()
        else:
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
        if self.item_height is not None:
            return
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
        if self.item_height is not None:
            self._sync_scrollbar()
            self._sync_window(float(first), float(last))
            return
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

    def _cancel_resize(self) -> None:
        """取消还没触发的窗口尺寸同步任务。"""
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
            self._resize_job = None

    def _clear_cards(self) -> None:
        """清空内层卡片并复位滚动位置。"""
        self._loading = False
        self._cancel_load()
        self._cancel_resize()
        self._built.clear()
        self._range = None
        for child in self.inner.winfo_children():
            child.destroy()
        if self.item_height is not None:
            self.inner.configure(height=0)
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
        if self.item_height is not None and self._items:
            # 虚拟模式的内容高度是算出来的，不依赖当前放上布局的卡片
            height = self.item_height * len(self._items) * self._card_scale()
            self.canvas.configure(
                scrollregion=(0, 0, self.canvas.winfo_width(), height)
            )
            return
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event: tk.Event) -> None:
        """canvas 宽度变化时让内层 Frame 跟着变宽。"""
        self.canvas.itemconfigure(self._window, width=event.width)
        if self.item_height is None:
            self.after(1, self._sync_scrollbar)
            return
        # 拖动窗口时 Configure 会连发很多次，合并成一次，避免反复排版
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(60, self._after_resize)

    def _after_resize(self) -> None:
        """窗口尺寸稳定后补一次滚动条与视口同步。"""
        self._resize_job = None
        self._sync_scrollbar()
        if self.item_height is not None:
            self._sync_window()

    # ------------------------------------------------------------------ #
    #  虚拟滚动
    def _card_scale(self) -> float:
        """卡片 place 时 CTk 会按窗口缩放放大坐标，这里取同一个系数。"""
        try:
            scale = float(ctk.ScalingTracker.get_widget_scaling(self))
        except Exception:
            scale = 1.0
        return scale if scale > 0 else 1.0

    def _layout_virtual(self) -> None:
        """按固定卡片高度把内层撑到总高，然后只铺视口附近的卡片。"""
        height = self.item_height or 0
        total = len(self._items) * height * self._card_scale()
        self.inner.configure(height=total)
        self.canvas.itemconfigure(self._window, width=self.canvas.winfo_width())
        self.canvas.configure(
            scrollregion=(0, 0, self.canvas.winfo_width(), total)
        )
        self._sync_window(force=True)

    def _ensure_card(self, index: int) -> tk.Misc:
        """按索引取卡：建过的直接复用，没建过的才调 ``render_card``。"""
        card = self._built.get(index)
        if card is None:
            card = self.render_card(self.inner, self._items[index])
            self._built[index] = card
        return card

    def _sync_window(
        self, first: Optional[float] = None, last: Optional[float] = None, force: bool = False
    ) -> None:
        """把视口附近的卡片放上布局，滚出视口的收起（保留对象不销毁）。

        ``first`` / ``last`` 由 yscrollcommand 回调直接给出；不传时读
        ``canvas.yview()``。滚动过程中回调参数比再读一次更接近真实位置。
        """
        height = self.item_height
        if height is None:
            return
        count = len(self._items)
        if count == 0:
            return
        # 内层是普通 tk.Frame，高度按物理像素算；卡片 place 的坐标是逻辑值，
        # CTk 会再乘一次缩放，所以总高要乘缩放系数，否则滚动位置会错位。
        scale = self._card_scale()
        total = count * height * scale
        step = height * scale
        if int(self.inner.cget("height")) != total:
            # 任何地方把内层改小时都拉回总高，否则滚动条比例会错
            self.inner.configure(height=total)
            self.canvas.configure(
                scrollregion=(0, 0, self.canvas.winfo_width(), total)
            )
        if first is None or last is None:
            current = self.canvas.yview()
            first, last = float(current[0]), float(current[1])
        # 缓冲几张，快速滚动或拖动滚动条时不会露出空白
        start = max(0, int(first * total // step) - 3)
        end = min(count, int(last * total // step) + 4)
        if not force and (start, end) == self._range:
            return
        self._range = (start, end)
        for index in range(start, end):
            card = self._ensure_card(index)
            # CTk 控件禁止在 place() 里传 width/height，卡片高度由
            # render_card 自己固定；这里只负责纵向定位和铺满宽度。
            card.place(x=self.padx[0], y=index * height + self.gap[0], relwidth=1)
        for index, card in list(self._built.items()):
            if index < start or index >= end:
                card.place_forget()
