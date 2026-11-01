"""卡片底部的「查看实现」面板：折叠标题 + 只读代码块 + 一句说明。

示例页里每个卡片都带一个这样的面板，之前每页各复制一份辅助函数；这里
收成一个公开组件，页面只写一行::

    from ctk_kit import CodePanel

    CodePanel(card, CODE, "这段代码的说明")
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

from . import tokens as T
from .collapse import Collapsible
from .layout import HintLabel
from .text import TextArea

__all__ = ["CodePanel"]

#: 代码块字体：等宽，比正文大一点，展开后不用凑近看。
CODE_FONT = ("Consolas", 15)


class CodePanel(Collapsible):
    """可折叠的「查看实现」面板。

    参数:
        master: 父容器，通常是卡片。
        code: 面板展开后显示的代码。
        note: 代码下面的一句说明，空字符串表示不要。
        collapsed_text: 收起时标题栏的文字，默认「查看实现」。
        expanded_text: 展开时标题栏的文字，默认「收起实现」。
        **kwargs: 其余参数交给 ``Collapsible``。

    面板构造时自动 ``pack(fill="x", pady=(6, 4), padx=(3, 3))``，调用方
    不用再摆位；代码块是只读 ``TextArea``，字体与行距在内部统一。
    """

    def __init__(
        self,
        master: tk.Misc,
        code: str,
        note: str = "",
        *,
        collapsed_text: str = "查看实现",
        expanded_text: str = "收起实现",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            master,
            collapsed_text=collapsed_text,
            expanded_text=expanded_text,
            **kwargs,
        )
        self.pack(fill="x", pady=(6, 4), padx=(3, 3))

        lines = code.splitlines() or [""]
        self.view = TextArea(
            self.body,
            height=min(30 + len(lines) * 24, 640),
            readonly=True,
            show_counter=False,
            bg_color=T.COLOR_INPUT,
        )
        self.view.textbox.configure(font=CODE_FONT)
        # CTkTextbox 没暴露行距，直接给里面的 tk.Text 加一点呼吸空间
        self.view.textbox._textbox.configure(spacing1=4, spacing2=4, spacing3=4)
        self.view.set(code)
        self.view.pack(fill="x", padx=12, pady=(12, 6 if note else 12))
        if note:
            HintLabel(self.body, note).pack(fill="x", padx=12, pady=(0, 12))
