import ctk_kit as ctk

"""主题切换"""


def on_theme(value: str) -> None:
    app.set_theme(value)  # 只换主题，颜色用主题默认值


app = ctk.App(title="主题切换", size=(460, 140))

# ---------- 外观主题 ----------
ctk.Segmented(
    app, ["Mica", "Frosted", "Dark", "Acrylic"], width=380, command=on_theme
).pack()

ctk.DropField(
    app,
    values=["Mica", "Frosted", "Dark", "Acrylic"],
    command=on_theme,
    placeholder="点右侧箭头选择主题",
    width=380,
).pack()

app.mainloop()
