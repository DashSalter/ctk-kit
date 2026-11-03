"""窗口几何的持久化：记住上次关闭时的大小和位置。

按 conf_base 的声明式写法：配置类直接继承 :class:`ConfigBase`，用
:class:`Section` + ``field()`` 声明字段，值类型由默认值推断，赋值即落盘。

    from ctk_kit import App

    app = App(title="备份")          # 自动记住位置和大小
    app.mainloop()

不想记就传 ``remember_geometry=False``。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from conf_base import ConfigBase, Section

__all__ = [
    "default_config_path",
    "read_appearance",
    "read_color_theme",
    "read_geometry",
    "write_appearance",
    "write_color_theme",
    "write_geometry",
]

_DEFAULT_WIDTH = 880
_DEFAULT_HEIGHT = 560

#: 配置文件里的段名。保持小写，旧版本写下的文件仍能读到。
_SECTION = "window"


def default_config_path() -> str:
    """默认配置文件：``~/.ctk-kit/window.json``。"""
    return str(Path.home() / ".ctk-kit" / "window.json")


class WindowState(ConfigBase):
    """窗口大小和位置。"""

    _path = default_config_path()

    window = Section(_SECTION)
    width = window.field(default=_DEFAULT_WIDTH, validator=lambda v: v > 0)
    height = window.field(default=_DEFAULT_HEIGHT, validator=lambda v: v > 0)
    x = window.field(default=-1)
    y = window.field(default=-1)

    appearance = Section("appearance")
    mode = appearance.field(default="system")   # light / dark / system
    color = appearance.field(default="")        # 颜色主题名或文件路径


def read_geometry() -> Optional[Tuple[int, int, int, int]]:
    """读取保存的 ``(宽, 高, x, y)``；没有有效记录时返回 ``None``。

    宽高是逻辑像素，x/y 是屏幕物理像素；x/y 为 -1 表示没有保存位置。
    文件损坏、字段不合法时也返回 ``None``，不让启动失败。
    """
    try:
        width = int(WindowState.width.value)
        height = int(WindowState.height.value)
        x = int(WindowState.x.value)
        y = int(WindowState.y.value)
    except Exception:  # noqa: BLE001 - 配置损坏不该阻止窗口启动
        return None
    if width <= 0 or height <= 0:
        return None
    return width, height, x, y


def write_geometry(width: int, height: int, x: int, y: int) -> None:
    """把窗口几何写进配置文件（宽高逻辑像素，x/y 屏幕物理像素）。"""
    with WindowState.window.batch():
        WindowState.width.value = int(width)
        WindowState.height.value = int(height)
        WindowState.x.value = int(x)
        WindowState.y.value = int(y)


def read_appearance() -> str:
    """读取上次选择的外观：``"light"`` / ``"dark"`` / ``"system"``。"""
    try:
        mode = str(WindowState.mode.value)
    except Exception:  # noqa: BLE001 - 配置损坏时回到系统外观
        return "system"
    return mode if mode in ("light", "dark", "system") else "system"


def write_appearance(mode: str) -> None:
    """记住当前外观。"""
    WindowState.mode.value = mode


def read_color_theme() -> str:
    """读取上次选择的颜色主题；空字符串表示用默认值。"""
    try:
        return str(WindowState.color.value or "")
    except Exception:  # noqa: BLE001
        return ""


def write_color_theme(name: str) -> None:
    """记住当前颜色主题（内置主题名或主题文件路径）。"""
    WindowState.color.value = name or ""
