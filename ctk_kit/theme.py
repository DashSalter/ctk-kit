"""外观相关的工具函数。

CustomTkinter 会把 ``(浅色, 深色)`` 二元组解析成当前外观对应的颜色，但只对
CTk 控件有效；原生 tk 控件（tk.Frame、tk.Label、tk.Canvas）和 canvas 无法
自己切换，需要在这里取值后手动重绘。

想做到「切主题不卡」的话，用 :func:`apply_appearance_fast` 代替
:func:`apply_appearance`，再配合 :class:`ctk_kit.pages.PageRebuilder` 按页重建。
"""

from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from typing import Optional, Sequence, Union

import customtkinter as ctk

from . import styles
from . import tokens as T
from .tokens import ColorPair

try:  # 内部表：拿得到才能跳过「一次性重绘所有控件」
    from customtkinter.windows.widgets.appearance_mode.appearance_mode_tracker import (
        AppearanceModeTracker,
    )
except Exception:  # noqa: BLE001 - customtkinter 换了内部结构
    AppearanceModeTracker = None  # type: ignore[assignment]

# 颜色令牌：``(浅色, 深色)`` 二元组，或者已经解析好的单值颜色字符串。
ColorToken = Union[str, ColorPair, Sequence[str]]


def is_dark() -> bool:
    """当前是否深色外观。"""
    return ctk.get_appearance_mode() == "Dark"


def is_win11() -> bool:
    """当前系统是不是 Windows 11（build 22000 以上）。

    Win11 上 ``SetWindowCompositionAttribute`` 的 accent 模糊对普通窗口
    基本失效，要用 ``DWMWA_SYSTEMBACKDROP_TYPE`` 才会真的糊；Win10 没有
    这个属性，仍得走 accent + tint。
    """
    if not sys.platform.startswith("win"):
        return False
    try:
        return sys.getwindowsversion().build >= 22000
    except Exception:  # noqa: BLE001
        return False


def color_of(token: ColorToken) -> str:
    """把颜色令牌取成单个颜色字符串；字符串原样返回。

    令牌本身都是字符串，这个函数存在的意义是兼容调用方自己传的色对：
    ``(浅色, 深色)`` 取深色，``(浅色, 深色, 毛玻璃)`` 取最后一项。

    参数:
        token: 颜色令牌或色对。

    返回:
        可直接传给 tk 控件的 ``bg`` / ``fg`` / ``fill`` 等选项的字符串。
    """
    if isinstance(token, (tuple, list)):
        values = [str(part) for part in token if part]
        return values[-1] if values else "#000000"
    return token


def apply_appearance(mode: str) -> None:
    """切换外观。

    参数:
        mode: ``"dark"``、``"light"`` 或 ``"system"``。当前实现里只有全小写的
            ``"light"`` 会切到浅色，其余取值（包括 ``"system"``）都落到深色，
            与 CTk 的 ``set_appearance_mode`` 行为保持一致。

    注意:
        跟随系统时 CTk 会自动变，但原生 tk 控件需要自己重绘——记得把它们的
        颜色刷新挂在 ``CTk`` 的回调里（例如监听 ``<<AppearanceModeChanged>>``，
        或者在自己的切换按钮里统一调用 :func:`repaint_native`）。
    """
    ctk.set_appearance_mode("Light" if mode == "light" else "Dark")


def repaint_native(widget: tk.Misc, bg: str) -> None:
    """给原生 tk 控件换底色。

    为什么不用 ``widget.configure(bg=...)``：customtkinter 会接管
    ``tk.Frame.configure``，走 CTk 的重绘路径，可能碰到已经销毁的子控件而报错。
    直接改 Tcl 选项能绕开这一层。

    参数:
        widget: 任意 tk 控件；已经销毁的控件不会抛异常。
        bg: 目标底色，通常是 :func:`color_of` 的返回值。
    """
    try:
        widget.tk.call(widget._w, "configure", "-background", bg)
    except Exception:  # noqa: BLE001 - 控件可能已经销毁
        pass


