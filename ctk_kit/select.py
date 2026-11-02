"""下拉选择的新样式：多选标签（``TagSelectField``）与层级树（``TreeSelectField``）。

两者共用 :class:`_PopupPanel`：无边框 ``CTkToplevel``、跟随窗口移动/缩放、
上下翻转、滚出可视区自动收起，这套面板行为与 ``dropdown.DropField`` 同源。
区别在面板内容——``DropField`` 是一行一个按钮，这里由子类自己铺行。
"""

from __future__ import annotations

import contextlib
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Optional, Sequence

import customtkinter as ctk

from . import tokens as T
from .inputs import CTkEntry
from .layout import style_scrollbar
from .theme import color_of

#: 面板最多铺几行，超出就在面板内部滚动。
_MAX_VISIBLE_ROWS = 8
#: 控件位置轮询间隔（毫秒）：页面滚动不会触发 <Configure>，只能主动看。
_FOLLOW_MS = 60
#: 窗口正在被拖动缩放时，面板保持不动，停手这么久之后再归位（秒）。
_RESIZE_QUIET = 0.30
#: 面板与输入框之间的间隙（逻辑像素）。
_PANEL_GAP = 2
#: 面板里每一行的高度（逻辑像素）。
_ROW_HEIGHT = 32
#: 已选中候选行的底色：只比卡片色亮一点点，选多了也不晃眼。
_SELECTED_ROW_BG = ("#eef8fa", "#1b262b")
#: 上面那行的悬停底色，比它稍亮一格。
_SELECTED_ROW_HOVER = ("#e2f1f5", "#223036")


