"""右键菜单：圆角面板 + 悬停高亮，配色跟随深浅色。

``tk.Menu`` 是系统原生菜单，圆角、描边和悬停色三个平台各长各的样，跟库里的
卡片对不上。这里不做原生菜单，改用跟下拉面板、提示浮窗同一套做法：

- 无边框 ``CTkToplevel``，窗口底色铺成描边色，卡片内缩 1px
  ——边框是「露出来的一圈底色」，会跟着窗口圆角一起弯，四角不断开
- 窗口本身交给 DWM 裁圆角（Win11），旧系统退回 ``SetWindowRgn`` 硬裁剪
- 每一项是 ``CTkButton``，悬停用 ``COLOR_SOFT_HOVER``，和下拉面板里的候选行一致

菜单是「用完即销毁」的：``show()`` 建窗口，选中某项或点到外面就 ``close()``。
"""

from __future__ import annotations

import contextlib
import inspect
import sys
import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from . import tokens as T

# 菜单项回调：点中某一项时执行。
Command = Optional[Callable[[], None]]

_ITEM_HEIGHT = 30  # 每一项的高度（逻辑像素）
_PAD = 4  # 面板内边距


class ContextMenu:
    """一个可以在任意位置弹出的右键菜单。"""

    def __init__(
        self,
        master: tk.Misc,
        *,
        width: int = 132,
        font: tuple = T.FONT_SMALL,
    ) -> None:
        """创建菜单。

        参数:
            master: 归属的控件，用来取顶层窗口与缩放比例。
            width: 面板宽度（逻辑像素）。
            font: 菜单项字体。
        """
        self._master = master
        self._width = width
        self._font = font
        self._items: list[tuple[str, Command]] = []
        self._popup: Optional[ctk.CTkToplevel] = None
        self._root_bind: Optional[str] = None
        self._focus_bind: Optional[str] = None
        self._follow_bind: Optional[str] = None
        # 唤出菜单时的屏幕位置与顶层窗口原点：窗口一动就按两者的位移跟着挪
        self._anchor: tuple[int, int] = (0, 0)
        self._origin: tuple[int, int] = (0, 0)
        self._size: tuple[int, int] = (0, 0)
        self._scaling = 1.0
        # 唤起这次菜单的控件；回调的第一个参数就是它
        self._source: Optional[tk.Misc] = None

    # ------------------------------------------------------------ 构造
    def add_command(self, label: str, command: Command = None) -> "ContextMenu":
        """追加一项；``command=None`` 时只显示文字、点了什么也不做。"""
        self._items.append((label, command))
        return self

    def add_separator(self) -> "ContextMenu":
        """追加一条分隔线。"""
        self._items.append(("", None))
        return self

    def clear(self) -> "ContextMenu":
        """清空所有项。"""
        self._items.clear()
        return self

    # ------------------------------------------------------------ 弹出
    def show(self, x: int, y: int, *, source: Optional[tk.Misc] = None) -> None:
        """在屏幕坐标 ``(x, y)`` 处弹出；已经弹出的话先收起旧的。

        参数:
            x: 屏幕横坐标（物理像素，通常直接给 ``event.x_root``）。
            y: 屏幕纵坐标（物理像素）。
            source: 唤起菜单的控件；菜单项回调会把它作为第一个参数传进去。
        """
        self.close()
        self._source = source
        if not self._items:
            return

        root = self._master.winfo_toplevel()
        try:
            scaling = root._get_window_scaling() or 1.0
        except Exception:  # noqa: BLE001 - 不是 CTk 顶层窗口
            scaling = 1.0

        popup = ctk.CTkToplevel(self._master)
        popup.withdraw()
        popup.overrideredirect(True)
        # 菜单必须浮在应用窗口之上：下拉面板也这么做，否则会被主窗口盖住
        popup.attributes("-topmost", True)
        # 窗口铺成描边色，卡片内缩 1px：边框是「露出来的一圈底色」，
        # 会跟着窗口圆角一起走，不像矩形描边那样在四个角断开。
        popup.configure(fg_color=T.COLOR_BORDER)

        body = ctk.CTkFrame(
            popup,
            fg_color=T.COLOR_CARD,
            corner_radius=max(1, T.RADIUS_MEDIUM - 1),
            border_width=0,
        )
        body.pack(fill="both", expand=True, padx=1, pady=1)

        inner = ctk.CTkFrame(body, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=_PAD, pady=_PAD)

        for label, command in self._items:
            if not label:
                ctk.CTkFrame(inner, height=1, fg_color=T.COLOR_BORDER).pack(
                    fill="x", padx=4, pady=3
                )
                continue
            ctk.CTkButton(
                inner,
                text=label,
                anchor="w",
                height=_ITEM_HEIGHT,
                corner_radius=T.RADIUS_SMALL,
                fg_color="transparent",
                hover_color=T.COLOR_SOFT_HOVER,
                text_color=T.COLOR_TEXT,
                font=self._font,
                command=lambda c=command: self._run(c),
            ).pack(fill="x", pady=(0, 1))

        popup.update_idletasks()
        # 宽高按逻辑像素给、位置直接用屏幕物理像素（和下拉面板同一套换算）；
        # 尺寸向下取整，多出来的那条像素会在圆角外露出一圈亮边。
        width = max(48, int(self._width))
        height = max(1, int((popup.winfo_reqheight() + 2) / scaling))
        x, y = self._fit_on_screen(x, y, width, height, scaling)

        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.deiconify()
        popup.update_idletasks()
        popup.lift()
        popup.bind("<Escape>", lambda _event: self.close())
        self._round_window_corners(popup, scaling)

        self._popup = popup
        self._scaling = scaling
        self._size = (width, height)
        self._anchor = (x, y)
        self._origin = (root.winfo_rootx(), root.winfo_rooty())
        # 点到菜单外面就收起（子控件的点击会冒泡到顶层窗口）
        self._root_bind = root.bind("<Button-1>", self._maybe_close, add="+")
        self._focus_bind = root.bind("<FocusOut>", self._on_root_focus_out, add="+")
        # 窗口移动/缩放时菜单跟着走，不然它会留在屏幕上原来的地方
        self._follow_bind = root.bind("<Configure>", self._follow_root, add="+")

    def close(self) -> None:
        """收起菜单；重复调用安全。"""
        root = self._master.winfo_toplevel()
        if self._root_bind is not None:
            with contextlib.suppress(Exception):
                root.unbind("<Button-1>", self._root_bind)
            self._root_bind = None
        if self._focus_bind is not None:
            with contextlib.suppress(Exception):
                root.unbind("<FocusOut>", self._focus_bind)
            self._focus_bind = None
        if self._follow_bind is not None:
            with contextlib.suppress(Exception):
                root.unbind("<Configure>", self._follow_bind)
            self._follow_bind = None
        if self._popup is not None:
            with contextlib.suppress(Exception):
                if self._popup.winfo_exists():
                    self._popup.destroy()
            self._popup = None

    @property
    def visible(self) -> bool:
        """菜单当前是否正显示。"""
        return self._popup is not None and bool(self._popup.winfo_exists())

    # ------------------------------------------------------------ 内部
    def _run(self, command: Command) -> None:
        # 先收起窗口再执行命令：回调里可能要弹对话框，菜单不该压在它下面
        self.close()
        if command is None:
            return
        source = self._source
        if source is not None and _accepts_one_arg(command):
            command(source)
        else:
            command()

    def _fit_on_screen(self, x: int, y: int, width: int, height: int, scaling: float):
        """把菜单位置收进屏幕范围，别让它在边缘被切掉。"""
        try:
            screen_w = self._master.winfo_screenwidth()
            screen_h = self._master.winfo_screenheight()
        except Exception:  # noqa: BLE001
            return int(x), int(y)
        w = int(width * scaling)
        h = int(height * scaling)
        x = max(0, min(int(x), screen_w - w - 4))
        y = max(0, min(int(y), screen_h - h - 4))
        return x, y

    def _follow_root(self, event: tk.Event) -> None:
        """主窗口移动或缩放时，让菜单跟着同样的位移。"""
        popup = self._popup
        if popup is None or not popup.winfo_exists():
            return
        root = self._master.winfo_toplevel()
        if event.widget is not root:
            return
        try:
            dx = root.winfo_rootx() - self._origin[0]
            dy = root.winfo_rooty() - self._origin[1]
        except Exception:  # noqa: BLE001
            return
        width, height = self._size
        x, y = self._fit_on_screen(
            self._anchor[0] + dx, self._anchor[1] + dy, width, height, self._scaling
        )
        with contextlib.suppress(Exception):
            popup.geometry(f"{width}x{height}+{x}+{y}")

    def _maybe_close(self, event: tk.Event) -> None:
        popup = self._popup
        if popup is None or not popup.winfo_exists():
            return
        if (
            popup.winfo_rootx()
            <= event.x_root
            <= popup.winfo_rootx() + popup.winfo_width()
            and popup.winfo_rooty()
            <= event.y_root
            <= popup.winfo_rooty() + popup.winfo_height()
        ):
            return
        self.close()

    def _on_root_focus_out(self, _event: tk.Event) -> None:
        # 切到别的程序、最小化时收起；稍等一会儿，避免刚点上菜单就被判成失焦
        self._master.after(120, self._check_focus)

    def _check_focus(self) -> None:
        if self._popup is None:
            return
        try:
            focused = self._master.winfo_toplevel().focus_get()
        except Exception:  # noqa: BLE001
            focused = None
        if focused is not None:
            name = str(focused)
            if name.startswith(str(self._popup)) or name.startswith(
                str(self._master.winfo_toplevel())
            ):
                return
        self.close()

    def _round_window_corners(self, popup: ctk.CTkToplevel, scaling: float) -> None:
        """把窗口本身裁成圆角（跟下拉面板、提示浮窗同一套）。

        优先让 Win11 的 DWM 画圆角——边缘由系统抗锯齿，没有阶梯；DWM 不可用
        （旧系统）时退回 ``SetWindowRgn`` 硬裁剪，那圈锯齿是 GDI 区域的固有代价。
        非 Windows 平台不做处理，窗口保持直角。
        """
        if sys.platform != "win32":
            return
        with contextlib.suppress(Exception):
            import ctypes

            popup.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(popup.winfo_id()) or popup.winfo_id()
            # 先清掉旧 region，否则残留的裁剪区会把 DWM 圆角整个挡住
            ctypes.windll.user32.SetWindowRgn(hwnd, None, True)
            # DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2
            preference = ctypes.c_int(2)
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)
            )
            if result == 0:
                return
            # CreateRoundRectRgn 收的是椭圆宽高（直径）
            diameter = int(T.RADIUS_MEDIUM * 2 * scaling)
            width = popup.winfo_width()
            height = popup.winfo_height()
            region = ctypes.windll.gdi32.CreateRoundRectRgn(
                0, 0, width + 1, height + 1, diameter, diameter
            )
            ctypes.windll.user32.SetWindowRgn(hwnd, region, True)


