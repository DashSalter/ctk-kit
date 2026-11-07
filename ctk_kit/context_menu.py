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
import time
import tkinter as tk
import weakref
from typing import Callable, Optional, Union

import customtkinter as ctk

from . import tokens as T
from .core.win32 import clear_window_alpha
from .popup import round_window_corners



# 菜单面板底色。比卡片浅一档，浮在玻璃/页面之上时边界更清楚。
_MENU_BG = "#2B2B2B"
# 菜单项悬停色：比底色亮一档，扫过时能看出是哪一行。
_MENU_HOVER = "#575A63"

# 菜单项回调：点中某一项时执行。
Command = Optional[Callable[[], None]]
# 菜单项可用性：布尔值表示固定状态；函数在每次弹出前以来源控件为参数求值。
Enabled = Optional[Union[bool, Callable[[tk.Misc], bool]]]

_ITEM_HEIGHT = 30  # 每一项的高度（逻辑像素）
_PAD = 4  # 面板内边距
# 展开：淡入 + 从下方滑入；收起只做淡出（毫秒 / 帧间隔 / 滑入距离逻辑像素）
_OPEN_ANIM_MS = 120
_ANIM_STEP = 16
_OPEN_SLIDE = 4
_CLOSE_ANIM_MS = 90

# 挂在控件上的属性名：记着这块控件上挂的是哪个菜单，重复挂载时先解掉旧的
_MENU_ATTR = "_ctk_kit_menu"
_EDIT_MENU_ATTR = "_ctk_kit_edit_menu"