class _PopupList(tk.Frame):
    """面板里的列表容器：内容超出时自己滚动。"""

    def __init__(self, master: tk.Misc, bg: str) -> None:
        """建列表：canvas 承载内容，内容超出时自己滚动。"""
        super().__init__(master, bg=bg, highlightthickness=0, bd=0)
        # 滚动条先建先 pack：pack 按调用顺序分配空间，倒过来放它会被 canvas 挤没
        self.scrollbar = style_scrollbar(
            ctk.CTkScrollbar(self, orientation="vertical", command=self._yview)
        )
        self.scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=2)
        self.scrollbar.pack_forget()

        self.canvas = tk.Canvas(
            self, bg=bg, highlightthickness=0, bd=0, yscrollcommand=self._on_scroll
        )
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollable = False

        self.inner.bind("<Configure>", self._sync_region)
        self.canvas.bind("<Configure>", self._sync_width)
        for widget in (self, self.canvas, self.inner):
            widget.bind("<MouseWheel>", self._on_wheel, add="+")

    def set_scrollable(self, flag: bool) -> None:
        """按需显示右侧滚动条；内容放得下时收起来。"""
        if flag == self.scrollable:
            return
        self.scrollable = flag
        if flag:
            self.scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=2)
        else:
            self.scrollbar.pack_forget()

    def _yview(self, *args: object) -> None:
        """滚动条拖动时驱动 canvas。"""
        self.canvas.yview(*args)

    def _on_scroll(self, first: str, last: str) -> None:
        """canvas 滚动时同步滚动条滑块位置。"""
        self.scrollbar.set(first, last)

    def bind_wheel(self, widget: tk.Misc) -> None:
        """行自己也要绑：鼠标停在行上时滚轮事件不会冒泡到 canvas。"""
        widget.bind("<MouseWheel>", self._on_wheel, add="+")

    def _sync_region(self, _event: Optional[tk.Event] = None) -> None:
        """内容尺寸变了，重算 canvas 的滚动区域。"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_width(self, event: tk.Event) -> None:
        """把内部内容框的宽度对齐到 canvas 宽度。"""
        self.canvas.itemconfigure(self._window, width=event.width)

    def _on_wheel(self, event: tk.Event) -> Optional[str]:
        """滚动候选列表；没有滚动空间时返回 ``None`` 让事件继续冒泡。"""
        if not self.scrollable:
            return None
        self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"


class _PopupPanel:
    """下拉面板的窗口与定位；行内容由 ``build`` 回调铺。

    ``build(parent)`` 在 ``parent`` 里铺好行并返回行数；行数会用来算面板高度。
    树形展开/收起后调用 :meth:`refresh` 重新铺行并重新定位。
    """

    def __init__(
        self,
        owner: tk.Misc,
        *,
        build: Callable[[tk.Misc], int],
    ) -> None:
        """记录宿主控件与铺行回调。"""
        self._owner = owner
        self._build = build
        self._rows = 0
        self._popup: Optional[ctk.CTkToplevel] = None
        self._listing: Optional[_PopupList] = None
        self._root_bind_id: Optional[str] = None
        self._focus_bind_id: Optional[str] = None
        self._resize_bind_id: Optional[str] = None
        self._follow_job: Optional[str] = None
        self._place_job: Optional[str] = None
        self._last_key: Optional[tuple] = None
        self._resize_quiet_until: float = 0.0
        self._last_root_size: tuple = ()

    @property
    def visible(self) -> bool:
        """面板当前是否正显示。"""
        return self._popup is not None and bool(self._popup.winfo_exists())

    # ------------------------------------------------------------ 打开/关闭
    def open(self) -> bool:
        """展开面板；已经在显示时先收起。返回是否真的弹出来了。"""
        if self.visible:
            self.close()
            return False

        popup = ctk.CTkToplevel(self._owner)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(fg_color=T.COLOR_BORDER)

        body = ctk.CTkFrame(
            popup,
            fg_color=T.COLOR_CARD,
            corner_radius=T.RADIUS_MEDIUM - 1,
            border_width=0,
        )
        body.pack(fill="both", expand=True, padx=1, pady=1)

        listing = _PopupList(body, color_of(T.COLOR_CARD))
        listing.pack(fill="both", expand=True, padx=5, pady=5)

        self._popup = popup
        self._listing = listing
        self._rows = max(0, int(self._build(listing.inner) or 0))
        self._last_key = None

        popup.update_idletasks()
        if not self._place_popup():
            self.close()
            return False
        popup.deiconify()
        popup.bind("<Escape>", self.close)
        # 鼠标进到面板上时再确认一次前台状态：切窗口的瞬间 FocusOut 可能没来
        popup.bind("<Enter>", self._on_popup_enter)
        _round_window_corners(self._owner, popup)

        self._root_bind_id = self._owner.winfo_toplevel().bind(
            "<Button-1>", self._maybe_close, add="+"
        )
        self._focus_bind_id = self._owner.winfo_toplevel().bind(
            "<FocusOut>", self._on_root_focus_out, add="+"
        )
        self._resize_bind_id = self._owner.winfo_toplevel().bind(
            "<Configure>", self._on_root_configure, add="+"
        )
        self._schedule_follow()
        return True

    def refresh(self) -> None:
        """重新铺行并重新定位：行数变了（展开/收起、增删选项）之后调用。"""
        if not self.visible or self._listing is None:
            return
        keep = self._listing.canvas.yview()
        for child in self._listing.inner.winfo_children():
            child.destroy()
        self._rows = max(0, int(self._build(self._listing.inner) or 0))
        if not self._place_popup():
            self.close()
            return
        if keep and keep[1] > keep[0]:
            self._listing.canvas.yview_moveto(keep[0])

    def sync_rows(self, count: int) -> None:
        """行数变了但内容已自己增删好：只重算面板高度与位置。

        和 :meth:`refresh` 的区别是不动已有的行，展开树形节点时用它，
        免得整块面板重建、看起来闪一下。
        """
        if not self.visible:
            return
        self._rows = max(0, int(count))
        if not self._place_popup():
            self.close()

    def close(self, _event: Optional[tk.Event] = None) -> None:
        """收起面板并清理绑定；重复调用安全。"""
        if self._root_bind_id is not None:
            with contextlib.suppress(Exception):
                self._owner.winfo_toplevel().unbind("<Button-1>", self._root_bind_id)
            self._root_bind_id = None
        if self._focus_bind_id is not None:
            with contextlib.suppress(Exception):
                self._owner.winfo_toplevel().unbind("<FocusOut>", self._focus_bind_id)
            self._focus_bind_id = None
        if self._resize_bind_id is not None:
            with contextlib.suppress(Exception):
                self._owner.winfo_toplevel().unbind("<Configure>", self._resize_bind_id)
            self._resize_bind_id = None
        if self._follow_job is not None:
            with contextlib.suppress(Exception):
                self._owner.after_cancel(self._follow_job)
            self._follow_job = None
        if self._place_job is not None:
            with contextlib.suppress(Exception):
                self._owner.after_cancel(self._place_job)
            self._place_job = None
        if self._popup is not None:
            with contextlib.suppress(Exception):
                if self._popup.winfo_exists():
                    self._popup.destroy()
            self._popup = None
        self._listing = None
        self._last_key = None

    # ------------------------------------------------------------ 定位
    def _anchor_key(self) -> tuple:
        """只要这些值没变，面板就不用重算位置。"""
        owner = self._owner
        root = owner.winfo_toplevel()
        return (
            owner.winfo_rootx(),
            owner.winfo_rooty(),
            owner.winfo_width(),
            owner.winfo_height(),
            root.winfo_rootx(),
            root.winfo_rooty(),
            root.winfo_width(),
            root.winfo_height(),
        )

    def _place_popup(self) -> bool:
        """把面板摆到控件下方或上方；摆不下就返回 ``False``。"""
        popup = self._popup
        owner = self._owner
        if popup is None or not popup.winfo_exists():
            return False
        if not owner.winfo_ismapped():
            return False

        root = owner.winfo_toplevel()
        scaling = root._get_window_scaling()
        root_left = root.winfo_rootx()
        root_top = root.winfo_rooty()
        root_right = root_left + root.winfo_width()
        root_bottom = root_top + root.winfo_height()

        widget_top = owner.winfo_rooty()
        widget_bottom = widget_top + owner.winfo_height()
        widget_left = owner.winfo_rootx()

        if widget_bottom <= root_top or widget_top >= root_bottom:
            return False
        if widget_left + owner.winfo_width() <= root_left or widget_left >= root_right:
            return False
        min_width = int(140 * scaling)
        if root_right - widget_left < min_width:
            return False

        row_px = int((_ROW_HEIGHT + 2) * scaling)
        pad_px = int(10 * scaling)
        visible_rows = min(max(1, self._rows), _MAX_VISIBLE_ROWS)
        needed = visible_rows * row_px + pad_px
        gap = int(_PANEL_GAP * scaling)

        space_below = root_bottom - widget_bottom - gap
        space_above = widget_top - root_top - gap
        below = space_below >= needed or space_below >= space_above
        available = space_below if below else space_above

        height_px = min(needed, available)
        if height_px < row_px:
            return False

        width_px = max(owner.winfo_width(), int(280 * scaling))
        width_px = min(width_px, root_right - root_left)
        left_px = min(widget_left, root_right - width_px)
        left_px = max(left_px, root_left)
        top_px = widget_bottom + gap if below else widget_top - gap - height_px

        popup.geometry(
            f"{max(1, int(width_px / scaling))}x{max(1, int(height_px / scaling))}"
            f"+{left_px}+{top_px}"
        )

        if self._listing is not None:
            content_px = self._rows * row_px + pad_px
            self._listing.set_scrollable(content_px > height_px)
        self._last_key = self._anchor_key()
        return True

    def _clip_popup_to_window(self) -> bool:
        """拖动缩窗时只裁右/下边界；整块被挤出窗口时返回 ``False``。"""
        popup = self._popup
        owner = self._owner
        if popup is None or not popup.winfo_exists():
            return False
        root = owner.winfo_toplevel()
        scaling = root._get_window_scaling()
        margin = int(6 * scaling)

        left = popup.winfo_rootx()
        top = popup.winfo_rooty()
        right_limit = root.winfo_rootx() + root.winfo_width() - margin
        bottom_limit = root.winfo_rooty() + root.winfo_height() - margin
        if left >= right_limit or top >= bottom_limit:
            return False

        width_px = min(popup.winfo_width(), right_limit - left)
        height_px = min(popup.winfo_height(), bottom_limit - top)
        if width_px <= 1 or height_px <= 1:
            return False

        popup.geometry(
            f"{max(1, int(width_px / scaling))}x{max(1, int(height_px / scaling))}"
            f"+{left}+{top}"
        )
        return True

    def _schedule_follow(self) -> None:
        """安排下一次跟随检查。"""
        self._follow_job = self._owner.after(_FOLLOW_MS, self._follow_tick)

    def _on_root_configure(self, event: tk.Event) -> None:
        """主窗口自己动的时候处理跟随；子控件的 Configure 一律忽略。"""
        if event.widget is not self._owner.winfo_toplevel():
            return
        size = (event.width, event.height)
        if size == self._last_root_size:
            if self.visible:
                self._place_popup()
            return
        self._last_root_size = size
        self._resize_quiet_until = time.monotonic() + _RESIZE_QUIET

    def _flush_place(self) -> None:
        """空闲时重摆面板；窗口还在缩放就再等一会儿。"""
        self._place_job = None
        if not self.visible:
            return
        if time.monotonic() < self._resize_quiet_until:
            return
        if not self._place_popup():
            self.close()

    def _follow_tick(self) -> None:
        """控件或窗口动了就重新摆面板；控件滚出可视区就收起。"""
        self._follow_job = None
        if not self.visible:
            return
        # 每轮先确认主程序还在前台：切应用 / 切虚拟桌面时 FocusOut 不一定来，
        # 而面板是 topmost，会一直压在新窗口上面
        if not self._is_active_window():
            self.close()
            return
        if time.monotonic() < self._resize_quiet_until:
            if not self._clip_popup_to_window():
                self.close()
                return
            self._schedule_follow()
            return
        if self._anchor_key() != self._last_key:
            if not self._place_popup():
                self.close()
                return
            if self._place_job is None:
                self._place_job = self._owner.after_idle(self._flush_place)
        self._schedule_follow()

    def _on_root_focus_out(self, _event: Optional[tk.Event] = None) -> None:
        """顶层窗口失焦后稍等再检查焦点。"""
        self._owner.after(100, self._check_focus)

    def _check_focus(self) -> None:
        """焦点既不在面板、也不在本窗口时收起面板。"""
        if not self.visible:
            return
        if not self._is_active_window():
            self.close()
            return
        try:
            focused = self._owner.winfo_toplevel().focus_get()
        except Exception:  # noqa: BLE001
            focused = None
        if focused is not None:
            name = str(focused)
            if name.startswith(str(self._popup)) or name.startswith(
                str(self._owner.winfo_toplevel())
            ):
                return
        self.close()

    def _is_active_window(self) -> bool:
        """当前前台窗口是不是本程序（主窗口或面板本身）。

        面板是 ``overrideredirect`` + ``topmost``：切到别的应用、别的虚拟桌面
        或另一块屏幕时，``<FocusOut>`` 不一定能收到，不主动判断就会一直浮着。
        Windows 上直接问系统当前前台窗口是谁。
        """
        root = self._owner.winfo_toplevel()
        try:
            if sys.platform == "win32":
                import ctypes

                user32 = ctypes.windll.user32
                foreground = user32.GetForegroundWindow()
                hwnds = {user32.GetParent(root.winfo_id()) or root.winfo_id()}
                if self._popup is not None and self._popup.winfo_exists():
                    hwnds.add(
                        user32.GetParent(self._popup.winfo_id())
                        or self._popup.winfo_id()
                    )
                return foreground in hwnds
            return root.focus_displayof() is not None
        except Exception:  # noqa: BLE001
            return True

    def _on_popup_enter(self, _event: Optional[tk.Event] = None) -> None:
        """鼠标进到面板上时再确认一次：主程序已经不在前台就收起。"""
        if not self._is_active_window():
            self.close()

    def _maybe_close(self, event: tk.Event) -> None:
        """顶层窗口上的点击：点在面板外就收起。"""
        popup = self._popup
        if popup is None or not popup.winfo_exists():
            return
        if (
            popup.winfo_rootx() <= event.x_root <= popup.winfo_rootx() + popup.winfo_width()
            and popup.winfo_rooty()
            <= event.y_root
            <= popup.winfo_rooty() + popup.winfo_height()
        ):
            return
        self.close()


def _round_window_corners(owner: tk.Misc, popup: ctk.CTkToplevel) -> None:
    """把面板窗口裁成圆角（Windows）；其它平台什么都不做。"""
    if sys.platform != "win32":
        return
    with contextlib.suppress(Exception):
        import ctypes

        popup.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(popup.winfo_id()) or popup.winfo_id()
        preference = ctypes.c_int(2)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)
        )
        if result == 0:
            return
        scaling = owner.winfo_toplevel()._get_window_scaling()
        radius = int(T.RADIUS_MEDIUM * 2 * scaling)
        width = popup.winfo_width()
        height = popup.winfo_height()
        region = ctypes.windll.gdi32.CreateRoundRectRgn(
            0, 0, width + 1, height + 1, radius, radius
        )
        ctypes.windll.user32.SetWindowRgn(hwnd, region, True)


class TagSelectField(ctk.CTkFrame):
    """多选标签下拉：点开的候选项变成标签排进框里，标签右侧小叉可删。

    没有输入框：整块就是标签区，点空白处或右侧箭头展开候选。标签不重复：
    已经选中的项再点一次会取消选中。标签多了横向滚动，鼠标停在标签上时
    整块标签一起高亮。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        values_provider: Callable[[], Sequence[str]],
        command: Optional[Callable[[list], None]] = None,
        placeholder: str = "",
        height: int = 36,
        values: Optional[Sequence[str]] = None,
        disabled: Optional[Sequence[str]] = None,
    ) -> None:
        """创建多选标签下拉。

        参数:
            master: 父容器。
            values_provider: 返回全部候选的函数，每次展开下拉都会调用。
            command: 选中/删除后的回调，参数是当前全部标签（列表）。
            placeholder: 一个标签都没有时的灰色提示文字。
            height: 整体高度（逻辑像素），默认 36。
            values: 初始选中的标签。
            disabled: 一开始就置灰的候选项；之后可以用 ``disable()`` 等方法改。
        """
        super().__init__(
            master,
            fg_color=T.COLOR_INPUT,
            border_width=1,
            border_color=T.COLOR_BORDER_INPUT,
            corner_radius=T.RADIUS_SMALL,
            height=height,
        )
        self.pack_propagate(False)
        # 与 DropField 同一个问题：CTk 默认把绘制高度取整到偶数，奇数物理像素
        # 时底边描边会被裁掉。
        self._draw_engine.set_round_to_even_numbers(False, False)
        self._draw()

        self._values_provider = values_provider
        self._command = command
        self._height = height
        self._values: list = []
        self._tags: list = []
        self._disabled: set = set(disabled or ())
        self._bg = color_of(T.COLOR_INPUT)
        # 只用来量标签文字宽度；单独一份，不碰 get_font() 的共享缓存
        self._measure_font = tkfont.Font(font=T.FONT_BODY)

        # 标签区：横向滚动；箭头固定在右侧
        # canvas 高度留出标签的上下留白：标签 24 + 上下各 4 = 32，正好不被裁
        self._canvas = tk.Canvas(
            self, height=height - 4, highlightthickness=0, bg=self._bg, bd=0
        )
        self._canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=1)
        self._strip = tk.Frame(self._canvas, bg=self._bg)
        self._window = self._canvas.create_window(
            (0, 0), window=self._strip, anchor="nw"
        )
        self._strip.bind("<Configure>", self._sync_region)
        self._canvas.bind("<Configure>", self._sync_size)
        for widget in (self._canvas, self._strip):
            widget.bind("<MouseWheel>", self._on_wheel)
            widget.bind("<Button-1>", self._on_strip_click)

        self.arrow: ctk.CTkLabel = ctk.CTkLabel(
            self,
            text="▼",
            width=24,
            height=24,
            font=(T.FONT_NAME, 10),
            text_color=T.COLOR_MUTED,
            fg_color="transparent",
            corner_radius=5,
            anchor="center",
            cursor="hand2",
        )
        self.arrow.pack(side="right", padx=(0, 8), pady=1)
        self.arrow.bind("<Button-1>", lambda _e: self.open_menu())

        # 一个标签都没有时的灰字提示；有标签就藏起来
        self._hint = ctk.CTkLabel(
            self,
            text=placeholder,
            font=T.FONT_SMALL,
            text_color=T.COLOR_FAINT,
            fg_color="transparent",
            anchor="w",
        )
        self._hint.place(x=10, rely=0.5, anchor="w")

        self._panel = _PopupPanel(self, build=self._build_rows)
        self.bind("<Destroy>", self._on_destroy)

        for value in values or ():
            self._add_tag(value)
        self._sync_hint()

    # ------------------------------------------------------------ 读写
    def get(self) -> list:
        """当前选中的标签（按添加顺序）。"""
        return list(self._values)

    def set(self, values: Sequence[str]) -> None:
        """整体替换标签列表。"""
        for _value, frame in self._tags:
            frame.destroy()
        self._tags.clear()
        self._values.clear()
        for value in values:
            self._add_tag(value)
        self._sync_size()
        if self._panel.visible:
            self._panel.refresh()

    def clear(self) -> None:
        """清空所有标签。"""
        self.set([])

    # ------------------------------------------------------------ 面板
    def open_menu(self) -> None:
        """展开候选面板。"""
        if not self._panel.open():
            self._panel.close()

    def _build_rows(self, parent: tk.Misc) -> int:
        """铺候选行；返回行数。

        行和 ``DropField`` 用同一个做法：一行一个 ``CTkButton``，高度 32、
        上下各留 1px、圆角 ``RADIUS_SMALL``，所以三张下拉列表的行距看起来一样。
        选中态不用整行亮色（选多了整块面板会晃眼），只给一层很淡的青底
        加青色文字。
        """
        values = list(self._values_provider() or [])
        for value in values:
            selected = value in self._values
            disabled = value in self._disabled
            button = ctk.CTkButton(
                parent,
                text=value,
                anchor="w",
                height=32,
                corner_radius=T.RADIUS_SMALL,
                fg_color=_SELECTED_ROW_BG if selected else "transparent",
                hover_color=(
                    T.COLOR_CARD
                    if disabled
                    else (_SELECTED_ROW_HOVER if selected else T.COLOR_SOFT_HOVER)
                ),
                text_color=T.COLOR_ACTIVE if selected else T.COLOR_TEXT,
                text_color_disabled=T.COLOR_FAINT,
                font=T.FONT_SMALL,
                command=lambda v=value: self._toggle(v),
                state="disabled" if disabled else "normal",
            )
            button.pack(fill="x", pady=1)
            if self._panel._listing is not None:
                self._panel._listing.bind_wheel(button)
        return len(values)

    # ------------------------------------------------------------ 禁用项
    def disable(self, value: str) -> None:
        """把某个候选项置灰；已经选中的会顺手从标签里移除。"""
        self._disabled.add(value)
        if value in self._values:
            self._remove_tag(value)
        elif self._panel.visible:
            self._panel.refresh()

    def enable(self, value: str) -> None:
        """解除某个候选项的禁用。"""
        self._disabled.discard(value)
        if self._panel.visible:
            self._panel.refresh()

    def is_disabled(self, value: str) -> bool:
        """这个候选项当前是不是禁用的。"""
        return value in self._disabled

    def get_disabled(self) -> list:
        """当前所有被禁用的候选项。"""
        return list(self._disabled)

    def set_disabled(self, values: Optional[Sequence[str]]) -> None:
        """整体设置禁用集合；传 ``None`` 或空列表等于全部解除。"""
        self._disabled = set(values or ())
        for value in list(self._values):
            if value in self._disabled:
                self._remove_tag(value)
        if self._panel.visible:
            self._panel.refresh()

    def clear_disabled(self) -> None:
        """解除全部禁用。"""
        self.set_disabled(None)

    def _toggle(self, value: str) -> None:
        """切换一个候选：没选就加标签，已选就删掉；面板保持打开。"""
        if value in self._disabled:
            return
        if value in self._values:
            self._remove_tag(value)
        else:
            self._add_tag(value)
            self._notify()
            if self._panel.visible:
                self._panel.refresh()

    # ------------------------------------------------------------ 标签
    def _add_tag(self, value: str) -> None:
        """加一个标签；重复值直接忽略。

        标签就是一个 ``CTkLabel``：底色、圆角、文字都在同一个控件上，
        不再套一层容器加一个 ×。点标签本身即可删掉。

        字体传裸 tuple，让 CTk 自己建一份：``get_font()`` 返回的是全库共享的
        ``CTkFont``，而 CTk 会对共享实例按控件缩放改写 size，一处改、处处变。
        """
        if value in self._values:
            return
        width = self._measure_font.measure(value) + 24
        tag = ctk.CTkLabel(
            self._strip,
            text=value,
            font=T.FONT_BODY,
            text_color=T.COLOR_ACCENT_TEXT,
            fg_color=T.COLOR_ACTIVE,
            corner_radius=6,
            height=24,
            width=width,
            cursor="hand2",
        )
        tag.pack(side="left", padx=(0, 6), pady=4)
        tag.bind("<Button-1>", lambda _e, v=value: self._remove_tag(v))
        tag.bind("<Enter>", lambda _e, t=tag: t.configure(fg_color=T.COLOR_ACTIVE_HOVER))
        tag.bind("<Leave>", lambda _e, t=tag: t.configure(fg_color=T.COLOR_ACTIVE))
        tag.bind("<MouseWheel>", self._on_wheel)
        self._values.append(value)
        self._tags.append((value, tag))
        self._sync_size()
        self._sync_hint()

    def _remove_tag(self, value: str) -> None:
        """删掉一个标签并回调。"""
        for index, (tag_value, frame) in enumerate(self._tags):
            if tag_value != value:
                continue
            frame.destroy()
            del self._tags[index]
            break
        if value in self._values:
            self._values.remove(value)
        self._sync_size()
        self._sync_hint()
        self._notify()
        if self._panel.visible:
            self._panel.refresh()

    def _notify(self) -> None:
        """把当前标签列表交给调用方。"""
        if self._command is not None:
            self._command(self.get())

    def _sync_hint(self) -> None:
        """没有标签时显示占位灰字，有了就藏起来。"""
        if self._values:
            self._hint.place_forget()
        elif not self._hint.winfo_ismapped():
            self._hint.place(x=10, rely=0.5, anchor="w")

    # ------------------------------------------------------------ 滚动与事件
    def _sync_region(self, _event: Optional[tk.Event] = None) -> None:
        """标签区尺寸变了，重算横向滚动区域。"""
        self._sync_size()

    def _sync_size(self, _event: Optional[tk.Event] = None) -> None:
        """内容比可视区宽才允许滚动；否则把内容宽度对齐到可视区。"""
        canvas_width = max(1, self._canvas.winfo_width())
        content_width = max(canvas_width, self._strip.winfo_reqwidth())
        height = max(1, self._strip.winfo_reqheight())
        self._canvas.itemconfigure(self._window, width=content_width)
        self._canvas.configure(scrollregion=(0, 0, content_width, height))

    def _on_wheel(self, event: tk.Event) -> Optional[str]:
        """标签区横向滚动；不够宽时不拦截事件。"""
        if self._strip.winfo_reqwidth() <= self._canvas.winfo_width():
            return None
        self._canvas.xview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"

    def _on_strip_click(self, _event: Optional[tk.Event] = None) -> str:
        """点标签区的空白处：展开面板。"""
        self.open_menu()
        return "break"

    def _on_destroy(self, event: tk.Event) -> None:
        """销毁时收面板，避免浮窗残留。"""
        if event.widget is self:
            self._panel.close()

    def destroy(self) -> None:
        """销毁前先收起面板。"""
        self._panel.close()
        with contextlib.suppress(tk.TclError):
            self.tk.call("font", "delete", self._measure_font.name)
        super().destroy()


