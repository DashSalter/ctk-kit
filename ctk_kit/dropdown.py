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
from .core.glass import backdrop_image
from .popup import round_window_corners, set_glass_geometry
from .fonts import get_font
from .inputs import CTkEntry
from .sugar import Enablable, Textual
from .theme import color_of, current_backdrop
from .core.win32 import acrylic_window

_ARROW_CLOSED = "▼"
_ARROW_OPEN = "▲"

# 面板最多铺几行，超出就在面板内部滚动
_MAX_VISIBLE_ROWS = 8
# 控件位置轮询间隔（毫秒）：页面滚动不会触发 <Configure>，只能主动看
_FOLLOW_MS = 60
# 窗口正在被拖动缩放时，面板保持不动，停手这么久之后再归位（秒）
_RESIZE_QUIET = 0.30
# 面板与输入框之间的间隙（逻辑像素）
# 面板底色和悬停色，跟右键菜单（context_menu._MENU_BG / _MENU_HOVER）保持一致。
_PANEL_BG = "#2B2B2B"
_PANEL_HOVER = "#575A63"


_PANEL_GAP = 2
# 打开面板的入场动画：淡入 + 从下方滑入（毫秒 / 每次间隔 / 滑入距离逻辑像素）
_OPEN_ANIM_MS = 130
_OPEN_ANIM_STEP = 16
_OPEN_SLIDE = 6
# 收起动画：淡出 + 向下滑回，比展开短，避免点完候选还迟迟不消失
_CLOSE_ANIM_MS = 100


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


