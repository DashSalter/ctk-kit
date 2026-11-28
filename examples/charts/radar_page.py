# -*- coding: utf-8 -*-
"""雷达图页：多系列对比、切换某人的数据。"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    HintLabel,
    PageBase,
    PageHeader,
    RadarChart,
    Segmented,
)

AXES = ["沟通", "协作", "执行力", "创新", "学习", "抗压"]

LI = [82, 76, 88, 64, 90, 72]
LI_LAST = [74, 70, 80, 58, 82, 66]
WANG = [70, 88, 68, 84, 75, 80]
ZHANG = [75, 70, 80, 72, 68, 86]


class RadarPageUI(PageBase):
    """雷达图页 UI：只建控件，切换数据留给 RadarPage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "雷达图")
        self.header.info.configure(text="多系列 · 悬停查看各维度数值")

        card = Card(self, title="团队能力评估")
        card.pack(fill="both", expand=True, pady=(14, 0))

        self.chart = RadarChart(
            card.row(1, fill="both", expand=True, padx=16, pady=(12, 8)),
            axes=AXES,
            max_value=100,
            height=430,
        )
        self.chart.add_series("小李", LI)
        self.chart.add_series("小王", WANG)
        self.chart.add_series("小张", ZHANG)
        self.chart.pack(fill="both", expand=True)

        row = card.row(2, fill="x", padx=16, pady=(0, 16))
        self.period = Segmented(row, ["本期", "上期"], width=168)
        self.period.pack(side="left")
        HintLabel(
            row,
            "切换时用 set_series() 只改「小李」这一组，其它人不受影响。",
        ).pack(side="left", padx=(12, 0))


class RadarPage(RadarPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.when_built(self.bind_events)

    def bind_events(self) -> None:
        """必须实现：注册页面内的事件。"""
        self.period.configure(command=self.switch_period)

    def switch_period(self, _value: str = "") -> None:
        """本期 / 上期切换：只替换小李的数据。"""
        current = self.period.get()
        self.chart.set_series("小李", LI if current == "本期" else LI_LAST)
        self.header.info.configure(text=f"小李：{current}")
