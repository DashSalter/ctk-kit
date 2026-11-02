"""图片缓存：同一个文件只解码一次，重复设置时复用已经转换好的 PIL 图片。

窗口里同一张图常被反复设置（切页重建、重新打开预览），每回都
``Image.open(...).convert(...)`` 会重复读盘和转换。这里按「绝对路径 + 修改
时间」缓存解码结果；文件改过，修改时间变了，缓存自然失效。
"""

from __future__ import annotations

import os
from typing import Dict, Tuple

try:
    from PIL import Image
except ImportError:  # Pillow 是 image 可选依赖，用到时再报错
    Image = None  # type: ignore[assignment]

_CACHE: Dict[Tuple[str, float], "Image.Image"] = {}


def open_image(path) -> "Image.Image":
    """读取图片文件，按路径与修改时间缓存解码后的 RGBA 图片。

    参数:
        path: 图片路径（``str`` 或 ``pathlib.Path``）。

    返回:
        ``PIL.Image.Image``；同一文件重复调用返回同一实例，调用方不要原地
        修改它（需要改就先 ``copy()``）。
    """
    if Image is None:
        raise ImportError(
            '图片缓存需要 Pillow，先执行 pip install "ctk-kit[image]"'
        )
    absolute = os.path.abspath(os.fspath(path))
    mtime = os.path.getmtime(absolute)
    key = (absolute, mtime)
    image = _CACHE.get(key)
    if image is None:
        with Image.open(absolute) as opened:
            # 调色板 / 灰度 / CMYK 统一转成 RGBA，透明背景交给调用方底色
            image = (
                opened.copy()
                if opened.mode in ("RGB", "RGBA")
                else opened.convert("RGBA")
            )
        _CACHE[key] = image
    return image


def clear() -> None:
    """清空缓存（文件被外部改写、或测试结束要释放内存时调用）。"""
    _CACHE.clear()
