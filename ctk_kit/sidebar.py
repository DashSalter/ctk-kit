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
        subtitle="v0.9.2 · 完整演示",
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
from .branding import logo_path
from .buttons import SecondaryButton
from .fonts import get_font
from .pages import PageRebuilder
from .styles import style_of
from .theme import apply_appearance_fast, freeze_redraw

__all__ = ["SidebarNav"]


# 建页函数：给父容器，返回一个已建好的页面。
PageBuilder = Callable[[tk.Misc], tk.Misc]

# 拖窗口时冻结页面布局，停手这么久之后才重排（毫秒）。
# 要比一帧的重排耗时更长，否则拖到一半就解冻、再冻结，反而更卡。
_THAW_MS = 320


def _load_logo(spec: Union[bool, str], size: int):
    """把 ``logo`` 参数变成 ``CTkImage``：``True`` 用内置图，``False`` 不显示。

    传字符串时读自定义图片。用 ``CTkImage`` 而不是裸 ``PhotoImage``，HighDPI
    缩放下才会跟着一起缩放。
    """
    if spec is False or not spec:
        return None

    from PIL import Image

    path = logo_path(size) if spec is True else spec
    image = Image.open(path).convert("RGBA")
    return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))


def _repaint_subtree(widget: tk.Misc, mode: str) -> None:
    """让子树里已有的 CTk 控件换到指定外观，只重绘、不重建。

    ``apply_appearance_fast`` 切主题时会跳过所有已有控件（这样才不卡），外壳
    靠 ``apply_theme`` 逐个换色；调用方塞进 footer 的自定义控件不在这套流程里，
    在这里统一补一次。
    """
    for child in widget.winfo_children():
        setter = getattr(child, "_set_appearance_mode", None)
        if callable(setter):
            try:
                setter(mode)
            except tk.TclError:
                return
        _repaint_subtree(child, mode)


