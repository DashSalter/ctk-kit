"""带表头的表格：一个固定表头 + 一块可滚动的内容区。

为什么不用 ``ttk.Treeview``：它在 Windows 上走系统主题，表头、选中行、滚动条
的配色都没法跟 :mod:`ctk_kit.tokens` 对齐，深浅色切换时尤其明显。这里用两个
``tk.Canvas`` 自绘（表头一个、内容一个），配色全部从令牌里取，和库里其它控件
是同一套观感；表头固定在顶部，不随内容滚动。

单元格只放文本，够用且快——几百行也不会卡，因为内容区只画一次，滚动交给
canvas 的 ``yview``。行数上万时给 ``page_size`` 开分页，每次只画当前页。

示例::

    table = Table(
        page,
        columns=[("名称", 220, "w"), ("状态", 90, "center"), ("更新时间", 140, "w")],
        max_visible_rows=8,
    )
    table.pack(fill="x")
    table.set_rows([["配置文件", "正常", "10-30 21:04"], ...])

列宽的写法是 ``(标题, 宽度, 对齐)``；宽度是逻辑像素，``None`` 表示吃掉剩余宽度
（一般给最后一列用），对齐取 ``"w" / "center" / "e"``。
"""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import font as tkfont
from typing import Any, Optional, Sequence, Tuple

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .layout import style_scrollbar
from .pagination import Pagination
from .scrolling import find_scrollable, wheel_step
from .theme import color_of

#: 一列的定义：``(标题, 宽度, 对齐)``。宽度为 ``None`` 时自动吃掉剩余空间。
Column = Tuple[str, Optional[int], str]

_CELL_PAD = 12  # 单元格左右内边距（逻辑像素）
_SCROLLBAR_GAP = 4  # 滚动条与内容区之间的间距（逻辑像素）


def _normalize_column(column: Sequence[Any]) -> Column:
    """把 ``(标题, 宽度)`` 这种简写补成完整的三元组。"""
    if len(column) == 3:
        title, width, anchor = column
    elif len(column) == 2:
        title, width = column
        anchor = "w"
    else:
        raise ValueError(f"列定义要 2 或 3 项，收到 {column!r}")
    if anchor not in ("w", "center", "e"):
        raise ValueError(f"列对齐只能是 w / center / e，收到 {anchor!r}")
    return (str(title), width, anchor)


def _fit_text(text: str, max_width: float, measure: tkfont.Font) -> str:
    """把文字截到列宽以内，超出部分用省略号，避免画到下一列上。"""
    if max_width <= 0:
        return ""
    if measure.measure(text) <= max_width:
        return text
    ellipsis = "…"
    if measure.measure(ellipsis) > max_width:
        return ""
    low, high = 0, len(text)
    while low < high:
        mid = (low + high + 1) // 2
        if measure.measure(text[:mid] + ellipsis) <= max_width:
            low = mid
        else:
            high = mid - 1
    return text[:low] + ellipsis


