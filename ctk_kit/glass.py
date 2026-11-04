"""毛玻璃背景：把浮层背后的屏幕内容截下来做高斯模糊。

Windows 的 DWM 毛玻璃（Mica / Acrylic）要求窗口带标题栏，库里这些浮层都是
``overrideredirect`` 无边框窗口，套不上。这里换一条纯 Python 的路子：
截一块屏幕，模糊后叠一层卡片色，塞进卡片里当背景。

浮层显示之后可以定时重截（``_GLASS_REFRESH_MS``），背后滚动或动画时背景
能跟着变。截图前用 :func:`excluding_from_capture` 把浮层自己从画面里排除，
不然拍到的就是它自己。
"""

from __future__ import annotations

import contextlib
import ctypes
import sys
from typing import Any, Iterator, Optional

from PIL import Image, ImageChops, ImageEnhance, ImageFilter

from . import tokens as T
from .paint import blend_hex
from .theme import color_of

__all__ = ["backdrop_image", "excluding_from_capture", "gradient_image"]

_WDA_NONE = 0x00000000
_WDA_EXCLUDEFROMCAPTURE = 0x00000011

# 噪声图按尺寸缓存：每次刷新都生成新噪声的话，颗粒位置会跟着变，
# 看起来就是满屏雪花在闪。同一块尺寸复用同一张图，刷新时才不会动。
_grain_cache: dict[tuple[int, int, float], Image.Image] = {}


def _grain(size: tuple[int, int], sigma: float) -> Image.Image:
    key = (size[0], size[1], round(sigma, 2))
    grain = _grain_cache.get(key)
    if grain is None:
        grain = Image.effect_noise(size, sigma).convert("RGB")
        _grain_cache[key] = grain
    return grain


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


# 8x8 Bayer 矩阵：有序抖动的阈值图案。用它而不是随机噪声，是因为图案规则，
# 看上去是细密网点而不是满屏雪花，静态图也不会有「沙沙」感。
_BAYER8 = (
    (0, 32, 8, 40, 2, 34, 10, 42),
    (48, 16, 56, 24, 50, 18, 58, 26),
    (12, 44, 4, 36, 14, 46, 6, 38),
    (60, 28, 52, 20, 62, 30, 54, 22),
    (3, 35, 11, 43, 1, 33, 9, 41),
    (51, 19, 59, 27, 49, 17, 57, 25),
    (15, 47, 7, 39, 13, 45, 5, 37),
    (63, 31, 55, 23, 61, 29, 53, 21),
)
_bayer_cache: dict[tuple[int, int], Image.Image] = {}


def _bayer(size: tuple[int, int], spread: float = 1.5) -> Image.Image:
    """平铺一张 8x8 的有序抖动图案（均值 128，±spread）。"""
    key = (size[0], size[1])
    tile = _bayer_cache.get(key)
    if tile is not None:
        return tile
    unit = Image.new("L", (8, 8))
    for y in range(8):
        for x in range(8):
            value = (_BAYER8[y][x] / 64.0 - 0.5) * 2
            unit.putpixel((x, y), 128 + int(round(value * spread)))
    tile = Image.new("L", (max(1, size[0]), max(1, size[1])))
    for y in range(0, tile.height, 8):
        for x in range(0, tile.width, 8):
            tile.paste(unit, (x, y))
    tile = tile.convert("RGB")
    _bayer_cache[key] = tile
    return tile


