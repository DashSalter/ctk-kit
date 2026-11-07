import ctk_kit as ctk

app = ctk.App(title="按钮示例", size=(640, 420))

card = ctk.Card(app, title="动作")
card.pack(fill="x", padx=24, pady=(24, 12))

ctk.PrimaryButton(card.row(1), "保存", command=lambda: print("保存")).pack(side="left")
ctk.SecondaryButton(card.row(1), "取消", command=app.destroy).pack(side="left", padx=(10, 0))
(ctk.SecondaryButton(card.row(1), "清除", command=lambda: print("清除"), border=True)
 .pack(side="left", padx=(10, 0)))
ctk.DangerButton(card.row(1), "删除", command=lambda: print("删除")).pack(side="left", padx=(10, 0))

# 卡片角落的小按钮：宽度随文字走
ctk.HintLabel(card.row(2), "查看按钮代码是如何放一行的").pack(side="left")
ctk.FlatButton(card.row(2), "复制", command=lambda: print("复制")).pack(side="right")
but = ctk.SoftButton(card.row(3), "收起")
but.pack(side="right")

# but.set_enabled(True)  # 是否启用
# but.set_text('-收起-')
# print(but.get_text())
# but.set_command(print, '收起')  # 设置点击事件

app.mainloop()
