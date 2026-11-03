"""徽标与标签：只读的状态块，用来标分类、计数或状态。

用法::

    from ctk_kit import Badge, Tag

    Badge(card, "已同步", color="success")          # 淡绿底、绿字
    Badge(card, "3", color="danger", variant="solid")  # 红底白字计数
    Badge(card, dot=True, color="warning")           # 一个状态点
    Tag(card, "草稿", variant="outline")             # 描边标签

``Tag`` 就是 ``Badge`` 的别名，两个名字导出的都是同一个类。

颜色跟着当前外观走：``soft`` 用主色和卡片底混出来的淡底，``solid`` 用
主色实底，``outline`` 只描边。文字一般是单行，太长会撑宽，不会自动换行。

圆角背景和描边用 Pillow 以 4 倍尺寸画好再缩回来，边缘没有 canvas 圆角的
锯齿；文字仍然交给 ``CTkLabel`` 渲染，保持系统字体的清晰度。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Optional, Union

import customtkinter as ctk
from PIL import Image, ImageDraw

from . import tokens as T
from .fonts import get_font, measure_text
from .paint import cached

__all__ = ["Badge", "Tag"]

ColorSpec = Union[str, T.ColorPair]

#: 背景图的超采样倍数：4 倍画、缩回逻辑尺寸，圆角边缘才平滑。
_SCALE = 4

#: 语义名到颜色令牌。
_COLOR_TOKENS = {
    "accent": T.COLOR_ACCENT,
    "primary": T.COLOR_ACCENT,
    "success": T.COLOR_SUCCESS,
    "warning": T.COLOR_WARNING,
    "danger": T.COLOR_DANGER,
    "error": T.COLOR_DANGER,
    "info": T.COLOR_ACCENT,
    "neutral": T.COLOR_MUTED,
}


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    """``#rrggbb`` 转 ``(r, g, b)``。"""
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _mix(fore: str, back: str, ratio: float) -> str:
    """按 ``ratio`` 把 ``fore`` 混进 ``back``，返回 ``#rrggbb``。"""
    fr, fg, fb = _hex_to_rgb(fore)
    br, bg, bb = _hex_to_rgb(back)
    r = round(fr * ratio + br * (1 - ratio))
    g = round(fg * ratio + bg * (1 - ratio))
    b = round(fb * ratio + bb * (1 - ratio))
    return f"#{r:02x}{g:02x}{b:02x}"


def _pair_mix(color: T.ColorPair, base: T.ColorPair, ratio: float) -> T.ColorPair:
    """深浅两套颜色分别混合，得到可以直接交给 CTk 的色对。"""
    return (_mix(color[0], base[0], ratio), _mix(color[1], base[1], ratio))


def _is_hex(value: str) -> bool:
    """是不是 ``#rrggbb``；自定义颜色名不能参与混合。"""
    return len(value) == 7 and value.startswith("#")


def _resolve_color(color: ColorSpec) -> T.ColorPair:
    """语义名 / 单色 / 色对，统一成 ``(light, dark)``。"""
    if isinstance(color, tuple):
        return color
    token = _COLOR_TOKENS.get(color)
    if token is not None:
        return token
    return (color, color)


