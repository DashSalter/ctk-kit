"""下拉输入框：输入框 + 右侧箭头，候选用 UI Kit 自己的卡片弹出。

不用 CTkComboBox：它底层是 tkinter.Menu（Windows 原生菜单），带粗白边、
直角和系统字体，和这套深色卡片的观感对不上。

箭头用字体里的实心三角字符，不做任何自绘——既不会有锯齿，也不会在输入框
内部留下色块。
"""

from __future__ import annotations

import contextlib
import sys
import tkinter as tk
from typing import Callable, Optional, Sequence

import customtkinter as ctk

from . import tokens as T

_ARROW_CLOSED = "▼"
_ARROW_OPEN = "▲"


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
            fg_color=T.COLOR_INPUT,
            border_width=1,
            border_color=T.COLOR_BORDER_INPUT,
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

        self.entry: ctk.CTkEntry = ctk.CTkEntry(
            self,
            fg_color="transparent",
            border_width=0,
            corner_radius=0,
            height=height - 2,
            font=T.FONT_BODY,
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
            font=(T.FONT_NAME, 11),
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

        for value in values:
            ctk.CTkButton(
                body,
                text=value,
                anchor="w",
                height=32,
                corner_radius=T.RADIUS_SMALL,
                fg_color="transparent",
                hover_color=T.COLOR_SOFT_HOVER,
                text_color=T.COLOR_TEXT,
                font=T.FONT_SMALL,
                command=lambda v=value: self._pick(v),
            ).pack(fill="x", padx=5, pady=1)

        popup.update_idletasks()
        # 宽高按逻辑像素缩放，位置参数直接是物理像素
        scaling = self.winfo_toplevel()._get_window_scaling()
        width = max(self.winfo_width(), int(320 * scaling)) / scaling
        height = (popup.winfo_reqheight() + 2) / scaling
        popup.geometry(
            f"{int(width)}x{int(height)}+"
            f"{self.winfo_rootx()}+{self.winfo_rooty() + self.winfo_height() + 2}"
        )
        popup.deiconify()
        popup.bind("<Escape>", self._close_menu)
        self._round_window_corners(popup)

        self._popup = popup
        self.arrow.configure(text=_ARROW_OPEN)
        # 点击面板以外的地方收起：绑在顶层窗口上（子控件的点击也会冒泡到顶层）
        self._root_bind_id = self.winfo_toplevel().bind(
            "<Button-1>", self._maybe_close_menu, add="+"
        )
        # 焦点离开本应用（切到别的程序）时也收起，避免面板一直浮在最上面
        self._focus_bind_id = self.winfo_toplevel().bind(
            "<FocusOut>", self._on_root_focus_out, add="+"
        )
        # 主窗口移动或缩放时，面板要贴着输入框重新对齐
        self._resize_bind_id = self.winfo_toplevel().bind(
            "<Configure>", self._follow_root, add="+"
        )

    def _follow_root(self, _event: Optional[tk.Event] = None) -> None:
        """主窗口移动 / 缩放后，把面板重新贴回输入框下方。"""
        popup = self._popup
        if popup is None or not popup.winfo_exists():
            return
        if not self.winfo_ismapped():
            self._close_menu()
            return
        scaling = self.winfo_toplevel()._get_window_scaling()
        width = max(self.winfo_width(), int(320 * scaling)) / scaling
        height = (popup.winfo_reqheight() + 2) / scaling
        popup.geometry(
            f"{int(width)}x{int(height)}+"
            f"{self.winfo_rootx()}+{self.winfo_rooty() + self.winfo_height() + 2}"
        )

    def _on_root_focus_out(self, _event: Optional[tk.Event] = None) -> None:
        """顶层窗口失焦后稍等再检查焦点，避免刚点面板就被收起。"""
        self.after(100, self._check_focus)

    def _check_focus(self) -> None:
        """焦点既不在面板、也不在本窗口时收起面板。"""
        if self._popup is None:
            return
        try:
            focused = self.focus_get()
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

    def destroy(self) -> None:
        """销毁前先收起面板，避免浮窗残留。"""
        self._close_menu()
        super().destroy()