# 整个应用同时只允许一个菜单：右键另一个控件时，先把上一个收掉
_OPEN_MENUS: "weakref.WeakSet[ContextMenu]" = weakref.WeakSet()


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
        self._items: list[tuple[str, Command, Enabled]] = []
        self._bind_ids: list[tuple[tk.Misc, str, str]] = []
        self._popup: Optional[ctk.CTkToplevel] = None
        self._root_bind: Optional[str] = None
        self._focus_bind: Optional[str] = None
        self._follow_bind: Optional[str] = None
        # 唤出菜单时的屏幕位置与顶层窗口原点：窗口一动就按两者的位移跟着挪
        self._anchor: tuple[int, int] = (0, 0)
        self._origin: tuple[int, int] = (0, 0)
        self._size: tuple[int, int] = (0, 0)
        self._scaling = 1.0
        # 展开/收起动画：淡入淡出期间 _popup 先摘掉，避免和关闭逻辑打架
        self._anim_job: Optional[str] = None
        self._anim_started: float = 0.0
        self._closing: Optional[ctk.CTkToplevel] = None
        self._close_job: Optional[str] = None
        # 唤起这次菜单的控件；回调的第一个参数就是它
        self._source: Optional[tk.Misc] = None

    # ------------------------------------------------------------ 构造
    def add_command(
        self, label: str, command: Command = None, *, enabled: Enabled = None
    ) -> "ContextMenu":
        """追加一项。

        参数:
            label: 显示文字。
            command: 点中后执行；``None`` 时只显示文字、点了什么也不做。
            enabled: 可用性。``None`` / ``True`` 总是可用，``False`` 总是灰掉；
                传函数时在每次弹出前以来源控件为参数求值——用它做「没选区就灰掉
                复制、剪贴板空就灰掉粘贴」这类判定。
        """
        self._items.append((label, command, enabled))
        return self

    def add_separator(self) -> "ContextMenu":
        """追加一条分隔线。"""
        self._items.append(("", None, None))
        return self

    def clear(self) -> "ContextMenu":
        """清空所有项。"""
        self._items.clear()
        return self

    def has_command(self, label: str) -> bool:
        """菜单里有没有叫 ``label`` 的项（分隔线不算）。"""
        return any(item_label == label for item_label, _c, _e in self._items)

    def remove_command(self, label: str) -> "ContextMenu":
        """删掉第一个叫 ``label`` 的项；没有就什么也不做。

        只删文字完全相同的第一项，重名项要删几次就调几次。删完顺手去掉
        因此孤零零留下来的分隔线。
        """
        for index, (item_label, _command, _enabled) in enumerate(self._items):
            if item_label == label:
                del self._items[index]
                self._drop_orphan_separators()
                break
        return self

    def rename_command(self, label: str, new_label: str) -> "ContextMenu":
        """把第一个叫 ``label`` 的项改成 ``new_label``；没有就什么也不做。"""
        for index, (item_label, command, enabled) in enumerate(self._items):
            if item_label == label:
                self._items[index] = (new_label, command, enabled)
                break
        return self

    def _drop_orphan_separators(self) -> None:
        """去掉开头、结尾和连续的分隔线：删项后不该留一条孤零零的线。"""
        cleaned: list[tuple[str, Command, Enabled]] = []
        for item in self._items:
            if item[0] == "":
                if not cleaned or cleaned[-1][0] == "":
                    continue
            cleaned.append(item)
        while cleaned and cleaned[-1][0] == "":
            cleaned.pop()
        self._items[:] = cleaned

    # ------------------------------------------------------------ 弹出
    def show(self, x: int, y: int, *, source: Optional[tk.Misc] = None) -> None:
        """在屏幕坐标 ``(x, y)`` 处弹出；已经弹出的话先收起旧的。

        参数:
            x: 屏幕横坐标（物理像素，通常直接给 ``event.x_root``）。
            y: 屏幕纵坐标（物理像素）。
            source: 唤起菜单的控件；菜单项回调会把它作为第一个参数传进去。
        """
        self.close()
        # 上一块还在淡出：立刻收掉，免得两块菜单叠在一起
        self._finish_closing()
        self._source = source
        if not self._items:
            return
        # 别的控件上还开着菜单就先收掉：一个窗口里同时只留一个
        for other in list(_OPEN_MENUS):
            if other is not self:
                other.close()
        _OPEN_MENUS.add(self)

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
            fg_color=_MENU_BG,
            # 圆角跟系统 DWM 圆角对齐，免得四角露出比 1px 粗的描边。
            corner_radius=T.RADIUS_SMALL,
            border_width=0,
        )
        body.pack(fill="both", expand=True, padx=1, pady=1)

        inner = ctk.CTkFrame(body, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=_PAD, pady=_PAD)

        for label, command, enabled in self._items:
            if not label:
                ctk.CTkFrame(inner, height=1, fg_color=T.COLOR_BORDER).pack(
                    fill="x", padx=4, pady=3
                )
                continue
            available = self._is_enabled(enabled, source)
            ctk.CTkButton(
                inner,
                text=label,
                anchor="w",
                height=_ITEM_HEIGHT,
                corner_radius=T.RADIUS_SMALL,
                fg_color="transparent",
                hover_color=_MENU_HOVER,
                text_color=T.COLOR_TEXT,
                text_color_disabled=T.COLOR_FAINT,
                font=self._font,
                state="normal" if available else "disabled",
                command=lambda c=command: self._run(c),
            ).pack(fill="x", pady=(0, 1))

        popup.update_idletasks()
        # 宽高按逻辑像素给、位置直接用屏幕物理像素（和下拉面板同一套换算）；
        # 尺寸向下取整，多出来的那条像素会在圆角外露出一圈亮边。
        width = max(48, int(self._width))
        height = max(1, int((popup.winfo_reqheight() + 2) / scaling))
        x, y = self._fit_on_screen(x, y, width, height, scaling)

        popup.geometry(f"{width}x{height}+{x}+{y}")
        # 先透明再显示，避免第一帧整块不透明地闪出来
        with contextlib.suppress(tk.TclError):
            popup.attributes("-alpha", 0.0)
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
        self._start_open_anim()

    def close(self, *, animate: bool = True) -> None:
        """收起菜单；重复调用安全。"""
        _OPEN_MENUS.discard(self)
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
        if self._anim_job is not None:
            with contextlib.suppress(Exception):
                self._master.after_cancel(self._anim_job)
            self._anim_job = None
        popup = self._popup
        self._popup = None
        if popup is None:
            return
        # 更早的一块还没淡完，先收掉
        self._finish_closing()
        if animate:
            with contextlib.suppress(tk.TclError):
                if popup.winfo_exists():
                    self._start_close_anim(popup)
                    return
        with contextlib.suppress(Exception):
            if popup.winfo_exists():
                popup.destroy()

    # ------------------------------------------------------------ 展开/收起动画
    def _start_open_anim(self) -> None:
        """菜单显示后开始淡入 + 下滑；窗口不支持 alpha 时只做下滑。"""
        if self._popup is None:
            return
        self._anim_started = time.perf_counter()
        self._anim_job = self._master.after(1, self._open_step)

    def _open_step(self) -> None:
        self._anim_job = None
        popup = self._popup
        if popup is None:
            return
        try:
            alive = bool(popup.winfo_exists())
        except tk.TclError:
            return
        if not alive:
            return
        width, height = self._size
        x, y = self._anchor
        slide = int(_OPEN_SLIDE * self._scaling)
        ratio = (time.perf_counter() - self._anim_started) / (_OPEN_ANIM_MS / 1000.0)
        done = ratio >= 1.0
        eased = 1.0 if done else 1.0 - (1.0 - ratio) ** 3
        offset = 0 if done else int(round((1.0 - eased) * slide))
        with contextlib.suppress(tk.TclError):
            popup.geometry(f"{width}x{height}+{x}+{y + offset}")
            popup.attributes("-alpha", 1.0 if done else round(eased, 3))
        if done:
            # 淡入结束摘掉 WS_EX_LAYERED：layered 窗口的内容是位图合成，
            # 125% 缩放下文字会被重采样得发虚
            with contextlib.suppress(Exception):
                clear_window_alpha(popup)
            return
        self._anim_job = self._master.after(_ANIM_STEP, self._open_step)

    def _finish_closing(self) -> None:
        """立刻结束上一块正在淡出的菜单。"""
        if self._close_job is not None:
            with contextlib.suppress(Exception):
                self._master.after_cancel(self._close_job)
            self._close_job = None
        popup = self._closing
        self._closing = None
        if popup is not None:
            with contextlib.suppress(Exception):
                if popup.winfo_exists():
                    popup.destroy()

    def _start_close_anim(self, popup: ctk.CTkToplevel) -> None:
        """淡出后销毁；菜单收起不做位移，淡完就没了。"""
        started = time.perf_counter()
        self._closing = popup

        def step() -> None:
            self._close_job = None
            if self._closing is not popup:
                return
            try:
                alive = bool(popup.winfo_exists())
            except tk.TclError:
                alive = False
            if not alive:
                self._closing = None
                return
            ratio = (time.perf_counter() - started) / (_CLOSE_ANIM_MS / 1000.0)
            done = ratio >= 1.0
            eased = 1.0 if done else 1.0 - (1.0 - ratio) ** 3
            with contextlib.suppress(tk.TclError):
                popup.attributes("-alpha", 0.0 if done else round(1.0 - eased, 3))
            if done:
                self._closing = None
                with contextlib.suppress(Exception):
                    popup.destroy()
                return
            with contextlib.suppress(tk.TclError):
                self._close_job = self._master.after(_ANIM_STEP, step)

        with contextlib.suppress(tk.TclError):
            self._close_job = self._master.after(1, step)

    @property
    def visible(self) -> bool:
        """菜单当前是否正显示。"""
        return self._popup is not None and bool(self._popup.winfo_exists())

    # ------------------------------------------------------------ 内部
    @staticmethod
    def _is_enabled(spec: Enabled, source: Optional[tk.Misc]) -> bool:
        """求值某一项的可用性；判定函数抛异常时按不可用处理，别让整块菜单炸掉。"""
        if spec is None:
            return True
        if callable(spec):
            try:
                return bool(spec(source))
            except Exception:  # noqa: BLE001
                return False
        return bool(spec)

    def _unbind(self) -> None:
        """解掉这个菜单挂出去的所有绑定（重新挂载时用来清掉旧的）。"""
        for target, sequence, func_id in self._bind_ids:
            with contextlib.suppress(Exception):
                target.unbind(sequence, func_id)
        self._bind_ids = []

    def _run(self, command: Command) -> None:
        """收起菜单再执行命令；命令接受一个参数时把触发控件传进去。"""
        # 先收起窗口再执行命令：回调里可能要弹对话框，菜单不该压在它下面
        # 点完立即消失，不播收起动画，免得淡出的菜单浮在随后的对话框上
        self.close(animate=False)
        if command is None:
            return
        source = self._source
        if source is not None and _accepts_one_arg(command):
            command(source)
        else:
            command()
        # 点完菜单把焦点还给输入框：不然接着敲键盘什么都不会发生
        inner = _text_widget(source) if source is not None else None
        if inner is not None:
            with contextlib.suppress(Exception):
                inner.focus_set()

    def _fit_on_screen(self, x: int, y: int, width: int, height: int, scaling: float) -> tuple[int, int]:
        """把菜单位置收进屏幕：右边放不下就翻到鼠标左边，下面放不下就翻到上边。

        屏幕边界取 ``winfo_vrootwidth / vrootheight``：这两个是**物理**像素，
        和 ``winfo_pointerxy``、``event.x_root`` 同一套坐标。``winfo_screenwidth``
        是逻辑值（本机 1707，物理是 2560），拿它比会把菜单一路夹到左边去。
        """
        try:
            screen_w = self._master.winfo_vrootwidth() or self._master.winfo_screenwidth()
            screen_h = (
                self._master.winfo_vrootheight() or self._master.winfo_screenheight()
            )
        except Exception:  # noqa: BLE001
            return int(x), int(y)
        w = int(width * scaling)
        h = int(height * scaling)
        x = int(x)
        y = int(y)
        if x + w > screen_w - 4:
            x = x - w  # 翻到鼠标左侧，右边缘贴着鼠标
        if y + h > screen_h - 4:
            y = y - h  # 翻到鼠标上方
        x = max(4, min(x, max(4, screen_w - w - 4)))
        y = max(4, min(y, max(4, screen_h - h - 4)))
        return x, y

    def _follow_root(self, event: tk.Event) -> None:
        """主窗口移动或缩放时，让菜单跟着同样的位移。"""
        popup = self._popup
        if popup is None or not popup.winfo_exists():
            return
        # 展开动画期间位置由动画控制，等它跑完再跟随
        if self._anim_job is not None:
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
        """点击位置落在菜单外面时收起菜单。"""
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
        """主窗口失焦后稍等再检查焦点，避免刚点菜单就被判成失焦。"""
        # 切到别的程序、最小化时收起；稍等一会儿，避免刚点上菜单就被判成失焦
        self._master.after(120, self._check_focus)

    def _check_focus(self) -> None:
        """确认焦点还在菜单或主窗口上；不在了就收起菜单。"""
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
        """把窗口本身裁成圆角，公共逻辑在 :mod:`ctk_kit.popup`。"""
        # 半径跟内部卡片同值：窗口比卡片更圆时，四角会露出一圈粗描边。
        round_window_corners(popup, T.RADIUS_SMALL, scaling)


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


