import ctk_kit as ctk

"""
组件如何快速放在容器的一行，以下是示例：一行里逐个 pack(side="left") 即可。
"""

app = ctk.App(title="按钮示例", size=(640, 420))

card = ctk.Card(app, title="动作").pack(fill="x", padx=24, pady=(24, 12))

row = card.row(1, fill="x", padx=16, pady=(14, 8))
ctk.PrimaryButton(row, "保存", command=lambda: print("保存")).pack(side="left")
ctk.SecondaryButton(row, "取消", command=app.destroy).pack(
    side="left", padx=(10, 0)
)
ctk.SecondaryButton(row, "清除", command=lambda: print("清除"), border=True).pack(
    side="left", padx=(10, 0)
)
ctk.DangerButton(row, "删除", command=lambda: print("删除")).pack(
    side="left", padx=(10, 0)
)

# 一行里左边说明、右边按钮：pack 的 side 控制方向
row = card.row(2, fill="x", padx=16, pady=(0, 8))
ctk.HintLabel(row, "查看按钮代码是如何放一行的").pack(side="left")
ctk.FlatButton(row, "复制", command=lambda: print("复制")).pack(side="right")

row = card.row(3, fill="x", padx=16, pady=(0, 14))
but = ctk.SoftButton(row, "收起").pack(side="right")

# but.set_enabled(True)  # 是否启用
# but.set_text('-收起-')
# print(but.get_text())
# but.set_command(print, '收起')  # 设置点击事件

app.mainloop()
