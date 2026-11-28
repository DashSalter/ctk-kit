# -*- coding: utf-8 -*-
"""折线图页：多系列、平滑曲线、面积填充、动态改数据。"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    HintLabel,
    LineChart,
    PageBase,
    PageHeader,
    Segmented,
)

WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
THIS_WEEK = [120, 180, 150, 260, 310, 420, 380]
LAST_WEEK = [90, 140, 130, 190, 230, 300, 260]

HOURS = ["9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
NORMAL = [180, 220, 195, 310, 280, 240, 210]
PEAK = [260, 320, 300, 420, 390, 350, 310]


class LinePageUI(PageBase):
    """折线图页 UI：只建控件，切换数据留给 LinePage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "折线图")
        self.header.info.configure(text="多系列 · 平滑 · 面积填充")

        self._build_trend()
        self._build_latency()

    def _build_trend(self) -> None:
        """两条曲线：本周平滑 + 面积，上周只画线。"""
        card = Card(self, title="一周访问趋势")
        card.pack(fill="both", expand=True)

        self.trend = LineChart(
            card.row(1, fill="both", expand=True, padx=16, pady=(12, 14)),
            categories=WEEK,
            height=280,
        )
        self.trend.add_series("本周", THIS_WEEK, smooth=True, area=True)
        self.trend.add_series("上周", LAST_WEEK, smooth=True)
        self.trend.pack(fill="both", expand=True)

    def _build_latency(self) -> None:
        """单系列 + 单位格式化 + 数据切换。"""
        card = Card(self, title="接口响应时间")
        card.pack(fill="both", expand=True, pady=(12, 0))

        self.latency = LineChart(
            card.row(1, fill="both", expand=True, padx=16, pady=(12, 6)),
            values=NORMAL,
            name="响应时间",
            categories=HOURS,
            formatter="{:.0f} ms",
            height=220,
        )
        self.latency.pack(fill="both", expand=True)

        row = card.row(2, fill="x", padx=16, pady=(0, 14))
        self.load = Segmented(row, ["正常", "高峰"], width=168)
        self.load.pack(side="left")
        HintLabel(
            row,
            "切换时调用 set_series()，只换数值不重建控件。",
        ).pack(side="left", padx=(12, 0))


class LinePage(LinePageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.when_built(self.bind_events)

    def bind_events(self) -> None:
        """必须实现：注册页面内的事件。"""
        self.load.configure(command=self.switch_load)

    def switch_load(self, _value: str = "") -> None:
        """正常 / 高峰切换：只更新响应时间这组数据。"""
        current = self.load.get()
        self.latency.set_series("响应时间", NORMAL if current == "正常" else PEAK)
        self.header.info.configure(text=f"当前负载：{current}")
