"""个人中心页：从侧边栏底部的头像点进来，显示大头像和名字。

这一页不在侧边栏的导航列表里，由「个人中心」入口（底部头像行）切过来。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Avatar,
    Badge,
    Card,
    CTkLabel,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    Scrollable,
    SoftButton,
    tokens as T,
)
from ctk_kit.fonts import get_font


class ProfilePage(PageBase):
    """个人中心：大圆头像 + 名称 + 返回。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "个人中心")
        self.header.info.configure(text="账号")

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        box = Card(area, title="账号")
        box.pack(fill="x")

        center = Frame(box)
        center.pack(fill="x", pady=(28, 24))

        self.avatar = Avatar(center, text="加点盐", size=96, status="online")
        self.avatar.pack()

        self.name = CTkLabel(
            center,
            text="加点盐",
            font=get_font((T.FONT_NAME, 22, "bold")),
            text_color=T.COLOR_TEXT,
        )
        self.name.pack(pady=(14, 0))

        meta = Frame(center)
        meta.pack(pady=(8, 0))
        Badge(meta, "在线", color="success", variant="soft", size="sm").pack(
            side="left"
        )
        HintLabel(meta, "上次登录：刚刚").pack(side="left", padx=(8, 0))

        SoftButton(center, "返回总览", command=self._go_home).pack(pady=(18, 0))

    def _go_home(self) -> None:
        """退回总览页。"""
        self.app.nav.show("总览")
