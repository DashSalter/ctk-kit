"""示例自己的窗口状态存储。

核心库（``ctk_kit``）只负责窗口本身，**不再内置任何持久化**：读什么、写到
哪、用什么格式，都由使用方决定。这个文件就是示例这边的实现——用 conf_base
的声明式写法把窗口几何、外观、颜色主题、底色存到
``~/.ctk-kit/window.json``。

接进 ``App`` 的方式是传一个对象进去，它需要提供下面这几个方法（返回值
不合法时核心会退回到默认值，抛异常也会被吞掉，不影响启动）::

    state = WindowStateStore()
    app = App(title="备份", state=state)

    state.read_geometry()   -> Optional[tuple[int, int, int, int]]  宽, 高, x, y
    state.write_geometry(width, height, x, y)
    state.read_appearance() -> str      light / dark / system
    state.write_appearance(mode)
    state.read_color_theme() -> str     主题名或文件路径，空串表示默认
    state.write_color_theme(name)
    state.read_backdrop()   -> str      none / acrylic
    state.write_backdrop(mode)

不想记就直接不传 ``state``。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from conf_base import ConfigBase, Section

__all__ = ["WindowState", "WindowStateStore", "default_config_path"]

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
    backdrop = appearance.field(default="none")  # none / acrylic（毛玻璃）


class WindowStateStore:
    """把 :class:`WindowState` 包成 ``App(state=...)`` 要的形状。"""

    def read_geometry(self) -> Optional[Tuple[int, int, int, int]]:
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

    def write_geometry(self, width: int, height: int, x: int, y: int) -> None:
        """把窗口几何写进配置文件（宽高逻辑像素，x/y 屏幕物理像素）。"""
        with WindowState.window.batch():
            WindowState.width.value = int(width)
            WindowState.height.value = int(height)
            WindowState.x.value = int(x)
            WindowState.y.value = int(y)

    def read_appearance(self) -> str:
        """读取上次选择的外观：``"light"`` / ``"dark"`` / ``"system"``。"""
        try:
            mode = str(WindowState.mode.value)
        except Exception:  # noqa: BLE001 - 配置损坏时回到系统外观
            return "system"
        return mode if mode in ("light", "dark", "system") else "system"

    def write_appearance(self, mode: str) -> None:
        """记住当前外观。"""
        WindowState.mode.value = mode

    def read_color_theme(self) -> str:
        """读取上次选择的颜色主题；空字符串表示用默认值。"""
        try:
            return str(WindowState.color.value or "")
        except Exception:  # noqa: BLE001
            return ""

    def write_color_theme(self, name: str) -> None:
        """记住当前颜色主题（内置主题名或主题文件路径）。"""
        WindowState.color.value = name or ""

    def read_backdrop(self) -> str:
        """读取上次选择的底色：``"none"``（不透明）或 ``"acrylic"``（毛玻璃）。"""
        try:
            mode = str(WindowState.backdrop.value or "").strip().lower()
        except Exception:  # noqa: BLE001 - 配置损坏时回到不透明
            return "none"
        return "acrylic" if mode in ("acrylic", "glass", "毛玻璃", "玻璃") else "none"

    def write_backdrop(self, mode: str) -> None:
        """记住当前底色模式。"""
        WindowState.backdrop.value = "acrylic" if str(mode).lower() in (
            "acrylic", "glass", "毛玻璃", "玻璃"
        ) else "none"