def _set_dwm_color(
    hwnd: int, attribute: int, color: Optional[ColorToken]
) -> bool:
    """给窗口的某个 DWM 颜色属性上色；不支持就返回 ``False``。

    Win32 的 ``COLORREF`` 是 ``0x00BBGGRR``，和 ``#RRGGBB`` 的字节序相反。
    ``color`` 传 ``None`` 时写 ``DWMWA_COLOR_DEFAULT``（``0xFFFFFFFF``），把
    属性交还给系统——标题栏重新由 DWM 绘制，玻璃外观靠这一步才能透出来。
    """
    try:
        if color is None:
            value = ctypes.c_int(-1)  # 0xFFFFFFFF == DWMWA_COLOR_DEFAULT
        else:
            rgb = color_of(color).lstrip("#")
            red, green, blue = int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16)
            value = ctypes.c_int(blue << 16 | green << 8 | red)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
        )
    except Exception:  # noqa: BLE001 - 老系统没有这些属性
        return False
    return result == 0


def set_titlebar_dark(window: tk.Misc, dark: bool, *, glass: bool = False) -> None:
    """把窗口的标题栏刷成和界面一致的颜色（仅 Windows 生效）。

    分两步：

    1. 先设 ``DWMWA_USE_IMMERSIVE_DARK_MODE``——老系统只认这个，它让标题栏在
       系统浅色/深色之间切换。
    2. 再尝试用 ``DWMWA_CAPTION_COLOR`` / ``DWMWA_BORDER_COLOR`` /
       ``DWMWA_TEXT_COLOR``（Windows 11 22H2+）把标题栏、边框、标题文字染成
       和侧边栏一致的颜色。不这么做的话，浅色下系统标题栏（约 ``#f3f3f3``）和
       内容区底色几乎同色，看起来「上边和右边一样」；深色下也各有各的色。

    不走 customtkinter 的 ``_windows_set_titlebar_color``：那个实现会先把窗口
    ``withdraw()`` 再 ``deiconify()``（切换时闪一下），还会把焦点还给一个可能
    已经销毁的控件（``bad window path name``）。

    参数:
        window: 任意顶层窗口（``CTk`` / ``CTkToplevel`` / ``tk.Toplevel``）。
        dark: ``True`` 深色标题栏，``False`` 浅色。
        glass: ``True`` 时不涂标题栏和边框色，交还 DWM——玻璃外观下一旦设了
            ``CAPTION_COLOR``，标题栏就变回不透明纯色，玻璃透不过来。
    """
    if sys.platform != "win32":
        return
    try:
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()
        value = ctypes.c_int(1 if dark else 0)
        # 20 是 Windows 10 1809+ 的 DWMWA_USE_IMMERSIVE_DARK_MODE，19 是更早的编号
        for attribute in (20, 19):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
            )
            if result == 0:
                break
    except Exception:  # noqa: BLE001 - 非 Windows 或 DWM 不可用
        return

    if glass:
        # 交还给 DWM：标题栏和边框恢复系统绘制，玻璃才能一直糊到顶上。
        _set_dwm_color(hwnd, 35, None)
        _set_dwm_color(hwnd, 34, None)
        return

    # 和窗口自身的层次对齐：标题栏 = 标题栏色，边框 = 描边色，文字 = 正文色
    from . import tokens as T

    _set_dwm_color(hwnd, 35, T.COLOR_TITLEBAR)  # DWMWA_CAPTION_COLOR
    _set_dwm_color(hwnd, 34, T.COLOR_BORDER)    # DWMWA_BORDER_COLOR
    _set_dwm_color(hwnd, 36, T.COLOR_TEXT)      # DWMWA_TEXT_COLOR


def repaint_window(window: tk.Misc, mode: str) -> None:
    """让窗口自己按新外观重绘一次，不碰它的子控件。

    直接调 ``CTk._set_appearance_mode`` 会连带处理标题栏（见
    :func:`set_titlebar_dark`），这里临时关掉那段逻辑，只更新窗口底色。

    参数:
        window: ``CTk`` 窗口。
        mode: ``"Light"`` 或 ``"Dark"``（首字母大写，与 CTk 内部一致）。
    """
    saved = getattr(window, "_deactivate_windows_window_header_manipulation", False)
    try:
        window._deactivate_windows_window_header_manipulation = True
    except Exception:  # noqa: BLE001 - 原生窗口没有这个属性
        pass
    try:
        setter = getattr(window, "_set_appearance_mode", None)
        if callable(setter):
            setter(mode)
    except Exception:  # noqa: BLE001 - 刷新失败不该打断切换
        pass
    finally:
        try:
            window._deactivate_windows_window_header_manipulation = saved
        except Exception:  # noqa: BLE001 - 原生窗口没有这个属性
            pass
    # 窗口底色可能变了，窗口类的擦除画刷也要跟着换，否则启动/还原时
    # 系统仍按旧底色（通常是黑色）先擦一遍。
    set_window_brush(window)


