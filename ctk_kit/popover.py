"""悬浮卡片：点一下控件，旁边弹一块内容。

和 ``Tooltip`` 的区别：Tooltip 是悬停显示的一段文字，鼠标移开就消失；
Popover 是点击打开、可以放按钮 / 输入框等任意控件，点外面才关。

用法::

    from ctk_kit import Popover, PrimaryButton

    def build(parent):
        CTkLabel(parent, text="筛选条件").pack(padx=12, pady=(12, 4))
        PrimaryButton(parent, "应用").pack(padx=12, pady=(4, 12))

    button = PrimaryButton(card, "筛选")
    Popover(button, content=build, width=220)
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional, Tuple

import customtkinter as ctk

from . import tokens as T
from .dialog import _round_corners

__all__ = ["Popover"]

PopoverContent = Optional[Callable[[ctk.CTkFrame], None]]


class Popover:
    """点控件弹出的浮动卡片。

    参数:
        widget: 触发弹层的控件。
        content: 构建内容的函数，参数是弹层内部容器。
        width: 弹层宽度（逻辑像素），默认 240。
        placement: ``bottom``（默认）或 ``top``。
        padding: 预留，暂未使用。

    方法:
        show() / hide() / toggle(): 手动控制。
        destroy(): 关掉并解绑点击事件。
    """

    def __init__(
        self,
        widget: tk.Misc,
        *,
        content: PopoverContent = None,
        width: int = 240,
        placement: str = "bottom",
        padding: int = 12,
    ) -> None:
        """给 ``widget`` 挂上点击切换弹层的行为。"""
        self._widget = widget
        self._content = content
        self._width = width
        self._placement = placement
        self._padding = padding
        self._window: Optional[ctk.CTkToplevel] = None
        self._bind_id = widget.bind("<Button-1>", self._on_click, add="+")

    # --- 对外 ---
    def show(self) -> None:
        """打开弹层；已经开着就什么也不做。"""
        if self._window is not None and self._window.winfo_exists():
            return

        window = ctk.CTkToplevel(self._widget)
        window.withdraw()
        window.overrideredirect(True)
        try:
            window.attributes("-topmost", True)
        except tk.TclError:
            pass

        frame = ctk.CTkFrame(
            window,
            fg_color=T.COLOR_CARD,
            border_width=1,
            border_color=T.COLOR_BORDER,
            corner_radius=T.RADIUS_MEDIUM,
        )
        frame.pack(fill="both", expand=True)
        if self._content is not None:
            self._content(frame)

        window.update_idletasks()
        width = self._width or frame.winfo_reqwidth()
        height = frame.winfo_reqheight()
        x, y = self._place(width, height)
        window.geometry(f"{width}x{height}+{x}+{y}")
        _round_corners(window, T.RADIUS_MEDIUM)
        window.deiconify()
        window.lift()
        window.focus_force()
        window.bind("<FocusOut>", lambda _e: window.after(60, self._maybe_hide))
        self._window = window

    def hide(self) -> None:
        """关掉弹层。"""
        window = self._window
        self._window = None
        if window is not None:
            try:
                window.destroy()
            except Exception:  # noqa: BLE001 - 窗口可能已经没了
                pass

    def toggle(self) -> None:
        """开着就关，关着就开。"""
        if self._window is not None and self._window.winfo_exists():
            self.hide()
        else:
            self.show()

    def destroy(self) -> None:
        """关掉弹层并解绑控件的点击事件。"""
        self.hide()
        try:
            self._widget.unbind("<Button-1>", self._bind_id)
        except Exception:  # noqa: BLE001
            pass

    # --- 内部 ---
    def _on_click(self, _event: tk.Event = None) -> None:
        """控件被点一下。"""
        self.toggle()

    def _place(self, width: int, height: int) -> Tuple[int, int]:
        """放在控件下方居中；贴边就翻到上方或往里收。"""
        widget = self._widget
        x = widget.winfo_rootx() + (widget.winfo_width() - width) // 2
        if self._placement == "top":
            y = widget.winfo_rooty() - height - 6
        else:
            y = widget.winfo_rooty() + widget.winfo_height() + 6

        screen_w = widget.winfo_screenwidth()
        screen_h = widget.winfo_screenheight()
        x = max(8, min(x, screen_w - width - 8))
        y = max(8, min(y, screen_h - height - 40))
        return x, y

    def _maybe_hide(self) -> None:
        """焦点离开后，指针也不在弹层或触发控件上才关。"""
        if self._window is None:
            return
        try:
            x, y = self._window.winfo_pointerxy()
            under = self._window.winfo_containing(x, y)
        except Exception:  # noqa: BLE001
            under = None
        if under is not None:
            path = str(under)
            if path.startswith(str(self._window)) or path.startswith(str(self._widget)):
                return
        try:
            focus = self._window.focus_get()
        except Exception:  # noqa: BLE001
            focus = None
        if focus is not None and str(focus).startswith(str(self._window)):
            return
        self.hide()