def _inner_widgets(widget: tk.Misc) -> list:
    """CTk 控件真正露脸的是内部 canvas / frame，只绑外层点不到。"""
    inner = []
    for name in ("_canvas", "_parent_frame", "_entry", "_textbox", "_text_label"):
        child = getattr(widget, name, None)
        if child is not None and hasattr(child, "bind"):
            inner.append(child)
    return inner


def _bind_targets(widget: tk.Misc, deep: bool) -> list:
    """收集要绑右键的控件：自身 + 内部可见部分（+ 可选的所有子控件）。"""
    targets: list = []
    seen: set = set()
    stack = [widget]
    while stack:
        current = stack.pop()
        for target in [current, *_inner_widgets(current)]:
            if id(target) in seen:
                continue
            seen.add(id(target))
            targets.append(target)
        if deep:
            stack.extend(current.winfo_children())
    return targets


def attach_menu(
    widget: tk.Misc,
    items=None,
    *,
    width: int = 132,
    event: str = "<Button-3>",
    deep: bool = False,
) -> ContextMenu:
    """给任意控件挂一个右键菜单，返回菜单对象，方便之后追加或改动。

    菜单项的写法是 ``(文字, 函数)``。函数可以接一个参数——那个参数就是
    ``widget`` 本身，所以同一个函数能复用在十几个按钮上；要再传别的参数，
    用 ``lambda button: 处理(button, "额外参数")`` 收住即可。::

        def on_edit(button):
            print("编辑", button.cget("text"))

        save = PrimaryButton(page, "保存")
        attach_menu(save, [("编辑", on_edit), ("删除", lambda btn: remove(btn, "草稿"))])

    参数:
        widget: 挂在哪个控件上（按钮、标签、卡片、任意 ``tk.Misc`` 都行）。
        items: 菜单项，每项 ``(文字, 函数)``；函数可以是无参的。
        width: 菜单面板宽度（逻辑像素）。
        event: 触发菜单的鼠标事件，默认右键。
        deep: 是否连容器里的子控件一起挂上。给卡片、面板这类容器传 ``True``，
            右键落在里面的文字或子控件上也能弹出。

    返回:
        这次新建的 :class:`ContextMenu`。
    """
    menu = ContextMenu(widget, width=width)
    for label, command in items or ():
        menu.add_command(label, command)

    def _open(mouse_event: tk.Event) -> str:
        """右键回调：按指针位置弹菜单，固定返回 ``"break"`` 阻止继续冒泡。"""
        # 用指针的屏幕坐标而不是 event.x_root：事件从内部 canvas 冒上来时，
        # 某些 tk 版本给的 x_root 会偏，菜单就跑得离鼠标很远
        try:
            pointer_x, pointer_y = widget.winfo_pointerxy()
        except Exception:  # noqa: BLE001
            pointer_x, pointer_y = mouse_event.x_root, mouse_event.y_root
        menu.show(pointer_x, pointer_y, source=widget)
        return "break"

    # 后挂的菜单替换先挂的：同一个控件上不该叠出两套菜单
    _detach_menus(widget)
    targets = _bind_targets(widget, deep)
    menu._bind_ids = _bind_open(targets, event, _open)
    setattr(widget, _MENU_ATTR, menu)
    return menu


