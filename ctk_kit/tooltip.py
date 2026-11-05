"""悬浮提示：鼠标停在控件上时，在下方弹一行说明。

用法::

    from ctk_kit import Tooltip

    Tooltip(button, "保存当前草稿")
    Tooltip(entry, lambda: f"当前长度 {len(entry.get())}", delay=300)

提示窗口是无边框的 ``Toplevel``，不抢焦点、不进任务栏；鼠标移开、按下
控件或控件被销毁时自动收起。文字如果是可调用对象，每次弹出前现取，
适合放「当前值」这类会变的内容。

提示的配色和下拉面板、右键菜单同一套（面板底、正文色），
不用系统毛玻璃——一小块浮层糊了背景反而看不清。圆角在 Windows 上裁出来，
其他平台退回直角，不影响功能。
"""

from __future__ import annotations

import contextlib
import sys
import time
import tkinter as tk
from typing import Any, Callable, Optional, Union

import customtkinter as ctk

from . import tokens as T
from .popup import round_window_corners
from .fonts import get_font
from .theme import color_of

__all__ = ["Tooltip"]

TextSource = Union[str, Callable[[], str]]

# 提示只做淡入：鼠标移开时它得立刻让路，再做淡出反而挡视线
_FADE_MS = 120
_FADE_STEP = 16

# 底色和右键菜单（context_menu._MENU_BG）、下拉面板（dropdown._PANEL_BG）
# 同一个值：比 COLOR_CARD 浅一档，一小块浮层才不会糊成黑块。
_TIP_BG = "#2B2B2B"


def _round_corners(window: tk.Misc, radius: int = 6) -> None:
    """把无边框窗口裁成圆角，公共逻辑在 :mod:`ctk_kit.popup`。"""
    round_window_corners(window, radius)


class Tooltip:
    """挂在任意控件上的悬停提示。

    参数:
        widget: 要挂提示的控件。
        text: 提示文字；也可以传一个返回字符串的函数，每次显示前调用。
        delay: 鼠标停多久后弹出（毫秒），默认 500。
        wraplength: 文字超过这个宽度就换行（像素），默认 300。
        font: 提示文字字体，默认正文字号再大一档（14px）。
        padding: ``(左右, 上下)`` 的内边距，默认 ``(14, 10)``。

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
        font: T.FontSpec = (T.FONT_NAME, 14),
        padding: tuple[int, int] = (14, 10),
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
        self._fade_job: Optional[str] = None
        self._fade_started: float = 0.0
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
            bg=_TIP_BG,
            fg=color_of(T.COLOR_TEXT),
            wraplength=self._wraplength,
            padx=self._padding[0],
            pady=self._padding[1],
        )
        self._tip.configure(fg_color=_TIP_BG)
        self._tip.update_idletasks()
        self._place()
        _round_corners(self._tip)
        with contextlib.suppress(tk.TclError):
            self._tip.attributes("-alpha", 0.0)
        self._tip.deiconify()
        self._tip.lift()
        self._tip.attributes("-topmost", True)
        self._shown = True
        self._start_fade_in()

    def hide(self) -> None:
        """收起提示；没有显示时什么也不做。"""
        self._cancel()
        self._cancel_fade()
        self._shown = False
        if self._tip is not None:
            with contextlib.suppress(tk.TclError):
                self._tip.withdraw()

    def destroy(self) -> None:
        """解绑事件并销毁提示窗口。"""
        self._alive = False
        self._cancel()
        self._cancel_fade()
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

    def _cancel_fade(self) -> None:
        """取消还没跑完的淡入。"""
        if self._fade_job is not None:
            with contextlib.suppress(Exception):
                self._widget.after_cancel(self._fade_job)
            self._fade_job = None

    def _start_fade_in(self) -> None:
        """从透明淡到不透明；窗口不支持 alpha 就直接全亮。"""
        tip = self._tip
        if tip is None:
            return
        self._cancel_fade()
        self._fade_started = time.perf_counter()
        self._fade_job = self._widget.after(1, self._fade_step)

    def _fade_step(self) -> None:
        self._fade_job = None
        tip = self._tip
        if tip is None:
            return
        try:
            alive = bool(tip.winfo_exists())
        except tk.TclError:
            return
        if not alive or not self._shown:
            return
        ratio = (time.perf_counter() - self._fade_started) / (_FADE_MS / 1000.0)
        done = ratio >= 1.0
        eased = 1.0 if done else 1.0 - (1.0 - ratio) ** 3
        with contextlib.suppress(tk.TclError):
            tip.attributes("-alpha", 1.0 if done else round(eased, 3))
        if not done:
            self._fade_job = self._widget.after(_FADE_STEP, self._fade_step)

    def _ensure_window(self) -> None:
        """第一次显示时建窗口，之后复用。"""
        if self._tip is not None:
            try:
                if self._tip.winfo_exists():
                    return
            except tk.TclError:
                pass
        # 和下拉面板、右键菜单同一路：整块铺面板底色，不用系统毛玻璃——
        # 提示只是一小块浮层，糊了背景反而看不清。
        tip = ctk.CTkToplevel(self._widget)
        tip.withdraw()
        tip.overrideredirect(True)
        tip.configure(fg_color=_TIP_BG)
        label = tk.Label(
            tip,
            text="",
            justify="left",
            anchor="w",
            bd=0,
            highlightthickness=0,
            bg=_TIP_BG,
            fg=color_of(T.COLOR_TEXT),
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
