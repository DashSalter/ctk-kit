"""三列滚轮时间选择器：时 / 分 / 秒各一列。

没有用 ``tk.Spinbox``，而是每列一张 canvas 自己画五格数字：中间一行高亮，
上下两行按距离淡化，滚动时整体平移并补新数字，看起来像滚轮。

用法::

    picker = TimePicker(root, value=datetime.time(9, 30))
    picker.pack()
    picker.get()            # datetime.time(9, 30)
    picker.set(datetime.time(18, 0, 0))
"""

from __future__ import annotations

import contextlib

import datetime as _dt
import time
import tkinter as tk
from typing import Any, Callable, Iterable, Optional, Tuple

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .sugar import Valuable
from .popup import round_window_corners, scaled_geometry
from .theme import color_of

__all__ = ["TimeField", "TimePicker"]

#: 每行高度、可见行数、滚动动画时长与帧间隔。
_ROW = 30
_VISIBLE = 5
_ANIM_MS = 120
_ANIM_STEP = 16

# 弹层面板的底色。和下拉框（select._PANEL_BG）、右键菜单（context_menu._MENU_BG）
# 用同一个值：这三个弹层长得一样，浅一档的卡片色摆在一起就显得日期、时间这两个
# 是「另一个组件」。
_POPUP_BG = "#2B2B2B"


class _Wheel(tk.Canvas):
    """一列数字滚轮。"""

    def __init__(
        self,
        master: tk.Misc,
        values: Iterable[int],
        *,
        width: int = 46,
        command: Optional[Callable[[], None]] = None,
        bg: Optional[str] = None,
    ) -> None:
        self._bg = bg or T.COLOR_CARD
        super().__init__(
            master,
            width=width,
            height=_ROW * _VISIBLE,
            highlightthickness=0,
            borderwidth=0,
            bg=color_of(self._bg),
            cursor="hand2",
        )
        self._values = list(values)
        self._command = command
        self._pos = 0.0
        # 动画中的显示位置是 _pos，逻辑位置是 _target；回调按 _target 报值。
        self._target = 0.0
        self._job: Optional[str] = None

        # 中间行的底色，画在文字下面。
        self._highlight = self.create_rectangle(
            0,
            0,
            width,
            _ROW,
            fill=color_of(T.COLOR_SOFT),
            outline="",
        )
        self._items = []
        for _ in range(_VISIBLE):
            item = self.create_text(
                width // 2,
                0,
                text="",
                fill=color_of(T.COLOR_TEXT),
                font=get_font((T.FONT_NAME, 16)),
            )
            self._items.append(item)

        self.tag_lower(self._highlight)
        self.bind("<MouseWheel>", self._on_wheel)
        self.bind("<Button-4>", lambda _event: self._scroll(-1))
        self.bind("<Button-5>", lambda _event: self._scroll(1))
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", lambda _event: self._paint())
        self.after(1, self._paint)

    # --- 对外 ---
    @property
    def index(self) -> int:
        """当前停留的数字。"""
        return int(round(self._target)) % len(self._values)

    def set(self, index: int, *, animate: bool = False) -> None:
        """跳到某个数字；默认不播动画、不回调。"""
        target = float(index % len(self._values))
        self._target = target
        if abs(target - self._pos) < 0.001:
            self._pos = target
            self._paint()
            return
        if animate:
            self._animate_to(target)
            return
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        self._pos = target
        self._paint()

    def step(self, delta: int) -> None:
        """往上 / 往下滚一格：逻辑值立刻变，动画随后跟上。"""
        self._target = float(int(round(self._target)) + delta)
        self._animate_to(self._target)
        if self._command is not None:
            self._command()

    def destroy(self) -> None:
        if self._job is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._job)
            self._job = None
        super().destroy()

    def apply_theme(self) -> None:
        """换外观后重取颜色。"""
        self.configure(bg=color_of(self._bg))
        self.itemconfigure(self._highlight, fill=color_of(T.COLOR_SOFT))
        self._paint()

    # --- 内部 ---
    def _scroll(self, delta: int) -> str:
        self.step(delta)
        # 不返回 break 的话，事件会继续冒泡到页面 Scrollable 的 bind_all 上。
        return "break"

    def _on_wheel(self, event: Any) -> str:
        return self._scroll(-1 if getattr(event, "delta", 0) > 0 else 1)

    def _on_click(self, event: Any) -> str:
        center = self.winfo_height() / 2
        if event.y < center - _ROW / 2:
            self.step(-1)
        elif event.y > center + _ROW / 2:
            self.step(1)
        return "break"

    def _paint(self) -> None:
        width = self.winfo_width() or 46
        height = self.winfo_height() or _ROW * _VISIBLE
        center = height / 2
        count = len(self._values)
        base = int(round(self._pos))
        middle = (_VISIBLE - 1) / 2
        for slot, item in enumerate(self._items):
            offset = slot - middle
            index = (base + int(offset)) % count
            y = center + (offset - (self._pos - base)) * _ROW
            self.coords(item, width / 2, y)
            distance = abs(offset - (self._pos - base))
            if distance < 0.6:
                color = T.COLOR_TEXT
            elif distance < 1.6:
                color = T.COLOR_MUTED
            else:
                color = T.COLOR_FAINT
            self.itemconfigure(
                item,
                text=f"{self._values[index]:02d}",
                fill=color_of(color),
            )
        self.coords(
            self._highlight,
            2,
            center - _ROW / 2,
            width - 2,
            center + _ROW / 2,
        )

    def _animate_to(self, target: float) -> None:
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        start = self._pos
        delta = target - start
        if abs(delta) < 0.001:
            return
        started = time.perf_counter()

        def tick() -> None:
            ratio = (time.perf_counter() - started) / (_ANIM_MS / 1000.0)
            eased = 1.0 - (1.0 - min(1.0, ratio)) ** 3
            self._pos = start + delta * eased
            self._paint()
            if ratio < 1.0:
                self._job = self.after(_ANIM_STEP, tick)
            else:
                self._job = None
                self._pos = float(target)
                self._paint()

        self._job = self.after(1, tick)


