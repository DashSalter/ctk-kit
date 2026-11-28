"""侧边栏导航：按钮 / 输入框 / 文本三页，个人中心和设置放在底部入口。

布局和示例里的侧边栏一致：底部左边头像 + 名字进个人中心，右边齿轮进设置。
"""

import tkinter as tk

import ctk_kit as ctk

app = ctk.App(title="侧边栏导航", size=(820, 560))

#: 设置页里的主题名与 set_theme 的对应关系。
THEMES = {"云母": "mica", "霜雾": "frosted", "深空": "dark", "亚克力": "acrylic"}


def build_button(page: tk.Misc) -> tk.Misc:
    """按钮页：放一个主按钮。"""
    row = ctk.Row(page)
    row.pack(fill="x", padx=8, pady=8)
    ctk.PrimaryButton(row, "点我").pack(side="left")
    return row


def build_entry(page: tk.Misc) -> tk.Misc:
    """输入框页：放一个输入框。"""
    row = ctk.Row(page)
    row.pack(fill="x", padx=8, pady=8)
    ctk.CTkEntry(row, placeholder="输入点什么").pack(
        side="left", fill="x", expand=True
    )
    return row


def build_text(page: tk.Misc) -> tk.Misc:
    """文本页：放一个 label。"""
    row = ctk.Row(page)
    row.pack(fill="x", padx=8, pady=8)
    ctk.Label(row, "这是一段文本，放在页面里。").pack(side="left")
    return row


def build_profile(page: tk.Misc) -> tk.Misc:
    """个人中心：头像 + 名字，从示例里简化过来。"""
    frame = ctk.CTkFrame(page, fg_color="transparent")
    ctk.Avatar(frame, text="加点盐", size=88, status="online").pack(pady=(32, 12))
    ctk.Label(frame, "加点盐").pack()
    ctk.HintLabel(frame, "个人中心示例：头像 + 名字").pack(pady=(8, 0))
    return frame


def build_settings(page: tk.Misc) -> tk.Misc:
    """设置页：只放切换主题。"""
    row = ctk.Row(page)
    row.pack(fill="x", padx=8, pady=8)
    hint = ctk.HintLabel(page, "当前主题：云母")

    def switch(widget) -> None:
        name = widget.get()
        app.set_theme(THEMES[name])
        hint.configure(text=f"当前主题：{name}")

    ctk.FieldLabel(row, "主题").pack(side="left", anchor="nw")
    ctk.Segmented(
        row, list(THEMES), command=switch, width=360
    ).pack(side="left", padx=(8, 0))
    hint.pack(anchor="w", padx=8)
    return row


def build_footer(parent: ctk.CTkFrame) -> None:
    """底部：左边头像 + 名字进个人中心，右边齿轮进设置。"""
    row = ctk.Row(parent)
    row.pack(fill="x", pady=(0, 8))

    ctk.Avatar(
        row,
        text="加点盐",
        size=32,
        status="online",
        command=lambda: nav.show("个人中心"),
    ).pack(side="left")

    name = ctk.Label(row, text="加点盐", anchor="w", cursor="hand2")
    name.pack(side="left", fill="x", expand=True, padx=(8, 0))
    name.on_click(lambda _event: nav.show("个人中心"))

    ctk.CTkButton(
        row,
        text="⚙",
        width=30,
        height=28,
        fg_color="transparent",
        hover_color=ctk.tokens.COLOR_SOFT_HOVER,
        corner_radius=ctk.tokens.RADIUS_SMALL,
        command=lambda: nav.show("设置"),
    ).pack(side="right", padx=(6, 0))


nav = ctk.SidebarNav(
    app,
    title="最小示例",
    subtitle="SidebarNav",
    pages={
        "按钮": build_button,
        "输入框": build_entry,
        "文本": build_text,
    },
    hidden_pages={
        "个人中心": build_profile,
        "设置": build_settings,
    },
    footer=build_footer,
)
nav.pack(fill="both", expand=True)

app.mainloop()
