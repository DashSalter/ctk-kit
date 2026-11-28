# -*- coding: utf-8 -*-
"""图表示例总入口：侧边栏 + 每类图一页，写法与 ``examples/basics`` 一致。

``App`` 负责窗口，``SidebarNav`` 负责左栏和右侧页面区；每个页面各放一个
文件，页面都按「UI 类 + 事件类」拆开：UI 类只建控件，事件类在构造时自动
``bind_events()``，交互都写在事件类里。

运行::

    python examples/charts/window.py
"""

from __future__ import annotations

from ctk_kit import App, SidebarNav

from bar_page import BarPage
from line_page import LinePage
from overview_page import OverviewPage
from pie_page import PiePage
from radar_page import RadarPage
from scatter_page import ScatterPage


class ChartsApp(App):
    """图表示例窗口：左侧切页，右侧滚动查看各类图。"""

    def __init__(self) -> None:
        super().__init__(
            title="ctk-kit 图表示例",
            size=(1180, 820),
            min_size=(780, 560),
            center=True,
        )
        self.nav = SidebarNav(
            self,
            title="ctk-kit",
            subtitle="图表示例",
            pages={
                "总览": OverviewPage,
                "柱状图": BarPage,
                "折线图": LinePage,
                "饼图": PiePage,
                "雷达图": RadarPage,
                "散点图": ScatterPage,
            },
            width=190,
            divider=True,
            initial="总览",
            padding=(36, 16),
        )
        self.nav.pack(fill="both", expand=True)


def main() -> None:
    ChartsApp().mainloop()


if __name__ == "__main__":
    main()
