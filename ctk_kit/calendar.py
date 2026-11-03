"""日历与日期选择：月视图网格 + 一个带弹层的日期输入框。

``Calendar`` 是纯月视图，可以单独放在页面里；``DatePicker`` 把它装进
弹出层，点输入框或右侧箭头时展开，选完写回 ``YYYY-MM-DD``。

日历格子用 ``CTkButton``：今天是主色描边，选中是主色实心、白字，
非本月日期用浅一档的灰色。周一作为一周的第一天。
"""

from __future__ import annotations

import calendar as _calendar
import datetime as _dt
import tkinter as tk
from typing import Any, Callable, Optional

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font

__all__ = ["Calendar", "DatePicker"]

DateCommand = Optional[Callable[[_dt.date], None]]

#: 星期表头，周一开始。
_WEEKDAYS = ("一", "二", "三", "四", "五", "六", "日")


class Calendar(ctk.CTkFrame):
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
        """重画标题和日期网格。"""
        if not self.winfo_exists():
            return
        self._title.configure(text=f"{self._year} 年 {self._month} 月")
        for child in self._grid.winfo_children():
            child.destroy()

        today = _dt.date.today()
        weeks = _calendar.Calendar(firstweekday=0).monthdatescalendar(
            self._year, self._month
        )
        for row, week in enumerate(weeks):
            for column, date in enumerate(week):
                self._cell(row, column, date, today)

    def _cell(
        self, row: int, column: int, date: _dt.date, today: _dt.date
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

        button = ctk.CTkButton(
            self._grid,
            text=str(date.day),
            width=32,
            height=30,
            corner_radius=T.RADIUS_SMALL,
            fg_color=fg,
            hover_color=hover,
            text_color=text_color,
            border_width=1 if (date == today and not selected) else 0,
            border_color=T.COLOR_ACCENT if date == today else T.COLOR_BORDER,
            font=get_font(T.FONT_SMALL),
            command=lambda d=date: self._pick(d),
        )
        button.grid(row=row, column=column, padx=1, pady=1)

    def _pick(self, date: _dt.date) -> None:
        """点日期：选中、重画、回调。"""
        self._value = date
        if date.month != self._month or date.year != self._year:
            self._year, self._month = date.year, date.month
        self._render()
        if self._command is not None:
            self._command(date)


class DatePicker(ctk.CTkFrame):
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
            placeholder_text_color=T.COLOR_FAINT,
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(10, 0), pady=2)
        self._entry.bind("<Button-1>", lambda _e: self.open())

        self._arrow = ctk.CTkButton(
            self._box,
            text="▾",
            width=28,
            height=28,
            corner_radius=T.RADIUS_SMALL,
            fg_color="transparent",
            hover_color=T.COLOR_HOVER_FAINT,
            text_color=T.COLOR_MUTED,
            font=get_font(T.FONT_SMALL),
            command=self.open,
        )
        self._arrow.pack(side="right", padx=(4, 4))

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
        win.configure(fg_color=T.COLOR_CARD)

        calendar = Calendar(win, value=self._value, command=self._pick)
        calendar.pack(padx=8, pady=8)

        win.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        w = calendar.winfo_reqwidth() + 16
        h = calendar.winfo_reqheight() + 16
        if x + w > self.winfo_screenwidth():
            x = self.winfo_screenwidth() - w - 8
        if y + h > self.winfo_screenheight():
            y = self.winfo_rooty() - h - 4
        win.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

        win.focus_force()
        win.bind("<FocusOut>", lambda _e: self.close())
        self._win = win

    def close(self) -> None:
        """关掉日历弹层。"""
        win, self._win = self._win, None
        if win is not None:
            try:
                win.destroy()
            except tk.TclError:
                pass

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
