"""基础容器：默认透明底的 ``Frame``。

``CTkFrame`` 的 ``fg_color`` 默认取主题色（不透明），而排版用的行、列、表单
容器绝大多数时候需要透明底，每次写 ``fg_color="transparent"`` 很啰嗦。
:class:`Frame` 就是把这一个默认值收进来的子类::

    row = Frame(page)          # 透明底
    card = Frame(page, fg_color=COLOR_CARD)   # 要底色就显式覆盖

原生 ``CTkFrame`` 仍原样从 ``ctk_kit`` 导出，需要默认主题底色的地方继续用它。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

__all__ = ["Frame"]


class Frame(ctk.CTkFrame):
    """纯布局容器，默认 ``fg_color="transparent"``。

    参数与 ``CTkFrame`` 完全一致；唯一区别是没传 ``fg_color`` 时用透明底。
    显式传 ``fg_color``（单色或深浅二元组）即可覆盖。
    """

    def __init__(self, master: tk.Misc, **kwargs: Any) -> None:
        """建透明底布局容器；显式 ``fg_color`` 可覆盖默认值。"""
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
