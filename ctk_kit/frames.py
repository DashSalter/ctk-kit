"""基础容器：带 ``row()`` 的 ``CTkFrame`` 和默认透明底的 ``Frame``。

``CTkFrame`` 的 ``fg_color`` 默认取主题色（不透明），而排版用的行、列、表单
容器绝大多数时候需要透明底，每次写 ``fg_color="transparent"`` 很啰嗦。
:class:`Frame` 就是把这一个默认值收进来的子类::

    row = Frame(page)          # 透明底
    card = Frame(page, fg_color=COLOR_CARD)   # 要底色就显式覆盖

两个容器都混入了 :class:`~ctk_kit.layout.RowHost`，可以直接按编号分行，
边距自动分配，和 ``Card`` 的写法一致::

    box = Frame(page, fg_color=COLOR_CARD)
    FieldLabel(box.row(1), "用户名").pack(side="left", anchor="nw")
    CTkEntry(box.row(1), placeholder="用户名").pack(
        side="left", fill="x", expand=True, padx=(8, 0)
    )

原生 ``CTkFrame`` 的能力全部保留：需要默认主题底色的地方原来怎么写还怎么写，
只是额外多了 ``row()`` 和 ``Row`` 这一套排版方法。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

from .chain import Chainable
from .layout import RowHost

__all__ = ["CTkFrame", "Frame"]


class CTkFrame(Chainable, RowHost, ctk.CTkFrame):
    """带 ``row()`` 的 ``CTkFrame``，其余参数和行为与原生一致。

    混入 :class:`~ctk_kit.chain.Chainable` 是为了静态类型提示：``pack()`` 的
    返回值标注成控件自身，所以 ``bar = Frame(page).pack(fill="x")`` 之后
    IDE 仍然能补全 ``row()`` / ``set_fg_color()`` 这些方法。
    """


class Frame(CTkFrame):
    """纯布局容器，默认 ``fg_color="transparent"``，同样带 ``row()``。

    参数与 ``CTkFrame`` 完全一致；唯一区别是没传 ``fg_color`` 时用透明底。
    显式传 ``fg_color``（单色或深浅二元组）即可覆盖。
    """

    def __init__(self, master: tk.Misc, **kwargs: Any) -> None:
        """建透明底布局容器；显式 ``fg_color`` 可覆盖默认值。"""
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
