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

所有工厂只返回控件，不负责摆位；``CTkEntry`` 是默认带库样式的类。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional, Sequence, Tuple

import customtkinter as ctk

from . import tokens as T
from .context_menu import attach_edit_menu
from .fonts import get_font
from .theme import color_of

try:  # Pillow 是可选依赖：装了就用抗锯齿的箭头图片
    from PIL import Image, ImageDraw, ImageTk

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

# 分段选择的选中回调：收到被选中的那一段文字。
SegmentCommand = Optional[Callable[[str], None]]
# 开关、勾选回调：不接收参数（CTk 的约定）。
SwitchCommand = Optional[Callable[[], None]]
# 滑块回调：收到当前数值（float）。
SliderCommand = Optional[Callable[[float], None]]
# 单选组回调：收到被选中的那一项文字。
RadioCommand = Optional[Callable[[str], None]]
# 焦点边框的回调：改完边框后以新的 border_width 调一次（给需要同步内缩的容器用）。
InsetHook = Optional[Callable[[int], None]]


class CTkEntry(ctk.CTkEntry):
    """默认套用 ctk-kit 输入框样式的 ``CTkEntry``。

    参数与 customtkinter 的 ``CTkEntry`` 完全一致，只是把底色、描边、圆角、
    字体和 placeholder 颜色换成 ``tokens`` 里的值，深浅色自动跟随；显式传
    同名参数可以覆盖任意一项。输入框默认带「复制 / 粘贴 / 剪切 / 清空」
    右键菜单，用 ``menu`` 控制。

    示例::

        entry = CTkEntry(frame, placeholder_text="输入名字", width=320)

        CTkEntry(frame, menu=False)              # 不要右键菜单
        CTkEntry(frame, menu=[("插入时间戳", stamp)])   # 只用自己的菜单项
    """

    def __init__(
        self, master: tk.Misc, *, menu: Any = True, **kwargs: Any
    ) -> None:
        """建带默认样式的输入框；显式参数可覆盖类说明里的默认值。

        参数:
            master: 父容器。
            menu: 右键菜单。``True`` 挂默认的复制/粘贴/剪切/清空，``False``
                或 ``None`` 不挂，传 ``(文字, 函数)`` 的序列则**只**用这些
                自定义项（默认项不再附带）。
            **kwargs: 透传给 customtkinter ``CTkEntry`` 的参数。
        """
        kwargs.setdefault("fg_color", T.COLOR_INPUT)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", T.COLOR_BORDER_INPUT)
        kwargs.setdefault("corner_radius", T.RADIUS_SMALL)
        kwargs.setdefault("font", get_font(T.FONT_BODY))
        kwargs.setdefault("text_color", T.COLOR_TEXT)
        kwargs.setdefault("placeholder_text_color", T.COLOR_FAINT)
        super().__init__(master, **kwargs)
        if menu:
            if menu is True:
                attach_edit_menu(self)
            else:
                attach_edit_menu(self, menu, preset=False)

    def set(self, text: str) -> None:
        """整体替换内容（清空后再写入），等价于 ``delete(0, "end")`` + ``insert``。"""
        self.delete(0, "end")
        if text:
            self.insert(0, text)

    def append(self, text: str) -> None:
        """把文字追加到当前内容末尾。"""
        if text:
            self.insert("end", text)

    def clear(self) -> None:
        """清空输入框。"""
        self.delete(0, "end")


