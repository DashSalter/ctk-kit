# -*- coding: utf-8 -*-
"""柱状图页：默认配色、逐柱配色、切换数据集。

和 ``examples/basics`` 的页面一样拆成「UI 类 + 事件类」：
``BarPageUI`` 只建控件，``BarPage`` 在构造时自动 ``bind_events()``。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    BarChart,
    Card,
    HintLabel,
    PageBase,
    PageHeader,
    Segmented,
)

WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
THIS_WEEK = [120, 180, 150, 260, 310, 420, 380]
LAST_WEEK = [90, 140, 130, 190, 230, 300, 260]

CHANNELS = ["官网", "小程序", "公众号", "直播", "邮件"]
RATES = [42, 68, 55, 81, 37]
CHANNEL_COLORS = ["#5ad8a6", "#5b8ff9", "#f6bd16", "#e8684a", "#6dc8ec"]


class BarPageUI(PageBase):
    """柱状图页 UI：只建控件，切换数据集留给 BarPage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "柱状图")
        self.header.info.configure(text="默认配色 · 逐柱配色 · 切换数据集")

        self._build_visits()
        self._build_channels()

    def _build_visits(self) -> None:
        """默认配色 + 数据集切换。"""
        card = Card(self, title="每周访问量")
        card.pack(fill="both", expand=True)

        self.visits = BarChart(
            card.row(1, fill="both", expand=True, padx=16, pady=(12, 6)),
            values=THIS_WEEK,
            categories=WEEK,
            height=260,
        )
        self.visits.pack(fill="both", expand=True)

        row = card.row(2, fill="x", padx=16, pady=(0, 14))
        self.period = Segmented(row, ["本周", "上周"], width=168)
        self.period.pack(side="left")
        HintLabel(
            row,
            "切换数据集只重画 canvas，图表控件本身不重建。",
        ).pack(side="left", padx=(12, 0))

    def _build_channels(self) -> None:
        """逐柱配色 + 固定纵轴范围。"""
        card = Card(self, title="各渠道转化率")
        card.pack(fill="both", expand=True, pady=(12, 0))

        self.rate = BarChart(
            card.row(1, fill="both", expand=True, padx=16, pady=(12, 10)),
            values=RATES,
            categories=CHANNELS,
            colors=CHANNEL_COLORS,
            y_range=(0, 100),
            formatter="{:.0f}%",
            height=230,
        )
        self.rate.pack(fill="both", expand=True)

        HintLabel(
            card,
            "colors 可以逐柱指定；y_range 固定到 0–100，多条渠道对比时不会跳轴。",
        ).pack(fill="x", padx=16, pady=(0, 14))


class BarPage(BarPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.when_built(self.bind_events)

    def bind_events(self) -> None:
        """必须实现：注册页面内的事件。"""
        self.period.configure(command=self.switch_period)

    def switch_period(self, _value: str = "") -> None:
        """本周 / 上周切换：只换数据，不重建图表控件。"""
        current = self.period.get()
        self.visits.set(THIS_WEEK if current == "本周" else LAST_WEEK)
        self.header.info.configure(text=f"正在查看：{current}")
