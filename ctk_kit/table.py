"""带表头的表格：一个固定表头 + 一块可滚动的内容区。

为什么不用 ``ttk.Treeview``：它在 Windows 上走系统主题，表头、选中行、滚动条
的配色都没法跟 :mod:`ctk_kit.tokens` 对齐，深浅色切换时尤其明显。这里用两个
``tk.Canvas`` 自绘（表头一个、内容一个），配色全部从令牌里取，和库里其它控件
是同一套观感；表头固定在顶部，不随内容滚动。

单元格只放文本，够用且快——几百行也不会卡，因为内容区只画一次，滚动交给
canvas 的 ``yview``。

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

import tkinter as tk
from typing import Any, Optional, Sequence, Tuple

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .layout import style_scrollbar
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
    ) -> None:
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
        self._rows: list[list[str]] = []
        self._widths: list[float] = []

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

        self._canvas.bind("<Configure>", lambda _e: self._redraw())
        self._header_canvas.bind("<Configure>", lambda _e: self._redraw())
        self._canvas.bind("<MouseWheel>", self._on_wheel)
        self._header_canvas.bind("<MouseWheel>", self._on_wheel)

        self._sync_height()
        self._redraw()

    # ------------------------------------------------------------------ #
    def set_rows(self, rows: Sequence[Sequence[Any]]) -> None:
        """整批替换数据。

        参数:
            rows: 每行一个序列，元素按列顺序排列；会被 ``str()`` 转成文本。
        """
        self._rows = [[str(cell) for cell in row] for row in rows]
        self._sync_height()
        self._redraw()

    def rows(self) -> list[list[str]]:
        """当前数据的浅拷贝。"""
        return [list(row) for row in self._rows]

    # ------------------------------------------------------------------ #
    def _px(self, value: float) -> int:
        """逻辑像素转物理像素（canvas 不参与 CTk 的缩放）。"""
        return max(1, int(round(self._apply_widget_scaling(value))))

    def _font(self, spec: Any = T.FONT_TABLE) -> tuple[str, int, str]:
        """表格文字字体：canvas 不走 CTk 的字体缩放，这里按 widget scaling 换算。"""
        return get_font(spec).create_scaled_tuple(self._apply_widget_scaling(1.0))

    def _sync_height(self) -> None:
        rows = len(self._rows)
        # 没数据时留两行高，空态提示才不会挤在边框上
        visible = min(rows, self._max_visible_rows) if rows else 2
        self._canvas.configure(height=self._px(visible * self._row_height))
        self._sync_scrollbar()

    def _sync_scrollbar(self) -> None:
        if len(self._rows) <= self._max_visible_rows:
            self._scrollbar.grid_remove()
        else:
            self._scrollbar.grid()

    def _on_scroll(self, first: str, last: str) -> None:
        self._scrollbar.set(first, last)

    def _on_wheel(self, event: tk.Event) -> str:
        if len(self._rows) <= self._max_visible_rows:
            return "break"
        step = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(step * 2, "units")
        return "break"

    # ------------------------------------------------------------------ #
    def _resolve_widths(self, total: float) -> list[float]:
        """按当前可用宽度算出每列的实际宽度。"""
        column_count = len(self._columns)
        pad = self._px(_CELL_PAD)
        fixed = [column[1] for column in self._columns]
        available = total - pad * 2 * column_count
        fixed_sum = sum(self._px(width) for width in fixed if width is not None)
        flexible = [index for index, width in enumerate(fixed) if width is None]
        widths: list[float] = []
        if flexible:
            rest = max(self._px(60), available - fixed_sum)
            share = rest / len(flexible)
            for width in fixed:
                widths.append(share if width is None else self._px(width))
        else:
            rest = available - fixed_sum
            if rest > 0:
                widths = [self._px(width) + rest / column_count for width in fixed]
            else:
                # 容器太窄：按比例压缩，至少留 40px，避免文字挤成一条
                scale = max(0.2, available / max(1.0, fixed_sum))
                widths = [max(self._px(40), self._px(width) * scale) for width in fixed]
        return widths

    def _redraw(self) -> None:
        for canvas in (self._header_canvas, self._canvas):
            canvas.delete("all")

        full = self._header_canvas.winfo_width()
        if full <= 1:
            return
        font = self._font()
        head_font = self._font(T.FONT_TABLE_HEAD)
        self._widths = self._resolve_widths(full)
        pad = self._px(_CELL_PAD)
        row_h = self._px(self._row_height)
        header_h = self._px(self._header_height)

        # ---- 表头 ----
        x = 0.0
        for index, (title, _width, anchor) in enumerate(self._columns):
            width = self._widths[index]
            if anchor == "w":
                self._header_canvas.create_text(
                    x + pad, header_h / 2, text=title, anchor="w",
                    font=head_font, fill=color_of(T.COLOR_MUTED),
                )
            elif anchor == "e":
                self._header_canvas.create_text(
                    x + width - pad, header_h / 2, text=title, anchor="e",
                    font=head_font, fill=color_of(T.COLOR_MUTED),
                )
            else:
                self._header_canvas.create_text(
                    x + width / 2, header_h / 2, text=title, anchor="center",
                    font=head_font, fill=color_of(T.COLOR_MUTED),
                )
            x += width + pad * 2
        self._header_canvas.create_line(
            0, header_h - 1, full, header_h - 1,
            fill=color_of(T.COLOR_BORDER),
        )

        # ---- 数据区 ----
        if not self._rows:
            self._canvas.create_text(
                full / 2,
                row_h,
                text=self._empty_text,
                anchor="center",
                font=font,
                fill=color_of(T.COLOR_FAINT),
            )
            self._canvas.configure(scrollregion=(0, 0, full, row_h * 2))
            return

        stripe = color_of(T.COLOR_HOVER_FAINT)
        body_color = color_of(T.COLOR_CARD)
        for row_index, row in enumerate(self._rows):
            top = row_index * row_h
            if self._striped and row_index % 2 == 1:
                self._canvas.create_rectangle(
                    0, top, full, top + row_h, fill=stripe, outline=""
                )
            x = 0.0
            for column_index, cell in enumerate(row[: len(self._columns)]):
                anchor = self._columns[column_index][2]
                width = self._widths[column_index]
                if anchor == "w":
                    self._canvas.create_text(
                        x + pad, top + row_h / 2, text=cell, anchor="w",
                        font=font, fill=color_of(T.COLOR_TEXT_SOFT),
                    )
                elif anchor == "e":
                    self._canvas.create_text(
                        x + width - pad, top + row_h / 2, text=cell, anchor="e",
                        font=font, fill=color_of(T.COLOR_TEXT_SOFT),
                    )
                else:
                    self._canvas.create_text(
                        x + width / 2, top + row_h / 2, text=cell, anchor="center",
                        font=font, fill=color_of(T.COLOR_TEXT_SOFT),
                    )
                x += width + pad * 2
            self._canvas.create_line(
                0, top + row_h - 1, full, top + row_h - 1,
                fill=color_of(T.COLOR_BORDER),
            )

        height = len(self._rows) * row_h
        self._canvas.configure(scrollregion=(0, 0, full, height))
        self._canvas.configure(bg=body_color)