def bind_focus_border(
    widget: tk.Misc,
    *,
    source: tk.Misc = None,
    idle_color: Any = None,
    width: int = T.BORDER_FOCUS_WIDTH,
    on_width: InsetHook = None,
) -> None:
    """给控件绑定「聚焦才出现描边」的焦点样式（可选）。

    库里的输入类控件默认**不**绑它：它们只有一圈 1px 的 ``COLOR_BORDER_INPUT``，
    聚焦时也不变色。想让聚焦时亮一圈主色，对这个控件调用一次即可。

    常态不画线：描边的槽位一直在，只是颜色等于控件自己的底色，于是看不见。
    聚焦时把同一槽位的颜色换成主色，边框亮出来而内容不会左右跳。

    宽度取 ``BORDER_FOCUS_WIDTH``（2）而不是 1：Tk 的 canvas 不做抗锯齿，
    1px 逻辑边在 150% 缩放下只有 1.5 个物理像素、落在半格上就会整段丢像素，
    作为「聚焦提示」不够醒目；库里的 1px 常态描边是另一套取舍（见 tokens）。

    参数:
        widget: ``CTkEntry`` / ``CTkTextbox`` / ``CTkFrame`` 这类支持
            ``configure(border_width=..., border_color=...)`` 的控件。
        source: 真正接收焦点的控件；复合控件（``DropField`` 的外框里包着
            entry）要传进来——焦点事件不会从子控件冒泡到父控件，
            绑错地方外框就永远不变色。默认就是 ``widget``。
        idle_color: 未聚焦时的描边颜色，必须等于控件底部的填充色（默认
            ``COLOR_INPUT``），线才会「消失」。``TextArea`` 这类可换底色的
            控件要传自己实际用的底色。
        width: 描边槽位宽度，默认 ``BORDER_FOCUS_WIDTH``；聚焦前后一致，
            所以不会引起布局位移。
        on_width: 描边宽度变化时的回调，参数是当前的 ``border_width``；
            给「子控件内缩量要跟着边框走」的自定义容器用。
    """

    resting = T.COLOR_INPUT if idle_color is None else idle_color
    target = widget if source is None else source

    def apply(color: Any) -> None:
        """把描边颜色换成 ``color``；槽位宽度保持不变，避免布局位移。"""
        try:
            widget.configure(border_width=width, border_color=color)
        except Exception:  # noqa: BLE001 - 控件可能已经销毁
            return
        if on_width is not None:
            on_width(width)

    def focus_in(_event: Any = None) -> None:
        """聚焦：把描边换成主色，线亮出来。"""
        apply(T.COLOR_ACCENT)

    def focus_out(_event: Any = None) -> None:
        """失焦：把描边换回底色，线“消失”。"""
        apply(resting)

    for sequence, handler in (("<FocusIn>", focus_in), ("<FocusOut>", focus_out)):
        try:
            target.bind(sequence, handler, add="+")
        except Exception:  # noqa: BLE001
            target.bind(sequence, handler)


def ToolbarEntry(
    master: tk.Misc, placeholder: str, *, height: int = 40, menu: Any = True
) -> CTkEntry:
    """页面顶部搜索框：填充底 + 1px 描边。

    参数:
        master: 父容器。
        placeholder: 未输入时显示的灰色占位文字。
        height: 高度（像素），默认 40。
        menu: 右键菜单，含义同 :class:`CTkEntry`；``False`` 关掉。

    返回:
        尚未摆位的 ``CTkEntry``（带本库默认样式，支持 ``set`` / ``append`` / ``clear``）。
    """
    return CTkEntry(
        master,
        placeholder_text=placeholder,
        placeholder_text_color=T.COLOR_FAINT,
        height=height,
        corner_radius=T.RADIUS_LARGE,
        font=get_font(T.FONT_BODY),
        fg_color=T.COLOR_INPUT,
        border_width=1,
        border_color=T.COLOR_BORDER_INPUT,
        text_color=T.COLOR_TEXT,
        menu=menu,
    )


