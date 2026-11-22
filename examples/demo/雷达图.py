"""雷达图示例：多系列、悬停查看各维度数值。"""

import ctk_kit as ctk

app = ctk.App(title="雷达图示例", size=(760, 680), min_size=(640, 560))

card = ctk.Card(app, inside_title="团队能力评估")
card.pack(fill="both", expand=True, padx=24, pady=24)

chart = ctk.RadarChart(
    card.row(1, fill="both", expand=True, padx=16, pady=(14, 14)),
    axes=["沟通", "协作", "执行力", "创新", "学习", "抗压"],
    max_value=100,
    height=420,
)
chart.add_series("小李", [82, 76, 88, 64, 90, 72])
chart.add_series("小王", [70, 88, 68, 84, 75, 80])
chart.add_series("小张", [75, 70, 80, 72, 68, 86])
chart.pack(fill="both", expand=True)

app.mainloop()
