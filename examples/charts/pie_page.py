# -*- coding: utf-8 -*-
"""饼图页：环形图、实心饼图、图例与外部标签。"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    HintLabel,
    PageBase,
    PageHeader,
    PieChart,
    Segmented,
)

LABELS = ["官网", "小程序", "公众号", "其它"]
THIS_WEEK = [42, 26, 18, 14]
LAST_WEEK = [38, 30, 20, 12]

DEVICE_LABELS = ["桌面端", "移动端", "平板"]
DEVICE_VALUES = [58, 27, 15]


class PiePageUI(PageBase):
    """饼图页 UI：只建控件，切换数据留给 PiePage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "饼图")
        self.header.info.configure(text="环形 · 实心 · 图例 · 外部标签")

        self._build_traffic()
        self._build_device()

    def _build_traffic(self) -> None:
        """环形图 + 外部标签 + 图例。"""
        card = Card(self, title="流量来源")
        card.pack(fill="both", expand=True)

        self.traffic = PieChart(
            card.row(1, fill="both", expand=True, padx=16, pady=(12, 6)),
            values=THIS_WEEK,
            labels=LABELS,
            donut=0.55,
            outer_labels=True,
            legend=True,
            height=270,
        )
        self.traffic.pack(fill="both", expand=True)

        row = card.row(2, fill="x", padx=16, pady=(0, 14))
        self.period = Segmented(row, ["本周", "上周"], width=168)
        self.period.pack(side="left")
        HintLabel(
            row,
            "donut 控制空心比例，0 就是实心饼图。",
        ).pack(side="left", padx=(12, 0))

    def _build_device(self) -> None:
        """实心饼图 + 自定义配色。"""
        card = Card(self, title="访问设备")
        card.pack(fill="both", expand=True, pady=(12, 0))

        self.device = PieChart(
            card.row(1, fill="both", expand=True, padx=16, pady=(12, 10)),
            values=DEVICE_VALUES,
            labels=DEVICE_LABELS,
            colors=["#5ad8a6", "#5b8ff9", "#f6bd16"],
            height=230,
        )
        self.device.pack(fill="both", expand=True)

        HintLabel(
            card,
            "colors 按数据顺序取色；legend 默认打开，外部标签适合项数少的数据。",
        ).pack(fill="x", padx=16, pady=(0, 14))


class PiePage(PiePageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.when_built(self.bind_events)

    def bind_events(self) -> None:
        """必须实现：注册页面内的事件。"""
        self.period.configure(command=self.switch_period)

    def switch_period(self, _value: str = "") -> None:
        """本周 / 上周切换：set() 会按新数据重算百分比与扇形。"""
        current = self.period.get()
        self.traffic.set(THIS_WEEK if current == "本周" else LAST_WEEK, LABELS)
        self.header.info.configure(text=f"正在查看：{current}")