def _bind_open(
    targets: list, event: str, handler: Callable[[tk.Event], str]
) -> list[tuple[tk.Misc, str, str]]:
    """把同一个弹出回调挂到一组控件上，返回绑定 id，方便之后整组解绑。

    一律用 ``add="+"``：控件上可能已经有调用方自己的右键绑定（或 Tk 自带的
    系统菜单），覆盖式 ``bind`` 会把它们悄悄吃掉。回调返回 ``"break"``，
    所以后挂的不会执行，但也不会被删除。
    """
    ids: list[tuple[tk.Misc, str, str]] = []
    for target in targets:
        ids.append((target, event, target.bind(event, handler, add="+")))
    if sys.platform == "darwin" and event == "<Button-3>":
        # macOS 的右键是 Button-2，也有人用 Ctrl+单击
        for target in targets:
            for sequence in ("<Button-2>", "<Control-Button-1>"):
                ids.append((target, sequence, target.bind(sequence, handler, add="+")))
    return ids


def _detach_menus(widget: tk.Misc) -> None:
    """解掉控件上先前由本模块挂的菜单绑定（后挂的替换先挂的）。"""
    for attr in (_MENU_ATTR, _EDIT_MENU_ATTR):
        previous = getattr(widget, attr, None)
        if isinstance(previous, ContextMenu):
            previous._unbind()
        with contextlib.suppress(Exception):
            setattr(widget, attr, None)


