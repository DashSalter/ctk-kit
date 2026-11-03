"""外壳控件的样式表：颜色集中定义，切主题时只 configure、不重建。

样式值用 :mod:`ctk_kit.tokens` 里的 ``(浅色, 深色)`` 令牌写成；控件在
``apply_theme()`` 里按当前外观解析成单个颜色，直接传给 ``configure``。
这样切主题时外壳控件（侧边栏、卡片、状态栏）可以原地换色，只有页面内容
才需要重建。

用法::

    from ctk_kit.styles import style_of

    sheet = style_of("card", "shell")      # 当前外观
    frame.configure(**sheet)

``style_of`` 的第三个参数可以显式指定 ``"light"`` / ``"dark"``；不传就按
``customtkinter.get_appearance_mode()`` 取当前外观。
"""

from __future__ import annotations

from typing import Dict, Optional, Union

from . import tokens as T

__all__ = ["SHEETS", "is_dark", "pick", "style_of"]

#: 一个样式值：单色字符串，或 ``(浅色, 深色)`` 令牌。
ColorValue = Union[str, T.ColorPair]

#: 控件名 -> 状态 -> ``configure`` 参数。状态名由各控件自己定义。
SHEETS: Dict[str, Dict[str, Dict[str, ColorValue]]] = {
    "sidebar": {
        "shell": {"fg_color": T.COLOR_BG},
        "side": {"fg_color": T.COLOR_SIDE, "bg_color": T.COLOR_SIDE},
        "content": {"fg_color": T.COLOR_BG, "bg_color": T.COLOR_BG},
        "title": {"text_color": T.COLOR_TEXT, "bg_color": T.COLOR_SIDE},
        "subtitle": {"text_color": T.COLOR_MUTED, "bg_color": T.COLOR_SIDE},
        "nav_normal": {
            "fg_color": "transparent",
            "bg_color": T.COLOR_SIDE,
            "hover_color": T.COLOR_SOFT,
            "text_color": T.COLOR_MUTED,
        },
        "nav_active": {
            "fg_color": T.COLOR_ACCENT,
            "bg_color": T.COLOR_SIDE,
            "hover_color": T.COLOR_ACCENT_HOVER,
            "text_color": T.COLOR_ACCENT_TEXT,
        },
        "bottom": {
            "fg_color": T.COLOR_SOFT,
            "hover_color": T.COLOR_SOFT_HOVER,
            "text_color": T.COLOR_TEXT,
        },
    },
    "card": {
        "shell": {"fg_color": T.COLOR_CARD, "border_color": T.COLOR_BORDER},
        "title": {"text_color": T.COLOR_TEXT},
    },
    "statusbar": {
        "shell": {"fg_color": T.COLOR_SOFT},
        "text": {"text_color": T.COLOR_TEXT},
        "right": {"text_color": T.COLOR_MUTED},
    },
}


def is_dark(mode: Optional[str] = None) -> bool:
    """``mode`` 是不是深色；``None`` / ``"system"`` 取当前全局外观。"""
    if mode is None or str(mode).lower() == "system":
        try:
            import customtkinter as ctk

            return ctk.get_appearance_mode() == "Dark"
        except Exception:  # noqa: BLE001 - 没装 customtkinter 时按深色处理
            return True
    return str(mode).lower() in ("dark", "深色")


def pick(value: ColorValue, mode: Optional[str] = None) -> str:
    """把一个样式值解析成当前外观下的单色字符串。"""
    if isinstance(value, (tuple, list)):
        return value[1] if is_dark(mode) else value[0]
    return value


def style_of(
    name: str, state: str, mode: Optional[str] = None
) -> Dict[str, str]:
    """取某个控件某个状态的 ``configure`` 参数，颜色已按外观解析。

    参数:
        name: 控件名，见 :data:`SHEETS`。
        state: 状态名，例如 ``"shell"`` / ``"title"``。
        mode: ``"light"`` / ``"dark"`` / ``"system"``；不传就取当前外观。

    返回:
        可以直接解包给 ``configure(**...)`` 的字典。
    """
    sheet = SHEETS[name][state]
    return {key: pick(value, mode) for key, value in sheet.items()}
