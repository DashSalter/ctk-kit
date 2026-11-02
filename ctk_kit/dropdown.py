"""下拉输入框：输入框 + 右侧箭头，候选用 UI Kit 自己的卡片弹出。

不用 CTkComboBox：它底层是 tkinter.Menu（Windows 原生菜单），带粗白边、
直角和系统字体，和这套深色卡片的观感对不上。

箭头用字体里的实心三角字符，不做任何自绘——既不会有锯齿，也不会在输入框
内部留下色块。
"""

from __future__ import annotations

import contextlib
import sys
import time
import tkinter as tk
from typing import Callable, Optional, Sequence

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .inputs import CTkEntry
from .theme import color_of

_ARROW_CLOSED = "▼"
_ARROW_OPEN = "▲"

# 面板最多铺几行，超出就在面板内部滚动
_MAX_VISIBLE_ROWS = 8
# 控件位置轮询间隔（毫秒）：页面滚动不会触发 <Configure>，只能主动看
_FOLLOW_MS = 60
# 窗口正在被拖动缩放时，面板保持不动，停手这么久之后再归位（秒）
_RESIZE_QUIET = 0.30
# 面板与输入框之间的间隙（逻辑像素）
_PANEL_GAP = 2


class _PopupList(tk.Frame):
    """面板里的候选列表：内容超出时自己滚动。

    不用 ``CTkScrollableFrame``：它内部用 ``bind_all`` 抢全应用的滚轮，
    面板开关几次就会留下幽灵绑定；这里只绑自己的 canvas。
    """

    def __init__(self, master: tk.Misc, bg: str) -> None:
        """建候选列表：canvas 承载内容，内容超出时自己滚动。"""
        super().__init__(master, bg=bg, highlightthickness=0, bd=0)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollable = False

        self.inner.bind("<Configure>", self._sync_region)
        self.canvas.bind("<Configure>", self._sync_width)
        for widget in (self, self.canvas, self.inner):
            widget.bind("<MouseWheel>", self._on_wheel, add="+")

    def bind_wheel(self, widget: tk.Misc) -> None:
        """按钮自己也要绑：鼠标停在按钮上时滚轮事件不会冒泡到 canvas。"""
        widget.bind("<MouseWheel>", self._on_wheel, add="+")

    def _sync_region(self, _event: tk.Event = None) -> None:
        """内容尺寸变了，重算 canvas 的滚动区域。"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_width(self, event: tk.Event) -> None:
        """把内部内容框的宽度对齐到 canvas 宽度。"""
        self.canvas.itemconfigure(self._window, width=event.width)

    def _on_wheel(self, event: tk.Event) -> Optional[str]:
        """滚动候选列表；列表没有滚动空间时返回 ``None`` 让事件继续冒泡。"""
        if not self.scrollable:
            return None
        self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"


class DropField(ctk.CTkFrame):
    """输入框 + 下拉箭头，整体是一块填充式圆角框，外圈 1px 描边。

    用法与输入框接近：``get()`` / ``set(value)``；选中候选后会回调
    ``command(value)``。候选由 ``values_provider()`` 提供，每次展开都会重新
    调用，所以数据源可以在外部随意变化。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        values_provider: Callable[[], Sequence[str]],
        command: Optional[Callable[[str], None]] = None,
        placeholder: str = "",
        height: int = 36,
    ) -> None:
        """创建下拉输入框。

        参数:
            master: 父容器。
            values_provider: 返回候选列表的函数，每次展开下拉都会调用一次。
            command: 选中候选后的回调，参数是被选中的字符串。
            placeholder: 输入框为空时的灰色占位文字。
            height: 整体高度（像素），默认 36。
        """
        super().__init__(
            master,
            fg_color=T.COLOR_BORDER_INPUT,
            border_width=0,
            corner_radius=T.RADIUS_SMALL,
            height=height,
        )
        self.pack_propagate(False)
        self._values_provider: Callable[[], Sequence[str]] = values_provider
        self._command: Optional[Callable[[str], None]] = command
        self._popup: Optional[ctk.CTkToplevel] = None
        self._root_bind_id: Optional[str] = None
        self._focus_bind_id: Optional[str] = None
        self._resize_bind_id: Optional[str] = None
        self._follow_job: Optional[str] = None
        self._place_job: Optional[str] = None
        self._last_key: Optional[tuple] = None
        self._resize_quiet_until: float = 0.0
        self._last_root_size: tuple = ()
        self._rows: int = 0
        self._listing: Optional[_PopupList] = None

        # 描边用「外框底色露一圈」，不用 CTkFrame 的 border_width：
        # 后者是一内一外两个圆角矩形叠出来的，控件高度按物理像素取整成奇数时，
        # 内框会把底边那一条盖掉（高分屏上尤其明显，底边直接消失）。
        self._border = max(1, int(round(self._apply_widget_scaling(1))))
        self._inner = ctk.CTkFrame(
            self,
            fg_color=T.COLOR_INPUT,
            border_width=0,
            corner_radius=max(0, T.RADIUS_SMALL - 1),
        )
        self._inner.pack(
            fill="both", expand=True, padx=self._border, pady=self._border
        )
        self._inner.pack_propagate(False)

        self.entry: CTkEntry = CTkEntry(
            self._inner,
            fg_color="transparent",
            border_width=0,
            corner_radius=0,
            height=height - 4,
            font=get_font(T.FONT_BODY),
            text_color=T.COLOR_TEXT,
            placeholder_text=placeholder,
            placeholder_text_color=T.COLOR_FAINT,
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(11, 0), pady=0)

        self.arrow: ctk.CTkLabel = ctk.CTkLabel(
            self._inner,
            text=_ARROW_CLOSED,
            width=34,
            height=26,
            font=get_font((T.FONT_NAME, 11)),
            text_color=T.COLOR_MUTED,
            fg_color="transparent",
            corner_radius=5,
            anchor="center",
        )
        self.arrow.pack(side="right", padx=(0, 3), pady=0)
        self.arrow.configure(cursor="hand2")
        self.arrow.bind("<Button-1>", lambda _event: self.open_menu())
        self.arrow.bind("<Enter>", lambda _event: self._set_hover(True))
        self.arrow.bind("<Leave>", lambda _event: self._set_hover(False))

    def _set_hover(self, hover: bool) -> None:
        """箭头悬停态：文字与底色一起变。"""
        self.arrow.configure(
            text_color=T.COLOR_TEXT if hover else T.COLOR_MUTED,
            fg_color=T.COLOR_HOVER_FAINT if hover else "transparent",
        )

    # --- 读写 ---
    def get(self) -> str:
        """当前输入框里的文字。"""
        return self.entry.get()

    def set(self, value: str) -> None:
        """直接写入一个值（不触发 ``command``）。"""
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def clear(self) -> None:
        """清空输入框，等价于 ``set("")``。"""
        self.set("")

    # --- 下拉面板 ---
    def open_menu(self) -> None:
        """展开候选面板；已经展开时再次调用会收起。"""
        if self._popup is not None and self._popup.winfo_exists():
            self._close_menu()
            return

        values = list(self._values_provider() or [])
        if not values:
            return

        popup = ctk.CTkToplevel(self)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        # 窗口铺成描边色、卡片内缩 1px：边框是「露出来的一圈底色」，
        # 会跟着窗口的圆角一起走，不会像矩形描边那样在四个角断开。
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
        for value in values:
            button = ctk.CTkButton(
                listing.inner,
                text=value,
                anchor="w",
                height=32,
                corner_radius=T.RADIUS_SMALL,
                fg_color="transparent",
                hover_color=T.COLOR_SOFT_HOVER,
                text_color=T.COLOR_TEXT,
                font=get_font(T.FONT_SMALL),
                command=lambda v=value: self._pick(v),
            )
            button.pack(fill="x", pady=1)
            listing.bind_wheel(button)

        popup.update_idletasks()
        self._popup = popup
        self._rows = len(values)
        self._listing = listing
        self._last_key = None
        if not self._place_popup():
            self._close_menu()
            return
        popup.deiconify()
        popup.bind("<Escape>", self._close_menu)
        self._round_window_corners(popup)

        self.arrow.configure(text=_ARROW_OPEN)
        # 点击面板以外的地方收起：绑在顶层窗口上（子控件的点击也会冒泡到顶层）
        self._root_bind_id = self.winfo_toplevel().bind(
            "<Button-1>", self._maybe_close_menu, add="+"
        )
        # 焦点离开本应用（切到别的程序）时也收起，避免面板一直浮在最上面
        self._focus_bind_id = self.winfo_toplevel().bind(
            "<FocusOut>", self._on_root_focus_out, add="+"
        )
        # 窗口移动 / 缩放走 <Configure>，但要过滤掉子控件冒泡上来的事件，
        # 否则页面一滚动就被疯狂触发；页面滚动本身交给轮询。
        self._resize_bind_id = self.winfo_toplevel().bind(
            "<Configure>", self._on_root_configure, add="+"
        )
        self._schedule_follow()

    # --- 面板定位 ---
    def _anchor_key(self) -> tuple:
        """只要这些值没变，面板就不用重算位置。"""
        root = self.winfo_toplevel()
        return (
            self.winfo_rootx(),
            self.winfo_rooty(),
            self.winfo_width(),
            self.winfo_height(),
            root.winfo_rootx(),
            root.winfo_rooty(),
            root.winfo_width(),
            root.winfo_height(),
        )

    def _place_popup(self) -> bool:
        """把面板摆到输入框下方或上方；摆不下就返回 False（调用方收起面板）。

        优先向下；下方装不下就往上翻。实在放不下就裁到能放的高度，
        剩下的候选靠面板内部滚动。
        """
        popup = self._popup
        if popup is None or not popup.winfo_exists():
            return False
        if not self.winfo_ismapped():
            return False

        root = self.winfo_toplevel()
        scaling = root._get_window_scaling()
        root_left = root.winfo_rootx()
        root_top = root.winfo_rooty()
        root_right = root_left + root.winfo_width()
        root_bottom = root_top + root.winfo_height()

        widget_top = self.winfo_rooty()
        widget_bottom = widget_top + self.winfo_height()
        widget_left = self.winfo_rootx()

        # 控件被滚出可视区（或窗口缩到装不下它）：收起，别把面板留在窗口外面
        if widget_bottom <= root_top or widget_top >= root_bottom:
            return False
        if widget_left + self.winfo_width() <= root_left or widget_left >= root_right:
            return False
        # 右边被窗口切掉太多时也不再硬塞：留不足一个最小面板宽就不显示
        min_width = int(140 * scaling)
        if root_right - widget_left < min_width:
            return False

        row_px = int(34 * scaling)
        pad_px = int(10 * scaling)
        visible_rows = min(self._rows, _MAX_VISIBLE_ROWS)
        needed = visible_rows * row_px + pad_px
        gap = int(_PANEL_GAP * scaling)

        space_below = root_bottom - widget_bottom - gap
        space_above = widget_top - root_top - gap
        below = space_below >= needed or space_below >= space_above
        available = space_below if below else space_above

        height_px = min(needed, available)
        if height_px < row_px:
            # 上下都塞不下一行，收起面板比画一半好
            return False

        width_px = max(self.winfo_width(), int(320 * scaling))
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
            self._listing.scrollable = content_px > height_px
        self._last_key = self._anchor_key()
        return True

    def _schedule_follow(self) -> None:
        """安排下一次跟随检查；重复调用会合并成一次。"""
        self._follow_job = self.after(_FOLLOW_MS, self._follow_tick)

    def _on_root_configure(self, event: tk.Event) -> None:
        """主窗口自己动的时候处理跟随；子控件的 Configure 一律忽略。

        Tk 的 bindtags 会让绑定在顶层窗口上的 ``<Configure>`` 收到所有子控件的
        事件，滚动页面时每帧几十个，所以这里先按 ``event.widget`` 过滤。

        移动窗口和缩放窗口要分开对待：
        - 移动：面板立刻整体平移，跟手
        - 缩放：面板先别动（每帧重排会把它一帧帧推到左边），停手之后再归位
        """
        if event.widget is not self.winfo_toplevel():
            return
        size = (event.width, event.height)
        if size == self._last_root_size:
            # 尺寸没变 = 窗口在挪位置，直接跟
            if self._popup is not None and self._popup.winfo_exists():
                self._place_popup()
            return
        self._last_root_size = size
        self._resize_quiet_until = time.monotonic() + _RESIZE_QUIET

    def _clip_popup_to_window(self) -> bool:
        """拖动缩窗时只裁右/下边界：左边和上边不动，超出窗口的部分切掉。

        返回 ``False`` 表示整块都被挤出窗口了，该收起。
        """
        popup = self._popup
        if popup is None or not popup.winfo_exists():
            return False
        root = self.winfo_toplevel()
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

    def _flush_place(self) -> None:
        """空闲时重摆面板；窗口还在缩放就再等一会儿。"""
        self._place_job = None
        if self._popup is None or not self._popup.winfo_exists():
            return
        if time.monotonic() < self._resize_quiet_until:
            return
        if not self._place_popup():
            self._close_menu()

    def _follow_tick(self) -> None:
        """控件或窗口动了就重新摆面板；控件滚出可视区就收起。"""
        self._follow_job = None
        popup = self._popup
        if popup is None or not popup.winfo_exists():
            return
        # 窗口正在被拖大拖小：面板别整块重排（会被一帧帧推走），只裁右/下边界
        if time.monotonic() < self._resize_quiet_until:
            if not self._clip_popup_to_window():
                self._close_menu()
                return
            self._schedule_follow()
            return
        if self._anchor_key() != self._last_key:
            # 先按当前坐标收一次，保证面板不会停在窗口外面；
            # 窗口刚变尺寸时子控件还没重排完，等这一轮布局结束再精确对齐。
            if not self._place_popup():
                self._close_menu()
                return
            if self._place_job is None:
                self._place_job = self.after_idle(self._flush_place)
        self._schedule_follow()

    def _on_root_focus_out(self, _event: Optional[tk.Event] = None) -> None:
        """顶层窗口失焦后稍等再检查焦点，避免刚点面板就被收起。"""
        self.after(100, self._check_focus)

    def _check_focus(self) -> None:
        """焦点既不在面板、也不在本窗口时收起面板。"""
        if self._popup is None:
            return
        try:
            focused = self.winfo_toplevel().focus_get()
        except Exception:
            focused = None
        if focused is not None:
            widget_name = str(focused)
            if widget_name.startswith(str(self._popup)) or widget_name.startswith(
                str(self.winfo_toplevel())
            ):
                return
        self._close_menu()

    def _round_window_corners(self, popup: ctk.CTkToplevel) -> None:
        """把窗口本身裁成圆角。

        优先让 Win11 的 DWM 画圆角（边缘抗锯齿、没有阶梯）；旧系统退回
        ``SetWindowRgn`` 硬裁剪——那圈锯齿是 GDI 区域的固有代价。
        非 Windows 平台什么都不做。
        """
        if sys.platform != "win32":
            return
        with contextlib.suppress(Exception):
            import ctypes

            popup.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(popup.winfo_id()) or popup.winfo_id()
            # DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2
            preference = ctypes.c_int(2)
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)
            )
            if result == 0:
                return
            scaling = self.winfo_toplevel()._get_window_scaling()
            # CreateRoundRectRgn 收的是椭圆宽高（直径）
            radius = int(T.RADIUS_MEDIUM * 2 * scaling)
            width = popup.winfo_width()
            height = popup.winfo_height()
            region = ctypes.windll.gdi32.CreateRoundRectRgn(
                0, 0, width + 1, height + 1, radius, radius
            )
            ctypes.windll.user32.SetWindowRgn(hwnd, region, True)

    def _maybe_close_menu(self, event: tk.Event) -> None:
        """顶层窗口上的点击：点在面板外就收起。"""
        popup = self._popup
        if popup is None or not popup.winfo_exists():
            return
        if (
            popup.winfo_rootx()
            <= event.x_root
            <= popup.winfo_rootx() + popup.winfo_width()
            and popup.winfo_rooty()
            <= event.y_root
            <= popup.winfo_rooty() + popup.winfo_height()
        ):
            return
        self._close_menu()

    def _pick(self, value: str) -> None:
        """选中候选：写入值、收起面板、回调。"""
        self.set(value)
        self._close_menu()
        if self._command is not None:
            self._command(value)

    def _close_menu(self, _event: Optional[tk.Event] = None) -> None:
        """收起面板并清理绑定；重复调用安全。"""
        if self._root_bind_id is not None:
            with contextlib.suppress(Exception):
                self.winfo_toplevel().unbind("<Button-1>", self._root_bind_id)
            self._root_bind_id = None
        if self._focus_bind_id is not None:
            with contextlib.suppress(Exception):
                self.winfo_toplevel().unbind("<FocusOut>", self._focus_bind_id)
            self._focus_bind_id = None
        if self._follow_job is not None:
            with contextlib.suppress(Exception):
                self.after_cancel(self._follow_job)
            self._follow_job = None
        if self._place_job is not None:
            with contextlib.suppress(Exception):
                self.after_cancel(self._place_job)
            self._place_job = None
        if self._resize_bind_id is not None:
            with contextlib.suppress(Exception):
                self.winfo_toplevel().unbind("<Configure>", self._resize_bind_id)
            self._resize_bind_id = None
        with contextlib.suppress(Exception):
            self.arrow.configure(text=_ARROW_CLOSED)
        if self._popup is not None:
            with contextlib.suppress(Exception):
                if self._popup.winfo_exists():
                    self._popup.destroy()
            self._popup = None
        self._listing = None
        self._last_key = None

    def destroy(self) -> None:
        """销毁前先收起面板，避免浮窗残留。"""
        self._close_menu()
        super().destroy()
