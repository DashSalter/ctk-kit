"""柱状图：Canvas 自绘，颜色和字体都跟着主题令牌走。

不依赖 matplotlib 这类绘图库：网格、坐标轴用 canvas 图元，柱体用 Pillow
在 3 倍尺寸上画好再缩回来（Tk 的 canvas 不做抗锯齿，直接画圆角会有硬边）。
Pillow 没装时退回直角矩形，功能不变。

用法::

    from ctk_kit import BarChart

    chart = BarChart(card, values=[120, 180, 150], categories=["周一", "周二", "周三"])
    chart.pack(fill="both", expand=True)
    chart.set([90, 140, 130])          # 换一组数据，只重画，不重建控件

换主题 / 换配色后 :mod:`ctk_kit.theming` 会调用 ``apply_theme()``，
图表按当前令牌自动重画；字号变化走 :func:`ctk_kit.fonts.get_font`，
不会出现「页面换了字体、图表还是旧字号」。
"""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import font as tkfont
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import customtkinter as ctk

from . import tokens as T
from .chain import Chainable
from .fonts import get_font
from .paint import blend_hex
from .theme import color_of

try:  # Pillow 是可选依赖
    from PIL import Image, ImageDraw, ImageTk

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

__all__ = ["BarChart", "LineChart", "PieChart", "RadarChart", "ScatterChart"]

ColorArg = Union[str, Sequence[str]]
Formatter = Union[str, Callable[[float], str]]

#: 超采样倍数：先画这么大再缩回去，柱体上沿才有渐变过渡。
_SUPERSAMPLE = 3


def _to_float(value: Any) -> float:
    """把任意输入转成有限浮点数；转不了或非有限值按 0 处理。"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def _default_format(value: float) -> str:
    """默认的数值文字：整数不带小数点，小数最多留两位。"""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _nice_ticks(low: float, high: float, count: int = 5) -> List[float]:
    """生成「整齐」的刻度：步长只取 1 / 2 / 2.5 / 5 / 10 乘 10 的幂。

    参数:
        low / high: 数据范围；顺序反了会自动交换，相等时补成 1。
        count: 期望的刻度段数（实际数量可能略有出入）。

    返回:
        从小到大排列的刻度值，首尾覆盖 ``low`` / ``high``。
    """
    if not math.isfinite(low) or not math.isfinite(high):
        return [0.0, 1.0]
    if high < low:
        low, high = high, low
    if high - low < 1e-9:
        high = low + 1.0

    raw = (high - low) / max(1, int(count))
    magnitude = 10.0 ** math.floor(math.log10(raw))
    step = magnitude
    for multiplier in (1.0, 2.0, 2.5, 5.0, 10.0):
        step = multiplier * magnitude
        if step >= raw:
            break

    start = math.floor(low / step) * step
    end = math.ceil(high / step) * step
    ticks: List[float] = []
    value = start
    # 用 0.5 个步长兜底，避免浮点误差把最后一个刻度漏掉
    while value <= end + step * 0.5:
        ticks.append(round(value, 10))
        value += step
    return ticks or [low, high]


def _to_hex(widget: tk.Misc, color: str) -> str:
    """把 Tk 认的颜色名（如 ``gray14``）转成 ``#rrggbb``，Pillow 才认。"""
    if not color or color.startswith("#"):
        return color
    try:
        red, green, blue = widget.winfo_rgb(color)
        return f"#{red // 257:02x}{green // 257:02x}{blue // 257:02x}"
    except Exception:  # noqa: BLE001 - 控件已销毁 / 颜色名不合法
        return color


def _canvas_bg(master: tk.Misc) -> str:
    """给 canvas 找一个实际背景色：tk 的 canvas 不认 ``transparent``。

    透明容器会一直往上找，直到遇到有实色的父控件；都没有就用窗口底色。
    """
    widget: Optional[tk.Misc] = master
    while widget is not None:
        try:
            value = widget.cget("fg_color")
        except Exception:  # noqa: BLE001 - 原生 tk 控件没有 fg_color
            value = None
        if isinstance(value, (tuple, list)) and value:
            return _to_hex(widget, color_of(value))
        if isinstance(value, str) and value and value != "transparent":
            return _to_hex(widget, value)
        parent = getattr(widget, "master", None)
        if parent is widget:
            break
        widget = parent
    return color_of(T.COLOR_BG)


def _fit_text(text: str, measure: Callable[[str], int], limit: float) -> str:
    """把文字截到 ``limit`` 像素以内，放不下时末尾补省略号。"""
    if limit <= 0:
        return ""
    if measure(text) <= limit:
        return text
    clipped = text
    while clipped and measure(clipped + "…") > limit:
        clipped = clipped[:-1]
    return clipped + "…" if clipped else ""


def _lighten(color: str, ratio: float = 0.18) -> str:
    """把颜色往白色方向提亮，用来高亮悬停的柱子。"""
    try:
        return blend_hex(color, "#ffffff", ratio)
    except ValueError:
        return color


def _rgba(color: str, alpha: int) -> Tuple[int, int, int, int]:
    """``#rrggbb`` 转带透明度的 RGBA；认不出来就用半透明灰。"""
    text = color.lstrip("#")
    if len(text) != 6:
        return (128, 128, 128, alpha)
    try:
        return (
            int(text[0:2], 16),
            int(text[2:4], 16),
            int(text[4:6], 16),
            alpha,
        )
    except ValueError:
        return (128, 128, 128, alpha)