def recolor_tree(
    widget: tk.Misc,
    bg: ColorToken,
    mode: Optional[str] = None,
    *,
    deep: bool = True,
) -> None:
    """把一棵控件树的「父底色」统一刷成 ``bg``，并让 CTk 控件按新外观重绘。

    侧边栏、状态栏这类「不属于任何页面」的容器用得着：切外观后它们的父底色
    还是旧的，而 ``CTkButton`` / ``CTkLabel`` 的 ``_bg_color`` 是构造时从父容器
    取死的，只改父容器会留下一圈颜色不对的方块。

    参数:
        widget: 子树的根（通常是侧边栏容器）。
        bg: 新的父底色，通常是 ``COLOR_SIDE`` / ``COLOR_BG``。
        mode: ``"Light"`` / ``"Dark"``；不传就按当前外观取。
        deep: 是否递归到子控件的内部。默认 ``True``；侧边栏这种「一眼就能数清
            几个按钮」的容器传 ``False`` 更快——CTk 控件的 ``_set_appearance_mode``
            本来就会重绘自己的画布和文字，再进里面刷一遍是白费力气（实测 41 个
            控件 46 ms，只刷直接子层 13 个 24 ms）。
    """
    mode_string = mode or ("Dark" if is_dark() else "Light")
    configure = getattr(widget, "configure", None)
    if callable(configure):
        try:
            configure(bg_color=bg)
        except Exception:  # noqa: BLE001 - 原生控件没有 bg_color
            pass
    setter = getattr(widget, "_set_appearance_mode", None)
    if callable(setter):
        try:
            setter(mode_string)
        except Exception:  # noqa: BLE001
            pass
    for child in widget.winfo_children():
        if deep:
            recolor_tree(child, bg, mode_string)
        else:
            recolor_shallow(child, bg, mode_string)


class freeze_redraw:
    """上下文管理器：切换外观期间挂起窗口重绘，退出时整体重画一次。

    切外观要「先刷外壳、再重建当前页」，两步之间有一帧「外壳已是新配色、页面
    还是旧的」的中间态；页面重建要几十到上百毫秒，这一帧会被看到，就是切换时
    的闪。用 Win32 的 ``WM_SETREDRAW`` 把绘制挂起，两步都做完再一起重画，中间
    态就不会上屏。

    非 Windows 或拿不到窗口句柄时什么也不做，退化成「有可能闪一下」。
    """

    _WM_SETREDRAW = 0x000B
    # RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN | RDW_UPDATENOW
    _REDRAW_FLAGS = 0x0001 | 0x0004 | 0x0080 | 0x0100

    def __init__(self, window: tk.Misc) -> None:
        self._window = window
        self._hwnd = 0

    def __enter__(self) -> "freeze_redraw":
        if sys.platform == "win32":
            try:
                user32 = ctypes.windll.user32
                hwnd = user32.GetParent(self._window.winfo_id()) or self._window.winfo_id()
                user32.SendMessageW(hwnd, self._WM_SETREDRAW, 0, 0)
                self._hwnd = hwnd
            except Exception:  # noqa: BLE001 - 拿不到句柄就退化成普通切换
                self._hwnd = 0
        return self

    def __exit__(self, *_exc: object) -> bool:
        if self._hwnd:
            try:
                user32 = ctypes.windll.user32
                user32.SendMessageW(self._hwnd, self._WM_SETREDRAW, 1, 0)
                user32.RedrawWindow(self._hwnd, None, None, self._REDRAW_FLAGS)
            except Exception:  # noqa: BLE001
                pass
            self._hwnd = 0
        return False


