"""外观相关的工具函数。

CustomTkinter 会把 ``(浅色, 深色)`` 二元组解析成当前外观对应的颜色，但只对
CTk 控件有效；原生 tk 控件（tk.Frame、tk.Label、tk.Canvas）和 canvas 无法
自己切换，需要在这里取值后手动重绘。
"""

from __future__ import annotations

import customtkinter as ctk


def is_dark() -> bool:
    return ctk.get_appearance_mode() == "Dark"


def color_of(token) -> str:
    """把 ``(浅色, 深色)`` 二元组按当前外观取一个值；普通字符串原样返回。"""
    if isinstance(token, (tuple, list)):
        return token[1] if is_dark() else token[0]
    return token


def apply_appearance(mode: str) -> None:
    """切换外观：``"dark"`` / ``"light"`` / ``"system"``。

    跟随系统时 CTk 会自动变，但原生 tk 控件需要自己重绘——记得把它们的
    颜色刷新挂在 ``CTk`` 的回调里（例如监听 ``<<AppearanceModeChanged>>``，
    或者在自己的切换按钮里统一调用 repaint_native）。
    """
    ctk.set_appearance_mode("Light" if mode == "light" else "Dark")


def repaint_native(widget, bg: str) -> None:
    """给原生 tk 控件换底色。

    为什么不用 ``widget.configure(bg=...)``：customtkinter 会接管
    ``tk.Frame.configure``，走 CTk 的重绘路径，可能碰到已经销毁的子控件而报错。
    直接改 Tcl 选项能绕开这一层。
    """
    try:
        widget.tk.call(widget._w, "configure", "-background", bg)
    except Exception:  # noqa: BLE001 - 控件可能已经销毁
        pass
