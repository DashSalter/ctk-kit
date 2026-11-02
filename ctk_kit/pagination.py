"""分页条：上一页 / 页码 / 下一页，配表格或懒加载列表用。

用法::

    from ctk_kit import Pagination

    pager = Pagination(card, total=238, page_size=20, command=load_page)
    pager.pack(fill="x")

    def load_page(page):
        rows = fetch(page)
        table.set_rows(rows)

``command`` 只在用户点页码时调用；代码里用 ``set_page`` / ``set_total``
改状态不会触发回调，避免「翻页回调里又翻页」的死循环。

页数多时自动折叠成「1 … 4 5 6 … 20」，当前页两边各留 ``siblings`` 页。
第一页禁用「上一页」、最后一页禁用「下一页」。
"""

from __future__ import annotations

import math
import tkinter as tk
from typing import Any, Callable, Optional

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font

__all__ = ["Pagination"]

PageCommand = Optional[Callable[[int], None]]

#: 页码按钮宽度。
_PAGE_WIDTH = 30
#: 上一页 / 下一页按钮宽度。
_ARROW_WIDTH = 64
#: 省略号占位宽度。
_GAP_WIDTH = 22


class Pagination(ctk.CTkFrame):
    """页码条。

    参数:
        master: 父容器。
        total: 总条数，默认 0。
        page_size: 每页条数，默认 10。
        current: 初始页码，从 1 开始，默认 1。
        command: 用户翻页时的回调，参数是新页码。
        siblings: 当前页两边各显示几页，默认 1。
        show_total: 左侧是否显示「共 N 条」，默认不显示。
        **kwargs: 透传给外层 ``CTkFrame``。

    属性:
        pages: 总页数（至少 1）。
        page: 当前页码。

    方法:
        set_page(page, notify=False): 跳到指定页；``notify=True`` 时也回调。
        set_total(total): 改总条数，当前页超出范围时夹到最后一页。
        set_page_size(size): 改每页条数，同上。
    """

    def __init__(
        self,
        master: tk.Misc,
        total: int = 0,
        page_size: int = 10,
        *,
        current: int = 1,
        command: PageCommand = None,
        siblings: int = 1,
        show_total: bool = False,
        **kwargs: Any,
    ) -> None:
        """建分页条并画出第一版页码。"""
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._total = max(0, int(total))
        self._page_size = max(1, int(page_size))
        self._command = command
        self._siblings = max(0, int(siblings))
        self._page = 1

        self._total_label: Optional[ctk.CTkLabel] = None
        if show_total:
            self._total_label = ctk.CTkLabel(
                self,
                text="",
                font=get_font(T.FONT_SMALL),
                text_color=T.COLOR_MUTED,
                fg_color="transparent",
            )
            self._total_label.pack(side="left", padx=(0, T.SPACE_MD))

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(side="left")

        self._page = max(1, min(int(current), self.pages))
        self._rebuild()

    # --- 对外 ---
    @property
    def pages(self) -> int:
        """总页数，空数据也算 1 页。"""
        return max(1, math.ceil(self._total / self._page_size))

    @property
    def page(self) -> int:
        """当前页码。"""
        return self._page

    def set_page(self, page: int, notify: bool = False) -> None:
        """跳到 ``page``；超出范围会夹到第一页/最后一页。

        参数:
            page: 目标页码，从 1 开始。
            notify: 是否调用 ``command``，默认不调用。
        """
        page = max(1, min(int(page), self.pages))
        if page == self._page:
            return
        self._page = page
        self._rebuild()
        if notify and self._command is not None:
            self._command(page)

    def set_total(self, total: int) -> None:
        """改总条数；当前页超出新范围时退到最后一页。"""
        self._total = max(0, int(total))
        self._page = max(1, min(self._page, self.pages))
        self._refresh_total()
        self._rebuild()

    def set_page_size(self, page_size: int) -> None:
        """改每页条数；当前页超出新范围时退到最后一页。"""
        self._page_size = max(1, int(page_size))
        self._page = max(1, min(self._page, self.pages))
        self._refresh_total()
        self._rebuild()

    # --- 内部 ---
    def _refresh_total(self) -> None:
        """更新左侧「共 N 条」。"""
        if self._total_label is not None:
            self._total_label.configure(text=f"共 {self._total} 条")

    def _rebuild(self) -> None:
        """清空页码区，按当前状态重画。"""
        if not self.winfo_exists():
            return
        for child in self._body.winfo_children():
            child.destroy()
        self._refresh_total()

        self._arrow(self._page - 1, "上一页", enabled=self._page > 1)
        for item in self._page_items():
            if item == "…":
                gap = ctk.CTkLabel(
                    self._body,
                    text="…",
                    width=_GAP_WIDTH,
                    font=get_font(T.FONT_SMALL),
                    text_color=T.COLOR_FAINT,
                    fg_color="transparent",
                )
                gap.pack(side="left")
            else:
                self._page_button(int(item))
        self._arrow(self._page + 1, "下一页", enabled=self._page < self.pages)

    def _page_items(self) -> list:
        """算出要显示的页码和省略号。"""
        pages = self.pages
        if pages <= 7:
            return list(range(1, pages + 1))
        left = max(2, self._page - self._siblings)
        right = min(pages - 1, self._page + self._siblings)
        items: list = [1]
        if left > 2:
            items.append("…")
        items.extend(range(left, right + 1))
        if right < pages - 1:
            items.append("…")
        items.append(pages)
        return items

    def _arrow(self, page: int, text: str, *, enabled: bool) -> None:
        """上一页 / 下一页按钮；``page`` 是目标页。"""
        button = ctk.CTkButton(
            self._body,
            text=text,
            width=_ARROW_WIDTH,
            height=28,
            corner_radius=T.RADIUS_SMALL - 2,
            border_spacing=0,
            font=get_font(T.FONT_SMALL),
            fg_color="transparent",
            hover_color=T.COLOR_HOVER_FAINT,
            text_color=T.COLOR_TEXT,
            text_color_disabled=T.COLOR_FAINT,
            state="normal" if enabled else "disabled",
            command=lambda p=page: self._go(p),
        )
        button.pack(side="left", padx=(0, T.SPACE_XS))

    def _page_button(self, page: int) -> None:
        """一个页码按钮；当前页用实心强调色。"""
        active = page == self._page
        button = ctk.CTkButton(
            self._body,
            text=str(page),
            width=_PAGE_WIDTH,
            height=28,
            corner_radius=T.RADIUS_SMALL - 2,
            border_spacing=0,
            font=get_font(T.FONT_SMALL),
            fg_color=T.COLOR_ACCENT if active else "transparent",
            hover_color=T.COLOR_ACCENT_HOVER if active else T.COLOR_HOVER_FAINT,
            text_color=T.COLOR_ACCENT_TEXT if active else T.COLOR_TEXT,
            command=lambda p=page: self._go(p),
        )
        button.pack(side="left", padx=(0, T.SPACE_XS))

    def _go(self, page: int) -> None:
        """用户点页码：更新状态、回调，然后重画。"""
        if page < 1 or page > self.pages or page == self._page:
            return
        self._page = page
        if self._command is not None:
            self._command(page)
        # 回调里可能已经重建/销毁了按钮，等事件处理完再重画
        self.after_idle(self._rebuild)
