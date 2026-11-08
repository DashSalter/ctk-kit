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
from .fonts import get_font

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
        detail: 标题右侧常驻的一行小字（摘要），默认空表示不显示。
        on_toggle: 展开状态变化回调，参数是新的状态（``True`` 为已展开）。
        **kwargs: 透传给外层 ``CTkFrame``。

    属性:
        body: 内容容器，往这里 pack 子控件。
        button: 标题那一行的 ``CTkButton``，想换字号/颜色可以直接改。
        detail_label: 右侧摘要标签，``set_detail()`` 改文字时用的就是它。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        collapsed_text: str = "显示代码",
        expanded_text: str = "隐藏代码",
        expanded: bool = False,
        button_height: int = 36,
        detail: str = "",
        on_toggle: ToggleCommand = None,
        **kwargs: Any,
    ) -> None:
        """建折叠面板：标题按钮在上，内容容器 ``body`` 在下。"""
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._collapsed_text = collapsed_text
        self._expanded_text = expanded_text
        self._detail = detail
        self._on_toggle = on_toggle
        self._expanded = bool(expanded)

        # 标题行单独一层：按钮铺满整行负责点击，右侧摘要叠在按钮上。
        # 摘要盖住按钮右端，点它也算点标题行（见 _on_detail_click）。
        self.header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.header.pack(fill="x")

        self.button = ctk.CTkButton(
            self.header,
            text="",
            height=button_height,
            corner_radius=T.RADIUS_SMALL,
            font=get_font(T.FONT_SMALL),
            fg_color="transparent",
            hover_color=T.COLOR_HOVER_FAINT,
            text_color=T.COLOR_ACCENT,
            text_color_disabled=T.COLOR_FAINT,
            command=self.toggle,
        )
        self.button.pack(fill="x")
        # 鼠标在标题行走廊上（还没碰到摘要）时，摘要底色也要跟着亮，
        # 否则整行亮了、右端小字那块还是暗的。
        self.button.bind("<Enter>", self._on_button_enter, add="+")
        self.button.bind("<Leave>", self._on_button_leave, add="+")

        self.detail_label = ctk.CTkLabel(
            self.header,
            text="",
            font=get_font(T.FONT_TINY),
            text_color=T.COLOR_MUTED,
            fg_color="transparent",
            anchor="e",
        )
        self.detail_label.bind("<Button-1>", self._on_detail_click)
        # 摘要盖在按钮右端，鼠标停在它上面时按钮收不到 Enter/Leave，
        # 这里转发一下，整条标题行的 hover 底色才能保持一致。
        self.detail_label.bind("<Enter>", self._on_detail_enter)
        self.detail_label.bind("<Leave>", self._on_detail_leave)
        self._sync_detail()

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

    @property
    def detail(self) -> str:
        """标题右侧的摘要文字，没设置时为空字符串。"""
        return self._detail

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

    def set_detail(self, text: str) -> None:
        """换掉标题右侧的摘要文字；空字符串表示不显示。"""
        self._detail = text
        self._sync_detail()

    # --- 内部 ---
    def _sync_detail(self) -> None:
        """按 ``detail`` 文本显示或隐藏右侧摘要。"""
        if not self._detail:
            self.detail_label.place_forget()
            return
        self.detail_label.configure(text=self._detail)
        self.detail_label.place(
            relx=1.0, x=-T.SPACE_MD, rely=0.5, anchor="e"
        )

    def _on_detail_click(self, _event: Any = None) -> str:
        """点摘要等于点标题行：它盖住了按钮右端，不转发就点不动。"""
        self.toggle()
        return "break"

    def _on_detail_enter(self, _event: Any = None) -> None:
        """鼠标移到摘要上时，让整条标题行（含摘要底色）一起高亮。"""
        self._set_detail_hover(True)
        self.button._on_enter()

    def _on_detail_leave(self, _event: Any = None) -> None:
        """鼠标离开摘要时恢复底色；移到按钮上就保持高亮。"""
        if not self._pointer_on_header():
            self._set_detail_hover(False)
            self.button._on_leave()

    def _on_button_enter(self, _event: Any = None) -> None:
        """鼠标进入标题按钮时，摘要底色同步变亮。"""
        self._set_detail_hover(True)

    def _on_button_leave(self, _event: Any = None) -> None:
        """鼠标离开按钮时，若没停在摘要上就恢复摘要底色。"""
        if not self._pointer_on_header():
            self._set_detail_hover(False)

    def _set_detail_hover(self, hovered: bool) -> None:
        """摘要画在按钮上面，得手动跟上按钮的 hover 底色。

        ``fg_color`` 是文字内圈，``bg_color`` 是 canvas 外圈；只改前者会在
        摘要边缘留一圈原底色，所以两个一起改。
        """
        if hovered:
            self.detail_label.configure(
                fg_color=T.COLOR_HOVER_FAINT,
                bg_color=T.COLOR_HOVER_FAINT,
            )
        else:
            self.detail_label.configure(fg_color="transparent", bg_color="transparent")

    def _pointer_on_header(self) -> bool:
        """指针是否还停在整条标题行内（按钮或摘要上）。"""
        x, y = self.winfo_pointerxy()
        under = self.header.winfo_containing(x, y)
        if under is None:
            return False
        path = str(under)
        base = str(self.header)
        return path == base or path.startswith(base + ".")

    def _sync_text(self) -> None:
        """按当前展开状态重画箭头和标题文字。"""
        arrow = _EXPANDED_ARROW if self._expanded else _COLLAPSED_ARROW
        label = self._expanded_text if self._expanded else self._collapsed_text
        self.button.configure(text=f"{arrow}    {label}")
