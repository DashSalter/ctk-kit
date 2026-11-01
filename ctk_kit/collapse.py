"""可展开面板：一行标题 + 折叠起来的内容。

点击标题那一行，内容向下展开；再点一次收起。标题文字两个状态都能改，
展开/收起的回调里能拿到当前状态，用来做「记住上次展开过」这类事。

单独用::

    panel = Collapsible(card, collapsed_text="显示代码", expanded_text="隐藏代码")
    panel.pack(fill="x")
    TextArea(panel.body, readonly=True).pack(fill="x", padx=12, pady=12)

``Collapsible`` 自己不画边框、自己不做背景，放进任何卡片都不会把原来的
排版挤乱；内容区 ``body`` 才是需要往里塞东西的地方。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional

import customtkinter as ctk

from . import tokens as T

ToggleCommand = Optional[Callable[[bool], None]]

_EXPANDED_ARROW = "▲"
_COLLAPSED_ARROW = "▼"


class Collapsible(ctk.CTkFrame):
    """可展开的面板：标题行常驻，内容区按需显示。

    参数:
        master: 父容器。
        collapsed_text: 收起时的标题文字，默认「显示代码」。
        expanded_text: 展开时的标题文字，默认「隐藏代码」。
        expanded: 初始是否展开，默认收起。
        button_height: 标题行高度（像素），默认 36。
        on_toggle: 展开状态变化回调，参数是新的状态（``True`` 为已展开）。
        **kwargs: 透传给外层 ``CTkFrame``。

    属性:
        body: 内容容器，往这里 pack 子控件。
        button: 标题那一行的 ``CTkButton``，想换字号/颜色可以直接改。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        collapsed_text: str = "显示代码",
        expanded_text: str = "隐藏代码",
        expanded: bool = False,
        button_height: int = 36,
        on_toggle: ToggleCommand = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._collapsed_text = collapsed_text
        self._expanded_text = expanded_text
        self._on_toggle = on_toggle
        self._expanded = bool(expanded)

        self.button = ctk.CTkButton(
            self,
            text="",
            height=button_height,
            corner_radius=T.RADIUS_SMALL,
            font=T.FONT_SMALL,
            fg_color="transparent",
            hover_color=T.COLOR_HOVER_FAINT,
            text_color=T.COLOR_ACCENT,
            text_color_disabled=T.COLOR_FAINT,
            command=self.toggle,
        )
        self.button.pack(fill="x")

        self.body = ctk.CTkFrame(
            self,
            fg_color=T.COLOR_SOFT,
            corner_radius=T.RADIUS_SMALL,
        )

        self._sync_text()
        if self._expanded:
            self.body.pack(fill="x", pady=(6, 0))

    # --- 对外 ---
    @property
    def expanded(self) -> bool:
        """当前是否展开。"""
        return self._expanded

    def expand(self) -> None:
        """展开；已经展开时什么也不做。"""
        self.set_expanded(True)

    def collapse(self) -> None:
        """收起；已经收起时什么也不做。"""
        self.set_expanded(False)

    def toggle(self) -> None:
        """切换展开状态。"""
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded: bool) -> None:
        """直接设置展开状态，状态没变就不回调。"""
        expanded = bool(expanded)
        if expanded == self._expanded:
            return
        self._expanded = expanded
        self._sync_text()
        if expanded:
            self.body.pack(fill="x", pady=(6, 0))
        else:
            self.body.pack_forget()
        if self._on_toggle is not None:
            self._on_toggle(expanded)

    def set_texts(self, *, collapsed_text: str, expanded_text: str) -> None:
        """换掉两个状态的标题文字（当前状态会立刻刷新）。"""
        self._collapsed_text = collapsed_text
        self._expanded_text = expanded_text
        self._sync_text()

    # --- 内部 ---
    def _sync_text(self) -> None:
        arrow = _EXPANDED_ARROW if self._expanded else _COLLAPSED_ARROW
        label = self._expanded_text if self._expanded else self._collapsed_text
        self.button.configure(text=f"{arrow}    {label}")
