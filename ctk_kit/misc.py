"""杂项控件：多种样式的进度条与圆环进度。

绘制方式和 ttkbootstrap 的 ``Meter`` 一致：先用 Pillow 在 3 倍尺寸上画，
最后缩回目标尺寸，靠重采样把边缘磨平。Tk 自己的 canvas 不做抗锯齿，
直接用 ``create_arc`` / ``create_oval`` 画出来的圆环是硬像素阶梯。

Pillow 是可选依赖：没装时退回 canvas 的直角/硬边画法，功能照常。
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

try:  # Pillow 是可选依赖
    from PIL import Image, ImageDraw, ImageTk

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

#: 超采样倍数：先画这么大再缩回去，边缘才有渐变过渡。
_SCALE = 3


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
    """进度条：连续 / 分格 / 带百分比 / 条纹 / 不确定态。

    整块是一个透明容器，左边是条本身，右边按需放百分比文字。
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
        self._height = max(6, int(height))
        self._striped = bool(striped)
        self._color = color_of(color or T.COLOR_ACTIVE)
        self._track_color = color_of(track or T.COLOR_BORDER_STRONG)
        self._photo = None
        self._label: Optional[ctk.CTkLabel] = None
        self._anim_job: Optional[str] = None
        self._anim_pos = 0.0

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", expand=True)

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

        self._canvas = tk.Canvas(
            row,
            width=max(20, width - (54 if show_text else 0)),
            height=self._height,
            bg=_parent_bg(row),
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(side="left")
        self._canvas.bind("<Configure>", lambda _e: self._render())
        self._render()

    # ------------------------------------------------------------ 读写
    def get(self) -> float:
        """当前进度（0~1）。"""
        return self._value

    def set(self, value: float) -> None:
        """写入进度；会先夹到 0~1，再重画。"""
        self._value = max(0.0, min(1.0, float(value)))
        self._render()

    # ------------------------------------------------------------ 绘制
    def _render(self) -> None:
        """重画整条；尺寸没定下来之前先跳过。"""
        canvas = self._canvas
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1:
            width = max(1, self.cget("width") or 240)
        if height <= 1:
            height = self._height
        canvas.delete("all")
        if self._label is not None:
            self._label.configure(text=f"{round(self._value * 100)}%")
        if not _HAS_PIL:
            self._draw_plain(width, height)
            return
        image = self._paint(width, height)
        self._photo = ImageTk.PhotoImage(image.resize((width, height), Image.LANCZOS))
        canvas.create_image(0, 0, image=self._photo, anchor="nw")

    def _paint(self, width: int, height: int):
        """在 3 倍尺寸上画好整条，再交给调用方缩回目标尺寸。"""
        scale = _SCALE
        w, h = width * scale, height * scale
        image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        pen = ImageDraw.Draw(image)
        radius = h // 2

        pen.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=self._track_color)

        if self._steps:
            gap = 3 * scale
            cell = (w - gap * (self._steps - 1)) / self._steps
            filled = round(self._value * self._steps)
            for index in range(min(filled, self._steps)):
                left = index * (cell + gap)
                pen.rounded_rectangle(
                    (left, 0, left + cell, h - 1), radius=radius, fill=self._color
                )
            return image

        filled_width = int(round(w * self._value))
        if filled_width <= 0:
            return image
        if not self._striped:
            pen.rounded_rectangle(
                (0, 0, filled_width - 1, h - 1), radius=radius, fill=self._color
            )
            return image

        # 条纹：先铺一层主色，再画 45° 暗色斜线，最后用圆角蒙版裁掉两头
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, filled_width - 1, h - 1), radius=radius, fill=255
        )
        pattern = Image.new("RGBA", (w, h), self._color)
        stripe = ImageDraw.Draw(pattern)
        dark = _shade(self._color, 0.82)
        step = max(6, height) * scale
        thick = max(2, height // 3) * scale
        for x in range(-h, w + h, step):
            stripe.line((x, h, x + h, 0), fill=dark, width=thick)
        image.paste(pattern, (0, 0), mask)
        return image

    def _draw_plain(self, width: int, height: int) -> None:
        """没装 Pillow 时的退路：canvas 画直角色块。"""
        canvas = self._canvas
        canvas.create_rectangle(0, 0, width, height, fill=self._track_color, outline="")
        if self._steps:
            gap = 3
            cell = (width - gap * (self._steps - 1)) / self._steps
            for index in range(min(round(self._value * self._steps), self._steps)):
                left = index * (cell + gap)
                canvas.create_rectangle(
                    left, 0, left + cell, height, fill=self._color, outline=""
                )
            return
        filled = width * self._value
        if filled <= 0:
            return
        canvas.create_rectangle(0, 0, filled, height, fill=self._color, outline="")

    # ------------------------------------------------------------ 不确定态
    def start_indeterminate(self) -> None:
        """切成不确定态：一段色块在轨道里来回滚。"""
        if self._steps or self._anim_job is not None:
            return
        self._anim_pos = -0.3
        self._animate()

    def stop_indeterminate(self) -> None:
        """退出不确定态，回到按 ``value`` 显示。"""
        if self._anim_job is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._anim_job)
            self._anim_job = None
        self._render()

    @property
    def animating(self) -> bool:
        """当前是不是在跑不确定态动画。"""
        return self._anim_job is not None

    def _animate(self) -> None:
        """一帧：把 30% 宽的色块往右推，出界后从左边重新进来。"""
        self._anim_pos += 0.02
        if self._anim_pos > 1.0:
            self._anim_pos = -0.3
        canvas = self._canvas
        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        canvas.delete("all")
        if _HAS_PIL:
            image = Image.new("RGBA", (width, height), color_of(T.COLOR_BORDER_STRONG))
            start = int(max(0.0, self._anim_pos) * width)
            end = min(width, start + int(0.3 * width))
            if end > start:
                pen = ImageDraw.Draw(image)
                pen.rounded_rectangle(
                    (start, 0, end - 1, height - 1),
                    radius=height // 2,
                    fill=self._color,
                )
            self._photo = ImageTk.PhotoImage(image)
            canvas.create_image(0, 0, image=self._photo, anchor="nw")
        else:
            self._draw_plain(width, height)
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

    和 ttkbootstrap 的 ``Meter`` 一个思路：PIL 在 3 倍尺寸上画弧，再缩回来，
    这样圆环边缘是平滑的，不会出现 canvas 那种一格一格的阶梯。
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
        self._color = color_of(color or T.COLOR_ACTIVE)
        self._track_color = color_of(track or T.COLOR_BORDER_STRONG)
        self._show_text = show_text
        self._value = max(0.0, min(1.0, float(value)))
        self._photo = None

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
        if _HAS_PIL:
            image = self._paint()
            self._photo = ImageTk.PhotoImage(
                image.resize((self._size, self._size), Image.LANCZOS)
            )
            canvas.create_image(0, 0, image=self._photo, anchor="nw")
        else:
            self._draw_plain()
        if self._show_text:
            canvas.create_text(
                self._size / 2,
                self._size / 2,
                text=f"{round(self._value * 100)}%",
                fill=color_of(T.COLOR_TEXT),
                font=(T.FONT_NAME, max(11, self._size // 5)),
            )

    def _paint(self):
        """在 3 倍尺寸上画圆环和刻度。"""
        scale = _SCALE
        size = self._size * scale
        thickness = self._thickness * scale
        # 底色不透明：透明像素在 Tk 里会和 canvas 背景拼出细微色差，看着像一块方框
        image = Image.new("RGBA", (size, size), _parent_bg(self))
        pen = ImageDraw.Draw(image)

        tick_len = 6 * scale if self._ticks else 0
        offset = (2 + (6 + 3 if self._ticks else 0)) * scale
        box = (offset, offset, size - offset - 1, size - offset - 1)

        pen.ellipse(box, outline=self._track_color, width=thickness)
        if self._value > 0:
            # PIL 的 0 度在 3 点钟方向、顺时针增大；从 -90 起步就是顶部
            pen.arc(
                box,
                start=-90,
                end=-90 + 360 * self._value,
                fill=self._color,
                width=thickness,
            )

        if self._ticks:
            half = size / 2
            outer = half - 2 * scale
            inner = outer - tick_len
            for index in range(self._ticks):
                angle = math.radians(-90 + 360 * index / self._ticks)
                cos = math.cos(angle)
                sin = math.sin(angle)
                done = index / self._ticks <= self._value
                pen.line(
                    (
                        half + cos * inner,
                        half + sin * inner,
                        half + cos * outer,
                        half + sin * outer,
                    ),
                    fill=self._color if done else self._track_color,
                    width=2 * scale,
                )
        return image

    def _draw_plain(self) -> None:
        """没装 Pillow 时的退路：canvas 画弧（边缘会有阶梯）。"""
        canvas = self._canvas
        size = self._size
        half = size / 2
        tick_len = 6 if self._ticks else 0
        offset = 2 + tick_len + (3 if self._ticks else 0)
        radius = half - offset - self._thickness / 2
        box = (half - radius, half - radius, half + radius, half + radius)
        canvas.create_oval(*box, outline=self._track_color, width=self._thickness)
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
