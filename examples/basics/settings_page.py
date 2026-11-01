import tkinter as tk

from ctk_kit import (
    Card,
    FieldLabel,
    Frame,
    get_appearance_mode,
    HintLabel,
    is_dark,
    PageBase,
    PageHeader,
    Scrollable,
    Segmented,
)


class SettingsPageUI(PageBase):

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "设置")

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "提示:切换主题模式只重建当前页，其余页切过去时再建")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_appearance(area)
        self.refresh_theme()

    def _build_appearance(self, area: tk.Misc) -> None:
        """外观模式：主题分段按钮 + 一行说明。"""
        box = Card(area, title="外观模式")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        FieldLabel(row, "主题", width=64).pack(side="left")

        self.theme = Segmented(row, ["浅色", "深色"], width=200)
        self.theme.pack(side="left", padx=(4, 0))

    def refresh_theme(self) -> None:
        """按当前外观刷新标题说明和分段选中项。"""
        self.header.info.configure(text=f"当前：{get_appearance_mode()}")
        self.theme.set("深色" if is_dark() else "浅色")


class SettingsPage(SettingsPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """必须实现：注册按钮和事件。"""
        self.theme.configure(command=self.on_theme)

    def on_theme(self, value: str) -> None:
        """切换浅色 / 深色；有 SidebarNav 时只重建当前页。"""
        self.app.set_appearance_mode(value)
