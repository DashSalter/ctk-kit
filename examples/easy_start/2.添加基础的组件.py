import ctk_kit as ctk

"""
组件的基础添加和布局
"""

app = ctk.App(
    title="上手教程",  # 窗口的标题
    size=(1000, 600),  # 窗口的显示大小
    min_size=(760, 540),  # 窗口的最小显示
)

# 创建一张卡片
card = ctk.Card(app, title='我是按钮卡片').pack(fill="x", padx=24, pady=(24, 12))

# 创建第一行的容器，放入按钮
row = card.row(1, fill="x", padx=16, pady=(14, 8))
ctk.PrimaryButton(row, text='我是按钮1').pack(side="left", padx=(10, 0))
ctk.SecondaryButton(row, text='我是按钮2').pack(side="left", padx=(10, 0))

# 创建第二行容器
row = card.row(2, fill="x", padx=16, pady=(14, 20))
ctk.SecondaryButton(row, text='我是按钮3').pack(side="left", padx=(10, 0))
ctk.SecondaryButton(row, text='我是按钮4 点我').pack(side="left", padx=(10, 0))

card = ctk.Card(app, inside_title='我是第二个卡片').pack(fill="x", padx=24, pady=(24, 12))
# 账号输入框
row = card.row(1, fill="x", padx=16, pady=(14, 8))
ctk.FieldLabel(row, '输入你的账号:').pack(side="left", anchor="nw")
ctk.CTkEntry(
    row,
    width=300,
    height=36,
    placeholder_text='账号'
).pack(side="left", fill="x", expand=True, padx=(8, 0))

# 密码输入框
row = card.row(2, fill="x", padx=16, pady=(14, 20))
ctk.FieldLabel(row, '输入你的密码:').pack(side="left", anchor="nw")
ctk.CTkEntry(
    row,
    width=300,
    height=36,
    placeholder_text='密码',
    password=True
).pack(side="left", fill="x", expand=True, padx=(8, 0))

app.mainloop()
