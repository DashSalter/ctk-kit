"""徽标与标签：只读的状态块，用来标分类、计数或状态。

用法::

    from ctk_kit import Badge, Tag

    Badge(card, "已同步", color="success")          # 淡绿底、绿字
    Badge(card, "3", color="danger", variant="solid")  # 红底白字计数
    Badge(card, dot=True, color="warning")           # 一个状态点
    Tag(card, "草稿", variant="outline")             # 描边标签

``Tag`` 就是 ``Badge`` 的别名，两个名字导出的都是同一个类。

颜色跟着当前外观走：``soft`` 用主色和卡片底混出来的淡底，``solid`` 用
主色实底，``outline`` 只描边。文字一般是单行，太长会撑宽，不会自动换行。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Optional, Union

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font

__all__ = ["Badge", "Tag"]

ColorSpec = Union[str, T.ColorPair]

#: 语义名到颜色令牌。
_COLOR_TOKENS = {
    "accent": T.COLOR_ACCENT,
    "primary": T.COLOR_ACCENT,
    "success": T.COLOR_SUCCESS,
    "warning": T.COLOR_WARNING,
    "danger": T.COLOR_DANGER,
    "error": T.COLOR_DANGER,
    "info": T.COLOR_ACCENT,
    "neutral": T.COLOR_MUTED,
}


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    """``#rrggbb`` 转 ``(r, g, b)``。"""
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _mix(fore: str, back: str, ratio: float) -> str:
    """按 ``ratio`` 把 ``fore`` 混进 ``back``，返回 ``#rrggbb``。"""
    fr, fg, fb = _hex_to_rgb(fore)
    br, bg, bb = _hex_to_rgb(back)
    r = round(fr * ratio + br * (1 - ratio))
    g = round(fg * ratio + bg * (1 - ratio))
    b = round(fb * ratio + bb * (1 - ratio))
    return f"#{r:02x}{g:02x}{b:02x}"


def _pair_mix(color: T.ColorPair, base: T.ColorPair, ratio: float) -> T.ColorPair:
    """深浅两套颜色分别混合，得到可以直接交给 CTk 的色对。"""
    return (_mix(color[0], base[0], ratio), _mix(color[1], base[1], ratio))


def _is_hex(value: str) -> bool:
    """是不是 ``#rrggbb``；自定义颜色名不能参与混合。"""
    return len(value) == 7 and value.startswith("#")


def _resolve_color(color: ColorSpec) -> T.ColorPair:
    """语义名 / 单色 / 色对，统一成 ``(light, dark)``。"""
    if isinstance(color, tuple):
        return color
    token = _COLOR_TOKENS.get(color)
    if token is not None:
        return token
    return (color, color)


class Badge(ctk.CTkFrame):
    """只读徽标：状态、分类或计数。

    参数:
        master: 父容器。
        text: 显示文字；``dot=True`` 时忽略。
        color: 语义名（``"accent"`` / ``"success"`` / ``"warning"`` /
            ``"danger"`` / ``"info"`` / ``"neutral"``）、单个颜色，
            或 ``(浅色, 深色)`` 色对。
        variant: ``"soft"``（淡底，默认）/ ``"solid"``（实底）/
            ``"outline"``（描边）。
        size: ``"sm"``（20 高、小一号字）或 ``"md"``（24 高，默认）。
        dot: 只画一个圆点，不显示文字。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        set_text(text): 换文字；``dot=True`` 时无效果。
        configure(text=...): 同 ``set_text``。
    """

    def __init__(
        self,
        master: tk.Misc,
        text: str = "",
        *,
        color: ColorSpec = "accent",
        variant: str = "soft",
        size: str = "md",
        dot: bool = False,
        **kwargs: Any,
    ) -> None:
        """建一个徽标；``text`` 为空且 ``dot=False`` 时显示一个空块。"""
        height = 20 if size == "sm" else 24
        padding = 7 if size == "sm" else 9
        font = T.FONT_TINY if size == "sm" else T.FONT_SMALL
        palette = _resolve_color(color)

        if dot:
            kwargs.setdefault("width", height)
            kwargs.setdefault("height", height)
            kwargs.setdefault("corner_radius", 999)
            kwargs.setdefault("fg_color", palette)
            kwargs.setdefault("border_width", 0)
        else:
            if variant == "solid":
                fg_color = palette
                text_color = "#1f1300" if color == "warning" else "#ffffff"
                border_width = 0
                border_color = palette
            elif variant == "outline":
                fg_color = "transparent"
                text_color = palette
                border_width = 1
                border_color = palette
            else:
                if all(_is_hex(part) for part in palette):
                    fg_color = _pair_mix(palette, T.COLOR_CARD, 0.14)
                else:
                    fg_color = T.COLOR_SOFT
                text_color = palette
                border_width = 0
                border_color = palette
            kwargs.setdefault("width", 1)
            kwargs.setdefault("height", height)
            kwargs.setdefault("corner_radius", height // 2)
            kwargs.setdefault("fg_color", fg_color)
            kwargs.setdefault("border_width", border_width)
            kwargs.setdefault("border_color", border_color)

        super().__init__(master, **kwargs)
        self._dot = dot
        self._padding = padding
        self._label: Optional[ctk.CTkLabel] = None

        if not dot:
            self._label = ctk.CTkLabel(
                self,
                text=text,
                font=get_font(font),
                text_color=text_color,
                fg_color="transparent",
            )
            self._label.pack(padx=padding, pady=0)
            self._fit_width()

    # --- 对外 ---
    def set_text(self, text: str) -> None:
        """换文字；圆点徽标没有文字，调用会被忽略。"""
        if self._label is not None:
            self._label.configure(text=text)
            self._fit_width()

    def configure(self, **kwargs: Any) -> None:
        """``text=`` 转发给内部文字，其余交给 ``CTkFrame``。"""
        if "text" in kwargs:
            self.set_text(kwargs.pop("text"))
        return super().configure(**kwargs)

    # --- 内部 ---
    def _fit_width(self) -> None:
        """按文字宽度把外层 frame 收到刚好包住文字。"""
        if self._label is None:
            return
        self.update_idletasks()
        self.configure(width=self._label.winfo_reqwidth() + self._padding * 2)


#: ``Tag`` 与 ``Badge`` 是同一个类，只是语义上更适合分类标签。
Tag = Badge
