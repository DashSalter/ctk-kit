"""手风琴：一组标题行，点开一节展开一块内容。

单开模式（``mode="single"``）同一时刻最多一节展开，适合设置页分区；
多开模式（``mode="multiple"``）各节互不影响，适合 FAQ、日志详情这类清单。
标题右侧可以常驻一行摘要（如「3 项」「已启用」），收起时也看得见。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional

import customtkinter as ctk

from . import layout
from . import tokens as T
from .collapse import Collapsible, ToggleCommand

__all__ = ["Accordion", "AccordionItem"]

_MODE_SINGLE = "single"
_MODE_MULTIPLE = "multiple"
_MODES = (_MODE_SINGLE, _MODE_MULTIPLE)


class AccordionItem(Collapsible):
    """手风琴里的一节：左边标题、右边摘要，下面是内容容器。

    一般由 :meth:`Accordion.add` 创建，不建议直接构造。

    参数:
        master: 父容器（通常是 ``Accordion``）。
        title: 标题文字。
        detail: 标题右侧的摘要小字，默认空表示不显示。
        expanded: 初始是否展开，默认收起。
        button_height: 标题行高度（像素），默认 36。
        on_toggle: 展开状态变化回调，参数是新的状态。

    属性:
        body: 内容容器，往这里 pack 子控件。
        title: 标题文字。
        detail: 右侧摘要文字。
        expanded: 当前是否展开。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str,
        detail: str = "",
        expanded: bool = False,
        button_height: int = 36,
        on_toggle: ToggleCommand = None,
        **kwargs: Any,
    ) -> None:
        self._title = title
        self._accordion: Optional["Accordion"] = None
        super().__init__(
            master,
            collapsed_text=title,
            expanded_text=title,
            expanded=False,
            button_height=button_height,
            detail=detail,
            on_toggle=on_toggle,
            **kwargs,
        )
        # 标题左对齐：Collapsible 默认居中，这里只作用于手风琴。
        self.button.configure(anchor="w")
        if expanded:
            self.set_expanded(True)

    # --- 对外 ---
    @property
    def title(self) -> str:
        """标题文字。"""
        return self._title

    def set_title(self, title: str) -> None:
        """换掉标题文字（摘要不受影响）。"""
        self._title = title
        self._sync_text()

    def set_texts(self, *, collapsed_text: str = "", expanded_text: str = "") -> None:
        """每节只有一个标题，取 ``collapsed_text``（为空时用 ``expanded_text``）。"""
        self.set_title(collapsed_text or expanded_text or self._title)

    def set_expanded(self, expanded: bool) -> None:
        """展开/收起；单开模式下展开前先让同组其它节收起。"""
        expanded = bool(expanded)
        if expanded and not self._expanded and self._accordion is not None:
            self._accordion._before_expand(self)
        super().set_expanded(expanded)

    # --- 内部 ---
    def _sync_text(self) -> None:
        arrow = "▲" if self._expanded else "▼"
        self.button.configure(text=f"{arrow}    {self._title}")


