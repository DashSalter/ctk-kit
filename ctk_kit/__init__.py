"""ctk-kit —— 面向 CustomTkinter 的轻量界面基件。

分三层：

- ``tokens``  设计令牌：颜色（深浅两套）、字体、圆角、间距
- ``theme``   取色与外观切换工具，以及原生 tk 控件的重绘
- 组件        ``buttons`` / ``inputs`` / ``dropdown`` / ``layout`` / ``scroll_list``

组件总览::

    python -m ctk_kit.demo
"""

from __future__ import annotations

__version__ = "0.1.0"

from . import tokens, theme
from .buttons import (
    FlatButton,
    SoftButton,
    danger_button,
    primary_button,
    soft_button,
)
from .dropdown import DropField
from .inputs import form_entry, segmented, switch, toolbar_entry
from .layout import (
    card,
    divider,
    empty_hint,
    field_label,
    hint_label,
    page_header,
    scrollable,
    section_title,
    style_scrollable,
)
from .scroll_list import LazyList
from .theme import apply_appearance, color_of, is_dark, repaint_native

__all__ = [
    "DropField",
    "FlatButton",
    "LazyList",
    "SoftButton",
    "__version__",
    "apply_appearance",
    "card",
    "color_of",
    "danger_button",
    "divider",
    "empty_hint",
    "field_label",
    "form_entry",
    "hint_label",
    "is_dark",
    "page_header",
    "primary_button",
    "repaint_native",
    "scrollable",
    "section_title",
    "segmented",
    "soft_button",
    "style_scrollable",
    "switch",
    "theme",
    "tokens",
    "toolbar_entry",
]
