"""日历与日期选择：月视图网格 + 一个带弹层的日期输入框。

``Calendar`` 是纯月视图，可以单独放在页面里；``DatePicker`` 把它装进
弹出层，点输入框或右侧箭头时展开，选完写回 ``YYYY-MM-DD``。

日历格子用 ``CTkButton``：今天是主色描边，选中是主色实心、白字，
非本月日期用浅一档的灰色。周一作为一周的第一天。
"""

from __future__ import annotations

import contextlib

import calendar as _calendar
import datetime as _dt
import tkinter as tk
from typing import Any, Callable, Optional, Tuple

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .sugar import Valuable
from .popup import round_window_corners, scaled_geometry

__all__ = ["Calendar", "DatePicker"]

DateCommand = Optional[Callable[[_dt.date], None]]

#: 星期表头，周一开始。
_WEEKDAYS = ("一", "二", "三", "四", "五", "六", "日")


class Calendar(Valuable, ctk.CTkFrame):
    """月视图日历。

    参数:
        master: 父容器。
        year / month: 初始年月；不传就用今天。
        value: 初始选中的日期（``datetime.date``），可选。
        command: 点日期时的回调，参数是 ``datetime.date``。
        width: 整体宽度，默认 260。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        get(): 当前选中的日期，未选中返回 ``None``。
        set(date): 选中某个日期并翻到它所在的月份。
        prev_month() / next_month(): 翻月。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        year: Optional[int] = None,
        month: Optional[int] = None,
        value: Optional[_dt.date] = None,
        command: DateCommand = None,
        width: int = 260,
        **kwargs: Any,
    ) -> None:
        """建月视图；默认显示今天所在的月份。"""
        kwargs.setdefault("fg_color", T.COLOR_CARD)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", T.COLOR_BORDER)
        kwargs.setdefault("corner_radius", T.RADIUS_MEDIUM)
        super().__init__(master, width=width, **kwargs)

        today = _dt.date.today()
        self._value = value
        self._command = command
        self._year = year or (value.year if value else today.year)
        self._month = month or (value.month if value else today.month)
        self._width = width

        self._head = ctk.CTkFrame(self, fg_color="transparent")
        self._head.pack(fill="x", padx=8, pady=(8, 4))

        self._prev = ctk.CTkButton(
            self._head,
            text="‹",
            width=28,
            height=28,
            corner_radius=T.RADIUS_SMALL,
            fg_color="transparent",
            hover_color=T.COLOR_HOVER_FAINT,
            text_color=T.COLOR_MUTED,
            font=get_font((T.FONT_NAME, 16)),
            command=self.prev_month,
        )
        self._prev.pack(side="left")

        self._title = ctk.CTkLabel(
            self._head,
            text="",
            font=get_font((T.FONT_NAME, 13, "bold")),
            text_color=T.COLOR_TEXT,
            fg_color="transparent",
        )
        self._title.pack(side="left", fill="x", expand=True)

        self._next = ctk.CTkButton(
            self._head,
            text="›",
            width=28,
            height=28,
            corner_radius=T.RADIUS_SMALL,
            fg_color="transparent",
            hover_color=T.COLOR_HOVER_FAINT,
            text_color=T.COLOR_MUTED,
            font=get_font((T.FONT_NAME, 16)),
            command=self.next_month,
        )
        self._next.pack(side="right")

        self._week = ctk.CTkFrame(self, fg_color="transparent")
        self._week.pack(fill="x", padx=8)
        for column, name in enumerate(_WEEKDAYS):
            label = ctk.CTkLabel(
                self._week,
                text=name,
                width=32,
                font=get_font(T.FONT_TINY),
                text_color=T.COLOR_FAINT,
                fg_color="transparent",
            )
            label.grid(row=0, column=column, padx=1, pady=(0, 2))

        self._grid = ctk.CTkFrame(self, fg_color="transparent")
        self._grid.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # 固定 6 行 × 7 列：有的月份只有 5 行，格子数量跟着变的话，快速翻月
        # 会让整个日历忽高忽低。这里一次建满，空行留白。
        self._cells = []  # type: list[list[ctk.CTkButton]]
        self._dates = []  # type: list[list[Optional[_dt.date]]]
        for row in range(6):
            cell_row = []
            date_row = []
            for column in range(7):
                button = ctk.CTkButton(
                    self._grid,
                    text="",
                    width=32,
                    height=30,
                    corner_radius=T.RADIUS_SMALL,
                    fg_color="transparent",
                    hover_color=T.COLOR_HOVER_FAINT,
                    text_color=T.COLOR_TEXT,
                    font=get_font(T.FONT_SMALL),
                    command=lambda r=row, c=column: self._click_cell(r, c),
                )
                button.grid(row=row, column=column, padx=1, pady=1)
                cell_row.append(button)
                date_row.append(None)
            self._cells.append(cell_row)
            self._dates.append(date_row)

        self._render()

    # --- 对外 ---
    def configure(self, **kwargs: Any) -> None:
        """改属性；``command=`` 换点日期回调，其余透传给 ``CTkFrame``。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        super().configure(**kwargs)

    def get(self) -> Optional[_dt.date]:
        """当前选中的日期；没选过就是 ``None``。"""
        return self._value

    def set(self, date: Optional[_dt.date]) -> None:
        """选中 ``date`` 并翻到它所在的月份；传 ``None`` 清空选择。"""
        self._value = date
        if date is not None:
            self._year, self._month = date.year, date.month
        self._render()

    def prev_month(self) -> None:
        """翻到上个月。"""
        if self._month == 1:
            self._year, self._month = self._year - 1, 12
        else:
            self._month -= 1
        self._render()

    def next_month(self) -> None:
        """翻到下个月。"""
        if self._month == 12:
            self._year, self._month = self._year + 1, 1
        else:
            self._month += 1
        self._render()

    # --- 内部 ---
    def _render(self) -> None:
        """重画标题和日期网格（格子复用，行数固定 6 行）。"""
        if not self.winfo_exists():
            return
        self._title.configure(text=f"{self._year} 年 {self._month} 月")

        today = _dt.date.today()
        weeks = _calendar.Calendar(firstweekday=0).monthdatescalendar(
            self._year, self._month
        )
        for row in range(6):
            for column in range(7):
                button = self._cells[row][column]
                if row < len(weeks):
                    date = weeks[row][column]
                    self._dates[row][column] = date
                    self._paint_cell(button, date, today)
                else:
                    self._dates[row][column] = None
                    button.configure(
                        text="",
                        state="disabled",
                        fg_color="transparent",
                        hover_color=T.COLOR_CARD,
                        border_width=0,
                    )

    def _click_cell(self, row: int, column: int) -> None:
        """点格子：空白行忽略，其余交给 ``_pick``。"""
        date = self._dates[row][column]
        if date is not None:
            self._pick(date)

    def _paint_cell(
        self, button: ctk.CTkButton, date: _dt.date, today: _dt.date
    ) -> None:
        """一个日期格子：本月 / 非本月、今天、选中三种状态。"""
        selected = self._value is not None and date == self._value
        in_month = date.month == self._month and date.year == self._year
        if selected:
            fg, hover, text_color = (
                T.COLOR_ACCENT,
                T.COLOR_ACCENT_HOVER,
                T.COLOR_ACCENT_TEXT,
            )
        else:
            fg, hover = "transparent", T.COLOR_HOVER_FAINT
            text_color = T.COLOR_TEXT if in_month else T.COLOR_FAINT

        button.configure(
            text=str(date.day),
            state="normal",
            fg_color=fg,
            hover_color=hover,
            text_color=text_color,
            border_width=1 if (date == today and not selected) else 0,
            border_color=T.COLOR_ACCENT if date == today else T.COLOR_BORDER,
        )

    def _pick(self, date: _dt.date) -> None:
        """点日期：选中、重画、回调。"""
        self._value = date
        if date.month != self._month or date.year != self._year:
            self._year, self._month = date.year, date.month
        self._render()
        if self._command is not None:
            self._command(date)


