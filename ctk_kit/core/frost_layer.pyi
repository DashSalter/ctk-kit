import tkinter as tk
from typing import Optional

__all__ = ["FrostLayer"]

class FrostLayer:
    master: tk.Misc
    color: str
    alpha: int
    glass: bool
    spread: int
    def __init__(
        self,
        master: tk.Misc,
        *,
        color: str = "#FFFFFF",
        alpha: int = 0x38,
        glass: bool = False,
        spread: int = 0,
    ) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def show(self) -> None: ...
    def hide(self) -> None: ...
    def configure(
        self,
        *,
        color: Optional[str] = None,
        alpha: Optional[int] = None,
        glass: Optional[bool] = None,
        spread: Optional[int] = None,
    ) -> None: ...
    def apply_glass(self) -> None: ...
    def sync(self) -> None: ...
