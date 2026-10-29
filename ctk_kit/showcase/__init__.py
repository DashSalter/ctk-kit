"""全部组件的示例窗口。

两种用法：

* 看全部页面：``ctk-kit-showcase``（或 ``python -m ctk_kit.showcase``）
* 只跑某一页：``python -m ctk_kit.showcase.pages.<名字>``，例如
  ``python -m ctk_kit.showcase.pages.buttons``、``...pages.notify``

每个页面的代码都在 ``pages/`` 下独立成文件，改哪一页就只启动哪一页，不必
把十个页面全跑一遍。
"""

from __future__ import annotations

import sys
from typing import Dict

import customtkinter as ctk

from ctk_kit import __version__
from ctk_kit import tokens as T
from ctk_kit.buttons import soft_button
from ctk_kit.notify import Notifier
from ctk_kit.pages import PageRebuilder
from ctk_kit.theme import (
    apply_appearance,
    recolor_tree,
    repaint_window,
    set_titlebar_dark,
)

from . import pages
from .data import APP_TITLE, INDEX, PAGES
from .shell import MARGIN_BOTTOM, MARGIN_TOP, MARGIN_X

__all__ = ["APP_TITLE", "INDEX", "PAGES", "ShowcaseApp", "main"]


class ShowcaseApp(ctk.CTk):
    """左侧导航 + 右侧页面，所有页面用 place 叠放。"""

    PAGES = PAGES

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        width, height = 1180, 780
        self.update_idletasks()
        left = max(0, (self.winfo_screenwidth() - width) // 2)
        top = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"{width}x{height}+{left}+{top}")
        self.minsize(960, 640)
        self.configure(fg_color=T.COLOR_BG)

        self._current = "总览"
        self._buttons: Dict[str, ctk.CTkButton] = {}

        self._sidebar = ctk.CTkFrame(
            self,
            width=200,
            corner_radius=0,
            fg_color=T.COLOR_SIDE,
            bg_color=T.COLOR_SIDE,
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)
        self._build_sidebar()

        self._area = ctk.CTkFrame(self, fg_color="transparent")
        self._area.pack(
            side="left",
            fill="both",
            expand=True,
            padx=MARGIN_X,
            pady=(MARGIN_TOP, MARGIN_BOTTOM),
        )

        # 提示浮层挂在根窗口上：切页、重建页面都不会打断正在显示的提示
        self._notifier = Notifier(self)

        self.pages = PageRebuilder(
            self._area, self._create_page, self.PAGES, on_hide=self._trim_page
        )
        self.pages.build_all()
        self.show_page("总览")
        # 窗口 mapped 之后 DWM 才会真正接管标题栏
        self.after(10, lambda: set_titlebar_dark(self, ctk.get_appearance_mode() == "Dark"))

    # ------------------------------------------------------------------ #
    def _build_sidebar(self) -> None:
        ctk.CTkLabel(
            self._sidebar,
            text="ctk-kit",
            font=(T.FONT_NAME, 16, "bold"),
            text_color=T.COLOR_TEXT,
            bg_color=T.COLOR_SIDE,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(22, 1))
        ctk.CTkLabel(
            self._sidebar,
            text=f"v{__version__} · 完整演示",
            font=T.FONT_TINY,
            text_color=T.COLOR_MUTED,
            bg_color=T.COLOR_SIDE,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 20))

        for name in self.PAGES:
            button = ctk.CTkButton(
                self._sidebar,
                text=name,
                height=38,
                corner_radius=T.RADIUS_SMALL,
                anchor="w",
                font=T.FONT_BODY,
                fg_color="transparent",
                bg_color=T.COLOR_SIDE,
                hover_color=T.COLOR_SOFT,
                text_color=T.COLOR_MUTED,
                border_spacing=10,
                command=lambda key=name: self.show_page(key),
            )
            button.pack(fill="x", padx=10, pady=3)
            self._buttons[name] = button

        bottom = ctk.CTkFrame(
            self._sidebar, fg_color="transparent", bg_color=T.COLOR_SIDE
        )
        bottom.pack(side="bottom", fill="x", padx=12, pady=(0, 16))
        # 存起来：切外观时这两层都要重刷（CTk 按钮的颜色是构造时算死的）
        self._bottom = bottom
        self._settings_button = soft_button(
            bottom, "设置", lambda: self.show_page("设置"), width=176
        )
        self._settings_button.pack()

    def _create_page(self, name: str) -> ctk.CTkFrame:
        """按页面名建一页；外观切换后单独重建某一页时也走这里。"""
        area = self._area
        if name == "总览":
            return pages.overview.build(area, navigate=self.show_page)
        if name == "基件":
            return pages.foundation.build(area)
        if name == "按钮":
            return pages.buttons.build(area)
        if name == "输入":
            return pages.inputs.build(area)
        if name == "布局":
            return pages.layout.build(area)
        if name == "提示":
            return pages.notify.build(area, notifier=self._notifier)
        if name == "列表":
            return pages.listing.build(area)
        if name == "主题":
            return pages.theme.build(area, on_toggle=self.toggle_appearance)
        if name == "表单":
            return pages.form.build(area)
        if name == "设置":
            return pages.settings.build(area, on_theme=self.set_appearance_mode)
        raise ValueError(f"未知页面：{name!r}；可选 {list(self.PAGES)}")

    def show_page(self, name: str) -> None:
        self.pages.show(name)  # 配色过期的页面会在这里被重建
        self._current = name
        self._paint_nav(name)

    def _paint_nav(self, active_name: str) -> None:
        """侧边栏导航的高亮：选中的用主色实底 + 白字，深色下也一眼能认出来。

        不用 ``COLOR_SEG_SELECTED`` 当底：那是分段控件的「选中段」色，深色下
        提亮之后和 ``COLOR_ACCENT`` 的文字凑成蓝底蓝字，反而看不清。
        """
        for key, button in self._buttons.items():
            active = key == active_name
            button.configure(
                fg_color=T.COLOR_ACCENT if active else "transparent",
                bg_color=T.COLOR_SIDE,
                text_color=T.COLOR_ACCENT_TEXT if active else T.COLOR_MUTED,
            )

    @staticmethod
    def _trim_page(page: ctk.CTkFrame) -> None:
        """离开页面时把很长的列表缩回首屏（只针对分批模式）。

        列表页滚到底加载了上百张卡后，再切回来时 Tk 要为这些控件重新排版，
        实测要 1 秒；缩回首屏后重排成本回到常数级。虚拟滚动模式本来只布局
        视口附近，卡片也复用着，切回来保持原位置即可。
        """
        listing = getattr(page, "listing", None)
        if listing is None or listing.item_height is not None:
            return
        if len(listing.cards) > 24:
            listing.reset()

    def set_appearance_mode(self, mode: str) -> None:
        """切换外观：只重建当前页，其余页等切过去再建。

        ``ctk.set_appearance_mode`` 会顺序遍历所有已注册控件、一次性全部重绘，
        实测要 380 ms 左右，切换时整窗会僵住。这里先把注册表清空再调用它——
        全局外观状态照常更新（之后新建的控件会用新配色），但已有控件一个都不
        重绘；然后只重建用户正看着的那一页（30–70 ms）。其余页面记进
        ``_stale``，等用户真的切过去时再建（见 :meth:`show_page`）。

        不在这里顺手把十页全建好：重建一页要 30–350 ms，Tk 是单线程的，连着建
        会让窗口看起来卡住一秒多，比原来的全量重绘还难受。

        页面必须**重建**而不是就地重绘：CTk 控件在滚动容器、卡片这类嵌套很深的
        结构里并不保证跟着外观重画，页面里又盖着 ``bg`` 写死的原生 ``tk.Frame``。

        为什么不在回调里直接销毁旧页：customtkinter 的 ``CTkScrollableFrame`` 在
        ``__init__`` 里挂了 ``bind_all`` 全局绑定，当场 ``destroy`` 会让事件继续
        派发给已销毁的控件（``bad window path name``）。重建走的是「先建新页、
        再销毁旧页」，新页挂好之后旧页才消失，不会留下空帧。
        """
        was_dark = ctk.get_appearance_mode() == "Dark"
        target = "Light" if mode == "light" else "Dark"
        if (target == "Dark") == was_dark:
            return

        # 顺序：侧边栏（色块小、最先落定）→ 窗口底色 + 标题栏 → 当前页整块重建。
        # 侧边栏只有十几行，先换它眼睛立刻有反馈；中间那一大块等窗口底色落定后
        # 随当前页一起整页重建（含卡片），不会出现「底色变了、卡片还是黑的」。
        # defer=True 让前面这两步真正上屏，再去重建页面：否则整个切换是一个同步
        # 调用，窗口在返回前根本没机会重绘。
        self.pages.switch(
            mode,
            before_rebuild=lambda: self._refresh_shell(target),
            defer=True,
        )
        # 这里只处理 idle 任务：把「侧边栏 + 底色已经换好」这一帧画出来。
        # 不能用 ``update()``——它会立刻把 ``after(1)`` 排队的页面重建也跑掉，
        # defer 就白设了。
        try:
            self.update_idletasks()
        except Exception:  # noqa: BLE001 - 窗口正在销毁
            pass

    def _refresh_shell(self, mode_string: str) -> None:
        """先刷侧边栏，再刷窗口底色和标题栏。"""
        self._refresh_sidebar(mode_string)
        # 让「侧边栏已换色」这一帧先上屏，再动窗口底色
        try:
            self.update_idletasks()
        except Exception:  # noqa: BLE001 - 窗口正在销毁
            pass
        repaint_window(self, mode_string)
        set_titlebar_dark(self, mode_string == "Dark")
        try:
            self.update_idletasks()
        except Exception:  # noqa: BLE001 - 窗口正在销毁
            pass

    def _refresh_sidebar(self, mode_string: str) -> None:
        """当前页重建之后刷侧边栏。

        侧边栏不整块重建（重建 14 个 CTkButton 要 150~240 ms），逐个改颜色即可：
        ``CTkButton`` 的 ``_bg_color`` 是构造时从父容器取死的，得显式重设。
        ``deep=False``：按钮内部的画布和文字由 ``_set_appearance_mode`` 自己重绘，
        再递归进去刷一遍只是白花 20 ms。
        """
        self._sidebar.configure(fg_color=T.COLOR_SIDE, bg_color=T.COLOR_SIDE)
        # 先把新配色写进每个按钮的属性，再统一让它们重绘一次（省掉每个按钮两次重绘）
        self._paint_nav(self._current or "")
        self._settings_button.configure(fg_color=T.COLOR_SOFT, bg_color=T.COLOR_SIDE)
        # deep=False 只刷直接子层：底部那层容器里的按钮要单独再刷一遍
        recolor_tree(self._bottom, T.COLOR_SIDE, mode_string, deep=False)
        recolor_tree(self._sidebar, T.COLOR_SIDE, mode_string, deep=False)
        self.update_idletasks()

    def toggle_appearance(self) -> None:
        self.set_appearance_mode(
            "light" if ctk.get_appearance_mode() == "Dark" else "dark"
        )


def main() -> int:
    apply_appearance("dark")
    app = ShowcaseApp()
    if "--page" in sys.argv:
        app.show_page(sys.argv[sys.argv.index("--page") + 1])
    if "--topmost" in sys.argv:
        app.attributes("-topmost", True)
    if "--where" in sys.argv:
        # 调试用：打印窗口矩形后退出，便于外部截图
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