def FormEntry(
    master: tk.Misc,
    *,
    show: str = "",
    placeholder: str = "",
    height: int = 38,
    password: bool = False,
    menu: Any = True,
) -> CTkEntry:
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
        menu: 右键菜单，含义同 :class:`CTkEntry`；``False`` 关掉。

    返回:
        尚未摆位的 ``CTkEntry``。
    """
    return CTkEntry(
        master,
        show=("•" if password else show) or "",
        placeholder_text=placeholder,
        height=height,
        menu=menu,
    )


def Segmented(
    master: tk.Misc,
    values: Sequence[str],
    command: SegmentCommand = None,
    *,
    width: int = 300,
    height: int = 34,
    font: T.FontSpec = T.FONT_SMALL,
) -> ctk.CTkSegmentedButton:
    """统一样式的分段选择：浅一档的容器底，选中段用主色高亮。

    容器底用 ``COLOR_SOFT``（次要按钮那一档）：分段控件是「一组按钮」，
    和输入框的 ``COLOR_INPUT`` 底色区分开，两种控件挨在一起时不会糊成一块。

    选中段用 :data:`tokens.COLOR_ACTIVE`（偏青的激活色），和开关、勾选、单选、
    滑块的填充色一致，不再是主按钮那种高饱和蓝。
    ``CTkSegmentedButton`` 只有一份 ``text_color``，青底和浅底不可能共用同一种
    文字色，所以这里在选中项变化时把选中段的文字改成 ``COLOR_ACCENT_TEXT``、
    其余段改回 ``COLOR_TEXT``（``set()`` 也走同一条路径）。

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
        selected_color=T.COLOR_ACTIVE,
        unselected_hover_color=T.COLOR_SOFT_HOVER,
        selected_hover_color=T.COLOR_ACTIVE_HOVER,
        text_color=T.COLOR_TEXT,
        font=get_font(font) if not isinstance(font, ctk.CTkFont) else font,
        dynamic_resizing=False,
    )

    segments = getattr(button, "_buttons_dict", {})

    def alive(widget: Any) -> bool:
        """控件是否还活着；已经销毁时返回 ``False``。"""
        try:
            return bool(widget.winfo_exists())
        except Exception:  # noqa: BLE001 - 控件可能已经销毁
            return False

    def paint(value: str) -> None:
        """给选中的段上亮色文字，其余段用普通文字色。"""
        for name, segment in segments.items():
            if not alive(segment):
                continue
            try:
                segment.configure(
                    text_color=T.COLOR_ACCENT_TEXT if name == value else T.COLOR_TEXT
                )
            except Exception:  # noqa: BLE001
                continue

    original_set = button.set

    def select(value: str, **kwargs) -> None:
        """先上色再 ``set``：避免调用方 command 重建页面后按钮已销毁。"""
        # CTkSegmentedButton 内部点按钮时会调 set(value, from_button_callback=True)，
        # 所以这里必须把多余的关键字参数原样转回去，不能只声明一个 value。
        #
        # 先上色再 set：set 里会触发调用方的 command，而 command 很可能正是
        # 「切换主题 → 重建整个页面」，一旦重建，这些段按钮就被销毁了，
        # 之后再 configure 会抛 invalid command name。
        paint(value)
        original_set(value, **kwargs)

    def on_click(value: str) -> None:
        """点击段按钮：先上色，再回调调用方的 ``command``。"""
        paint(value)
        if command is not None:
            command(value)

    button.set = select  # type: ignore[method-assign]
    button.configure(command=on_click)

    if values:
        # 不留「一段都没选中」的中间态
        select(values[0])
    return button


