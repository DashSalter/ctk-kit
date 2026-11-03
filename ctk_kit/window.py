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

from typing import Any, Optional, Sequence

from customtkinter import (
    CTk,
    get_appearance_mode,
    set_appearance_mode,
    set_default_color_theme,
)

from .branding import set_window_icon
from .notify import Notifier
from .preferences import read_geometry, write_geometry
from .theme import apply_appearance, set_titlebar_dark, set_window_brush

__all__ = ["App"]


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
        remember_geometry: 默认 ``True``，关闭时把窗口大小和位置写进配置，
            下次启动自动恢复；传 ``False`` 关掉。
        config_path: 记住几何用的配置文件；不传用
            ``~/.ctk-kit/window.json``。多个应用各记各的时传不同路径。
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
        config_path: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """建根窗口：先应用外观/主题，再交给 ``CTk`` 完成其余初始化。"""
        if appearance is not None:
            set_appearance_mode(appearance)
        if theme is not None:
            set_default_color_theme(theme)

        super().__init__(**kwargs)

        self._remember_geometry = remember_geometry
        self._config_path = config_path
        self._geometry_written = False

        # 窗口还未显示时先把 TkTopLevel 的擦除画刷换成窗口底色：系统在启动、
        # 最大化、还原时先用画刷擦背景，默认是黑色，改掉后不会闪黑块。
        set_window_brush(self)

        # 登记的外壳控件：切外观时按顺序调它们的 apply_theme()，不重建。
        self._themeables: list = []

        if title is not None:
            self.title(title)
        if size is not None:
            self.geometry(f"{int(size[0])}x{int(size[1])}")
        if min_size is not None:
            self.minsize(int(min_size[0]), int(min_size[1]))
        if remember_geometry:
            self._restore_geometry(min_size)
        if center:
            self.after_idle(self._center_on_screen)

        if icon is not False:
            if isinstance(icon, str):
                set_window_icon(self, path=icon)
            else:
                set_window_icon(self)

        # 窗口 mapped 之后 DWM 才真正接管标题栏；在这里内置标题栏颜色，
        # 调用方不用再写 ``after(10, lambda: set_titlebar_dark(...))``。
        self.after(10, self._refresh_titlebar)

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

    def set_appearance_mode(self, mode: str) -> None:
        """切换外观。

        窗口里挂了 ``SidebarNav``（``self.nav``）时交给它处理——外壳原地
        换色，只重建当前页，其余页等切过去时再建；没有导航时走普通的
        :func:`apply_appearance`，已有控件一起重绘。登记过的外壳控件
        （``register_themeable``）在导航之后统一换色。

        参数:
            mode: ``"light"`` / ``"dark"`` / ``"system"``；也接受中文的
                ``"浅色"`` / ``"深色"``（分段按钮的值可以直接传进来）。
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
            set_titlebar_dark(self, get_appearance_mode() == "Dark")
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

    def _restore_geometry(self, min_size: Optional[Sequence[int]]) -> None:
        """按上次保存的几何恢复窗口；没有记录或文件损坏就保持原样。"""
        state = read_geometry(self._config_path)
        if state is None:
            return

        width, height, x, y = state
        if min_size is not None:
            width = max(width, int(min_size[0]))
            height = max(height, int(min_size[1]))

        # 没有保存过位置（-1）时只恢复大小，位置交给 CTk 的默认行为。
        if x < 0 or y < 0:
            self.geometry(f"{width}x{height}")
            return

        # 位置是物理像素；宽高是逻辑像素，夹到屏幕内之前先换回物理尺寸。
        scale = float(getattr(self, "_window_scaling", 1.0) or 1.0)
        max_x = max(0, self.winfo_screenwidth() - int(round(width * scale)))
        max_y = max(0, self.winfo_screenheight() - int(round(height * scale)))
        x = max(0, min(x, max_x))
        y = max(0, min(y, max_y))
        self.geometry(f"{width}x{height}+{x}+{y}")

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
            write_geometry(width, height, self.winfo_x(), self.winfo_y(), self._config_path)
        except Exception:  # noqa: BLE001 - 关闭时写失败不该拦住退出
            pass

    def _on_close(self) -> None:
        self._save_geometry()
        self._geometry_written = True
        self.destroy()

    def destroy(self) -> None:
        """销毁前补存一次几何，``app.destroy()`` 直接关闭时也能记住。"""
        if (
            getattr(self, "_remember_geometry", False)
            and not getattr(self, "_geometry_written", False)
        ):
            self._save_geometry()
            self._geometry_written = True
        super().destroy()
