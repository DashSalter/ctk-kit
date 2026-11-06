"""最小窗口示例：侧边栏 + 各组件页，全部只用 ctk_kit。

``App`` 负责窗口，``SidebarNav`` 负责左栏和右侧页面区；每个页面各放一个
文件，页面都按「UI 类 + 事件类」拆开：UI 类只建控件，事件类在构造时自动
``bind_events()``，交互都写在事件类里。
"""

from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path

from PIL import Image

from ctk_kit import (
    __version__ as _ctk_version,
    App,
    Avatar,
    CTkButton,
    CTkImage,
    Frame,
    Label,
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
from theme_page import ThemePage
from window_state import WindowStateStore

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
        # 状态持久化是使用方的事：核心库不再自带配置文件，这里接示例
        # 自己的实现（~/.ctk-kit/window.json）。不传就什么都不记。
        state = WindowStateStore()
        super().__init__(
            title="ctk-kit 组件总栏",
            size=(1200, 800),
            min_size=(380, 220),
            center=True,
            state=state,
        )
        # 设置页要写回底色 / 透明度，先把 store 挂出来给它用。
        self.state_store = state
        # 先藏起来：建页面、盖遮罩期间不要让用户看到半成品的第一帧。
        self.withdraw()

        # 页面类本身就是构建器：SidebarNav 需要「给一个父容器、返回页面」的
        # 可调用对象，类正好满足。页面内部从控件树拿根窗口（App）。
        self.nav = SidebarNav(
            self,
            title="ctk-kit",
            subtitle=f"v{_ctk_version} · 示例",
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
                "主题": ThemePage,
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
        closed = False

        def _close_splash() -> None:
            """撤遮罩，只撤一次（finish 不幂等，重复调用会重复排 destroy）。"""
            nonlocal closed
            if closed:
                return
            closed = True
            splash.finish()

        # 遮罩里先建「当前页 + 左右相邻」，其余页交给侧边栏在后台慢慢补。
        #   CTK_DEMO_PAGES=组件,按钮   只建这几页（测试单页时用）
        #   CTK_DEMO_NO_WARM=1        只建当前页、不在后台预建（最快启动）
        names = list(self.nav.rebuilder.pages)
        current = self.nav.current
        index = names.index(current) if current in names else 0
        preload = [names[i] for i in (index - 1, index, index + 1) if 0 <= i < len(names)]
        wanted = [
            part.strip()
            for part in os.environ.get("CTK_DEMO_PAGES", "").split(",")
            if part.strip()
        ]
        if wanted:
            preload = [name for name in wanted if name in names]
        elif os.environ.get("CTK_DEMO_NO_WARM", "").strip() not in ("", "0"):
            self.nav._warm_enabled = False
            preload = [current] if current in names else []

        try:
            self.nav.rebuilder.build_all(progress=splash.set_progress, names=preload)
        finally:
            # 遮罩要等这几页真正建完才撤（首屏那两张同步卡不够看），
            # 关窗或其他异常导致回调没跑也要兜底撤一次。
            # 先把计数加满再登记回调：有的页（整页同步建的）会在
            # when_built 里立刻回调，边加边登记会提前把遮罩撤掉。
            pages = [self.nav.rebuilder.frame(name) for name in preload]
            remaining = [
                sum(1 for page in pages if hasattr(page, "when_built"))
            ]

            def _one_done() -> None:
                remaining[0] -= 1
                if remaining[0] <= 0:
                    _close_splash()

            if remaining[0] <= 0:
                _close_splash()
            else:
                for page in pages:
                    page.when_built(_one_done)
            self.after(8000, _close_splash)

        # App 在毛玻璃模式下会自动建一层默认底色的背景窗口；这里把上次存的
        # 颜色 / 透明度 / 尺寸盖回去（晚于 App 内部那次 40ms 的自动创建）。
        self.after(120, self._restore_frost)

    def _restore_frost(self) -> None:
        """恢复持久化的背景窗口设置；没记录或不是毛玻璃就跳过。"""
        store = getattr(self, "state_store", None)
        record = store.read_frost() if store is not None else None
        if not record or not getattr(self, "frost_active", False):
            return
        self.set_frost_backdrop(
            record["color"],
            alpha=record["alpha"],
            spread=record["spread"],
        )

    def set_backdrop(self, mode, *, save: bool = True):
        """切到毛玻璃后，把上次存的底色盖回自动创建的那一层。"""
        super().set_backdrop(mode, save=save)
        self.after(120, self._restore_frost)

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

        name = Label(
            row,
            text="加点盐",
            font=get_font((T.FONT_NAME, 13, "bold")),
            anchor="w",
            cursor="hand2",
        )
        name.pack(side="left", fill="x", expand=True, padx=(8, 0))
        name.on_click(lambda _event: self._open_profile())

        # 设置入口靠右，和头像同一行。图标只放一版深色稿，深色主题下按 alpha
        # 换成浅色线条，不用单独再下一份浅色图。
        self._gear = CTkImage(
            light_image=_tinted_icon("setting.png", "#3a3f47"),
            dark_image=_tinted_icon("setting.png", "#c9cfd8"),
            size=(17, 17),
        )
        self.settings_button = CTkButton(
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