# ------------------------------------------------------------ 输入框默认菜单
def attach_edit_menu(
    widget: tk.Misc,
    items=None,
    *,
    preset: bool = True,
    width: int = 132,
    reset: bool = False,
) -> ContextMenu:
    """给输入类控件挂「复制 / 粘贴 / 剪切 / 清空」右键菜单，返回菜单对象。

    这是 :func:`attach_menu` 的一个预设。默认项会按控件当前状态自动置灰：
    没选中文字时「剪切 / 复制」灰掉，剪贴板里没有文本时「粘贴」灰掉，
    输入框为空时「清空」灰掉——菜单里不该出现点了没反应的项。

    ``widget`` 可以是本库的 ``CTkEntry`` / ``TextArea``，也可以是
    customtkinter 的 ``CTkEntry`` / ``CTkTextbox``：内部会自己找到真正
    承载文字的 ``tk.Entry`` / ``tk.Text``。

    重复调用返回**同一个**菜单对象，不会叠出两套；这次传的 ``items`` 会追加
    到已有菜单末尾::

        entry = CTkEntry(frame)
        menu = attach_edit_menu(entry)
        menu.add_command("全选", select_all)      # 追加一项

        # 也可以这样追加；没有第二套菜单，只有多出来的一项
        attach_edit_menu(entry, [("插入时间戳", stamp)])

    参数:
        widget: 输入类控件（单行、多行都行）。
        items: 自定义项，每项 ``(文字, 函数)``；函数可以接一个参数（控件本身）。
            首次挂载时排在默认项后面（中间自动加分隔线），之后每次调用都是
            纯追加，不加分隔线。
        preset: 首次挂载时是否带上默认的四项。``False`` 时菜单里只有
            ``items``；控件已经挂过菜单时这个参数不起作用（除非 ``reset=True``）。
        width: 菜单面板宽度（逻辑像素），默认 132；同样只在首次挂载时生效。
        reset: 丢掉控件上现有的菜单重新建一套。默认项被删掉、改乱之后想恢复
            原样时用它::

                attach_edit_menu(entry, reset=True)   # 恢复成默认四项

    返回:
        这次挂上的 :class:`ContextMenu`。
    """
    existing = getattr(widget, _EDIT_MENU_ATTR, None)
    if isinstance(existing, ContextMenu) and not reset:
        # 已经挂过：把这次传的项追加进去，不重复建一套菜单。
        # preset 此时无意义——默认项在第一次挂载时就已经决定了。
        for label, command in items or ():
            existing.add_command(label, command)
        return existing

    menu = ContextMenu(widget, width=width)
    if preset:
        menu.add_command(
            "复制", lambda w: _run_virtual(w, "<<Copy>>"), enabled=_has_selection
        )
        menu.add_command(
            "粘贴",
            lambda w: _run_virtual(w, "<<Paste>>"),
            enabled=lambda w: not _is_readonly(w) and bool(_clipboard_text(w)),
        )
        menu.add_command(
            "剪切",
            lambda w: _run_virtual(w, "<<Cut>>"),
            enabled=lambda w: _has_selection(w) and not _is_readonly(w),
        )
        menu.add_separator()
        menu.add_command(
            "清空",
            _clear_text,
            enabled=lambda w: not _is_readonly(w) and bool(_text_of(w)),
        )

    extra = list(items or ())
    if extra:
        if preset:
            menu.add_separator()
        for label, command in extra:
            menu.add_command(label, command)

    def _open(mouse_event: tk.Event) -> str:
        """右键回调：先把光标挪到点击处、切到可编辑状态，再弹菜单。"""
        _prepare_edit(widget, mouse_event)
        try:
            pointer_x, pointer_y = widget.winfo_pointerxy()
        except Exception:  # noqa: BLE001
            pointer_x, pointer_y = mouse_event.x_root, mouse_event.y_root
        menu.show(pointer_x, pointer_y, source=widget)
        return "break"

    _detach_menus(widget)
    menu._bind_ids = _bind_open(_edit_targets(widget), "<Button-3>", _open)
    setattr(widget, _EDIT_MENU_ATTR, menu)
    return menu


