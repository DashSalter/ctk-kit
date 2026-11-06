import ctk_kit as ctk

app = ctk.App(title="输入框示例", size=(640, 420))

card = ctk.Card(app, title="输入框")
card.pack(fill="x", padx=24, pady=(24, 12))

row = ctk.Frame(card)
row.pack(fill="x", padx=16, pady=(12, 16))

# 普通输入框：placeholder 是没输入时显示的灰色提示
name = ctk.FormEntry(row, placeholder="请输入名称")
name.pack(side="left")

# 密码框：内容显示成圆点
pwd = ctk.FormEntry(row, password=True)
pwd.pack(side="left", padx=(10, 0))

# 代码里赋值、取值
name.set_text("张三")
print("名称：", name.get_text())

# 改属性：set_ + 构造参数名
name.set_placeholder_text("改过的提示")

# 禁用与恢复（禁用后点不进去，也改不了）
pwd.disable()
pwd.enable()

app.mainloop()