def Switch(
    master: tk.Misc,
    command: SwitchCommand = None,
    *,
    text: str = "",
    width: int = 44,
) -> ctk.CTkSwitch:
    """设置页的开关：只留轨道，拨到右边时轨道变激活色。

    轨道用 ``COLOR_BORDER_STRONG`` 而不是 ``COLOR_SOFT``：后者在深色主题下
    （``#22242c``）和卡片底几乎同色，整个开关看起来就是一团黑；把手则取
    ``COLOR_MUTED``，深色下比轨道亮、浅色下比轨道暗，两个主题都分得清。
    拨到右边时用 ``COLOR_ACTIVE``（偏青），和勾选、单选、滑块同一个颜色。

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
        font=get_font(T.FONT_SMALL),
        text_color=T.COLOR_TEXT,
        fg_color=T.COLOR_BORDER_STRONG,
        progress_color=T.COLOR_ACTIVE,
        button_color=T.COLOR_BUTTON_KNOB,
        button_hover_color=T.COLOR_BUTTON_KNOB_HOVER,
        command=command,
    )


def Checkbox(
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
        fg_color=T.COLOR_ACTIVE,
        hover_color=T.COLOR_ACTIVE_HOVER,
        checkmark_color=T.COLOR_ACCENT_TEXT,
        text_color=T.COLOR_TEXT,
        font=get_font(T.FONT_SMALL),
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
        """某个单选框被选中：把变量里的值交给调用方的 ``command``。"""
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
            # 选中时 CTk 画的是「粗环 + 中间挖空」，挖空圆的直径 = 宽度 - 2 * 这个值。
            # 取 6 时挖空只剩 6px，150% 缩放下被取整成方块；取 4 留出 10px，才是圆的。
            border_width_checked=4,
            border_color=T.COLOR_BORDER_STRONG,
            fg_color=T.COLOR_ACTIVE,
            hover_color=T.COLOR_ACTIVE_HOVER,
            text_color=T.COLOR_TEXT,
            font=get_font(T.FONT_SMALL),
        )
        button.pack(anchor="w", pady=(0, gap) if index < len(values) - 1 else 0)

    if values:
        var.set(values[0])
    return frame, var


def Slider(
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
        # 高度就是把手的直径：12 比默认的 16 轻，轨道仍靠 border_width 压成 4px。
        height=12,
        # 圆角给大值让轨道和把手都成胶囊/正圆；button_length=0 表示把手是正圆。
        # 别把 border_width 设成 0：CTkSlider 是「整高画一圈 border、内层再画 fg」，
        # 轨道 = height - 2 * border_width，改成 0 会变成一根粗条。
        # 12 高配 4px 边框，正好留出 4px 轨道，和改小把手前的观感一致。
        border_width=4,
        corner_radius=1000,
        fg_color=T.COLOR_BORDER_STRONG,
        progress_color=T.COLOR_ACTIVE,
        button_color=T.COLOR_ACTIVE,
        button_hover_color=T.COLOR_ACTIVE_HOVER,
        button_corner_radius=1000,
        button_length=0,
        command=command,
    )


def ProgressBar(
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
        progress_color=T.COLOR_ACTIVE,
    )
    bar.set(max(0.0, min(1.0, value)))
    return bar


class Spinner(ctk.CTkFrame):
    """带上下箭头的步进输入框：可以走数字范围，也可以走一组备选文字。

    右侧是 canvas 画的两个小三角（不用字体符号，缩放后不会有马赛克）；
    点上半格加一步、点下半格减一步。数字模式下到边界就停住，不绕回。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        from_: float = 0,
        to: float = 100,
        increment: float = 1,
        values: Optional[Sequence[str]] = None,
        value: Any = None,
        command: Optional[Callable[[Any], None]] = None,
        placeholder: str = "",
        height: int = 36,
        width: int = 160,
        as_int: bool = True,
    ) -> None:
        """创建步进输入框。

        参数:
            master: 父容器。
            from_ / to / increment: 数字模式的起止与步长（闭区间）。
            values: 传了就走「一组文字」模式，上下箭头在列表里前后移动。
            value: 初始值；不传时数字模式取 ``from_``，列表模式取第一项。
            command: 每次步进或提交后的回调，参数是当前值。
            placeholder: 输入框为空时的灰色占位文字。
            height: 整体高度（逻辑像素），默认 36。
            width: 控件宽度（逻辑像素），默认 160。
            as_int: 数字模式下 ``get()`` 是否返回整数。
        """
        super().__init__(
            master,
            fg_color=T.COLOR_INPUT,
            border_width=1,
            border_color=T.COLOR_BORDER_INPUT,
            corner_radius=T.RADIUS_SMALL,
            height=height,
            width=width,
        )
        self.pack_propagate(False)
        # 和 DropField 同一个坑：CTk 默认把绘制高度取整到偶数，奇数物理像素时
        # 底边描边会被裁掉。
        self._draw_engine.set_round_to_even_numbers(False, False)
        self._draw()

        self._from = from_
        self._to = to
        self._increment = increment
        self._values = list(values) if values is not None else None
        self._command = command
        self._as_int = as_int
        self._height = height
        self._bg = color_of(T.COLOR_INPUT)
        self._arrow_photos: list = []

        # 先贴箭头、再放输入框：pack 按调用顺序分空间，反过来输入框会把箭头挤没
        self._arrows = tk.Canvas(
            self,
            width=22,
            height=height - 2,
            bg=self._bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._arrows.pack(side="right", fill="y", padx=(0, 5), pady=1)
        self._arrows.bind("<Button-1>", self._on_arrow)
        self._arrows.bind("<Configure>", lambda _e: self._draw_arrows())

        self.entry: CTkEntry = CTkEntry(
            self,
            fg_color="transparent",
            border_width=0,
            corner_radius=0,
            font=T.FONT_BODY,
            text_color=T.COLOR_TEXT,
            placeholder_text=placeholder,
            placeholder_text_color=T.COLOR_FAINT,
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(12, 2), pady=1)
        self.entry.bind("<Return>", self._commit)
        self.entry.bind("<FocusOut>", self._commit)

        if value is not None:
            self.set(value)
        elif self._values:
            self.set(self._values[0])
        else:
            self.set(self._from)
        self._draw_arrows()

    # ------------------------------------------------------------ 读写
    def get(self) -> Any:
        """当前值：数字模式按 ``as_int`` 返回 int/float，列表模式返回文字。"""
        text = self.entry.get().strip()
        if self._values is not None:
            return text
        return self._parse(text)

    def set(self, value: Any) -> None:
        """直接写入值（不触发回调，也不做越界钳制）。"""
        text = self._format(value)
        self.entry.delete(0, "end")
        self.entry.insert(0, text)

    # ------------------------------------------------------------ 内部
    def _parse(self, text: str) -> Any:
        """把输入框文字解析成数字；解析不了就退回起点。"""
        try:
            number = float(text)
        except (TypeError, ValueError):
            number = float(self._from)
        if self._as_int and float(number).is_integer():
            return int(number)
        return number

    def _format(self, value: Any) -> str:
        """把值格式化成输入框里的文字。"""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    def _step(self, direction: int) -> None:
        """上下挪一步：数字模式夹在区间里，列表模式夹在首尾之间。"""
        if self._values is not None:
            current = self.entry.get().strip()
            try:
                index = self._values.index(current)
            except ValueError:
                index = 0 if direction > 0 else len(self._values) - 1
            index = max(0, min(len(self._values) - 1, index + direction))
            self.set(self._values[index])
        else:
            current = self._parse(self.entry.get())
            stepped = current + direction * self._increment
            stepped = max(self._from, min(self._to, stepped))
            self.set(stepped)
        self._notify()

    def _commit(self, _event: Optional[tk.Event] = None) -> None:
        """回车或失焦：把手输的文字夹回区间里再写回。"""
        if self._values is not None:
            current = self.entry.get().strip()
            if current not in self._values and self._values:
                self.set(self._values[0])
        else:
            number = self._parse(self.entry.get())
            number = max(self._from, min(self._to, number))
            self.set(number)
        self._notify()

    def _notify(self) -> None:
        """把当前值交给调用方。"""
        if self._command is not None:
            self._command(self.get())

    def _on_arrow(self, event: tk.Event) -> None:
        """点上半个加一步、下半个减一步。"""
        middle = max(1, self._arrows.winfo_height()) / 2
        self._step(1 if event.y < middle else -1)

    def _draw_arrows(self) -> None:
        """重画两个小三角；高度变了会重新调用。

        照 ttkbootstrap 的 Spinbox：箭头用**图片**而不是按坐标画多边形。
        两个箭头是同一套绘制出的位图（只是上下翻转），尺寸严格一致；
        canvas 直接画多边形时，小数中点加取整会让两个三角形差 1px。
        """
        canvas = self._arrows
        canvas.delete("all")
        self._arrow_photos = []
        height = canvas.winfo_height()
        if height <= 1:
            # 刚建好还没布局，先用构造时的高度兜底，否则会画在不可见的位置
            height = self._height - 2
        middle = height // 2
        # canvas 只认具体的颜色字符串，令牌里的 (浅色, 深色) 元组要先解析
        color = color_of(T.COLOR_MUTED)
        for index, center in enumerate((middle - 9, middle + 9)):
            up = index == 0
            if _HAS_PIL:
                photo = self._arrow_image(up, color)
                self._arrow_photos.append(photo)
                canvas.create_image(9, center, image=photo, anchor="center")
                continue
            if up:
                points = (3, center + 3, 15, center + 3, 9, center - 3)
            else:
                points = (3, center - 3, 15, center - 3, 9, center + 3)
            canvas.create_polygon(*points, fill=color, outline="")

    @staticmethod
    def _arrow_image(up: bool, color: str, width: int = 12, height: int = 7):
        """画一个上/下三角的小图：4 倍尺寸画完再缩，边缘平滑。"""
        scale = 4
        image = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
        pen = ImageDraw.Draw(image)
        w, h = width * scale, height * scale
        if up:
            points = [(0, h - 1), (w - 1, h - 1), (w // 2, 0)]
        else:
            points = [(0, 0), (w - 1, 0), (w // 2, h - 1)]
        pen.polygon(points, fill=color)
        return ImageTk.PhotoImage(image.resize((width, height), Image.LANCZOS))

    def configure(self, **kwargs: Any) -> None:
        """改外观后补一次重绘，圆角/描边颜色才会跟着变。"""
        super().configure(**kwargs)
        if "fg_color" in kwargs or "border_color" in kwargs:
            self._draw()