class DropField(Enablable, Textual, ctk.CTkFrame):
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
        disabled: Optional[Sequence[str]] = None,
        glass: bool = True,
    ) -> None:
        """创建下拉输入框。

        参数:
            master: 父容器。
            values_provider: 返回候选列表的函数，每次展开下拉都会调用一次。
            command: 选中候选后的回调，参数是被选中的字符串。
            placeholder: 输入框为空时的灰色占位文字。
            height: 整体高度（像素），默认 36。
            disabled: 一开始就置灰的候选项；之后可以用 ``disable()`` 等方法改。
            glass: 面板边缘铺一层背后的模糊图，默认开；截图失败退回纯色。
        """
        super().__init__(
            master,
            fg_color=T.COLOR_INPUT,
            border_width=1,
            border_color=T.COLOR_BORDER_INPUT,
            # 圆角调小一档：CTk 的圆角是多边形画的，125% 缩放下大半径的右侧
            # 会露出明显的像素阶梯，小半径时肉眼基本看不出来。
            corner_radius=6,
            height=height,
        )
        self.pack_propagate(False)
        # CTkFrame 默认把绘制尺寸向下取整到偶数：控件的物理高度是奇数时，
        # 底边那条描边会被整条裁掉（125% / 150% 这类缩放下很常见）。
        # 关掉取整，按真实尺寸画，四边才齐。
        self._draw_engine.set_round_to_even_numbers(False, False)
        self._draw()
        self._values_provider: Callable[[], Sequence[str]] = values_provider
        self._command: Optional[Callable[[str], None]] = command
        self._disabled: set = set(disabled or ())
        # 控件本身是否可用；禁用时点不开面板、输入框也不接受键入
        self._enabled = True
        self._popup: Optional[ctk.CTkToplevel] = None
        self._root_bind_id: Optional[str] = None
        self._focus_bind_id: Optional[str] = None
        self._resize_bind_id: Optional[str] = None
        self._follow_job: Optional[str] = None
        self._place_job: Optional[str] = None
        self._anim_job: Optional[str] = None
        self._anim_started: float = 0.0
        self._popup_box: Optional[tuple] = None
        self._glass = False
        self._closing: Optional[ctk.CTkToplevel] = None
        self._close_job: Optional[str] = None
        self._last_key: Optional[tuple] = None
        self._resize_quiet_until: float = 0.0
        self._last_root_size: tuple = ()
        self._rows: int = 0
        self._listing: Optional[_PopupList] = None
        self._popup_body: Optional[ctk.CTkFrame] = None
        self._backdrop: Optional[ctk.CTkLabel] = None
        self._photo: Optional[ctk.CTkImage] = None
        self._glass = glass

        self.entry: CTkEntry = CTkEntry(
            self,
            fg_color="transparent",
            border_width=0,
            corner_radius=0,
            height=height - 2,
            font=get_font(T.FONT_BODY),
            text_color=T.COLOR_TEXT,
            placeholder_text=placeholder,
            placeholder_text_color=T.COLOR_FAINT,
        )
        # 内缩量等于外框的 border_width，否则子控件会压住那 1px 描边
        self.entry.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=1)

        self.arrow: ctk.CTkLabel = ctk.CTkLabel(
            self,
            text=_ARROW_CLOSED,
            width=34,
            height=26,
            font=get_font((T.FONT_NAME, 11)),
            text_color=T.COLOR_MUTED,
            fg_color="transparent",
            corner_radius=5,
            anchor="center",
        )
        self.arrow.pack(side="right", padx=(0, 4), pady=1)
        self.arrow.configure(cursor="hand2")
        self.arrow.bind("<Button-1>", lambda _event: self.open_menu())
        self.arrow.bind("<Enter>", lambda _event: self._set_hover(True))
        self.arrow.bind("<Leave>", lambda _event: self._set_hover(False))

    def _set_hover(self, hover: bool) -> None:
        """箭头悬停态：文字与底色一起变。"""
        if not getattr(self, "_enabled", True):
            return
        self.arrow.configure(
            text_color=T.COLOR_TEXT if hover else T.COLOR_MUTED,
            fg_color=T.COLOR_HOVER_FAINT if hover else "transparent",
        )

    def _apply_enabled(self, enabled: bool) -> None:
        """禁用时输入框变灰、箭头点不动、面板收起。"""
        self._enabled = bool(enabled)
        try:
            self.entry.configure(state="normal" if enabled else "disabled")
            self.arrow.configure(
                text_color=T.COLOR_MUTED if enabled else T.COLOR_FAINT,
                fg_color="transparent",
                cursor="hand2" if enabled else "",
            )
        except Exception:  # noqa: BLE001 - 窗口销毁中
            return
        if not enabled:
            self._close_menu()

    # --- 读写 ---
    def get(self) -> str:
        """当前输入框里的文字。"""
        return self.entry.get()

    def set(self, value: str) -> None:
        """直接写入一个值（不触发 ``command``）。"""
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def set_text(self, text: Any) -> None:
        """同 :meth:`set`；下拉框的「文字」就是输入框内容。"""
        self.set("" if text is None else str(text))

    def get_text(self) -> str:
        """读回输入框内容，等价于 ``get()``。"""
        try:
            return str(self.get())
        except Exception:  # noqa: BLE001 - 窗口销毁中
            return ""

    def clear(self) -> None:
        """清空输入框，等价于 ``set("")``。"""
        self.set("")

    # --- 下拉面板 ---
    def _build_rows(self, listing: _PopupList) -> None:
        """铺候选按钮：禁用的项置灰、点了不响应。"""
        for value in list(self._values_provider() or []):
            disabled = value in self._disabled
            button = ctk.CTkButton(
                listing.inner,
                text=value,
                anchor="w",
                height=32,
                corner_radius=T.RADIUS_SMALL,
                fg_color="transparent",
                hover_color=_PANEL_BG if disabled else _PANEL_HOVER,
                text_color=T.COLOR_TEXT,
                text_color_disabled=T.COLOR_FAINT,
                font=get_font(T.FONT_SMALL),
                command=lambda v=value: self._pick(v),
                state="disabled" if disabled else "normal",
            )
            # 左右 10：左边和层级树行的文字缩进（listing 5 + 10）对齐，
            # 右边这 10 正好给滚动条让位，出不出滚动条都不挤文字。
            button.pack(fill="x", pady=1)
            listing.bind_wheel(button)

    def _refresh_rows(self) -> None:
        """面板开着的时候按新的禁用集合重铺，关着就什么都不做。"""
        if self._listing is None or self._popup is None:
            return
        if not self._popup.winfo_exists():
            return
        for child in self._listing.inner.winfo_children():
            child.destroy()
        self._build_rows(self._listing)
        self._rows = len(list(self._values_provider() or []))
        if not self._place_popup():
            self._close_menu()

    # ------------------------------------------------------------ 禁用项
    def disable(self, value: Optional[str] = None) -> None:
        """禁用整个下拉框（不传参）或某个候选项（传 ``value``）。

        参数:
            value: 候选项文字。不传表示禁用控件本身——点不开面板、输入框
                也不再接受键入。
        """
        if value is None:
            self.set_enabled(False)
            return
        self._disabled.add(value)
        self._refresh_rows()

    def enable(self, value: Optional[str] = None) -> None:
        """启用整个下拉框（不传参）或解除某个候选项（传 ``value``）。"""
        if value is None:
            self.set_enabled(True)
            return
        self._disabled.discard(value)
        self._refresh_rows()

    def is_disabled(self, value: str) -> bool:
        """这个候选项当前是不是禁用的。"""
        return value in self._disabled

    def get_disabled(self) -> list:
        """当前所有被禁用的候选项（按传入顺序）。"""
        return list(self._disabled)

    def set_disabled(self, values: Optional[Sequence[str]]) -> None:
        """整体设置禁用集合；传 ``None`` 或空列表等于全部解除。"""
        self._disabled = set(values or ())
        self._refresh_rows()

    def clear_disabled(self) -> None:
        """解除全部禁用。"""
        self.set_disabled(None)

    def open_menu(self) -> None:
        """展开候选面板；已经展开时再次调用会收起。"""
        if not getattr(self, "_enabled", True):
            return
        if self._popup is not None and self._popup.winfo_exists():
            self._close_menu()
            return

        # 上一块面板还在淡出：立刻收掉，免得开新面板时两块叠在一起
        self._finish_closing()

        values = list(self._values_provider() or [])
        if not values:
            return

        # 面板不挂玻璃：右键菜单就是这么做的，展开时不会惊动 DWM，
        # 主窗口不会跟着闪一下。底色统一用 _PANEL_BG。
        veil = None
        popup = ctk.CTkToplevel(self)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        # 窗口铺成描边色、卡片内缩 1px：边框是「露出来的一圈底色」，
        # 会跟着窗口的圆角一起走，不会像矩形描边那样在四个角断开。
        popup.configure(fg_color=veil or T.COLOR_BORDER)

        body = ctk.CTkFrame(
            popup,
            fg_color=veil or _PANEL_BG,
            # 圆角跟系统 DWM 圆角对齐，免得四角露出比 1px 粗的描边。
            corner_radius=T.RADIUS_SMALL,
            border_width=0,
        )
        body.pack(fill="both", expand=True, padx=1, pady=1)
        # 背景先建、放在底层；模糊图等面板尺寸定下来后再补
        self._popup_body = body
        self._backdrop = ctk.CTkLabel(body, text="", fg_color="transparent")
        self._backdrop.place(x=0, y=0, relwidth=1, relheight=1)

        listing = _PopupList(body, veil or _PANEL_BG)
        listing.pack(fill="both", expand=True, padx=5, pady=5)
        self._build_rows(listing)

        popup.update_idletasks()
        self._popup = popup
        self._rows = len(values)
        self._listing = listing
        self._last_key = None
        self._glass = veil is not None
        if self._glass:
            # 玻璃要在「还没显示」时挂好：窗口第一次出现就是模糊背景，
            # 不会先闪一帧不透明底。挂完再定位，边框差值才是准的。
            tint = None
            with contextlib.suppress(Exception):
                tint = self.winfo_toplevel()._glass_tint()
            acrylic_window(popup, tint=tint)
            popup.update()
        if not self._place_popup():
            self._close_menu()
            return
        # 截图必须在显示之前：这时屏幕上还是面板背后的真实内容。
        # 系统玻璃已经给了真实背景，再铺一张模糊图反而是双份模糊。
        if not self._glass:
            self._apply_backdrop()
        # 先透明再显示，避免第一帧整块不透明地闪出来
        with contextlib.suppress(tk.TclError):
            popup.attributes("-alpha", 0.0)
        popup.deiconify()
        popup.bind("<Escape>", self._close_menu)
        # 鼠标进到面板上时再确认一次前台状态：切窗口的瞬间 FocusOut 可能没来
        popup.bind("<Enter>", self._on_popup_enter)
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
        self._start_open_anim()
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

        if self._glass:
            set_glass_geometry(popup, width_px, height_px, left_px, top_px)
        else:
            popup.geometry(
                f"{max(1, int(width_px / scaling))}x{max(1, int(height_px / scaling))}"
                f"+{left_px}+{top_px}"
            )

        # 入场动画要用的最终位置；窗口尺寸用逻辑像素（geometry 自己会乘缩放）
        self._popup_box = (
            max(1, int(width_px / scaling)),
            max(1, int(height_px / scaling)),
            left_px,
            top_px,
            int(_OPEN_SLIDE * scaling),
        )

        if self._listing is not None:
            content_px = self._rows * row_px + pad_px
            self._listing.scrollable = content_px > height_px
        self._last_key = self._anchor_key()
        return True

    def _start_open_anim(self) -> None:
        """面板显示后开始淡入 + 下滑；窗口不支持 alpha 时只做下滑。

        玻璃面板不做动画：它的尺寸靠 ``SetWindowPos`` 校正在客户区上，
        动画每帧改 ``geometry()`` 会把客户区又缩回去，内容被裁掉。
        """
        if self._popup is None or self._popup_box is None:
            return
        if self._glass:
            with contextlib.suppress(tk.TclError):
                self._popup.attributes("-alpha", 1.0)
            self._schedule_follow()
            return
        self._anim_started = time.perf_counter()
        self._anim_job = self.after(1, self._open_step)

    def _open_step(self) -> None:
        self._anim_job = None
        popup = self._popup
        if popup is None or not popup.winfo_exists() or self._popup_box is None:
            return
        width, height, left, top, slide = self._popup_box
        ratio = (time.perf_counter() - self._anim_started) / (_OPEN_ANIM_MS / 1000.0)
        done = ratio >= 1.0
        eased = 1.0 if done else 1.0 - (1.0 - ratio) ** 3
        offset = 0 if done else int(round((1.0 - eased) * slide))
        with contextlib.suppress(tk.TclError):
            popup.geometry(f"{width}x{height}+{left}+{top + offset}")
            popup.attributes("-alpha", 1.0 if done else round(eased, 3))
        if done:
            self._schedule_follow()
            return
        self._anim_job = self.after(_OPEN_ANIM_STEP, self._open_step)

    def _schedule_follow(self) -> None:
        """安排下一次跟随检查；重复调用会合并成一次。"""
        # 入场动画期间位置由动画控制，别让跟随逻辑把面板拽回去
        if self._anim_job is not None:
            return
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

        if self._glass:
            set_glass_geometry(popup, width_px, height_px, left, top)
        else:
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
        # 每轮先确认主程序还在前台：切应用 / 切虚拟桌面时 FocusOut 不一定来，
        # 而面板是 topmost，会一直压在新窗口上面
        if not self._is_active_window():
            self._close_menu()
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
        if not self._is_active_window():
            self._close_menu()
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

    def _is_active_window(self) -> bool:
        """当前前台窗口是不是本程序（主窗口或面板本身）。

        面板是 ``overrideredirect`` + ``topmost``：切到别的应用、别的虚拟桌面
        或另一块屏幕时，``<FocusOut>`` 不一定能收到，不主动判断就会一直浮着。
        Windows 上直接问系统当前前台窗口是谁。
        """
        root = self.winfo_toplevel()
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
        except Exception:
            return True

    def _on_popup_enter(self, _event: Optional[tk.Event] = None) -> None:
        """鼠标进到面板上时再确认一次：主程序已经不在前台就收起。"""
        if not self._is_active_window():
            self._close_menu()

    def _round_window_corners(self, popup: ctk.CTkToplevel) -> None:
        """把窗口本身裁成圆角，公共逻辑在 :mod:`ctk_kit.popup`。"""
        # 半径跟内部卡片同值：窗口比卡片更圆时，四角会露出一圈粗描边。
        round_window_corners(popup, T.RADIUS_SMALL)

    def _apply_backdrop(self) -> None:
        """把面板背后的屏幕内容模糊后铺在卡片底层；截图失败就保持纯色。

        列表本身是 ``tk.Canvas`` + ``tk.Frame``，必须有不透明底色，所以
        这层模糊图只会从卡片外圈的 5px 内边距和圆角处露出来。
        """
        popup = self._popup
        if (
            not self._glass
            or popup is None
            or self._backdrop is None
            or self._popup_box is None
        ):
            return
        width, height, left, top, _slide = self._popup_box
        with contextlib.suppress(Exception):
            scaling = popup._get_window_scaling()
            width_px = max(1, int(round(width * scaling)))
            height_px = max(1, int(round(height * scaling)))
            image = backdrop_image(
                left + 1,
                top + 1,
                width_px - 2,
                height_px - 2,
                scaling=scaling,
                radius=T.RADIUS_SMALL,
            )
            if image is None:
                return
            photo = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(max(1, width - 2), max(1, height - 2)),
            )
            self._photo = photo
            self._backdrop.configure(image=photo)

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

    def _close_menu(
        self, _event: Optional[tk.Event] = None, *, animate: bool = True
    ) -> None:
        """收起面板并清理绑定；重复调用安全。

        ``animate=False`` 时直接销毁浮窗（控件自己销毁时用）。
        """
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
        if self._anim_job is not None:
            with contextlib.suppress(Exception):
                self.after_cancel(self._anim_job)
            self._anim_job = None
        if self._resize_bind_id is not None:
            with contextlib.suppress(Exception):
                self.winfo_toplevel().unbind("<Configure>", self._resize_bind_id)
            self._resize_bind_id = None
        with contextlib.suppress(Exception):
            self.arrow.configure(text=_ARROW_CLOSED)
        popup = self._popup
        box = self._popup_box
        self._popup = None
        self._popup_box = None
        self._listing = None
        self._popup_body = None
        self._backdrop = None
        self._photo = None
        self._last_key = None
        if popup is None:
            # 已经关过（或正在淡出），不要再打断它
            return
        # 更早的一块还没淡完，先收掉
        self._finish_closing()
        if animate and box is not None and not self._glass:
            with contextlib.suppress(tk.TclError):
                if popup.winfo_exists():
                    self._start_close_anim(popup, box)
                    return
        with contextlib.suppress(Exception):
            if popup.winfo_exists():
                popup.destroy()

    def _finish_closing(self) -> None:
        """立刻结束上一块正在淡出的面板。"""
        if self._close_job is not None:
            with contextlib.suppress(Exception):
                self.after_cancel(self._close_job)
            self._close_job = None
        popup = self._closing
        self._closing = None
        if popup is not None:
            with contextlib.suppress(Exception):
                if popup.winfo_exists():
                    popup.destroy()

    def _start_close_anim(self, popup: ctk.CTkToplevel, box: tuple) -> None:
        """淡出 + 向下滑回，动画结束再销毁窗口。"""
        width, height, left, top, slide = box
        started = time.perf_counter()
        self._closing = popup

        def step() -> None:
            self._close_job = None
            if self._closing is not popup:
                return
            try:
                alive = bool(popup.winfo_exists())
            except tk.TclError:
                alive = False
            if not alive:
                self._closing = None
                return
            ratio = (time.perf_counter() - started) / (_CLOSE_ANIM_MS / 1000.0)
            done = ratio >= 1.0
            eased = 1.0 if done else 1.0 - (1.0 - ratio) ** 3
            offset = int(round(eased * slide))
            with contextlib.suppress(tk.TclError):
                popup.attributes(
                    "-alpha", 0.0 if done else round(1.0 - eased, 3)
                )
                popup.geometry(f"{width}x{height}+{left}+{top + offset}")
            if done:
                self._closing = None
                with contextlib.suppress(Exception):
                    popup.destroy()
                return
            with contextlib.suppress(tk.TclError):
                self._close_job = self.after(_OPEN_ANIM_STEP, step)

        with contextlib.suppress(tk.TclError):
            self._close_job = self.after(1, step)

    def destroy(self) -> None:
        """销毁前先收起面板，避免浮窗残留。"""
        self._close_menu(animate=False)
        self._finish_closing()
        super().destroy()
