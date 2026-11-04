"""毛玻璃背景：把浮层背后的屏幕内容截下来做高斯模糊。

Windows 的 DWM 毛玻璃（Mica / Acrylic）要求窗口带标题栏，库里这些浮层都是
``overrideredirect`` 无边框窗口，套不上。这里换一条纯 Python 的路子：
浮层显示**之前**截一块屏幕，模糊后叠一层卡片色，塞进卡片里当背景。

代价是这张图是「快照」，背后内容变了要重截；好在浮层一般弹出来就静止了。
"""

from __future__ import annotations

from typing import Optional

from PIL import Image, ImageFilter

from . import tokens as T
from .theme import color_of

__all__ = ["backdrop_image"]


def backdrop_image(
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    scaling: float = 1.0,
    blur: int = 14,
    tint: float = 0.72,
    radius: int = 8,
) -> Optional[Image.Image]:
    """截 ``(x, y, width, height)`` 这块屏幕，模糊后叠一层卡片色。

    返回的是**不透明**的 RGB 图：Tk 的 ``PhotoImage`` 不合成 alpha 通道，
    带透明像素的图在控件上会显示成黑色，四个角就会出现黑边。圆角交给
    窗口本身的 ``SetWindowRgn`` 裁剪，图片保持直角即可。

    参数:
        x / y / width / height: 浮层在屏幕上的位置和尺寸，**物理像素**。
        scaling: 窗口缩放（125% 传 1.25），用来换算模糊半径。
        blur: 高斯模糊半径（逻辑像素），越大越糊。
        tint: 卡片色覆盖比例，0 是全透、1 是全不透明；0.7 左右文字最好读。
        radius: 圆角半径（逻辑像素），保留参数但不再用于裁图。

    返回:
        RGB 图（物理像素），截图失败时返回 ``None``。
    """
    width = max(1, int(width))
    height = max(1, int(height))
    try:
        from PIL import ImageGrab

        shot = ImageGrab.grab(
            bbox=(int(x), int(y), int(x) + width, int(y) + height),
            all_screens=True,
        ).convert("RGB")
        if shot.size != (width, height):
            shot = shot.resize((width, height), Image.LANCZOS)
    except Exception:  # noqa: BLE001 - 远程桌面、权限受限时截不到
        return None

    radius_px = int(round(blur * scaling))
    if radius_px > 0:
        shot = shot.filter(ImageFilter.GaussianBlur(radius=radius_px))
    card = Image.new("RGB", shot.size, color_of(T.COLOR_CARD))
    shot = Image.blend(shot, card, max(0.0, min(1.0, tint)))
    return shot
