"""骨架屏：加载中的占位条，默认缓慢呼吸。

用法::

    from ctk_kit import Skeleton

    Skeleton(card, width=240, height=14)
    Skeleton(card, width=160, height=14, animated=False)   # 静态占位

放在要出现文字 / 图片的位置，数据回来后再换成真实控件。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Optional

import customtkinter as ctk

from . import tokens as T

__all__ = ["Skeleton"]


class Skeleton(ctk.CTkFrame):
    """圆角占位条。

    参数:
        master: 父容器。
        width / height: 占位尺寸（逻辑像素）。
        radius: 圆角，默认 6；传 ``None`` 用高度的一半（胶囊形）。
        animated: 是否呼吸，默认 ``True``。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        start(): 开始呼吸。
        stop(): 停在当前颜色。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        width: int = 200,
        height: int = 12,
        radius: Optional[int] = 6,
        animated: bool = True,
        **kwargs: Any,
    ) -> None:
        """建占位条；``animated=False`` 时不启动定时器。"""
        super().__init__(
            master,
            width=width,
            height=height,
            fg_color=T.COLOR_SOFT,
            corner_radius=height // 2 if radius is None else radius,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._running = False
        self._job: Any = None
        self._bright = False

        if animated:
            self.start()

    # --- 对外 ---
    def start(self) -> None:
        """开始呼吸；重复调用没有副作用。"""
        if self._running:
            return
        self._running = True
        self._tick()

    def stop(self) -> None:
        """停在当前颜色，取消定时器。"""
        self._running = False
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:  # noqa: BLE001 - 控件可能已经销毁
                pass
            self._job = None

    # --- 内部 ---
    def _tick(self) -> None:
        """两种底色之间来回换，慢一点更像呼吸。"""
        if not self._running or not self.winfo_exists():
            return
        self._bright = not self._bright
        self.configure(
            fg_color=T.COLOR_SOFT_HOVER if self._bright else T.COLOR_SOFT
        )
        self._job = self.after(650, self._tick)

    def destroy(self) -> None:
        """销毁前先停掉定时器。"""
        self.stop()
        super().destroy()
