from typing import Any, Iterator, Optional

from PIL import Image

__all__ = ["backdrop_image", "excluding_from_capture", "gradient_image"]

def gradient_image(
    width: int,
    height: int,
    *,
    top: Optional[str] = None,
    bottom: Optional[str] = None,
) -> Image.Image: ...
def excluding_from_capture(window: Any) -> Iterator[None]: ...
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
) -> Optional[Image.Image]: ...
