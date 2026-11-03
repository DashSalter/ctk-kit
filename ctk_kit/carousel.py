"""轮播：一次显示一张卡片，左右箭头或底部圆点切换。

用法::

    from ctk_kit import Carousel

    Carousel(card, items=[
        ("更快", "页面切换不再重建整个窗口"),
        ("更轻", "组件按需创建，内存占用更小"),
        ("更稳", "统一了主题和缩放处理"),
    ], height=180)

``items`` 每项是 ``(标题, 说明)``；传 ``autoplay=3000`` 会自动轮播。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, List, Optional, Sequence, Tuple

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font

__all__ = ["Carousel"]

SlideCommand = Optional[Callable[[int], None]]


class Carousel(ctk.CTkFrame):
    """卡片式轮播。

    参数:
        master: 父容器。
        items: 每项 ``(标题, 说明)``，或只给标题字符串。
        height: 展示区高度，默认 180。
        autoplay: 自动切换间隔（毫秒）；0 表示不自动。
        command: 切换回调，参数是当前下标（0 开始）。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        show(index, notify=True): 跳到某一张。
        next() / prev(): 下一张 / 上一张。
        start() / stop(): 开 / 关自动轮播。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        items: Sequence[Any] = (),
        height: int = 180,
        autoplay: int = 0,
        command: SlideCommand = None,
        **kwargs: Any,
    ) -> None:
        """建轮播；``items`` 为空时只显示空壳。"""
        super().__init__(master, fg_color="transparent", **kwargs)

        self._items: List[Tuple[str, str]] = [
            self._normalize(item) for item in items
        ]
        self._index = 0
        self._autoplay = autoplay
        self._command = command
        self._job: Any = None

        self._stage = ctk.CTkFrame(
            self,
            fg_color=T.COLOR_SOFT,
            corner_radius=T.RADIUS_MEDIUM,
            height=height,
        )
        self._stage.pack(fill="x")
        self._stage.pack_propagate(False)

        body = ctk.CTkFrame(self._stage, fg_color="transparent")
        body.place(relx=0.5, rely=0.5, anchor="center")
        self._title = ctk.CTkLabel(
            body,
            text="",
            font=get_font(T.FONT_TITLE),
            text_color=T.COLOR_TEXT,
        )
        self._title.pack()
        self._text = ctk.CTkLabel(
            body,
            text="",
            font=get_font(T.FONT_BODY),
            text_color=T.COLOR_MUTED,
            wraplength=360,
            justify="center",
        )
        self._text.pack(pady=(6, 0))

        self._counter = ctk.CTkLabel(
            self._stage,
            text="",
            font=get_font(T.FONT_TINY),
            text_color=T.COLOR_FAINT,
        )
        self._counter.place(relx=1.0, rely=1.0, x=-10, y=-8, anchor="se")

        for text, side, relx, x in (
            ("‹", "left", 0.0, 10),
            ("›", "right", 1.0, -10),
        ):
            ctk.CTkButton(
                self._stage,
                text=text,
                width=32,
                height=32,
                corner_radius=16,
                fg_color=T.COLOR_CARD,
                hover_color=T.COLOR_SOFT_HOVER,
                text_color=T.COLOR_TEXT,
                font=get_font((T.FONT_NAME, 18, "bold")),
                command=self.prev if side == "left" else self.next,
            ).place(relx=relx, rely=0.5, x=x, anchor="w" if side == "left" else "e")

        self._dots = ctk.CTkFrame(self, fg_color="transparent")
        self._dots.pack(pady=(8, 0))

        self._render_dots()
        self.show(0, notify=False)

    # --- 对外 ---
    def show(self, index: int, notify: bool = True) -> None:
        """跳到 ``index``（会对总数取模）。"""
        if not self._items:
            return
        self._index = int(index) % len(self._items)
        title, text = self._items[self._index]
        self._title.configure(text=title)
        self._text.configure(text=text)
        self._counter.configure(text=f"{self._index + 1} / {len(self._items)}")
        self._render_dots()
        if notify and self._command is not None:
            self._command(self._index)
        self._schedule()

    def next(self) -> None:
        """下一张。"""
        self.show(self._index + 1)

    def prev(self) -> None:
        """上一张。"""
        self.show(self._index - 1)

    def start(self) -> None:
        """开始自动轮播。"""
        self._schedule()

    def stop(self) -> None:
        """停止自动轮播。"""
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:  # noqa: BLE001
                pass
            self._job = None

    # --- 内部 ---
    def _normalize(self, raw: Any) -> Tuple[str, str]:
        """字符串或 ``(标题, 说明)`` 统一成二元组。"""
        if isinstance(raw, str):
            return raw, ""
        values = list(raw) + [""]
        return str(values[0]), str(values[1])

    def _render_dots(self) -> None:
        """底部圆点：当前一个是主色。"""
        for child in self._dots.winfo_children():
            child.destroy()
        for index in range(len(self._items)):
            ctk.CTkButton(
                self._dots,
                text="",
                width=8,
                height=8,
                corner_radius=4,
                fg_color=T.COLOR_ACTIVE if index == self._index else T.COLOR_BORDER_STRONG,
                hover_color=T.COLOR_ACTIVE_HOVER,
                command=lambda i=index: self.show(i),
            ).pack(side="left", padx=3)

    def _schedule(self) -> None:
        """重排自动轮播定时器。"""
        self.stop()
        if self._autoplay > 0:
            self._job = self.after(self._autoplay, self._tick)

    def _tick(self) -> None:
        """定时器到点，下一张。"""
        self._job = None
        if self._autoplay > 0 and self._items:
            self.show(self._index + 1)

    def destroy(self) -> None:
        """销毁前停掉定时器。"""
        self.stop()
        super().destroy()
