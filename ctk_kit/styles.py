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

__all__ = ["SHEETS", "is_dark", "pick", "refresh_tokens", "style_of"]

#: 一个样式值：单色字符串，或 ``(浅色, 深色)`` 令牌。
ColorValue = Union[str, T.ColorPair]

#: 控件名 -> 状态 -> ``configure`` 参数。状态名由各控件自己定义。
SHEETS: Dict[str, Dict[str, Dict[str, ColorValue]]] = {
    "sidebar": {
        "shell": {"fg_color": T.COLOR_BG},
        "side": {"fg_color": T.COLOR_SIDE, "bg_color": T.COLOR_SIDE},
        "content": {"fg_color": T.COLOR_BG, "bg_color": T.COLOR_BG},
        "divider": {"fg_color": T.COLOR_BORDER, "bg_color": T.COLOR_BG},
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


def refresh_tokens() -> None:
    """把 ``SHEETS`` 里缓存的令牌重新指向 :mod:`ctk_kit.tokens` 的当前值。

    ``SHEETS`` 是模块导入时抓的一次快照；玻璃外观会在运行时替换
    ``tokens.COLOR_BG`` / ``COLOR_SIDE``，这边必须跟着同步，否则侧边栏
    ``apply_theme()`` 刷回去的还是旧底色。
    """
    sidebar = SHEETS["sidebar"]
    sidebar["shell"]["fg_color"] = T.COLOR_BG
    sidebar["side"]["fg_color"] = T.COLOR_SIDE
    sidebar["side"]["bg_color"] = T.COLOR_SIDE
    sidebar["content"]["fg_color"] = T.COLOR_BG
    sidebar["content"]["bg_color"] = T.COLOR_BG
    sidebar["divider"]["bg_color"] = T.COLOR_BG
    sidebar["title"]["bg_color"] = T.COLOR_SIDE
    sidebar["subtitle"]["bg_color"] = T.COLOR_SIDE
    sidebar["nav_normal"]["bg_color"] = T.COLOR_SIDE
    sidebar["nav_active"]["bg_color"] = T.COLOR_SIDE


def is_dark(mode: Optional[str] = None) -> bool:
    """``mode`` 是不是深色；``None`` / ``"system"`` 取当前全局外观。"""
    if mode is None or str(mode).lower() == "system":
        try:
            import customtkinter as ctk

            return ctk.get_appearance_mode() == "Dark"
        except Exception:  # noqa: BLE001 - 没装 customtkinter 时按深色处理
            return True
    return str(mode).lower() in ("dark", "深色")


def _glass_active() -> bool:
    """当前是否毛玻璃底色；样式模块不依赖 theme，只能延迟导入。"""
    try:
        from .theme import current_backdrop

        return current_backdrop() == "acrylic"
    except Exception:  # noqa: BLE001 - 独立使用 styles 时按不透明处理
        return False


def pick(value: ColorValue, mode: Optional[str] = None) -> str:
    """把一个样式值解析成当前外观下的单色字符串。

    三元组的第三项只给毛玻璃底色用；二元组照旧按深浅外观取。
    """
    if isinstance(value, (tuple, list)):
        if len(value) >= 3 and _glass_active():
            return value[2]
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