def _edit_targets(widget: tk.Misc) -> list:
    """输入类控件上真正会收到右键的地方：外壳 + 内部文本控件所在的那一层。"""
    targets: list = []
    seen: set = set()
    for node in _text_path(widget):
        for target in _bind_targets(node, deep=False):
            if id(target) in seen:
                continue
            seen.add(id(target))
            targets.append(target)
    return targets


def _text_path(widget: tk.Misc) -> list:
    """沿着宿主关系找到真正承载文字的 ``tk.Entry`` / ``tk.Text``。

    ``CTkEntry`` 里面是 ``_entry``，``CTkTextbox`` 里面是 ``_textbox``；
    ``TextArea`` 又多包了一层 ``.textbox``。返回从外壳到文字控件的路径；
    找不到时返回 ``[widget]``，调用方据此判断这不是输入类控件。
    """
    path: list = []
    node: Optional[tk.Misc] = widget
    for _ in range(5):
        if node is None:
            break
        path.append(node)
        for name in ("_entry", "_textbox"):
            inner = getattr(node, name, None)
            if isinstance(inner, (tk.Entry, tk.Text)):
                path.append(inner)
                return path
        node = getattr(node, "textbox", None)
    return path


def _text_widget(widget: tk.Misc) -> Optional[tk.Misc]:
    """控件里真正承载文字的 ``tk.Entry`` / ``tk.Text``；不是输入类控件时返回 ``None``。"""
    path = _text_path(widget)
    inner = path[-1] if path else None
    return inner if isinstance(inner, (tk.Entry, tk.Text)) else None


