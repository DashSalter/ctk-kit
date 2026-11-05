"""窗口入口：把标题、尺寸这些常用设置收进构造参数。

``CTk`` 自己只收 tk 的构造参数，标题、初始尺寸、最小尺寸都得建完再逐条设置::

    app = ctk.CTk()
    app.title("备份")
    app.geometry("880x560")
    app.minsize(640, 400)

:class:`App` 是 ``CTk`` 的子类，把这几个参数挪进构造函数，一行就能建好::

    app = App(title="备份", size=(880, 560), min_size=(640, 400))

``CTk`` 仍然原样从 ``ctk_kit`` 导出；需要完全原生的入口时直接用它。
"""

from __future__ import annotations

import contextlib
from typing import Any, Optional, Sequence

from customtkinter import (
    CTk,
    get_appearance_mode,
    set_appearance_mode,
    set_default_color_theme,
)

from .branding import set_window_icon
from .core.frost_layer import FrostLayer
from .notify import Notifier
from .theme import (
    apply_appearance,
    apply_backdrop,
    freeze_redraw,
    set_titlebar_dark,
    set_window_brush,
)
from .core.win32 import (
    DWMWA_BORDER_COLOR,
    DWMWA_CAPTION_COLOR,
    DWMWA_WINDOW_CORNER_PREFERENCE,
    clear_window_alpha,
    disable_acrylic,
    enable_acrylic,
    extended_frame_bounds,
    set_dwm_attribute,
    set_frame_border_thickness,
    set_transitions_disabled,
)

__all__ = ["App"]

#: 底层颜色模式用的透明键色。DWM 只把纯黑当全透明，这个近似黑不会被
#: 当成透明，所以「看起来透明」的判定交给 -transparentcolor 自己做。
_FROST_KEY = "#010203"


