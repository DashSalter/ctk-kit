"""每个示例页一个模块，既能被主窗口装配，也能单独启动。

单独启动：

    python -m ctk_kit.showcase.pages.buttons
    python -m ctk_kit.showcase.pages.notify --topmost

每个模块都导出 ``build(master, ...)`` 与 ``main()``；改某一页时只跑那一个
模块就够了，不需要把十个页面都启动起来。

这里用惰性导入：只有真正访问 ``pages.buttons`` 时才加载那个模块。否则
``python -m ctk_kit.showcase.pages.buttons`` 会因为包已经把所有页面都导入过，
触发 runpy 的 "found in sys.modules" 警告。
"""

from __future__ import annotations

import importlib

_NAMES = (
    "buttons",
    "foundation",
    "form",
    "inputs",
    "layout",
    "listing",
    "notify",
    "overview",
    "settings",
    "theme",
)

__all__ = list(_NAMES)


def __getattr__(name: str):
    if name in _NAMES:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals()) + list(_NAMES))
