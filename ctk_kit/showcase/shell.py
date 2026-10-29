"""各示例页共用的辅助函数与单页启动器。

页面模块只依赖这里和 ``ctk_kit`` 的公开组件，彼此之间不互相 import——想改
某一页时只看那一个文件就够了。
"""

from __future__ import annotations

import sys
import tkinter as tk
from typing import Callable

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.layout import card, hint_label
from ctk_kit.theme import apply_appearance, color_of

from .data import APP_TITLE

MARGIN_X = 24
MARGIN_TOP = 18
MARGIN_BOTTOM = 16


def _tone(value, dark: bool) -> str:
    """色值可能是 (浅色, 深色) 二元组，也可能是单色。"""
    if isinstance(value, (tuple, list)):
        return value[1] if dark else value[0]
    return value


def _text(master, text: str, *, font, color: str, bg: str, **kwargs) -> tk.Label:
    """原生 tk.Label 的薄封装：字体、颜色、底色三件套总是要一起写。"""
    return tk.Label(master, text=text, font=font, bg=bg, fg=color, **kwargs)


class Feedback:
    """页面底部的交互回显。

    ``count`` 记录回显过几次，方便确认按钮真的把动作传到了这里。
    """

    def __init__(self, label: ctk.CTkLabel):
        self.label = label
        self.count = 0

    def __call__(self, text: str) -> None:
        self.count += 1
        self.label.configure(text=text)

    def text(self) -> str:
        return self.label.cget("text")


def _feedback(page, text: str = "等待交互…") -> Feedback:
    """把反馈条挂在页面底部；先于内容 pack，内容再多也不会把它挤掉。"""
    bar = ctk.CTkFrame(page, fg_color="transparent")
    bar.pack(side="bottom", fill="x", pady=(8, 0))
    label = hint_label(bar, text)
    label.pack(fill="x")
    feedback = Feedback(label)
    page.feedback = feedback
    return feedback


def _card_shell(master) -> ctk.CTkFrame:
    return card(master)


def _card_body(box: ctk.CTkFrame) -> tk.Frame:
    """卡片里放原生控件，背景与卡片同色才不会露出缝隙。"""
    body = tk.Frame(box, bg=color_of(T.COLOR_CARD))
    body.pack(fill="both", expand=True, padx=16, pady=14)
    return body


def _row(body, bg: str) -> tk.Frame:
    row = tk.Frame(body, bg=bg)
    row.pack(fill="x", pady=(0, 8))
    return row


def run_page(
    factory: Callable[[ctk.CTk], ctk.CTkFrame],
    title: str,
    *,
    width: int = 1180,
    height: int = 780,
) -> int:
    """单独启动一个示例页。

    每个页面模块末尾都有一行 ``python -m ctk_kit.showcase.pages.<名字>`` 的
    用法说明；改完某一页只跑这一个文件即可，不用打开整个窗口。

    参数:
        factory: 接收根窗口、返回填好内容的 ``CTkFrame``。
        title: 页面名，拼进窗口标题。
        width: 初始窗口宽。
        height: 初始窗口高。

    返回:
        进程退出码，恒为 ``0``。
    """
    apply_appearance("dark")
    app = ctk.CTk()
    app.title(f"{APP_TITLE} · {title}")
    app.configure(fg_color=T.COLOR_BG)
    app.update_idletasks()
    left = max(0, (app.winfo_screenwidth() - width) // 2)
    top = max(0, (app.winfo_screenheight() - height) // 2)
    app.geometry(f"{width}x{height}+{left}+{top}")
    app.minsize(720, 520)

    page = factory(app)
    page.pack(
        fill="both",
        expand=True,
        padx=MARGIN_X,
        pady=(MARGIN_TOP, MARGIN_BOTTOM),
    )

    if "--topmost" in sys.argv:
        app.attributes("-topmost", True)
    if "--where" in sys.argv:
        # 调试用：打印窗口矩形后退出，便于外部截图
        def report() -> None:
            print(
                f"{app.winfo_rootx()},{app.winfo_rooty()},"
                f"{app.winfo_width()},{app.winfo_height()}",
                flush=True,
            )
            app.destroy()

        app.after(900, report)

    app.mainloop()
    return 0
