"""卡片底部的「查看实现」面板：折叠标题 + 只读代码块 + 一句说明。

示例页里每个卡片都带一个这样的面板，之前每页各复制一份辅助函数；这里
收成一个公开组件，页面只写一行::

    from ctk_kit import CodePanel

    CodePanel(card, CODE, "这段代码的说明")

代码块不是构造时就建：面板收起时只保留标题行，第一次展开才创建
``TextArea`` 并填入代码。一页好几个卡片时，能省掉大半的控件创建。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Optional

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
    不用再摆位；代码块是只读 ``TextArea``，字体与行距在内部统一。代码块
    在第一次展开时才创建，收起状态下 ``view`` 为 ``None``。
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
        """建折叠面板；代码块留到第一次展开时再创建。"""
        super().__init__(
            master,
            collapsed_text=collapsed_text,
            expanded_text=expanded_text,
            on_toggle=self._on_toggle,
            **kwargs,
        )
        self.pack(fill="x", pady=(6, 4), padx=(3, 3))

        self._code = code
        self._note = note
        self._note_label: Optional[HintLabel] = None
        self.view: Optional[TextArea] = None
        # 构造时就是展开态（expanded=True）的话，直接建出来
        if self.expanded:
            self._build_view()

    def set_code(self, code: str) -> None:
        """换掉面板里的代码；已经展开时立刻刷新显示。"""
        self._code = code
        if self.view is not None:
            self.view.set(code)

    def set_note(self, note: str) -> None:
        """换掉代码下面那句说明；空字符串表示不要说明。"""
        self._note = note
        if self._note_label is not None:
            self._note_label.configure(text=note)

    def _on_toggle(self, expanded: bool) -> None:
        """展开时补建代码块；收起时保留已有控件，下次展开直接复用。"""
        if expanded:
            self._build_view()

    def _build_view(self) -> None:
        """第一次展开时创建代码块；重复调用无副作用。"""
        if self.view is not None:
            return
        lines = self._code.splitlines() or [""]
        view = TextArea(
            self.body,
            height=min(30 + len(lines) * 24, 640),
            readonly=True,
            show_counter=False,
            bg_color=T.COLOR_INPUT,
        )
        view.textbox.configure(font=CODE_FONT)
        # CTkTextbox 没暴露行距，直接给里面的 tk.Text 加一点呼吸空间
        view.textbox._textbox.configure(spacing1=4, spacing2=4, spacing3=4)
        view.set(self._code)
        view.pack(fill="x", padx=12, pady=(12, 6 if self._note else 12))
        if self._note:
            self._note_label = HintLabel(self.body, self._note)
            self._note_label.pack(fill="x", padx=12, pady=(0, 12))
        self.view = view
