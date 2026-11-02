"""页面基类：统一初始化，UI 类和事件类都从这里开始。"""

from __future__ import annotations

import tkinter as tk

from .frames import Frame


class PageBase(Frame):
    """所有页面的公共基类。

    统一在这里拿到根窗口（``App``）；主题、日志、用户信息等全局初始化
    也可以放在这里。子类只负责建界面，事件类再实现 :meth:`bind_events`。
    """

    def __init__(self, master: tk.Misc) -> None:
        """建页面容器，并把根窗口存到 ``self.app``。"""
        super().__init__(master)
        self.app = master.winfo_toplevel()

    def bind_events(self) -> None:
        """建议实现：在这里注册按钮和事件绑定。

        只是约定，不是强制；不需要绑定的页面保持空实现即可。
        """

    def on_show(self) -> None:
        """页面被切到前台时调用（默认什么都不做，按需覆写）。

        适合刷新数据、恢复滚动位置这类「每次露面都要做」的事。此时页面已经
        摆放好、尺寸也更新过了。
        """

    def on_hide(self) -> None:
        """页面被切走、或按当前外观要被重建销毁之前调用（默认什么都不做）。

        适合停掉定时器、收起很长的列表这类「离开时省点资源」的事。
        """
