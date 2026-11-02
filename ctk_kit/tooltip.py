"""悬浮提示：鼠标停在控件上时，在下方弹一行说明。

用法::

    from ctk_kit import Tooltip

    Tooltip(button, "保存当前草稿")
    Tooltip(entry, lambda: f"当前长度 {len(entry.get())}", delay=300)

提示窗口是无边框的 ``Toplevel``，不抢焦点、不进任务栏；鼠标移开、按下
控件或控件被销毁时自动收起。文字如果是可调用对象，每次弹出前现取，
适合放「当前值」这类会变的内容。

提示的配色跟着当前外观走（卡片底、正文色、1px 描边），圆角在 Windows
上裁出来；其他平台退回直角，不影响功能。
"""

from __future__ import annotations

import contextlib
import sys
import tkinter as tk
from typing import Any, Callable, Optional, Union

from . import tokens as T
from .fonts import get_font
from .theme import color_of

__all__ = ["Tooltip"]

TextSource = Union[str, Callable[[], str]]


def _round_corners(window: tk.Misc, radius: int = 6) -> None:
    """把无边框窗口裁成圆角（Windows）；其他平台不做处理。"""
    with contextlib.suppress(Exception):
        if sys.platform != "win32":
            return
        import ctypes

        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()
        preference = ctypes.c_int(2)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)
        )
        if result == 0:
            return
        scaling = window.winfo_fpixels("1i") / 96.0
        r = int(radius * 2 * scaling)
        region = ctypes.windll.gdi32.CreateRoundRectRgn(
            0, 0, window.winfo_width() + 1, window.winfo_height() + 1, r, r
        )
        ctypes.windll.user32.SetWindowRgn(hwnd, region, True)


