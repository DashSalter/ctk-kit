"""ctk-kit —— 面向 CustomTkinter 的轻量界面基件。

内容分这几块：

- ``tokens``  设计令牌：颜色（深浅两套）、字体、圆角、间距
- ``theme``   取色与外观切换工具，以及原生 tk 控件的重绘
- ``pages``   多页面窗口的页面管理：按需重建，切外观不卡
- 组件        ``buttons`` / ``inputs`` / ``dropdown`` / ``select`` / ``layout`` / ``notify`` / ``dialog`` / ``scroll_list`` / ``text`` / ``sidebar`` / ``page``
- 原生接口    CustomTkinter 的 ``CTk`` / ``CTkImage`` 等原样转出，
              ``App`` 是 ``CTk`` 的便捷子类（标题、尺寸、外观都能直接传参）；
              ``CTkEntry`` / ``CTkButton`` 默认套用库的样式，``Frame`` 默认透明底

安装::

    pip install ctk-kit

最小示例::

    from ctk_kit import App, Card, PageHeader, PrimaryButton

    app = App(title="备份", size=(880, 560), min_size=(640, 400))
    header = PageHeader(app, "备份")
    box = Card(app)
    PrimaryButton(box, "立即备份", command=lambda: print("go")).pack(padx=16, pady=16)
    app.mainloop()

全组件展示（仓库示例，clone 后运行）::

    python examples/basics/window.py

仓库: https://gitee.com/kuangjianke/ctk-kit
镜像: https://github.com/DashSalter/ctk-kit
"""

from __future__ import annotations

from typing import Any

__version__ = "0.9.2"

# 原生 CustomTkinter 的公开接口原样转出，用户只 import ctk_kit 就够了。
# 显式列名字而不是 ``from customtkinter import *``：这样 __all__ 与实际导出
# 一一对应，也不会把 customtkinter 内部的 StringVar / filedialog 之类带进来。
from customtkinter import (
    CTk,
    CTkBaseClass,
    CTkCanvas,
    CTkCheckBox,
    CTkComboBox,
    CTkFont,
    CTkFrame,
    CTkImage,
    CTkInputDialog,
    CTkLabel,
    CTkOptionMenu,
    CTkProgressBar,
    CTkRadioButton,
    CTkScrollableFrame,
    CTkScrollbar,
    CTkSegmentedButton,
    CTkSlider,
    CTkSwitch,
    CTkTabview,
    CTkTextbox,
    CTkToplevel,
    get_appearance_mode,
    set_appearance_mode,
    set_default_color_theme,
)

from . import tokens, theme
from .branding import ICON_PATH, LOGO_PATH, load_logo, set_window_icon
from .buttons import (
    CTkButton,
    DangerButton,
    FlatButton,
    PrimaryButton,
    SecondaryButton,
    SoftButton,
)
from .choices import Check, Radio
from .collapse import Collapsible
from .code_panel import CodePanel
from .context_menu import ContextMenu, attach_edit_menu, attach_menu
from .dialog import Dialog, alert, confirm, prompt
from .dropdown import DropField
from .files import DropZone, PathField, has_dnd, pick_path
from .frames import Frame
from .inputs import (
    CTkEntry,
    Checkbox,
    FormEntry,
    ProgressBar,
    Segmented,
    Slider,
    Spinner,
    Switch,
    ToolbarEntry,
    bind_focus_border,
    radio_group,
)
from .layout import (
    Card,
    divider,
    empty_hint,
    FieldLabel,
    HintLabel,
    PageHeader,
    Scrollable,
    SectionTitle,
    style_scrollable,
    style_scrollbar,
    vertical_divider,
)
from .misc import Progress, RingProgress
from .notify import Notifier, notify
from .page import PageBase
from .pages import PageRebuilder
from .scroll_list import LazyList
from .select import Stepper, TagSelectField, TreeSelectField
from .sidebar import SidebarNav
from .table import Table
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
from .window import App

__all__ = [
    "App",
    "CTk",
    "CTkBaseClass",
    "CTkButton",
    "CTkCanvas",
    "CTkCheckBox",
    "CTkComboBox",
    "CTkEntry",
    "CTkFont",
    "CTkFrame",
    "CTkImage",
    "CTkInputDialog",
    "CTkLabel",
    "CTkOptionMenu",
    "CTkProgressBar",
    "CTkRadioButton",
    "CTkScrollableFrame",
    "CTkScrollbar",
    "CTkSegmentedButton",
    "CTkSlider",
    "CTkSwitch",
    "CTkTabview",
    "CTkTextbox",
    "CTkToplevel",
    "Card",
    "Checkbox",
    "Check",
    "CodePanel",
    "Collapsible",
    "ContextMenu",
    "DangerButton",
    "Dialog",
    "DropField",
    "TagSelectField",
    "TreeSelectField",
    "Stepper",
    "DropZone",
    "FieldLabel",
    "FlatButton",
    "FormEntry",
    "Frame",
    "HintLabel",
    "ICON_PATH",
    "ImageViewer",
    "LOGO_PATH",
    "LazyList",
    "Notifier",
    "PageBase",
    "PageHeader",
    "PageRebuilder",
    "PathField",
    "PrimaryButton",
    "ProgressBar",
    "Progress",
    "RingProgress",
    "Scrollable",
    "SecondaryButton",
    "SectionTitle",
    "Segmented",
    "SidebarNav",
    "Slider",
    "Spinner",
    "SoftButton",
    "Switch",
    "Table",
    "TextArea",
    "ToolbarEntry",
    "__version__",
    "alert",
    "apply_appearance",
    "apply_appearance_fast",
    "attach_edit_menu",
    "attach_menu",
    "bind_focus_border",
    "color_of",
    "confirm",
    "divider",
    "vertical_divider",
    "empty_hint",
    "get_appearance_mode",
    "has_dnd",
    "is_dark",
    "load_logo",
    "notify",
    "pick_path",
    "prompt",
    "radio_group",
    "Radio",
    "recolor_tree",
    "repaint_native",
    "set_appearance_mode",
    "set_default_color_theme",
    "set_titlebar_dark",
    "set_window_icon",
    "style_scrollable",
    "style_scrollbar",
    "theme",
    "tokens",
]


def __getattr__(name: str) -> Any:
    """``ImageViewer`` 依赖 Pillow，真的用到时才导入。

    这样没装 ``pillow`` 的项目 ``import ctk_kit`` 依然能用其余全部控件，
    只有 ``ctk_kit.ImageViewer`` 会在导入时给出明确的安装提示。
    """
    if name == "ImageViewer":
        from .image_view import ImageViewer

        return ImageViewer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
