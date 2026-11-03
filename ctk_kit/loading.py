"""启动遮罩：大 logo、一行进度说明和一条细进度条。

用法::

    splash = LoadingOverlay(app, title="ctk-kit")
    app.update()
    nav.rebuilder.build_all(progress=splash.set_progress)
    splash.finish()

遮罩直接 ``place`` 在父容器上，不需要额外的 ``Toplevel``；构建期间它
盖住整个内容区，建完 ``finish()`` 销毁即可。
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional

import customtkinter as ctk

from . import tokens as T
from .branding import logo_path
from .fonts import get_font

__all__ = ["LoadingOverlay"]


class LoadingOverlay(ctk.CTkFrame):
    """铺满父容器的启动遮罩。

    参数:
        master: 要盖住的容器，通常是 ``App``。
        title: logo 下方的标题，默认 ``"ctk-kit"``。
        message: 初始说明文字，默认 ``"正在加载…"``。
        logo_size: logo 边长（逻辑像素），默认 96。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str = "ctk-kit",
        message: str = "正在加载…",
        logo_size: int = 96,
    ) -> None:
        super().__init__(master, fg_color=T.COLOR_BG, corner_radius=0)
        self._title = title

        self._logo_image: Optional[ctk.CTkImage] = None
        try:
            from PIL import Image

            image = Image.open(logo_path(logo_size)).convert("RGBA")
            self._logo_image = ctk.CTkImage(
                light_image=image, dark_image=image, size=(logo_size, logo_size)
            )
        except (OSError, ImportError):
            self._logo_image = None

        if self._logo_image is not None:
            self._logo = ctk.CTkLabel(
                self,
                text="",
                image=self._logo_image,
                fg_color="transparent",
            )
            self._logo.place(relx=0.5, rely=0.38, anchor="center")

        self._title_label = ctk.CTkLabel(
            self,
            text=title,
            font=get_font((T.FONT_NAME, 22, "bold")),
            text_color=T.COLOR_TEXT,
            fg_color="transparent",
        )
        self._title_label.place(relx=0.5, rely=0.505, anchor="center")

        self._message = ctk.CTkLabel(
            self,
            text=message,
            font=get_font(T.FONT_SMALL),
            text_color=T.COLOR_MUTED,
            fg_color="transparent",
        )
        self._message.place(relx=0.5, rely=0.555, anchor="center")

        self._bar = ctk.CTkProgressBar(
            self,
            height=4,
            corner_radius=2,
            fg_color=T.COLOR_SOFT,
            progress_color=T.COLOR_ACCENT,
        )
        self._bar.place(relx=0.5, rely=0.60, anchor="center", relwidth=0.26)
        self._bar.set(0)

        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()

    def set_progress(self, done: int, total: int, name: str = "") -> None:
        """更新进度；``name`` 是刚建完的页面名。

        构建期间 Tk 是单线程的，``after`` 补间动画跑不起来，进度条会停在
        旧值上（看起来像最后一页卡住 30%）。这里直接跳到准确比例，等
        ``finish()`` 再停一帧撤掉。
        """
        ratio = done / total if total else 0
        try:
            text = f"正在加载 {name}" if name else self._title
            self._message.configure(text=f"{text}  {done}/{total}")
            self._bar.set(ratio)
            self.update_idletasks()
        except tk.TclError:
            return

    def finish(self) -> None:
        """构建完成，撤掉遮罩。

        先让进度条停在满格一小会儿，避免最后一步还差一截就消失。
        """
        try:
            self._bar.set(1.0)
            self.update_idletasks()
            self.after(120, self.destroy)
        except tk.TclError:
            pass
