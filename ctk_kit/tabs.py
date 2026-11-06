"""标签页：把 ``CTkTabview`` 套成本库的配色和圆角。

用法::

    from ctk_kit import Tabs

    tabs = Tabs(card, values=("常规", "高级", "关于"))
    tabs.pack(fill="both", expand=True, padx=16, pady=12)

    CTkLabel(tabs.tab("常规"), text="常规设置").pack(padx=12, pady=12)

``tab(name)`` 就是 ``CTkTabview.tab()`` 的别名；``add`` / ``set`` / ``get``
和原生用法一致。选中标签用偏青的激活色，文字改成白色；未选中用浅一档的
容器底和常规文字色，和 ``Segmented`` 的分段按钮保持一致。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Sequence

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .sugar import Valuable


class Tabs(Valuable, ctk.CTkTabview):
    """统一样式的标签页容器。

    参数:
        master: 父容器。
        values: 标签文字，按显示顺序排列；非空时默认选中第一个。
        command: 切换标签时的回调，参数是标签文字。
        width / height: 整体尺寸；高度默认 260。
        **kwargs: 透传给 ``CTkTabview``，显式传同名样式参数可覆盖。

    方法:
        add(name): 追加一个标签页并返回内容容器。
        tab(name): 取某个标签页的内容容器。
        set(name): 切换标签。
        get(): 当前标签文字。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        values: Sequence[str] = (),
        command: Any = None,
        width: int = 420,
        height: int = 260,
        **kwargs: Any,
    ) -> None:
        """建标签页容器；``values`` 里的标签会依次加进去。"""
        self._user_command = command
        kwargs.setdefault("fg_color", T.COLOR_CARD)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", T.COLOR_BORDER)
        kwargs.setdefault("corner_radius", T.RADIUS_MEDIUM)
        kwargs.setdefault("segmented_button_fg_color", T.COLOR_SOFT)
        kwargs.setdefault("segmented_button_selected_color", T.COLOR_ACTIVE)
        kwargs.setdefault("segmented_button_selected_hover_color", T.COLOR_ACTIVE_HOVER)
        kwargs.setdefault("segmented_button_unselected_color", T.COLOR_SOFT)
        kwargs.setdefault("segmented_button_unselected_hover_color", T.COLOR_SOFT_HOVER)
        kwargs.setdefault("text_color", T.COLOR_TEXT)
        kwargs.setdefault("segmented_button_font", get_font(T.FONT_SMALL))
        # CTkTabview 的回调不带参数；包一层，按文档把当前标签文字传出去。
        super().__init__(
            master, width=width, height=height, command=self._tab_changed, **kwargs
        )

        for name in values:
            self.add(name)
        if values:
            # 初始选中第一个标签，但不触发用户的 command
            saved = self._user_command
            self._user_command = None
            try:
                self.set(values[0])
            finally:
                self._user_command = saved

    # --- 对外 ---
    def configure(self, **kwargs: Any) -> None:
        """改属性；``command=`` 换切换回调，其余透传给 ``CTkTabview``。"""
        if "command" in kwargs:
            self._user_command = kwargs.pop("command")
        super().configure(**kwargs)

    def tab(self, name: str) -> Any:
        """取标签页的内容容器；``CTkTabview.tab`` 的别名。"""
        return super().tab(name)

    def set(self, name: str) -> None:
        """切换标签，并把选中标签的文字改成白色。"""
        super().set(name)
        self._paint(name)

    def add(self, name: str) -> Any:
        """加一个标签页；返回内容容器。"""
        frame = super().add(name)
        self._paint(self.get())
        return frame

    # --- 内部 ---
    def _tab_changed(self) -> None:
        """``CTkTabview`` 切换后回调：把当前标签文字转给用户回调。"""
        if self._user_command is not None:
            self._user_command(self.get())

    def _paint(self, current: str) -> None:
        """给选中的标签上白字，其余标签用常规文字色。"""
        buttons = getattr(
            getattr(self, "_segmented_button", None), "_buttons_dict", {}
        )
        for name, button in buttons.items():
            try:
                button.configure(
                    text_color=(
                        T.COLOR_ACCENT_TEXT if name == current else T.COLOR_TEXT
                    )
                )
            except Exception:  # noqa: BLE001 - 控件可能已经销毁
                continue