class Accordion(ctk.CTkFrame):
    """手风琴容器：一组可折叠的节，标题行下面是内容。

    单开模式下点开一节会自动收起其它节，允许多节全部收起；
    多开模式下各节独立，可以同时展开任意多节。

    参数:
        master: 父容器。
        mode: ``"single"``（单开，默认）或 ``"multiple"``（多开）。
        on_change: 展开状态变化回调，参数是（节序号, 新的状态）；
            点开一节连带收起另一节时，会先收到被收起那节的回调。
        **kwargs: 透传给外层 ``CTkFrame``。

    属性:
        mode: 当前模式。

    示例::

        acc = Accordion(parent, mode="single")
        basic = acc.add("基本信息", detail="3 项", expanded=True)
        Label(basic.body, "……").pack(fill="x", padx=12, pady=10)
        acc.add("高级选项", detail="2 项")
        acc.expand(1)          # 程序控制：展开第 2 节
        acc.collapse_all()     # 全部收起
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        mode: str = _MODE_SINGLE,
        on_change: Optional[Callable[[int, bool], None]] = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)

        self._mode = self._check_mode(mode)
        self._on_change = on_change
        self._items: list[AccordionItem] = []
        self._dividers: list[tk.Frame] = []

    # --- 对外 ---
    @property
    def mode(self) -> str:
        """当前模式：``"single"`` 或 ``"multiple"``。"""
        return self._mode

    def add(
        self,
        title: str,
        *,
        detail: str = "",
        expanded: bool = False,
        button_height: int = 36,
    ) -> AccordionItem:
        """在末尾追加一节，返回这一节（内容往 ``item.body`` 里放）。

        参数:
            title: 标题文字。
            detail: 标题右侧的摘要小字，默认空。
            expanded: 加进来时是否直接展开，默认收起。
            button_height: 标题行高度，默认 36。
        """
        index = len(self._items)
        if index:
            self._dividers.append(
                layout.divider(self, pady=(T.SPACE_SM, T.SPACE_SM))
            )
        item = AccordionItem(
            self,
            title=title,
            detail=detail,
            button_height=button_height,
            on_toggle=lambda flag, i=index: self._notify(i, flag),
        )
        item._accordion = self
        item.pack(fill="x")
        self._items.append(item)
        if expanded:
            item.set_expanded(True)
        return item

    @property
    def items(self) -> list[AccordionItem]:
        """所有节，按添加顺序；返回副本，改这个列表不影响组件。"""
        return list(self._items)

    def expanded_items(self) -> list[int]:
        """当前展开的节的序号，升序。"""
        return [i for i, item in enumerate(self._items) if item.expanded]

    def expand(self, index: int) -> None:
        """展开第 ``index`` 节；单开模式下会自动收起其它展开的节。"""
        self._item(index).expand()

    def collapse(self, index: int) -> None:
        """收起第 ``index`` 节。"""
        self._item(index).collapse()

    def toggle(self, index: int) -> None:
        """切换第 ``index`` 节。"""
        self._item(index).toggle()

    def collapse_all(self) -> None:
        """收起所有节（每节都会走一次 ``on_change``）。"""
        for item in self._items:
            item.set_expanded(False)

    def set_mode(self, mode: str) -> None:
        """切换 single / multiple；切到 single 时只保留序号最小的展开节。"""
        mode = self._check_mode(mode)
        if mode == self._mode:
            return
        self._mode = mode
        if mode == _MODE_SINGLE:
            opened = self.expanded_items()
            for index in opened[1:]:
                self._items[index].set_expanded(False)

    def clear(self) -> None:
        """移除所有节，连带销毁里面的内容。"""
        for item in self._items:
            item.destroy()
        self._items.clear()
        for divider in self._dividers:
            divider.destroy()
        self._dividers.clear()

    def __len__(self) -> int:
        """节的数量。"""
        return len(self._items)

    # --- 内部 ---
    @staticmethod
    def _check_mode(mode: str) -> str:
        if mode not in _MODES:
            raise ValueError('mode 只能是 "single" 或 "multiple"')
        return mode

    def _item(self, index: int) -> AccordionItem:
        if not isinstance(index, int):
            raise TypeError(f"节序号必须是 int，收到 {type(index).__name__}")
        try:
            return self._items[index]
        except IndexError:
            raise IndexError(
                f"节序号 {index} 超出范围（共 {len(self._items)} 节）"
            ) from None

    def _notify(self, index: int, expanded: bool) -> None:
        if self._on_change is not None:
            self._on_change(index, expanded)

    def _before_expand(self, item: AccordionItem) -> None:
        """single 模式的不变量：要开一节，就把别的展开节先收掉。"""
        if self._mode != _MODE_SINGLE:
            return
        for other in self._items:
            if other is not item and other.expanded:
                other.set_expanded(False)