class TreeSelectField(ctk.CTkFrame):
    """层级树下拉：分组节点点开才显示子项，子项逐级缩进。

    分组节点本身不能被选中（它就是一层目录），点它只切换展开/收起，
    右侧的 ``▶`` / ``▼`` 跟着变。只有叶子节点能选，选中后写进输入框。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        values_provider: Callable[[], Sequence],
        command: Optional[Callable[[str], None]] = None,
        placeholder: str = "",
        height: int = 36,
        value: str = "",
        disabled: Optional[Sequence[str]] = None,
    ) -> None:
        """创建层级树下拉。

        参数:
            master: 父容器。
            values_provider: 返回整棵树，元素是 ``"叶子"`` 或
                ``("分组", ["子项", ...])``，子项可继续嵌套。
            command: 选中叶子后的回调，参数是选中值。
            placeholder: 输入框为空时的灰色占位文字。
            height: 整体高度（逻辑像素），默认 36。
            value: 初始选中值。
        """
        super().__init__(
            master,
            fg_color=T.COLOR_INPUT,
            border_width=1,
            border_color=T.COLOR_BORDER_INPUT,
            corner_radius=T.RADIUS_SMALL,
            height=height,
        )
        self.pack_propagate(False)
        self._draw_engine.set_round_to_even_numbers(False, False)
        self._draw()

        self._values_provider = values_provider
        self._command = command
        self._height = height
        self._expanded: set = set()
        self._disabled: set = set(disabled or ())
        #: 当前面板里可见行：``{路径: 行控件}``，用来增量增删
        self._rows_map: dict = {}
        #: 分组行的右箭头：``{路径: 箭头 label}``
        self._markers: dict = {}
        #: 行实际挂在哪一层，展开时新行要放进同一个容器
        self._row_parent: Optional[tk.Misc] = None

        self.entry: CTkEntry = CTkEntry(
            self,
            fg_color="transparent",
            border_width=0,
            corner_radius=0,
            height=height - 8,
            font=T.FONT_BODY,
            text_color=T.COLOR_TEXT,
            placeholder_text=placeholder,
            placeholder_text_color=T.COLOR_FAINT,
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(12, 4), pady=1)

        self.arrow: ctk.CTkLabel = ctk.CTkLabel(
            self,
            text="▼",
            width=24,
            height=24,
            font=(T.FONT_NAME, 10),
            text_color=T.COLOR_MUTED,
            fg_color="transparent",
            corner_radius=5,
            anchor="center",
            cursor="hand2",
        )
        self.arrow.pack(side="right", padx=(0, 8), pady=1)
        self.arrow.bind("<Button-1>", lambda _e: self.open_menu())
        self.entry.bind("<Button-1>", lambda _e: self.open_menu())

        self._panel = _PopupPanel(self, build=self._build_rows)
        self.bind("<Destroy>", self._on_destroy)

        if value:
            self.set(value)

    # ------------------------------------------------------------ 读写
    def get(self) -> str:
        """当前输入框里的值。"""
        return self.entry.get()

    def set(self, value: str) -> None:
        """直接写入选中值（不触发回调）。"""
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    # ------------------------------------------------------------ 面板
    def open_menu(self) -> None:
        """展开候选面板。"""
        self._panel.open()

    # ------------------------------------------------------------ 禁用项
    def disable(self, value: str) -> None:
        """把某个叶子候选置灰：能看到，但选不了。"""
        self._disabled.add(value)
        if self._panel.visible:
            self._panel.refresh()

    def enable(self, value: str) -> None:
        """解除某个叶子候选的禁用。"""
        self._disabled.discard(value)
        if self._panel.visible:
            self._panel.refresh()

    def is_disabled(self, value: str) -> bool:
        """这个叶子候选当前是不是禁用的。"""
        return value in self._disabled

    def get_disabled(self) -> list:
        """当前所有被禁用的候选。"""
        return list(self._disabled)

    def set_disabled(self, values: Optional[Sequence[str]]) -> None:
        """整体设置禁用集合；传 ``None`` 或空列表等于全部解除。"""
        self._disabled = set(values or ())
        if self._panel.visible:
            self._panel.refresh()

    def clear_disabled(self) -> None:
        """解除全部禁用。"""
        self.set_disabled(None)

    def _tree(self) -> list:
        """把外部数据统一成 ``(文字, 子项列表或 None)`` 的嵌套结构。"""
        return [self._normalize(item) for item in (self._values_provider() or [])]

    @classmethod
    def _normalize(cls, item: object) -> tuple:
        """单个节点规范化；字符串等于没有子项的叶子。"""
        if isinstance(item, str):
            return (item, None)
        try:
            label = str(item[0])  # type: ignore[index]
            children = item[1] if len(item) > 1 else None  # type: ignore[index,arg-type]
        except (TypeError, IndexError):
            return (str(item), None)
        if children is None:
            return (label, None)
        return (label, [cls._normalize(child) for child in children])

    def _flatten(self) -> list:
        """整棵树按当前展开状态摊平：``(缩进层级, 文字, 是否分组, 路径)``。"""
        return self._subtree_rows(())

    def _nodes_under(self, path: tuple) -> list:
        """``path`` 对应的子节点列表；空路径返回整棵树。"""
        nodes = self._tree()
        for label in path:
            found = None
            for node_label, children in nodes:
                if node_label == label:
                    found = children
                    break
            nodes = found or []
        return nodes

    def _subtree_rows(self, path: tuple) -> list:
        """``path`` 之下按展开状态可见的行（不含 ``path`` 自己）。"""
        rows: list = []
        expanded = self._expanded

        def walk(nodes: Sequence, depth: int, prefix: tuple) -> None:
            for label, children in nodes:
                child_path = prefix + (label,)
                is_group = children is not None
                rows.append((depth, label, is_group, child_path))
                if is_group and child_path in expanded:
                    walk(children, depth + 1, child_path)

        walk(self._nodes_under(path), len(path), path)
        return rows

    def _build_rows(self, parent: tk.Misc) -> int:
        """铺整棵树的可见行；返回行数。"""
        self._row_parent = parent
        self._rows_map.clear()
        self._markers.clear()
        rows = self._flatten()
        for depth, label, is_group, path in rows:
            self._make_row(parent, depth, label, is_group, path)
        return len(rows)

    def _make_row(
        self, parent: tk.Misc, depth: int, label: str, is_group: bool, path: tuple
    ) -> ctk.CTkFrame:
        """建一行并记进 ``_rows_map``；分组行顺手记下右侧的箭头。"""
        font = T.FONT_SMALL
        row = ctk.CTkFrame(parent, fg_color="transparent", height=_ROW_HEIGHT)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        disabled = (not is_group) and label in self._disabled
        text = ctk.CTkLabel(
            row,
            text=label,
            anchor="w",
            font=font,
            text_color=(
                T.COLOR_MUTED
                if is_group
                else (T.COLOR_FAINT if disabled else T.COLOR_TEXT)
            ),
            fg_color="transparent",
        )
        text.pack(side="left", fill="x", expand=True, padx=(10 + depth * 14, 0))
        widgets = [row, text]
        if is_group:
            marker = ctk.CTkLabel(
                row,
                text="▼" if path in self._expanded else "▶",
                width=20,
                font=(T.FONT_NAME, 9),
                text_color=T.COLOR_MUTED,
                fg_color="transparent",
            )
            marker.pack(side="right", padx=(0, 8))
            widgets.append(marker)
            self._markers[path] = marker

        if is_group:
            handler = lambda _e, p=path: self._toggle_expand(p)  # noqa: E731
        elif disabled:
            handler = lambda _e: None  # noqa: E731
        else:
            handler = lambda _e, v=label: self._pick(v)  # noqa: E731
        for widget in widgets:
            widget.bind("<Button-1>", handler)
            widget.bind(
                "<Enter>",
                lambda _e, r=row, d=disabled: r.configure(
                    fg_color="transparent" if d else T.COLOR_SOFT_HOVER
                ),
            )
            widget.bind(
                "<Leave>", lambda _e, r=row: r.configure(fg_color="transparent")
            )
            if self._panel._listing is not None:
                self._panel._listing.bind_wheel(widget)
        self._rows_map[path] = row
        return row

    def _toggle_expand(self, path: tuple) -> None:
        """展开 / 收起一个分组节点。

        只在原来的行里增删受影响的那几行，不重建整个列表：重建会让面板
        整体重绘一次，看起来就是「闪一下」。只改行数、再重算面板高度。
        """
        if not self._panel.visible:
            return
        if path in self._expanded:
            self._expanded.discard(path)
            self._remove_children(path)
        else:
            self._expanded.add(path)
            self._insert_children(path)
        marker = self._markers.get(path)
        if marker is not None:
            marker.configure(text="▼" if path in self._expanded else "▶")
        self._panel.sync_rows(len(self._rows_map))

    def _insert_children(self, path: tuple) -> None:
        """把 ``path`` 之下按展开状态可见的行插到它后面。"""
        anchor = self._rows_map.get(path)
        if anchor is None or self._row_parent is None:
            return
        previous = anchor
        for depth, label, is_group, child_path in self._subtree_rows(path):
            row = self._make_row(self._row_parent, depth, label, is_group, child_path)
            row.pack_configure(after=previous)
            previous = row

    def _remove_children(self, path: tuple) -> None:
        """删掉 ``path`` 的所有后代行；别的行不动，pack 会自己往上收。"""
        depth = len(path)
        for child_path in [p for p in self._rows_map if len(p) > depth and p[:depth] == path]:
            row = self._rows_map.pop(child_path, None)
            self._markers.pop(child_path, None)
            if row is not None:
                with contextlib.suppress(tk.TclError):
                    row.destroy()

    def _pick(self, value: str) -> None:
        """选中叶子：写入输入框、收起面板、回调。"""
        if value in self._disabled:
            return
        self.set(value)
        self._panel.close()
        if self._command is not None:
            self._command(value)

    def _on_destroy(self, event: tk.Event) -> None:
        """销毁时收面板，避免浮窗残留。"""
        if event.widget is self:
            self._panel.close()

    def destroy(self) -> None:
        """销毁前先收起面板。"""
        self._panel.close()
        super().destroy()


class Stepper(ctk.CTkFrame):
    """紧凑步进器：``[ − ] 当前值 ▾ [ + ]``。

    左边减一步、右边加一步，中间点开是一组候选。数值范围（``from_`` /
    ``to`` / ``increment``）和备选列表（``values``）二选一；面板行为复用
    ``_PopupPanel``，和三个下拉一致。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        values: Optional[Sequence] = None,
        from_: float = 0,
        to: float = 100,
        increment: float = 1,
        value=None,
        command: Optional[Callable[[object], None]] = None,
        width: int = 170,
        height: int = 36,
        suffix: str = "%",
        decimals: int = 0,
    ) -> None:
        """创建步进器。

        参数:
            master: 父容器。
            values: 备选列表；传了就只在列表里前后移动。
            from_ / to / increment: 数值模式的起止与步长。
            value: 初始值；不传时数值模式取 ``from_``、列表模式取第一项。
            command: 值变化后的回调，参数是当前值。
            width: 整块宽度（逻辑像素），默认 170。
            height: 高度（逻辑像素），默认 36。
            suffix: 显示时拼在数值后面的单位，默认 ``"%"``。
            decimals: 数值显示几位小数，默认 0（取整）。
        """
        super().__init__(
            master,
            fg_color=T.COLOR_INPUT,
            border_width=1,
            border_color=T.COLOR_BORDER_INPUT,
            corner_radius=T.RADIUS_SMALL,
            height=height,
            width=width,
        )
        self.pack_propagate(False)
        # 和下拉框同一个坑：CTk 默认把绘制高度取整到偶数，奇数物理像素时底边描边会缺
        self._draw_engine.set_round_to_even_numbers(False, False)
        self._draw()

        self._values = list(values) if values is not None else None
        self._from = from_
        self._to = to
        self._increment = increment
        self._command = command
        self._suffix = suffix
        self._decimals = max(0, int(decimals))
        self._height = height
        self._bg = color_of(T.COLOR_INPUT)
        self._value = self._normalize(value) if value is not None else self._default()

        self._minus = tk.Canvas(
            self,
            width=22,
            height=height - 2,
            bg=self._bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._minus.pack(side="left", fill="y", padx=(8, 0), pady=1)
        self._plus = tk.Canvas(
            self,
            width=22,
            height=height - 2,
            bg=self._bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._plus.pack(side="right", fill="y", padx=(0, 8), pady=1)
        self._mid = tk.Canvas(
            self,
            height=height - 2,
            bg=self._bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._mid.pack(side="left", fill="x", expand=True, pady=1)

        self._minus.bind("<Button-1>", lambda _e: self._step(-1))
        self._plus.bind("<Button-1>", lambda _e: self._step(1))
        self._mid.bind("<Button-1>", lambda _e: self._open())
        for canvas in (self._minus, self._plus, self._mid):
            canvas.bind("<Configure>", lambda _e: self._draw_all())

        self._panel = _PopupPanel(self, build=self._build_rows)
        self.bind("<Destroy>", self._on_destroy)
        self._draw_all()

    # ------------------------------------------------------------ 读写
    def get(self):
        """当前值：列表模式返回列表里的那一项，数值模式返回 int/float。"""
        return self._value

    def set(self, value) -> None:
        """直接写入（不触发回调）。"""
        self._value = self._normalize(value)
        self._draw_mid()

    def _normalize(self, value):
        """数值模式统一成 int/float，列表模式原样保留。"""
        if self._values is not None:
            return value
        number = round(float(value), self._decimals)
        return int(number) if self._decimals == 0 else number

    def _default(self):
        """没给初始值时：列表取第一项，数值取起点。"""
        if self._values:
            return self._values[0]
        return self._normalize(self._from)

    def _label_of(self, value) -> str:
        """显示用的文字：数值拼单位，列表值原样。"""
        if self._values is not None:
            return str(value)
        return f"{value}{self._suffix}"

    def _candidates(self) -> list:
        """面板里的候选。"""
        if self._values is not None:
            return list(self._values)
        count = int((self._to - self._from) / self._increment) + 1
        count = max(1, min(count, 200))
        return [self._normalize(self._from + index * self._increment) for index in range(count)]

    # ------------------------------------------------------------ 交互
    def _step(self, direction: int) -> None:
        """左右箭头：列表里前后挪一项，数值上加减一个步长。"""
        if self._values is not None:
            try:
                index = self._values.index(self._value)
            except ValueError:
                index = 0
            index = max(0, min(len(self._values) - 1, index + direction))
            self._apply(self._values[index])
        else:
            stepped = float(self._value) + direction * self._increment
            stepped = max(self._from, min(self._to, stepped))
            self._apply(self._normalize(stepped))

    def _apply(self, value) -> None:
        """写入新值、重画、回调。"""
        self._value = self._normalize(value)
        self._draw_mid()
        if self._command is not None:
            self._command(self._value)

    def _open(self) -> None:
        """点中间：弹出候选面板。"""
        self._panel.open()

    def _build_rows(self, parent: tk.Misc) -> int:
        """铺候选按钮；返回行数。"""
        options = self._candidates()
        for option in options:
            chosen = option == self._value
            button = ctk.CTkButton(
                parent,
                text=self._label_of(option),
                anchor="w",
                height=32,
                corner_radius=T.RADIUS_SMALL,
                fg_color=_SELECTED_ROW_BG if chosen else "transparent",
                hover_color=_SELECTED_ROW_HOVER if chosen else T.COLOR_SOFT_HOVER,
                text_color=T.COLOR_ACTIVE if chosen else T.COLOR_TEXT,
                font=T.FONT_SMALL,
                command=lambda v=option: self._pick(v),
            )
            button.pack(fill="x", pady=1)
            if self._panel._listing is not None:
                self._panel._listing.bind_wheel(button)
        return len(options)

    def _pick(self, value) -> None:
        """面板里选中一项：写入、收起、回调。"""
        self._panel.close()
        self._apply(value)

    # ------------------------------------------------------------ 绘制
    def _draw_all(self) -> None:
        """重画减号、加号和中间那一段。"""
        self._draw_sign(self._minus, plus=False)
        self._draw_sign(self._plus, plus=True)
        self._draw_mid()

    def _draw_sign(self, canvas: tk.Canvas, *, plus: bool) -> None:
        """减号是一横，加号再加一竖；纯像素线，没有字体渲染的毛边。"""
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return
        color = color_of(T.COLOR_MUTED)
        middle = height // 2
        half = 5
        canvas.create_line(
            width // 2 - half, middle, width // 2 + half, middle, fill=color, width=2
        )
        if plus:
            center = width // 2
            canvas.create_line(
                center, middle - half, center, middle + half, fill=color, width=2
            )

    def _draw_mid(self) -> None:
        """中间的值和右箭头：两者当作一个整体居中。"""
        canvas = self._mid
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return
        middle = height // 2
        text_item = canvas.create_text(
            0,
            middle,
            text=self._label_of(self._value),
            anchor="w",
            fill=color_of(T.COLOR_TEXT),
            font=(T.FONT_NAME, 11),
        )
        bbox = canvas.bbox(text_item)
        text_width = (bbox[2] - bbox[0]) if bbox else 0
        gap = 6
        arrow = 9
        start = (width - (text_width + gap + arrow)) / 2
        canvas.move(text_item, start, 0)
        # 右侧一个小三角，表示可以点开
        tip_x = start + text_width + gap + arrow // 2
        canvas.create_polygon(
            tip_x - 4,
            middle - 2,
            tip_x + 4,
            middle - 2,
            tip_x,
            middle + 3,
            fill=color_of(T.COLOR_MUTED),
            outline="",
        )

    def _on_destroy(self, event: tk.Event) -> None:
        """销毁时收面板，避免浮窗残留。"""
        if event.widget is self:
            self._panel.close()

    def destroy(self) -> None:
        """销毁前先收起面板。"""
        self._panel.close()
        super().destroy()


