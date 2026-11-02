"""带大/小标题和翻页按钮的侧边栏，连同页面管理一起封装。

桌面程序常见的「左边一列导航、右边一页一页切」在这个模块里只暴露一个
:class:`SidebarNav`：把页面构建函数按名字交进来，它负责侧边栏、标题、导航
按钮的高亮，以及页面的按需创建与切换::

    from ctk_kit import App, SidebarNav

    app = App(title="ctk-kit", size=(1180, 780))

    def build_basic(area):
        page = ctk.CTkFrame(area, fg_color="transparent")
        ...
        return page

    nav = SidebarNav(
        app,
        title="ctk-kit",
        subtitle="v0.9.1 · 完整演示",
        pages={"基础": build_basic, "复杂": build_complex},
    )
    nav.pack(fill="both", expand=True)
    nav.show("基础")
    app.mainloop()

``SidebarNav`` 本身是 ``CTkFrame``：左边一列侧边栏，右边是页面
容器；页面由 :class:`ctk_kit.pages.PageRebuilder` 管理，切页只换层级，切外观
只重建当前页。想拿某一页的容器或它里面的子控件，用 :meth:`SidebarNav.page`
或 :attr:`SidebarNav.frames`。

``width`` 传整数是固定宽度（逻辑像素）；传 ``0`` 到 ``1`` 之间的小数则按
``SidebarNav`` 自身宽度的比例算，窗口拉宽时侧边栏一起变宽。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Dict, Mapping, Optional, Tuple, Union

import customtkinter as ctk

from . import tokens as T
from .buttons import SecondaryButton
from .fonts import get_font
from .pages import PageRebuilder
from .theme import apply_appearance_fast, color_of

__all__ = ["SidebarNav"]

# 建页函数：给父容器，返回一个已建好的页面。
PageBuilder = Callable[[tk.Misc], tk.Misc]

# 拖窗口时冻结页面布局，停手这么久之后才重排（毫秒）。
# 要比一帧的重排耗时更长，否则拖到一半就解冻、再冻结，反而更卡。
_THAW_MS = 320


class SidebarNav(ctk.CTkFrame):
    """侧边栏导航 + 页面容器。

    参数:
        master: 父容器，通常就是 ``App`` 根窗口。
        title: 侧边栏顶部的大标题。
        pages: 页面名到建页函数的映射；顺序就是导航按钮的顺序。建页函数只
            接收一个参数——页面容器，返回建好的页面。
        subtitle: 大标题下面的小字（版本号、一句话说明）。
        width: 侧边栏宽度。整数是逻辑像素（例如 200）；``0`` 到 ``1`` 之间的
            小数是按 ``SidebarNav`` 宽度的比例（例如 ``0.2`` 表示 20%），
            窗口拉宽时侧边栏跟着变宽。默认 200。
        padding: 页面区四周留白 ``(水平, 垂直)``，默认 ``(16, 16)``。
        bottom_pages: 不放进导航列表、而是放在侧边栏最下面的页面（例如
            「设置」）；值同样是建页函数，默认空。
        bottom_width: 底部按钮宽度（逻辑像素），默认 176。
        initial: 启动后直接显示的页面名；不传就显示 ``pages`` 的第一页。
        on_change: 每次切页后调用，参数是新的页面名。
        on_hide: 页面被切走时的回调，参数是那个页面容器（见 ``PageRebuilder``）。
        **kwargs: 其余参数交给 ``CTkFrame``。

    拖动窗口边缘时，页面区会先保持旧尺寸（冻结布局），松手约 320 ms 后
    再按新尺寸重排一次，避免大页面在拖动过程中逐帧重画、卡顿。

    示例::

        nav = SidebarNav(app, title="备份", pages={"任务": build_tasks, "设置": build_settings})
        nav.pack(fill="both", expand=True)
        nav.show("任务")
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str,
        pages: Mapping[str, PageBuilder],
        subtitle: str = "",
        width: Union[int, float] = 200,
        padding: Tuple[int, int] = (16, 16),
        bottom_pages: Optional[Mapping[str, PageBuilder]] = None,
        bottom_width: int = 176,
        initial: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
        on_hide: Optional[Callable[[tk.Misc], None]] = None,
        **kwargs: Any,
    ) -> None:
        if not pages and not bottom_pages:
            raise ValueError("pages 不能为空")

        kwargs.setdefault("fg_color", T.COLOR_BG)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)

        bottom_pages = dict(bottom_pages or {})
        self._builders: Dict[str, PageBuilder] = {**dict(pages), **bottom_pages}
        self._names: Tuple[str, ...] = tuple(pages) + tuple(bottom_pages)
        self._nav_names: Tuple[str, ...] = tuple(pages)
        self._bottom_pages = bottom_pages
        self._bottom_width = bottom_width
        self._on_change = on_change
        self._width = width
        self._padding = padding
        self._buttons: Dict[str, ctk.CTkButton] = {}
        self._bottom_buttons: Dict[str, ctk.CTkButton] = {}
        # 上一次高亮的导航按钮：切页时只刷变化的那两个，外观切换才全量重刷。
        self._painted_name: Optional[str] = None

        # 拖动窗口时冻结页面区：只动窗口，松手后再按新尺寸重排。
        self._frozen = False
        self._thaw_job: Optional[str] = None
        self._last_window_size: Tuple[int, int] = (0, 0)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------------------------------------------------------- 侧边栏
        # 比例模式下先按 200 建，真实宽度由 _sync_sidebar_width 定
        self.sidebar = ctk.CTkFrame(
            self,
            width=width if isinstance(width, int) else 200,
            corner_radius=0,
            fg_color=T.COLOR_SIDE,
            bg_color=T.COLOR_SIDE,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.sidebar,
            text=title,
            font=get_font((T.FONT_NAME, 16, "bold")),
            text_color=T.COLOR_TEXT,
            bg_color=T.COLOR_SIDE,
            anchor="w",
        )
        self.title_label.pack(fill="x", padx=18, pady=(22, 1))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text=subtitle,
            font=get_font(T.FONT_TINY),
            text_color=T.COLOR_MUTED,
            bg_color=T.COLOR_SIDE,
            anchor="w",
        )
        self.subtitle_label.pack(fill="x", padx=18, pady=(0, 20))

        for name in self._nav_names:
            button = ctk.CTkButton(
                self.sidebar,
                text=name,
                height=38,
                corner_radius=T.RADIUS_SMALL,
                anchor="w",
                font=get_font(T.FONT_BODY),
                fg_color="transparent",
                bg_color=T.COLOR_SIDE,
                hover_color=T.COLOR_SOFT,
                text_color=T.COLOR_MUTED,
                border_spacing=10,
                command=lambda key=name: self.show(key),
            )
            button.pack(fill="x", padx=10, pady=3)
            self._buttons[name] = button
            # 按下就切页：不等松开，把建页的耗时提前到按下瞬间。
            # CTkButton.bind 会同时绑到内部画布和文字标签，add="+" 保留自带的按下动画。
            # command 仍保留，键盘激活（空格/回车）还能正常切页。
            button.bind(
                "<ButtonPress-1>",
                lambda _event, key=name: self.show(key),
                add="+",
            )

        # 底部按钮：不在导航列表里的页面（如「设置」），放在侧边栏最下面。
        if self._bottom_pages:
            self.bottom = ctk.CTkFrame(
                self.sidebar, fg_color="transparent", bg_color=T.COLOR_SIDE
            )
            self.bottom.pack(side="bottom", fill="x", padx=12, pady=(0, 16))
            for name in self._bottom_pages:
                button = SecondaryButton(
                    self.bottom,
                    name,
                    command=lambda key=name: self.show(key),
                    width=self._bottom_width,
                )
                button.pack()
                self._bottom_buttons[name] = button

        # ---------------------------------------------------------- 页面区
        self.content = ctk.CTkFrame(self, fg_color=T.COLOR_BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")

        # 内容再套一层，留出页面边距：页面用 place 铺满它，自己不用管外边距。
        # 不用 pack：拖动窗口时要把页面区钉在旧尺寸上，只有 place 能“冻结”。
        self.body = ctk.CTkFrame(self.content, fg_color="transparent")
        self._place_body()

        self.rebuilder = PageRebuilder(
            self.body, self._create_page, self._names, on_hide=on_hide
        )
        # 启动时不把所有页面一起建出来：先只建当前页，其余页交给
        # _prewarm_pages 在空闲时间逐帧补，窗口能更快显示出来。
        self.show(initial if initial is not None else self._names[0])

        # 侧边栏宽度：先钉一次，窗口尺寸变化时再按比例重算。
        # CTkBaseClass 把 bind 禁用了，这里直接走 tkinter 的绑定。
        tk.Misc.bind(self, "<Configure>", self._on_configure, "+")
        # 页面区尺寸变化时跟着摆一次；拖动冻结期间跳过。
        tk.Misc.bind(self.content, "<Configure>", self._on_content_configure, "+")
        self.update_idletasks()
        self._sync_sidebar_width()
        self._place_body()
        # 构造时窗口可能还没 mapped，content 尺寸要等首帧；再补一次。
        self.after(1, self._place_body)

    # ------------------------------------------------------------------ 尺寸

    def _window_scale(self) -> float:
        """当前窗口缩放：96 DPI 下是 1.0，150% 缩放是 1.5。

        不用 ``winfo_fpixels("1i")``：Tk 自己未必开了 DPI 感知，读到的还是
        96；CTk 窗口自己的 ``_get_window_scaling()`` 才是实际生效的那个值。
        """
        try:
            window = self.winfo_toplevel()
            getter = getattr(window, "_get_window_scaling", None)
            if callable(getter):
                return float(getter())
        except Exception:  # noqa: BLE001 - 窗口还没建好
            pass
        try:
            from customtkinter.windows.widgets.scaling.scaling_tracker import (
                ScalingTracker,
            )

            return float(ScalingTracker.get_window_scaling(self))
        except Exception:  # noqa: BLE001 - 版本不同
            return 1.0

    def _sync_sidebar_width(self, total_px: Optional[int] = None) -> None:
        """按 ``width`` 钉住侧边栏列宽。

        ``grid`` 的 ``minsize`` 吃物理像素，所以整数宽度要先乘屏幕缩放；
        比例模式则直接按 ``SidebarNav`` 当前的物理宽度算。
        """
        if total_px is None:
            total_px = self.winfo_width()
        if isinstance(self._width, float) and 0 < self._width < 1:
            if total_px <= 1:
                return
            px = int(total_px * self._width)
        else:
            px = int(self._width * self._window_scale())
        self.grid_columnconfigure(0, minsize=max(1, px))

    def _on_configure(self, event: tk.Event) -> None:
        if event.widget is not self:
            return
        self._sync_sidebar_width(event.width)

        # 拖窗口时先冻结页面区：窗口继续变，页面保持旧尺寸，停手 320ms 后重排。
        size = (event.width, event.height)
        if self._frozen:
            if size == self._last_window_size:
                return
            self._last_window_size = size
            self._restart_thaw()
            return
        if not self._freeze_body():
            self._place_body()
            return
        self._last_window_size = size
        self._restart_thaw()

    def _on_content_configure(self, event: tk.Event) -> None:
        """页面区尺寸变化时重新摆页面容器；拖动冻结期间不动。"""
        if event.widget is not self.content:
            return
        if not self._frozen:
            self._place_body()

    def _place_body(self) -> None:
        """把页面容器摆进 ``content``，按 ``padding`` 留边。

        ``place`` 的尺寸是物理像素，``content`` 的 ``winfo_*`` 也是物理像素，
        两者直接相减即可。冻结期间不更新，页面区就停在旧尺寸上。
        """
        if self._frozen:
            return
        width, height = self.content.winfo_width(), self.content.winfo_height()
        if width <= 1 or height <= 1:
            return
        pad_x, pad_y = self._padding
        # CTkBaseClass.place 不允许传 width/height，直接走 tkinter 的 Place。
        tk.Place.place(
            self.body,
            x=pad_x,
            y=pad_y,
            width=max(1, width - pad_x * 2),
            height=max(1, height - pad_y * 2),
        )

    def _freeze_body(self) -> bool:
        """把页面区钉在当前尺寸上，返回是否成功。"""
        if self._frozen:
            return True
        width, height = self.body.winfo_width(), self.body.winfo_height()
        if width <= 1 or height <= 1:
            return False
        self._frozen = True
        return True

    def _restart_thaw(self) -> None:
        """每来一次 ``<Configure>`` 就往后推一次解冻时间。"""
        if self._thaw_job is not None:
            try:
                self.after_cancel(self._thaw_job)
            except Exception:  # noqa: BLE001 - 控件正在销毁
                pass
        self._thaw_job = self.after(_THAW_MS, self._thaw_layout)

    def _thaw_layout(self) -> None:
        """停手后按新尺寸重排一次。"""
        self._thaw_job = None
        if not self._frozen:
            return
        self._frozen = False
        self._place_body()
        try:
            self.update_idletasks()
        except Exception:  # noqa: BLE001 - 控件正在销毁
            pass

    # ------------------------------------------------------------------ 页面

    def _create_page(self, name: str) -> tk.Misc:
        try:
            builder = self._builders[name]
        except KeyError:
            raise ValueError(f"未知页面：{name!r}；可选 {list(self._names)}") from None
        return builder(self.body)

    def show(self, name: str) -> None:
        """显示某一页并高亮对应的导航按钮。"""
        self.rebuilder.show(name)
        self._paint_nav(name)
        if self._on_change is not None:
            self._on_change(name)

    def page(self, name: str) -> tk.Misc:
        """取某一页的容器；还没建出来就先建出来（但不显示）。"""
        return self.rebuilder.frame(name)

    @property
    def current(self) -> Optional[str]:
        """当前显示的页面名。"""
        return self.rebuilder.current

    @property
    def frames(self) -> Dict[str, tk.Misc]:
        """页面名到已建容器的映射。"""
        return self.rebuilder.frames

    @property
    def names(self) -> Tuple[str, ...]:
        """全部页面名，按构造时的顺序。"""
        return self._names

    # ------------------------------------------------------------------ 外观

    def _paint_nav(self, active_name: str, *, force: bool = False) -> None:
        """选中的按钮用主色实底 + 白字，其余透明底灰字。

        切页时只改「上一个选中」和「新的选中」两个按钮，其余不动——每次
        切页重刷十来个 CTkButton 的 canvas 会明显拖慢切页。外观切换时颜色
        令牌变了，传 ``force=True`` 全部重刷。
        """
        if not force and active_name == self._painted_name:
            return
        previous = self._painted_name
        self._painted_name = active_name
        accent = color_of(T.COLOR_ACCENT)
        accent_text = color_of(T.COLOR_ACCENT_TEXT)
        side = color_of(T.COLOR_SIDE)
        muted = color_of(T.COLOR_MUTED)
        for key, button in self._buttons.items():
            if key == active_name:
                button.configure(
                    fg_color=accent, bg_color=side, text_color=accent_text
                )
            elif force or key == previous:
                button.configure(
                    fg_color="transparent", bg_color=side, text_color=muted
                )

    def set_appearance_mode(self, mode: str) -> None:
        """切换外观：只重建当前页，侧边栏和标题跟着换色。

        ``mode`` 取 ``"light"`` / ``"dark"`` / ``"system"``，语义与
        ``customtkinter.set_appearance_mode`` 相同。

        顺序很重要：先切全局外观、再刷外壳、最后重建页面。页面里的
        ``Scrollable`` 会在构造时从父容器取底色，外壳没刷完就重建，页面会
        留着上一套外观的底色。
        """
        apply_appearance_fast(mode, window=self.winfo_toplevel())

        bg = color_of(T.COLOR_BG)
        side = color_of(T.COLOR_SIDE)
        self.configure(fg_color=bg)
        self.content.configure(fg_color=bg)
        self.body.configure(bg_color=bg)
        self.sidebar.configure(fg_color=side, bg_color=side)
        self.title_label.configure(text_color=color_of(T.COLOR_TEXT), bg_color=side)
        self.subtitle_label.configure(
            text_color=color_of(T.COLOR_MUTED), bg_color=side
        )
        self._paint_nav(self.rebuilder.current or "", force=True)

        soft = color_of(T.COLOR_SOFT)
        soft_hover = color_of(T.COLOR_SOFT_HOVER)
        text = color_of(T.COLOR_TEXT)
        for button in self._bottom_buttons.values():
            button.configure(
                fg_color=soft,
                hover_color=soft_hover,
                text_color=text,
            )

        # 其余页只标过期，切过去时再按新外观建；当前页立刻重建。
        self.rebuilder.mark_stale()
        current = self.rebuilder.current
        if current is not None:
            self.rebuilder.rebuild(current)

    def toggle_appearance(self) -> None:
        """在深浅两套外观之间切换。"""
        mode = "light" if ctk.get_appearance_mode() == "Dark" else "dark"
        self.set_appearance_mode(mode)
