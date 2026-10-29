"""把「切主题不卡」接进自己的程序：最小可运行示例。

两个页面 + 一个切换按钮，切换时只重建正在看的那一页，其余页等切过去时再建。

运行::

    python examples/fast_theme.py
"""

from __future__ import annotations

import sys

import customtkinter as ctk

from ctk_kit import PageRebuilder, apply_appearance, is_dark, set_titlebar_dark
from ctk_kit import tokens as T
from ctk_kit.buttons import primary_button
from ctk_kit.layout import card, hint_label, page_header, section_title
from ctk_kit.theme import recolor_tree, repaint_window

PAGES = ("概览", "设置")


def build_overview(master: ctk.CTkFrame) -> ctk.CTkFrame:
    page = ctk.CTkFrame(master, fg_color="transparent")
    page_header(page, "概览")
    section_title(page, "卡片")
    box = card(page)
    ctk.CTkLabel(
        box,
        text="切主题时这一页会按新配色重建，其余页等切过去再建。",
        font=T.FONT_SMALL,
        text_color=T.COLOR_MUTED,
        wraplength=420,
        justify="left",
        anchor="w",
    ).pack(padx=16, pady=14, fill="x")
    box.pack(fill="x", pady=(0, 12))
    hint_label(page, "切到「设置」再切回来，配色都是新的。").pack(fill="x")
    scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
    scroll.pack(fill="both", expand=True, pady=(12, 0))
    for index in range(12):
        row = card(scroll)
        ctk.CTkLabel(
            row,
            text=f"第 {index + 1} 行内容",
            font=T.FONT_SMALL,
            text_color=T.COLOR_TEXT,
            anchor="w",
        ).pack(padx=16, pady=10, fill="x")
        row.pack(fill="x", pady=(0, 8))
    return page


def build_settings(master: ctk.CTkFrame, on_toggle) -> ctk.CTkFrame:
    page = ctk.CTkFrame(master, fg_color="transparent")
    page_header(page, "设置")
    section_title(page, "外观")
    box = card(page)
    primary_button(box, "切换深浅色", command=on_toggle).pack(
        padx=16, pady=14, anchor="w"
    )
    box.pack(fill="x", pady=(0, 12))
    hint_label(page, "切换后当前页立刻按新配色重建。").pack(fill="x")
    return page


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ctk-kit 快速切主题")
        self.geometry("880x560")
        self.configure(fg_color=T.COLOR_BG)

        self._sidebar = ctk.CTkFrame(
            self, width=160, corner_radius=0, fg_color=T.COLOR_SIDE, bg_color=T.COLOR_SIDE
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(side="left", fill="both", expand=True, padx=20, pady=16)

        # 页面管理交给 PageRebuilder：它负责叠放、切页、按新配色重建
        self.pages = PageRebuilder(self._body, self._build_page, PAGES)
        self.pages.build_all()

        self._buttons = {}
        for name in PAGES:
            button = ctk.CTkButton(
                self._sidebar,
                text=name,
                height=36,
                corner_radius=T.RADIUS_SMALL,
                anchor="w",
                fg_color="transparent",
                hover_color=T.COLOR_SOFT_HOVER,
                text_color=T.COLOR_MUTED,
                bg_color=T.COLOR_SIDE,
                command=lambda value=name: self.show(value),
            )
            button.pack(fill="x", padx=10, pady=2)
            self._buttons[name] = button

        self.show("概览")

    def _build_page(self, name: str) -> ctk.CTkFrame:
        if name == "概览":
            return build_overview(self._body)
        return build_settings(self._body, self.toggle_theme)

    def show(self, name: str) -> None:
        self.pages.show(name)
        self._paint_nav(name)

    def _paint_nav(self, active_name: str) -> None:
        for key, button in self._buttons.items():
            active = key == active_name
            button.configure(
                fg_color=T.COLOR_ACCENT if active else "transparent",
                bg_color=T.COLOR_SIDE,
                text_color=T.COLOR_ACCENT_TEXT if active else T.COLOR_MUTED,
            )

    def toggle_theme(self) -> None:
        mode = "light" if is_dark() else "dark"
        # 顺序：侧边栏 → 窗口底色 + 标题栏 → 当前页整块重建
        self.pages.switch(
            mode,
            before_rebuild=lambda: self._refresh_shell(mode),
            defer=True,
        )
        self.show(self.pages.current or "概览")

    def _refresh_shell(self, mode: str) -> None:
        """侧边栏不属于任何页面，自己刷；然后再刷窗口底色和标题栏。"""
        self._refresh_sidebar(mode)
        self.update_idletasks()
        repaint_window(self, "Light" if mode == "light" else "Dark")
        set_titlebar_dark(self, mode == "dark")
        self.update_idletasks()

    def _refresh_sidebar(self, mode: str) -> None:
        """父底色 + 按钮的文字/底色。"""
        self._sidebar.configure(fg_color=T.COLOR_SIDE, bg_color=T.COLOR_SIDE)
        self._paint_nav(self.pages.current or "概览")
        recolor_tree(self._sidebar, T.COLOR_SIDE, deep=False)


def main() -> int:
    apply_appearance("dark")
    app = App()
    # 窗口 mapped 之后 DWM 才会真正接管标题栏
    app.after(10, lambda: set_titlebar_dark(app, True))
    if "--where" in sys.argv:

        def report() -> None:
            print(
                f"{app.winfo_rootx()},{app.winfo_rooty()},"
                f"{app.winfo_width()},{app.winfo_height()}",
                flush=True,
            )
            app.destroy()

        app.after(900, report)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
