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


def color_of(token: ColorToken) -> str:
    """把 ``(浅色, 深色)`` 二元组按当前外观取一个值；普通字符串原样返回。

    参数:
        token: 颜色令牌，可以是 ``("#ffffff", "#131418")`` 这样的二元组，
            也可以是 ``"#ff0000"`` 这样的单值；单值不做任何转换。

    返回:
        当前外观下可用的单个颜色字符串，可直接传给 tk 控件的 ``bg`` /
        ``fg`` / ``fill`` 等选项。
    """
    if isinstance(token, (tuple, list)):
        return token[1] if is_dark() else token[0]
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


def _set_dwm_color(hwnd: int, attribute: int, color: ColorToken) -> bool:
    """给窗口的某个 DWM 颜色属性上色；不支持就返回 ``False``。

    Win32 的 ``COLORREF`` 是 ``0x00BBGGRR``，和 ``#RRGGBB`` 的字节序相反。
    """
    try:
        rgb = color_of(color).lstrip("#")
        red, green, blue = int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16)
        value = ctypes.c_int(blue << 16 | green << 8 | red)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
        )
    except Exception:  # noqa: BLE001 - 老系统没有这些属性
        return False
    return result == 0


def set_titlebar_dark(window: tk.Misc, dark: bool) -> None:
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
        except Exception:  # noqa: BLE001
            pass


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
        set_titlebar_dark(window, target == "Dark")
