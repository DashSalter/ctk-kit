"""滚轮在「控件自己」和「外层滚动容器」之间的传递。

文本区、表格这类内部能滚的控件，滚到边界以后应该把滚轮交给外面最近的
``CTkScrollableFrame``；内部根本没有滚动空间时也一样，否则用户会觉得
「鼠标放在这里页面就滚不动了」。``text.py`` 和 ``table.py`` 原来各有一份
同样的查找 + 传递逻辑，这里收成两个函数共用。
"""

from __future__ import annotations

from typing import Any, Optional

import customtkinter as ctk


def find_scrollable(widget: Any) -> Optional[ctk.CTkScrollableFrame]:
    """从 ``widget`` 的父容器向上找第一个 ``CTkScrollableFrame``。

    参数:
        widget: 起点控件；从它的 ``master`` 开始找，不包含它自己。

    返回:
        最近的滚动容器；找不到时返回 ``None``。``Scrollable`` 是
        ``CTkScrollableFrame`` 的子类，同样会被找到。
    """
    node = getattr(widget, "master", None)
    while node is not None:
        if isinstance(node, ctk.CTkScrollableFrame):
            return node
        node = getattr(node, "master", None)
    return None


def wheel_step(
    view: Any,
    units: int,
    *,
    self_units: int = 3,
    parent_units: int = 20,
    master: Any = None,
) -> str:
    """先滚 ``view`` 自己；到边界（或没有滚动空间）时交给外层滚动容器。

    参数:
        view: 有 ``yview()`` / ``yview_scroll()`` 的控件，通常是
            ``tk.Text`` 或 ``tk.Canvas``。
        units: 滚动方向，正数向下、负数向上。
        self_units: 自身滚动一格相当于几个 ``"units"``；文本区默认 3 行，
            表格默认 2 行。
        parent_units: 交给外层时一格滚多少像素。canvas 的 ``"units"`` 就是
            像素，给一个和页面滚动接近的步长，否则一格只挪 1px，像卡住。
        master: 找外层滚动容器的起点；默认从 ``view`` 自己开始找。

    返回:
        固定返回 ``"break"``，阻止 Tk 继续把同一个滚轮事件派发给父级。
    """
    try:
        top, bottom = view.yview()
    except Exception:  # noqa: BLE001 - 控件正在销毁
        return "break"
    can_scroll = (units > 0 and bottom < 1.0) or (units < 0 and top > 0.0)
    if can_scroll:
        view.yview_scroll(units * self_units, "units")
        return "break"
    parent = find_scrollable(master if master is not None else view)
    if parent is not None:
        parent._parent_canvas.yview_scroll(units * parent_units, "units")
    return "break"
