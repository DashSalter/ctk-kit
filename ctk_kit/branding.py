"""品牌资源：内置 logo 的加载、窗口图标的设置。

logo 放在 :data:`LOGO_DIR` 里，一共几份：

- ``logo.png``：1024 的正图，透明背景
- ``logo-16.png`` … ``logo-256.png``：按尺寸预渲染的小图，避免运行时缩放开销
- ``logo.ico``：多尺寸 Windows 图标，给窗口标题栏和任务栏用

用 :func:`set_window_icon` 给窗口挂图标；:func:`load_logo` 拿一张
``PhotoImage`` 放到画面上（例如空状态的占位）。
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Optional

from . import tokens as T
from .fonts import get_font
from .theme import color_of

__all__ = [
    "LOGO_DIR",
    "LOGO_PATH",
    "ICON_PATH",
    "DIM_MAX",
    "dim_image",
    "dim_ratio",
    "get_dim_ratio",
    "load_logo",
    "logo_path",
    "set_dim_ratio",
    "set_window_icon",
]

#: logo 资源目录。
LOGO_DIR = Path(__file__).resolve().parent / "logo"
#: 1024 的主图。
LOGO_PATH = LOGO_DIR / "logo.png"
#: 多尺寸 Windows 图标。
ICON_PATH = LOGO_DIR / "logo.ico"

#: 已经读过的 ``PhotoImage``：tk 的图片对象没有别的引用就会被回收，变成一片空白。
_PHOTO_CACHE: dict = {}

#: 背景透明度为 0 时图片最多减多少亮度（0–1）。
DIM_MAX = 0.25
#: 当前生效的压暗比例，由 App 按「背景透明度」更新。
_DIM = 0.20


def dim_ratio(alpha: int = 255, max_dim: float = DIM_MAX) -> float:
    """把「背景透明度」（0–255）换算成压暗比例。

    255（最实）→ 0，0（全透）→ `max_dim`，中间线性。

    参数:
        alpha: 背景透明度，0–255；255 表示完全实色、不压暗。
        max_dim: 透明度为 0 时的压暗上限，默认 0.5（50%）。
    """
    value = max(0, min(255, int(alpha)))
    return max(0.0, min(1.0, float(max_dim) * (1.0 - value / 255.0)))


def set_dim_ratio(value: float) -> bool:
    """设置全局压暗比例；值变了返回 `True`，调用方据此决定是否重画。"""
    global _DIM
    value = max(0.0, min(1.0, float(value)))
    if abs(value - _DIM) < 1e-4:
        return False
    _DIM = value
    return True


def get_dim_ratio() -> float:
    """当前全局压暗比例。"""
    return _DIM


def dim_image(image, dim: Optional[float] = None):
    """把图片整体压暗，只动 RGB、保留 alpha。

    玻璃模式下 DWM 会给窗口内容叠一层白（约 64/255），彩色图像看起来
    发灰。先把 RGB 按同样的量减掉，叠完才接近原色。

    参数:
        image: 任意 PIL 图，内部会转成 RGBA。
        dim: 压暗比例，0–1；默认 0.25，即每通道减 25% 的 255。
    """
    if dim is None:
        dim = _DIM
    if dim <= 0:
        return image
    from PIL import Image

    delta = int(round(255 * min(1.0, float(dim))))
    if not delta:
        return image
    red, green, blue, alpha = image.convert("RGBA").split()
    return Image.merge(
        "RGBA",
        (
            red.point(lambda value: max(0, value - delta)),
            green.point(lambda value: max(0, value - delta)),
            blue.point(lambda value: max(0, value - delta)),
            alpha,
        ),
    )


def logo_path(size: int = 0) -> Path:
    """内置 logo 的路径。

    参数:
        size: 想要的小图边长；有预渲染版本就用它，没有就退回主图。
    """
    if size:
        small = LOGO_DIR / f"logo-{int(size)}.png"
        if small.exists():
            return small
    return LOGO_PATH


def load_logo(size: int = 96, *, fallback: Optional["Path"] = None):
    """读一张 logo，返回可以直接给 canvas / label 用的 ``PhotoImage``。

    参数:
        size: 边长（逻辑像素）；返回的图片就是这么大。
        fallback: 内置 logo 读不到时改用这张图（例如调用方自己的图）。

    返回:
        ``ImageTk.PhotoImage``；同一尺寸会复用同一个对象。
    """
    key = (int(size), str(fallback) if fallback else "")
    cached = _PHOTO_CACHE.get(key)
    if cached is not None:
        return cached

    from PIL import Image, ImageTk

    path = logo_path(size)
    if not path.exists():
        if fallback is None:
            raise FileNotFoundError(f"找不到内置 logo：{path}")
        path = Path(fallback)

    image = Image.open(path).convert("RGBA")
    if image.size != (size, size):
        image = image.resize((size, size), Image.LANCZOS)
    photo = ImageTk.PhotoImage(image)
    _PHOTO_CACHE[key] = photo
    return photo


def set_window_icon(window: tk.Misc, *, size: int = 64, path: Optional[str] = None) -> None:
    """给窗口挂图标：标题栏左上角和任务栏都会用上。

    参数:
        window: 任意控件；会作用到它所在的顶层窗口。
        size: ``iconphoto`` 用的边长。
        path: 自定义 ``.ico``；不传就用内置的。
    """
    top = window.winfo_toplevel()
    icon = Path(path) if path else ICON_PATH

    if icon.suffix.lower() == ".ico" and icon.exists():
        try:
            # default= 让之后新建的 Toplevel 也用同一张，不用每个窗口都设
            top.iconbitmap(default=str(icon))
        except tk.TclError:
            pass

    try:
        photo = load_logo(size)
    except (FileNotFoundError, OSError):
        return
    try:
        top.iconphoto(True, photo)
    except tk.TclError:
        return
    # 顶层窗口持有引用，避免被垃圾回收
    top._ctk_kit_icon = photo


def empty_state(window: tk.Misc, canvas: tk.Canvas, width: float, height: float, text: str = "") -> None:
    """在空白区域画一个居中的 logo（可选下面带一行提示文字）。

    参数:
        window: 用来定位资源目录的控件。
        canvas: 要画的 canvas。
        width / height: 画布当前尺寸。
        text: 图下方的提示文字；空字符串就只画图。
    """
    ctk_font = get_font(T.FONT_SMALL)
    faint = color_of(T.COLOR_FAINT)
    size = int(min(width, height) * 0.22)
    size = max(32, min(96, size))
    try:
        photo = load_logo(size)
    except (FileNotFoundError, OSError):
        if text:
            canvas.create_text(
                width / 2,
                height / 2,
                text=text,
                font=ctk_font,
                fill=faint,
            )
        return

    offset = 12 if text else 0
    canvas.create_image(width / 2, height / 2 - offset, image=photo)
    # canvas 的 create_image 会持有它，但保持一份显式引用更稳妥
    holder = getattr(window, "_ctk_kit_empty_photo", None)
    if holder is not photo:
        window._ctk_kit_empty_photo = photo
    if text:
        canvas.create_text(
            width / 2,
            height / 2 + size / 2 + 14,
            text=text,
            font=ctk_font,
            fill=faint,
        )
