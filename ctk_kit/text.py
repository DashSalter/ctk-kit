"""大文本组件：带占位符、字数统计与只读模式的多行输入区。

``CTkTextbox`` 自身没有占位符，只读状态也要调用方自己管 ``state``；
``TextArea`` 把这两件事连同字数统计包成一个可直接摆位的整体：

- 占位符：没有内容且失焦时显示灰色占位文字，聚焦或输入后自动让位
- 字数：底部一行 ``N 字 · M 行``，``show_counter=False`` 可关掉
- 只读：``readonly=True`` 时禁止编辑，``set_readonly()`` 可随时切换
- ``on_change``：键盘输入或 ``set()`` 之后回调最新全文

所有颜色、字体、圆角都取自 ``tokens``，切换深浅色不需要额外处理。

工厂只返回控件，不负责摆位::

    area = TextArea(frame, placeholder="写点什么…", on_change=print)
    area.pack(fill="both", expand=True)
    area.set("第一行\\n第二行")
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional

import customtkinter as ctk

from . import tokens as T

# 内容变化回调：收到最新的全文（空文本时是空字符串）。
ChangeHandler = Optional[Callable[[str], None]]


class TextArea(ctk.CTkFrame):
    """多行文本输入区，附带占位符、字数统计与只读模式。"""

    def __init__(
        self,
        master: tk.Misc,
        *,
        placeholder: str = "",
        height: int = 200,
        readonly: bool = False,
        show_counter: bool = True,
        on_change: ChangeHandler = None,
        bg_color: Any = None,
        text_color: Any = None,
        **kwargs: Any,
    ) -> None:
        """创建文本区。

        参数:
            master: 父容器。
            placeholder: 没有内容时显示的灰色占位文字，空字符串表示不要占位符。
            height: 文本区高度（像素），默认 200；状态栏另算。
            readonly: 是否只读（禁止编辑，仍可选中与复制）。
            show_counter: 是否在底部显示字数统计，默认 True。
            on_change: 内容变化时的回调，参数是当前全文。
            bg_color: 文本区底色（颜色元组或 ``"transparent"``），默认用输入框底色
                ``COLOR_INPUT``。放在卡片里当日志显示时，传 ``COLOR_CARD`` 或
                ``"transparent"`` 就不会比周围亮一截。
            text_color: 正文颜色，默认 ``COLOR_TEXT``。
            **kwargs: 透传给外层 ``CTkFrame`` 的参数。
        """
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._placeholder = placeholder
        self._placeholder_active = False
        self._readonly = bool(readonly)
        self._on_change = on_change
        self._text_color: Any = text_color if text_color is not None else T.COLOR_TEXT

        self.textbox = ctk.CTkTextbox(
            self,
            height=height,
            corner_radius=T.RADIUS_MEDIUM,
            border_width=1,
            border_color=T.COLOR_BORDER,
            fg_color=bg_color if bg_color is not None else T.COLOR_INPUT,
            text_color=self._text_color,
            font=T.FONT_BODY,
            wrap="word",
        )
        self.textbox.pack(fill="both", expand=True)
        self.textbox.bind("<FocusIn>", self._handle_focus_in)
        self.textbox.bind("<FocusOut>", self._handle_focus_out)
        self.textbox.bind("<KeyRelease>", lambda _event: self._refresh())

        self.counter = ctk.CTkLabel(
            self,
            text="0 字",
            anchor="e",
            font=T.FONT_TINY,
            text_color=T.COLOR_FAINT,
        )
        if show_counter:
            self.counter.pack(fill="x", pady=(T.SPACE_XS, 0))

        if self._placeholder:
            self._show_placeholder()
        self._apply_readonly_state()
        self._refresh(notify=False)

    # ------------------------------------------------------------ 读写
    def get(self) -> str:
        """返回当前全文；占位符显示中时返回空字符串。"""
        if self._placeholder_active:
            return ""
        return self.textbox.get("1.0", "end-1c")

    def set(self, text: str) -> None:
        """整体替换内容；传空字符串会恢复占位符。"""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        if text:
            self.textbox.insert("1.0", text)
            self._placeholder_active = False
            self.textbox.configure(text_color=self._text_color)
        elif self._placeholder:
            self._show_placeholder()
        else:
            self._placeholder_active = False
            self.textbox.configure(text_color=self._text_color)
        self._apply_readonly_state()
        self._refresh()

    def clear(self) -> None:
        """清空内容，等价于 ``set("")``。"""
        self.set("")

    # ------------------------------------------------------------ 只读
    @property
    def readonly(self) -> bool:
        """当前是否处于只读状态。"""
        return self._readonly

    def set_readonly(self, value: bool) -> None:
        """切换只读状态。"""
        self._readonly = bool(value)
        self._apply_readonly_state()

    # ------------------------------------------------------------ 内部
    def _apply_readonly_state(self) -> None:
        self.textbox.configure(state="disabled" if self._readonly else "normal")

    def _show_placeholder(self) -> None:
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", self._placeholder)
        self.textbox.configure(text_color=T.COLOR_FAINT)
        self._placeholder_active = True
        self._apply_readonly_state()

    def _clear_placeholder(self) -> None:
        self.textbox.delete("1.0", "end")
        self.textbox.configure(text_color=self._text_color)
        self._placeholder_active = False

    def _handle_focus_in(self, _event: Any) -> None:
        # 只读时保留占位符：它不是可编辑内容，不该因为聚焦就消失
        if self._placeholder_active and not self._readonly:
            self._clear_placeholder()

    def _handle_focus_out(self, _event: Any) -> None:
        if self._placeholder_active:
            return
        if not self.textbox.get("1.0", "end-1c") and self._placeholder:
            self._show_placeholder()
            self._refresh()

    def _refresh(self, notify: bool = True) -> None:
        text = self.get()
        if text:
            lines = text.count("\n") + 1
            self.counter.configure(text=f"{len(text)} 字 · {lines} 行")
        else:
            self.counter.configure(text="0 字")
        if notify and self._on_change is not None:
            self._on_change(text)