class TimePicker(Valuable, ctk.CTkFrame):
    """时 / 分 / 秒三列滚轮。

    参数:
        master: 父容器。
        value: 初始时间（``datetime.time``），默认当前时间。
        command: 任意一列滚完时回调，参数是新的 ``datetime.time``。
        width: 整体宽度，默认按三列内容撑开。
    """

    def __init__(
        self,
        master: tk.Misc,
        value: Optional[_dt.time] = None,
        command: Optional[Callable[[_dt.time], None]] = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("fg_color", T.COLOR_CARD)
        kwargs.setdefault("corner_radius", T.RADIUS_MEDIUM)
        super().__init__(master, **kwargs)
        self._bg = kwargs["fg_color"]
        self._command = command

        self._hour = _Wheel(self, range(24), command=self._changed, bg=self._bg)
        self._minute = _Wheel(self, range(60), command=self._changed, bg=self._bg)
        self._second = _Wheel(self, range(60), command=self._changed, bg=self._bg)

        self._colons = []
        self._hour.pack(side="left", padx=(12, 0), pady=10)
        self._colon().pack(side="left")
        self._minute.pack(side="left")
        self._colon().pack(side="left")
        self._second.pack(side="left", padx=(0, 12))

        self.set(value if value is not None else _dt.datetime.now().time())

    # --- 对外 ---
    def get(self) -> _dt.time:
        """当前选中的时间。"""
        return _dt.time(self._hour.index, self._minute.index, self._second.index)

    def set(self, value: _dt.time) -> None:
        """直接写入时间，不回调。"""
        self._hour.set(value.hour)
        self._minute.set(value.minute)
        self._second.set(value.second)

    def configure(self, **kwargs: Any) -> None:
        """``command=`` 换回调，其余透传给 ``CTkFrame``。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if kwargs:
            super().configure(**kwargs)

    def apply_theme(self) -> None:
        """切外观后重刷三列颜色。"""
        super().configure(fg_color=self._bg)
        for wheel in (self._hour, self._minute, self._second):
            wheel.apply_theme()
        for label in self._colons:
            label.configure(text_color=T.COLOR_MUTED)

    # --- 内部 ---
    def _colon(self) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            self,
            text=":",
            width=10,
            fg_color="transparent",
            text_color=T.COLOR_MUTED,
            font=get_font((T.FONT_NAME, 16)),
        )
        self._colons.append(label)
        return label

    def _changed(self) -> None:
        if self._command is not None:
            self._command(self.get())


#: 弹层跟随输入框位置的轮询间隔（毫秒）。
_FOLLOW_MS = 120


class TimeField(Valuable, ctk.CTkFrame):
    """时间输入框：[时] : [分] : [秒 ▾]。

    三段平时可以直接键入，回车或失焦时解析、越界夹回；点右侧三角形才弹出
    三列滚轮，滚动时立即更新并回调，没有确定 / 取消按钮。

    参数:
        master: 父容器。
        value: 初始时间（``datetime.time``），默认 00:00:00。
        command: 滚动或键入后回调，参数是新的 ``datetime.time``。
        width: 整体宽度，默认 150。
        readonly: 只读时不能键入、也点不开弹层，值照常显示；之后可用
            :meth:`set_readonly` 切换。

    方法:
        get(): 当前时间。
        set(time): 直接写一个时间，不弹层。
        set_readonly(flag): 开关只读。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        value: Optional[_dt.time] = None,
        command: Optional[Callable[[_dt.time], None]] = None,
        width: int = 140,
        readonly: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", width=width, height=38, **kwargs)
        # 不让子控件把整体撑宽，宽度和弹层保持一致。
        self.pack_propagate(False)
        self._value = value if value is not None else _dt.time(0, 0, 0)
        self._command = command
        self._readonly = bool(readonly)
        self._win: Optional[ctk.CTkToplevel] = None
        self._picker: Optional[TimePicker] = None
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
        self._box.pack(fill="both", expand=True)
        self._box.pack_propagate(False)

        self._hour = self._segment()
        self._minute = self._segment()
        self._second = self._segment()

        self._hour.pack(side="left", padx=(10, 0))
        self._colon().pack(side="left")
        self._minute.pack(side="left")
        self._colon().pack(side="left")
        self._second.pack(side="left")

        # 箭头才是弹层入口；三段留给键盘，点数字不会把面板顶出来。
        self._arrow = ctk.CTkLabel(
            self._box,
            text="▾",
            width=26,
            height=34,
            text_color=T.COLOR_MUTED,
            font=get_font((T.FONT_NAME, 20)),
            cursor="hand2",
        )
        self._arrow.pack(side="right", padx=(2, 4))
        self._arrow.bind("<Button-1>", self._on_click, add="+")
        for entry in (self._hour, self._minute, self._second):
            entry.bind("<Return>", self._commit_typed)
            entry.bind("<FocusOut>", self._commit_typed)

        self._apply_readonly()
        self._sync_text()

    # --- 对外 ---
    def configure(self, **kwargs: Any) -> None:
        """``command=`` 换回调，其余透传给 ``CTkFrame``。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        super().configure(**kwargs)

    def get(self) -> _dt.time:
        """当前时间。"""
        return self._value

    def set(self, value: _dt.time) -> None:
        """直接写入时间，不弹层、不回调。"""
        self._value = value
        self._sync_text()

    def set_readonly(self, flag: bool = True) -> None:
        """开关只读：只读时点不开弹层，值照常显示。"""
        flag = bool(flag)
        if flag == self._readonly:
            return
        self._readonly = flag
        if flag:
            self.close()
        self._apply_readonly()

    def open(self) -> None:
        """打开时间弹层；已经打开就关掉。"""
        if self._readonly:
            return
        if self._win is not None and self._win.winfo_exists():
            self.close()
            return
        win = ctk.CTkToplevel(self)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(fg_color=T.COLOR_BORDER)
        body = ctk.CTkFrame(
            win,
            fg_color=_POPUP_BG,
            corner_radius=T.RADIUS_SMALL,
            border_width=0,
        )
        body.pack(fill="both", expand=True, padx=1, pady=1)

        picker = TimePicker(
            body, value=self._value, command=self._on_scrolled, fg_color=_POPUP_BG
        )
        picker.pack(padx=8, pady=8)

        win.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        w = win.winfo_reqwidth()
        h = win.winfo_reqheight()
        if x + w > self.winfo_screenwidth():
            x = self.winfo_screenwidth() - w - 8
        if y + h > self.winfo_screenheight():
            y = self.winfo_rooty() - h - 4
        win.geometry(scaled_geometry(win, w, h, max(0, x), max(0, y)))
        round_window_corners(win, T.RADIUS_SMALL)

        win.focus_force()
        win.bind("<FocusOut>", lambda _e: self.after(80, self._close_if_outside))
        # grab 之后点主窗口会被重定向到弹层，靠这个关掉；否则无边框窗口
        # 拿不到可靠的 FocusOut，点旁边没反应。
        with contextlib.suppress(tk.TclError):
            win.grab_set()
        win.bind("<Button-1>", self._on_popup_click, add="+")
        self._win = win
        self._picker = picker
        self._anchor = (x, y)
        self._watch_job = self.after(_FOLLOW_MS, self._follow)

    def close(self) -> None:
        """关掉时间弹层。"""
        for job in (self._watch_job,):
            if job is not None:
                with contextlib.suppress(tk.TclError):
                    self.after_cancel(job)
        self._watch_job = None
        win, self._win = self._win, None
        self._picker = None
        if win is not None:
            with contextlib.suppress(tk.TclError):
                win.grab_release()
        if win is not None:
            with contextlib.suppress(tk.TclError):
                win.destroy()

    # --- 内部 ---
    def _on_click(self, _event: Any = None) -> None:
        """点箭头：只读时什么都不做。"""
        if not self._readonly:
            self.open()

    def _apply_readonly(self) -> None:
        """只读时文字压灰、光标换箭头；可编辑时三段能键入。"""
        color = T.COLOR_MUTED if self._readonly else T.COLOR_TEXT
        cursor = "arrow" if self._readonly else "xterm"
        state = "readonly" if self._readonly else "normal"
        for entry in (self._hour, self._minute, self._second):
            try:
                entry.configure(text_color=color, cursor=cursor, state=state)
            except (tk.TclError, ValueError):
                continue
        self._arrow.configure(
            text_color=T.COLOR_FAINT if self._readonly else T.COLOR_MUTED,
            cursor="arrow" if self._readonly else "hand2",
        )

    def _commit_typed(self, _event: Any = None) -> None:
        """回车或失焦：把三段文字解析成时间，越界夹回，坏值退回原样。"""
        if self._readonly:
            return
        try:
            hour = int(self._hour.get().strip() or 0)
            minute = int(self._minute.get().strip() or 0)
            second = int(self._second.get().strip() or 0)
        except (TypeError, ValueError):
            self._sync_text()
            return
        value = _dt.time(
            max(0, min(23, hour)),
            max(0, min(59, minute)),
            max(0, min(59, second)),
        )
        if value != self._value:
            self._value = value
            if self._command is not None:
                self._command(value)
        self._sync_text()

    def _segment(self) -> ctk.CTkEntry:
        entry = ctk.CTkEntry(
            self._box,
            width=30,
            height=28,
            fg_color="transparent",
            border_width=0,
            corner_radius=0,
            justify="center",
            font=get_font(T.FONT_BODY),
            text_color=T.COLOR_TEXT,
            state="readonly" if self._readonly else "normal",
        )
        entry.bind("<Key>", self._block_keys)
        return entry

    def _colon(self) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            self._box,
            text=":",
            width=8,
            text_color=T.COLOR_MUTED,
            font=get_font(T.FONT_BODY),
        )

    def _on_scrolled(self, value: _dt.time) -> None:
        """滚轮每滚一格就写回并回调。"""
        self._value = value
        self._sync_text()
        if self._command is not None:
            self._command(value)

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
                win.geometry(scaled_geometry(win, win.winfo_width(), win.winfo_height(), x, y))
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

    def _close_if_outside(self) -> None:
        """失焦后确认指针也离开了弹层，才关闭。"""
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

    def _block_keys(self, event: Any) -> Optional[str]:
        if not self._readonly:
            return None
        if event.char and event.char.isprintable():
            return "break"
        return None

    def _sync_text(self) -> None:
        readonly = self._readonly
        for entry, number in (
            (self._hour, self._value.hour),
            (self._minute, self._value.minute),
            (self._second, self._value.second),
        ):
            if readonly:
                entry.configure(state="normal")
            entry.delete(0, "end")
            entry.insert(0, f"{number:02d}")
            if readonly:
                entry.configure(state="readonly")
