"""勾选框与单选圆点：用 Pillow 画抗锯齿的指示符。

ttkbootstrap 的 ``Checkbutton`` / ``Radiobutton`` 指示符是**图片**：它把资源里的
PNG 重新着色后交给 ttk 的 image element。Tk 自己用 canvas 画圆环时不做抗锯齿，
圆形边缘就会有一格一格的阶梯，这里照同样的思路，用 Pillow 在 4 倍尺寸上画好再缩回来。
"""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Any, Callable, Optional

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .paint import cached
from .theme import color_of

try:  # Pillow 是可选依赖
    from PIL import Image, ImageDraw, ImageTk

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

#: 超采样倍数。
_SCALE = 4


def _bg_of(master: tk.Misc) -> str:
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
def _round_image(size: int, checked: bool, color: str, track: str, foreground: str):
    """圆点：未选中是描边圆环，选中是实心圆加一个浅色内点。"""
    scale = _SCALE
    total = size * scale
    image = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pad = 1 * scale
    box = (pad, pad, total - pad - 1, total - pad - 1)
    if checked:
        pen.ellipse(box, fill=color)
        inner = total * 0.2
        center = total / 2
        pen.ellipse(
            (center - inner, center - inner, center + inner, center + inner),
            fill=foreground,
        )
    else:
        pen.ellipse(box, outline=track, width=2 * scale)
    return image.resize((size, size), Image.LANCZOS)


@cached
def _square_image(
    size: int, checked: bool, color: str, track: str, foreground: str
):
    """勾选框：未选中是圆角方框，选中是实心方块加一个白色对勾。"""
    scale = _SCALE
    total = size * scale
    image = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pad = 1 * scale
    box = (pad, pad, total - pad - 1, total - pad - 1)
    radius = max(2, int(total * 0.22))
    if checked:
        pen.rounded_rectangle(box, radius=radius, fill=color)
        width = max(2, int(total * 0.09))
        pen.line(
            [
                (total * 0.27, total * 0.52),
                (total * 0.44, total * 0.69),
                (total * 0.75, total * 0.33),
            ],
            fill=foreground,
            width=width,
            joint="curve",
        )
    else:
        pen.rounded_rectangle(box, radius=radius, outline=track, width=2 * scale)
    return image.resize((size, size), Image.LANCZOS)