def recolor_shallow(widget: tk.Misc, bg: ColorToken, mode: str) -> None:
    """只刷这一个控件（不再往下递归），配合 ``recolor_tree(deep=False)``。"""
    configure = getattr(widget, "configure", None)
    if callable(configure):
        try:
            configure(bg_color=bg)
        except Exception:  # noqa: BLE001 - 原生控件没有 bg_color
            pass
    setter = getattr(widget, "_set_appearance_mode", None)
    if callable(setter):
        try:
            setter(mode)
        except Exception:  # noqa: BLE001
            pass


def apply_appearance_fast(mode: str, *, window: Optional[tk.Misc] = None) -> None:
    """切换外观，但**不让已有控件重绘**——这是「切主题不卡」的关键。

    ``ctk.set_appearance_mode()`` 会顺序遍历 ``AppearanceModeTracker`` 里注册的
    所有控件逐个重绘，一千多个控件要 380 ms 左右，切换时整窗会僵住。这里先把
    注册表清空再调用它：全局外观状态照常更新（之后新建的控件会用新配色），
    已有控件一个都不重绘，由调用方自己决定重建哪些（见
    :class:`ctk_kit.pages.PageRebuilder`）。

    注意:
        调用之后**已有控件仍然是旧配色**。不重建/不重绘的话，界面会半新半旧。

    参数:
        mode: ``"light"`` / ``"dark"`` / ``"system"``，语义同 :func:`apply_appearance`。
        window: 传了就把窗口自己也刷一遍（底色 + 标题栏颜色）。

    返回:
        无。

    示例::

        def toggle(self):
            mode = "light" if is_dark() else "dark"
            apply_appearance_fast(mode, window=self)
            self.pages.switch(mode)      # 自己的页面管理器
            self.sidebar.configure(fg_color=tokens.COLOR_SIDE)
    """
    target = "Light" if mode == "light" else "Dark"
    callbacks = None
    if AppearanceModeTracker is not None:
        callbacks = getattr(AppearanceModeTracker, "callback_list", None)

    if callbacks is None:
        # 内部结构变了：退回官方做法，慢但一定正确
        apply_appearance(mode)
    else:
        saved = list(callbacks)
        callbacks.clear()
        try:
            ctk.set_appearance_mode(target)
        finally:
            callbacks.extend(saved)

    if window is not None:
        repaint_window(window, target)
        set_titlebar_dark(
            window, target == "Dark", glass=current_backdrop() == "acrylic"
        )


#: 窗口类背景画刷：hwnd -> HBRUSH。换主题时替换，旧刷在这里删。
_WINDOW_BRUSHES: dict = {}
_GCLP_HBRBACKGROUND = -10


def _colorref(color: str) -> int:
    """``#RRGGBB`` -> Win32 ``COLORREF``（``0x00BBGGRR``）。"""
    rgb = color.lstrip("#")
    red, green, blue = int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16)
    return blue << 16 | green << 8 | red


def set_window_brush(window: tk.Misc, color: Optional[str] = None) -> bool:
    """把顶层窗口类的背景画刷换成 ``color``（默认当前窗口底色）。

    Windows 在窗口启动、最大化、还原、焦点切换触发重绘时，会先用窗口类的
    背景画刷擦一遍；Tk 的 ``TkTopLevel`` 类没有画刷，系统就按黑色擦，主题
    内容还没画出来时会闪一块黑。换掉画刷后，系统擦的第一帧就是窗口底色。

    参数:
        window: 任意顶层窗口（``CTk`` / ``CTkToplevel`` / ``tk.Toplevel``）。
        color: ``#RRGGBB``；不传就取 ``tokens.COLOR_BG`` 的当前外观值。

    返回:
        设置成功返回 ``True``；非 Windows 或 API 不可用返回 ``False``。

    注意:
        Windows 的窗口类是整个进程共享的，设置一次后所有 ``TkTopLevel``
        窗口都会用这个底色；多个 App 用不同主题时以最后一次设置为准。
    """
    if sys.platform != "win32":
        return False
    try:
        from ctypes import wintypes

        from . import tokens as T

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

        user32.GetParent.argtypes = [wintypes.HWND]
        user32.GetParent.restype = wintypes.HWND
        setter = getattr(user32, "SetClassLongPtrW", user32.SetClassLongW)
        setter.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
        setter.restype = ctypes.c_void_p
        gdi32.CreateSolidBrush.argtypes = [wintypes.DWORD]
        gdi32.CreateSolidBrush.restype = wintypes.HBRUSH
        gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
        gdi32.DeleteObject.restype = wintypes.BOOL

        hwnd = user32.GetParent(window.winfo_id())
        if not hwnd:
            # 窗口还没建出 wrapper（例如 App 刚构造完还没映射）：先不设，
            # 等 _refresh_titlebar 时窗口已经映射再补。
            return False
        if color is None:
            color = color_of(T.COLOR_BG)
        brush = gdi32.CreateSolidBrush(_colorref(color))
        if not brush:
            return False
        previous = _WINDOW_BRUSHES.get(hwnd)
        setter(hwnd, _GCLP_HBRBACKGROUND, brush)
        _WINDOW_BRUSHES[hwnd] = brush
        if previous:
            gdi32.DeleteObject(previous)
        return True
    except Exception:  # noqa: BLE001 - 非 Windows、老系统或 Tk 窗口还没建好
        return False