def _catmull_rom(
    points: Sequence[Tuple[float, float]], samples: int = 12
) -> List[Tuple[float, float]]:
    """Catmull-Rom 插值：把折点变成平滑曲线，返回加密后的点列。"""
    if len(points) < 3:
        return list(points)
    padded = [points[0], *points, points[-1]]
    result: List[Tuple[float, float]] = []
    for index in range(1, len(padded) - 2):
        p0, p1, p2, p3 = (
            padded[index - 1],
            padded[index],
            padded[index + 1],
            padded[index + 2],
        )
        for step in range(samples):
            t = step / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * (
                2 * p1[0]
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                2 * p1[1]
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            result.append((x, y))
    result.append(points[-1])
    return result


#: 多系列默认配色：取令牌名而不是色值，换主题时会重新解析。
_SERIES_TOKENS: Tuple[str, ...] = (
    "COLOR_KNOB",
    "COLOR_WARNING",
    "COLOR_SUCCESS",
    "COLOR_ERROR",
    "COLOR_ACCENT",
)


class BarChart(Chainable, ctk.CTkFrame):
    """柱状图：横向一排柱子，纵轴自动取整齐刻度。

    参数:
        master: 父容器。
        values: 柱子的值，按类别顺序排列；负数会画在 0 线下方。
        categories: 每根柱子下面的文字；不传就用 ``"1"`` / ``"2"`` …。
        colors: 柱体颜色。可以是单个颜色（全部同色），也可以是颜色序列
            （按柱子循环取用）；不传用 :data:`tokens.COLOR_KNOB`。
        width / height: 控件初始尺寸（逻辑像素），默认 420 × 240；
            ``pack(fill="both", expand=True)`` 后会跟着父容器拉伸。
        bar_ratio: 柱宽占「每格宽度」的比例，默认 0.62。
        radius: 柱体顶部圆角（逻辑像素），默认 4；传 0 就是直角。
        show_values: 是否在柱顶标数值，默认 ``True``。
        show_grid: 是否画横向网格线，默认 ``True``。
        show_tooltip: 鼠标移到柱子上时是否高亮并弹出类别 + 数值，默认 ``True``。
        y_ticks: 纵轴期望的刻度段数，默认 5。
        y_range: ``(最小, 最大)`` 固定纵轴范围；不传按数据自动取。
        formatter: 数值文字格式。可以传回调 ``lambda v: f"{v} 次"``，
            也可以传格式串 ``"{:.0f}%"``。
        empty_text: 没有数据时居中显示的提示。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        get(): 当前数据（浮点数列表）。
        set(values, categories=None): 换数据，只重画不重建控件。
        set_categories(categories): 只换类别文字。
        set_colors(colors): 换柱体颜色；传 ``None`` 恢复默认。
        set_y_range(low, high): 固定纵轴范围；传 ``None`` 恢复自动。
        apply_theme(): 按当前令牌重画（换配色 / 换主题时自动调用）。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        values: Sequence[float] = (),
        categories: Optional[Sequence[Any]] = None,
        colors: Optional[ColorArg] = None,
        width: int = 420,
        height: int = 240,
        bar_ratio: float = 0.62,
        radius: int = 4,
        show_values: bool = True,
        show_grid: bool = True,
        show_tooltip: bool = True,
        y_ticks: int = 5,
        y_range: Optional[Tuple[float, float]] = None,
        formatter: Optional[Formatter] = None,
        empty_text: str = "暂无数据",
        **kwargs: Any,
    ) -> None:
        """建柱状图；数据可以在构造时给，也可以用 :meth:`set` 后补。"""
        super().__init__(master, fg_color="transparent", **kwargs)
        self._values: List[float] = [_to_float(value) for value in values]
        self._categories: List[str] = [str(item) for item in (categories or ())]
        self._colors = colors
        self._bar_ratio = max(0.05, min(1.0, float(bar_ratio)))
        self._radius = max(0, int(radius))
        self._show_values = bool(show_values)
        self._show_grid = bool(show_grid)
        self._show_tooltip = bool(show_tooltip)
        self._y_ticks = max(2, int(y_ticks))
        self._y_range = _normalize_range(y_range)
        self._formatter = formatter
        self._empty_text = str(empty_text)

        self._photo = None
        self._tip_photo = None
        self._redraw_job: Optional[str] = None
        #: 当前悬停的柱子序号；``None`` 表示鼠标不在图上
        self._hover_index: Optional[int] = None
        #: 最近一次绘制的布局：(左, 上, 右, 下, 柱数, 每格宽)
        self._layout: Optional[Tuple[float, float, float, float, int, float]] = None
        #: 最近一次绘制的柱体矩形：(左, 上, 右, 下, 是否向上)
        self._bars: List[Tuple[float, float, float, float, bool]] = []

        self._canvas = tk.Canvas(
            self,
            width=self._px(width),
            height=self._px(height),
            bg=_canvas_bg(self),
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", self._schedule_redraw)
        self._canvas.bind("<Motion>", self._on_motion)
        self._canvas.bind("<Leave>", self._on_leave)
        # 构造时还没布局，宽高都是 1，等 idle 再画第一帧
        self.after_idle(self._redraw)

    # ------------------------------------------------------------ 读写
    def get(self) -> List[float]:
        """当前数据（浮点数列表）。"""
        return list(self._values)

    def set(
        self,
        values: Sequence[float],
        categories: Optional[Sequence[Any]] = None,
    ) -> None:
        """换数据；``categories`` 不传时沿用旧的（长度不匹配就重置成序号）。"""
        self._values = [_to_float(value) for value in values]
        if categories is not None:
            self._categories = [str(item) for item in categories]
        if len(self._categories) != len(self._values):
            self._categories = [str(index + 1) for index in range(len(self._values))]
        self._schedule_redraw()

    def set_categories(self, categories: Sequence[Any]) -> None:
        """换每根柱子下面的文字；长度可以和数据不一致，缺的补序号。"""
        self._categories = [str(item) for item in categories]
        self._schedule_redraw()

    def set_colors(self, colors: Optional[ColorArg]) -> None:
        """换柱体颜色；单个颜色全部同色，序列则按柱子循环取用。"""
        self._colors = colors
        self._schedule_redraw()

    def set_y_range(self, low: Optional[float], high: Optional[float] = None) -> None:
        """固定纵轴范围；传 ``None`` 恢复按数据自动取刻度。"""
        if low is None:
            self._y_range = None
        else:
            self._y_range = _normalize_range((low, high))
        self._schedule_redraw()

    # ------------------------------------------------------------ 主题
    def apply_theme(self) -> None:
        """按当前令牌重画整张图（``theming`` 运行时换色后调用）。"""
        if not self._canvas.winfo_exists():
            return
        try:
            self._canvas.configure(bg=_canvas_bg(self))
        except tk.TclError:
            return
        self._redraw()

    # ------------------------------------------------------------ 绘制
    def _px(self, value: float) -> int:
        """逻辑像素转物理像素（canvas 不参与 CTk 的缩放）。"""
        return max(1, int(round(self._apply_widget_scaling(value))))

    def _font(self, spec: T.FontSpec) -> tuple:
        """canvas 文字字体：按 widget scaling 换算成实际字号。"""
        return get_font(spec).create_scaled_tuple(self._apply_widget_scaling(1.0))

    def _schedule_redraw(self, _event: Any = None) -> None:
        """把连续尺寸变化合并成一次重绘。"""
        if self._redraw_job is None:
            self._redraw_job = self.after_idle(self._flush_redraw)

    def _flush_redraw(self) -> None:
        """idle 里真正执行重绘。"""
        self._redraw_job = None
        try:
            exists = self.winfo_exists()
        except tk.TclError:  # 窗口已经销毁，排队的任务直接作废
            return
        if exists:
            self._redraw()

    def destroy(self) -> None:
        """销毁前取消排队中的重绘。"""
        if self._redraw_job is not None:
            try:
                self.after_cancel(self._redraw_job)
            except tk.TclError:
                pass
            self._redraw_job = None
        super().destroy()

    def _bar_colors(self, count: int) -> List[str]:
        """按柱子数量取颜色：单色铺满，序列循环，未指定用默认令牌色。"""
        default = color_of(T.COLOR_KNOB)
        if self._colors is None:
            return [default] * count
        if isinstance(self._colors, str):
            return [color_of(self._colors)] * count
        palette = [color_of(color) for color in self._colors]
        if not palette:
            return [default] * count
        return [palette[index % len(palette)] for index in range(count)]

    def _format_value(self, value: float) -> str:
        """按 ``formatter`` 生成数值文字，出错时退回默认格式。"""
        formatter = self._formatter
        if callable(formatter):
            try:
                return str(formatter(value))
            except Exception:  # noqa: BLE001 - 回调是用户代码
                return _default_format(value)
        if isinstance(formatter, str):
            try:
                return formatter.format(value)
            except (IndexError, KeyError, ValueError):
                return _default_format(value)
        return _default_format(value)

    def _axis(self) -> Tuple[float, float, List[float]]:
        """算出纵轴范围与刻度。"""
        values = self._values or [0.0]
        low = min(0.0, min(values))
        high = max(0.0, max(values))
        if self._y_range is not None:
            low, high = self._y_range
        ticks = _nice_ticks(low, high, self._y_ticks)
        return ticks[0], ticks[-1], ticks

    def _redraw(self) -> None:
        """画网格、柱体、数值和类别文字。"""
        if self._redraw_job is not None:
            try:
                self.after_cancel(self._redraw_job)
            except tk.TclError:
                pass
            self._redraw_job = None

        canvas = self._canvas
        if not canvas.winfo_exists():
            return
        canvas.delete("all")
        self._layout = None
        self._bars = []
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        tick_font = self._font(T.FONT_TINY)
        label_font = self._font(T.FONT_SMALL)
        value_font = self._font(T.FONT_TINY)
        measure_tick = tkfont.Font(font=tick_font)

        if not self._values:
            self._hover_index = None
            canvas.create_text(
                width / 2,
                height / 2,
                text=self._empty_text,
                anchor="center",
                font=label_font,
                fill=color_of(T.COLOR_FAINT),
            )
            return

        low, high, ticks = self._axis()
        tick_labels = [self._format_value(tick) for tick in ticks]
        axis_width = max(measure_tick.measure(text) for text in tick_labels)
        left = axis_width + self._px(10)
        top = self._px(22) if self._show_values else self._px(10)
        right = self._px(6)
        bottom = self._px(26)
        plot_left = float(left)
        plot_top = float(top)
        plot_right = float(width - right)
        plot_bottom = float(height - bottom)
        if plot_right - plot_left < 8 or plot_bottom - plot_top < 8:
            return

        span = high - low if high != low else 1.0

        def y_of(value: float) -> float:
            """数值 → 画布 y 坐标。"""
            return plot_bottom - (value - low) / span * (plot_bottom - plot_top)

        # ---- 网格与纵轴刻度 ----
        for tick, text in zip(ticks, tick_labels):
            y = y_of(tick)
            is_zero = abs(tick) < 1e-9
            # 关掉网格时仍保留 0 线，正负柱子才有共同基准
            if self._show_grid or is_zero:
                canvas.create_line(
                    plot_left,
                    y,
                    plot_right,
                    y,
                    fill=color_of(T.COLOR_BORDER_STRONG if is_zero else T.COLOR_BORDER),
                )
            canvas.create_text(
                plot_left - self._px(8),
                y,
                text=text,
                anchor="e",
                font=tick_font,
                fill=color_of(T.COLOR_FAINT),
            )

        # ---- 柱体 ----
        count = len(self._values)
        slot = (plot_right - plot_left) / count
        bar_width = max(1.0, slot * self._bar_ratio)
        base_y = min(plot_bottom, max(plot_top, y_of(0.0)))
        bars: List[Tuple[float, float, float, float, bool]] = []
        for index, value in enumerate(self._values):
            center = plot_left + slot * (index + 0.5)
            value_y = y_of(value)
            top_y = min(value_y, base_y)
            bottom_y = max(value_y, base_y)
            if bottom_y - top_y < 1.0:
                # 0 值也留一条 1px 的底线，柱子不会凭空消失
                bottom_y = top_y + 1.0
            bars.append(
                (
                    center - bar_width / 2,
                    top_y,
                    center + bar_width / 2,
                    bottom_y,
                    value >= 0,
                )
            )

        colors = self._bar_colors(count)
        self._bars = bars
        self._layout = (plot_left, plot_top, plot_right, plot_bottom, count, slot)
        if self._hover_index is not None and self._hover_index >= count:
            self._hover_index = None
        if self._show_tooltip and self._hover_index is not None:
            colors[self._hover_index] = _lighten(colors[self._hover_index])
        radius = min(float(self._px(self._radius)), bar_width / 2)
        if _HAS_PIL:
            self._draw_bars_pil(canvas, bars, colors, radius, width, height)
        else:
            for (x0, y0, x1, y1, _up), color in zip(bars, colors):
                canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

        # ---- 柱顶数值 ----
        if self._show_values and slot >= self._px(22):
            for (x0, y0, x1, y1, up), value in zip(bars, self._values):
                if y1 - y0 < self._px(14):
                    continue
                center = (x0 + x1) / 2
                if up:
                    canvas.create_text(
                        center,
                        y0 - self._px(3),
                        text=self._format_value(value),
                        anchor="s",
                        font=value_font,
                        fill=color_of(T.COLOR_TEXT_SOFT),
                    )
                else:
                    canvas.create_text(
                        center,
                        y1 + self._px(3),
                        text=self._format_value(value),
                        anchor="n",
                        font=value_font,
                        fill=color_of(T.COLOR_TEXT_SOFT),
                    )

        # ---- 类别文字 ----
        if slot >= self._px(24):
            measure_label = tkfont.Font(font=label_font)
            for index in range(count):
                text = (
                    self._categories[index]
                    if index < len(self._categories)
                    else str(index + 1)
                )
                center = plot_left + slot * (index + 0.5)
                canvas.create_text(
                    center,
                    plot_bottom + self._px(6),
                    text=_fit_text(text, measure_label.measure, slot - self._px(6)),
                    anchor="n",
                    font=label_font,
                    fill=color_of(T.COLOR_MUTED),
                )

        # ---- 悬停气泡 ----
        if self._show_tooltip and self._hover_index is not None:
            self._draw_tooltip(canvas, width, height)

    def _draw_tooltip(self, canvas: tk.Canvas, width: int, height: int) -> None:
        """在悬停柱子的上方画一个圆角气泡：类别 + 数值。"""
        index = self._hover_index
        if index is None or index >= len(self._bars):
            return
        x0, y0, x1, y1, _up = self._bars[index]
        category = (
            self._categories[index] if index < len(self._categories) else str(index + 1)
        )
        text = f"{category}  {self._format_value(self._values[index])}"
        font = self._font(T.FONT_SMALL)
        measure = tkfont.Font(font=font)
        pad_x = self._px(8)
        pad_y = self._px(5)
        bubble_w = float(measure.measure(text) + pad_x * 2)
        bubble_h = float(measure.metrics("linespace") + pad_y * 2)

        # x 跟着柱子居中，但不出画布；y 优先放在柱顶上方，上面放不下就放柱底下方
        left, top, right, _bottom, _count, _slot = self._layout or (0, 0, width, height, 1, 1)
        center = (x0 + x1) / 2
        bubble_x = min(max(center - bubble_w / 2, left), max(left, right - bubble_w))
        bubble_y = y0 - bubble_h - self._px(6)
        if bubble_y < 0:
            bubble_y = y1 + self._px(6)
        if bubble_y + bubble_h > height:
            bubble_y = max(0.0, height - bubble_h)
        radius = float(self._px(T.RADIUS_SMALL))
        fill = color_of(T.COLOR_INPUT)
        outline = color_of(T.COLOR_BORDER_STRONG)

        if _HAS_PIL:
            scale = _SUPERSAMPLE
            layer = Image.new(
                "RGBA", (int(bubble_w * scale), int(bubble_h * scale)), (0, 0, 0, 0)
            )
            pen = ImageDraw.Draw(layer)
            pen.rounded_rectangle(
                (1, 1, bubble_w * scale - 1, bubble_h * scale - 1),
                radius=radius * scale,
                fill=fill,
                outline=outline,
                width=max(1, scale),
            )
            self._tip_photo = ImageTk.PhotoImage(
                layer.resize((int(bubble_w), int(bubble_h)), Image.LANCZOS)
            )
            canvas.create_image(bubble_x, bubble_y, anchor="nw", image=self._tip_photo)
        else:
            canvas.create_rectangle(
                bubble_x,
                bubble_y,
                bubble_x + bubble_w,
                bubble_y + bubble_h,
                fill=fill,
                outline=outline,
            )
        canvas.create_text(
            bubble_x + bubble_w / 2,
            bubble_y + bubble_h / 2,
            text=text,
            anchor="center",
            font=font,
            fill=color_of(T.COLOR_TEXT),
        )

    # ------------------------------------------------------------ 鼠标
    def _on_motion(self, event: tk.Event) -> None:
        """鼠标移动：算出落在哪根柱子上，序号变了才重画。"""
        if not self._show_tooltip or self._layout is None:
            return
        left, top, right, bottom, count, slot = self._layout
        if not (left <= event.x <= right and top <= event.y <= bottom + self._px(20)):
            self._set_hover(None)
            return
        index = int((event.x - left) / max(1.0, slot))
        self._set_hover(min(count - 1, max(0, index)))

    def _on_leave(self, _event: tk.Event) -> None:
        """指针离开图表时收起气泡。"""
        self._set_hover(None)

    def _set_hover(self, index: Optional[int]) -> None:
        """更新悬停序号；没变化就不重画。"""
        if index == self._hover_index:
            return
        self._hover_index = index
        self._redraw()

    def _draw_bars_pil(
        self,
        canvas: tk.Canvas,
        bars: Sequence[Tuple[float, float, float, float, bool]],
        colors: Sequence[str],
        radius: float,
        width: int,
        height: int,
    ) -> None:
        """用 Pillow 画圆角柱体，3 倍超采样后缩回，边缘没有锯齿。

        圆角只留在远离 0 线的一头：贴基线的那头补一块矩形盖掉圆角，
        柱子看起来像「从地上长出来」。
        """
        scale = _SUPERSAMPLE
        layer = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
        pen = ImageDraw.Draw(layer)
        for (x0, y0, x1, y1, up), color in zip(bars, colors):
            corner = min(radius, (x1 - x0) / 2, (y1 - y0) / 2)
            box = (x0 * scale, y0 * scale, x1 * scale, y1 * scale)
            if corner >= 1:
                pen.rounded_rectangle(box, radius=corner * scale, fill=color)
                if up:
                    pen.rectangle(
                        (x0 * scale, y1 * scale - corner * scale, x1 * scale, y1 * scale),
                        fill=color,
                    )
                else:
                    pen.rectangle(
                        (x0 * scale, y0 * scale, x1 * scale, y0 * scale + corner * scale),
                        fill=color,
                    )
            else:
                pen.rectangle(box, fill=color)

        self._photo = ImageTk.PhotoImage(
            layer.resize((width, height), Image.LANCZOS)
        )
        canvas.create_image(0, 0, anchor="nw", image=self._photo)


class LineChart(Chainable, ctk.CTkFrame):
    """折线图：多条折线共用一个横轴，悬停时竖线对齐并显示各系列数值。

    纵轴按数据自动取范围（不像柱状图从 0 起），也可以 ``y_range`` 固定。
    线条、面积和圆点都用 Pillow 3 倍超采样绘制，边缘没有锯齿。

    用法::

        from ctk_kit import LineChart

        chart = LineChart(card, categories=["周一", "周二", "周三"])
        chart.add_series("访问量", [120, 180, 210], smooth=True, area=True)
        chart.add_series("转化", [30, 45, 52])
        chart.pack(fill="both", expand=True)

    参数:
        master: 父容器。
        values: 单系列数据；给 ``series`` 时以 ``series`` 为准。
        name: ``values`` 这条线的名称（图例和提示气泡里显示）。
        series: 多系列数据，``{"名称": [值…]}`` 或 ``[(名称, [值…]), …]``。
        categories: 横轴文字；不传就用 ``"1"`` / ``"2"`` …。
        colors: 系列颜色。单个颜色所有线同色，序列按系列顺序取用；
            不传用内置的一组令牌色。
        width / height: 控件初始尺寸（逻辑像素），默认 420 × 240。
        smooth: 是否把折线画成平滑曲线，默认 ``False``。
        area: 是否在线下方填充半透明面积，默认 ``False``。
        markers: 是否在每个数据点画圆点，默认 ``True``。
        show_grid: 是否画横向网格线，默认 ``True``。
        show_tooltip: 悬停时是否显示竖线和数值气泡，默认 ``True``。
        legend: 是否在右上角显示图例，默认 ``True``。
        y_ticks: 纵轴期望的刻度段数，默认 5。
        y_range: ``(最小, 最大)`` 固定纵轴范围；不传按数据自动取。
        formatter: 数值文字格式，可以是回调或 ``"{:.0f} ms"`` 这样的格式串。
        empty_text: 没有数据时居中显示的提示。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        get(): ``{系列名: [值…]}``。
        set(values, categories=None): 换成单系列（旧系列会被替换）。
        add_series(name, values, …): 增加或覆盖一条线。
        set_series(name, values): 同 :meth:`add_series`。
        set_categories(categories): 只换横轴文字。
        set_colors(colors): 换系列颜色；传 ``None`` 恢复默认。
        set_y_range(low, high): 固定纵轴范围；传 ``None`` 恢复自动。
        apply_theme(): 按当前令牌重画（换配色 / 换主题时自动调用）。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        values: Sequence[float] = (),
        name: str = "数值",
        series: Optional[Sequence[Tuple[str, Sequence[float]]]] = None,
        categories: Optional[Sequence[Any]] = None,
        colors: Optional[ColorArg] = None,
        width: int = 420,
        height: int = 240,
        smooth: bool = False,
        area: bool = False,
        markers: bool = True,
        show_grid: bool = True,
        show_tooltip: bool = True,
        legend: bool = True,
        y_ticks: int = 5,
        y_range: Optional[Tuple[float, float]] = None,
        formatter: Optional[Formatter] = None,
        empty_text: str = "暂无数据",
        **kwargs: Any,
    ) -> None:
        """建折线图；数据可以构造时给，也可以之后用 :meth:`add_series` 补。"""
        super().__init__(master, fg_color="transparent", **kwargs)
        self._series: Dict[str, List[float]] = {}
        self._series_colors: Dict[str, Optional[str]] = {}
        #: 单条线的样式覆盖：{名称: {"smooth": …, "area": …, "markers": …}}
        self._styles: Dict[str, Dict[str, bool]] = {}
        self._categories: List[str] = [str(item) for item in (categories or ())]
        self._colors = colors
        self._smooth = bool(smooth)
        self._area = bool(area)
        self._markers = bool(markers)
        self._show_grid = bool(show_grid)
        self._show_tooltip = bool(show_tooltip)
        self._legend = bool(legend)
        self._y_ticks = max(2, int(y_ticks))
        self._y_range = _normalize_range(y_range)
        self._formatter = formatter
        self._empty_text = str(empty_text)

        self._photo = None
        self._tip_photo = None
        self._redraw_job: Optional[str] = None
        self._hover_index: Optional[int] = None
        self._layout: Optional[Tuple[float, float, float, float, int, float]] = None

        self._canvas = tk.Canvas(
            self,
            width=self._px(width),
            height=self._px(height),
            bg=_canvas_bg(self),
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", self._schedule_redraw)
        self._canvas.bind("<Motion>", self._on_motion)
        self._canvas.bind("<Leave>", self._on_leave)

        if series is not None:
            items = series.items() if hasattr(series, "items") else series
            for item_name, item_values in items:
                self.add_series(item_name, item_values)
        elif values:
            self.add_series(name, values)
        else:
            self.after_idle(self._redraw)

    # ------------------------------------------------------------ 读写
    def get(self) -> Dict[str, List[float]]:
        """当前数据：``{系列名: [值…]}``。"""
        return {name: list(values) for name, values in self._series.items()}

    def set(
        self,
        values: Sequence[float],
        categories: Optional[Sequence[Any]] = None,
    ) -> None:
        """换成单系列数据；已有的多条线会被一条线替换。"""
        only = next(iter(self._series), "数值") if len(self._series) == 1 else "数值"
        self._series = {only: [_to_float(value) for value in values]}
        self._series_colors = {only: self._series_colors.get(only)}
        if only not in self._styles:
            self._styles[only] = {}
        if categories is not None:
            self._categories = [str(item) for item in categories]
        if len(self._categories) != len(self._series[only]):
            self._categories = [str(index + 1) for index in range(len(self._series[only]))]
        self._schedule_redraw()

    def add_series(
        self,
        name: str,
        values: Sequence[float],
        *,
        color: Optional[str] = None,
        smooth: Optional[bool] = None,
        area: Optional[bool] = None,
        markers: Optional[bool] = None,
    ) -> None:
        """增加一条线；同名会覆盖原来的数据，未传的样式沿用全局设置。"""
        key = str(name)
        self._series[key] = [_to_float(value) for value in values]
        self._series_colors[key] = color
        style = self._styles.setdefault(key, {})
        for option, flag in (("smooth", smooth), ("area", area), ("markers", markers)):
            if flag is not None:
                style[option] = bool(flag)
        self._schedule_redraw()

    def set_series(self, name: str, values: Sequence[float]) -> None:
        """覆盖一条线的数据；不存在就新增。"""
        self.add_series(name, values)

    def set_categories(self, categories: Sequence[Any]) -> None:
        """换横轴文字；长度可以和数据不一致，缺的补序号。"""
        self._categories = [str(item) for item in categories]
        self._schedule_redraw()

    def set_colors(self, colors: Optional[ColorArg]) -> None:
        """换系列颜色；单个颜色所有线同色，序列按系列循环取用。"""
        self._colors = colors
        self._schedule_redraw()

    def set_y_range(self, low: Optional[float], high: Optional[float] = None) -> None:
        """固定纵轴范围；传 ``None`` 恢复按数据自动取刻度。"""
        if low is None:
            self._y_range = None
        else:
            self._y_range = _normalize_range((low, high))
        self._schedule_redraw()

    # ------------------------------------------------------------ 主题
    def apply_theme(self) -> None:
        """按当前令牌重画整张图（``theming`` 运行时换色后调用）。"""
        if not self._canvas.winfo_exists():
            return
        try:
            self._canvas.configure(bg=_canvas_bg(self))
        except tk.TclError:
            return
        self._redraw()

    # ------------------------------------------------------------ 绘制基础
    def _px(self, value: float) -> int:
        """逻辑像素转物理像素（canvas 不参与 CTk 的缩放）。"""
        return max(1, int(round(self._apply_widget_scaling(value))))

    def _font(self, spec: T.FontSpec) -> tuple:
        """canvas 文字字体：按 widget scaling 换算成实际字号。"""
        return get_font(spec).create_scaled_tuple(self._apply_widget_scaling(1.0))

    def _schedule_redraw(self, _event: Any = None) -> None:
        """把连续尺寸变化合并成一次重绘。"""
        if self._redraw_job is None:
            self._redraw_job = self.after_idle(self._flush_redraw)

    def _flush_redraw(self) -> None:
        """idle 里真正执行重绘。"""
        self._redraw_job = None
        try:
            exists = self.winfo_exists()
        except tk.TclError:  # 窗口已经销毁，排队的任务直接作废
            return
        if exists:
            self._redraw()

    def destroy(self) -> None:
        """销毁前取消排队中的重绘。"""
        if self._redraw_job is not None:
            try:
                self.after_cancel(self._redraw_job)
            except tk.TclError:
                pass
            self._redraw_job = None
        super().destroy()

    def _series_color(self, index: int, name: str) -> str:
        """取第 ``index`` 条线的颜色：显式指定 > 构造参数 > 默认令牌色。"""
        explicit = self._series_colors.get(name)
        source = explicit if explicit is not None else self._colors
        default = color_of(getattr(T, _SERIES_TOKENS[index % len(_SERIES_TOKENS)]))
        if source is None:
            return default
        if isinstance(source, str):
            return color_of(source)
        palette = list(source)
        return color_of(palette[index % len(palette)]) if palette else default

    def _format_value(self, value: float) -> str:
        """按 ``formatter`` 生成数值文字，出错时退回默认格式。"""
        formatter = self._formatter
        if callable(formatter):
            try:
                return str(formatter(value))
            except Exception:  # noqa: BLE001 - 回调是用户代码
                return _default_format(value)
        if isinstance(formatter, str):
            try:
                return formatter.format(value)
            except (IndexError, KeyError, ValueError):
                return _default_format(value)
        return _default_format(value)

    def _axis(self) -> Tuple[float, float, List[float]]:
        """算出纵轴范围与刻度（按数据最小 / 最大，不强制包含 0）。"""
        values = [value for items in self._series.values() for value in items] or [0.0]
        low, high = min(values), max(values)
        if self._y_range is not None:
            low, high = self._y_range
        ticks = _nice_ticks(low, high, self._y_ticks)
        return ticks[0], ticks[-1], ticks

    def _category_count(self) -> int:
        """横轴点数：取类别文字与各系列长度的最大值。"""
        if not self._series:
            return 0
        return max([len(self._categories)] + [len(item) for item in self._series.values()])

    # ------------------------------------------------------------ 绘制
    def _redraw(self) -> None:
        """画网格、面积、折线、圆点、图例和悬停气泡。"""
        if self._redraw_job is not None:
            try:
                self.after_cancel(self._redraw_job)
            except tk.TclError:
                pass
            self._redraw_job = None

        canvas = self._canvas
        if not canvas.winfo_exists():
            return
        canvas.delete("all")
        self._layout = None
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        tick_font = self._font(T.FONT_TINY)
        label_font = self._font(T.FONT_SMALL)
        measure_tick = tkfont.Font(font=tick_font)

        if not self._series:
            self._hover_index = None
            canvas.create_text(
                width / 2,
                height / 2,
                text=self._empty_text,
                anchor="center",
                font=label_font,
                fill=color_of(T.COLOR_FAINT),
            )
            return

        low, high, ticks = self._axis()
        tick_labels = [self._format_value(tick) for tick in ticks]
        axis_width = max(measure_tick.measure(text) for text in tick_labels)
        left = axis_width + self._px(10)
        top = self._px(28) if self._legend else self._px(12)
        right = self._px(8)
        bottom = self._px(26)
        plot_left = float(left)
        plot_top = float(top)
        plot_right = float(width - right)
        plot_bottom = float(height - bottom)
        if plot_right - plot_left < 8 or plot_bottom - plot_top < 8:
            return

        count = self._category_count()
        if count <= 0:
            return
        span = high - low if high != low else 1.0

        def y_of(value: float) -> float:
            """数值 → 画布 y 坐标。"""
            return plot_bottom - (value - low) / span * (plot_bottom - plot_top)

        # ---- 网格与纵轴刻度 ----
        for tick, text in zip(ticks, tick_labels):
            y = y_of(tick)
            is_zero = abs(tick) < 1e-9
            if self._show_grid or is_zero:
                canvas.create_line(
                    plot_left,
                    y,
                    plot_right,
                    y,
                    fill=color_of(T.COLOR_BORDER_STRONG if is_zero else T.COLOR_BORDER),
                )
            canvas.create_text(
                plot_left - self._px(8),
                y,
                text=text,
                anchor="e",
                font=tick_font,
                fill=color_of(T.COLOR_FAINT),
            )

        # ---- 横轴坐标 ----
        step = (plot_right - plot_left) / (count - 1) if count > 1 else 0.0

        def x_of(index: int) -> float:
            """第几根 → 画布 x 坐标；只有一个点时居中。"""
            if count <= 1:
                return (plot_left + plot_right) / 2
            return plot_left + step * index

        series_items = list(self._series.items())
        colors = [
            self._series_color(index, item_name)
            for index, (item_name, _values) in enumerate(series_items)
        ]
        drawn: List[Tuple[List[Tuple[float, float]], str, bool, bool, bool]] = []
        for (item_name, item_values), color in zip(series_items, colors):
            style = self._styles.get(item_name, {})
            points = [
                (x_of(index), y_of(value))
                for index, value in enumerate(item_values)
                if index < count
            ]
            if points:
                drawn.append(
                    (
                        points,
                        color,
                        style.get("smooth", self._smooth),
                        style.get("area", self._area),
                        style.get("markers", self._markers),
                    )
                )

        self._layout = (plot_left, plot_top, plot_right, plot_bottom, count, step)
        if self._hover_index is not None and self._hover_index >= count:
            self._hover_index = None

        if _HAS_PIL:
            self._draw_paths_pil(canvas, drawn, width, height, plot_bottom)
        else:
            self._draw_paths_plain(canvas, drawn, plot_bottom)

        # ---- 悬停竖线 ----
        if self._show_tooltip and self._hover_index is not None:
            guide_x = x_of(self._hover_index)
            canvas.create_line(
                guide_x,
                plot_top,
                guide_x,
                plot_bottom,
                fill=color_of(T.COLOR_BORDER_STRONG),
                dash=(3, 3),
            )

        # ---- 横轴文字 ----
        if step >= self._px(18) or count == 1:
            span_px = step if count > 1 else (plot_right - plot_left)
            max_labels = max(1, int((plot_right - plot_left) / self._px(56)))
            label_step = max(1, int(math.ceil(count / max_labels)))
            measure_label = tkfont.Font(font=label_font)
            for index in range(0, count, label_step):
                text = (
                    self._categories[index]
                    if index < len(self._categories)
                    else str(index + 1)
                )
                text = _fit_text(
                    text, measure_label.measure, span_px * label_step - self._px(6)
                )
                # 首尾文字往内收，避免半个字被画布边缘切掉
                label_x = x_of(index)
                half = measure_label.measure(text) / 2
                label_x = min(
                    max(label_x, half + self._px(2)), width - half - self._px(2)
                )
                canvas.create_text(
                    label_x,
                    plot_bottom + self._px(6),
                    text=text,
                    anchor="n",
                    font=label_font,
                    fill=color_of(T.COLOR_MUTED),
                )

        # ---- 图例 ----
        if self._legend:
            self._draw_legend(canvas, plot_right, top, series_items, colors)

        # ---- 悬停气泡 ----
        if self._show_tooltip and self._hover_index is not None:
            self._draw_tooltip(canvas, self._hover_index, x_of(self._hover_index), height)

    def _draw_paths_pil(
        self,
        canvas: tk.Canvas,
        drawn: Sequence[Tuple[List[Tuple[float, float]], str, bool, bool, bool]],
        width: int,
        height: int,
        plot_bottom: float,
    ) -> None:
        """用 Pillow 画面积、折线和圆点，3 倍超采样后缩回。"""
        scale = _SUPERSAMPLE
        line_width = max(2, int(round(self._px(2) * scale)))
        layer = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
        pen = ImageDraw.Draw(layer)

        # 面积先画，避免盖住别的线
        for points, color, smooth, area, _markers in drawn:
            path = _catmull_rom(points) if smooth else list(points)
            if area and len(path) >= 2:
                polygon = [(x * scale, y * scale) for x, y in path]
                polygon.append((path[-1][0] * scale, plot_bottom * scale))
                polygon.append((path[0][0] * scale, plot_bottom * scale))
                pen.polygon(polygon, fill=_rgba(color, 46))

        for points, color, smooth, _area, markers in drawn:
            path = _catmull_rom(points) if smooth else list(points)
            if len(path) >= 2:
                pen.line(
                    [(x * scale, y * scale) for x, y in path],
                    fill=color,
                    width=line_width,
                    joint="curve",
                )
            if markers:
                radius = max(2, int(round(self._px(3) * scale)))
                for index, (x, y) in enumerate(points):
                    hovered = self._hover_index is not None and index == self._hover_index
                    dot = radius * 1.7 if hovered else radius
                    box = (x * scale - dot, y * scale - dot, x * scale + dot, y * scale + dot)
                    if hovered:
                        pen.ellipse(
                            box, fill=color, outline=(255, 255, 255, 230), width=max(1, scale)
                        )
                    else:
                        pen.ellipse(box, fill=color)

        self._photo = ImageTk.PhotoImage(layer.resize((width, height), Image.LANCZOS))
        canvas.create_image(0, 0, anchor="nw", image=self._photo)

    def _draw_paths_plain(
        self,
        canvas: tk.Canvas,
        drawn: Sequence[Tuple[List[Tuple[float, float]], str, bool, bool, bool]],
        plot_bottom: float,
    ) -> None:
        """没装 Pillow 时的退路：canvas 直画折线、面积和圆点。"""
        for points, color, smooth, area, markers in drawn:
            path = _catmull_rom(points) if smooth else list(points)
            if area and len(path) >= 2:
                polygon = [coord for point in path for coord in point]
                polygon += [path[-1][0], plot_bottom, path[0][0], plot_bottom]
                canvas.create_polygon(polygon, fill=color, outline="", stipple="gray25")
            if len(path) >= 2:
                canvas.create_line(
                    [coord for point in path for coord in point],
                    fill=color,
                    width=self._px(2),
                    smooth=smooth,
                )
            if markers:
                radius = self._px(3)
                for index, (x, y) in enumerate(points):
                    hovered = self._hover_index is not None and index == self._hover_index
                    r = radius * 2 if hovered else radius
                    canvas.create_oval(
                        x - r,
                        y - r,
                        x + r,
                        y + r,
                        fill=color,
                        outline=color_of(T.COLOR_TEXT) if hovered else color,
                    )

    def _draw_legend(
        self,
        canvas: tk.Canvas,
        right: float,
        top: float,
        series_items: Sequence[Tuple[str, Sequence[float]]],
        colors: Sequence[str],
    ) -> None:
        """在顶部右侧画「小圆点 + 系列名」图例，放不下就少画后面几条。"""
        font = self._font(T.FONT_TINY)
        measure = tkfont.Font(font=font)
        dot = self._px(8)
        gap = self._px(5)
        spacing = self._px(14)
        entries = [
            (dot + gap + measure.measure(item_name), item_name, color)
            for (item_name, _values), color in zip(series_items, colors)
        ]
        total = sum(width for width, _name, _color in entries) + spacing * max(
            0, len(entries) - 1
        )
        x = max(self._px(4), right - total)
        y = max(self._px(4), top / 2)
        self._legend_photos = []
        for width, item_name, color in entries:
            if x + width > right:
                break
            _legend_dot(canvas, x + dot / 2, y, dot, color, self)
            canvas.create_text(
                x + dot + gap,
                y,
                text=item_name,
                anchor="w",
                font=font,
                fill=color_of(T.COLOR_MUTED),
            )
            x += width + spacing

    def _draw_tooltip(
        self, canvas: tk.Canvas, index: int, hover_x: float, height: int
    ) -> None:
        """在悬停竖线的另一侧画气泡：类别 + 各系列数值。"""
        if self._layout is None:
            return
        left, top, right, _bottom, _count, _step = self._layout
        category = (
            self._categories[index] if index < len(self._categories) else str(index + 1)
        )
        lines = [category]
        for item_name, item_values in self._series.items():
            if index < len(item_values):
                lines.append(f"{item_name}  {self._format_value(item_values[index])}")
        if len(lines) == 1:
            return

        font = self._font(T.FONT_SMALL)
        measure = tkfont.Font(font=font)
        pad_x = self._px(9)
        pad_y = self._px(6)
        bubble_w = float(max(measure.measure(line) for line in lines) + pad_x * 2)
        bubble_h = float(measure.metrics("linespace") * len(lines) + pad_y * 2)
        # 气泡放在竖线的另一侧：前半段贴右边，后半段贴左边
        if hover_x <= (left + right) / 2:
            bubble_x = right - bubble_w - self._px(6)
        else:
            bubble_x = left + self._px(6)
        bubble_x = max(left, min(bubble_x, max(left, right - bubble_w)))
        bubble_y = top + self._px(6)
        if bubble_y + bubble_h > height:
            bubble_y = max(0.0, height - bubble_h)
        radius = float(self._px(T.RADIUS_SMALL))
        fill = color_of(T.COLOR_INPUT)
        outline = color_of(T.COLOR_BORDER_STRONG)

        if _HAS_PIL:
            scale = _SUPERSAMPLE
            layer = Image.new(
                "RGBA", (int(bubble_w * scale), int(bubble_h * scale)), (0, 0, 0, 0)
            )
            pen = ImageDraw.Draw(layer)
            pen.rounded_rectangle(
                (1, 1, bubble_w * scale - 1, bubble_h * scale - 1),
                radius=radius * scale,
                fill=fill,
                outline=outline,
                width=max(1, scale),
            )
            self._tip_photo = ImageTk.PhotoImage(
                layer.resize((int(bubble_w), int(bubble_h)), Image.LANCZOS)
            )
            canvas.create_image(bubble_x, bubble_y, anchor="nw", image=self._tip_photo)
        else:
            canvas.create_rectangle(
                bubble_x,
                bubble_y,
                bubble_x + bubble_w,
                bubble_y + bubble_h,
                fill=fill,
                outline=outline,
            )
        canvas.create_text(
            bubble_x + pad_x,
            bubble_y + pad_y,
            text="\n".join(lines),
            anchor="nw",
            justify="left",
            font=font,
            fill=color_of(T.COLOR_TEXT),
        )

    # ------------------------------------------------------------ 鼠标
    def _on_motion(self, event: tk.Event) -> None:
        """鼠标移动：按最近的横轴点更新悬停序号，变了才重画。"""
        if not self._show_tooltip or self._layout is None:
            return
        left, top, right, bottom, count, step = self._layout
        if not (left <= event.x <= right and top - self._px(4) <= event.y <= bottom + self._px(20)):
            self._set_hover(None)
            return
        if count <= 1 or step <= 0:
            index = 0
        else:
            index = int(round((event.x - left) / step))
        self._set_hover(min(count - 1, max(0, index)))

    def _on_leave(self, _event: tk.Event) -> None:
        """指针离开图表时收起竖线和气泡。"""
        self._set_hover(None)

    def _set_hover(self, index: Optional[int]) -> None:
        """更新悬停序号；没变化就不重画。"""
        if index == self._hover_index:
            return
        self._hover_index = index
        self._redraw()


class _ChartBase(Chainable, ctk.CTkFrame):
    """图表公共部分：画布、缩放、重绘调度和主题刷新。"""

    def __init__(
        self, master: tk.Misc, *, width: int, height: int, **kwargs: Any
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._photo = None
        self._tip_photo = None
        self._redraw_job: Optional[str] = None
        self._canvas = tk.Canvas(
            self,
            width=self._px(width),
            height=self._px(height),
            bg=_canvas_bg(self),
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", self._schedule_redraw)

    # ------------------------------------------------------------ 基础
    def _px(self, value: float) -> int:
        """逻辑像素转物理像素（canvas 不参与 CTk 的缩放）。"""
        return max(1, int(round(self._apply_widget_scaling(value))))

    def _font(self, spec: T.FontSpec) -> tuple:
        """canvas 文字字体：按 widget scaling 换算成实际字号。"""
        return get_font(spec).create_scaled_tuple(self._apply_widget_scaling(1.0))

    def _schedule_redraw(self, _event: Any = None) -> None:
        """把连续尺寸变化合并成一次重绘。"""
        if self._redraw_job is None:
            self._redraw_job = self.after_idle(self._flush_redraw)

    def _flush_redraw(self) -> None:
        """idle 里真正执行重绘。"""
        self._redraw_job = None
        try:
            exists = self.winfo_exists()
        except tk.TclError:  # 窗口已经销毁，排队的任务直接作废
            return
        if exists:
            self._redraw()

    def destroy(self) -> None:
        """销毁前取消排队中的重绘。"""
        if self._redraw_job is not None:
            try:
                self.after_cancel(self._redraw_job)
            except tk.TclError:
                pass
            self._redraw_job = None
        super().destroy()

    def apply_theme(self) -> None:
        """按当前令牌重画整张图（``theming`` 运行时换色后调用）。"""
        if not self._canvas.winfo_exists():
            return
        try:
            self._canvas.configure(bg=_canvas_bg(self))
        except tk.TclError:
            return
        self._redraw()

    def _format_value(self, value: float) -> str:
        """按 ``formatter`` 生成数值文字，出错时退回默认格式。"""
        formatter = getattr(self, "_formatter", None)
        if callable(formatter):
            try:
                return str(formatter(value))
            except Exception:  # noqa: BLE001 - 回调是用户代码
                return _default_format(value)
        if isinstance(formatter, str):
            try:
                return formatter.format(value)
            except (IndexError, KeyError, ValueError):
                return _default_format(value)
        return _default_format(value)


def _legend_dot(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    size: int,
    color: str,
    owner: Any,
) -> None:
    """画图例小圆点：Pillow 超采样，边缘比 canvas 椭圆干净。"""
    if _HAS_PIL:
        scale = _SUPERSAMPLE
        layer = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse(
            (0, 0, size * scale - 1, size * scale - 1), fill=color
        )
        photo = ImageTk.PhotoImage(layer.resize((size, size), Image.LANCZOS))
        photos = getattr(owner, "_legend_photos", None)
        if photos is None:
            photos = owner._legend_photos = []
        photos.append(photo)
        canvas.create_image(cx, cy, anchor="center", image=photo)
    else:
        radius = size / 2
        canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            fill=color, outline="",
        )


def _series_legend(
    canvas: tk.Canvas,
    right: float,
    top: float,
    names: Sequence[str],
    colors: Sequence[str],
    font: tuple,
    px: Callable[[float], int],
    owner: Any,
) -> None:
    """在顶部右侧画「小圆点 + 名称」图例，放不下的条目直接省略。"""
    owner._legend_photos = []
    measure = tkfont.Font(font=font)
    dot = px(8)
    gap = px(5)
    spacing = px(14)
    entries = [(dot + gap + measure.measure(name), name, color) for name, color in zip(names, colors)]
    total = sum(width for width, _name, _color in entries) + spacing * max(
        0, len(entries) - 1
    )
    x = max(px(4), right - total)
    y = max(px(4), top / 2)
    for width, name, color in entries:
        if x + width > right:
            break
        _legend_dot(canvas, x + dot / 2, y, dot, color, owner)
        canvas.create_text(
            x + dot + gap,
            y,
            text=name,
            anchor="w",
            font=font,
            fill=color_of(T.COLOR_MUTED),
        )
        x += width + spacing


def _bubble_size(
    lines: Sequence[str], font: tuple, pad_x: int, pad_y: int
) -> Tuple[float, float]:
    """量出多行气泡的宽高。"""
    measure = tkfont.Font(font=font)
    width = max(measure.measure(line) for line in lines) + pad_x * 2
    height = measure.metrics("linespace") * len(lines) + pad_y * 2
    return float(width), float(height)


def _draw_bubble(
    canvas: tk.Canvas,
    x: float,
    y: float,
    lines: Sequence[str],
    font: tuple,
    pad_x: int,
    pad_y: int,
    radius: float,
    owner: Any,
) -> None:
    """在 ``(x, y)`` 左上角画多行圆角气泡；照片引用挂在 ``owner`` 上。"""
    bubble_w, bubble_h = _bubble_size(lines, font, pad_x, pad_y)
    fill = color_of(T.COLOR_INPUT)
    outline = color_of(T.COLOR_BORDER_STRONG)
    if _HAS_PIL:
        scale = _SUPERSAMPLE
        layer = Image.new(
            "RGBA", (int(bubble_w * scale), int(bubble_h * scale)), (0, 0, 0, 0)
        )
        pen = ImageDraw.Draw(layer)
        pen.rounded_rectangle(
            (1, 1, bubble_w * scale - 1, bubble_h * scale - 1),
            radius=radius * scale,
            fill=fill,
            outline=outline,
            width=max(1, scale),
        )
        owner._tip_photo = ImageTk.PhotoImage(
            layer.resize((int(bubble_w), int(bubble_h)), Image.LANCZOS)
        )
        canvas.create_image(x, y, anchor="nw", image=owner._tip_photo)
    else:
        canvas.create_rectangle(
            x, y, x + bubble_w, y + bubble_h, fill=fill, outline=outline
        )
    canvas.create_text(
        x + pad_x,
        y + pad_y,
        text="\n".join(lines),
        anchor="nw",
        justify="left",
        font=font,
        fill=color_of(T.COLOR_TEXT),
    )


class ScatterChart(_ChartBase):
    """散点图：横纵轴都是数值，支持多组散点，鼠标靠近圆点时显示坐标。

    用法::

        from ctk_kit import ScatterChart

        chart = ScatterChart(card, series={"男性": [(170, 65), (175, 70)]})
        chart.add_series("女性", [(160, 50), (165, 55)])
        chart.pack(fill="both", expand=True)

    参数:
        master: 父容器。
        points: 单组散点 ``[(x, y), …]``；给 ``series`` 时以 ``series`` 为准。
        name: ``points`` 这组散点的名称。
        series: 多组散点，``{"名称": [(x, y), …]}`` 或 ``[(名称, […]), …]``。
        colors: 圆点颜色；单个颜色全部同色，序列按组循环取用。
        width / height: 初始尺寸（逻辑像素），默认 420 × 280。
        radius: 圆点半径（逻辑像素），默认 4。
        show_grid: 是否画横纵网格，默认 ``True``。
        show_tooltip: 鼠标靠近圆点时是否高亮并显示坐标，默认 ``True``。
        legend: 是否显示图例，默认 ``True``。
        x_ticks / y_ticks: 横 / 纵轴期望的刻度段数，默认 5。
        x_range / y_range: 固定轴范围；不传按数据自动取。
        formatter: 数值文字格式，可以是回调或格式串。
        empty_text: 没有数据时的提示。

    方法:
        get(): ``{名称: [(x, y), …]}``。
        set(points): 换成单组散点。
        add_series(name, points, color=None): 增加或覆盖一组散点。
        set_colors / set_x_range / set_y_range: 换颜色或固定轴范围。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        points: Sequence[Sequence[float]] = (),
        name: str = "数据",
        series: Optional[Sequence[Tuple[str, Sequence[Sequence[float]]]]] = None,
        colors: Optional[ColorArg] = None,
        width: int = 420,
        height: int = 280,
        radius: int = 4,
        show_grid: bool = True,
        show_tooltip: bool = True,
        legend: bool = True,
        x_ticks: int = 5,
        y_ticks: int = 5,
        x_range: Optional[Tuple[float, float]] = None,
        y_range: Optional[Tuple[float, float]] = None,
        formatter: Optional[Formatter] = None,
        empty_text: str = "暂无数据",
        **kwargs: Any,
    ) -> None:
        self._series: Dict[str, List[Tuple[float, float]]] = {}
        self._series_colors: Dict[str, Optional[str]] = {}
        self._colors = colors
        self._point_radius = max(1, int(radius))
        self._show_grid = bool(show_grid)
        self._show_tooltip = bool(show_tooltip)
        self._legend = bool(legend)
        self._x_ticks = max(2, int(x_ticks))
        self._y_ticks = max(2, int(y_ticks))
        self._x_range = _normalize_range(x_range)
        self._y_range = _normalize_range(y_range)
        self._formatter = formatter
        self._empty_text = str(empty_text)
        self._hover: Optional[Tuple[str, int]] = None
        self._layout: Optional[Tuple[float, float, float, float]] = None
        self._screen: List[Tuple[str, int, float, float, str]] = []

        super().__init__(master, width=width, height=height, **kwargs)
        self._canvas.bind("<Motion>", self._on_motion)
        self._canvas.bind("<Leave>", self._on_leave)

        if series is not None:
            items = series.items() if hasattr(series, "items") else series
            for item_name, item_points in items:
                self.add_series(item_name, item_points)
        elif points:
            self.add_series(name, points)
        else:
            self.after_idle(self._redraw)

    # ------------------------------------------------------------ 读写
    def get(self) -> Dict[str, List[Tuple[float, float]]]:
        """当前散点：``{名称: [(x, y), …]}``。"""
        return {key: list(value) for key, value in self._series.items()}

    def set(self, points: Sequence[Sequence[float]]) -> None:
        """换成单组散点；已有的多组会被一组替换。"""
        only = next(iter(self._series), "数据") if len(self._series) == 1 else "数据"
        self._series = {only: _to_points(points)}
        self._series_colors = {only: self._series_colors.get(only)}
        self._schedule_redraw()

    def add_series(
        self,
        name: str,
        points: Sequence[Sequence[float]],
        *,
        color: Optional[str] = None,
    ) -> None:
        """增加一组散点；同名会覆盖原来的点。"""
        key = str(name)
        self._series[key] = _to_points(points)
        self._series_colors[key] = color
        self._schedule_redraw()

    def set_colors(self, colors: Optional[ColorArg]) -> None:
        """换圆点颜色；单个颜色全部同色，序列按组循环取用。"""
        self._colors = colors
        self._schedule_redraw()

    def set_x_range(self, low: Optional[float], high: Optional[float] = None) -> None:
        """固定横轴范围；传 ``None`` 恢复自动。"""
        self._x_range = _normalize_range((low, high)) if low is not None else None
        self._schedule_redraw()

    def set_y_range(self, low: Optional[float], high: Optional[float] = None) -> None:
        """固定纵轴范围；传 ``None`` 恢复自动。"""
        self._y_range = _normalize_range((low, high)) if low is not None else None
        self._schedule_redraw()

    # ------------------------------------------------------------ 绘制
    def _color_for(self, index: int, name: str) -> str:
        """取某一组散点的颜色。"""
        explicit = self._series_colors.get(name)
        source = explicit if explicit is not None else self._colors
        default = color_of(getattr(T, _SERIES_TOKENS[index % len(_SERIES_TOKENS)]))
        if source is None:
            return default
        if isinstance(source, str):
            return color_of(source)
        palette = list(source)
        return color_of(palette[index % len(palette)]) if palette else default

    def _ranges(self) -> Tuple[float, float, float, float]:
        """算横纵轴范围（固定范围优先）。"""
        xs = [x for points in self._series.values() for x, _y in points] or [0.0]
        ys = [y for points in self._series.values() for _x, y in points] or [0.0]
        x_low, x_high = self._x_range or (min(xs), max(xs))
        y_low, y_high = self._y_range or (min(ys), max(ys))
        return x_low, x_high, y_low, y_high

    def _redraw(self) -> None:
        """画坐标轴、网格、散点和悬停提示。"""
        if self._redraw_job is not None:
            try:
                self.after_cancel(self._redraw_job)
            except tk.TclError:
                pass
            self._redraw_job = None

        canvas = self._canvas
        if not canvas.winfo_exists():
            return
        canvas.delete("all")
        self._layout = None
        self._screen = []
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        tick_font = self._font(T.FONT_TINY)
        label_font = self._font(T.FONT_SMALL)
        measure_tick = tkfont.Font(font=tick_font)

        if not self._series:
            self._hover = None
            canvas.create_text(
                width / 2,
                height / 2,
                text=self._empty_text,
                anchor="center",
                font=label_font,
                fill=color_of(T.COLOR_FAINT),
            )
            return

        x_low, x_high, y_low, y_high = self._ranges()
        x_ticks = _nice_ticks(x_low, x_high, self._x_ticks)
        y_ticks = _nice_ticks(y_low, y_high, self._y_ticks)
        x_labels = [self._format_value(tick) for tick in x_ticks]
        y_labels = [self._format_value(tick) for tick in y_ticks]
        left = max(measure_tick.measure(text) for text in y_labels) + self._px(10)
        top = self._px(28) if self._legend else self._px(12)
        right = self._px(10)
        bottom = self._px(30)
        plot_left = float(left)
        plot_top = float(top)
        plot_right = float(width - right)
        plot_bottom = float(height - bottom)
        if plot_right - plot_left < 16 or plot_bottom - plot_top < 16:
            return

        x_span = x_ticks[-1] - x_ticks[0] or 1.0
        y_span = y_ticks[-1] - y_ticks[0] or 1.0

        def x_of(value: float) -> float:
            """横轴数值 → 画布 x。"""
            return plot_left + (value - x_ticks[0]) / x_span * (plot_right - plot_left)

        def y_of(value: float) -> float:
            """纵轴数值 → 画布 y。"""
            return plot_bottom - (value - y_ticks[0]) / y_span * (plot_bottom - plot_top)

        # ---- 网格 ----
        if self._show_grid:
            for tick in x_ticks:
                canvas.create_line(
                    x_of(tick), plot_top, x_of(tick), plot_bottom,
                    fill=color_of(T.COLOR_BORDER),
                )
        for tick, text in zip(y_ticks, y_labels):
            if self._show_grid:
                canvas.create_line(
                    plot_left, y_of(tick), plot_right, y_of(tick),
                    fill=color_of(T.COLOR_BORDER),
                )
            canvas.create_text(
                plot_left - self._px(8), y_of(tick), text=text, anchor="e",
                font=tick_font, fill=color_of(T.COLOR_FAINT),
            )
        for tick, text in zip(x_ticks, x_labels):
            canvas.create_text(
                x_of(tick), plot_bottom + self._px(6), text=text, anchor="n",
                font=tick_font, fill=color_of(T.COLOR_FAINT),
            )

        # ---- 散点 ----
        items = list(self._series.items())
        colors = [self._color_for(index, key) for index, (key, _pts) in enumerate(items)]
        for (key, points), color in zip(items, colors):
            for index, (x_value, y_value) in enumerate(points):
                if x_ticks[0] <= x_value <= x_ticks[-1] and y_ticks[0] <= y_value <= y_ticks[-1]:
                    self._screen.append(
                        (key, index, x_of(x_value), y_of(y_value), color)
                    )
        self._layout = (plot_left, plot_top, plot_right, plot_bottom)

        size = self._px(self._point_radius)
        if _HAS_PIL:
            scale = _SUPERSAMPLE
            layer = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
            pen = ImageDraw.Draw(layer)
            for key, index, cx, cy, color in self._screen:
                hovered = self._hover == (key, index)
                dot = size * (1.8 if hovered else 1.0) * scale
                box = (cx * scale - dot, cy * scale - dot, cx * scale + dot, cy * scale + dot)
                if hovered:
                    pen.ellipse(box, fill=color, outline=(255, 255, 255, 230), width=max(1, scale))
                else:
                    pen.ellipse(box, fill=color)
            self._photo = ImageTk.PhotoImage(layer.resize((width, height), Image.LANCZOS))
            canvas.create_image(0, 0, anchor="nw", image=self._photo)
        else:
            for key, index, cx, cy, color in self._screen:
                hovered = self._hover == (key, index)
                r = size * 2 if hovered else size
                canvas.create_oval(
                    cx - r, cy - r, cx + r, cy + r, fill=color,
                    outline=color_of(T.COLOR_TEXT) if hovered else color,
                )

        if self._legend:
            _series_legend(
                canvas, plot_right, top, [key for key, _pts in items], colors,
                self._font(T.FONT_TINY), self._px, self,
            )

        if self._show_tooltip and self._hover is not None:
            self._draw_tooltip(canvas, width, height)

    def _draw_tooltip(self, canvas: tk.Canvas, width: int, height: int) -> None:
        """在鼠标附近显示悬停圆点所属系列和坐标。"""
        assert self._hover is not None
        key, index = self._hover
        points = self._series.get(key, [])
        if index >= len(points):
            return
        x_value, y_value = points[index]
        lines = [key, f"x  {self._format_value(x_value)}", f"y  {self._format_value(y_value)}"]
        font = self._font(T.FONT_SMALL)
        pad_x, pad_y = self._px(9), self._px(6)
        bubble_w, bubble_h = _bubble_size(lines, font, pad_x, pad_y)
        point = next(
            ((px, py) for name, idx, px, py, _color in self._screen if (name, idx) == (key, index)),
            None,
        )
        if point is None:
            return
        bubble_x = min(max(point[0] + self._px(10), 0), max(0, width - bubble_w))
        bubble_y = min(max(point[1] - bubble_h - self._px(10), 0), max(0, height - bubble_h))
        _draw_bubble(
            canvas, bubble_x, bubble_y, lines, font, pad_x, pad_y,
            float(self._px(T.RADIUS_SMALL)), self,
        )

    # ------------------------------------------------------------ 鼠标
    def _on_motion(self, event: tk.Event) -> None:
        """找最近的圆点（12px 内），变了才重画。"""
        if not self._show_tooltip:
            return
        limit = self._px(12)
        nearest: Optional[Tuple[str, int]] = None
        best = float(limit * limit)
        for key, index, px, py, _color in self._screen:
            distance = (event.x - px) ** 2 + (event.y - py) ** 2
            if distance <= best:
                best = distance
                nearest = (key, index)
        if nearest != self._hover:
            self._hover = nearest
            self._redraw()

    def _on_leave(self, _event: tk.Event) -> None:
        """指针离开时收起提示。"""
        if self._hover is not None:
            self._hover = None
            self._redraw()


def _to_points(points: Sequence[Sequence[float]]) -> List[Tuple[float, float]]:
    """把 ``[(x, y), …]`` 统一成浮点二元组，坏数据按 0 处理。"""
    result: List[Tuple[float, float]] = []
    for point in points:
        values = list(point)
        if len(values) >= 2:
            result.append((_to_float(values[0]), _to_float(values[1])))
    return result


class PieChart(_ChartBase):
    """饼图 / 环形图：扇区按数值占比切分，右侧图例带百分比。

    用法::

        from ctk_kit import PieChart

        chart = PieChart(card, values=[42, 28, 18, 12],
                         labels=["官网", "小程序", "公众号", "其它"], donut=0.55)
        chart.pack(fill="both", expand=True)

    参数:
        master: 父容器。
        values: 各扇区的数值（小于 0 按 0 处理）。
        labels: 扇区名称；不传用 ``"1"`` / ``"2"`` …。
        colors: 扇区颜色；单个颜色全部同色，序列按扇区循环取用。
        width / height: 初始尺寸（逻辑像素），默认 420 × 280。
        donut: 环形内孔占比（0–0.9），默认 0 为实心饼图。
        show_tooltip: 悬停是否高亮扇区并显示数值，默认 ``True``。
        legend: 是否在右侧显示图例，默认 ``True``。
        formatter: 数值文字格式（只影响提示气泡里的数值）。
        empty_text: 没有数据时的提示。

    方法:
        get(): 当前数值列表。
        set(values, labels=None): 换数据。
        set_labels(labels) / set_colors(colors) / set_donut(ratio)。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        values: Sequence[float] = (),
        labels: Optional[Sequence[Any]] = None,
        colors: Optional[ColorArg] = None,
        width: int = 420,
        height: int = 280,
        donut: float = 0.0,
        show_tooltip: bool = True,
        legend: bool = True,
        formatter: Optional[Formatter] = None,
        empty_text: str = "暂无数据",
        **kwargs: Any,
    ) -> None:
        self._values = [_to_float(value) for value in values]
        self._labels = [str(label) for label in (labels or ())]
        self._colors = colors
        self._donut = max(0.0, min(0.9, float(donut)))
        self._show_tooltip = bool(show_tooltip)
        self._legend = bool(legend)
        self._formatter = formatter
        self._empty_text = str(empty_text)
        self._hover: Optional[int] = None
        self._geometry: Optional[Tuple[float, float, float]] = None

        super().__init__(master, width=width, height=height, **kwargs)
        self._canvas.bind("<Motion>", self._on_motion)
        self._canvas.bind("<Leave>", self._on_leave)
        self.after_idle(self._redraw)

    # ------------------------------------------------------------ 读写
    def get(self) -> List[float]:
        """当前数值列表。"""
        return list(self._values)

    def set(self, values: Sequence[float], labels: Optional[Sequence[Any]] = None) -> None:
        """换数据；``labels`` 不传时沿用旧的（长度不匹配就重置成序号）。"""
        self._values = [_to_float(value) for value in values]
        if labels is not None:
            self._labels = [str(label) for label in labels]
        if len(self._labels) != len(self._values):
            self._labels = [str(index + 1) for index in range(len(self._values))]
        self._schedule_redraw()

    def set_labels(self, labels: Sequence[Any]) -> None:
        """只换扇区名称。"""
        self._labels = [str(label) for label in labels]
        self._schedule_redraw()

    def set_colors(self, colors: Optional[ColorArg]) -> None:
        """换扇区颜色。"""
        self._colors = colors
        self._schedule_redraw()

    def set_donut(self, ratio: float) -> None:
        """调整环形内孔占比（0 为实心饼图）。"""
        self._donut = max(0.0, min(0.9, float(ratio)))
        self._schedule_redraw()

    # ------------------------------------------------------------ 绘制
    def _color_for(self, index: int) -> str:
        """取第 ``index`` 个扇区的颜色。"""
        source = self._colors
        default = color_of(getattr(T, _SERIES_TOKENS[index % len(_SERIES_TOKENS)]))
        if source is None:
            return default
        if isinstance(source, str):
            return color_of(source)
        palette = list(source)
        return color_of(palette[index % len(palette)]) if palette else default

    def _shares(self) -> Tuple[float, List[float]]:
        """总值与各扇区占比（占比 0–1）。"""
        positive = [max(0.0, value) for value in self._values]
        total = sum(positive)
        if total <= 0:
            return 0.0, [0.0 for _ in positive]
        return total, [value / total for value in positive]

    def _redraw(self) -> None:
        """画扇区、图例和悬停提示。"""
        if self._redraw_job is not None:
            try:
                self.after_cancel(self._redraw_job)
            except tk.TclError:
                pass
            self._redraw_job = None

        canvas = self._canvas
        if not canvas.winfo_exists():
            return
        canvas.delete("all")
        self._geometry = None
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        label_font = self._font(T.FONT_SMALL)
        total, shares = self._shares()
        if total <= 0:
            self._hover = None
            canvas.create_text(
                width / 2, height / 2, text=self._empty_text, anchor="center",
                font=label_font, fill=color_of(T.COLOR_FAINT),
            )
            return

        # 右侧留图例的位置，剩下的方形区域放饼
        measure = tkfont.Font(font=self._font(T.FONT_TINY))
        legend_w = 0.0
        if self._legend:
            texts = [
                f"{self._label_at(index)}  {shares[index] * 100:.0f}%"
                for index in range(len(self._values))
            ]
            legend_w = min(
                max(measure.measure(text) for text in texts) + self._px(34),
                width * 0.45,
            )
        area_left = 0.0
        area_right = width - legend_w
        area_top = 0.0
        area_bottom = float(height)
        radius = max(
            8.0,
            min(
                (area_right - area_left) / 2 - self._px(10),
                (area_bottom - area_top) / 2 - self._px(10),
            ),
        )
        center_x = (area_left + area_right) / 2
        center_y = (area_top + area_bottom) / 2
        self._geometry = (center_x, center_y, radius)

        base_colors = [self._color_for(index) for index in range(len(self._values))]
        start = -90.0
        if _HAS_PIL:
            scale = _SUPERSAMPLE
            layer = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
            pen = ImageDraw.Draw(layer)
            bg = _canvas_bg(self)
            for index, share in enumerate(shares):
                end = start + share * 360.0
                if share > 0:
                    color = base_colors[index]
                    if self._hover == index:
                        color = _lighten(color, 0.16)
                        draw_radius = radius + self._px(5)
                    else:
                        draw_radius = radius
                    pen.pieslice(
                        (
                            (center_x - draw_radius) * scale,
                            (center_y - draw_radius) * scale,
                            (center_x + draw_radius) * scale,
                            (center_y + draw_radius) * scale,
                        ),
                        start=start,
                        end=end,
                        fill=color,
                        outline=bg,
                        width=max(1, scale),
                    )
                start = end
            if self._donut > 0:
                inner = radius * self._donut
                pen.ellipse(
                    (
                        (center_x - inner) * scale,
                        (center_y - inner) * scale,
                        (center_x + inner) * scale,
                        (center_y + inner) * scale,
                    ),
                    fill=bg,
                )
            self._photo = ImageTk.PhotoImage(layer.resize((width, height), Image.LANCZOS))
            canvas.create_image(0, 0, anchor="nw", image=self._photo)
        else:
            start = -90.0
            for index, share in enumerate(shares):
                end = start + share * 360.0
                if share > 0:
                    canvas.create_arc(
                        center_x - radius, center_y - radius,
                        center_x + radius, center_y + radius,
                        start=start, extent=share * 360.0, style="pieslice",
                        fill=base_colors[index], outline="",
                    )
                start = end

        if self._legend:
            self._draw_legend(canvas, width - legend_w, height, shares, base_colors)

        if self._show_tooltip and self._hover is not None:
            self._draw_tooltip(canvas, width, height)

    def _label_at(self, index: int) -> str:
        """扇区名称；没有就补序号。"""
        return self._labels[index] if index < len(self._labels) else str(index + 1)

    def _draw_legend(
        self,
        canvas: tk.Canvas,
        left: float,
        height: int,
        shares: Sequence[float],
        colors: Sequence[str],
    ) -> None:
        """右侧竖排图例：色块 + 名称 + 百分比。"""
        font = self._font(T.FONT_TINY)
        measure = tkfont.Font(font=font)
        dot = self._px(8)
        gap = self._px(7)
        line_h = measure.metrics("linespace") + self._px(8)
        x = left + self._px(12)
        y = max(self._px(10), (height - line_h * len(colors)) / 2 + line_h / 2)
        for index, color in enumerate(colors):
            text = f"{self._label_at(index)}  {shares[index] * 100:.0f}%"
            if x + measure.measure(text) + dot + gap > self._canvas.winfo_width():
                break
            canvas.create_rectangle(
                x, y - dot / 2, x + dot, y + dot / 2, fill=color, outline=""
            )
            canvas.create_text(
                x + dot + gap, y, text=text, anchor="w", font=font,
                fill=color_of(T.COLOR_MUTED),
            )
            y += line_h

    def _draw_tooltip(self, canvas: tk.Canvas, width: int, height: int) -> None:
        """在指针右侧显示扇区名称、数值和百分比。"""
        assert self._hover is not None
        index = self._hover
        total, shares = self._shares()
        if index >= len(self._values) or total <= 0:
            return
        lines = [
            self._label_at(index),
            f"{self._format_value(self._values[index])}  ({shares[index] * 100:.0f}%)",
        ]
        font = self._font(T.FONT_SMALL)
        pad_x, pad_y = self._px(9), self._px(6)
        bubble_w, bubble_h = _bubble_size(lines, font, pad_x, pad_y)
        cx, cy, radius = self._geometry or (width / 2, height / 2, 10.0)
        bubble_x = min(max(cx + radius * 0.3, 0), max(0, width - bubble_w))
        bubble_y = min(max(cy - bubble_h / 2, 0), max(0, height - bubble_h))
        _draw_bubble(
            canvas, bubble_x, bubble_y, lines, font, pad_x, pad_y,
            float(self._px(T.RADIUS_SMALL)), self,
        )

    # ------------------------------------------------------------ 鼠标
    def _on_motion(self, event: tk.Event) -> None:
        """按指针方向算出落在哪个扇区，变了才重画。"""
        if not self._show_tooltip or self._geometry is None:
            return
        cx, cy, radius = self._geometry
        dx, dy = event.x - cx, event.y - cy
        if dx * dx + dy * dy > (radius + self._px(6)) ** 2:
            self._set_hover(None)
            return
        total, shares = self._shares()
        if total <= 0:
            self._set_hover(None)
            return
        angle = (math.degrees(math.atan2(dy, dx)) + 90.0) % 360.0
        cursor = 0.0
        for index, share in enumerate(shares):
            cursor += share * 360.0
            if angle <= cursor:
                self._set_hover(index)
                return
        self._set_hover(len(shares) - 1)

    def _on_leave(self, _event: tk.Event) -> None:
        """指针离开时收起提示。"""
        self._set_hover(None)

    def _set_hover(self, index: Optional[int]) -> None:
        """更新悬停扇区；没变化就不重画。"""
        if index == self._hover:
            return
        self._hover = index
        self._redraw()


class RadarChart(_ChartBase):
    """雷达图：多个维度围成一圈，每个系列画成一个多边形。

    用法::

        from ctk_kit import RadarChart

        chart = RadarChart(card, axes=["速度", "力量", "技巧", "耐力", "智力"],
                           max_value=100)
        chart.add_series("小李", [80, 62, 74, 56, 90])
        chart.add_series("小王", [70, 85, 60, 72, 66])
        chart.pack(fill="both", expand=True)

    参数:
        master: 父容器。
        axes: 各维度名称。
        series: 多系列数据，``{"名称": [值…]}`` 或 ``[(名称, […]), …]``。
        colors: 系列颜色；单个颜色全部同色，序列按系列循环取用。
        width / height: 初始尺寸（逻辑像素），默认 420 × 320。
        max_value: 纵轴满值；不传取数据最大值（至少为 1）。
        rings: 网格圈数，默认 5。
        show_tooltip: 悬停是否显示该维度的各系列数值，默认 ``True``。
        legend: 是否显示图例，默认 ``True``。
        formatter: 数值文字格式。
        empty_text: 没有数据时的提示。

    方法:
        get(): ``{名称: [值…]}``。
        add_series(name, values, color=None) / set_series(name, values)。
        set_axes(axes) / set_colors(colors) / set_max_value(value)。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        axes: Sequence[Any] = (),
        series: Optional[Sequence[Tuple[str, Sequence[float]]]] = None,
        colors: Optional[ColorArg] = None,
        width: int = 420,
        height: int = 320,
        max_value: Optional[float] = None,
        rings: int = 5,
        show_tooltip: bool = True,
        legend: bool = True,
        formatter: Optional[Formatter] = None,
        empty_text: str = "暂无数据",
        **kwargs: Any,
    ) -> None:
        self._axes = [str(axis) for axis in axes]
        self._series: Dict[str, List[float]] = {}
        self._series_colors: Dict[str, Optional[str]] = {}
        self._colors = colors
        self._max_value = None if max_value is None else max(0.0, float(max_value))
        self._rings = max(1, int(rings))
        self._show_tooltip = bool(show_tooltip)
        self._legend = bool(legend)
        self._formatter = formatter
        self._empty_text = str(empty_text)
        self._hover: Optional[int] = None
        self._geometry: Optional[Tuple[float, float, float, int]] = None

        super().__init__(master, width=width, height=height, **kwargs)
        self._canvas.bind("<Motion>", self._on_motion)
        self._canvas.bind("<Leave>", self._on_leave)

        if series is not None:
            items = series.items() if hasattr(series, "items") else series
            for item_name, item_values in items:
                self.add_series(item_name, item_values)
        else:
            self.after_idle(self._redraw)

    # ------------------------------------------------------------ 读写
    def get(self) -> Dict[str, List[float]]:
        """当前各系列数值。"""
        return {key: list(value) for key, value in self._series.items()}

    def add_series(
        self,
        name: str,
        values: Sequence[float],
        *,
        color: Optional[str] = None,
    ) -> None:
        """增加或覆盖一个系列。"""
        key = str(name)
        self._series[key] = [_to_float(value) for value in values]
        self._series_colors[key] = color
        self._schedule_redraw()

    def set_series(self, name: str, values: Sequence[float]) -> None:
        """覆盖一个系列的数据；不存在就新增。"""
        self.add_series(name, values)

    def set_axes(self, axes: Sequence[Any]) -> None:
        """换维度名称。"""
        self._axes = [str(axis) for axis in axes]
        self._schedule_redraw()

    def set_colors(self, colors: Optional[ColorArg]) -> None:
        """换系列颜色。"""
        self._colors = colors
        self._schedule_redraw()

    def set_max_value(self, value: Optional[float]) -> None:
        """固定满值；传 ``None`` 恢复按数据自动取。"""
        self._max_value = None if value is None else max(0.0, float(value))
        self._schedule_redraw()

    # ------------------------------------------------------------ 绘制
    def _color_for(self, index: int, name: str) -> str:
        """取第 ``index`` 个系列的颜色。"""
        explicit = self._series_colors.get(name)
        source = explicit if explicit is not None else self._colors
        default = color_of(getattr(T, _SERIES_TOKENS[index % len(_SERIES_TOKENS)]))
        if source is None:
            return default
        if isinstance(source, str):
            return color_of(source)
        palette = list(source)
        return color_of(palette[index % len(palette)]) if palette else default

    def _axis_count(self) -> int:
        """维度数：取轴名称与各系列长度的最大值。"""
        if not self._series:
            return 0
        return max([len(self._axes)] + [len(values) for values in self._series.values()])

    def _axis_name(self, index: int) -> str:
        """第 ``index`` 个维度的名称。"""
        return self._axes[index] if index < len(self._axes) else str(index + 1)

    def _redraw(self) -> None:
        """画网格、多边形、轴标签、图例和悬停提示。"""
        if self._redraw_job is not None:
            try:
                self.after_cancel(self._redraw_job)
            except tk.TclError:
                pass
            self._redraw_job = None

        canvas = self._canvas
        if not canvas.winfo_exists():
            return
        canvas.delete("all")
        self._geometry = None
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        label_font = self._font(T.FONT_SMALL)
        count = self._axis_count()
        if count < 3:
            self._hover = None
            canvas.create_text(
                width / 2, height / 2, text=self._empty_text, anchor="center",
                font=label_font, fill=color_of(T.COLOR_FAINT),
            )
            return

        top = self._px(28) if self._legend else self._px(8)
        margin = self._px(40)
        radius = max(10.0, min(width / 2, (height - top) / 2) - margin)
        center_x = width / 2
        center_y = top + (height - top) / 2
        self._geometry = (center_x, center_y, radius, count)

        def point_at(index: int, ratio: float) -> Tuple[float, float]:
            """第 ``index`` 个轴上、距圆心 ``ratio`` 倍半径处的坐标。"""
            angle = math.radians(-90.0 + 360.0 * index / count)
            return (
                center_x + math.cos(angle) * radius * ratio,
                center_y + math.sin(angle) * radius * ratio,
            )

        # ---- 网格与轴 ----
        for ring in range(1, self._rings + 1):
            ratio = ring / self._rings
            points = [coord for index in range(count) for coord in point_at(index, ratio)]
            canvas.create_polygon(
                points, fill="", outline=color_of(T.COLOR_BORDER),
            )
        for index in range(count):
            x, y = point_at(index, 1.0)
            canvas.create_line(
                center_x, center_y, x, y, fill=color_of(T.COLOR_BORDER)
            )

        # ---- 系列 ----
        values_all = [value for items in self._series.values() for value in items]
        top_value = self._max_value or (max(values_all) if values_all else 1.0)
        if top_value <= 0:
            top_value = 1.0
        items = list(self._series.items())
        colors = [self._color_for(index, key) for index, (key, _values) in enumerate(items)]
        if _HAS_PIL:
            scale = _SUPERSAMPLE
            canvas_size = (width * scale, height * scale)
            layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
            for (key, values), color in zip(items, colors):
                points = [
                    point_at(index, min(1.0, max(0.0, value / top_value)))
                    for index, value in enumerate(values)
                ]
                if len(points) < 3:
                    continue
                # 每个系列单独一层再合成，重叠区域的透明度会累加，
                # 直接画在同一层会把前面的填色整片覆盖掉
                overlay = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
                pen = ImageDraw.Draw(overlay)
                polygon = [(x * scale, y * scale) for x, y in points]
                pen.polygon(polygon, fill=_rgba(color, 45))
                pen.line(polygon + [polygon[0]], fill=color, width=max(2, self._px(2) * scale))
                dot = max(2, int(self._px(3) * scale))
                for index, (x, y) in enumerate(points):
                    hovered = self._hover is not None and index == self._hover
                    r = dot * 1.8 if hovered else dot
                    box = (x * scale - r, y * scale - r, x * scale + r, y * scale + r)
                    if hovered:
                        pen.ellipse(box, fill=color, outline=(255, 255, 255, 230), width=max(1, scale))
                    else:
                        pen.ellipse(box, fill=color)
                layer = Image.alpha_composite(layer, overlay)
            self._photo = ImageTk.PhotoImage(layer.resize((width, height), Image.LANCZOS))
            canvas.create_image(0, 0, anchor="nw", image=self._photo)
        else:
            for (key, values), color in zip(items, colors):
                points = [
                    point_at(index, min(1.0, max(0.0, value / top_value)))
                    for index, value in enumerate(values)
                ]
                if len(points) < 3:
                    continue
                canvas.create_polygon(
                    [coord for point in points for coord in point],
                    fill=color, outline=color, stipple="gray25",
                )
                for index, (x, y) in enumerate(points):
                    r = self._px(3) * (2 if self._hover == index else 1)
                    canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=color)

        # ---- 轴标签 ----
        for index in range(count):
            x, y = point_at(index, 1.0)
            dx, dy = x - center_x, y - center_y
            if abs(dx) <= 1:
                anchor = "n" if dy > 1 else ("s" if dy < -1 else "center")
            elif abs(dy) <= 1:
                anchor = "w" if dx > 1 else "e"
            else:
                anchor = ("n" if dy > 1 else "s") + ("w" if dx > 1 else "e")
            gap = self._px(10)
            canvas.create_text(
                x + dx / radius * gap,
                y + dy / radius * gap,
                text=self._axis_name(index), anchor=anchor,
                font=self._font(T.FONT_TINY),
                fill=color_of(T.COLOR_TEXT if self._hover == index else T.COLOR_MUTED),
            )

        if self._legend:
            _series_legend(
                canvas, width - self._px(8), top, [key for key, _values in items],
                colors, self._font(T.FONT_TINY), self._px, self,
            )

        if self._show_tooltip and self._hover is not None:
            self._draw_tooltip(canvas, width, height)

    def _draw_tooltip(self, canvas: tk.Canvas, width: int, height: int) -> None:
        """显示悬停维度上各系列的数值。"""
        assert self._hover is not None
        index = self._hover
        lines = [self._axis_name(index)]
        for key, values in self._series.items():
            if index < len(values):
                lines.append(f"{key}  {self._format_value(values[index])}")
        if len(lines) == 1:
            return
        font = self._font(T.FONT_SMALL)
        pad_x, pad_y = self._px(9), self._px(6)
        bubble_w, bubble_h = _bubble_size(lines, font, pad_x, pad_y)
        geometry = self._geometry
        center_x = width / 2
        if geometry is not None:
            center_x = geometry[0]
        bubble_x = (
            self._px(8) if center_x <= width / 2 else max(0.0, width - bubble_w - self._px(8))
        )
        bubble_y = self._px(34)
        bubble_y = min(bubble_y, max(0.0, height - bubble_h))
        _draw_bubble(
            canvas, bubble_x, bubble_y, lines, font, pad_x, pad_y,
            float(self._px(T.RADIUS_SMALL)), self,
        )

    # ------------------------------------------------------------ 鼠标
    def _on_motion(self, event: tk.Event) -> None:
        """按指针方向找最近的轴，变了才重画。"""
        if not self._show_tooltip or self._geometry is None:
            return
        cx, cy, radius, count = self._geometry
        dx, dy = event.x - cx, event.y - cy
        if dx * dx + dy * dy > (radius * 1.15) ** 2:
            self._set_hover(None)
            return
        angle = (math.degrees(math.atan2(dy, dx)) + 90.0) % 360.0
        step = 360.0 / count
        index = int(round(angle / step)) % count
        self._set_hover(index)

    def _on_leave(self, _event: tk.Event) -> None:
        """指针离开时收起提示。"""
        self._set_hover(None)

    def _set_hover(self, index: Optional[int]) -> None:
        """更新悬停轴；没变化就不重画。"""
        if index == self._hover:
            return
        self._hover = index
        self._redraw()


def _normalize_range(
    value: Optional[Sequence[Optional[float]]],
) -> Optional[Tuple[float, float]]:
    """把 ``(low, high)`` 统一成升序浮点二元组；缺值或相等时返回 ``None``。"""
    if value is None:
        return None
    items = list(value)
    if len(items) < 2 or items[0] is None or items[1] is None:
        return None
    low, high = _to_float(items[0]), _to_float(items[1])
    if low == high:
        return None
    return (low, high) if low < high else (high, low)
