"""颜色选择器：点色块从预设颜色里挑一个。

用法::

    from ctk_kit import ColorPicker

    picker = ColorPicker(card, value="#2563eb", command=lambda c: print(c))
    picker.pack(side="left")

    picker.get()          # 当前颜色
    picker.set("#dc2626") # 直接改

``colors`` 可以换成自己的色板；``command`` 在用户选色时触发，``set()``
默认不触发。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, List, Optional, Sequence

import customtkinter as ctk

from . import tokens as T
from .dialog import _round_corners
from .fonts import get_font
from .popup import scaled_geometry

__all__ = ["ColorPicker"]

ColorCommand = Optional[Callable[[str], None]]

#: 默认色板：常用主色 + 深浅灰，够覆盖大多数场景。
_SWATCHES = [
    "#2563eb",
    "#0891b2",
    "#059669",
    "#ca8a04",
    "#ea580c",
    "#dc2626",
    "#db2777",
    "#7c3aed",
    "#475569",
    "#0f172a",
    "#ffffff",
    "#94a3b8",
]


class ColorPicker(ctk.CTkFrame):
    """带色块预览的下拉选色控件。

    参数:
        master: 父容器。
        value: 初始颜色，默认主色蓝。
        colors: 自定义色板（hex 字符串列表）；不传用内置 12 色。
        command: 选色回调，参数是 hex 字符串。
        width: 控件宽度，默认 130。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        get(): 当前颜色。
        set(color, notify=False): 改颜色；``notify=True`` 时也回调。
        open() / close() / toggle(): 手动控制色板。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        value: str = "#2563eb",
        colors: Optional[Sequence[str]] = None,
        command: ColorCommand = None,
        width: int = 130,
        **kwargs: Any,
    ) -> None:
        """建颜色选择器；色板默认 4 列 3 行。"""
        super().__init__(
            master,
            fg_color=T.COLOR_INPUT,
            border_width=1,
            border_color=T.COLOR_BORDER_INPUT,
            corner_radius=T.RADIUS_SMALL,
            width=width,
            height=38,
            **kwargs,
        )
        self.pack_propagate(False)

        self._value = value
        self._command = command
        self._colors: List[str] = list(colors) if colors else list(_SWATCHES)
        self._popup: Optional[ctk.CTkToplevel] = None

        self._swatch = ctk.CTkButton(
            self,
            text="",
            width=22,
            height=22,
            corner_radius=4,
            fg_color=value,
            hover_color=value,
            border_width=1,
            border_color=T.COLOR_BORDER,
            command=self.toggle,
        )
        self._swatch.pack(side="left", padx=(8, 6))

        self._label = ctk.CTkLabel(
            self,
            text=value,
            font=get_font(T.FONT_TINY),
            text_color=T.COLOR_TEXT,
            anchor="w",
        )
        self._label.pack(side="left", fill="x", expand=True)

        self._arrow = ctk.CTkButton(
            self,
            text="▾",
            width=26,
            height=26,
            corner_radius=6,
            fg_color="transparent",
            hover_color=T.COLOR_SOFT,
            text_color=T.COLOR_MUTED,
            font=get_font((T.FONT_NAME, 16)),
            command=self.toggle,
        )
        self._arrow.pack(side="right", padx=(0, 6))

    # --- 对外 ---
    def get(self) -> str:
        """当前颜色。"""
        return self._value

    def set(self, color: str, notify: bool = False) -> None:
        """改颜色；``notify=True`` 时也触发 ``command``。"""
        self._value = color
        self._swatch.configure(fg_color=color, hover_color=color)
        self._label.configure(text=color)
        if notify and self._command is not None:
            self._command(color)

    def open(self) -> None:
        """打开色板；已经开着就什么也不做。"""
        if self._popup is not None and self._popup.winfo_exists():
            return

        window = ctk.CTkToplevel(self)
        window.withdraw()
        window.overrideredirect(True)
        try:
            window.attributes("-topmost", True)
        except tk.TclError:
            pass

        # 描边画在窗口上：整窗铺描边色，色板卡片四边各内缩 1px。
        window.configure(fg_color=T.COLOR_BORDER)
        frame = ctk.CTkFrame(
            window,
            fg_color=T.COLOR_CARD,
            border_width=0,
            # 圆角跟系统 DWM 圆角对齐，免得四角露出比 1px 粗的描边。
            corner_radius=T.RADIUS_SMALL,
        )
        frame.pack(fill="both", expand=True, padx=1, pady=1)

        columns = 4
        for index, color in enumerate(self._colors):
            selected = color.lower() == self._value.lower()
            ctk.CTkButton(
                frame,
                text="",
                width=28,
                height=28,
                corner_radius=6,
                fg_color=color,
                hover_color=color,
                border_width=2 if selected else 1,
                border_color=T.COLOR_TEXT if selected else T.COLOR_BORDER,
                command=lambda c=color: self._pick(c),
            ).grid(
                row=index // columns,
                column=index % columns,
                padx=6,
                pady=6,
            )

        window.update_idletasks()
        width = frame.winfo_reqwidth() + 2
        height = frame.winfo_reqheight() + 2
        x, y = self._place(width, height)
        # 宽高是物理像素，geometry 会再乘窗口缩放，交给 scaled_geometry 除回去。
        window.geometry(scaled_geometry(window, width, height, x, y))
        _round_corners(window, T.RADIUS_SMALL)
        window.deiconify()
        window.lift()
        window.focus_force()
        window.bind("<FocusOut>", lambda _e: window.after(60, self._maybe_hide))
        self._popup = window

    def close(self) -> None:
        """关掉色板。"""
        window = self._popup
        self._popup = None
        if window is not None:
            try:
                window.destroy()
            except Exception:  # noqa: BLE001
                pass

    def toggle(self) -> None:
        """开着就关，关着就开。"""
        if self._popup is not None and self._popup.winfo_exists():
            self.close()
        else:
            self.open()

    # --- 内部 ---
    def _place(self, width: int, height: int) -> tuple:
        """色板放在控件下方，贴边就往里收。"""
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(8, min(x, screen_w - width - 8))
        y = max(8, min(y, screen_h - height - 40))
        return x, y

    def _pick(self, color: str) -> None:
        """选中一个颜色并关闭色板。"""
        self.set(color, notify=True)
        self.close()

    def _maybe_hide(self) -> None:
        """焦点离开后，指针也不在弹层或控件上才关。"""
        if self._popup is None:
            return
        try:
            x, y = self._popup.winfo_pointerxy()
            under = self._popup.winfo_containing(x, y)
        except Exception:  # noqa: BLE001
            under = None
        if under is not None:
            path = str(under)
            if path.startswith(str(self._popup)) or path.startswith(str(self)):
                return
        if self._has_focus():
            return
        self.close()

    def _has_focus(self) -> bool:
        """焦点是否还在弹层里。"""
        if self._popup is None:
            return False
        try:
            focus = self._popup.focus_get()
        except Exception:  # noqa: BLE001
            return False
        return focus is not None and str(focus).startswith(str(self._popup))
