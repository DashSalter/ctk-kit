"""散点图示例：多组散点、悬停显示坐标。"""

import ctk_kit as ctk

app = ctk.App(title="散点图示例", size=(880, 620), min_size=(720, 520))

card = ctk.Card(app, inside_title="身高与体重分布")
card.pack(fill="both", expand=True, padx=24, pady=24)

chart = ctk.ScatterChart(
    card.row(1, fill="both", expand=True, padx=16, pady=(14, 14)),
    series={
        "男性": [
            (168, 62), (172, 68), (175, 72), (180, 78),
            (183, 82), (178, 75), (170, 64), (176, 70),
        ],
        "女性": [
            (155, 46), (158, 50), (161, 52), (165, 56),
            (168, 58), (160, 48), (163, 54), (157, 47),
        ],
    },
    x_range=(150, 190),
    y_range=(40, 90),
    height=360,
)
chart.pack(fill="both", expand=True)

app.mainloop()
