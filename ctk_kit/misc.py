"""杂项控件：多种样式的进度条。

``Progress`` 比 ``inputs.ProgressBar`` 多几种形态：分格、带百分比文字、
不确定态（来回滚动的动画）。连续条的外观和 ``ProgressBar`` 保持一致。
"""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Optional

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font


class Progress(ctk.CTkFrame):
    """进度条：连续 / 分格 / 带百分比文字 / 不确定态。

    整块是一个透明容器，左边是条本身，右边按需放百分比文字。
    条高、圆角都跟着 ``height`` 走；``steps>0`` 时画成一格一格。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        value: float = 0.0,
        width: int = 240,
        height: int = 8,
        steps: int = 0,
        show_text: bool = False,
        color: Optional[str] = None,
        track: Optional[str] = None,
    ) -> None:
        """创建进度条。

        参数:
            master: 父容器。
            value: 初始进度，0~1。
            width: 整行宽度（含右侧文字），默认 240。
            height: 条本身的高度（像素），默认 8。
            steps: 大于 0 时分格显示，格子数就是它。
            show_text: 右侧是否显示百分比文字。
            color: 已完成部分的颜色，默认主色（``COLOR_ACTIVE``）。
            track: 轨道颜色，默认 ``COLOR_BORDER_STRONG``。
        """
        super().__init__(master, fg_color="transparent", width=width)
        self._value = max(0.0, min(1.0, float(value)))
        self._steps = max(0, int(steps))
        self._height = max(4, int(height))
        self._color = color or T.COLOR_ACTIVE
        self._track_color = track or T.COLOR_BORDER_STRONG
        self._segments: list = []
        self._fill: Optional[ctk.CTkFrame] = None
        self._label: Optional[ctk.CTkLabel] = None
        self._anim_job: Optional[str] = None
        self._anim_pos = 0.0

        row = ctk.CTkFrame(self, fg_color="transparent", height=self._height)
        row.pack(fill="x", expand=True)
        row.pack_propagate(False)

        if show_text:
            self._label = ctk.CTkLabel(
                row,
                text="0%",
                width=46,
                anchor="e",
                font=get_font(T.FONT_SMALL),
                text_color=T.COLOR_MUTED,
                fg_color="transparent",
            )
            self._label.pack(side="right", padx=(8, 0))

        self._track = ctk.CTkFrame(
            row,
            height=self._height,
            fg_color=T.COLOR_BORDER_STRONG if track is None else track,
            corner_radius=self._height // 2,
        )
        self._track.pack(side="left", fill="x", expand=True)
        self._track.pack_propagate(False)

        if self._steps:
            for index in range(self._steps):
                cell = ctk.CTkFrame(
                    self._track,
                    fg_color="transparent",
                    corner_radius=max(2, self._height // 2 - 1),
                )
                cell.place(
                    relx=index / self._steps,
                    rely=0,
                    relwidth=1 / self._steps - 0.012,
                    relheight=1,
                )
                self._segments.append(cell)
        else:
            self._fill = ctk.CTkFrame(
                self._track,
                fg_color=self._color,
                corner_radius=self._height // 2,
            )
            self._fill.place(relx=0, rely=0, relheight=1, relwidth=0.001)

        self._render()

    # ------------------------------------------------------------ 读写
    def get(self) -> float:
        """当前进度（0~1）。"""
        return self._value

    def set(self, value: float) -> None:
        """写入进度；会先夹到 0~1，再按当前形态重画。"""
        self._value = max(0.0, min(1.0, float(value)))
        self._render()

    # ------------------------------------------------------------ 外观
    def _render(self) -> None:
        """按当前值和形态重画。"""
        if self._label is not None:
            self._label.configure(text=f"{round(self._value * 100)}%")
        if self._steps:
            filled = self._value * self._steps
            for index, cell in enumerate(self._segments):
                # 整格已达标才点亮；最后一格按比例半亮用透明度做不了，直接整格
                color = self._color if index < round(filled) else "transparent"
                cell.configure(fg_color=color)
            return
        if self._fill is not None:
            self._fill.place_configure(relwidth=max(0.001, self._value))

    # ------------------------------------------------------------ 不确定态
    def start_indeterminate(self) -> None:
        """切成不确定态：一段色块在轨道里来回滚，用来表示「不知道还要多久」。"""
        if self._steps or self._fill is None or self._anim_job is not None:
            return
        self._anim_pos = -0.3
        self._animate()

    def stop_indeterminate(self) -> None:
        """退出不确定态，回到按 ``value`` 显示。"""
        if self._anim_job is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._anim_job)
            self._anim_job = None
        if self._fill is not None:
            self._fill.place_configure(relx=0, relwidth=max(0.001, self._value))
        self._render()

    @property
    def animating(self) -> bool:
        """当前是不是在跑不确定态动画。"""
        return self._anim_job is not None

    def _animate(self) -> None:
        """一帧：把 30% 宽的色块往右推，出界后从左边重新进来。"""
        if self._fill is None:
            return
        self._anim_pos += 0.02
        if self._anim_pos > 1.0:
            self._anim_pos = -0.3
        self._fill.place_configure(relx=max(0.0, self._anim_pos), relwidth=0.3)
        self._anim_job = self.after(30, self._animate)

    def destroy(self) -> None:
        """销毁前先停掉动画，避免 after 回调打到已销毁的控件上。"""
        if self._anim_job is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._anim_job)
            self._anim_job = None
        super().destroy()