class Badge(ctk.CTkFrame):
    """只读徽标：状态、分类或计数。

    参数:
        master: 父容器。
        text: 显示文字；``dot=True`` 时忽略。
        color: 语义名（``"accent"`` / ``"success"`` / ``"warning"`` /
            ``"danger"`` / ``"info"`` / ``"neutral"``）、单个颜色，
            或 ``(浅色, 深色)`` 色对。
        variant: ``"soft"``（淡底，默认）/ ``"solid"``（实底）/
            ``"outline"``（描边）。
        size: ``"sm"``（20 高、小一号字）或 ``"md"``（24 高，默认）。
        dot: 只画一个圆点，不显示文字。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        set_text(text): 换文字；``dot=True`` 时无效果。
        configure(text=...): 同 ``set_text``。
    """

    def __init__(
        self,
        master: tk.Misc,
        text: str = "",
        *,
        color: ColorSpec = "accent",
        variant: str = "soft",
        size: str = "md",
        dot: bool = False,
        **kwargs: Any,
    ) -> None:
        """建一个徽标；``text`` 为空且 ``dot=False`` 时显示一个空块。"""
        height = 20 if size == "sm" else 24
        padding = 7 if size == "sm" else 9
        font = get_font(T.FONT_TINY if size == "sm" else T.FONT_SMALL)
        palette = _resolve_color(color)

        self._dot = dot
        self._variant = variant
        self._color = color
        self._palette = palette
        self._height = height
        self._padding = padding
        self._font = font
        self._text = "" if dot else text

        # 圆点是一个正方形，文字标签按文字宽度加左右内边距
        width = height if dot else max(height, measure_text(text, font) + padding * 2)
        self._width = width

        # 背景全部画在图片里，外层 frame 只当定位容器
        kwargs.pop("fg_color", None)
        kwargs.setdefault("width", width)
        kwargs.setdefault("height", height)
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label = ctk.CTkLabel(
            self,
            text=self._text,
            image=self._image(width, height),
            compound="center",
            fg_color="transparent",
            text_color=self._text_color(),
            font=font,
            width=width,
            height=height,
        )
        self._label.place(x=0, y=0, relwidth=1, relheight=1)

    # --- 对外 ---
    def set_text(self, text: str) -> None:
        """换文字；圆点徽标没有文字，调用会被忽略。"""
        if self._dot:
            return
        self._text = text
        width = max(self._height, measure_text(text, self._font) + self._padding * 2)
        self._width = width
        self.configure(width=width)
        self._label.configure(
            text=text,
            width=width,
            image=self._image(width, self._height),
        )

    def configure(self, **kwargs: Any) -> None:
        """``text=`` 转发给内部文字，其余交给 ``CTkFrame``。"""
        if "text" in kwargs:
            self.set_text(kwargs.pop("text"))
        return super().configure(**kwargs)

    # --- 内部 ---
    def _text_color(self) -> Union[str, T.ColorPair]:
        """文字颜色：实底用白字（警告色用深字），其余用主色。"""
        if self._dot:
            return self._palette
        if self._variant == "solid":
            return "#1f1300" if self._color == "warning" else "#ffffff"
        return self._palette

    def _fill(self, mode: int) -> Optional[str]:
        """按外观和形态取底色；``outline`` 返回 ``None``（只描边）。"""
        if self._dot or self._variant == "solid":
            return self._palette[mode]
        if self._variant == "outline":
            return None
        if all(_is_hex(part) for part in self._palette):
            return _mix(self._palette[mode], T.COLOR_CARD[mode], 0.14)
        return T.COLOR_SOFT[mode]

    def _render(self, width: int, height: int, mode: int) -> Image.Image:
        """画一张 ``mode`` 外观的胶囊 / 圆点，尺寸是逻辑尺寸的 4 倍。"""
        outline = None
        if self._variant == "outline" and not self._dot:
            outline = self._palette[mode]
        return _badge_image(width, height, self._fill(mode), outline)

    def _image(self, width: int, height: int) -> ctk.CTkImage:
        """深浅两套背景图，交给 ``CTkImage`` 按 DPI 缩放。"""
        return ctk.CTkImage(
            light_image=self._render(width, height, 0),
            dark_image=self._render(width, height, 1),
            size=(width, height),
        )


@cached
def _badge_image(
    width: int, height: int, fill: Optional[str], outline: Optional[str]
) -> Image.Image:
    """画一张胶囊 / 圆点；``fill`` 为空表示只描边，``outline`` 为空表示不描边。"""
    pixel_w = width * _SCALE
    pixel_h = height * _SCALE
    image = Image.new("RGBA", (pixel_w, pixel_h), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    box = (0, 0, pixel_w - 1, pixel_h - 1)
    radius = pixel_h // 2
    if fill is not None:
        pen.rounded_rectangle(box, radius=radius, fill=fill)
    if outline is not None:
        pen.rounded_rectangle(box, radius=radius, outline=outline, width=_SCALE)
    return image


#: ``Tag`` 与 ``Badge`` 是同一个类，只是语义上更适合分类标签。
Tag = Badge
