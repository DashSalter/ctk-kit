"""状态栏：窗口底部一条，左边状态、右边补充信息。

用法::

    from ctk_kit import StatusBar

    bar = StatusBar(root, text="就绪", right="12 项")
    bar.pack(side="bottom", fill="x")

    bar.set_text("正在保存…", tone="warning")
    bar.set_right("已保存")

``tone`` 支持 ``neutral`` / ``success`` / ``warning`` / ``danger``，
只影响左边的小圆点。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Optional

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .paint import animate_color
from .styles import style_of

__all__ = ["StatusBar"]

_TONES = {
    "neutral": T.COLOR_MUTED,
    "success": T.COLOR_SUCCESS,
    "warning": T.COLOR_WARNING,
    "danger": T.COLOR_DANGER,
}


def _tone_color(tone: str, mode: Optional[str] = None) -> str:
    """取圆点颜色；未知 tone 退回 ``neutral``。"""
    return _TONES.get(tone, T.COLOR_MUTED)


class StatusBar(ctk.CTkFrame):
    """一条横向状态栏。

    参数:
        master: 父容器。
        text: 左侧文字，默认「就绪」。
        tone: 左侧圆点颜色，默认 ``neutral``。
        right: 右侧文字，默认空。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        set_text(text, tone=None): 改左侧文字和圆点。
        set_right(text): 改右侧文字。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        text: str = "就绪",
        tone: str = "neutral",
        right: str = "",
        **kwargs: Any,
    ) -> None:
        """建状态栏；高度固定 30。"""
        super().__init__(
            master,
            fg_color=T.COLOR_SOFT,
            corner_radius=0,
            height=30,
            **kwargs,
        )
        self.pack_propagate(False)

        self._tone = tone
        self._dot = ctk.CTkLabel(
            self,
            text="●",
            font=get_font(T.FONT_BADGE),
            text_color=_TONES.get(tone, T.COLOR_MUTED),
        )
        self._dot.pack(side="left", padx=(12, 6))

        self._label = ctk.CTkLabel(
            self,
            text=text,
            font=get_font(T.FONT_SMALL),
            text_color=T.COLOR_TEXT,
            anchor="w",
        )
        self._label.pack(side="left")

        self._right = ctk.CTkLabel(
            self,
            text=right,
            font=get_font(T.FONT_SMALL),
            text_color=T.COLOR_MUTED,
            anchor="e",
        )
        self._right.pack(side="right", padx=12)

    # --- 对外 ---
    def set_text(self, text: str, tone: Optional[str] = None) -> None:
        """改左侧文字；``tone`` 不传就保持原色。"""
        self._label.configure(text=text)
        if tone is not None:
            old = _tone_color(self._tone)
            self._tone = tone
            # 圆点颜色做一次短渐变，级别切换时不会硬跳
            animate_color(self._dot, "text_color", old, _tone_color(tone), 120)

    def set_right(self, text: str) -> None:
        """改右侧文字。"""
        self._right.configure(text=text)

    def apply_theme(self, mode: Optional[str] = None) -> None:
        """按当前（或指定）外观刷状态栏颜色，不重建控件。

        参数:
            mode: ``"light"`` / ``"dark"`` / ``"system"``；不传取当前外观。
        """
        self.configure(**style_of("statusbar", "shell", mode))
        self._label.configure(**style_of("statusbar", "text", mode))
        self._right.configure(**style_of("statusbar", "right", mode))
        self._dot.configure(text_color=_tone_color(self._tone, mode))
