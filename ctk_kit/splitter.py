"""可拖动分栏：左右（或上下）两块，中间一根手柄。

用法::

    from ctk_kit import Splitter

    split = Splitter(card, initial=0.35, min_size=120)
    split.pack(fill="both", expand=True)

    CTkLabel(split.first, text="目录").pack()
    CTkLabel(split.second, text="内容").pack()

``first`` / ``second`` 是两个内容容器；拖动中间手柄改变比例，两边都不会
小于 ``min_size``。``orientation="vertical"`` 改成上下分栏。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional

import customtkinter as ctk

from . import tokens as T

__all__ = ["Splitter"]

RatioCommand = Optional[Callable[[float], None]]


class Splitter(ctk.CTkFrame):
    """两栏分隔容器。

    参数:
        master: 父容器。
        orientation: ``horizontal`` 左右分栏，``vertical`` 上下分栏。
        initial: 初始比例（0–1），默认 0.5。
        min_size: 每一边的最小像素，默认 80。
        handle: 手柄厚度，默认 6。
        command: 拖动结束时的回调，参数是当前比例。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        set_ratio(ratio, notify=False): 按比例重新分栏。
        get_ratio(): 当前比例。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        orientation: str = "horizontal",
        initial: float = 0.5,
        min_size: int = 80,
        handle: int = 6,
        command: RatioCommand = None,
        **kwargs: Any,
    ) -> None:
        """建分栏；``initial`` 会夹到允许范围内。"""
        super().__init__(master, fg_color="transparent", **kwargs)

        self._horizontal = orientation != "vertical"
        self._ratio = max(0.0, min(1.0, initial))
        self._min = min_size
        self._handle_size = handle
        self._command = command

        self.first = ctk.CTkFrame(self, fg_color="transparent")
        self.second = ctk.CTkFrame(self, fg_color="transparent")

        self._handle = ctk.CTkFrame(
            self,
            fg_color=T.COLOR_BORDER,
            width=handle,
            height=handle,
            corner_radius=handle // 2,
        )
        self._handle.configure(
            cursor="sb_h_double_arrow" if self._horizontal else "sb_v_double_arrow"
        )

        self.bind("<Configure>", lambda _e: self._layout())
        self._handle.bind("<Button-1>", self._start)
        self._handle.bind("<B1-Motion>", self._drag)
        self._handle.bind("<ButtonRelease-1>", self._release)

    # --- 对外 ---
    def set_ratio(self, ratio: float, notify: bool = False) -> None:
        """按比例分栏；``notify=True`` 时也回调。"""
        self._ratio = self._clamp(ratio)
        self._layout()
        if notify and self._command is not None:
            self._command(self._ratio)

    def get_ratio(self) -> float:
        """当前比例。"""
        return self._ratio

    # --- 内部 ---
    def _clamp(self, ratio: float) -> float:
        """按最小像素夹住比例。"""
        total = self.winfo_width() if self._horizontal else self.winfo_height()
        if total <= 0:
            return max(0.0, min(1.0, ratio))
        limit = min(0.5, self._min / total)
        return max(limit, min(1.0 - limit, ratio))

    def _layout(self) -> None:
        """按比例摆两个内容和手柄。"""
        total_w = self.winfo_width()
        total_h = self.winfo_height()
        if total_w <= 1 or total_h <= 1:
            return
        half = self._handle_size // 2
        if self._horizontal:
            pos = int(total_w * self._ratio)
            self.first.configure(width=max(1, pos - half), height=total_h)
            self.first.place(x=0, y=0)
            self._handle.configure(width=self._handle_size, height=total_h)
            self._handle.place(x=max(0, pos - half), y=0)
            self.second.configure(
                width=max(1, total_w - pos - half), height=total_h
            )
            self.second.place(x=pos + half, y=0)
        else:
            pos = int(total_h * self._ratio)
            self.first.configure(width=total_w, height=max(1, pos - half))
            self.first.place(x=0, y=0)
            self._handle.configure(width=total_w, height=self._handle_size)
            self._handle.place(x=0, y=max(0, pos - half))
            self.second.configure(
                width=total_w, height=max(1, total_h - pos - half)
            )
            self.second.place(x=0, y=pos + half)

    def _start(self, _event: tk.Event) -> None:
        """按住手柄。"""
        self._handle.configure(fg_color=T.COLOR_ACTIVE)

    def _drag(self, event: tk.Event) -> None:
        """拖动时实时分栏。"""
        total = self.winfo_width() if self._horizontal else self.winfo_height()
        if total <= 0:
            return
        # 手柄上的 event.x 是相对手柄自己的坐标，只有 0..handle 宽；
        # 换算成相对分栏容器的位置，否则一拖就跳回最左边。
        if self._horizontal:
            pos = event.x_root - self.winfo_rootx()
        else:
            pos = event.y_root - self.winfo_rooty()
        self._ratio = self._clamp(pos / total)
        self._layout()

    def _release(self, _event: tk.Event) -> None:
        """松手：恢复手柄颜色并回调。"""
        self._handle.configure(fg_color=T.COLOR_BORDER)
        if self._command is not None:
            self._command(self._ratio)
