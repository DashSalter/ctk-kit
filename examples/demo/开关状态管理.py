import ctk_kit as ctk

app = ctk.App(title="开关示例", size=(640, 420))

card = ctk.Card(app, title="开关")
card.pack(fill="x", padx=24, pady=(24, 12))

row = ctk.Frame(card)
row.pack(fill="x", padx=16, pady=(12, 16))


# command 不带参数，当前状态用 get_value() 读
def on_toggle():
    print("启用调试：", debug.get_value())


# 带文字的开关：value=True 表示创建时就是打开的
debug = ctk.Switch(row, on_toggle, text="启用调试", value=True)
debug.pack(side="left")

# 只要轨道的紧凑开关
compact = ctk.Switch(row, width=60)
compact.pack(side="left", padx=(12, 0))

# 代码里设置、读取
compact.set_value(True)
print("紧凑开关：", "开" if compact.get_value() else "关")

# 改文字；禁用后点不动
debug.set_text("调试模式")
compact.disable()

app.mainloop()
