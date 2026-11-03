"""窗口几何的持久化：记住上次关闭时的大小和位置。

配置用 conf_base 的声明式 ``ConfigBase`` 管理，默认写在用户目录的
``~/.ctk-kit/window.json``；``App`` 构造时读取，关闭时写回。

    from ctk_kit import App

    app = App(title="备份")          # 自动记住位置和大小
    app.mainloop()

不想记就传 ``remember_geometry=False``；多个应用各记各的，传不同的
``config_path`` 即可。
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

from conf_base import ConfigBase, Section

__all__ = ["default_config_path", "window_state", "read_geometry", "write_geometry"]

# 同一个路径只建一个配置类：conf_base 的配置项是类级描述符，
# 每次新建类都会重新读一遍文件，没必要。
_STATE_CLASSES: Dict[str, type] = {}


def default_config_path() -> str:
    """默认配置文件：``~/.ctk-kit/window.json``。"""
    return str(Path.home() / ".ctk-kit" / "window.json")


def window_state(path: Optional[str] = None) -> type:
    """返回指定路径对应的 ``WindowState`` 配置类（按路径缓存）。

    参数:
        path: 配置文件路径；不传用 :func:`default_config_path`。
    """
    target = str(Path(path).expanduser()) if path else default_config_path()
    cached = _STATE_CLASSES.get(target)
    if cached is not None:
        return cached

    section = Section("window")
    state = type(
        "WindowState",
        (ConfigBase,),
        {
            "_path": target,
            "window": section,
            "width": section.field(default=880),
            "height": section.field(default=560),
            "x": section.field(default=-1),
            "y": section.field(default=-1),
        },
    )
    _STATE_CLASSES[target] = state
    return state


def read_geometry(path: Optional[str] = None) -> Optional[Tuple[int, int, int, int]]:
    """读取保存的 ``(宽, 高, x, y)``；没有有效记录时返回 ``None``。

    宽高是逻辑像素，x/y 是屏幕物理像素；x/y 为 -1 表示没有保存位置。
    文件损坏、字段不是整数时也返回 ``None``，不让启动失败。
    """
    try:
        state = window_state(path)
        width = int(state.window.width)
        height = int(state.window.height)
        x = int(state.window.x)
        y = int(state.window.y)
    except Exception:  # noqa: BLE001 - 配置损坏不该阻止窗口启动
        return None
    if width <= 0 or height <= 0:
        return None
    return width, height, x, y


def write_geometry(
    width: int,
    height: int,
    x: int,
    y: int,
    path: Optional[str] = None,
) -> None:
    """把窗口几何写进配置文件（宽高逻辑像素，x/y 屏幕物理像素）。"""
    state = window_state(path)
    state.window.update(
        width=int(width),
        height=int(height),
        x=int(x),
        y=int(y),
    )
