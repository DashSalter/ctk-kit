"""按钮：主按钮、次要按钮、危险按钮，以及卡片里用的微型按钮。

尺寸约定：
- 主按钮      38 高、圆角 9  —— 保存、搜索这一层的动作
- 次要按钮    30 高、圆角 8  —— 取消、刷新、选择目录
- 微型按钮    由文字宽度算出来 —— 卡片里的「复制 / 显示 / 详情」
"""

from __future__ import annotations

import tkinter.font as tkfont

import customtkinter as ctk

from . import tokens as T
from .theme import color_of

# 同一套字体反复测量很浪费，按字体规格缓存度量对象
_MEASURERS: dict[tuple, tkfont.Font] = {}


def _measurer(font_spec) -> tkfont.Font:
    key = tuple(font_spec)
    cached = _MEASURERS.get(key)
    if cached is None:
        cached = tkfont.Font(font=font_spec)
        _MEASURERS[key] = cached
    return cached


def primary_button(
    master,
    text: str,
    command=None,
    *,
    width: int = 120,
    height: int = 38,
    radius: int = T.RADIUS_SMALL + 1,
    font=T.FONT_BODY,
) -> ctk.CTkButton:
    """强调色主按钮（保存 / 搜索 / 立即备份）。"""
    return ctk.CTkButton(
        master,
        text=text,
        width=width,
        height=height,
        corner_radius=radius,
        font=font,
        fg_color=T.COLOR_ACCENT,
        hover_color=T.COLOR_ACCENT_HOVER,
        text_color=T.COLOR_ACCENT_TEXT,
        command=command,
    )


def soft_button(
    master,
    text: str,
    command=None,
    *,
    width: int = 76,
    height: int = 30,
    font=T.FONT_SMALL,
    border: bool = False,
) -> ctk.CTkButton:
    """浅底次要按钮。

    ``border=True`` 时加一圈细边，适合「取消 / 清除」这类不该抢视线的动作。
    """
    return ctk.CTkButton(
        master,
        text=text,
        width=width,
        height=height,
        corner_radius=T.RADIUS_SMALL if height <= 30 else T.RADIUS_SMALL + 1,
        font=font,
        fg_color=T.COLOR_SOFT,
        hover_color=T.COLOR_SOFT_HOVER,
        text_color=T.COLOR_TEXT,
        border_width=1 if border else 0,
        border_color=T.COLOR_BORDER if border else T.COLOR_SOFT,
        command=command,
    )


def danger_button(
    master,
    text: str,
    command=None,
    *,
    width: int = 76,
    height: int = 30,
    font=T.FONT_SMALL,
) -> ctk.CTkButton:
    """危险动作（删除 / 清空全部）：淡红底 + 红字，比纯红按钮安静。"""
    return ctk.CTkButton(
        master,
        text=text,
        width=width,
        height=height,
        corner_radius=T.RADIUS_SMALL,
        font=font,
        fg_color=T.COLOR_DANGER_SOFT,
        hover_color=T.COLOR_DANGER_SOFT_HOVER,
        text_color=T.COLOR_DANGER,
        command=command,
    )


class FlatButton(ctk.CTkButton):
    """卡片里的小号圆角按钮（复制 / 显示 / 详情）。

    宽度按文字实测宽度算出来，既不浪费横向空间，也不会把文字挤掉。
    """

    def __init__(
        self,
        master,
        text: str,
        command=None,
        *,
        bg=None,
        hover=None,
        fg=None,
        font=T.FONT_TINY,
        padx: int = 10,
        pady: int = 3,
        radius: int = T.RADIUS_SMALL,
    ):
        measure = _measurer(font)
        super().__init__(
            master,
            text=text,
            command=command,
            width=measure.measure(text) + padx * 2,
            height=measure.metrics("linespace") + pady * 2,
            corner_radius=radius,
            font=font,
            fg_color=bg if bg is not None else color_of(T.COLOR_SOFT),
            hover_color=hover if hover is not None else color_of(T.COLOR_SOFT_HOVER),
            text_color=fg if fg is not None else color_of(T.COLOR_TEXT),
        )


class SoftButton(FlatButton):
    """更安静的小按钮：灰字、更小的内边距（复制 / 显示 / 收起）。"""

    def __init__(self, master, text: str, command=None):
        super().__init__(
            master,
            text,
            command,
            fg=color_of(T.COLOR_MUTED),
            padx=8,
            pady=2,
            radius=T.RADIUS_SMALL - 2,
        )
