"""输入控件：工具栏搜索框、分段选择、表单输入框。

分段选择（CTkSegmentedButton）有几个必须显式指定的参数，否则深浅色的观感
会不一致：

- ``fg_color`` / ``unselected_color`` 用输入框底色，否则默认是灰色
- ``selected_color`` 用淡强调色，避免整块高饱和蓝
- ``dynamic_resizing=False`` 否则切换选项会改控件宽度，把右边的元素挤动
- 不能传 ``border_width`` / ``border_color``，CTk 会直接抛 ValueError
"""

from __future__ import annotations

import customtkinter as ctk

from . import tokens as T


def toolbar_entry(master, placeholder: str, *, height: int = 40) -> ctk.CTkEntry:
    """页面顶部搜索框：聚焦时描边变强调色。"""
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
    master,
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
    master,
    values: list[str],
    command=None,
    *,
    width: int = 300,
    height: int = 34,
    font=T.FONT_SMALL,
) -> ctk.CTkSegmentedButton:
    """统一样式的分段选择：底色同输入框，选中段淡色高亮。"""
    button = ctk.CTkSegmentedButton(
        master,
        values=values,
        width=width,
        height=height,
        corner_radius=T.RADIUS_SMALL,
        fg_color=T.COLOR_INPUT,
        unselected_color=T.COLOR_INPUT,
        selected_color=T.COLOR_SEG_SELECTED,
        unselected_hover_color=T.COLOR_SOFT,
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


def switch(master, command=None, *, width: int = 44) -> ctk.CTkSwitch:
    """设置页的开关：去掉文字，只留轨道，颜色跟随主色。"""
    return ctk.CTkSwitch(
        master,
        text="",
        width=width,
        progress_color=T.COLOR_ACCENT,
        command=command,
    )
