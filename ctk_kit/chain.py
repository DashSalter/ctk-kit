"""让布局方法返回控件自身，方便连写。"""

from __future__ import annotations

from typing import Any, Optional

from typing_extensions import Self


class Chainable:
    """混入后 ``pack`` / ``grid`` / ``place`` 返回控件自身。

    Tk 的布局方法固定返回 ``None``，赋值时拿不到控件。混入这个类之后::

        but = PrimaryButton(row, "保存").pack(side="left")
        but.disable()

    ctk-kit 里带交互的常用组件都混入了它。
    """

    def pack(
        self,
        side: Optional[str] = None,
        fill: Optional[str] = None,
        expand: Optional[bool] = None,
        padx: Any = None,
        pady: Any = None,
        anchor: Optional[str] = None,
        ipadx: Optional[int] = None,
        ipady: Optional[int] = None,
        **kwargs: Any,
    ) -> Self:
        """按 ``side`` / ``fill`` / ``expand`` … 摆放，返回控件自身。"""
        options = {
            "side": side,
            "fill": fill,
            "expand": expand,
            "padx": padx,
            "pady": pady,
            "anchor": anchor,
            "ipadx": ipadx,
            "ipady": ipady,
        }
        getattr(super(), "pack")(
            **{key: value for key, value in options.items() if value is not None}, **kwargs
        )
        return self

    def grid(
        self,
        row: Optional[int] = None,
        column: Optional[int] = None,
        rowspan: Optional[int] = None,
        columnspan: Optional[int] = None,
        sticky: Optional[str] = None,
        padx: Any = None,
        pady: Any = None,
        ipadx: Optional[int] = None,
        ipady: Optional[int] = None,
        **kwargs: Any,
    ) -> Self:
        """按网格摆放，返回控件自身。"""
        options = {
            "row": row,
            "column": column,
            "rowspan": rowspan,
            "columnspan": columnspan,
            "sticky": sticky,
            "padx": padx,
            "pady": pady,
            "ipadx": ipadx,
            "ipady": ipady,
        }
        getattr(super(), "grid")(
            **{key: value for key, value in options.items() if value is not None}, **kwargs
        )
        return self

    def place(
        self,
        x: Any = None,
        y: Any = None,
        relx: Any = None,
        rely: Any = None,
        relwidth: Any = None,
        relheight: Any = None,
        width: Any = None,
        height: Any = None,
        anchor: Optional[str] = None,
        bordermode: Optional[str] = None,
        **kwargs: Any,
    ) -> Self:
        """按坐标摆放，返回控件自身。"""
        options = {
            "x": x,
            "y": y,
            "relx": relx,
            "rely": rely,
            "relwidth": relwidth,
            "relheight": relheight,
            "width": width,
            "height": height,
            "anchor": anchor,
            "bordermode": bordermode,
        }
        getattr(super(), "place")(
            **{key: value for key, value in options.items() if value is not None}, **kwargs
        )
        return self