class SidebarNav(ctk.CTkFrame):
    """侧边栏导航 + 页面容器。

    参数:
        master: 父容器，通常就是 ``App`` 根窗口。
        title: 侧边栏顶部的大标题。
        pages: 页面名到建页函数的映射；顺序就是导航按钮的顺序。建页函数只
            接收一个参数——页面容器，返回建好的页面。
        subtitle: 大标题下面的小字（版本号、一句话说明）。
        logo: 大标题左侧的图标。``True``（默认）用内置 logo，``False`` 不显示，
            传字符串则用自定义图片路径。
        logo_size: 图标边长（逻辑像素），默认 32。
        width: 侧边栏宽度。整数是逻辑像素（例如 200）；``0`` 到 ``1`` 之间的
            小数是按 ``SidebarNav`` 宽度的比例（例如 ``0.2`` 表示 20%），
            窗口拉宽时侧边栏跟着变宽。默认 200。
        padding: 页面区四周留白 ``(水平, 垂直)``，默认 ``(16, 16)``。
        bottom_pages: 不放进导航列表、而是放在侧边栏最下面的页面（例如
            「设置」）；值同样是建页函数，默认空。
        hidden_pages: 只登记页面、不生成导航按钮（例如从头像点进去的
            「个人中心」）；``show(name)`` 仍然可以切过去。
        footer: 底部按钮上方的自定义区域，参数是底部容器；可以放头像、
            账号行之类。头像行会排在 ``bottom_pages`` 按钮的上方。
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
        logo: Union[bool, str] = True,
        logo_size: int = 32,
        width: Union[int, float] = 200,
        padding: Tuple[int, int] = (16, 16),
        bottom_pages: Optional[Mapping[str, PageBuilder]] = None,
        hidden_pages: Optional[Mapping[str, PageBuilder]] = None,
        footer: Optional[Callable[[ctk.CTkFrame], None]] = None,
        bottom_width: int = 176,
        initial: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
        on_hide: Optional[Callable[[tk.Misc], None]] = None,
        **kwargs: Any,
    ) -> None:
        """建侧边栏与页面容器；只创建当前页，其余页等切过去再建。"""
        if not pages and not bottom_pages:
            raise ValueError("pages 不能为空")

        kwargs.setdefault("fg_color", T.COLOR_BG)
        kwargs.setdefault("corner_radius", 0)
        super().__init__(master, **kwargs)

        bottom_pages = dict(bottom_pages or {})
        hidden_pages = dict(hidden_pages or {})
        self._builders: Dict[str, PageBuilder] = {
            **dict(pages),
            **bottom_pages,
            **hidden_pages,
        }
        self._names: list[str] = (
            list(pages) + list(bottom_pages) + list(hidden_pages)
        )
        self._nav_names: list[str] = list(pages)
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

        # 顶部品牌区：logo 在左，大标题 / 小标题在右，两行字整体与 logo 垂直居中。
        self._logo_size = max(16, int(logo_size))
        self._logo_image = _load_logo(logo, self._logo_size)
        self._head = ctk.CTkFrame(
            self.sidebar, fg_color="transparent", bg_color=T.COLOR_SIDE
        )
        self._head.pack(fill="x", padx=18, pady=(22, 20))

        if self._logo_image is not None:
            self.logo_label = ctk.CTkLabel(
                self._head,
                text="",
                image=self._logo_image,
                width=self._logo_size,
                height=self._logo_size,
                fg_color="transparent",
                bg_color=T.COLOR_SIDE,
            )
            self.logo_label.pack(side="left", padx=(0, 10))

        self._title_box = ctk.CTkFrame(
            self._head, fg_color="transparent", bg_color=T.COLOR_SIDE
        )
        self._title_box.pack(side="left", fill="x", expand=True)

        self.title_label = ctk.CTkLabel(
            self._title_box,
            text=title,
            font=get_font((T.FONT_NAME, 16, "bold")),
            text_color=T.COLOR_TEXT,
            bg_color=T.COLOR_SIDE,
            anchor="w",
        )
        self.title_label.pack(fill="x")

        self.subtitle_label = ctk.CTkLabel(
            self._title_box,
            text=subtitle,
            font=get_font(T.FONT_TINY),
            text_color=T.COLOR_MUTED,
            bg_color=T.COLOR_SIDE,
            anchor="w",
        )
        self.subtitle_label.pack(fill="x", pady=(1, 0))

        for name in self._nav_names:
            self._add_nav_button(name)

        # 底部：先放自定义区域（例如账号头像），再放「设置」这类按钮。
        if self._bottom_pages or footer is not None:
            bottom = self._ensure_bottom()
            if footer is not None:
                footer(bottom)
            for name in self._bottom_pages:
                self._add_bottom_button(name)

        # ---------------------------------------------------------- 页面区
        self.content = ctk.CTkFrame(self, fg_color=T.COLOR_BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")

        # 内容再套一层，留出页面边距：页面用 place 铺满它，自己不用管外边距。
        # 不用 pack：拖动窗口时要把页面区钉在旧尺寸上，只有 place 能“冻结”。
        self.body = ctk.CTkFrame(self.content, fg_color="transparent")
        self._place_body()

        self.rebuilder = PageRebuilder(
            self.body,
            self._create_page,
            self._names,
            on_hide=on_hide,
            first_of=self._first_of,
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

    # ------------------------------------------------------------------ 按钮

    def _ensure_bottom(self) -> ctk.CTkFrame:
        """确保底部分区存在（构造时没有底部页、后来动态加页才需要建）。"""
        bottom = getattr(self, "bottom", None)
        if bottom is None:
            bottom = ctk.CTkFrame(
                self.sidebar, fg_color="transparent", bg_color=T.COLOR_SIDE
            )
            bottom.pack(side="bottom", fill="x", padx=12, pady=(0, 16))
            self.bottom = bottom
        return bottom

    def _add_nav_button(self, name: str) -> ctk.CTkButton:
        """建一个导航按钮并挂到侧边栏（构造与动态加页共用）。"""
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
        return button

    def _add_bottom_button(self, name: str) -> ctk.CTkButton:
        """建一个底部按钮并挂到底部分区（构造与动态加页共用）。"""
        button = SecondaryButton(
            self._ensure_bottom(),
            name,
            command=lambda key=name: self.show(key),
            width=self._bottom_width,
        )
        button.pack()
        self._bottom_buttons[name] = button
        return button

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
        """窗口尺寸变化：重算侧边栏宽度，并冻结/解冻页面区。"""
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
        """按页面名调用建页函数；名字不存在时列出可选项。"""
        try:
            builder = self._builders[name]
        except KeyError:
            raise ValueError(f"未知页面：{name!r}；可选 {list(self._names)}") from None
        return builder(self.body)

    def _first_of(self, name: str) -> int:
        """页面声明的 ``cards_first``；启动构建据此决定跳不跳过。"""
        builder = self._builders.get(name)
        try:
            return int(getattr(builder, "cards_first", 0) or 0)
        except (TypeError, ValueError):
            return 0

    def show(self, name: str) -> None:
        """显示某一页并高亮对应的导航按钮。"""
        self.rebuilder.show(name)
        # 页面刚 pack 上，先把已建好的部分画出来；分帧补建的卡片才有
        # 中间的可见状态，而不是全部建完才一次性刷新。
        try:
            self.update_idletasks()
        except tk.TclError:
            pass
        self._paint_nav(name)
        if self._on_change is not None:
            self._on_change(name)

    def page(self, name: str) -> tk.Misc:
        """取某一页的容器；还没建出来就先建出来（但不显示）。"""
        return self.rebuilder.frame(name)

    def add_page(
        self, name: str, builder: PageBuilder, *, bottom: bool = False
    ) -> None:
        """动态加一页：建导航按钮（或底部按钮），页面等切过去时再建。

        参数:
            name: 页面名，不能与已有页面重名。
            builder: 建页函数，接收页面容器、返回页面。
            bottom: ``True`` 加到侧边栏底部，样式和 ``bottom_pages`` 一致。
        """
        if name in self._builders:
            raise ValueError(f"页面已存在：{name!r}；可选 {list(self._names)}")
        self._builders[name] = builder
        self._names.append(name)
        self.rebuilder.add_page(name)
        if bottom:
            self._bottom_pages[name] = builder
            self._add_bottom_button(name)
        else:
            self._nav_names.append(name)
            self._add_nav_button(name)
        self._paint_nav(self.rebuilder.current or "", force=True)

    def remove_page(self, name: str) -> None:
        """动态删一页：销毁导航按钮与页面容器。

        不能删正在显示的页面；需要的话先 :meth:`show` 到别的页再删。

        参数:
            name: 页面名。

        异常:
            ValueError: 页面不存在，或者它是当前唯一页面。
        """
        if name not in self._builders:
            raise ValueError(f"未知页面：{name!r}；可选 {list(self._names)}")
        if name == self.rebuilder.current:
            others = [key for key in self._names if key != name]
            if not others:
                raise ValueError("不能删除唯一的页面")
            self.show(others[0])
        self._builders.pop(name, None)
        if name in self._names:
            self._names.remove(name)
        if name in self._nav_names:
            self._nav_names.remove(name)
        self._bottom_pages.pop(name, None)
        button = self._buttons.pop(name, None)
        if button is None:
            button = self._bottom_buttons.pop(name, None)
        if button is not None:
            try:
                button.destroy()
            except Exception:  # noqa: BLE001 - 控件可能已经销毁
                pass
        if self._painted_name == name:
            self._painted_name = None
        self.rebuilder.remove_page(name)

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
        """全部页面名，按当前顺序（动态加页/删页后会变）。"""
        return tuple(self._names)

    # ------------------------------------------------------------------ 外观

    def _paint_nav(
        self, active_name: str, *, force: bool = False, mode: Optional[str] = None
    ) -> None:
        """选中的按钮用主色实底 + 白字，其余透明底灰字。

        切页时只改「上一个选中」和「新的选中」两个按钮，其余不动——每次
        切页重刷十来个 CTkButton 的 canvas 会明显拖慢切页。外观切换时颜色
        令牌变了，传 ``force=True`` 全部重刷。
        """
        if not force and active_name == self._painted_name:
            return
        previous = self._painted_name
        self._painted_name = active_name
        active = style_of("sidebar", "nav_active", mode)
        normal = style_of("sidebar", "nav_normal", mode)
        for key, button in self._buttons.items():
            if key == active_name:
                button.configure(**active)
            elif force or key == previous:
                button.configure(**normal)

    def apply_theme(self, mode: Optional[str] = None) -> None:
        """只刷外壳颜色（侧边栏、标题、导航、底部按钮），不重建页面。

        参数:
            mode: ``"light"`` / ``"dark"`` / ``"system"``；不传取当前外观。
                调用前要确保全局外观已经切好，否则 CTk 的自动色对仍按旧外观
                取色。``set_appearance_mode()`` 会按正确顺序调用它。
        """
        shell = style_of("sidebar", "shell", mode)
        side = style_of("sidebar", "side", mode)

        self.configure(**shell)
        self.content.configure(**style_of("sidebar", "content", mode))
        self.body.configure(bg_color=shell["fg_color"])
        self.sidebar.configure(**side)
        self._head.configure(fg_color="transparent", bg_color=side["bg_color"])
        self._title_box.configure(fg_color="transparent", bg_color=side["bg_color"])
        if self._logo_image is not None:
            self.logo_label.configure(bg_color=side["bg_color"])
        self.title_label.configure(**style_of("sidebar", "title", mode))
        self.subtitle_label.configure(**style_of("sidebar", "subtitle", mode))
        self._paint_nav(self.rebuilder.current or "", force=True, mode=mode)

        bottom = style_of("sidebar", "bottom", mode)
        for button in self._bottom_buttons.values():
            button.configure(**bottom)

        # footer 是调用方自己塞进来的控件（头像、名字、设置按钮），外壳不知道
        # 里面有什么，统一让子树里已有的 CTk 控件按新外观重绘一次。
        footer = getattr(self, "bottom", None)
        if footer is not None:
            _repaint_subtree(footer, "Light" if mode == "light" else "Dark")

    def set_appearance_mode(self, mode: str) -> None:
        """切换外观：外壳原地换色，只重建当前页。

        ``mode`` 取 ``"light"`` / ``"dark"`` / ``"system"``，语义与
        ``customtkinter.set_appearance_mode`` 相同。

        顺序很重要：先切全局外观、再刷外壳、最后重建页面。页面里的
        ``Scrollable`` 会在构造时从父容器取底色，外壳没刷完就重建，页面会
        留着上一套外观的底色。

        整个过程包在 :class:`ctk_kit.theme.freeze_redraw` 里：重建当前页要几十到
        上百毫秒，不冻结绘制的话，中间会先合成一帧「外壳已是新色、页面还是旧
        色」，看起来就是切主题时闪一下。
        """
        window = self.winfo_toplevel()
        with freeze_redraw(window):
            apply_appearance_fast(mode, window=window)

            # 外壳控件只 configure 换色，不销毁重建；页面内容仍按需重建。
            self.apply_theme(mode)

            # 其余页只标过期，切过去时再按新外观建；当前页立刻重建。
            self.rebuilder.mark_stale()
            current = self.rebuilder.current
            if current is not None:
                self.rebuilder.rebuild(current)

    def toggle_appearance(self) -> None:
        """在深浅两套外观之间切换。"""
        mode = "light" if ctk.get_appearance_mode() == "Dark" else "dark"
        self.set_appearance_mode(mode)
