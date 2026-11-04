"""最小窗口示例：侧边栏 + 各组件页，全部只用 ctk_kit。

``App`` 负责窗口，``SidebarNav`` 负责左栏和右侧页面区；每个页面各放一个
文件，页面都按「UI 类 + 事件类」拆开：UI 类只建控件，事件类在构造时自动
``bind_events()``，交互都写在事件类里。
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from ctk_kit import (
    App,
    Avatar,
    CTkLabel,
    Frame,
    LoadingOverlay,
    SidebarNav,
    tokens as T,
)
from ctk_kit.fonts import get_font

from button_page import ButtonPage
from choices_page import ChoicesPage
from collapse_page import CollapsePage
from datetime_page import TimeDatePage
from dialog_page import DialogPage
from extras_page import ExtrasPage
from image_page import ImagePage
from inputs_page import InputsPage
from listing_page import ListingPage
from menu_page import MenuPage
from misc_page import MiscPage
from notify_page import NotifyPage
from overview_page import OverviewPage
from profile_page import ProfilePage
from select_page import SelectPage
from settings_page import SettingsPage
from table_page import TablePage

_ICON_DIR = Path(__file__).resolve().parents[2] / "ctk_kit" / "Icon"


def _tinted_icon(name: str, color: str) -> Image.Image:
    """把单色图标的线条换成指定颜色，保留透明边缘。

    只下载一版深色图标就够了，深色主题下按 alpha 通道换成浅色。
    """
    image = Image.open(_ICON_DIR / name).convert("RGBA")
    solid = Image.new("RGBA", image.size, color)
    solid.putalpha(image.getchannel("A"))
    return solid


class DemoApp(App):
    def __init__(self) -> None:
        super().__init__(
            title="ctk-kit 组件总栏",
            size=(1200, 800),
            min_size=(380, 220),
            center=True,
        )
        # 先藏起来：建页面、盖遮罩期间不要让用户看到半成品的第一帧。
        self.withdraw()

        # 页面类本身就是构建器：SidebarNav 需要「给一个父容器、返回页面」的
        # 可调用对象，类正好满足。页面内部从控件树拿根窗口（App）。
        self.nav = SidebarNav(
            self,
            title="ctk-kit",
            subtitle="v0.9.2 · 示例",
            pages={
                "总览": OverviewPage,
                "按钮": ButtonPage,
                "组件": ExtrasPage,
                "输入": InputsPage,
                "下拉": SelectPage,
                "选择": ChoicesPage,
                "展开": CollapsePage,
                "时间日期": TimeDatePage,
                "表格": TablePage,
                "图片": ImagePage,
                "提示": NotifyPage,
                "弹窗": DialogPage,
                "菜单": MenuPage,
                "列表": ListingPage,
                "杂项": MiscPage,
            },
            hidden_pages={
                "个人中心": ProfilePage,
                "设置": SettingsPage,
            },
            footer=self._build_account,
            width=200,   # 侧边栏固定宽度（逻辑像素），窗口拉宽时不跟着变
            divider=True,  # 侧边栏和页面之间画 1px 分隔线
            initial="总览",
            padding=(40, 16),
        )
        self.nav.pack(fill="both", expand=True)

        # 启动流程：窗口先保持隐藏，遮罩盖好之后再一次显示出来，
        # 所以用户看到的第一帧就是带 logo 和进度条的启动屏。
        splash = LoadingOverlay(self)
        self.deiconify()
        self.update()
        try:
            # 启动时只等首页：其余页第一次切过去再建，遮罩不用陪着等十几页。
            self.nav.rebuilder.build_all(
                progress=splash.set_progress, names=[self.nav.current]
            )
        finally:
            splash.finish()

    def _build_account(self, parent: tk.Misc) -> None:
        """侧边栏底部一行：左边头像 + 名字进个人中心，右边齿轮进设置。"""
        row = Frame(parent)
        row.pack(fill="x", pady=(0, 8))

        Avatar(
            row,
            text="加点盐",
            size=32,
            status="online",
            command=self._open_profile,
        ).pack(side="left")

        name = CTkLabel(
            row,
            text="加点盐",
            font=get_font((T.FONT_NAME, 13, "bold")),
            text_color=T.COLOR_TEXT,
            anchor="w",
            cursor="hand2",
        )
        name.pack(side="left", fill="x", expand=True, padx=(8, 0))
        name.bind("<Button-1>", lambda _event: self._open_profile())

        # 设置入口靠右，和头像同一行。图标只放一版深色稿，深色主题下按 alpha
        # 换成浅色线条，不用单独再下一份浅色图。
        self._gear = ctk.CTkImage(
            light_image=_tinted_icon("setting.png", "#3a3f47"),
            dark_image=_tinted_icon("setting.png", "#c9cfd8"),
            size=(17, 17),
        )
        self.settings_button = ctk.CTkButton(
            row,
            text="",
            image=self._gear,
            width=30,
            height=28,
            fg_color="transparent",
            hover_color=T.COLOR_SOFT_HOVER,
            corner_radius=T.RADIUS_SMALL,
            command=self._open_settings,
        )
        self.settings_button.pack(side="right", padx=(6, 0))

    def _open_profile(self) -> None:
        """切到个人中心页。"""
        self.nav.show("个人中心")

    def _open_settings(self) -> None:
        """切到设置页。"""
        self.nav.show("设置")


def main() -> None:
    DemoApp().mainloop()


if __name__ == "__main__":
    main()
