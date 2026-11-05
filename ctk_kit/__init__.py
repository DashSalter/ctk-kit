"""ctk-kit —— 面向 CustomTkinter 的轻量界面基件。

内容分这几块：

- ``tokens``  设计令牌：颜色（深浅两套）、字体、圆角、间距
- ``theme``   取色与外观切换工具，以及原生 tk 控件的重绘
- ``pages``   多页面窗口的页面管理：按需重建，切外观不卡
- 组件        ``buttons`` / ``inputs`` / ``dropdown`` / ``select`` / ``layout`` / ``notify`` / ``dialog`` / ``scroll_list`` / ``text`` / ``sidebar`` / ``page`` / ``tabs`` / ``calendar`` / ``range`` / ``search`` / ``steps`` / ``avatar`` / ``breadcrumb`` / ``placeholder`` / ``splitter`` / ``popover`` / ``color`` / ``statusbar`` / ``timeline`` / ``carousel`` / ``treeview`` / ``menubar``
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

#: 改这里时记得同步 ``pyproject.toml`` 的 ``version``（打包以那份为准，
#: 这行只给 ``ctk_kit.__version__`` 用）。
__version__ = "0.11.0"

# 核心模块（win32 / glass / frost_layer）发布时是编译好的 .pyd，源码不在仓库里。
# 装错平台或 Python 版本时，import 那一层会报得很晚、很难懂，这里提前说清楚。
try:  # pragma: no cover - 只在缺二进制时触发
    import importlib as _importlib

    for _core_name in ("win32", "glass", "frost_layer"):
        _importlib.import_module(f"{__name__}.core.{_core_name}")
except ImportError as _exc:  # noqa: BLE001
    import platform as _platform
    import sys as _sys

    _missing = getattr(_exc, "name", "") or ""
    if not _missing.startswith(f"{__name__}.core."):
        # 二进制装好了，但它 import 时缺第三方依赖（最常见的是 Pillow）。
        # 这种错误说成「核心模块没加载」会让人找错方向。
        raise ImportError(
            f"ctk-kit 缺少依赖：{_missing or '未知模块'}。\n"
            "  试试重装一遍，让 pip 把依赖补齐：\n"
            "  pip install --upgrade --force-reinstall ctk-kit"
        ) from _exc

    raise ImportError(
        "ctk-kit 的核心模块没能加载。\n"
        f"  当前环境：Python {_sys.version.split()[0]} / {_platform.system()} {_platform.machine()}\n"
        "  这些模块以 abi3 二进制发布，需要 Python 3.9+ 且与安装包平台一致（Windows x64）。\n"
        "  如果是在源码仓库里运行，先执行：python -m tools.build_core\n"
        "  缺哪个模块看下面的原始错误。"
    ) from _exc

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

from . import theming, tokens, theme
from .avatar import Avatar
from .badge import Badge, Tag
from .breadcrumb import Breadcrumb
from .calendar import Calendar, DatePicker
from .timepicker import TimeField, TimePicker
from .carousel import Carousel
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
from .color import ColorDialog, ColorPicker
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
from .loading import LoadingOverlay
from .menubar import MenuBar
from .misc import Progress, RingProgress
from .notify import Notifier, notify
from .page import PageBase
from .pages import PageRebuilder
from .pagination import Pagination
from .popover import Popover
from .range import RangeSlider
from .scroll_list import LazyList
from .search import SearchBox
from .select import Stepper, TagSelectField, TreeSelectField
from .sidebar import SidebarNav
from .placeholder import Skeleton
from .splitter import Splitter
from .statusbar import StatusBar
from .steps import Steps, Wizard
from .table import Table
from .tabs import Tabs
from .text import TextArea
from .timeline import Timeline
from .theme import (
    apply_appearance,
    apply_appearance_fast,
    apply_backdrop,
    color_of,
    current_backdrop,
    is_dark,
    recolor_tree,
    repaint_native,
    set_titlebar_dark,
    set_window_brush,
)
from .tooltip import Tooltip
from .treeview import TreeView
from .window import App

__all__ = [
    "App",
    "Avatar",
    "Badge",
    "Breadcrumb",
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
    "Calendar",
    "Carousel",
    "Card",
    "Checkbox",
    "Check",
    "CodePanel",
    "Collapsible",
    "ColorDialog",
    "ColorPicker",
    "ContextMenu",
    "DangerButton",
    "DatePicker",
    "TimeField",
    "TimePicker",
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
    "LoadingOverlay",
    "MenuBar",
    "Notifier",
    "PageBase",
    "PageHeader",
    "PageRebuilder",
    "Pagination",
    "PathField",
    "Popover",
    "PrimaryButton",
    "ProgressBar",
    "Progress",
    "RangeSlider",
    "RingProgress",
    "Scrollable",
    "SearchBox",
    "SecondaryButton",
    "SectionTitle",
    "Segmented",
    "SidebarNav",
    "Skeleton",
    "Slider",
    "Spinner",
    "Splitter",
    "StatusBar",
    "SoftButton",
    "Steps",
    "Switch",
    "Table",
    "Tabs",
    "Tag",
    "TextArea",
    "Timeline",
    "ToolbarEntry",
    "Tooltip",
    "TreeView",
    "Wizard",
    "__version__",
    "alert",
    "apply_appearance",
    "apply_appearance_fast",
    "apply_backdrop",
    "attach_edit_menu",
    "attach_menu",
    "bind_focus_border",
    "color_of",
    "confirm",
    "current_backdrop",
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
    "set_window_brush",
    "set_window_icon",
    "style_scrollable",
    "style_scrollbar",
    "theme",
    "theming",
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
