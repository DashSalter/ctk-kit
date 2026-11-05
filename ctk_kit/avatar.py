"""头像：圆形图片或首字，右下角可以带一个在线状态点。

用法::

    from ctk_kit import Avatar

    Avatar(card, text="张三", size=48, status="online")
    Avatar(card, image=ctk.CTkImage(..., size=(40, 40)), size=40)

没有图片时取文字的第一个字（英文自动转大写）；颜色可以传语义名
（``accent`` / ``success`` / ``warning`` / ``danger`` / ``neutral``）或十六进制色。

圆形、图片裁切和状态点都在同一张 Pillow 图上合成（4 倍尺寸绘制再缩回），
和开关、徽标一样，边缘没有 canvas 圆角的锯齿。状态点直接画进头像图里，
不另叠控件，免得把圆形右下角盖出一个方角。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional, Tuple

import customtkinter as ctk

from . import tokens as T
from .branding import dim_image
from .fonts import get_font
from .paint import cached
from .theme import color_of

try:  # Pillow 是可选依赖
    from PIL import Image, ImageDraw

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

__all__ = ["Avatar"]

#: 语义色名字到令牌的映射。
_COLORS = {
    "accent": T.COLOR_ACCENT,
    "success": T.COLOR_SUCCESS,
    "warning": T.COLOR_WARNING,
    "danger": T.COLOR_DANGER,
    "neutral": T.COLOR_MUTED,
}

#: 状态点颜色。
_STATUS = {
    "online": T.COLOR_SUCCESS,
    "away": T.COLOR_WARNING,
    "busy": T.COLOR_DANGER,
    "offline": T.COLOR_FAINT,
}

#: 画图时的超采样倍数。
_SCALE = 4


def _resolve(color: Any) -> Any:
    """把语义名换成令牌；十六进制或其他值原样返回。"""
    if isinstance(color, str) and color in _COLORS:
        return _COLORS[color]
    return color


def _pair(color: Any) -> Tuple[str, str]:
    """把单色或 ``(浅, 深)`` 色对统一成两色。"""
    if isinstance(color, (tuple, list)) and len(color) == 2:
        return str(color[0]), str(color[1])
    return str(color), str(color)


@cached
def _circle(size: int, fill: str) -> "Image.Image":
    """画一个实心圆，尺寸是逻辑尺寸的 4 倍。"""
    total = size * _SCALE
    image = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    ImageDraw.Draw(image).ellipse((0, 0, total - 1, total - 1), fill=fill)
    return image


@cached
def _circle_mask(size: int) -> "Image.Image":
    """圆形遮罩，用来把图片裁成头像。"""
    total = size * _SCALE
    mask = Image.new("L", (total, total), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, total - 1, total - 1), fill=255)
    return mask


def _with_status(
    base: "Image.Image",
    size: int,
    dot: int,
    fill: str,
    border: str,
) -> "Image.Image":
    """在头像图右下角画状态点；``border`` 取卡片底色，边缘更干净。"""
    result = base.copy()
    pen = ImageDraw.Draw(result)
    radius = dot * _SCALE / 2.0
    center_x = size * _SCALE - radius - 2
    center_y = size * _SCALE - radius - 2
    pen.ellipse(
        (
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
        ),
        fill=fill,
        outline=border,
        width=max(1, int(dot * 0.14)) * _SCALE,
    )
    return result


class Avatar(ctk.CTkFrame):
    """圆形头像。

    参数:
        master: 父容器。
        text: 名字；没有图片时取第一个字。
        image: ``CTkImage``，给了就显示图片、忽略文字。
        size: 直径（逻辑像素），默认 40。
        dim: 图片预先压暗的比例，默认 0.25，抵消玻璃合成那层白；0 = 不处理。
        color: 底色，语义名或十六进制，默认 ``accent``。
        status: ``online`` / ``away`` / ``busy`` / ``offline``；不传就不画状态点。
        command: 点头像时的回调；传了会把光标改成手形。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        set_text(text): 换文字。
        set_image(image): 换图片；传 ``None`` 退回文字。
        set_status(status): 换状态点。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        text: str = "",
        image: Optional[ctk.CTkImage] = None,
        size: int = 40,
        dim: Optional[float] = None,
        color: Any = "accent",
        status: Optional[str] = None,
        command: Optional[Callable[[], None]] = None,
        **kwargs: Any,
    ) -> None:
        """建头像；``size`` 同时决定字号和圆角。"""
        super().__init__(
            master,
            fg_color="transparent",
            width=size,
            height=size,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._size = size
        self._dim = None if dim is None else float(dim)
        self._image = image
        self._status = status
        self._text = text
        self._color = color
        self._dot_size = max(8, size // 3)

        self._label = ctk.CTkLabel(
            self,
            text="",
            width=size,
            height=size,
            corner_radius=0 if _HAS_PIL else size // 2,
            fg_color="transparent" if _HAS_PIL else color_of(_resolve(color)),
            text_color=T.COLOR_ACCENT_TEXT,
            font=get_font((T.FONT_NAME, max(10, size // 3), "bold")),
        )
        self._label.pack(fill="both", expand=True)

        # 没有 Pillow 时退回旧做法：另叠一个圆角 label 当状态点。
        self._dot = None
        if not _HAS_PIL:
            self._dot = ctk.CTkLabel(
                self,
                text="",
                width=self._dot_size,
                height=self._dot_size,
                corner_radius=T.RADIUS_PILL,
                fg_color=T.COLOR_SUCCESS,
            )
        self._apply_text()
        self._apply_status()

        if command is not None:
            self._label.configure(cursor="hand2")
            self._label.bind("<Button-1>", lambda _event: command())

    # --- 对外 ---
    def set_text(self, text: str) -> None:
        """换文字；有图片时只更新备用文字。"""
        self._text = text
        self._apply_text()

    def set_image(self, image: Optional[ctk.CTkImage]) -> None:
        """换图片；``None`` 退回显示首字。"""
        self._image = image
        self._apply_text()

    def _refresh_dim(self) -> None:
        """背景透明度变了：按新比例重画图片。"""
        if self._image is not None and _HAS_PIL:
            self._apply_text()

    def set_status(self, status: Optional[str]) -> None:
        """换状态点；``None`` 收起来。"""
        self._status = status
        self._apply_status()

    # --- 内部 ---
    def _apply_text(self) -> None:
        """按有没有图片决定显示图片还是首字。"""
        if not _HAS_PIL:
            self._label.configure(
                image="",
                text="" if self._image is not None else self._initial(self._text),
                fg_color=color_of(_resolve(self._color)),
            )
            return

        light, dark = self._base_images()
        if self._status in _STATUS:
            color = _pair(_STATUS[self._status])
            border = _pair(T.COLOR_CARD)
            light = _with_status(
                light, self._size, self._dot_size, color[0], border[0]
            )
            dark = _with_status(
                dark, self._size, self._dot_size, color[1], border[1]
            )

        self._label.configure(
            image=ctk.CTkImage(
                light_image=light,
                dark_image=dark,
                size=(self._size, self._size),
            ),
            text=self._initial(self._text) if self._image is None else "",
            compound="center",
            fg_color="transparent",
        )

    def _apply_status(self) -> None:
        """状态点：Pillow 路径已画进头像图，只有无 Pillow 时才叠控件。"""
        if _HAS_PIL:
            self._apply_text()
            return

        if not (self._status and self._status in _STATUS):
            self._dot.place_forget()
            return
        self._dot.configure(fg_color=color_of(_STATUS[self._status]))
        self._dot.place(relx=1.0, rely=1.0, anchor="se", x=2, y=2)

    def _base_images(self) -> Tuple["Image.Image", "Image.Image"]:
        """头像底图：图片裁圆，或纯色圆。"""
        if self._image is not None:
            return self._round_images(self._image)
        light, dark = _pair(_resolve(self._color))
        return _circle(self._size, light), _circle(self._size, dark)

    def _round_images(
        self, image: ctk.CTkImage
    ) -> Tuple["Image.Image", "Image.Image"]:
        """把用户给的 ``CTkImage`` 裁成圆形。"""
        size = self._size
        mask = _circle_mask(size)

        def cut(source):
            if source is None:
                return None
            resized = source.convert("RGBA").resize(
                (size * _SCALE, size * _SCALE), Image.LANCZOS
            )
            resized = dim_image(resized, self._dim)
            resized.putalpha(mask)
            return resized

        light = cut(getattr(image, "_light_image", None))
        if light is None:
            # 没有底层图时退回纯色，避免整张头像消失。
            light, dark = _pair(_resolve(self._color))
            return _circle(size, light), _circle(size, dark)
        dark = cut(getattr(image, "_dark_image", None)) or light
        return light, dark

    @staticmethod
    def _initial(text: str) -> str:
        """取第一个字；英文转大写。"""
        stripped = text.strip()
        if not stripped:
            return "?"
        first = stripped[0]
        return first.upper() if first.isascii() else first