# ---------------------------------------------------------------- 玻璃外观
# 模块加载时的普通底色：从玻璃切回来时用，避免「普通色 = 玻璃色」。
_BASE_BG = T.COLOR_BG
_BASE_SIDE = T.COLOR_SIDE
_backdrop = "none"
# 当前玻璃模式铺的透明键色，运行时换色要把它保住。
_veil = "#000000"

#: 接受的玻璃模式写法（小写比较，中文不受 lower 影响）。
_GLASS_ALIASES = {"acrylic", "glass", "玻璃", "毛玻璃", "磨砂"}


def current_backdrop() -> str:
    """当前底色模式：``"none"`` 或 ``"acrylic"``。"""
    return _backdrop


def current_veil() -> str:
    """玻璃模式下铺在窗口底 / 侧边栏的透明键色，普通模式返回 ``"#000000"``。"""
    return _veil


def rebase_token(name: str, value: ColorToken) -> None:
    """改某个颜色令牌在**普通底色**下的基准值。

    毛玻璃模式切回不透明时会把 ``COLOR_BG`` / ``COLOR_SIDE`` 还原成「进玻璃
    之前」的值；运行时换色（``theming.apply_palette``）改完令牌后要同步改这个
    基准，否则一关玻璃用户挑的颜色就被还原丢掉了。

    参数:
        name: 令牌名，例如 ``"COLOR_BG"``。
        value: 新的颜色字符串。
    """
    global _BASE_BG, _BASE_SIDE

    if name == "COLOR_BG":
        _BASE_BG = value
    elif name == "COLOR_SIDE":
        _BASE_SIDE = value


def apply_backdrop(mode: str = "none", veil: str = "#000000") -> str:
    """把全局底色在「普通」和「玻璃」之间切换，返回实际生效的模式。

    玻璃模式下 ``tokens.COLOR_BG`` / ``COLOR_SIDE`` 被换成 ``veil``：DWM 的
    acrylic 把**纯黑**像素当成透明，窗口底和侧边栏于是透出桌面的模糊；卡片、
    输入框这些仍是实色，浮在玻璃上。

    ``veil`` 是「透明键色」，默认纯黑。改它只影响「看起来像不像透」：DWM
    只认纯黑（``#000000``）为全透明，换成近黑或深灰，那块区域就变成实色面板，
    玻璃也就看不见了——所以这个值适合拿来试，不适合当真当假。

    只改颜色令牌，**已经建好的控件不会自己变**——调用方要接着重建外壳和页面。
    ``ctk_kit.window.App.set_backdrop()`` 已经把整套流程包好了。

    参数:
        mode: ``"none"`` 关闭；``"acrylic"``（也接受 ``"glass"`` / ``"毛玻璃"``）
            开启。
        veil: 玻璃模式下铺在窗口底/侧边栏/页面底的颜色，``"#RRGGBB"``。

    返回:
        实际生效的模式，``"none"`` 或 ``"acrylic"``。
    """
    global _backdrop, _veil
    wanted = "acrylic" if str(mode).strip().lower() in _GLASS_ALIASES else "none"
    if wanted == "acrylic":
        _veil = veil
        T.COLOR_BG = veil
        T.COLOR_SIDE = veil
    else:
        T.COLOR_BG = _BASE_BG
        T.COLOR_SIDE = _BASE_SIDE
    styles.refresh_tokens()
    _backdrop = wanted
    return _backdrop
