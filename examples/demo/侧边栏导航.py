import ctk_kit as ctk

"""侧边栏导航：最小用法——SidebarNav 加两个页面，切页时只创建当前页。"""

app = ctk.App(title="侧边栏导航", size=(820, 560))


def build_home(page: ctk.CTkFrame) -> ctk.CTkFrame:
    """首页：新建一个页面容器返回，控件放进这个容器里。"""
    frame = ctk.CTkFrame(page, fg_color="transparent")
    ctk.Label(frame, "这是首页，切到「设置」看看。").pack(anchor="w", padx=8, pady=(8, 12))

    card = ctk.Card(frame, title="首页卡片")
    card.pack(fill="x", padx=8)
    ctk.Label(card, "侧边栏只负责切页，页面里用什么组件都可以。").pack(
        anchor="w", padx=16, pady=14
    )
    return frame


def build_settings(page: ctk.CTkFrame) -> ctk.CTkFrame:
    """设置页：另一个独立容器，代码只在第一次切过来时执行。"""
    frame = ctk.CTkFrame(page, fg_color="transparent")
    ctk.Label(frame, "这是设置页。").pack(anchor="w", padx=8, pady=(8, 12))

    card = ctk.Card(frame, title="开关")
    card.pack(fill="x", padx=8)
    ctk.Switch(card, text="示例开关").pack(anchor="w", padx=16, pady=14)
    return frame


nav = ctk.SidebarNav(
    app,
    title="最小示例",
    subtitle="SidebarNav",
    pages={"首页": build_home, "设置": build_settings},
)
nav.pack(fill="both", expand=True)

app.mainloop()
