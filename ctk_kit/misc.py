"""杂项控件：多种样式的进度条。

``Progress`` 比 ``inputs.ProgressBar`` 多几种形态：分格、带百分比文字、
不确定态（来回滚动的动画）。连续条的外观和 ``ProgressBar`` 保持一致。
"""

from __future__ import annotations

import contextlib
import math
import tkinter as tk
from typing import Optional

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .theme import color_of


def _shade(color: str, factor: float) -> str:
    """把 ``#rrggbb`` 整体压暗一点，用来画条纹的暗色斜线。"""
    try:
        value = color.lstrip("#")
        red, green, blue = (int(value[index : index + 2], 16) for index in (0, 2, 4))
    except (ValueError, AttributeError):
        return color
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, round(red * factor))),
        max(0, min(255, round(green * factor))),
        max(0, min(255, round(blue * factor))),
    )


def _parent_bg(master: tk.Misc) -> str:
    """给 canvas 找一个实际背景色：tk 的 canvas 不认 ``transparent``。"""
    try:
        value = master.cget("fg_color")
    except Exception:  # noqa: BLE001
        value = None
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return color_of(value)
    if isinstance(value, str) and value and value != "transparent":
        return value
    return color_of(T.COLOR_CARD)


class Progress(ctk.CTkFrame):
    """进度条：连续 / 分格 / 带百分比文字 / 不确定态。

    整块是一个透明容器，左边是条本身，右边按需放百分比文字。
    条高、圆角都跟着 ``height`` 走；``steps>0`` 时画成一格一格。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        value: float = 0.0,
        width: int = 240,
        height: int = 8,
        steps: int = 0,
        show_text: bool = False,
        striped: bool = False,
        color: Optional[str] = None,
        track: Optional[str] = None,
    ) -> None:
        """创建进度条。

        参数:
            master: 父容器。
            value: 初始进度，0~1。
            width: 整行宽度（含右侧文字），默认 240。
            height: 条本身的高度（像素），默认 8。
            steps: 大于 0 时分格显示，格子数就是它。
            show_text: 右侧是否显示百分比文字。
            striped: ``True`` 时已完成部分画成斜条纹。
            color: 已完成部分的颜色，默认主色（``COLOR_ACTIVE``）。
            track: 轨道颜色，默认 ``COLOR_BORDER_STRONG``。
        """
        super().__init__(master, fg_color="transparent", width=width)
        self._value = max(0.0, min(1.0, float(value)))
        self._steps = max(0, int(steps))
        self._height = max(4, int(height))
        # 统一解析成当前外观下的单值：canvas 只认字符串，不认令牌元组
        self._color = color_of(color or T.COLOR_ACTIVE)
        self._track_color = color_of(track or T.COLOR_BORDER_STRONG)
        self._striped = bool(striped)
        self._segments: list = []
        self._fill: Optional[tk.Misc] = None
        self._label: Optional[ctk.CTkLabel] = None
        self._anim_job: Optional[str] = None
        self._anim_pos = 0.0

        row = ctk.CTkFrame(self, fg_color="transparent", height=self._height)
        row.pack(fill="x", expand=True)
        row.pack_propagate(False)

        if show_text:
            self._label = ctk.CTkLabel(
                row,
                text="0%",
                width=46,
                anchor="e",
                font=get_font(T.FONT_SMALL),
                text_color=T.COLOR_MUTED,
                fg_color="transparent",
            )
            self._label.pack(side="right", padx=(8, 0))

        self._track = ctk.CTkFrame(
            row,
            height=self._height,
            fg_color=T.COLOR_BORDER_STRONG if track is None else track,
            corner_radius=self._height // 2,
        )
        self._track.pack(side="left", fill="x", expand=True)
        self._track.pack_propagate(False)

        if self._steps:
            for index in range(self._steps):
                cell = ctk.CTkFrame(
                    self._track,
                    fg_color="transparent",
                    corner_radius=max(2, self._height // 2 - 1),
                )
                cell.place(
                    relx=index / self._steps,
                    rely=0,
                    relwidth=1 / self._steps - 0.012,
                    relheight=1,
                )
                self._segments.append(cell)
        else:
            if self._striped:
                # 条纹要自己画斜线，用 canvas 当填充层
                canvas = tk.Canvas(
                    self._track,
                    bg=self._color,
                    highlightthickness=0,
                    bd=0,
                )
                canvas.place(relx=0, rely=0, relheight=1, relwidth=0.001)
                canvas.bind("<Configure>", self._draw_stripes)
                self._fill = canvas
            else:
                self._fill = ctk.CTkFrame(
                    self._track,
                    fg_color=self._color,
                    corner_radius=self._height // 2,
                )
                self._fill.place(relx=0, rely=0, relheight=1, relwidth=0.001)

        self._render()

    # ------------------------------------------------------------ 读写
    def get(self) -> float:
        """当前进度（0~1）。"""
        return self._value

    def set(self, value: float) -> None:
        """写入进度；会先夹到 0~1，再按当前形态重画。"""
        self._value = max(0.0, min(1.0, float(value)))
        self._render()

    # ------------------------------------------------------------ 外观
    def _render(self) -> None:
        """按当前值和形态重画。"""
        if self._label is not None:
            self._label.configure(text=f"{round(self._value * 100)}%")
        if self._steps:
            filled = self._value * self._steps
            for index, cell in enumerate(self._segments):
                color = self._color if index < round(filled) else "transparent"
                cell.configure(fg_color=color)
            return
        if self._fill is not None:
            self._fill.place_configure(relwidth=max(0.001, self._value))
            if self._striped:
                self._draw_stripes()

    def _draw_stripes(self, _event: Optional[tk.Event] = None) -> None:
        """在填充层里画 45° 斜条纹；条纹宽度跟着条高走。"""
        canvas = self._fill
        if canvas is None:
            return
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 0 or height <= 0:
            return
        canvas.create_rectangle(0, 0, width, height, fill=self._color, outline="")
        dark = _shade(self._color, 0.82)
        step = max(6, height)
        thick = max(2, height // 3)
        for x in range(-height, width + height, step):
            canvas.create_line(x, height, x + height, 0, fill=dark, width=thick)

    # ------------------------------------------------------------ 不确定态
    def start_indeterminate(self) -> None:
        """切成不确定态：一段色块在轨道里来回滚，用来表示「不知道还要多久」。"""
        if self._steps or self._fill is None or self._anim_job is not None:
            return
        self._anim_pos = -0.3
        self._animate()

    def stop_indeterminate(self) -> None:
        """退出不确定态，回到按 ``value`` 显示。"""
        if self._anim_job is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._anim_job)
            self._anim_job = None
        if self._fill is not None:
            self._fill.place_configure(relx=0, relwidth=max(0.001, self._value))
        self._render()

    @property
    def animating(self) -> bool:
        """当前是不是在跑不确定态动画。"""
        return self._anim_job is not None

    def _animate(self) -> None:
        """一帧：把 30% 宽的色块往右推，出界后从左边重新进来。"""
        if self._fill is None:
            return
        self._anim_pos += 0.02
        if self._anim_pos > 1.0:
            self._anim_pos = -0.3
        self._fill.place_configure(relx=max(0.0, self._anim_pos), relwidth=0.3)
        self._anim_job = self.after(30, self._animate)

    def destroy(self) -> None:
        """销毁前先停掉动画，避免 after 回调打到已销毁的控件上。"""
        if self._anim_job is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._anim_job)
            self._anim_job = None
        super().destroy()


class RingProgress(ctk.CTkFrame):
    """圆环进度：外圈可以带刻度，中间显示百分比。

    圆环用 canvas 的 ``create_arc`` 画；``ticks>0`` 时在环外侧画一圈短线，
    走过的刻度用主色、剩下的用轨道色。整块尺寸由 ``size`` 决定，不随容器拉伸。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        value: float = 0.0,
        size: int = 140,
        thickness: int = 10,
        show_text: bool = True,
        ticks: int = 0,
        color: Optional[str] = None,
        track: Optional[str] = None,
    ) -> None:
        """创建圆环进度。

        参数:
            master: 父容器。
            value: 初始进度，0~1。
            size: 整块的正方形边长（像素），默认 140。
            thickness: 圆环粗细（像素），默认 10。
            show_text: 中心是否显示百分比。
            ticks: 大于 0 时在环外画这么多根刻度线。
            color: 已完成部分的颜色，默认主色。
            track: 轨道颜色，默认 ``COLOR_BORDER_STRONG``。
        """
        super().__init__(master, fg_color="transparent", width=size, height=size)
        self.pack_propagate(False)
        self._size = max(60, int(size))
        self._thickness = max(3, int(thickness))
        self._ticks = max(0, int(ticks))
        # 统一解析成当前外观下的单值：canvas 只认字符串，不认令牌元组
        self._color = color_of(color or T.COLOR_ACTIVE)
        self._track_color = color_of(track or T.COLOR_BORDER_STRONG)
        self._show_text = show_text
        self._value = max(0.0, min(1.0, float(value)))

        self._canvas = tk.Canvas(
            self,
            width=self._size,
            height=self._size,
            bg=_parent_bg(self),
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True)
        self._render()

    # ------------------------------------------------------------ 读写
    def get(self) -> float:
        """当前进度（0~1）。"""
        return self._value

    def set(self, value: float) -> None:
        """写入进度；会先夹到 0~1 再重画。"""
        self._value = max(0.0, min(1.0, float(value)))
        self._render()

    # ------------------------------------------------------------ 绘制
    def _render(self) -> None:
        """重画整块：轨道环、进度弧、刻度、中间文字。"""
        canvas = self._canvas
        canvas.delete("all")
        size = self._size
        half = size / 2
        tick_len = 6 if self._ticks else 0
        # 有刻度时把圆环整体往里收，给外圈刻度腾位置
        offset = 2 + tick_len + (3 if self._ticks else 0)
        radius = half - offset - self._thickness / 2
        box = (half - radius, half - radius, half + radius, half + radius)

        canvas.create_oval(
            *box, outline=self._track_color, width=self._thickness
        )
        if self._value > 0:
            canvas.create_arc(
                *box,
                start=90,
                extent=-359.99 * self._value,
                style="arc",
                outline=self._color,
                width=self._thickness,
            )

        if self._ticks:
            outer = half - 2
            inner = half - 2 - tick_len
            for index in range(self._ticks):
                angle = math.radians(90 - 360 * index / self._ticks)
                cos = math.cos(angle)
                sin = math.sin(angle)
                done = index / self._ticks <= self._value
                canvas.create_line(
                    half + cos * inner,
                    half - sin * inner,
                    half + cos * outer,
                    half - sin * outer,
                    fill=self._color if done else self._track_color,
                    width=2,
                )

        if self._show_text:
            canvas.create_text(
                half,
                half,
                text=f"{round(self._value * 100)}%",
                fill=color_of(T.COLOR_TEXT),
                font=(T.FONT_NAME, max(11, size // 5)),
            )
