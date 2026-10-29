"""输入与选择控件：搜索框、表单输入、分段选择、开关、勾选、单选、滑块、进度条。

分段选择（CTkSegmentedButton）有几个必须显式指定的参数，否则深浅色的观感
会不一致：

- ``fg_color`` / ``unselected_color`` 用输入框底色，否则默认是灰色
- ``selected_color`` 用淡强调色，避免整块高饱和蓝
- ``dynamic_resizing=False`` 否则切换选项会改控件宽度，把右边的元素挤动
- 不能传 ``border_width`` / ``border_color``，CTk 会直接抛 ValueError

选择类控件（勾选、单选、开关、滑块）只把「选中/填充」部分交给主色，未选中态
一律用 ``COLOR_BORDER_STRONG`` 描边、``COLOR_SOFT`` 做轨道，避免深色主题下
一排控件全是高饱和蓝。

所有工厂只返回控件，不负责摆位。
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Sequence, Tuple

import customtkinter as ctk

from . import tokens as T

# 分段选择的选中回调：收到被选中的那一段文字。
SegmentCommand = Optional[Callable[[str], None]]
# 开关、勾选回调：不接收参数（CTk 的约定）。
SwitchCommand = Optional[Callable[[], None]]
# 滑块回调：收到当前数值（float）。
SliderCommand = Optional[Callable[[float], None]]
# 单选组回调：收到被选中的那一项文字。
RadioCommand = Optional[Callable[[str], None]]


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


def switch(
    master: tk.Misc,
    command: SwitchCommand = None,
    *,
    text: str = "",
    width: int = 44,
) -> ctk.CTkSwitch:
    """设置页的开关：只留轨道，拨到右边时轨道变主色。

    参数:
        master: 父容器。
        command: 拨动回调，不接收参数；用 ``toggle()`` 或点击都会触发。
        text: 轨道右侧的文字，默认空（设置页那种「标签在左边」的排法）。
        width: 开关宽度（像素），默认 44；卡片里的紧凑尺寸可以传 60 / 40。

    返回:
        尚未摆位的 ``CTkSwitch``。
    """
    return ctk.CTkSwitch(
        master,
        text=text,
        width=width,
        font=T.FONT_SMALL,
        text_color=T.COLOR_TEXT,
        fg_color=T.COLOR_SOFT,
        progress_color=T.COLOR_ACCENT,
        button_color=T.COLOR_SIDE,
        button_hover_color=T.COLOR_CARD,
        command=command,
    )


def checkbox(
    master: tk.Misc,
    text: str = "",
    command: SwitchCommand = None,
    *,
    width: int = 20,
    height: int = 20,
) -> ctk.CTkCheckBox:
    """勾选框：未选中是描边空心方块，选中后填主色并打勾。

    参数:
        master: 父容器。
        text: 方块右侧的文字。
        command: 勾选/取消回调，不接收参数。
        width: 方块宽度（像素），默认 20。
        height: 方块高度（像素），默认 20。

    返回:
        尚未摆位的 ``CTkCheckBox``。
    """
    return ctk.CTkCheckBox(
        master,
        text=text,
        width=width,
        height=height,
        checkbox_width=width,
        checkbox_height=height,
        corner_radius=T.RADIUS_SMALL - 2,
        border_width=2,
        border_color=T.COLOR_BORDER_STRONG,
        fg_color=T.COLOR_ACCENT,
        hover_color=T.COLOR_ACCENT_HOVER,
        checkmark_color=T.COLOR_ACCENT_TEXT,
        text_color=T.COLOR_TEXT,
        font=T.FONT_SMALL,
        command=command,
    )


def radio_group(
    master: tk.Misc,
    values: Sequence[str],
    command: RadioCommand = None,
    *,
    variable: Optional[tk.StringVar] = None,
    gap: int = 8,
) -> Tuple[ctk.CTkFrame, tk.StringVar]:
    """一组互斥单选框：内部自己建容器，选中状态由返回的 ``StringVar`` 持有。

    ``CTkRadioButton`` 必须共用同一个 ``variable`` 才会互斥，单独建两个控件
    会出现「能同时选中」的错觉，所以这里直接给一组。

    参数:
        master: 父容器。
        values: 各项文字，按显示顺序排列；非空时默认选中第一项。
        command: 切换回调，参数是被选中的那一项文字（同时也会更新 ``variable``）。
        variable: 外部传入的 ``StringVar``，可用于读写当前选中项；不传则内部新建。
        gap: 各选项之间的垂直间距（像素），默认 8。

    返回:
        ``(容器, 变量)``：容器是 ``CTkFrame``（``fg_color="transparent"``），
        已经按顺序摆好单选框；变量是 ``StringVar``，读它拿到当前选中项。
    """
    var = variable if variable is not None else tk.StringVar(master=master)

    def on_select() -> None:
        if command is not None:
            command(var.get())

    frame = ctk.CTkFrame(master, fg_color="transparent")
    for index, value in enumerate(values):
        button = ctk.CTkRadioButton(
            frame,
            text=value,
            value=value,
            variable=var,
            command=on_select,
            radiobutton_width=18,
            radiobutton_height=18,
            corner_radius=9,
            border_width_unchecked=2,
            border_width_checked=6,
            border_color=T.COLOR_BORDER_STRONG,
            fg_color=T.COLOR_ACCENT,
            hover_color=T.COLOR_ACCENT_HOVER,
            text_color=T.COLOR_TEXT,
            font=T.FONT_SMALL,
        )
        button.pack(anchor="w", pady=(0, gap) if index < len(values) - 1 else 0)

    if values:
        var.set(values[0])
    return frame, var


def slider(
    master: tk.Misc,
    command: SliderCommand = None,
    *,
    from_: float = 0.0,
    to: float = 100.0,
    steps: int = 0,
    width: int = 220,
) -> ctk.CTkSlider:
    """滑块：轨道底色淡，已滑过的部分和圆钮是主色。

    参数:
        master: 父容器。
        command: 拖动回调，参数是当前数值（float）。
        from_: 最小值，默认 0。
        to: 最大值，默认 100。
        steps: 分段数；``0`` 表示连续，正整数表示只能停在等分点上。
        width: 宽度（像素），默认 220。

    返回:
        尚未摆位的 ``CTkSlider``；读数用 ``get()``。
    """
    return ctk.CTkSlider(
        master,
        from_=from_,
        to=to,
        number_of_steps=steps if steps > 0 else None,
        width=width,
        height=16,
        # 圆角给大值让轨道和把手都成胶囊/正圆；button_length=0 表示把手是正圆。
        # 别把 border_width 设成 0：CTkSlider 是「整高画一圈 border、内层再画 fg」，
        # 轨道那 4px 的细线正是靠默认的 border_width=6 缩出来的，设 0 会变成一根粗条。
        corner_radius=1000,
        fg_color=T.COLOR_BORDER_STRONG,
        progress_color=T.COLOR_ACCENT,
        button_color=T.COLOR_ACCENT,
        button_hover_color=T.COLOR_ACCENT_HOVER,
        button_corner_radius=1000,
        button_length=0,
        command=command,
    )


def progressbar(
    master: tk.Misc,
    *,
    value: float = 0.0,
    width: int = 220,
    height: int = 6,
) -> ctk.CTkProgressBar:
    """细进度条：``value`` 取 0~1，圆角跟随高度。

    参数:
        master: 父容器。
        value: 初始进度，0~1 的小数。
        width: 宽度（像素），默认 220。
        height: 高度（像素），默认 6；进度条越细越像「状态条」。

    返回:
        尚未摆位的 ``CTkProgressBar``；更新用 ``set(0~1)``。
    """
    bar = ctk.CTkProgressBar(
        master,
        width=width,
        height=height,
        corner_radius=height // 2,
        border_width=0,
        fg_color=T.COLOR_BORDER_STRONG,
        progress_color=T.COLOR_ACCENT,
    )
    bar.set(max(0.0, min(1.0, value)))
    return bar
