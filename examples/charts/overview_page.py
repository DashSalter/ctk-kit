# -*- coding: utf-8 -*-
"""总览页：五类图各取一小块，一屏看完。

``PageBase`` 提供页面根容器和 ``when_built``；这里只需要建一个 2×2 的网格，
每个格子里放一张带标题的卡片和一张小图。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    BarChart,
    Card,
    Frame,
    HintLabel,
    LineChart,
    PageBase,
    PageHeader,
    PieChart,
    RadarChart,
)

WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
VISITS = [120, 180, 150, 260, 310, 420, 380]
LAST_WEEK = [90, 140, 130, 190, 230, 300, 260]


class OverviewPage(PageBase):
    """总览页：只读展示，不需要事件类。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "总览")
        self.header.info.configure(text="五种图表一屏预览")

        grid = Frame(self)
        grid.pack(fill="both", expand=True, pady=(14, 0))
        grid.columnconfigure((0, 1), weight=1, uniform="col")
        grid.rowconfigure((0, 1), weight=1, uniform="row")

        self._bar_chart(grid, 0, 0)
        self._line_chart(grid, 0, 1)
        self._pie_chart(grid, 1, 0)
        self._radar_chart(grid, 1, 1)

        HintLabel(
            self,
            "左侧可以切到每一类图的完整示例；改数据后调用 set() / set_series() 即可重画。",
        ).pack(fill="x", pady=(10, 0))

    def _cell(self, grid: tk.Misc, row: int, column: int, title: str) -> tk.Misc:
        """建一格卡片，返回内容区；四角留出间距。

        这里用 ``inside_title``：带外部 ``title`` 的 Card 会把标题 pack 到父容器，
        和网格布局的 grid 冲突。
        """
        card = Card(grid, inside_title=title)
        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=(0, 6) if column == 0 else (6, 0),
            pady=(0, 6) if row == 0 else (6, 0),
        )
        return card.row(1, fill="both", expand=True, padx=14, pady=(6, 12))

    def _bar_chart(self, grid: tk.Misc, row: int, column: int) -> None:
        chart = BarChart(
            self._cell(grid, row, column, "每周访问量"),
            values=VISITS,
            categories=WEEK,
            height=200,
        )
        chart.pack(fill="both", expand=True)

    def _line_chart(self, grid: tk.Misc, row: int, column: int) -> None:
        chart = LineChart(
            self._cell(grid, row, column, "访问趋势"),
            categories=WEEK,
            height=200,
        )
        chart.add_series("本周", VISITS, smooth=True, area=True)
        chart.add_series("上周", LAST_WEEK, smooth=True)
        chart.pack(fill="both", expand=True)

    def _pie_chart(self, grid: tk.Misc, row: int, column: int) -> None:
        chart = PieChart(
            self._cell(grid, row, column, "流量来源"),
            values=[42, 26, 18, 14],
            labels=["官网", "小程序", "公众号", "其它"],
            donut=0.55,
            legend=True,
            height=200,
        )
        chart.pack(fill="both", expand=True)

    def _radar_chart(self, grid: tk.Misc, row: int, column: int) -> None:
        chart = RadarChart(
            self._cell(grid, row, column, "能力评估"),
            axes=["沟通", "协作", "执行力", "创新", "学习", "抗压"],
            max_value=100,
            height=200,
        )
        chart.add_series("小李", [82, 76, 88, 64, 90, 72])
        chart.add_series("小王", [70, 88, 68, 84, 75, 80])
        chart.pack(fill="both", expand=True)
