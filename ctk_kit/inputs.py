"""输入控件：工具栏搜索框、分段选择、表单输入框。

分段选择（CTkSegmentedButton）有几个必须显式指定的参数，否则深浅色的观感
会不一致：

- ``fg_color`` / ``unselected_color`` 用输入框底色，否则默认是灰色
- ``selected_color`` 用淡强调色，避免整块高饱和蓝
- ``dynamic_resizing=False`` 否则切换选项会改控件宽度，把右边的元素挤动
- 不能传 ``border_width`` / ``border_color``，CTk 会直接抛 ValueError

所有工厂只返回控件，不负责摆位。
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Sequence

import customtkinter as ctk

from . import tokens as T

# 分段选择的选中回调：收到被选中的那一段文字。
SegmentCommand = Optional[Callable[[str], None]]
# 开关回调：不接收参数（CTk 的约定）。
SwitchCommand = Optional[Callable[[], None]]


def toolbar_entry(master: tk.Misc, placeholder: str, *, height: int = 40) -> ctk.CTkEntry:
    """页面顶部搜索框：聚焦时描边变强调色。

    参数:
        master: 父容器。
        placeholder: 未输入时显示的灰色占位文字。
        height: 高度（像素），默认 40。

    返回:
        已经绑好焦点样式、尚未摆位的 ``CTkEntry``。
    """
    entry = ctk.CTkEntry(
        master,
        placeholder_text=placeholder,
        placeholder_text_color=T.COLOR_FAINT,
        height=height,
        corner_radius=T.RADIUS_LARGE,
        font=T.FONT_BODY,
        fg_color=T.COLOR_INPUT,
        border_color=T.COLOR_BORDER,
        border_width=1,
        text_color=T.COLOR_TEXT,
    )
    entry.bind("<FocusIn>", lambda _event: entry.configure(border_color=T.COLOR_ACCENT))
    entry.bind(
        "<FocusOut>", lambda _event: entry.configure(border_color=T.COLOR_BORDER)
    )
    return entry


def form_entry(
    master: tk.Misc,
    *,
    show: str = "",
    placeholder: str = "",
    height: int = 38,
    password: bool = False,
) -> ctk.CTkEntry:
    """表单里的单行输入。

    ``password=True`` 时用圆点打码。注意 CTkEntry 带了 ``placeholder_text``
    时，内部 Entry 的 ``show`` 会被占位符机制置空，``cget("show")`` 读到的是
    空字符串——要判断是否在打码，得自己记住状态，别去读控件。

    参数:
        master: 父容器。
        show: 自定义替代字符（例如 ``"*"``），空字符串表示正常显示。
        placeholder: 未输入时的灰色占位文字。
        height: 高度（像素），默认 38。
        password: 为 ``True`` 时用圆点 ``"•"`` 打码，优先级高于 ``show``。

    返回:
        尚未摆位的 ``CTkEntry``。
    """
    return ctk.CTkEntry(
        master,
        show=("•" if password else show) or "",
        placeholder_text=placeholder,
        placeholder_text_color=T.COLOR_FAINT,
        height=height,
        corner_radius=T.RADIUS_SMALL,
        font=T.FONT_BODY,
        fg_color=T.COLOR_INPUT,
        border_color=T.COLOR_BORDER,
        border_width=1,
        text_color=T.COLOR_TEXT,
    )


def segmented(
    master: tk.Misc,
    values: Sequence[str],
    command: SegmentCommand = None,
    *,
    width: int = 300,
    height: int = 34,
    font: T.FontSpec = T.FONT_SMALL,
) -> ctk.CTkSegmentedButton:
    """统一样式的分段选择：浅一档的容器底，选中段淡色高亮。

    容器底比卡片深一档（``COLOR_SOFT``），否则浅色主题下和白色卡片同色
    （``COLOR_INPUT`` 的浅色值就是 ``#ffffff``），整组分段会「消失」在卡片里。

    参数:
        master: 父容器。
        values: 各段文字，按显示顺序排列；非空时默认选中第一项。
        command: 切换回调，参数是被选中的那一段文字。
        width: 整体宽度（像素），默认 300；``dynamic_resizing=False`` 保证
            切换选项时宽度不变。
        height: 高度（像素），默认 34。
        font: 字体规格，默认 :data:`tokens.FONT_SMALL`。

    返回:
        尚未摆位的 ``CTkSegmentedButton``。
    """
    button = ctk.CTkSegmentedButton(
        master,
        values=values,
        width=width,
        height=height,
        corner_radius=T.RADIUS_SMALL,
        fg_color=T.COLOR_SOFT,
        unselected_color=T.COLOR_SOFT,
        selected_color=T.COLOR_SEG_SELECTED,
        unselected_hover_color=T.COLOR_SOFT_HOVER,
        selected_hover_color=T.COLOR_SEG_SELECTED,
        text_color=T.COLOR_TEXT,
        font=font,
        dynamic_resizing=False,
        command=command,
    )
    if values:
        # 不留「一段都没选中」的中间态
        button.set(values[0])
    return button


def switch(master: tk.Misc, command: SwitchCommand = None, *, width: int = 44) -> ctk.CTkSwitch:
    """设置页的开关：去掉文字，只留轨道，颜色跟随主色。

    参数:
        master: 父容器。
        command: 拨动回调，不接收参数；用 ``toggle()`` 或点击都会触发。
        width: 开关宽度（像素），默认 44；卡片里的紧凑尺寸可以传 60 / 40。

    返回:
        尚未摆位的 ``CTkSwitch``。
    """
    return ctk.CTkSwitch(
        master,
        text="",
        width=width,
        progress_color=T.COLOR_ACCENT,
        command=command,
    )
