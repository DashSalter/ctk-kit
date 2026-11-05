"""输入与选择控件：搜索框、表单输入、分段选择、开关、勾选、单选、滑块、进度条。

分段选择是一块自绘控件：容器铺 ``COLOR_SOFT``，选中块（``COLOR_ACTIVE`` 的
圆角条）在段之间平移，切换时带缓动；用整块按钮改色做不出「滑过去」的效果。

选择类控件（勾选、单选、开关、滑块）只把「选中/填充」部分交给主色，未选中态
一律用 ``COLOR_BORDER_STRONG`` 描边、``COLOR_SOFT`` 做轨道，避免深色主题下
一排控件全是高饱和蓝。

所有工厂只返回控件，不负责摆位；``CTkEntry`` 是默认带库样式的类。
"""

from __future__ import annotations

import contextlib
import time
import tkinter as tk
from typing import Any, Callable, Optional, Sequence, Tuple

import customtkinter as ctk

from . import tokens as T
from .choices import Check, Radio
from .context_menu import attach_edit_menu
from .fonts import get_font
from .paint import blend_hex, cached
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
# 滑块超采样倍数：先按 4 倍画，再 LANCZOS 缩回去，边缘才平滑。
_SLIDER_SCALE = 4
#: 滑块轨道高度（逻辑像素）。
_SLIDER_TRACK = 4
#: 滑块圆钮直径（逻辑像素）。
_SLIDER_KNOB = 14
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


#: 分段选择滑块的内缩（逻辑像素）：留一圈容器底色当描边。
_SEGMENT_INSET = 2
#: 滑块滑动时长（毫秒）。
_SEGMENT_ANIM_MS = 170
#: 滑块动画帧间隔（毫秒）。
_SEGMENT_ANIM_STEP = 16


@cached
def _segment_slider(width: int, height: int, radius: int, color: str):
    """画选中块的圆角矩形；超采样后缩回，边缘才有抗锯齿。"""
    scale = 4
    image = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pen.rounded_rectangle(
        (0, 0, width * scale - 1, height * scale - 1),
        radius=radius * scale,
        fill=color,
    )
    return image.resize((width, height), Image.LANCZOS)