class Tooltip:
    """挂在任意控件上的悬停提示。

    参数:
        widget: 要挂提示的控件。
        text: 提示文字；也可以传一个返回字符串的函数，每次显示前调用。
        delay: 鼠标停多久后弹出（毫秒），默认 500。
        wraplength: 文字超过这个宽度就换行（像素），默认 300。
        font: 提示文字字体，默认 :data:`tokens.FONT_SMALL`。
        padding: ``(左右, 上下)`` 的内边距，默认 ``(10, 6)``。

    属性:
        text: 当前文字（读的时候会把函数求值）。

    方法:
        show(): 立刻显示，不等 ``delay``。
        hide(): 收起。
        set_text(text): 换文字；正在显示时立刻重排。
        configure(text=...): 同 ``set_text``。
        destroy(): 解绑并销毁提示窗口。
    """

    def __init__(
        self,
        widget: tk.Misc,
        text: TextSource = "",
        *,
        delay: int = 500,
        wraplength: int = 300,
        font: T.FontSpec = T.FONT_SMALL,
        padding: tuple[int, int] = (10, 6),
    ) -> None:
        """建提示对象并绑好 ``<Enter>`` / ``<Leave>`` 等事件。"""
        self._widget = widget
        self._source: TextSource = text
        self._delay = max(0, int(delay))
        self._wraplength = max(80, int(wraplength))
        self._font = font
        self._padding = (int(padding[0]), int(padding[1]))

        self._after_id: Optional[str] = None
        self._tip: Optional[tk.Toplevel] = None
        self._label: Optional[tk.Label] = None
        self._shown = False
        self._alive = True

        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_press, add="+")
        widget.bind("<Destroy>", self._on_destroy, add="+")

    # --- 对外 ---
    @property
    def text(self) -> str:
        """当前提示文字；传的是函数时每次读都重新求值。"""
        return self._resolve()

    def set_text(self, text: TextSource) -> None:
        """换掉提示文字；正在显示时立刻按新文字重排。"""
        self._source = text
        if self._shown:
            self.show()

    def configure(self, **kwargs: Any) -> None:
        """只认 ``text=``，其余参数忽略（保留自定义控件常见的调用写法）。"""
        if "text" in kwargs:
            self.set_text(kwargs.pop("text"))

    def show(self) -> None:
        """立刻弹出提示，不等待 ``delay``。"""
        self._cancel()
        if not self._widget_alive():
            return
        text = self._resolve()
        if not text:
            return
        if not self._widget.winfo_viewable():
            return

        self._ensure_window()
        assert self._tip is not None and self._label is not None
        self._label.configure(
            text=text,
            font=get_font(self._font),
            bg=color_of(T.COLOR_CARD),
            fg=color_of(T.COLOR_TEXT),
            wraplength=self._wraplength,
            padx=self._padding[0],
            pady=self._padding[1],
        )
        self._tip.configure(bg=color_of(T.COLOR_BORDER))
        self._tip.update_idletasks()
        self._place()
        _round_corners(self._tip)
        self._tip.deiconify()
        self._tip.lift()
        self._tip.attributes("-topmost", True)
        self._shown = True

    def hide(self) -> None:
        """收起提示；没有显示时什么也不做。"""
        self._cancel()
        self._shown = False
        if self._tip is not None:
            with contextlib.suppress(tk.TclError):
                self._tip.withdraw()

    def destroy(self) -> None:
        """解绑事件并销毁提示窗口。"""
        self._alive = False
        self._cancel()
        self._shown = False
        if self._tip is not None:
            with contextlib.suppress(tk.TclError):
                self._tip.destroy()
        self._tip = None
        self._label = None

    # --- 内部 ---
    def _resolve(self) -> str:
        """求值文字来源。"""
        if callable(self._source):
            try:
                return str(self._source())
            except Exception:
                return ""
        return str(self._source)

    def _widget_alive(self) -> bool:
        """控件还在不在。"""
        if not self._alive:
            return False
        try:
            return bool(self._widget.winfo_exists())
        except tk.TclError:
            return False

    def _on_enter(self, _event: Optional[tk.Event] = None) -> None:
        """鼠标进入：延迟弹出。"""
        if not self._alive:
            return
        self._cancel()
        if self._delay <= 0:
            self.show()
        else:
            self._after_id = self._widget.after(self._delay, self.show)

    def _on_leave(self, _event: Optional[tk.Event] = None) -> None:
        """鼠标离开：取消或收起。"""
        if self._alive:
            self.hide()

    def _on_press(self, _event: Optional[tk.Event] = None) -> None:
        """按下控件时收起，避免提示挡着。"""
        if self._alive:
            self.hide()

    def _on_destroy(self, event: tk.Event) -> None:
        """控件销毁：清理提示窗口。"""
        if event.widget is self._widget:
            self.destroy()

    def _cancel(self) -> None:
        """取消还没到时的弹出任务。"""
        if self._after_id is not None:
            with contextlib.suppress(tk.TclError):
                self._widget.after_cancel(self._after_id)
            self._after_id = None

    def _ensure_window(self) -> None:
        """第一次显示时建窗口，之后复用。"""
        if self._tip is not None:
            try:
                if self._tip.winfo_exists():
                    return
            except tk.TclError:
                pass
        tip = tk.Toplevel(self._widget)
        tip.withdraw()
        tip.overrideredirect(True)
        tip.configure(bg=color_of(T.COLOR_BORDER))
        label = tk.Label(
            tip,
            text="",
            justify="left",
            anchor="w",
            bd=0,
            highlightthickness=0,
        )
        label.pack(padx=1, pady=1)
        self._tip = tip
        self._label = label

    def _place(self) -> None:
        """把提示放在控件下方居中；贴边时翻到上方或往回收。"""
        assert self._tip is not None
        tip = self._tip
        width = max(1, tip.winfo_reqwidth())
        height = max(1, tip.winfo_reqheight())
        x = self._widget.winfo_rootx() + self._widget.winfo_width() // 2 - width // 2
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 8

        screen_w = self._widget.winfo_screenwidth()
        screen_h = self._widget.winfo_screenheight()
        if x + width > screen_w - 4:
            x = screen_w - width - 4
        if x < 4:
            x = 4
        if y + height > screen_h - 4:
            y = self._widget.winfo_rooty() - height - 8
        if y < 4:
            y = 4
        tip.geometry(f"+{x}+{y}")
