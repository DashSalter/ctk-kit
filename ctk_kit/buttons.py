"""按钮：主按钮、次要按钮、危险按钮，以及卡片里用的微型按钮。

尺寸约定：
- 主按钮      38 高、圆角 9  —— 保存、搜索这一层的动作
- 次要按钮    30 高、圆角 8  —— 取消、刷新、选择目录
- 微型按钮    由文字宽度算出来 —— 卡片里的「复制 / 显示 / 详情」

所有按钮工厂只返回 ``ctk.CTkButton``，不负责 ``pack`` / ``grid``，摆位交给调用方。
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, Dict, Optional

import customtkinter as ctk

from . import tokens as T
from .theme import ColorToken, color_of

# 无参回调；CTk 的 command 就是这么调的，不会传入事件对象。
Command = Optional[Callable[[], None]]

# 同一套字体反复测量很浪费，按字体规格缓存度量对象。
# 注意：度量对象绑定在某个 Tk 解释器上，解释器销毁后需要清空（测试里有 fixture）。
_MEASURERS: Dict[tuple, tkfont.Font] = {}


def _measurer(font_spec: T.FontSpec) -> tkfont.Font:
    """返回 ``font_spec`` 对应的 ``tkfont.Font`` 度量对象，并按规格缓存。

    参数:
        font_spec: ``(字族, 字号)`` 或 ``(字族, 字号, "bold")``。

    返回:
        可用于 ``measure()`` / ``metrics()`` 的字体对象；相同规格返回同一实例。
    """
    key = tuple(font_spec)
    cached = _MEASURERS.get(key)
    if cached is None:
        cached = tkfont.Font(font=font_spec)
        _MEASURERS[key] = cached
    return cached


def primary_button(
    master: tk.Misc,
    text: str,
    command: Command = None,
    *,
    width: int = 120,
    height: int = 38,
    radius: int = T.RADIUS_SMALL + 1,
    font: T.FontSpec = T.FONT_BODY,
) -> ctk.CTkButton:
    """强调色主按钮（保存 / 搜索 / 立即备份）。

    参数:
        master: 父容器。
        text: 按钮文字。
        command: 点击回调，不接收参数。
        width: 宽度（像素），默认 120。
        height: 高度（像素），默认 38。
        radius: 圆角半径，默认 9。
        font: 字体规格，默认 :data:`tokens.FONT_BODY`。

    返回:
        尚未摆位的 ``CTkButton``。
    """
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
    master: tk.Misc,
    text: str,
    command: Command = None,
    *,
    width: int = 76,
    height: int = 30,
    font: T.FontSpec = T.FONT_SMALL,
    border: bool = False,
) -> ctk.CTkButton:
    """浅底次要按钮。

    ``border=True`` 时加一圈细边，适合「取消 / 清除」这类不该抢视线的动作。

    参数:
        master: 父容器。
        text: 按钮文字。
        command: 点击回调，不接收参数。
        width: 宽度（像素），默认 76。
        height: 高度（像素），默认 30；高度超过 30 时圆角自动加 1。
        font: 字体规格，默认 :data:`tokens.FONT_SMALL`。
        border: 是否显示 1px 边框。

    返回:
        尚未摆位的 ``CTkButton``。
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
    master: tk.Misc,
    text: str,
    command: Command = None,
    *,
    width: int = 76,
    height: int = 30,
    font: T.FontSpec = T.FONT_SMALL,
) -> ctk.CTkButton:
    """危险动作（删除 / 清空全部）：淡红底 + 红字，比纯红按钮安静。

    参数:
        master: 父容器。
        text: 按钮文字。
        command: 点击回调，不接收参数。
        width: 宽度（像素），默认 76。
        height: 高度（像素），默认 30。
        font: 字体规格，默认 :data:`tokens.FONT_SMALL`。

    返回:
        尚未摆位的 ``CTkButton``。
    """
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
    颜色默认取当前外观下的浅色/深色单值（经 :func:`theme.color_of`），
    所以深浅色切换后需要重新创建才能刷新。
    """

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        command: Command = None,
        *,
        bg: Optional[ColorToken] = None,
        hover: Optional[ColorToken] = None,
        fg: Optional[ColorToken] = None,
        font: T.FontSpec = T.FONT_TINY,
        padx: int = 10,
        pady: int = 3,
        radius: int = T.RADIUS_SMALL,
    ) -> None:
        """创建按文字宽度自适应的微型按钮。

        参数:
            master: 父容器。
            text: 按钮文字；宽度由它决定。
            command: 点击回调，不接收参数。
            bg: 底色，默认 ``tokens.COLOR_SOFT``。
            hover: 悬停底色，默认 ``tokens.COLOR_SOFT_HOVER``。
            fg: 文字颜色，默认 ``tokens.COLOR_TEXT``。
            font: 字体规格，默认 :data:`tokens.FONT_TINY`。
            padx: 文字左右各留的空白（像素），默认 10。
            pady: 文字上下各留的空白（像素），默认 3。
            radius: 圆角半径，默认 :data:`tokens.RADIUS_SMALL`。
        """
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

    def __init__(self, master: tk.Misc, text: str, command: Command = None) -> None:
        """创建灰字小按钮。

        参数:
            master: 父容器。
            text: 按钮文字。
            command: 点击回调，不接收参数。
        """
        super().__init__(
            master,
            text,
            command,
            fg=color_of(T.COLOR_MUTED),
            padx=8,
            pady=2,
            radius=T.RADIUS_SMALL - 2,
        )
