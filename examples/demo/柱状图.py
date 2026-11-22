"""柱状图示例：默认配色、逐柱配色、切换数据集。"""

import ctk_kit as ctk

WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
THIS_WEEK = [120, 180, 150, 260, 310, 420, 380]
LAST_WEEK = [90, 140, 130, 190, 230, 300, 260]

app = ctk.App(title="柱状图示例", size=(880, 760), min_size=(720, 600))

# ------------------------------------------------------------------ 默认配色
visit = ctk.Card(app, inside_title="本周访问量")
visit.pack(fill="both", expand=True, padx=24, pady=(24, 12))

chart = ctk.BarChart(
    visit.row(1, fill="both", expand=True, padx=16, pady=(14, 6)),
    values=THIS_WEEK,
    categories=WEEK,
    height=260,
)
chart.pack(fill="both", expand=True)


def switch_period(name: str) -> None:
    # 换数据只重画 canvas，控件本身不重建
    chart.set(THIS_WEEK if name == "本周" else LAST_WEEK)


# 切换数据显示
switch_row = visit.row(2, padx=16, pady=(0, 14))
period = ctk.Segmented(switch_row, ["本周", "上周"], switch_period, width=160)
period.pack(side="left")

# ------------------------------------------------------- 逐柱配色 + 固定纵轴
rate = ctk.Card(app, inside_title="各渠道转化率")
rate.pack(fill="both", expand=True, padx=24, pady=(0, 24))

channel = ctk.BarChart(
    rate.row(1, fill="both", expand=True, padx=16, pady=(14, 10)),
    values=[42, 68, 55, 81, 37],
    categories=["官网", "小程序", "公众号", "直播", "邮件"],
    colors=["#5ad8a6", "#5b8ff9", "#f6bd16", "#e8684a", "#6dc8ec"],
    y_range=(0, 100),
    formatter="{:.0f}%",
    height=220,
)
channel.pack(fill="both", expand=True)

app.mainloop()