def gradient_image(
    width: int,
    height: int,
    *,
    top: Optional[str] = None,
    bottom: Optional[str] = None,
) -> Image.Image:
    """生成一张固定的竖向渐变，当作不依赖屏幕内容的卡片背景。

    颜色默认取卡片色：顶部提亮一点、底部压暗一点，模仿光从上方打下来。
    这个图不截屏、不随窗口移动变化，每次显示都一模一样。
    """
    width = max(1, int(width))
    height = max(1, int(height))
    base = color_of(T.COLOR_CARD)
    top = top or base
    bottom = bottom or blend_hex(base, "#000000", 0.18)
    # 按 8 倍纵向分辨率做 float 插值，再 BILINEAR 降采样：色阶边界会被
    # 摊宽到十几行，不会一步一台阶。
    steps = height * 8
    top_rgb = _rgb(top)
    bottom_rgb = _rgb(bottom)
    column = Image.new("RGB", (1, steps))
    span = max(1, steps - 1)
    for y in range(steps):
        t = y / span
        column.putpixel(
            (0, y),
            tuple(int(round(a + (b - a) * t)) for a, b in zip(top_rgb, bottom_rgb)),
        )
    image = column.resize((width, height), Image.BILINEAR)
    # 8bit 量化后剩下的色阶仍然会有台阶，用有序抖动把边界打散。
    image = ImageChops.add(image, _bayer(image.size), scale=1.0, offset=-128)
    return image


@contextlib.contextmanager
def excluding_from_capture(window: Any) -> Iterator[None]:
    """临时把 ``window`` 从屏幕截图里排除，退出时恢复。

    ``WDA_EXCLUDEFROMCAPTURE``（Win10 2004+）期间窗口在截图/录屏中都不可见，
    用来「刷新背景图时别把浮层自己拍进去」。旧系统上 ``SetWindowDisplayAffinity``
    返回 0，这里直接跳过——重截出来的图会带窗口自己的残影，但不会崩。
    """
    hwnd = 0
    if sys.platform == "win32":
        with contextlib.suppress(Exception):
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()
            if not ctypes.windll.user32.SetWindowDisplayAffinity(
                hwnd, _WDA_EXCLUDEFROMCAPTURE
            ):
                hwnd = 0
            else:
                # 等 DWM 把窗口从合成画面里真正去掉再截图，否则可能拍到还没
                # 重绘的黑色区域（卡片背景里会出现一块块暗矩形）。
                ctypes.windll.dwmapi.DwmFlush()
    try:
        yield
    finally:
        if hwnd:
            with contextlib.suppress(Exception):
                ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, _WDA_NONE)


def backdrop_image(
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    scaling: float = 1.0,
    blur: int = 20,
    radius: int = 8,
    blur_scale: float = 0.5,
    upscale: float = 2.0,
) -> Optional[Image.Image]:
    """截 ``(x, y, width, height)`` 这块屏幕，做高斯模糊后返回。

    返回的是**不透明**的 RGB 图：Tk 的 ``PhotoImage`` 不合成 alpha 通道，
    带透明像素的图在控件上会显示成黑色，四个角就会出现黑边。圆角交给
    窗口本身的 ``SetWindowRgn`` 裁剪，图片保持直角即可。

    参数:
        x / y / width / height: 浮层在屏幕上的位置和尺寸，**物理像素**。
        scaling: 窗口缩放（125% 传 1.25），用来换算模糊半径。
        blur: 高斯模糊半径（逻辑像素），越大越糊。
        radius: 圆角半径（逻辑像素），保留参数但不再用于裁图。
        blur_scale: 模糊范围系数
            想让边缘更散就调大，想更锐就调小。
        upscale: 模糊前的升采样倍数（默认 2 倍）。放大后模糊再缩回，边缘
            过渡比直接模糊更细腻；1.0 表示关闭。

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

    original_size = shot.size
    radius_px = max(1, int(blur * scaling))
    if upscale > 1.0:
        shot = shot.resize(
            (int(original_size[0] * upscale), int(original_size[1] * upscale)),
            Image.LANCZOS,
        )
        radius_px = max(1, int(radius_px * upscale * blur_scale))

        shot = shot.filter(ImageFilter.GaussianBlur(radius=radius_px))
        shot = shot.resize(original_size, Image.LANCZOS)
    else:
        shot = shot.filter(ImageFilter.GaussianBlur(radius=radius_px))
    return shot
