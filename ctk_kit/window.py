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

from .notify import Notifier
from .theme import apply_appearance, set_titlebar_dark

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
        **kwargs: Any,
    ) -> None:
        """建根窗口：先应用外观/主题，再交给 ``CTk`` 完成其余初始化。"""
        if appearance is not None:
            set_appearance_mode(appearance)
        if theme is not None:
            set_default_color_theme(theme)

        super().__init__(**kwargs)

        if title is not None:
            self.title(title)
        if size is not None:
            self.geometry(f"{int(size[0])}x{int(size[1])}")
        if min_size is not None:
            self.minsize(int(min_size[0]), int(min_size[1]))
        if center:
            self.after_idle(self._center_on_screen)

        # 窗口 mapped 之后 DWM 才真正接管标题栏；在这里内置标题栏颜色，
        # 调用方不用再写 ``after(10, lambda: set_titlebar_dark(...))``。
        self.after(10, self._refresh_titlebar)

        # 提示层挂在根窗口上：切页、缩放时都不会被页面带走。Notifier 不建
        # 控件，只有真正 show() 时才出现浮层，所以默认建一个没有额外开销。
        if notifier:
            self.notifier = Notifier(self)

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

    def set_appearance_mode(self, mode: str) -> None:
        """切换外观。

        窗口里挂了 ``SidebarNav``（``self.nav``）时交给它处理——只重建当前页，
        其余页等切过去时再建；没有导航时走普通的 :func:`apply_appearance`，
        已有控件一起重绘。

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