def _text_of(widget: tk.Misc) -> str:
    """控件里的文字；占位符显示中算空字符串。"""
    if getattr(widget, "_placeholder_text_active", False):  # CTkEntry 的占位符
        return ""
    if isinstance(widget, tk.Text):
        return widget.get("1.0", "end-1c")
    if isinstance(widget, tk.Entry):
        return widget.get()
    getter = getattr(widget, "get", None)
    if callable(getter):
        try:
            return str(getter())
        except Exception:  # noqa: BLE001 - CTkTextbox.get 需要两个索引
            pass
    inner = _text_widget(widget)
    if isinstance(inner, tk.Text):
        return inner.get("1.0", "end-1c")
    return str(inner.get()) if isinstance(inner, tk.Entry) else ""


def _has_selection(widget: tk.Misc) -> bool:
    """控件里有没有选中的文字。"""
    inner = _text_widget(widget)
    if inner is None:
        return False
    try:
        if isinstance(inner, tk.Text):
            return bool(inner.tag_ranges("sel"))
        return bool(inner.selection_present())
    except Exception:  # noqa: BLE001
        return False


def _is_readonly(widget: tk.Misc) -> bool:
    """控件是否不可编辑（TextArea 的只读开关，或内部 Text / Entry 的 state）。"""
    if bool(getattr(widget, "readonly", False)):
        return True
    inner = _text_widget(widget)
    if inner is None:
        return False
    try:
        return str(inner.cget("state")) in ("disabled", "readonly")
    except Exception:  # noqa: BLE001
        return False