class Segmented(ctk.CTkFrame):
    """统一样式的分段选择：浅一档的容器底，选中块滑到目标段。

    容器底用 ``COLOR_SOFT``（次要按钮那一档）：分段控件是「一组按钮」，
    和输入框的 ``COLOR_INPUT`` 底色区分开，两种控件挨在一起时不会糊成一块。

    选中块用 :data:`tokens.COLOR_ACTIVE`（偏青的激活色），和开关、勾选、单选、
    滑块的填充色一致。选中块的文字用 ``COLOR_ACCENT_TEXT``，其余段用
    ``COLOR_TEXT``；切换时滑块平移、文字颜色同步过渡。

    和 ``CTkSegmentedButton`` 的实现不同：它靠每个段按钮自己变色，没有可移动的
    选中块；这里用一块 canvas 画滑块和文字，才能做「滑过去」的动画。

    参数:
        master: 父容器。
        values: 各段文字，按显示顺序排列；非空时默认选中第一项。
        command: 切换回调，参数是被选中的那一段文字。
        width: 整体宽度（像素），默认 300。
        height: 高度（像素），默认 34。
        font: 字体规格，默认 :data:`tokens.FONT_SMALL`。
    """

    def __init__(
        self,
        master: tk.Misc,
        values: Sequence[str] = (),
        command: SegmentCommand = None,
        *,
        width: int = 300,
        height: int = 34,
        font: T.FontSpec = T.FONT_SMALL,
        corner_radius: int = T.RADIUS_SMALL,
    ) -> None:
        super().__init__(
            master,
            width=width,
            height=height,
            fg_color=T.COLOR_SOFT,
            corner_radius=corner_radius,
        )
        self._values = [str(value) for value in values]
        self._command = command
        self._font = get_font(font) if not isinstance(font, ctk.CTkFont) else font
        self._radius = corner_radius
        self._index = 0 if self._values else -1
        self._hover = -1
        self._enabled = True
        # 浮点段索引：动画期间落在两段之间
        self._progress = float(self._index) if self._index >= 0 else 0.0
        self._anim_job: Optional[str] = None
        self._anim_from = self._progress
        self._anim_to = self._progress
        self._anim_started = 0.0
        self._seg_w = 0.0
        self._slider: Optional[int] = None
        self._slider_photo = None
        self._texts: list[int] = []
        self._inset = max(1, int(round(_SEGMENT_INSET * self._get_widget_scaling())))

        self._seg_canvas = tk.Canvas(
            self,
            highlightthickness=0,
            borderwidth=0,
            bg=color_of(T.COLOR_SOFT),
        )
        # canvas 是方形，四角要落在容器的圆角弧以内，否则会把圆角顶成直角。
        # 圆心到角点的最短内缩约是 radius * (1 - 1/√2) ≈ 0.29R，这里取 0.35R 留余量。
        radius_px = self._radius * self._get_widget_scaling()
        margin = max(1, int(radius_px * 0.35 + 0.999))
        self._seg_canvas.place(
            x=margin,
            y=margin,
            relwidth=1,
            relheight=1,
            width=-2 * margin,
            height=-2 * margin,
        )
        self._seg_canvas.bind("<Button-1>", self._on_click)
        self._seg_canvas.bind("<Motion>", self._on_motion)
        self._seg_canvas.bind("<Leave>", self._on_leave)
        self._seg_canvas.bind("<Configure>", self._on_configure)

    # ------------------------------------------------------------ 公共 API
    def set_enabled(self, enabled: bool) -> None:
        """启用 / 禁用。禁用时点击无反应，整块换成输入框底显得「灰掉」。"""
        self._enabled = bool(enabled)
        base = T.COLOR_SOFT if self._enabled else T.COLOR_INPUT
        try:
            self.configure(fg_color=base)
            self._seg_canvas.configure(bg=color_of(base))
        except Exception:  # noqa: BLE001 - 窗口销毁中
            pass

    def get(self) -> str:
        """当前选中段文字；没有段时返回空字符串。"""
        if 0 <= self._index < len(self._values):
            return self._values[self._index]
        return ""

    def set(self, value: str, **kwargs: Any) -> None:
        """选中 ``value``；和 ``CTkSegmentedButton`` 一样会触发 ``command``。"""
        try:
            index = self._values.index(value)
        except ValueError:
            return
        if index == self._index and not kwargs.get("from_button_callback"):
            return
        self._index = index
        self._animate_to(float(index))
        if self._command is not None:
            self._command(value)

    def configure(self, require_redraw: bool = False, **kwargs: Any) -> Any:
        """支持 ``values=`` / ``command=``，其余参数转给 ``CTkFrame``。"""
        if "values" in kwargs:
            self._set_values(list(kwargs.pop("values")))
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if kwargs:
            return super().configure(require_redraw=require_redraw, **kwargs)
        return self

    def cget(self, attribute_name: str) -> Any:
        """读回 ``values`` / ``command``，与 ``CTkSegmentedButton`` 对齐。"""
        if attribute_name == "values":
            return list(self._values)
        if attribute_name == "command":
            return self._command
        return super().cget(attribute_name)

    # ------------------------------------------------------------ 布局
    def _set_values(self, values: Sequence[str]) -> None:
        """换一组段；原选中项还在就保留，否则回到第一段。"""
        current = self.get()
        self._values = [str(value) for value in values]
        if not self._values:
            self._index = -1
        elif current in self._values:
            self._index = self._values.index(current)
        else:
            self._index = 0
        self._progress = float(self._index) if self._index >= 0 else 0.0
        self._hover = -1
        self._layout()

    def _on_configure(self, _event: tk.Event) -> None:
        self._layout()

    def _layout(self) -> None:
        """按 canvas 实际尺寸重排滑块与文字。"""
        width = self._seg_canvas.winfo_width()
        height = self._seg_canvas.winfo_height()
        if width <= 1 or height <= 1:
            return
        if not self._values:
            self._seg_canvas.delete("all")
            self._slider = None
            self._texts = []
            return
        self._seg_w = width / len(self._values)
        self._draw_sliders(height)
        self._draw_texts(height)

    def _draw_sliders(self, height: int) -> None:
        """滑块只有一块，尺寸随段宽变；位置由 ``_place_slider`` 更新。"""
        inset = self._inset
        slider_w = max(2, int(round(self._seg_w)) - 2 * inset)
        slider_h = max(2, height - 2 * inset)
        radius = max(1, min(slider_h // 2, int(round(self._radius))))
        source = _segment_slider(
            slider_w, slider_h, radius, color_of(T.COLOR_ACTIVE)
        )
        # 只有 Pillow 在时才画得出抗锯齿滑块；没有就退回纯色矩形。
        if _HAS_PIL:
            photo = ImageTk.PhotoImage(source)
        else:
            photo = None
        self._slider_photo = photo
        if self._slider is None or not self._seg_canvas.winfo_exists():
            self._seg_canvas.delete("slider")
            if photo is not None:
                self._slider = self._seg_canvas.create_image(
                    0, inset, anchor="nw", image=photo, tags="slider"
                )
            else:
                self._slider = None
                self._seg_canvas.create_rectangle(
                    0, inset, slider_w, inset + slider_h,
                    fill=color_of(T.COLOR_ACTIVE), width=0, tags="slider",
                )
        else:
            if photo is not None:
                self._seg_canvas.itemconfig(self._slider, image=photo)
            self._seg_canvas.coords(
                self._slider,
                self._progress * self._seg_w + inset,
                inset,
            )
        self._place_slider()

    def _place_slider(self) -> None:
        if self._slider is None:
            return
        x = self._progress * self._seg_w + self._inset
        self._seg_canvas.coords(self._slider, x, self._inset)

    def _draw_texts(self, height: int) -> None:
        for item in self._texts:
            self._seg_canvas.delete(item)
        self._texts = []
        for index, value in enumerate(self._values):
            center = (index + 0.5) * self._seg_w
            item = self._seg_canvas.create_text(
                center,
                height / 2,
                text=value,
                font=self._font,
                fill=self._text_color(index),
                tags="seg-text",
            )
            self._texts.append(item)

    def _text_color(self, index: int) -> str:
        """选中度：滑块覆盖到的段用浅色文字，其余用普通文字色。"""
        ratio = max(0.0, 1.0 - abs(self._progress - index))
        if self._anim_job is None:
            ratio = 1.0 if index == self._index else 0.0
        if index == self._hover and self._anim_job is None and index != self._index:
            ratio = 0.25
        return blend_hex(
            color_of(T.COLOR_TEXT), color_of(T.COLOR_ACCENT_TEXT), ratio
        )

    def _paint_texts(self) -> None:
        for index, item in enumerate(self._texts):
            self._seg_canvas.itemconfig(item, fill=self._text_color(index))

    # ------------------------------------------------------------ 交互
    def _segment_at(self, x: int) -> int:
        if not self._values or self._seg_w <= 0:
            return -1
        index = int(x // self._seg_w)
        return max(0, min(len(self._values) - 1, index))

    def _on_click(self, event: tk.Event) -> None:
        if not self._enabled:
            return
        index = self._segment_at(event.x)
        if index < 0:
            return
        self._index = index
        self._animate_to(float(index))
        if self._command is not None:
            self._command(self._values[index])

    def _on_motion(self, event: tk.Event) -> None:
        if not self._enabled:
            return
        index = self._segment_at(event.x)
        if index != self._hover:
            self._hover = index
            self._paint_texts()
            self._seg_canvas.configure(cursor="hand2")
        elif event.widget is self._seg_canvas:
            self._seg_canvas.configure(cursor="hand2")

    def _on_leave(self, _event: tk.Event) -> None:
        if self._hover != -1:
            self._hover = -1
            self._paint_texts()
        self._seg_canvas.configure(cursor="")

    # ------------------------------------------------------------ 动画
    def _animate_to(self, target: float) -> None:
        """滑块从当前位置滑到 ``target`` 段。"""
        self._anim_from = self._progress
        self._anim_to = target
        if abs(self._anim_from - target) < 0.001:
            self._progress = target
            if self._anim_job is not None:
                with contextlib.suppress(tk.TclError):
                    self.after_cancel(self._anim_job)
                self._anim_job = None
            self._place_slider()
            self._paint_texts()
            return
        self._anim_started = time.perf_counter()
        if self._anim_job is None:
            self._anim_job = self.after(_SEGMENT_ANIM_STEP, self._anim_step)

    def _anim_step(self) -> None:
        self._anim_job = None
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        elapsed = (time.perf_counter() - self._anim_started) * 1000
        ratio = min(1.0, elapsed / _SEGMENT_ANIM_MS)
        if ratio >= 1.0:
            self._progress = self._anim_to
            self._place_slider()
            self._paint_texts()
            return
        eased = 1.0 - (1.0 - ratio) ** 3
        self._progress = self._anim_from + (self._anim_to - self._anim_from) * eased
        self._place_slider()
        self._paint_texts()
        self._anim_job = self.after(_SEGMENT_ANIM_STEP, self._anim_step)

    def destroy(self) -> None:
        if self._anim_job is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._anim_job)
            self._anim_job = None
        super().destroy()


# ---------------------------------------------------------------- 开关

#: 开关轨道尺寸（逻辑像素），和 CTkSwitch 的默认值一致。
_SWITCH_TRACK = (36, 18)
#: 圆球与轨道上下边缘的间距（逻辑像素）。
_SWITCH_GAP = 3
#: 画开关时的超采样倍数。
_SWITCH_SCALE = 4
#: 拨动动画时长（毫秒）；太短看不出缓冲，太长显得拖沓。
_SWITCH_ANIM_MS = 170
#: 动画帧间隔（毫秒）；Tk 定时器实际会落到 16–31ms，按经过时间插值即可。
_SWITCH_ANIM_STEP = 16


def _draw_switch(track: str, knob: str, progress: float):
    """按 ``progress``（0=关、1=开）画开关图，圆心位置连续插值。"""
    width, height = _SWITCH_TRACK
    scale = _SWITCH_SCALE
    total_w = width * scale
    total_h = height * scale
    image = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pen.rounded_rectangle(
        (0, 0, total_w - 1, total_h - 1),
        radius=total_h / 2,
        fill=track,
    )

    gap = _SWITCH_GAP * scale
    radius = total_h / 2 - gap
    center_y = total_h / 2
    left = gap + radius
    right = total_w - gap - radius
    center_x = left + (right - left) * progress
    pen.ellipse(
        (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
        fill=knob,
    )
    return image


@cached
def _switch_image(track: str, knob: str, checked: bool):
    """画一张终态开关图：胶囊轨道 + 圆球，4 倍尺寸画完再交给 ``CTkImage`` 缩。"""
    return _draw_switch(track, knob, 1.0 if checked else 0.0)


def _switch_picture(checked: bool, hover: bool, progress: Optional[float] = None):
    """开关的深浅两张图：``CTkImage`` 会按当前外观挑一张。

    ``progress`` 给定时按中间态画（0=关、1=开），动画用；不传则取终态，
    走 :func:`_switch_image` 的缓存。
    """
    ratio = (1.0 if checked else 0.0) if progress is None else progress
    knob = T.COLOR_BUTTON_KNOB_HOVER if hover else T.COLOR_BUTTON_KNOB
    light_track = blend_hex(T.COLOR_BORDER_STRONG[0], T.COLOR_ACTIVE[0], ratio)
    dark_track = blend_hex(T.COLOR_BORDER_STRONG[1], T.COLOR_ACTIVE[1], ratio)
    if progress is None:
        return (
            _switch_image(light_track, knob[0], checked),
            _switch_image(dark_track, knob[1], checked),
        )
    return (
        _draw_switch(light_track, knob[0], ratio),
        _draw_switch(dark_track, knob[1], ratio),
    )


class Switch(ctk.CTkFrame):
    """设置页的开关：胶囊轨道 + 圆球，Pillow 画的抗锯齿图片。

    和 ``Check`` / ``Radio`` 一样不用 canvas 图元：Tk 的 canvas 不做抗锯齿，
    直接画圆角矩形和圆，边缘会有一格一格的阶梯。这里用 Pillow 在 4 倍尺寸
    上画好，再交给 ``CTkImage`` 缩到逻辑尺寸，HighDPI 下也跟着缩放。

    轨道用 ``COLOR_BORDER_STRONG`` 而不是 ``COLOR_SOFT``：后者在深色主题下
    （``#22242c``）和卡片底几乎同色，整个开关看起来就是一团黑；把手则取
    ``COLOR_BUTTON_KNOB``，深色下比轨道亮、浅色下比轨道深，两个主题都分得清。
    悬停时换成 ``COLOR_BUTTON_KNOB_HOVER``，同样按「浅色走深、深色走亮」取色，
    不会糊进轨道里。
    拨到右边时轨道用 ``COLOR_ACTIVE``（偏青），和勾选、单选、滑块同一个颜色。

    参数:
        master: 父容器。
        command: 拨动回调，不接收参数；用 ``toggle()`` 或点击都会触发。
        text: 轨道右侧的文字，默认空（设置页那种「标签在左边」的排法）。
        width: 控件总宽（逻辑像素），默认 44；轨道本身固定 36 宽。

    方法 ``get()`` / ``select()`` / ``deselect()`` / ``toggle()`` 与
    ``CTkSwitch`` 一致；``configure(command=...)`` 可以后挂回调。
    """

    def __init__(
        self,
        master: tk.Misc,
        command: SwitchCommand = None,
        *,
        text: str = "",
        width: int = 44,
    ) -> None:
        super().__init__(master, fg_color="transparent", width=width, height=24)
        self._command = command
        self._checked = False
        self._hover = False
        self._photos: dict = {}
        self._photo = None
        # 视觉进度（0=关、1=开），动画期间与 _checked 不同步
        self._progress = 0.0
        self._anim_job: Optional[str] = None
        self._anim_from = 0.0
        self._anim_to = 0.0
        self._anim_started = 0.0

        self._track = ctk.CTkLabel(
            self,
            text="",
            width=_SWITCH_TRACK[0],
            height=_SWITCH_TRACK[1],
            fg_color="transparent",
            cursor="hand2",
        )
        self._track.pack(side="left")

        self._label = ctk.CTkLabel(
            self,
            text=text,
            font=get_font(T.FONT_SMALL),
            text_color=T.COLOR_TEXT,
            fg_color="transparent",
            anchor="w",
            cursor="hand2",
        )
        self._label.pack(side="left", padx=(6, 0))

        for widget in (self._track, self._label):
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

        self._refresh()

    # ------------------------------------------------------------ 绘制
    def _refresh(self) -> None:
        """按当前状态换图；同一状态复用已经画好的 ``CTkImage``。"""
        if not _HAS_PIL:
            self._track.configure(text="开" if self._checked else "关")
            return
        if self._anim_job is not None:
            # 动画中的 hover 变化只换圆球颜色，不跳回终态
            self._paint(self._progress)
            return
        self._progress = 1.0 if self._checked else 0.0
        key = (self._checked, self._hover)
        photo = self._photos.get(key)
        if photo is None:
            light, dark = _switch_picture(self._checked, self._hover)
            photo = ctk.CTkImage(
                light_image=light, dark_image=dark, size=_SWITCH_TRACK
            )
            self._photos[key] = photo
        self._photo = photo
        self._track.configure(image=self._photo, text="")

    def _paint(self, progress: float) -> None:
        """画一帧中间态；不走缓存，动画帧的键会无限增长。"""
        if not _HAS_PIL:
            return
        light, dark = _switch_picture(self._checked, self._hover, progress)
        photo = ctk.CTkImage(light_image=light, dark_image=dark, size=_SWITCH_TRACK)
        self._photo = photo
        self._track.configure(image=photo, text="")

    # ------------------------------------------------------------ 动画
    def _animate_to(self, target: float) -> None:
        """从当前进度补间到 ``target``；正在动的动画直接改目标，不重启动。"""
        if not _HAS_PIL:
            self._refresh()
            return
        self._anim_from = self._progress
        self._anim_to = target
        if abs(self._anim_from - target) < 0.001:
            self._progress = target
            if self._anim_job is not None:
                try:
                    self.after_cancel(self._anim_job)
                except tk.TclError:
                    pass
                self._anim_job = None
            self._refresh()
            return
        self._anim_started = time.perf_counter()
        if self._anim_job is None:
            self._anim_job = self.after(_SWITCH_ANIM_STEP, self._anim_step)

    def _anim_step(self) -> None:
        """按真实经过时间插值；Tk 的 after 会抖到 30ms，不能按帧数累加。"""
        self._anim_job = None
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        elapsed = (time.perf_counter() - self._anim_started) * 1000
        ratio = min(1.0, elapsed / _SWITCH_ANIM_MS)
        eased = 1.0 - (1.0 - ratio) ** 3  # ease_out_cubic
        if ratio >= 1.0:
            self._progress = self._anim_to
            self._refresh()
            return
        self._progress = self._anim_from + (self._anim_to - self._anim_from) * eased
        self._paint(self._progress)
        self._anim_job = self.after(_SWITCH_ANIM_STEP, self._anim_step)

    # ------------------------------------------------------------ 交互
    def _on_click(self, _event: Optional[tk.Event] = None) -> None:
        self.toggle()

    def _on_enter(self, _event: Optional[tk.Event] = None) -> None:
        if not self._hover:
            self._hover = True
            self._refresh()

    def _on_leave(self, _event: Optional[tk.Event] = None) -> None:
        if self._hover:
            self._hover = False
            self._refresh()

    # ------------------------------------------------------------ 状态
    def toggle(self, _event: Optional[tk.Event] = None) -> None:
        """拨动一次并触发 ``command``。"""
        self._checked = not self._checked
        self._animate_to(1.0 if self._checked else 0.0)
        if self._command is not None:
            self._command()

    def select(self) -> None:
        """拨到右边（不触发 ``command``）。"""
        self._checked = True
        self._animate_to(1.0)

    def deselect(self) -> None:
        """拨回左边（不触发 ``command``）。"""
        self._checked = False
        self._animate_to(0.0)

    def get(self) -> int:
        """0 / 1。"""
        return 1 if self._checked else 0

    def destroy(self) -> None:
        """销毁前取消动画帧；页面重建时不留 ``after`` 残留。"""
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except tk.TclError:
                pass
            self._anim_job = None
        super().destroy()

    def configure(self, **kwargs) -> None:
        """支持 ``configure(command=...)``，和 CTk 控件的用法一致。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "text" in kwargs:
            self._label.configure(text=kwargs.pop("text"))
        if kwargs:
            super().configure(**kwargs)


def Checkbox(
        master: tk.Misc,
        text: str = "",
        command: SwitchCommand = None,
        *,
        width: int = 20,
        height: int = 20,
) -> "Check":
    """勾选框：未选中是描边空心方块，选中后填主色并打勾。

    指示符是 Pillow 画的抗锯齿图片（4 倍尺寸画完再缩），圆形/方块边缘比
    canvas 直接画要平滑。

    参数:
        master: 父容器。
        text: 方块右侧的文字。
        command: 勾选/取消回调，不接收参数。
        width: 方块宽度（像素），默认 20。
        height: 方块高度（像素），默认 20。

    返回:
        尚未摆位的 ``Check``；``get()`` 返回 0/1，``select()`` / ``deselect()`` 可直接改。
    """
    return Check(
        master,
        text,
        command,
        width=width,
        height=height,
        font=get_font(T.FONT_SMALL),
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
        button = Radio(
            frame,
            value,
            value,
            variable=var,
            command=on_select,
            width=20,
            height=20,
            font=get_font(T.FONT_SMALL),
        )
        button.pack(anchor="w", pady=(0, gap) if index < len(values) - 1 else 0)

    if values:
        var.set(values[0])
    return frame, var


def _slider_bg(master: tk.Misc) -> str:
    """给 canvas 找一个实际背景色：canvas 不认 ``transparent``。"""
    try:
        value = master.cget("fg_color")
    except Exception:  # noqa: BLE001
        value = None
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return color_of(value)
    if isinstance(value, str) and value and value != "transparent":
        return value
    return color_of(T.COLOR_CARD)


class Slider(ctk.CTkFrame):
    """滑块：轨道底色淡，已滑过的部分和圆钮是主色。

    自绘（Pillow 4 倍超采样再 LANCZOS 缩放），圆钮和轨道两端没有锯齿。

    参数:
        master: 父容器。
        command: 拖动回调，参数是当前数值（float）。
        from_: 最小值，默认 0。
        to: 最大值，默认 100。
        steps: 分段数；``0`` 表示连续，正整数表示只能停在等分点上。
        width: 宽度（像素），默认 220。

    方法:
        get(): 当前值。
        set(value, notify=False): 改值，``notify=True`` 时也回调。
    """

    def __init__(
        self,
        master: tk.Misc,
        command: SliderCommand = None,
        *,
        from_: float = 0.0,
        to: float = 100.0,
        steps: int = 0,
        width: int = 220,
        state: str = "normal",
        **kwargs: Any,
    ) -> None:
        """建滑块；初值在 ``from_``。"""
        super().__init__(master, fg_color="transparent", **kwargs)

        self._from = float(from_)
        self._to = float(to) if float(to) != float(from_) else float(from_) + 1.0
        self._steps = max(0, int(steps))
        self._command = command
        self._width = max(_SLIDER_KNOB + 8, int(width))
        self._height = _SLIDER_KNOB + 4
        self._pad = _SLIDER_KNOB / 2 + 1
        self._value = self._clamp(self._from)
        self._state = str(state or "normal")
        self._photo = None

        self._canvas = tk.Canvas(
            self,
            width=self._width,
            height=self._height,
            bg=_slider_bg(self),
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._canvas.pack()
        self._canvas.bind("<Button-1>", self._press)
        self._canvas.bind("<B1-Motion>", self._drag)
        self._canvas.bind("<ButtonRelease-1>", self._release)
        self._render()

    # ---- 取值 / 赋值 ----------------------------------------------------

    def get(self) -> float:
        """当前值。"""
        return self._value

    def set(self, value: float, notify: bool = False) -> None:
        """改值并重画；``notify=True`` 时也触发回调。"""
        wrapped = self._clamp(value)
        if wrapped == self._value:
            return
        self._value = wrapped
        self._render()
        if notify and self._command is not None:
            self._command(self._value)

    def configure(self, **kwargs: Any) -> None:
        """支持 ``command`` / ``state``，其余交给 ``CTkFrame``。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "state" in kwargs:
            self._state = str(kwargs.pop("state") or "normal")
            self._render()
        if kwargs:
            super().configure(**kwargs)

    config = configure

    # ---- 坐标换算 ------------------------------------------------------

    def _clamp(self, value: float) -> float:
        """夹到区间并按 ``steps`` 吸附。"""
        value = max(self._from, min(self._to, float(value)))
        if self._steps > 0:
            step = (self._to - self._from) / self._steps
            if step > 0:
                value = self._from + round((value - self._from) / step) * step
        return max(self._from, min(self._to, value))

    def _track_width(self) -> float:
        return max(1.0, self._width - 2 * self._pad)

    def _value_to_x(self, value: float) -> float:
        """值 → 画布上的 x 坐标。"""
        ratio = (value - self._from) / (self._to - self._from)
        return self._pad + ratio * self._track_width()

    def _x_to_value(self, x: float) -> float:
        """画布 x 坐标 → 值。"""
        ratio = (x - self._pad) / self._track_width()
        return self._clamp(self._from + ratio * (self._to - self._from))

    # ---- 鼠标 ----------------------------------------------------------

    def _press(self, event: tk.Event) -> None:
        """按下：立刻跳到点击位置。"""
        if self._state == "disabled":
            return
        self._value = self._x_to_value(event.x)
        self._render()
        if self._command is not None:
            self._command(self._value)

    def _drag(self, event: tk.Event) -> None:
        """拖动：连续更新。"""
        if self._state == "disabled":
            return
        value = self._x_to_value(event.x)
        if value == self._value:
            return
        self._value = value
        self._render()
        if self._command is not None:
            self._command(self._value)

    def _release(self, _event: tk.Event) -> None:
        """松开：无需额外动作（拖动时已经回调过）。"""

    # ---- 绘制 ----------------------------------------------------------

    def _render(self) -> None:
        """画轨道、已滑过段和圆钮。"""
        canvas = self._canvas
        canvas.delete("all")
        track = color_of(T.COLOR_BORDER_STRONG)
        active = color_of(
            T.COLOR_MUTED if self._state == "disabled" else T.COLOR_ACTIVE
        )

        if not _HAS_PIL:
            self._render_plain(track, active)
            return

        scale = _SLIDER_SCALE
        w, h = self._width, self._height
        image = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
        pen = ImageDraw.Draw(image)
        center = h * scale / 2
        bar = _SLIDER_TRACK * scale
        x0 = self._pad * scale
        x1 = (w - self._pad) * scale
        knob_x = self._value_to_x(self._value) * scale

        pen.rounded_rectangle(
            (x0, center - bar / 2, x1, center + bar / 2),
            radius=bar / 2,
            fill=track,
        )
        if knob_x > x0:
            pen.rounded_rectangle(
                (x0, center - bar / 2, knob_x, center + bar / 2),
                radius=bar / 2,
                fill=active,
            )
        radius = _SLIDER_KNOB * scale / 2
        pen.ellipse(
            (knob_x - radius, center - radius, knob_x + radius, center + radius),
            fill=active,
        )

        self._photo = ImageTk.PhotoImage(image.resize((w, h), Image.LANCZOS))
        canvas.create_image(0, 0, anchor="nw", image=self._photo)

    def _render_plain(self, track: str, active: str) -> None:
        """没装 Pillow 时的退路：直角轨道 + 硬边圆钮。"""
        canvas = self._canvas
        center = self._height / 2
        half = _SLIDER_TRACK / 2
        x0 = self._pad
        x1 = self._width - self._pad
        knob_x = self._value_to_x(self._value)
        canvas.create_rectangle(x0, center - half, x1, center + half, fill=track, outline="")
        if knob_x > x0:
            canvas.create_rectangle(
                x0, center - half, knob_x, center + half, fill=active, outline=""
            )
        radius = _SLIDER_KNOB / 2
        canvas.create_oval(
            knob_x - radius,
            center - radius,
            knob_x + radius,
            center + radius,
            fill=active,
            outline="",
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
        self._arrows.pack(side="right", fill="y", padx=(0, 7), pady=1)
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
