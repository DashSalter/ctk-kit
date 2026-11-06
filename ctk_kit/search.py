"""搜索框：左侧放大镜、右侧清空按钮，输入带防抖。

用法::

    from ctk_kit import SearchBox

    search = SearchBox(page, placeholder="搜索组件", command=filter_rows)
    search.pack(fill="x", padx=16, pady=12)

    search.get()      # 当前文字
    search.clear()    # 清空并触发一次 command

默认停止输入 300ms 后回调，避免每敲一个字都查一遍；按回车会立刻回调。
放大镜和清空按钮都用 Pillow 在 4 倍尺寸上画，边缘没有阶梯。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional

import customtkinter as ctk

from . import tokens as T
from .context_menu import attach_edit_menu
from .fonts import get_font
from .paint import cached
from .sugar import Bindable, Enablable
from .theme import color_of

try:  # Pillow 是可选依赖
    from PIL import Image, ImageDraw, ImageTk

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

__all__ = ["SearchBox"]

SearchCommand = Optional[Callable[[str], None]]

#: 放大镜图标边长（逻辑像素）。
_ICON_SIZE = 18
#: 超采样倍数。
_SCALE = 4


def _parent_bg(master: tk.Misc) -> str:
    """给 canvas 找一个实际背景色。"""
    try:
        value = master.cget("fg_color")
    except Exception:  # noqa: BLE001
        value = None
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return color_of(value)
    if isinstance(value, str) and value and value != "transparent":
        return value
    return color_of(T.COLOR_CARD)


@cached
def _magnifier(color: str):
    """画一个放大镜：圆环 + 斜柄。"""
    scale = _SCALE
    size = _ICON_SIZE
    image = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pen.ellipse(
        (3 * scale, 2 * scale, 12 * scale, 11 * scale),
        outline=color,
        width=2 * scale,
    )
    pen.line(
        (10 * scale, 9 * scale, 15 * scale, 14 * scale),
        fill=color,
        width=2 * scale,
    )
    return image.resize((size, size), Image.LANCZOS)


class SearchBox(Enablable, Bindable, ctk.CTkFrame):
    """带放大镜和清空按钮的搜索输入框。

    参数:
        master: 父容器。
        placeholder: 未输入时的占位文字。
        command: 搜索回调，参数是当前文字；默认 300ms 防抖。
        width: 整体宽度，默认 240。
        height: 高度，默认 38。
        delay: 防抖毫秒数，默认 300；传 0 表示每次输入都回调。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        get(): 当前文字。
        set(text): 写入文字，不触发回调。
        clear(): 清空并触发一次回调。
        search(): 立刻触发一次回调（不等防抖）。
        focus(): 让输入框获得焦点。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        placeholder: str = "搜索",
        command: SearchCommand = None,
        width: int = 240,
        height: int = 38,
        delay: int = 300,
        **kwargs: Any,
    ) -> None:
        """建搜索框；``command`` 可以之后用 ``configure`` 再挂。"""
        kwargs.setdefault("fg_color", T.COLOR_INPUT)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", T.COLOR_BORDER_INPUT)
        kwargs.setdefault("corner_radius", T.RADIUS_SMALL)
        kwargs.setdefault("height", height)
        super().__init__(master, width=width, **kwargs)
        self.pack_propagate(False)

        self._command = command
        self._delay = max(0, int(delay))
        self._job: Optional[str] = None
        self._icon_photo = None

        self._icon = tk.Canvas(
            self,
            width=_ICON_SIZE,
            height=_ICON_SIZE,
            bg=_parent_bg(self),
            highlightthickness=0,
            bd=0,
        )
        self._icon.pack(side="left", padx=(10, 2))
        self._paint_icon()

        self._entry = ctk.CTkEntry(
            self,
            fg_color="transparent",
            border_width=0,
            corner_radius=0,
            height=max(24, height - 6),
            font=get_font(T.FONT_BODY),
            text_color=T.COLOR_TEXT,
            placeholder_text=placeholder,
            placeholder_text_color=T.COLOR_FAINT,
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, 2), pady=2)
        attach_edit_menu(self._entry)
        self._entry.bind("<KeyRelease>", self._on_key)
        self._entry.bind("<Return>", lambda _e: self.search())

        self._clear = ctk.CTkButton(
            self,
            text="×",
            width=22,
            height=22,
            corner_radius=11,
            fg_color="transparent",
            hover_color=T.COLOR_HOVER_FAINT,
            text_color=T.COLOR_MUTED,
            font=get_font((T.FONT_NAME, 14)),
            command=self.clear,
        )
        self._clear.pack(side="right", padx=(0, 8))

    # --- 对外 ---
    def get(self) -> str:
        """当前文字。"""
        return self._entry.get()

    def set(self, text: str, *, notify: bool = False) -> None:
        """写入文字；``notify=True`` 时也触发回调。"""
        self._entry.delete(0, "end")
        if text:
            self._entry.insert(0, text)
        if notify:
            self._fire()

    def clear(self) -> None:
        """清空并立刻触发一次回调。"""
        self._entry.delete(0, "end")
        self._fire()

    def search(self) -> None:
        """立刻触发回调，不等防抖。"""
        self._cancel()
        self._fire()

    def focus(self) -> None:
        """让输入框获得焦点。"""
        self._entry.focus_set()

    def _apply_enabled(self, enabled: bool) -> None:
        """禁用时输入框和清除按钮都不响应。"""
        try:
            self._entry.configure(state="normal" if enabled else "disabled")
            self._clear.configure(state="normal" if enabled else "disabled")
        except (tk.TclError, ValueError):
            return

    def is_enabled(self) -> bool:
        """当前是否可输入。"""
        try:
            return str(self._entry.cget("state")) != "disabled"
        except Exception:  # noqa: BLE001 - 窗口销毁中
            return True

    def set_text(self, text: Any) -> None:
        """同 :meth:`set`。"""
        self.set("" if text is None else str(text))

    def get_text(self) -> str:
        """读回文字，等价于 ``get()``。"""
        return self.get()

    def configure(self, **kwargs: Any) -> None:
        """``command=`` / ``placeholder=`` 换回调或占位文字。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "placeholder" in kwargs:
            self._entry.configure(placeholder_text=kwargs.pop("placeholder"))
        return super().configure(**kwargs)

    # --- 内部 ---
    def _on_key(self, _event: Optional[tk.Event] = None) -> None:
        """按键：重置防抖计时器。"""
        self._cancel()
        if self._delay <= 0:
            self._fire()
        else:
            self._job = self.after(self._delay, self._fire)

    def _cancel(self) -> None:
        """取消还没到点的防抖任务。"""
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:  # noqa: BLE001
                pass
            self._job = None

    def _fire(self) -> None:
        """到点：回调当前文字。"""
        self._job = None
        if self._command is not None:
            self._command(self.get())

    def _paint_icon(self) -> None:
        """画放大镜；主题切换后颜色会跟着变。"""
        color = color_of(T.COLOR_MUTED)
        self._icon.delete("all")
        if _HAS_PIL:
            self._icon_photo = ImageTk.PhotoImage(_magnifier(color))
            self._icon.create_image(
                _ICON_SIZE / 2, _ICON_SIZE / 2, image=self._icon_photo
            )
            return
        self._icon.create_oval(3, 2, 12, 11, outline=color, width=2)
        self._icon.create_line(10, 9, 15, 14, fill=color, width=2)
