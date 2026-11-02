"""最小窗口示例：侧边栏 + 各组件页，全部只用 ctk_kit。

``App`` 负责窗口，``SidebarNav`` 负责左栏和右侧页面区；每个页面各放一个
文件，页面都按「UI 类 + 事件类」拆开：UI 类只建控件，事件类在构造时自动
``bind_events()``，交互都写在事件类里。
"""

from __future__ import annotations

from ctk_kit import App, SidebarNav

from button_page import ButtonPage
from choices_page import ChoicesPage
from collapse_page import CollapsePage
from image_page import ImagePage
from inputs_page import InputsPage
from listing_page import ListingPage
from menu_page import MenuPage
from notify_page import NotifyPage
from overview_page import OverviewPage
from select_page import SelectPage
from settings_page import SettingsPage
from table_page import TablePage


class DemoApp(App):
    def __init__(self) -> None:
        super().__init__(
            title="欢迎使用CTkKit",
            size=(1200, 800),
            min_size=(380, 220),
            center=True,
        )

        # 页面类本身就是构建器：SidebarNav 需要「给一个父容器、返回页面」的
        # 可调用对象，类正好满足。页面内部从控件树拿根窗口（App）。
        self.nav = SidebarNav(
            self,
            title="ctk-kit",
            subtitle="v0.9.2 · 示例",
            pages={
                "总览": OverviewPage,
                "按钮": ButtonPage,
                "输入": InputsPage,
                "下拉": SelectPage,
                "选择": ChoicesPage,
                "展开": CollapsePage,
                "表格": TablePage,
                "图片": ImagePage,
                "提示": NotifyPage,
                "菜单": MenuPage,
                "列表": ListingPage,
            },
            bottom_pages={
                "设置": SettingsPage,
            },
            width=200,   # 侧边栏固定宽度（逻辑像素），窗口拉宽时不跟着变
            initial="总览",
            padding=(40, 16),
        )
        self.nav.pack(fill="both", expand=True)


def main() -> None:
    DemoApp().mainloop()


if __name__ == "__main__":
    main()