def _clipboard_text(widget: tk.Misc) -> str:
    """剪贴板里的文本；剪贴板为空或放的不是文本时返回空字符串。"""
    try:
        return str(widget.clipboard_get())
    except Exception:  # noqa: BLE001 - 空剪贴板会抛 TclError
        return ""


def _run_virtual(widget: tk.Misc, sequence: str) -> None:
    """把 ``<<Copy>>`` / ``<<Cut>>`` / ``<<Paste>>`` 发给内部文本控件。

    走 Tk 自己的虚拟事件，而不是手写 ``clipboard_append`` + ``insert``：
    选区替换、撤销栈、粘贴后的光标位置都和键盘快捷键完全一致。

    发事件前先聚焦：菜单点完时焦点还在那个浮层上，个别平台（以及 Tk 的
    某些半绑定状态）没有焦点的控件收不到剪贴板操作。
    """
    inner = _text_widget(widget)
    if inner is None:
        return
    with contextlib.suppress(Exception):
        inner.focus_set()
        inner.event_generate(sequence)


def _clear_text(widget: tk.Misc) -> None:
    """清空控件内容；优先走控件自己的 ``clear()``，只读时临时放开再锁回去。"""
    clear = getattr(widget, "clear", None)
    if callable(clear):
        with contextlib.suppress(Exception):
            clear()
            return
    inner = _text_widget(widget)
    if inner is None:
        return
    try:
        state = str(inner.cget("state"))
    except Exception:  # noqa: BLE001
        state = "normal"
    with contextlib.suppress(Exception):
        inner.configure(state="normal")
    if isinstance(inner, tk.Text):
        inner.delete("1.0", "end")
    else:
        inner.delete(0, "end")
    if state != "normal":
        with contextlib.suppress(Exception):
            inner.configure(state=state)


def _prepare_edit(widget: tk.Misc, event: Optional[tk.Event] = None) -> None:
    """右键时把插入点挪到点击处、撤掉占位符、拿焦点。

    右键本身不会移动光标（Tk 的 Entry / Text 都没有这个默认行为），不挪的话
    粘贴会插到上一次的插入点——通常就是末尾，看着像「粘错地方」。

    不聚焦的话，粘贴会插到 CTkEntry 的占位文字后面（占位符是真实插进去的
    一段灰字），用户看到的就是「内容里混进了 placeholder」。
    """
    # 先把占位符撤掉：占位文字是真的插在控件里的，光标坐标会跟着它算偏。
    # TextArea 的 _clear_placeholder 会直接清空内容，必须确认现在真的是占位符
    if getattr(widget, "_placeholder_active", False):
        clear = getattr(widget, "_clear_placeholder", None)
        if callable(clear):
            with contextlib.suppress(Exception):
                clear()
    deactivate = getattr(widget, "_deactivate_placeholder", None)  # CTkEntry 的占位符
    if callable(deactivate):
        with contextlib.suppress(Exception):
            deactivate()
    inner = _text_widget(widget)
    if inner is None:
        return
    with contextlib.suppress(Exception):
        inner.focus_set()
    if event is not None:
        _move_caret(inner, event)


def _move_caret(inner: tk.Misc, event: tk.Event) -> None:
    """把插入点放到鼠标当前所在的位置，粘贴才会落在右键的地方。"""
    try:
        pointer_x, pointer_y = inner.winfo_pointerxy()
        x = pointer_x - inner.winfo_rootx()
        y = pointer_y - inner.winfo_rooty()
    except Exception:  # noqa: BLE001 - 控件可能已经销毁
        x, y = event.x, event.y
    x, y = max(0, int(x)), max(0, int(y))
    with contextlib.suppress(Exception):
        if isinstance(inner, tk.Text):
            inner.mark_set("insert", f"@{x},{y}")
        elif isinstance(inner, tk.Entry):
            inner.icursor(f"@{x}")