class App(CTk):
    """带便捷参数的 ``CTk`` 根窗口。

    参数:
        title: 窗口标题；不传就保持 tk 的默认标题。
        size: 初始尺寸 ``(宽, 高)``，单位是逻辑像素，等价于
            ``app.geometry("宽x高")``。
        min_size: 最小尺寸 ``(宽, 高)``，用户拖不到比这更小。
        appearance: ``"light"`` / ``"dark"`` / ``"system"``；在窗口创建前生效，
            等价于 ``set_appearance_mode(...)``。
        theme: 内置主题名（``"blue"`` / ``"dark-blue"`` / ``"green"``）或自定义
            主题文件路径，等价于 ``set_default_color_theme(...)``。
        center: ``True`` 时窗口建好后按当前屏幕居中。
        notifier: 默认 ``True``，自动建好提示层 ``self.notifier``，可以直接
            ``app.notify(...)``；``False`` 时不建（也不需要提示的窗口可以关掉）。
        icon: 窗口图标。默认 ``True`` 用内置 logo；传 ``False`` 不设；
            传字符串则当成自定义 ``.ico`` / ``.png`` 路径。
        remember_geometry: 默认 ``True``，关闭时把窗口大小和位置交给 ``state``
            保存，下次启动自动恢复；没传 ``state`` 时什么都不会记。
        remember_theme: 默认 ``True``，记住上次选择的外观、颜色主题和底色，
            下次启动自动恢复；同样需要 ``state``。
        backdrop: ``"none"``（不透明）或 ``"acrylic"``（毛玻璃）；在窗口创建前
            生效，默认沿用上次的选择。也可以建好后 ``app.set_backdrop(...)``
            即时切换。
        state: 可选的"窗口状态存储"对象，见下方说明；核心库不内置持久化。
        **kwargs: 其余参数原样交给 ``CTk``，例如 ``fg_color`` / ``bg_color``。

    注意:
        ``appearance`` 与 ``theme`` 是全局设置，会影响之后创建的所有窗口和控件。

    示例::

        from ctk_kit import App

        app = App(title="备份", size=(880, 560), min_size=(640, 400), center=True)
        app.notify("已保存")                 # 等价于 app.notifier.show("已保存")
        app.mainloop()
    """

    def __init__(
        self,
        *,
        title: Optional[str] = None,
        size: Optional[Sequence[int]] = None,
        min_size: Optional[Sequence[int]] = None,
        appearance: Optional[str] = None,
        theme: Optional[str] = None,
        center: bool = False,
        notifier: bool = True,
        icon: Any = True,
        remember_geometry: bool = True,
        remember_theme: bool = True,
        backdrop: Optional[str] = None,
        state: Any = None,
        **kwargs: Any,
    ) -> None:
        """建根窗口：先应用外观/主题，再交给 ``CTk`` 完成其余初始化。

        ``state`` 是"窗口状态存储"：核心库不内置持久化，要用就把一个带
        ``read_geometry`` / ``write_geometry`` / ``read_appearance`` /
        ``write_appearance`` / ``read_color_theme`` / ``write_color_theme`` /
        ``read_backdrop`` / ``write_backdrop`` 这些方法的对象传进来（见
        ``examples/basics/window_state.py``）；不传就什么都不记。
        """
        self._state = state
        # 没显式指定就沿用上次的选择；remember_theme=False 时保持 CTk 默认。
        if remember_theme:
            if appearance is None:
                appearance = self._state_call("read_appearance")
            if theme is None:
                theme = self._state_call("read_color_theme") or None
            if backdrop is None:
                backdrop = self._state_call("read_backdrop")
        if appearance is not None:
            set_appearance_mode(appearance)
        if theme is not None:
            set_default_color_theme(theme)
        # 玻璃底色必须在建控件之前定下来：tokens 里的 COLOR_BG / COLOR_SIDE
        # 会被换成纯黑，之后创建的控件才按玻璃取值。
        self._backdrop = apply_backdrop(backdrop or "none")
        # 整窗玻璃的参数，运行时用 set_glass_options() 调（设置页有一组控件）。
        # tint 是 0xAABBGGRR：alpha 越高越暗、越低越透。默认沿用原来的 0xE6。
        self._glass = {
            "kind": "accent",   # accent / acrylic / system / mica
            "alpha": 0xE6,
            "wca": 30,          # SetWindowCompositionAttribute 的属性号，见 win32.py
            "state": 3,         # AccentState：0 关 / 2 透明 / 3 模糊 / 4 亚克力
            "backdrop": 0,      # DWMWA_SYSTEMBACKDROP_TYPE，0 表示不单独指定
            "corners": 0,       # 0 默认 / 1 不圆 / 2 圆 / 3 小圆
            "border": None,     # 34：None 默认 / DWMWA_COLOR_NONE / 颜色
            "caption": None,    # 35：None 交给 DWM / 颜色
            "color": "#181A20",
            "veil": "#000000",  # 透明键色：窗口底/侧边栏/页面底铺它，纯黑才透明
            "opacity": 1.0,     # 窗口整体透明度（-alpha），1.0 为不透明
            "frame": False,
            "extend": True,
            "titlebar": True,
            "dark": True,
        }
        # 是否调用过 wm attributes -alpha；调用过就得靠 Win32 摘 LAYERED 位复原。
        self._alpha_applied = False
        # 底层颜色窗口（毛玻璃「所看到的那张底」），None 表示没开。
        self._frost_layer: Optional[FrostLayer] = None
        # 窗口调试项（设置页的「窗口调试」卡片），不参与外观持久化。
        self._debug = {
            "hide_frame_border": False,  # 37：0 去掉那条 1px 系统边框
            "disable_transitions": False,  # 3：关掉 DWM 过渡动画
            # 37 只有 Win11 22H2+ 支持；None 表示还没探测过。
            "frame_border_supported": None,
        }

        super().__init__(**kwargs)

        self._base_fg = getattr(self, "_fg_color", None)

        self._remember_geometry = remember_geometry
        self._remember_theme = remember_theme
        self._geometry_written = False

        # 窗口还未显示时先把 TkTopLevel 的擦除画刷换成窗口底色：系统在启动、
        # 最大化、还原时先用画刷擦背景，默认是黑色，改掉后不会闪黑块。
        set_window_brush(self)

        # 玻璃模式：窗口自己的底色先刷成「透明键色」，DWM 才把这一层当透明。
        if self._backdrop == "acrylic":
            try:
                self.configure(fg_color=self._glass["veil"])
            except Exception:  # noqa: BLE001 - fg_color 不被支持时忽略
                pass

        # 登记的外壳控件：切外观时按顺序调它们的 apply_theme()，不重建。
        self._themeables: list = []

        if title is not None:
            self.title(title)
        if size is not None:
            self.geometry(f"{int(size[0])}x{int(size[1])}")
        if min_size is not None:
            self.minsize(int(min_size[0]), int(min_size[1]))
        restored = False
        if remember_geometry:
            restored = self._restore_geometry(min_size)
        if center and not restored:
            self.after_idle(self._center_on_screen)

        if icon is not False:
            if isinstance(icon, str):
                set_window_icon(self, path=icon)
            else:
                set_window_icon(self)

        # 窗口 mapped 之后 DWM 才真正接管标题栏；在这里内置标题栏颜色，
        # 调用方不用再写 ``after(10, lambda: set_titlebar_dark(...))``。
        self.after(10, self._refresh_titlebar)
        # 同理，玻璃合成也要等窗口映射之后才生效。
        self.after(10, self._refresh_backdrop)

        # 提示层挂在根窗口上：切页、缩放时都不会被页面带走。Notifier 不建
        # 控件，只有真正 show() 时才出现浮层，所以默认建一个没有额外开销。
        if notifier:
            self.notifier = Notifier(self)

        if remember_geometry:
            self.protocol("WM_DELETE_WINDOW", self._on_close)

    def notify(self, message: str, **kwargs: Any) -> Any:
        """弹出一条提示，等价于 ``self.notifier.show(message, **kwargs)``。

        参数与 :meth:`Notifier.show` 相同，例如 ``level="error"``、
        ``style="card"``、``position="bottom"``。

        返回这条提示的 ``CTkFrame``。
        """
        notifier = getattr(self, "notifier", None)
        if notifier is None:
            raise AttributeError(
                "这个 App 创建时传了 notifier=False，没有提示层；"
                "需要提示时单独建一个 Notifier(app)。"
            )
        return notifier.show(message, **kwargs)

    def register_themeable(self, widget: Any) -> None:
        """登记一个带 ``apply_theme()`` 的外壳控件，切外观时自动调用。

        适合状态栏、独立卡片这类不在 ``SidebarNav`` 页面里的控件：它们的
        颜色可以直接 ``configure`` 换掉，不需要销毁重建。重复登记同一个控件
        不会生效两次。
        """
        if widget not in self._themeables:
            self._themeables.append(widget)

    def set_appearance_mode(self, mode: str, *, save: bool = True) -> None:
        """切换外观。

        窗口里挂了 ``SidebarNav``（``self.nav``）时交给它处理——外壳原地
        换色，只重建当前页，其余页等切过去时再建；没有导航时走普通的
        :func:`apply_appearance`，已有控件一起重绘。登记过的外壳控件
        （``register_themeable``）在导航之后统一换色。

        参数:
            mode: ``"light"`` / ``"dark"`` / ``"system"``；也接受中文的
                ``"浅色"`` / ``"深色"``（分段按钮的值可以直接传进来）。
            save: 默认 ``True``，把选择写进配置，下次启动沿用；
                临时切换不想影响下次启动时传 ``False``。
        """
        if mode == "浅色":
            mode = "light"
        elif mode == "深色":
            mode = "dark"

        nav = getattr(self, "nav", None)
        setter = getattr(nav, "set_appearance_mode", None)
        if callable(setter):
            setter(mode)
        else:
            apply_appearance(mode)

        for widget in getattr(self, "_themeables", []):
            apply = getattr(widget, "apply_theme", None)
            if callable(apply):
                apply(mode)

        # 窗口类的擦除画刷跟着新底色换，避免切主题后还原窗口闪旧色。
        set_window_brush(self)

        if save and getattr(self, "_remember_theme", False):
            self._state_call("write_appearance", mode)

    def _refresh_backdrop(self) -> None:
        """窗口映射后把玻璃挂上（DWM 只对已映射的窗口生效）。"""
        self._apply_glass()
        # 玻璃挂好之后再垫底层颜色窗口：主窗口的模糊采样的是它，顺序反了
        # 就会先采到桌面、再也不会更新。
        self.after(40, self._auto_frost_layer)

    def _auto_frost_layer(self) -> None:
        """毛玻璃模式下自动建底层颜色窗口（已经有就不动）。"""
        if self._backdrop == "acrylic" and self._frost_layer is None:
            # 默认底色跟着外观走：深色配黑，浅色配白，不然字看不见。
            self.set_frost_backdrop(
                "#000000" if get_appearance_mode() == "Dark" else "#FFFFFF"
            )
        elif self._backdrop != "acrylic" and self._frost_layer is not None:
            self.clear_frost_backdrop()

    def glass_options(self) -> dict:
        """当前的毛玻璃参数（可调项见 :meth:`set_glass_options`）。"""
        return dict(self._glass)

    def set_glass_options(self, **kwargs) -> dict:
        """改一个或多个毛玻璃参数并立即重挂，返回改完后的全部参数。

        可调项：

        ``kind``
            ``"accent"``（模糊 + tint，默认）、``"acrylic"``（Win10 亚克力，
            Win11 上可能卡顿）、``"system"``（系统亚克力背板，标题栏也糊）、
            ``"mica"``（只糊壁纸）。
        ``alpha``
            0–255，越高玻璃越暗；只在 accent / acrylic 下有效。
        ``color``
            tint 的底色，``"#RRGGBB"``。
        ``opacity``
            0.1–1.0，窗口整体透明度（Tk 的 ``-alpha``）。小于 1 时窗口变成
            layered，DWM 会把系统玻璃摘掉——这个和毛玻璃是二选一的。
        ``frame``
            是否补 ``WS_THICKFRAME``（无边框窗口需要；标准窗口补了可能让
            DWM 重算非客户区）。
        ``extend``
            是否 ``DwmExtendFrameIntoClientArea(-1)``。
        ``titlebar``
            是否把标题栏交还给 DWM（``False`` 时刷成纯色，玻璃就糊不上去了）。
        ``dark``
            是否让标题栏跟随深色外观。
        """
        if "kind" in kwargs and "state" not in kwargs:
            # 换合成方式时把 AccentState 一起带上，否则会沿用上一个方式的值。
            self._glass["state"] = {"acrylic": 4}.get(kwargs["kind"], 3)
            if "backdrop" not in kwargs:
                self._glass["backdrop"] = 0
        self._glass.update(kwargs)
        if "veil" in kwargs:
            self._apply_veil()
        else:
            self._apply_glass()
        return dict(self._glass)

    def window_debug(self) -> dict:
        """当前的窗口调试项（可调项见 :meth:`set_window_debug`）。

        ``frame_border_supported`` 是探测结果：``True`` 表示当前系统认
        ``DWMWA_VISIBLE_FRAME_BORDER_THICKNESS``（37），``False`` 表示不支持
        （Win10 / Win11 21H2 及更早），``None`` 表示还没探测过。
        """
        if self._debug.get("frame_border_supported") is None:
            self._debug["frame_border_supported"] = set_frame_border_thickness(
                self, 0 if self._debug["hide_frame_border"] else 1
            )
        return dict(self._debug)

    def set_window_debug(
        self,
        *,
        hide_frame_border: Optional[bool] = None,
        disable_transitions: Optional[bool] = None,
    ) -> dict:
        """改窗口的 DWM 调试项并立即生效，返回改完后的全部参数。

        可调项：

        ``hide_frame_border``
            ``True`` 时把 ``DWMWA_VISIBLE_FRAME_BORDER_THICKNESS``（37）设成 0，
            去掉窗口四周那条 1px 系统边框；``False`` 恢复成 1。仅 Win11 22H2+
            有效，老系统上静默无效。
        ``disable_transitions``
            ``True`` 时设 ``DWMWA_TRANSITIONS_FORCEDISABLED``（3），关掉窗口
            出现、消失、重建时的 DWM 过渡动画；``False`` 恢复系统默认。
        """
        if hide_frame_border is not None:
            self._debug["hide_frame_border"] = bool(hide_frame_border)
            self._debug["frame_border_supported"] = set_frame_border_thickness(
                self, 0 if hide_frame_border else 1
            )
        if disable_transitions is not None:
            self._debug["disable_transitions"] = bool(disable_transitions)
            set_transitions_disabled(self, bool(disable_transitions))
        return dict(self._debug)

    def frame_bounds(self) -> Optional[tuple[int, int, int, int]]:
        """窗口含阴影的真实屏幕矩形 ``(left, top, right, bottom)``，物理像素。

        和 ``winfo_rootx()`` 那套（客户区坐标）比，它多出阴影和边框；弹层要
        贴屏幕边时用它算才对得齐。读不到时（非 Windows / 系统太老）返回
        ``None``。
        """
        return extended_frame_bounds(self)

    def _state_call(self, name: str, *args: Any) -> Any:
        """调一次状态存储上的方法；没接存储或调用失败都返回 ``None``。

        核心库不关心数据存在哪、什么格式，只按约定调这几个方法。
        """
        if self._state is None:
            return None
        try:
            return getattr(self._state, name)(*args)
        except Exception:  # noqa: BLE001 - 读写失败不该影响窗口本身
            return None

    def _glass_tint(self) -> int:
        """把 ``color`` + ``alpha`` 拼成 ``0xAABBGGRR``。"""
        rgb = str(self._glass["color"]).lstrip("#")
        red, green, blue = int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16)
        return (int(self._glass["alpha"]) & 0xFF) << 24 | blue << 16 | green << 8 | red

    def _apply_glass(self) -> None:
        """按 ``self._glass`` 重新挂一次玻璃（切参数、切外观时调用）。"""
        if self._backdrop != "acrylic":
            return
        opts = self._glass
        kind = opts["kind"]
        explicit_backdrop = int(opts.get("backdrop", 0) or 0)
        system_backdrop = explicit_backdrop or {"system": 3, "mica": 2}.get(kind, 0)
        # 整体透明度走 Tk 的 -alpha。注意：只要调用过一次，窗口就带上
        # WS_EX_LAYERED，DWM 立刻停止做玻璃合成——所以不透明时**一次都不调**；
        # 拖下去再拖回 100% 时，还得把 LAYERED 位摘掉玻璃才会回来。
        opacity = max(0.1, min(1.0, float(opts.get("opacity", 1.0))))
        if opacity < 1.0:
            try:
                self.attributes("-alpha", opacity)
                self._alpha_applied = True
            except Exception:  # noqa: BLE001 - 老 Tk 或平台不支持 -alpha
                pass
        elif getattr(self, "_alpha_applied", False):
            clear_window_alpha(self)
            self._alpha_applied = False
        enable_acrylic(
            self,
            tint=None if system_backdrop else self._glass_tint(),
            dark=bool(opts["dark"]),
            system_backdrop=system_backdrop,
            frame=bool(opts["frame"]),
            accent=int(opts.get("state", 3) or 3),
            attribute=int(opts.get("wca", 30)),
            extend=bool(opts["extend"]),
        )
        # 标题栏交还给 DWM：一旦设过 CAPTION_COLOR，标题栏就是不透明纯色，
        # 玻璃糊不上去。
        set_titlebar_dark(
            self, get_appearance_mode() == "Dark", glass=bool(opts["titlebar"])
        )
        corners = int(opts.get("corners", 0) or 0)
        set_dwm_attribute(
            self,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            corners - 1 if corners else None,
        )
        set_dwm_attribute(self, DWMWA_BORDER_COLOR, opts.get("border"))
        if bool(opts["titlebar"]):
            # titlebar=False 时标题栏已经被涂成纯色，这里再写就会把它盖掉。
            set_dwm_attribute(self, DWMWA_CAPTION_COLOR, opts.get("caption"))
        set_window_brush(self)

    def _apply_veil(self) -> None:
        """换「透明键色」，把窗口底 / 侧边栏 / 当前页一起换成它。

        DWM 只把 extended frame 区域里的**纯黑**当成全透明；换成近黑或深灰，
        那块区域就变成实色面板，玻璃也就跟着看不见了。所以调这个值主要是
        用来验证「底下的黑色到底透不透」，真要出玻璃得保持 ``#000000``。
        """
        veil = str(self._glass.get("veil") or "#000000")
        if self._backdrop == "acrylic":
            apply_backdrop("acrylic", veil)
            try:
                self.configure(fg_color=veil)
            except Exception:  # noqa: BLE001 - 老窗口没有 fg_color
                pass
        with freeze_redraw(self):
            self._apply_glass()
            set_window_brush(self)
        # 不能在这里同步重建：这个方法是设置页的控件回调里调的，同步重建会把
        # 正在响应点击的那个页面销毁掉。等这一轮事件处理完再重建。
        self.after_idle(self._repaint_shell)

    def set_frost_backdrop(
        self,
        color: str = "#FFFFFF",
        *,
        alpha: int = 0x38,
        glass: bool = False,
        spread: int = 0,
        save: bool = False,
    ) -> None:
        """让毛玻璃「后面」是可控的底色，而不是桌面。

        做法是双窗口：底下再开一个和主窗口等大、同位置的窗口，它自己开着
        系统毛玻璃；主窗口把客户区刷成透明键（``#010203``）并调到
        ``-transparentcolor``，于是看到的顺序是

            桌面 → 被底层窗口模糊 → 叠上 ``color`` → 上层控件

        颜色和浓度随时可改，模糊由 DWM 完成，不重画任何图。

        参数:
            color: 叠在模糊桌面上的颜色，``"#RRGGBB"``。
            alpha: 颜色浓度，``0``–``255``；``0x38`` 是「能看出颜色、还透」。
            glass: ``True`` 时这一层自己也挂系统毛玻璃（而不是纯色块）。
            spread: 底层窗口比主窗口向外多出的逻辑像素（0 = 严丝合缝）。
            save: 预留参数，暂不写入配置。

        注意:
            只有 Windows 提供系统亚克力；其他平台这一层就是一块纯色窗口。
        """
        del save  # 目前不持久化，留着是为了和 set_backdrop 的签名一致
        if self._frost_layer is None:
            self._frost_layer = FrostLayer(
                self, color=color, alpha=alpha, glass=glass, spread=spread
            )
            self._frost_layer.start()
        else:
            self._frost_layer.configure(
                color=color, alpha=alpha, glass=glass, spread=spread
            )

    def clear_frost_backdrop(self) -> None:
        """关掉底层颜色窗口。"""
        if self._frost_layer is not None:
            self._frost_layer.stop()
            self._frost_layer = None

    @property
    def frost_active(self) -> bool:
        """底层颜色窗口是否开着。"""
        return self._frost_layer is not None

    @property
    def frost_layer(self) -> Optional[FrostLayer]:
        """底层颜色窗口对象，没开时为 ``None``。"""
        return self._frost_layer

    def set_backdrop(self, mode: str = "acrylic", *, save: bool = True) -> None:
        """开启或关闭「毛玻璃」底色，默认开启。

        玻璃模式下窗口底和侧边栏都画纯黑，透出桌面的模糊；卡片、输入框
        仍是实色。切换会把外壳和当前页重建一次——颜色令牌变了，已经建好的
        控件不会自己换色。

        参数:
            mode: ``"none"`` 关闭；``"acrylic"``（也接受 ``"glass"`` /
                ``"毛玻璃"``）开启。
            save: 默认 ``True``，把选择写进配置，下次启动沿用。

        注意:
            只有 Windows 11 的 DWM 提供系统亚克力；其他平台退化成纯黑底。
        """
        if self._frost_layer is not None:
            self.clear_frost_backdrop()
        mode = apply_backdrop(mode)
        if mode == self._backdrop:
            return
        self._backdrop = mode
        with freeze_redraw(self):
            if mode == "acrylic":
                try:
                    self.configure(fg_color=self._glass["veil"])
                except Exception:  # noqa: BLE001 - fg_color 不被支持时忽略
                    pass
                self._apply_glass()
            else:
                if self._base_fg is not None:
                    try:
                        self.configure(fg_color=self._base_fg)
                    except Exception:  # noqa: BLE001 - 旧窗口没有这个属性
                        pass
                disable_acrylic(self)
                set_titlebar_dark(self, get_appearance_mode() == "Dark")
            set_window_brush(self)
            self._repaint_shell()
        # 切回毛玻璃时把底层颜色窗口也补回来。
        self.after(40, self._auto_frost_layer)
        if save and getattr(self, "_remember_theme", False):
            self._state_call("write_backdrop", mode)

    def toggle_backdrop(self) -> None:
        """在普通底色和毛玻璃之间切换。"""
        self.set_backdrop("none" if self._backdrop == "acrylic" else "acrylic")

    def _repaint_shell(self) -> None:
        """按当前颜色令牌重刷外壳和当前页（切底色后调用）。"""
        nav = getattr(self, "nav", None)
        apply = getattr(nav, "apply_theme", None)
        if callable(apply):
            apply()
        for widget in getattr(self, "_themeables", []):
            apply = getattr(widget, "apply_theme", None)
            if callable(apply):
                apply()
        rebuilder = getattr(nav, "rebuilder", None)
        if rebuilder is not None:
            rebuilder.mark_stale()
            current = rebuilder.current
            if current is not None:
                rebuilder.rebuild(current)

    def set_color_theme(self, theme: str, *, save: bool = True) -> None:
        """切换颜色主题（内置主题名或主题文件路径）。

        颜色主题只影响之后创建的控件；窗口里已有的控件不会自动换色，
        需要重建页面或重新创建窗口才能看到效果。

        参数:
            theme: ``"blue"`` / ``"dark-blue"`` / ``"green"``，或主题文件
                路径；等价于 :func:`set_default_color_theme`。
            save: 默认 ``True``，把选择写进配置，下次启动沿用。
        """
        set_default_color_theme(theme)
        if save and getattr(self, "_remember_theme", False):
            self._state_call("write_color_theme", theme)

    def toggle_appearance(self) -> None:
        """在深浅两套外观之间切换。"""
        mode = "light" if get_appearance_mode() == "Dark" else "dark"
        self.set_appearance_mode(mode)

    @property
    def current_page(self) -> Optional[str]:
        """当前显示的页面名；窗口没挂 ``SidebarNav`` 时是 ``None``。"""
        nav = getattr(self, "nav", None)
        return getattr(nav, "current", None)

    def show_page(self, name: str) -> None:
        """切到某一页，等价于 ``self.nav.show(name)``。

        参数:
            name: 页面名，必须是 ``SidebarNav`` 里注册过的页面。

        异常:
            AttributeError: 窗口没有挂 ``SidebarNav``（``self.nav``）。
        """
        nav = getattr(self, "nav", None)
        show = getattr(nav, "show", None)
        if not callable(show):
            raise AttributeError(
                "这个窗口没有挂 SidebarNav（self.nav），无法切页；"
                "先建一个 SidebarNav 并赋给 self.nav。"
            )
        show(name)

    def _refresh_titlebar(self) -> None:
        """把标题栏刷成和当前外观一致（仅 Windows 11 22H2+ 真正上色）。"""
        try:
            set_window_brush(self)
        except Exception:  # noqa: BLE001 - 窗口可能已经销毁
            pass
        try:
            set_titlebar_dark(
                self,
                get_appearance_mode() == "Dark",
                glass=self._backdrop == "acrylic",
            )
        except Exception:  # noqa: BLE001 - 窗口可能已经销毁
            pass

    def _set_appearance_mode(self, mode_string: str) -> None:
        """切外观时重刷标题栏。

        屏蔽 ``CTk`` 自带的那套标题栏逻辑（它会先 ``withdraw()`` 再
        ``deiconify()``，切换时闪一下），改用本库的 ``set_titlebar_dark``。
        """
        saved = getattr(self, "_deactivate_windows_window_header_manipulation", False)
        self._deactivate_windows_window_header_manipulation = True
        try:
            super()._set_appearance_mode(mode_string)
        finally:
            self._deactivate_windows_window_header_manipulation = saved
        try:
            self.after_idle(self._refresh_titlebar)
        except Exception:  # noqa: BLE001 - 窗口正在销毁
            pass

    def _center_on_screen(self) -> None:
        """把窗口挪到屏幕中央。

        尺寸取 CTk 自己的逻辑像素值（``_current_width`` / ``_current_height``），
        而不是 ``winfo_width()``——后者是物理像素，和逻辑像素的
        ``winfo_screenwidth()`` 混算会在高分屏上把窗口挪偏、尺寸放大。
        """
        self.update_idletasks()
        width = int(getattr(self, "_current_width", 0)) or self.winfo_width()
        height = int(getattr(self, "_current_height", 0)) or self.winfo_height()
        left = max(0, (self.winfo_screenwidth() - width) // 2)
        top = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"{width}x{height}+{left}+{top}")

    def _restore_geometry(self, min_size: Optional[Sequence[int]]) -> bool:
        """按上次保存的几何恢复窗口；没有记录或文件损坏就保持原样。

        返回是否真的恢复了；调用方据此决定还要不要居中——用户上次把窗口
        放在某个位置，就不该被 ``center=True`` 又挪回屏幕中间。
        """
        state = self._state_call("read_geometry")
        if state is None:
            return False

        width, height, x, y = state
        if min_size is not None:
            width = max(width, int(min_size[0]))
            height = max(height, int(min_size[1]))

        # -1,-1 是「没保存过位置」的哨兵；其余负坐标是合法的
        # （Windows 边缘吸附时客户区会略微跑到屏幕外），不能当成未保存。
        if x == -1 and y == -1:
            self.geometry(f"{width}x{height}")
            return False

        # 位置是物理像素；宽高是逻辑像素，夹到屏幕内之前先换回物理尺寸。
        # 只夹右边和下边：左边/上边允许为负，窗口部分贴出屏幕是正常状态。
        scale = float(getattr(self, "_window_scaling", 1.0) or 1.0)
        max_x = max(0, self.winfo_screenwidth() - int(round(width * scale)))
        max_y = max(0, self.winfo_screenheight() - int(round(height * scale)))
        x = min(x, max_x)
        y = min(y, max_y)
        self.geometry(f"{width}x{height}+{x}+{y}")
        return True

    def _save_geometry(self) -> None:
        """把当前大小和位置写进配置。最大化/最小化时保留上次的普通几何。"""
        if not getattr(self, "_remember_geometry", False):
            return
        try:
            if self.state() != "normal":
                return
            width = int(getattr(self, "_current_width", 0) or self.winfo_width())
            height = int(getattr(self, "_current_height", 0) or self.winfo_height())
            if width <= 0 or height <= 0:
                return
            # winfo_x/y 是客户区坐标，和 geometry("+x+y") 的外框坐标差一圈
            # Windows 边框；保存和恢复都用 geometry() 的 +x+y，位置才不偏。
            x, y = self.winfo_x(), self.winfo_y()
            try:
                parts = self.geometry().split("+")
                if len(parts) >= 3:
                    x, y = int(parts[1]), int(parts[2])
            except (ValueError, IndexError):
                pass
            self._state_call("write_geometry", width, height, x, y)
        except Exception:  # noqa: BLE001 - 关闭时写失败不该拦住退出
            pass

    def _on_close(self) -> None:
        self._save_geometry()
        self._geometry_written = True
        self.destroy()

    def destroy(self) -> None:
        """销毁前补存一次几何，并清掉还挂着的 after 定时器。"""
        if (
            getattr(self, "_remember_geometry", False)
            and not getattr(self, "_geometry_written", False)
        ):
            self._save_geometry()
            self._geometry_written = True
        self._cancel_pending_afters()
        if self._frost_layer is not None:
            with contextlib.suppress(Exception):
                self._frost_layer.stop()
            self._frost_layer = None
        super().destroy()

    def _cancel_pending_afters(self) -> None:
        """取消解释器里所有待触发的 after。

        Tk 的 after 定时器挂在解释器上，不随控件销毁自动取消；主窗口关掉后
        它们再触发就会报 ``invalid command name "...update"``。customtkinter
        的外观/缩放跟踪器、按钮点击动画都会留下这种定时器，所以退出前统一
        清一遍。
        """
        try:
            jobs = self.tk.call("after", "info")
        except Exception:  # noqa: BLE001 - 解释器已经没了
            return
        if isinstance(jobs, str):
            jobs = (jobs,)
        for job in jobs:
            # 直接走 Tcl 取消，不调用 after_cancel：后者会顺手 deletecommand，
            # 而命令可能注册在子窗口上、不在 App 的命令表里，子窗口销毁时
            # 再删一次就会报 "can't delete Tcl command"。
            try:
                self.tk.call("after", "cancel", job)
            except Exception:  # noqa: BLE001 - 已经被别的路径取消
                pass
