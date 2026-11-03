"""范围滑块：一根轨道、两个圆球，选一段区间。

和 ``Switch`` 一样用 Pillow 在 4 倍尺寸上画轨道和圆球，缩回时靠重采样
把边缘磨平——Tk 的 canvas 不做抗锯齿，直接画椭圆会有一格一格的阶梯。

用法::

    from ctk_kit import RangeSlider

    price = RangeSlider(card, from_=0, to=1000, values=(200, 800),
                        command=lambda low, high: print(low, high))
    price.pack(fill="x", padx=16, pady=12)

``get()`` 返回 ``(low, high)``；``set(low, high)`` 直接改值，默认不回调。
拖着圆球移动时只在松开鼠标时回调一次，避免拖动过程中反复请求数据。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional, Sequence, Tuple

import customtkinter as ctk

from . import tokens as T
from .theme import color_of

try:  # Pillow 是可选依赖
    from PIL import Image, ImageDraw, ImageTk

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

__all__ = ["RangeSlider"]

RangeCommand = Optional[Callable[[float, float], None]]

#: 超采样倍数。
_SCALE = 4
#: 轨道高度（逻辑像素）。
_TRACK_HEIGHT = 6
#: 圆球直径（逻辑像素）。
_KNOB = 18


def _parent_bg(master: tk.Misc) -> str:
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


class RangeSlider(ctk.CTkFrame):
    """双滑块范围选择。

    参数:
        master: 父容器。
        from_: 最小值，默认 0。
        to: 最大值，默认 100。
        values: 初始 ``(low, high)``，默认 ``(from_, to)``。
        width: 整体宽度，默认 240。
        height: 高度，默认 28（要能放下圆球）。
        step: 大于 0 时按这个步长取整。
        command: 松开鼠标时的回调，参数是 ``(low, high)``。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        get(): 当前 ``(low, high)``。
        set(low, high, notify=False): 改区间，``notify=True`` 时也回调。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        from_: float = 0.0,
        to: float = 100.0,
        values: Optional[Sequence[float]] = None,
        width: int = 240,
        height: int = 28,
        step: float = 0.0,
        command: RangeCommand = None,
        **kwargs: Any,
    ) -> None:
        """建范围滑块；两个圆球初始在 ``values`` 或两端。"""
        super().__init__(master, fg_color="transparent", **kwargs)

        self._from = float(from_)
        self._to = float(to) if float(to) != float(from_) else self._from + 1.0
        self._step = max(0.0, float(step))
        self._command = command
        self._width = max(60, int(width))
        self._height = max(_KNOB + 4, int(height))
        self._pad = _KNOB // 2 + 2

        start = (self._from, self._to) if values is None else values
        self._low, self._high = self._clamp_pair(float(start[0]), float(start[1]))
        self._active = 0
        self._photo = None

        self._canvas = tk.Canvas(
            self,
            width=self._width,
            height=self._height,
            bg=_parent_bg(self),
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._canvas.pack()
        self._canvas.bind("<Button-1>", self._press)
        self._canvas.bind("<B1-Motion>", self._drag)
        self._canvas.bind("<ButtonRelease-1>", self._release)
        self._render()

    # --- 对外 ---
    def get(self) -> Tuple[float, float]:
        """当前区间 ``(low, high)``。"""
        return self._low, self._high

    def set(self, low: float, high: float, notify: bool = False) -> None:
        """改区间；超出范围会夹紧，``low > high`` 会自动对调。"""
        self._low, self._high = self._clamp_pair(float(low), float(high))
        self._render()
        if notify and self._command is not None:
            self._command(self._low, self._high)

    def configure(self, **kwargs: Any) -> None:
        """``command=`` 换回调，其余交给 ``CTkFrame``。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        return super().configure(**kwargs)

    # --- 内部 ---
    def _clamp(self, value: float) -> float:
        """夹到 ``[from_, to]``，并按 ``step`` 取整。"""
        value = max(self._from, min(self._to, value))
        if self._step > 0:
            value = self._from + round((value - self._from) / self._step) * self._step
            value = max(self._from, min(self._to, value))
            # 消掉浮点尾差
            value = round(value, 6)
        return value

    def _clamp_pair(self, low: float, high: float) -> Tuple[float, float]:
        """排序并夹紧两个值。"""
        low, high = sorted((self._clamp(low), self._clamp(high)))
        return low, high

    def _track_width(self) -> float:
        """圆球圆心可以走的像素宽度。"""
        return self._width - 2 * self._pad

    def _value_to_x(self, value: float) -> float:
        """值 → 画布上的 x 坐标。"""
        ratio = (value - self._from) / (self._to - self._from)
        return self._pad + ratio * self._track_width()

    def _x_to_value(self, x: float) -> float:
        """画布 x 坐标 → 值。"""
        ratio = (x - self._pad) / self._track_width()
        return self._clamp(self._from + ratio * (self._to - self._from))

    def _press(self, event: tk.Event) -> None:
        """按下：选最近的圆球，并立刻跳到点击位置。"""
        low_x = self._value_to_x(self._low)
        high_x = self._value_to_x(self._high)
        self._active = 0 if abs(event.x - low_x) <= abs(event.x - high_x) else 1
        self._drag(event)

    def _drag(self, event: tk.Event) -> None:
        """拖动：更新当前圆球，两个圆球不会交叉。"""
        value = self._x_to_value(event.x)
        if self._active == 0:
            self._low = min(value, self._high)
        else:
            self._high = max(value, self._low)
        self._render()

    def _release(self, _event: tk.Event) -> None:
        """松开：回调一次。"""
        if self._command is not None:
            self._command(self._low, self._high)

    def _render(self) -> None:
        """画轨道、已选段和两个圆球。"""
        canvas = self._canvas
        canvas.delete("all")
        track = color_of(T.COLOR_BORDER_STRONG)
        active = color_of(T.COLOR_ACTIVE)
        knob = color_of(T.COLOR_CARD)

        if not _HAS_PIL:
            self._render_plain(track, active, knob)
            return

        scale = _SCALE
        w, h = self._width, self._height
        image = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
        pen = ImageDraw.Draw(image)
        center = h * scale / 2
        bar = _TRACK_HEIGHT * scale
        x0 = self._pad * scale
        x1 = (self._width - self._pad) * scale

        pen.rounded_rectangle(
            (x0, center - bar / 2, x1, center + bar / 2),
            radius=bar / 2,
            fill=track,
        )
        low_x = self._value_to_x(self._low) * scale
        high_x = self._value_to_x(self._high) * scale
        if high_x > low_x:
            pen.rounded_rectangle(
                (low_x, center - bar / 2, high_x, center + bar / 2),
                radius=bar / 2,
                fill=active,
            )

        radius = _KNOB * scale / 2
        for value in (self._low, self._high):
            cx = self._value_to_x(value) * scale
            pen.ellipse(
                (cx - radius, center - radius, cx + radius, center + radius),
                fill=knob,
                outline=active,
                width=2 * scale,
            )

        self._photo = ImageTk.PhotoImage(
            image.resize((w, h), Image.LANCZOS)
        )
        canvas.create_image(0, 0, anchor="nw", image=self._photo)

    def _render_plain(self, track: str, active: str, knob: str) -> None:
        """没装 Pillow 时的退路：canvas 直角轨道 + 硬边圆球。"""
        canvas = self._canvas
        center = self._height / 2
        half = _TRACK_HEIGHT / 2
        low_x = self._value_to_x(self._low)
        high_x = self._value_to_x(self._high)
        canvas.create_rectangle(
            self._pad,
            center - half,
            self._width - self._pad,
            center + half,
            fill=track,
            outline="",
        )
        if high_x > low_x:
            canvas.create_rectangle(
                low_x, center - half, high_x, center + half, fill=active, outline=""
            )
        radius = _KNOB / 2
        for value in (self._low, self._high):
            cx = self._value_to_x(value)
            canvas.create_oval(
                cx - radius,
                center - radius,
                cx + radius,
                center + radius,
                fill=knob,
                outline=active,
                width=2,
            )
