import ctk_kit as ctk

"""
组件的基础添加和布局
"""

app = ctk.App(
    title="上手教程",  # 窗口的标题
    size=(1000, 600),  # 窗口的显示大小
    min_size=(760, 540),  # 窗口的最小显示
)

card = ctk.Card(app, inside_title='登录').pack(fill="x", padx=24, pady=(24, 12))
# 账号输入框
row = card.row(1, fill="x", padx=16, pady=(14, 8))
ctk.FieldLabel(row, '输入你的账号:').pack(side="left", anchor="nw")
account = ctk.CTkEntry(
    row,
    width=300,
    height=36,
    placeholder_text='账号'
).pack(side="left", fill="x", expand=True, padx=(8, 0))

# 密码输入框
row = card.row(2, fill="x", padx=16, pady=(14, 8))
ctk.FieldLabel(row, '输入你的密码:').pack(side="left", anchor="nw")
pwd = ctk.CTkEntry(
    row,
    width=300,
    height=36,
    placeholder_text='密码',
    password=True
).pack(side="left", fill="x", expand=True, padx=(8, 0))

row = card.row(3, fill="x", padx=16, pady=(14, 20))
but = ctk.PrimaryButton(
    row,
    text='开始登录',
    # command=get_info #
).pack(side="left", padx=(10, 0))


def get_info():
    # 弹出账号和密码的信息
    app.notify(f"账号:{account.get()} 密码:{pwd.get()}")


# 按钮绑定点击事件
but.on_click(get_info)

app.mainloop()
