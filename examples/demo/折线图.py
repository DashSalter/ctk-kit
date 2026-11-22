"""折线图示例：多系列、平滑曲线、面积填充、悬停提示。"""

import ctk_kit as ctk

WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
THIS_WEEK = [120, 180, 150, 260, 310, 420, 380]
LAST_WEEK = [90, 140, 130, 190, 230, 300, 260]

app = ctk.App(title="折线图示例", size=(880, 760), min_size=(720, 600))

# ------------------------------------------------------- 多系列 + 平滑 + 面积
trend = ctk.Card(app, inside_title="一周访问趋势")
trend.pack(fill="both", expand=True, padx=24, pady=(24, 12))

chart = ctk.LineChart(
    trend.row(1, fill="both", expand=True, padx=16, pady=(14, 14)),
    categories=WEEK,
    height=260,
)
# 本周画成平滑曲线并填充面积，上周只画线
chart.add_series("本周", THIS_WEEK, smooth=True, area=True)
chart.add_series("上周", LAST_WEEK, smooth=True)
chart.pack(fill="both", expand=True)

# ------------------------------------------------------- 单系列 + 数据点 + 单位
response = ctk.Card(app, inside_title="接口响应时间")
response.pack(fill="both", expand=True, padx=24, pady=(0, 24))

latency = ctk.LineChart(
    response.row(1, fill="both", expand=True, padx=16, pady=(14, 14)),
    values=[180, 220, 195, 310, 280, 240, 210],
    name="响应时间",
    categories=["9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"],
    formatter="{:.0f} ms",
    height=200,
)
latency.pack(fill="both", expand=True)

app.mainloop()
