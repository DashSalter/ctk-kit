"""饼图示例：环形图与实心饼图。"""

import ctk_kit as ctk

app = ctk.App(title="饼图示例", size=(880, 700), min_size=(720, 560))

# ---------------------------------------------------------------- 环形图
traffic = ctk.Card(app, inside_title="流量来源")
traffic.pack(fill="both", expand=True, padx=24, pady=(24, 12))

donut = ctk.PieChart(
    traffic.row(1, fill="both", expand=True, padx=16, pady=(14, 14)),
    values=[42, 26, 18, 14],
    labels=["官网", "小程序", "公众号", "其它"],
    donut=0.55,
    height=260,
)
donut.pack(fill="both", expand=True)

# ---------------------------------------------------------------- 实心饼图
device = ctk.Card(app, inside_title="访问设备")
device.pack(fill="both", expand=True, padx=24, pady=(0, 24))

pie = ctk.PieChart(
    device.row(1, fill="both", expand=True, padx=16, pady=(14, 14)),
    values=[58, 27, 15],
    labels=["桌面端", "移动端", "平板"],
    colors=["#5ad8a6", "#5b8ff9", "#f6bd16"],
    height=240,
)
pie.pack(fill="both", expand=True)

app.mainloop()
