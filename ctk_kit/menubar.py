"""菜单栏：窗口顶部一排菜单按钮，点开是下拉菜单。

下拉面板复用 :class:`ContextMenu`，圆角、描边和悬停色与右键菜单一致。

用法::

    from ctk_kit import MenuBar

    MenuBar(root, items=[
        ("文件", [("新建", new_file), ("打开", open_file), "-", ("退出", quit)]),
        ("编辑", [("撤销", undo), ("重做", redo)]),
    ]).pack(side="top", fill="x")

``"-"`` 表示分隔线；菜单项回调可以无参，也可以接一个参数（触发菜单的按钮）。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, List, Optional, Sequence, Tuple

import customtkinter as ctk

from . import tokens as T
from .context_menu import ContextMenu
from .fonts import get_font

__all__ = ["MenuBar"]

MenuItem = Tuple[str, Optional[Callable]]
MenuEntries = Sequence[Any]


class MenuBar(ctk.CTkFrame):
    """横向菜单栏。

    参数:
        master: 父容器。
        items: ``(菜单名, 菜单项列表)`` 的序列。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        add_menu(label, entries): 追加一个菜单。
        close(): 收起所有打开的下拉。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        items: Sequence[Tuple[str, MenuEntries]] = (),
        **kwargs: Any,
    ) -> None:
        """建菜单栏；高度固定 34。"""
        super().__init__(
            master,
            fg_color=T.COLOR_SIDE,
            corner_radius=0,
            height=34,
            **kwargs,
        )
        self.pack_propagate(False)

        self._menus: List[ContextMenu] = []
        for label, entries in items:
            self.add_menu(label, entries)

    # --- 对外 ---
    def add_menu(self, label: str, entries: MenuEntries = ()) -> ctk.CTkButton:
        """追加一个菜单，返回它的按钮。"""
        button = ctk.CTkButton(
            self,
            text=label,
            height=26,
            corner_radius=T.RADIUS_SMALL,
            fg_color="transparent",
            hover_color=T.COLOR_SOFT_HOVER,
            text_color=T.COLOR_TEXT,
            font=get_font(T.FONT_SMALL),
        )
        button.pack(side="left", padx=(4, 0), pady=4)

        menu = ContextMenu(button, width=150)
        for entry in entries:
            if entry is None or entry == "-":
                menu.add_separator()
                continue
            text, command = entry
            if text == "-":
                menu.add_separator()
            else:
                menu.add_command(text, command)

        button.configure(
            command=lambda b=button, m=menu: m.show(
                b.winfo_rootx(),
                b.winfo_rooty() + b.winfo_height() + 1,
                source=b,
            )
        )
        self._menus.append(menu)
        return button

    def close(self) -> None:
        """收起所有打开的下拉。"""
        for menu in self._menus:
            menu.close()
