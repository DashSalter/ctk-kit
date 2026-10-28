"""外观相关的工具函数。

CustomTkinter 会把 ``(浅色, 深色)`` 二元组解析成当前外观对应的颜色，但只对
CTk 控件有效；原生 tk 控件（tk.Frame、tk.Label、tk.Canvas）和 canvas 无法
自己切换，需要在这里取值后手动重绘。
"""

from __future__ import annotations

import tkinter as tk
from typing import Sequence, Union

import customtkinter as ctk

from .tokens import ColorPair

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
