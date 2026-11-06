"""菜单栏：窗口顶部一排菜单按钮，点开是下拉菜单。

下拉面板复用 :class:`ContextMenu`，圆角、描边和悬停色与右键菜单一致。

菜单按钮之间还能插输入框、按钮、搜索框、开关：靠左的直接接在菜单按钮后面，
靠右的进 ``bar.trailing`` 容器。

用法::

    from ctk_kit import MenuBar

    bar = MenuBar(root, items=[
        ("文件", [("新建", new_file), ("打开", open_file), "-", ("退出", quit)]),
        ("编辑", [("撤销", undo), ("重做", redo)]),
    ])
    bar.pack(side="top", fill="x")

    bar.add_entry("跳转到行号", width=120)          # 接在「编辑」后面
    bar.add_search("搜索命令", width=200, command=run)   # 靠右
    bar.add_button("设置", command=open_settings)     # 靠右

    # 想放别的控件：建在 bar（靠左）或 bar.trailing（靠右）上，再交给 add_widget()
    bar.add_widget(Switch(bar.trailing, text="自动保存"), side="right")

``"-"`` 表示分隔线；菜单项回调可以无参，也可以接一个参数（触发菜单的按钮）。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, List, Optional, Sequence, Tuple

import customtkinter as ctk

from . import tokens as T
from .context_menu import ContextMenu
from .fonts import get_font
from .search import SearchBox

__all__ = ["MenuBar"]

MenuItem = Tuple[str, Optional[Callable]]
MenuEntries = Sequence[Any]

#: 菜单栏默认高度；输入框 / 按钮会按「高度 - 8」收缩，留出上下留白。
_DEFAULT_HEIGHT = 34


class MenuBar(ctk.CTkFrame):
    """横向菜单栏，菜单按钮之间可以插输入框、按钮等自定义控件。

    参数:
        master: 父容器。
        items: ``(菜单名, 菜单项列表)`` 的序列。
        height: 整条栏的高度，默认 34；插输入框时想更宽松就传 40。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        add_menu(label, entries): 追加一个菜单。
        add_entry(placeholder, ...): 加一个输入框。
        add_button(text, command, ...): 加一个按钮。
        add_search(placeholder, ...): 加一个带放大镜的搜索框。
        add_widget(widget, side): 把已建好的控件摆进来。
        close(): 收起所有打开的下拉。

    属性:
        trailing: 靠右的容器，自己建控件时用它当 master。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        items: Sequence[Tuple[str, MenuEntries]] = (),
        height: int = _DEFAULT_HEIGHT,
        **kwargs: Any,
    ) -> None:
        """建菜单栏；高度固定，内部控件统一按内容高度收缩。"""
        kwargs.pop("height", None)  # 高度只走上面的参数，避免和下面重复
        self._height = max(28, int(height))
        super().__init__(
            master,
            fg_color=T.COLOR_SIDE,
            corner_radius=0,
            height=self._height,
            **kwargs,
        )
        self.pack_propagate(False)

        # 靠右的容器：先 pack 占住右侧，后面加多少菜单按钮都不影响它。
        self.trailing = ctk.CTkFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self.trailing.pack(side="right", padx=(4, 8), pady=4)

        self._menus: List[ContextMenu] = []
        for label, entries in items:
            self.add_menu(label, entries)

    # --- 对外：菜单 ---
    def add_menu(self, label: str, entries: MenuEntries = ()) -> ctk.CTkButton:
        """追加一个菜单，返回它的按钮。"""
        button = self._make_button(label)
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

    # --- 对外：插控件 ---
    def add_entry(
        self,
        placeholder: str = "",
        *,
        side: str = "left",
        width: int = 180,
        command: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> ctk.CTkEntry:
        """加一个输入框；``command`` 在按回车时收到当前文字。"""
        parent = self._parent_for(side)
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            width=width,
            height=self._content_height(),
            corner_radius=T.RADIUS_SMALL,
            fg_color=T.COLOR_INPUT,
            border_width=1,
            border_color=T.COLOR_BORDER_INPUT,
            text_color=T.COLOR_TEXT,
            font=get_font(T.FONT_SMALL),
            **kwargs,
        )
        if command is not None:
            entry.bind("<Return>", lambda _event: command(entry.get()))
        return self.add_widget(entry, side=side)  # type: ignore[return-value]

    def add_button(
        self,
        text: str,
        command: Optional[Callable[[], None]] = None,
        *,
        side: str = "left",
        width: Optional[int] = None,
        **kwargs: Any,
    ) -> ctk.CTkButton:
        """加一个和菜单按钮同样式的按钮；不传 ``width`` 按文字估个宽度。"""
        button = self._make_button(text, parent=self._parent_for(side), width=width, **kwargs)
        button.configure(command=command)
        return self.add_widget(button, side=side)  # type: ignore[return-value]

    def add_search(
        self,
        placeholder: str = "搜索",
        *,
        side: str = "right",
        width: int = 200,
        command: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> SearchBox:
        """加一个带放大镜的搜索框，默认靠右。"""
        box = SearchBox(
            self._parent_for(side),
            placeholder=placeholder,
            width=width,
            height=self._content_height() + 2,
            command=command,
            **kwargs,
        )
        return self.add_widget(box, side=side)  # type: ignore[return-value]

    def add_widget(self, widget: tk.Misc, *, side: str = "left") -> tk.Misc:
        """把已经建好的控件摆进菜单栏，返回它。

        控件要建在 ``bar``（靠左）或 ``bar.trailing``（靠右）上，否则 Tk 不允许
        跨父容器 pack，这里会抛 ``ValueError``。
        """
        parent = self._parent_for(side)
        if widget.master is not parent:
            raise ValueError(
                "控件要建在菜单栏上：靠左用 bar 当 master，靠右用 bar.trailing"
            )
        widget.pack(side="left", padx=(4, 0), pady=0 if side == "right" else 4)
        return widget

    def close(self) -> None:
        """收起所有打开的下拉。"""
        for menu in self._menus:
            menu.close()

    # --- 内部 ---
    def _parent_for(self, side: str) -> tk.Misc:
        """``side="right"`` 用靠右容器，其余都接在左侧。"""
        return self.trailing if side == "right" else self

    def _content_height(self) -> int:
        """栏里控件的高度：栏高减 8，最少 22。"""
        return max(22, self._height - 8)

    def _make_button(
        self,
        text: str,
        *,
        parent: Optional[tk.Misc] = None,
        width: Optional[int] = None,
        **kwargs: Any,
    ) -> ctk.CTkButton:
        """建一个和菜单按钮同样式（透明底 + 悬停色）的按钮。"""
        if width is None:
            # 中文按 13px、英文按 7px 估，再加两侧留白；够用，也不至于太宽。
            units = sum(13 if ord(ch) > 0x2E80 else 7 for ch in text)
            width = max(48, units + 30)
        kwargs.setdefault("height", self._content_height())
        kwargs.setdefault("corner_radius", T.RADIUS_SMALL)
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("hover_color", T.COLOR_SOFT_HOVER)
        kwargs.setdefault("text_color", T.COLOR_TEXT)
        kwargs.setdefault("font", get_font(T.FONT_SMALL))
        return ctk.CTkButton(parent or self, text=text, width=width, **kwargs)