def _accepts_one_arg(func: Callable) -> bool:
    """回调能不能接一个位置参数——能就把触发菜单的控件传进去。"""
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        return False
    for parameter in signature.parameters.values():
        if parameter.kind in (
            parameter.POSITIONAL_ONLY,
            parameter.POSITIONAL_OR_KEYWORD,
            parameter.VAR_POSITIONAL,
        ):
            return True
    return False


def attach_menu(
    widget: tk.Misc,
    items=None,
    *,
    width: int = 132,
    event: str = "<Button-3>",
) -> ContextMenu:
    """给任意控件挂一个右键菜单，返回菜单对象，方便之后追加或改动。

    菜单项的写法是 ``(文字, 函数)``。函数可以接一个参数——那个参数就是
    ``widget`` 本身，所以同一个函数能复用在十几个按钮上；要再传别的参数，
    用 ``lambda button: 处理(button, "额外参数")`` 收住即可。::

        def on_edit(button):
            print("编辑", button.cget("text"))

        save = primary_button(page, "保存")
        attach_menu(save, [("编辑", on_edit), ("删除", lambda btn: remove(btn, "草稿"))])

    参数:
        widget: 挂在哪个控件上（按钮、标签、卡片、任意 ``tk.Misc`` 都行）。
        items: 菜单项，每项 ``(文字, 函数)``；函数可以是无参的。
        width: 菜单面板宽度（逻辑像素）。
        event: 触发菜单的鼠标事件，默认右键。

    返回:
        这次新建的 :class:`ContextMenu`。
    """
    menu = ContextMenu(widget, width=width)
    for label, command in items or ():
        menu.add_command(label, command)

    def _open(mouse_event: tk.Event) -> str:
        menu.show(mouse_event.x_root, mouse_event.y_root, source=widget)
        return "break"

    widget.bind(event, _open)
    if sys.platform == "darwin" and event == "<Button-3>":
        # macOS 的右键是 Button-2，也有人用 Ctrl+单击
        widget.bind("<Button-2>", _open)
        widget.bind("<Control-Button-1>", _open)
    return menu
