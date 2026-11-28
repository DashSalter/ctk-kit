# -*- coding: utf-8 -*-
"""散点图页：多组散点、悬停显示坐标。"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    HintLabel,
    PageBase,
    PageHeader,
    ScatterChart,
)

MALE = [
    (168, 62), (172, 68), (175, 72), (180, 78),
    (183, 82), (178, 75), (170, 64), (176, 70),
]
FEMALE = [
    (155, 46), (158, 50), (161, 52), (165, 56),
    (168, 58), (160, 48), (163, 54), (157, 47),
]


class ScatterPage(PageBase):
    """散点图页：两组数据共用同一坐标系，不需要事件。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "散点图")
        self.header.info.configure(text="多组散点 · 悬停显示坐标")

        card = Card(self, title="身高与体重分布")
        card.pack(fill="both", expand=True, pady=(14, 0))

        self.chart = ScatterChart(
            card.row(1, fill="both", expand=True, padx=16, pady=(12, 10)),
            series={"男性": MALE, "女性": FEMALE},
            x_range=(150, 190),
            y_range=(40, 90),
            height=380,
        )
        self.chart.pack(fill="both", expand=True)

        HintLabel(
            card,
            "series 的键就是图例；两组点各取一种颜色，x_range / y_range 固定坐标范围。",
        ).pack(fill="x", padx=16, pady=(0, 14))