class _Mark(ctk.CTkFrame):
    """勾选/单选共用的底座：左边一个指示符，右边一行字。"""

    _shape = "round"

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        *,
        width: int,
        height: int,
        command: Optional[Callable[[], None]],
        font: Any,
    ) -> None:
        """建底座：canvas 放指示符，label 放文字。"""
        super().__init__(master, fg_color="transparent")
        self._size = max(12, int(height))
        self._command = command
        self._bg = _bg_of(self)
        self._photo = None

        self._canvas = tk.Canvas(
            self,
            width=self._size,
            height=self._size,
            bg=self._bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._canvas.pack(side="left")
        self._label = ctk.CTkLabel(
            self,
            text=text,
            font=font,
            text_color=T.COLOR_TEXT,
            fg_color="transparent",
            cursor="hand2",
        )
        self._label.pack(side="left", padx=(8, 0))
        for widget in (self._canvas, self._label):
            widget.bind("<Button-1>", self._on_click)

    # ------------------------------------------------------------ 子类实现
    def _is_checked(self) -> bool:
        """子类给：当前是否选中。"""
        raise NotImplementedError

    def _set_checked(self, value: bool) -> None:
        """子类给：写入选中状态。"""
        raise NotImplementedError

    # ------------------------------------------------------------ 公共
    def _on_click(self, _event: Optional[tk.Event] = None) -> None:
        """点击：切换选中状态并回调。"""
        self._set_checked(not self._is_checked())
        self._refresh()
        if self._command is not None:
            self._command()

    def _refresh(self) -> None:
        """重画指示符。"""
        self._canvas.delete("all")
        checked = self._is_checked()
        color = color_of(T.COLOR_ACTIVE)
        track = color_of(T.COLOR_BORDER_STRONG)
        foreground = color_of(T.COLOR_ACCENT_TEXT)
        if not _HAS_PIL:
            self._draw_plain(checked, color, track, foreground)
            return
        make = _round_image if self._shape == "round" else _square_image
        self._photo = ImageTk.PhotoImage(
            make(self._size, checked, color, track, foreground)
        )
        self._canvas.create_image(self._size / 2, self._size / 2, image=self._photo)

    def _draw_plain(self, checked: bool, color: str, track: str, fg: str) -> None:
        """没装 Pillow 时的退路：canvas 画圆/方框（边缘会有阶梯）。"""
        canvas = self._canvas
        size = self._size
        pad = 2
        box = (pad, pad, size - pad, size - pad)
        if self._shape == "round":
            if checked:
                canvas.create_oval(*box, fill=color, outline="")
                inner = size * 0.2
                canvas.create_oval(
                    size / 2 - inner,
                    size / 2 - inner,
                    size / 2 + inner,
                    size / 2 + inner,
                    fill=fg,
                    outline="",
                )
            else:
                canvas.create_oval(*box, outline=track, width=2)
        else:
            if checked:
                canvas.create_rectangle(*box, fill=color, outline="")
            else:
                canvas.create_rectangle(*box, outline=track, width=2)

    def configure(self, **kwargs: Any) -> None:
        """支持 ``configure(command=...)``，和 CTk 控件的用法一致。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if kwargs:
            super().configure(**kwargs)
            self._bg = _bg_of(self)
            self._canvas.configure(bg=self._bg)
            self._refresh()


class Check(_Mark):
    """勾选框：实心圆角方块 + 白色对勾。"""

    _shape = "square"

    def __init__(
        self,
        master: tk.Misc,
        text: str = "",
        command: Optional[Callable[[], None]] = None,
        *,
        width: int = 18,
        height: int = 18,
        variable: Optional[tk.IntVar] = None,
        font: Any = None,
    ) -> None:
        """建勾选框；``get()`` 返回 0/1，和 ``CTkCheckBox`` 一致。"""
        self._variable = variable or tk.IntVar(value=0)
        super().__init__(
            master,
            text,
            width=width,
            height=height,
            command=command,
            font=font or get_font(T.FONT_BODY),
        )
        self._variable.trace_add("write", lambda *_: self._refresh())
        self._refresh()

    def _is_checked(self) -> bool:
        return bool(self._variable.get())

    def _set_checked(self, value: bool) -> None:
        self._variable.set(1 if value else 0)

    def get(self) -> int:
        """0 / 1。"""
        return 1 if self._is_checked() else 0

    def select(self) -> None:
        """勾上。"""
        self._set_checked(True)
        self._refresh()

    def deselect(self) -> None:
        """取消勾选。"""
        self._set_checked(False)
        self._refresh()


class Radio(_Mark):
    """单选项：圆形指示符，多个共享同一个 ``StringVar`` 才互斥。"""

    _shape = "round"

    def __init__(
        self,
        master: tk.Misc,
        text: str = "",
        value: str = "",
        *,
        variable: Optional[tk.StringVar] = None,
        command: Optional[Callable[[], None]] = None,
        width: int = 18,
        height: int = 18,
        font: Any = None,
    ) -> None:
        """建单选项；``value`` 是选中时写进变量的值。"""
        self._value = value if value else text
        self._variable = variable or tk.StringVar()
        super().__init__(
            master,
            text,
            width=width,
            height=height,
            command=command,
            font=font or get_font(T.FONT_BODY),
        )
        self._variable.trace_add("write", lambda *_: self._refresh())
        self._refresh()

    def _is_checked(self) -> bool:
        return self._variable.get() == self._value

    def _set_checked(self, value: bool) -> None:
        if value:
            self._variable.set(self._value)

    def select(self) -> None:
        """选中这一项。"""
        self._set_checked(True)
        self._refresh()
