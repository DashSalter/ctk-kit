"""ctk-kit —— 面向 CustomTkinter 的轻量界面基件。

分四层：

- ``tokens``  设计令牌：颜色（深浅两套）、字体、圆角、间距
- ``theme``   取色与外观切换工具，以及原生 tk 控件的重绘
- ``pages``   多页面窗口的页面管理：按需重建，切外观不卡
- 组件        ``buttons`` / ``inputs`` / ``dropdown`` / ``layout`` / ``notify`` / ``scroll_list`` / ``text``

安装::

    pip install ctk-kit

最小示例::

    import customtkinter as ctk
    from ctk_kit import primary_button, card, page_header

    app = ctk.CTk()
    header, info = page_header(app, "备份")
    box = card(app)
    primary_button(box, "立即备份", command=lambda: print("go")).pack(padx=16, pady=16)
    app.mainloop()

全组件展示（随包发布，装好后直接运行）::

    ctk-kit-showcase
    python -m ctk_kit.showcase

从源码运行时等价写法：``python examples/showcase.py``。

仓库: https://gitee.com/kuangjianke/ctk-kit
镜像: https://github.com/DashSalter/ctk-kit
"""

from __future__ import annotations

__version__ = "0.8.0"

from . import tokens, theme
from .buttons import (
    FlatButton,
    SoftButton,
    danger_button,
    primary_button,
    soft_button,
)
from .dropdown import DropField
from .inputs import (
    bind_focus_border,
    checkbox,
    form_entry,
    progressbar,
    radio_group,
    segmented,
    slider,
    switch,
    toolbar_entry,
)
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
    style_scrollbar,
)
from .notify import Notifier, notify
from .pages import PageRebuilder
from .scroll_list import LazyList
from .text import TextArea
from .theme import (
    apply_appearance,
    apply_appearance_fast,
    color_of,
    is_dark,
    recolor_tree,
    repaint_native,
    set_titlebar_dark,
)

__all__ = [
    "DropField",
    "FlatButton",
    "LazyList",
    "Notifier",
    "PageRebuilder",
    "SoftButton",
    "TextArea",
    "__version__",
    "apply_appearance",
    "apply_appearance_fast",
    "bind_focus_border",
    "card",
    "checkbox",
    "color_of",
    "danger_button",
    "divider",
    "empty_hint",
    "field_label",
    "form_entry",
    "hint_label",
    "is_dark",
    "notify",
    "page_header",
    "primary_button",
    "progressbar",
    "radio_group",
    "recolor_tree",
    "repaint_native",
    "scrollable",
    "section_title",
    "segmented",
    "set_titlebar_dark",
    "slider",
    "soft_button",
    "style_scrollable",
    "style_scrollbar",
    "switch",
    "theme",
    "tokens",
    "toolbar_entry",
]
