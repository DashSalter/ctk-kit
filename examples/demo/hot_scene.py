# -*- coding: utf-8 -*-
"""热更新演示：改这个文件保存，窗口自动更新。

用法和普通 ``App`` 一样，只是把 ``ctk.App`` 换成 ``ctk.HotApp``。改按钮
宽高、文本、坐标，增删循环列表里的按钮，保存后只更新变化的那部分；输入
内容、滚动位置都保留。
"""

import ctk_kit as ctk
from ctk_kit import DropField

TITLE = "界面热更新"

# 工具栏按钮：(文字, 宽, 高)。增删条目、改宽高都可。
TOOLBAR = [
    ("开始", 110, 40),
    ("暂停", 96, 36),
    ("停止", 96, 36),
]

# 自由布局按钮：(文字, x, y, 宽, 高)。
FLOATING = [
    ("新增", 24, 20, 120, 44),
    ("编辑", 168, 44, 120, 44),
    ("删除", 312, 68, 120, 44),
]

app = ctk.HotApp(title=TITLE, size=(900, 640))

page = ctk.Frame(app)
page.pack(fill="both", expand=True, padx=24, pady=20)

header = ctk.PageHeader(page, TITLE)
header.info.set_text("和普通 App 用法一样，保存即更新")


bar = ctk.Card(page, inside_title="工具栏")
bar.pack(fill="x", pady=(12, 0))

toolbar = bar.row(1, fill="x")
for text, width, height in TOOLBAR:
    ctk.PrimaryButton(toolbar, text, width=width, height=height).pack(
        side="left", padx=(0, 12)
    )

toolbar = bar.row(2, fill="x")
ctk.FieldLabel(toolbar, "选择").pack(side="left")
field = DropField(
    toolbar,
    values_provider=lambda: ["选项 A", "选项 B", "选项 C"],
    command=lambda value: print(value),
    placeholder="点右侧箭头选择",
    height=36,
)
field.pack(side="left", fill="x", expand=True)

stage_card = ctk.Card(page, inside_title="自由布局")
stage_card.pack(fill="both", expand=True, pady=(12, 0))

stage = ctk.Frame(stage_card)
stage.pack(fill="both", expand=True, padx=12, pady=12)
for text, x, y, width, height in FLOATING:
    ctk.SecondaryButton(stage, text, width=width, height=height).place(x=x, y=y)

app.mainloop()