class Table(ctk.CTkFrame):
    """带固定表头的表格。

    参数:
        master: 父容器。
        columns: 列定义序列，每项是 ``(标题, 宽度, 对齐)``；宽度为 ``None``
            表示这一列吃掉剩余宽度（通常只给最后一列）。
        row_height: 每行高度（逻辑像素），默认 40。
        header_height: 表头高度（逻辑像素），默认 40。
        max_visible_rows: 最多同时显示几行，超出后内容区出现滚动条，默认 8。
        striped: 是否给隔行加一层淡底色，默认 ``True``。
        empty_text: 没有数据时内容区居中显示的提示。
        page_size: 每页行数；大于 0 时底部出现分页条，表格只画当前页，
            默认 0（不分页，滚轮滚动全部数据）。

    返回:
        尚未摆位的 ``Table``；用 :meth:`set_rows` 填数据。
    """

    def __init__(
        self,
        master: tk.Misc,
        columns: Sequence[Sequence[Any]],
        *,
        row_height: int = 40,
        header_height: int = 40,
        max_visible_rows: int = 8,
        striped: bool = True,
        empty_text: str = "暂无数据",
        page_size: int = 0,
    ) -> None:
        """建表头与内容区；列宽、行高、最多可见行数在这里定下来。"""
        super().__init__(
            master,
            fg_color=T.COLOR_CARD,
            border_width=1,
            border_color=T.COLOR_BORDER,
            corner_radius=0,
        )
        self._columns = [_normalize_column(column) for column in columns]
        if not self._columns:
            raise ValueError("Table 至少要有一列")
        self._row_height = row_height
        self._header_height = header_height
        self._max_visible_rows = max(1, max_visible_rows)
        self._striped = striped
        self._empty_text = empty_text
        self._all_rows: list[list[str]] = []
        self._rows: list[list[str]] = []
        self._widths: list[float] = []
        self._page_size = max(0, int(page_size))
        self._page = 1
        self._pager: Optional[Pagination] = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._header_canvas = tk.Canvas(
            self,
            height=self._px(header_height),
            bd=0,
            highlightthickness=0,
            bg=color_of(T.COLOR_SOFT),
        )
        self._header_canvas.grid(row=0, column=0, sticky="ew")

        self._canvas = tk.Canvas(
            self,
            bd=0,
            highlightthickness=0,
            bg=color_of(T.COLOR_CARD),
        )
        self._canvas.grid(row=1, column=0, sticky="nsew")

        # 滚动条占一列，落在表格外侧，不压住内容；跨表头与内容两行，从上到下铺满，
        # 不在表头右边留一块单独的色块。
        self._scrollbar = ctk.CTkScrollbar(
            self, command=self._canvas.yview, orientation="vertical"
        )
        style_scrollbar(self._scrollbar)
        self._scrollbar.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="ns",
            padx=(self._px(_SCROLLBAR_GAP), 0),
        )

        self._canvas.configure(yscrollcommand=self._on_scroll)

        self._drag_index: Optional[int] = None
        self._drag_start = 0
        self._drag_width = 0.0
        self._drag_rest = 0.0
        self._hover_index: Optional[int] = None
        self._hover_edge: Optional[int] = None
        self._header_canvas.bind("<Button-1>", self._on_header_press)
        self._header_canvas.bind("<B1-Motion>", self._on_header_drag)
        self._header_canvas.bind("<ButtonRelease-1>", self._on_header_release)
        self._header_canvas.bind("<Motion>", self._on_header_motion)
        self._header_canvas.bind("<Leave>", self._on_header_leave)

        self._canvas.bind("<Configure>", lambda _e: self._redraw())
        self._header_canvas.bind("<Configure>", lambda _e: self._redraw())
        for canvas in (self._canvas, self._header_canvas):
            canvas.bind("<MouseWheel>", self._on_wheel)
            canvas.bind("<Button-4>", self._on_wheel_linux)
            canvas.bind("<Button-5>", self._on_wheel_linux)

        self._sync_pager()
        self._sync_height()
        self._redraw()

    # ------------------------------------------------------------------ #
    @property
    def pages(self) -> int:
        """总页数；不分页时固定为 1。"""
        if self._page_size <= 0:
            return 1
        return max(1, math.ceil(len(self._all_rows) / self._page_size))

    @property
    def page(self) -> int:
        """当前页码，从 1 开始；不分页时固定为 1。"""
        return self._page

    @property
    def page_size(self) -> int:
        """每页行数；0 表示不分页。"""
        return self._page_size

    def set_rows(self, rows: Sequence[Sequence[Any]]) -> None:
        """整批替换数据。

        参数:
            rows: 每行一个序列，元素按列顺序排列；会被 ``str()`` 转成文本。
        """
        self._all_rows = [[str(cell) for cell in row] for row in rows]
        self._page = 1
        self._sync_page()
        self._sync_pager()
        self._sync_height()
        self._redraw()

    def rows(self) -> list[list[str]]:
        """全部数据的浅拷贝（分页时也是全量，不是当前页）。"""
        return [list(row) for row in self._all_rows]

    def set_page(self, page: int) -> None:
        """跳到指定页；不分页时什么也不做。

        参数:
            page: 页码，从 1 开始；超出范围会夹到第一页/最后一页。
        """
        if self._page_size <= 0:
            return
        self._page = max(1, min(int(page), self.pages))
        self._sync_page()
        if self._pager is not None:
            self._pager.set_page(self._page)
        self._sync_height()
        self._redraw()

    def set_page_size(self, size: int) -> None:
        """改每页行数；传 0 关闭分页。

        参数:
            size: 每页行数，0 表示不分页；改完会回到第一页。
        """
        size = max(0, int(size))
        if size == self._page_size:
            return
        self._page_size = size
        self._page = 1
        if size <= 0 and self._pager is not None:
            self._pager.destroy()
            self._pager = None
        self._sync_page()
        self._sync_pager()
        self._sync_height()
        self._redraw()

    def add_row(self, row: Sequence[Any]) -> None:
        """在末尾追加一行。

        参数:
            row: 按列顺序排列的单元格；会被 ``str()`` 转成文本。
        """
        self.set_rows([*self._all_rows, list(row)])

    def remove_row(self, index: int) -> None:
        """删除指定下标的行。

        参数:
            index: 行下标，从 0 开始。

        异常:
            IndexError: 下标越界。
        """
        self._all_rows.pop(index)
        self._page = min(self._page, self.pages)
        self._sync_page()
        self._sync_pager()
        self._sync_height()
        self._redraw()

    def _sync_page(self) -> None:
        """按当前页从全量数据里切出要画的那一段。"""
        if self._page_size <= 0:
            self._rows = list(self._all_rows)
            return
        start = (self._page - 1) * self._page_size
        self._rows = list(self._all_rows[start : start + self._page_size])

    def _sync_pager(self) -> None:
        """建/更新底部分页条；不分页时销毁它。"""
        if self._page_size <= 0:
            return
        total = len(self._all_rows)
        if self._pager is None:
            self._pager = Pagination(
                self,
                total=total,
                page_size=self._page_size,
                current=self._page,
                command=self._on_pager,
                show_total=True,
            )
            self._pager.grid(
                row=2,
                column=0,
                columnspan=2,
                sticky="ew",
                padx=self._px(10),
                pady=(self._px(6), self._px(8)),
            )
        else:
            self._pager.set_total(total)
            self._pager.set_page_size(self._page_size)
            self._pager.set_page(self._page)

    def _on_pager(self, page: int) -> None:
        """分页条点击回调：只切当前页，不重复改分页条自身状态。"""
        if self._page_size <= 0:
            return
        self._page = max(1, min(int(page), self.pages))
        self._sync_page()
        self._sync_height()
        self._redraw()

    # ------------------------------------------------------------------ #
    def _px(self, value: float) -> int:
        """逻辑像素转物理像素（canvas 不参与 CTk 的缩放）。"""
        return max(1, int(round(self._apply_widget_scaling(value))))

    def _font(self, spec: Any = T.FONT_TABLE) -> tuple[str, int, str]:
        """表格文字字体：canvas 不走 CTk 的字体缩放，这里按 widget scaling 换算。"""
        return get_font(spec).create_scaled_tuple(self._apply_widget_scaling(1.0))

    def _sync_height(self) -> None:
        """按行数调整内容区高度，并同步滚动条显隐。"""
        if self._page_size > 0:
            # 分页时高度固定为一页，翻到最后一页也不缩，表格不会跳
            visible = self._page_size
        else:
            rows = len(self._rows)
            # 没数据时留两行高，空态提示才不会挤在边框上
            visible = min(rows, self._max_visible_rows) if rows else 2
        self._canvas.configure(height=self._px(visible * self._row_height))
        self._sync_scrollbar()

    def _sync_scrollbar(self) -> None:
        """行数超过可见上限才显示滚动条；分页时一页放得下，常隐。"""
        if self._page_size > 0:
            self._scrollbar.grid_remove()
        elif len(self._rows) <= self._max_visible_rows:
            self._scrollbar.grid_remove()
        else:
            self._scrollbar.grid()

    def _on_scroll(self, first: str, last: str) -> None:
        """canvas 滚动时同步滚动条滑块的位置。"""
        self._scrollbar.set(first, last)

    def _on_wheel(self, event: tk.Event) -> str:
        """Windows / macOS：delta 为正表示向上滚。"""
        if not event.delta:
            return "break"
        return self._wheel_step(-1 if event.delta > 0 else 1)

    def _on_wheel_linux(self, event: tk.Event) -> str:
        """Linux：Button-4 向上，Button-5 向下。"""
        return self._wheel_step(-1 if event.num == 4 else 1)

    def _wheel_step(self, units: int) -> str:
        """先滚表格；表格没有滚动空间时把滚轮转给外层 Scrollable。"""
        return wheel_step(
            self._canvas,
            units,
            self_units=2,
            master=self,
        )

    def _find_scrollable(self) -> Optional[ctk.CTkScrollableFrame]:
        """向上找最近的 CTkScrollableFrame（Scrollable 是它的子类）。"""
        return find_scrollable(self)

    # ------------------------------------------------------------------ #
    def _header_edge_at(self, x: float) -> Optional[int]:
        """表头 x 靠近某列右边界时，返回左边那列的下标。"""
        if not self._widths:
            return None
        pad = self._px(_CELL_PAD)
        edge = 0.0
        for index, width in enumerate(self._widths):
            edge += width + pad * 2
            if abs(x - edge) <= self._px(6):
                return index
        return None

    def _column_at(self, x: float) -> Optional[int]:
        """表头 x 落在哪一列里。"""
        if not self._widths:
            return None
        pad = self._px(_CELL_PAD)
        left = 0.0
        for index, width in enumerate(self._widths):
            right = left + width + pad * 2
            if left <= x < right:
                return index
            left = right
        return len(self._widths) - 1 if x >= left else None

    def _on_header_press(self, event: tk.Event) -> Optional[str]:
        """按住列边界，进入拖动改宽。"""
        index = self._header_edge_at(event.x)
        if index is None:
            return None
        self._drag_index = index
        self._drag_start = event.x
        self._drag_width = self._widths[index]
        # 最后一列默认吸收表头剩余宽度；拖它时要把这部分刨掉，
        # 否则写回的宽度会连同剩余一起算，下一帧再吸收一次就膨胀了。
        self._drag_rest = 0.0
        if index == len(self._columns) - 1:
            logical = self._columns[index][1]
            if logical is not None:
                self._drag_rest = max(0.0, self._drag_width - self._px(logical))
        self._hover_edge = index
        self._hover_index = self._column_at(event.x)
        self._draw_header()
        self._header_canvas.configure(cursor="sb_h_double_arrow")
        return "break"

    def _on_header_drag(self, event: tk.Event) -> Optional[str]:
        """拖动时只改当前列的宽度，其他列不跟着动。"""
        if self._drag_index is None:
            return None
        delta = event.x - self._drag_start
        width = max(self._px(40), self._drag_width + delta)
        # 拖到表头右边缘就停：给其他列留够空间，别把当前列的数据挤出去
        full = self._header_canvas.winfo_width()
        pad = self._px(_CELL_PAD)
        others = sum(self._widths) - self._widths[self._drag_index]
        max_width = full - pad * 2 * len(self._widths) - others
        if max_width > 0:
            width = min(width, max_width)
        title, _width, anchor = self._columns[self._drag_index]
        scale = self._apply_widget_scaling(1.0)
        logical = max(1.0, (width - self._drag_rest) / scale)
        self._columns[self._drag_index] = (title, logical, anchor)
        self._redraw()
        return "break"

    def _on_header_release(self, _event: tk.Event) -> None:
        """松手结束拖动。"""
        self._drag_index = None
        self._header_canvas.configure(cursor="")
        self._redraw()

    def _on_header_motion(self, event: tk.Event) -> None:
        """悬停时高亮所在列，靠近边界时换成左右箭头。"""
        if self._drag_index is not None:
            return
        edge = self._header_edge_at(event.x)
        column = self._column_at(event.x)
        if edge != self._hover_edge or column != self._hover_index:
            self._hover_edge = edge
            self._hover_index = column
            self._draw_header()
        cursor = "sb_h_double_arrow" if edge is not None else ""
        self._header_canvas.configure(cursor=cursor)

    def _on_header_leave(self, _event: tk.Event) -> None:
        """指针离开表头时清掉高亮。"""
        if self._drag_index is not None:
            return
        if self._hover_index is None and self._hover_edge is None:
            return
        self._hover_index = None
        self._hover_edge = None
        self._draw_header()
        self._header_canvas.configure(cursor="")

    def _draw_header(self) -> None:
        """重画表头：悬停列淡底色、列分隔线、拖动边界高亮。"""
        canvas = self._header_canvas
        canvas.delete("all")
        full = canvas.winfo_width()
        if full <= 1:
            return
        self._widths = self._resolve_widths(full)
        pad = self._px(_CELL_PAD)
        header_h = self._px(self._header_height)
        font = self._font(T.FONT_TABLE_HEAD)
        measure = tkfont.Font(font=font)

        if self._hover_index is not None and self._hover_index < len(self._widths):
            left = 0.0
            for i in range(self._hover_index):
                left += self._widths[i] + pad * 2
            right = left + self._widths[self._hover_index] + pad * 2
            canvas.create_rectangle(
                left,
                0,
                right,
                header_h,
                fill=color_of(T.COLOR_SOFT_HOVER),
                outline="",
            )

        x = 0.0
        for index, (title, _width, anchor) in enumerate(self._columns):
            width = self._widths[index]
            if anchor == "w":
                tx, text_anchor = x + pad, "w"
            elif anchor == "e":
                tx, text_anchor = x + width - pad, "e"
            else:
                tx, text_anchor = x + width / 2, "center"
            canvas.create_text(
                tx,
                header_h / 2,
                text=_fit_text(title, max(0, width), measure),
                anchor=text_anchor,
                font=font,
                fill=color_of(T.COLOR_MUTED),
            )
            right = x + width + pad * 2
            # 每列都画右边界，最后一列也要有，否则不知道拖哪里改宽
            canvas.create_line(
                min(right, full) - 0.5, 0, min(right, full) - 0.5, header_h,
                fill=color_of(T.COLOR_BORDER),
            )
            if self._hover_edge == index:
                canvas.create_line(
                    min(right, full) - 1, 0, min(right, full) - 1, header_h,
                    fill=color_of(T.COLOR_ACTIVE),
                    width=2,
                )
            x = right

        canvas.create_line(
            0, header_h - 1, full, header_h - 1,
            fill=color_of(T.COLOR_BORDER),
        )

    def _resolve_widths(self, total: float) -> list[float]:
        """按当前可用宽度算出每列的实际宽度。

        固定宽度之外的空间留白，不再塞给最后一列——否则拖前面的列时
        最后一列会跟着伸缩，看起来像「拖一列、动两列」。
        """
        column_count = len(self._columns)
        pad = self._px(_CELL_PAD)
        fixed = [column[1] for column in self._columns]
        available = max(1.0, total - pad * 2 * column_count)
        flexible = [index for index, width in enumerate(fixed) if width is None]
        widths: list[float] = []
        if flexible:
            fixed_sum = sum(self._px(width) for width in fixed if width is not None)
            rest = max(self._px(60), available - fixed_sum)
            share = rest / len(flexible)
            for width in fixed:
                widths.append(share if width is None else self._px(width))
        else:
            widths = [self._px(width) for width in fixed]
            total_fixed = sum(widths)
            if total_fixed > available:
                # 容器太窄：按比例压缩，保证不越过内容区（文字会截断）
                scale = available / total_fixed
                widths = [max(1, int(round(width * scale))) for width in widths]
        return widths

    def _redraw(self) -> None:
        """整体重画表头与内容区（列宽、单元格、斑马纹）。"""
        self._draw_header()
        canvas = self._canvas
        canvas.delete("all")
        full = self._header_canvas.winfo_width()
        if full <= 1:
            return
        font = self._font()
        measure = tkfont.Font(font=font)
        pad = self._px(_CELL_PAD)
        row_h = self._px(self._row_height)

        # ---- 数据区 ----
        if not self._rows:
            canvas.create_text(
                full / 2,
                row_h,
                text=self._empty_text,
                anchor="center",
                font=font,
                fill=color_of(T.COLOR_FAINT),
            )
            canvas.configure(
                scrollregion=(0, 0, full, row_h * (self._page_size or 2))
            )
            return

        stripe = color_of(T.COLOR_HOVER_FAINT)
        body_color = color_of(T.COLOR_CARD)
        for row_index, row in enumerate(self._rows):
            top = row_index * row_h
            if self._striped and row_index % 2 == 1:
                canvas.create_rectangle(
                    0, top, full, top + row_h, fill=stripe, outline=""
                )
            x = 0.0
            for column_index, column in enumerate(self._columns):
                cell = row[column_index] if column_index < len(row) else ""
                anchor = column[2]
                width = self._widths[column_index]
                text = _fit_text(cell, max(0, width), measure)
                if anchor == "w":
                    canvas.create_text(
                        x + pad, top + row_h / 2, text=text, anchor="w",
                        font=font, fill=color_of(T.COLOR_TEXT_SOFT),
                    )
                elif anchor == "e":
                    canvas.create_text(
                        x + width - pad, top + row_h / 2, text=text, anchor="e",
                        font=font, fill=color_of(T.COLOR_TEXT_SOFT),
                    )
                else:
                    canvas.create_text(
                        x + width / 2, top + row_h / 2, text=text, anchor="center",
                        font=font, fill=color_of(T.COLOR_TEXT_SOFT),
                    )
                x += width + pad * 2
                # 数据区也画列分隔线，拖列宽时能直接看到边界移动
                canvas.create_line(
                    min(x, full) - 0.5, top, min(x, full) - 0.5, top + row_h,
                    fill=color_of(T.COLOR_BORDER),
                )
            canvas.create_line(
                0, top + row_h - 1, full, top + row_h - 1,
                fill=color_of(T.COLOR_BORDER),
            )

        height = len(self._rows) * row_h
        if self._page_size > 0:
            height = self._page_size * row_h
        canvas.configure(scrollregion=(0, 0, full, height))
        canvas.configure(bg=body_color)