#: 弹层跟随输入框位置的轮询间隔（毫秒）。
_FOLLOW_MS = 120


class DatePicker(Valuable, ctk.CTkFrame):
    """日期输入框：点一下弹出日历，选完写回。

    参数:
        master: 父容器。
        value: 初始日期（``datetime.date``），可选。
        command: 选中日期时的回调，参数是 ``datetime.date``。
        placeholder: 未选日期时的占位文字。
        width: 整体宽度，默认 200。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        get(): 当前日期，未选返回 ``None``。
        set(date): 直接写一个日期，不弹层。
        open() / close(): 打开、关闭日历弹层。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        value: Optional[_dt.date] = None,
        command: DateCommand = None,
        placeholder: str = "选择日期",
        width: int = 200,
        **kwargs: Any,
    ) -> None:
        """建日期输入框；``value`` 会直接显示出来。"""
        super().__init__(master, fg_color="transparent", width=width, **kwargs)

        self._value = value
        self._command = command
        self._placeholder = placeholder
        self._win: Optional[ctk.CTkToplevel] = None
        self._watch_job: Optional[str] = None
        self._anchor: Optional[Tuple[int, int]] = None

        self._box = ctk.CTkFrame(
            self,
            fg_color=T.COLOR_INPUT,
            border_width=1,
            border_color=T.COLOR_BORDER_INPUT,
            corner_radius=T.RADIUS_SMALL,
            height=38,
        )
        self._box.pack(fill="x")
        self._box.pack_propagate(False)

        self._entry = ctk.CTkEntry(
            self._box,
            fg_color="transparent",
            border_width=0,
            corner_radius=0,
            font=get_font(T.FONT_BODY),
            text_color=T.COLOR_TEXT,
            placeholder_text=placeholder,
            placeholder_text_color=T.COLOR_MUTED,
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(10, 0), pady=2)

        # 箭头只是视觉提示，点击它和点击输入框是同一个入口（整框可点）。
        self._arrow = ctk.CTkLabel(
            self._box,
            text="▾",
            width=30,
            height=34,
            text_color=T.COLOR_MUTED,
            font=get_font((T.FONT_NAME, 20)),
            cursor="hand2",
        )
        self._arrow.pack(side="right", padx=(2, 2), pady=1)
        for widget in (self._box, self._entry, self._arrow):
            widget.bind("<Button-1>", lambda _event: self.open(), add="+")

        self._sync_text()

    # --- 对外 ---
    def configure(self, **kwargs: Any) -> None:
        """改属性；``command=`` 换选中回调，其余透传给 ``CTkFrame``。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        super().configure(**kwargs)

    def get(self) -> Optional[_dt.date]:
        """当前选中的日期；没选过就是 ``None``。"""
        return self._value

    def set(self, date: Optional[_dt.date]) -> None:
        """直接写入日期，不弹层、不回调。"""
        self._value = date
        self._sync_text()

    def open(self) -> None:
        """打开日历弹层；已经打开就关掉。"""
        if self._win is not None and self._win.winfo_exists():
            self.close()
            return
        win = ctk.CTkToplevel(self)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(fg_color=T.COLOR_BORDER)
        # 描边画在窗口上，卡片四边各内缩 1px；Calendar 自身不再画边框。
        body = ctk.CTkFrame(
            win,
            fg_color=T.COLOR_CARD,
            # 圆角跟系统 DWM 圆角对齐，免得四角露出比 1px 粗的描边。
            corner_radius=T.RADIUS_SMALL,
            border_width=0,
        )
        body.pack(fill="both", expand=True, padx=1, pady=1)

        calendar = Calendar(body, value=self._value, command=self._pick, border_width=0)
        calendar.pack(padx=8, pady=8)

        win.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        w = win.winfo_reqwidth()
        h = win.winfo_reqheight()
        if x + w > self.winfo_screenwidth():
            x = self.winfo_screenwidth() - w - 8
        if y + h > self.winfo_screenheight():
            y = self.winfo_rooty() - h - 4
        # 宽高是物理像素，geometry 会再乘窗口缩放，交给 scaled_geometry 除回去。
        win.geometry(scaled_geometry(win, w, h, max(0, x), max(0, y)))
        round_window_corners(win, T.RADIUS_SMALL)

        win.focus_force()
        # 点弹层内部的翻月按钮也会让窗口收到 FocusOut，直接 close 会把整个
        # 日历关掉；延迟一下，等指针真的离开弹层再关。
        win.bind("<FocusOut>", lambda _e: self.after(80, self._close_if_outside))
        # grab 之后点主窗口会被重定向到弹层，靠这个关掉；否则无边框窗口
        # 拿不到可靠的 FocusOut，点旁边没反应。
        with contextlib.suppress(tk.TclError):
            win.grab_set()
        win.bind("<Button-1>", self._on_popup_click, add="+")
        self._win = win
        self._anchor = (max(0, x), max(0, y))
        self._watch_job = self.after(_FOLLOW_MS, self._follow)

    def _close_if_outside(self) -> None:
        """失焦后确认指针也离开了弹层，才关闭。

        点击弹层里的「上个月 / 下个月」按钮时，焦点会从窗口落到按钮上，
        触发 ``<FocusOut>``；只要指针还在弹层范围内就继续留着。
        """
        win = self._win
        if win is None:
            return
        try:
            pointer_x, pointer_y = win.winfo_pointerxy()
            left, top = win.winfo_rootx(), win.winfo_rooty()
            right = left + win.winfo_width()
            bottom = top + win.winfo_height()
        except tk.TclError:
            self.close()
            return
        if left <= pointer_x < right and top <= pointer_y < bottom:
            return
        self.close()

    def close(self) -> None:
        """关掉日历弹层。"""
        win, self._win = self._win, None
        if self._watch_job is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._watch_job)
            self._watch_job = None
        if win is not None:
            with contextlib.suppress(tk.TclError):
                win.grab_release()
            with contextlib.suppress(tk.TclError):
                win.destroy()

    def _follow(self) -> None:
        """输入框被滚动 / 移动后，弹层跟着挪。"""
        win = self._win
        if win is None:
            return
        try:
            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height() + 4
        except tk.TclError:
            self.close()
            return
        if self._anchor != (x, y):
            self._anchor = (x, y)
            with contextlib.suppress(tk.TclError):
                win.geometry(
                    scaled_geometry(win, win.winfo_width(), win.winfo_height(), x, y)
                )
        self._watch_job = self.after(_FOLLOW_MS, self._follow)

    def _on_popup_click(self, event: Any) -> None:
        """grab 期间点在弹层矩形之外就关。"""
        win = self._win
        if win is None:
            return
        try:
            left, top = win.winfo_rootx(), win.winfo_rooty()
            right = left + win.winfo_width()
            bottom = top + win.winfo_height()
        except tk.TclError:
            self.close()
            return
        if left <= event.x_root < right and top <= event.y_root < bottom:
            return
        self.close()

    # --- 内部 ---
    def _pick(self, date: _dt.date) -> None:
        """选中日期：写回输入框、回调、收弹层。"""
        self._value = date
        self._sync_text()
        self.close()
        if self._command is not None:
            self._command(date)

    def _sync_text(self) -> None:
        """把 ``_value`` 写进输入框。"""
        text = self._value.strftime("%Y-%m-%d") if self._value else ""
        self._entry.delete(0, "end")
        if text:
            self._entry.insert(0, text)
        else:
            # delete 之后 CTkEntry 不会自己把占位文字放回去。
            self._entry._activate_placeholder()
