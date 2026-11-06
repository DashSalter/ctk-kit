import ctk_kit as ctk

"""主题切换：一个下拉/分段就能换玻璃主题，颜色可以单独改。"""

app = ctk.App(title="主题切换", size=(760, 540), backdrop="acrylic")

# ---------- 外观主题 ----------
card = ctk.Card(app, title="外观主题")
card.pack(fill="x", padx=24, pady=(24, 12))


def on_theme(value: str) -> None:
    app.set_theme(value)  # 只换主题，颜色用主题默认值


ctk.Segmented(
    card, ["Mica", "Frosted", "Dark", "Acrylic"], width=380, command=on_theme
).pack(side="left", padx=10, pady=10)

card2 = ctk.Card(app, title="测试组件")
card2.pack(fill="x", padx=24, pady=(24, 12))

ctk.SecondaryButton(card2, text='按钮').pack(side="left",padx=10, pady=10)

app.mainloop()
