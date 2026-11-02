"""共享字体：同一种字体规格只建一个 ``CTkFont`` 实例。

CTk 控件接受 tuple 字体时会各自创建一个 ``tkinter.font.Font``；页面反复
重建时，同一行字会留下很多重复的字体对象。这里按规格缓存，库内控件的
默认字体都走同一份，重建页面时直接复用。
"""

from __future__ import annotations

import tkinter as tk
from typing import Dict, Tuple

import customtkinter as ctk

_CACHE: Dict[Tuple, ctk.CTkFont] = {}
_ROOT = None


def get_font(spec) -> ctk.CTkFont:
    """取某个字体规格对应的共享 ``CTkFont``，第一次调用时创建。

    参数:
        spec: ``(family, size)`` 或 ``(family, size, weight)`` 形式的元组，
            与 :mod:`ctk_kit.tokens` 里的 ``FONT_*`` 常量一致。

    返回:
        可被多个控件同时引用的 ``CTkFont`` 实例。
    """
    global _ROOT
    # 字体对象绑定在 Tk 解释器上：换了 root（比如关窗后重新建 App）就清空，
    # 否则新控件会引用上一个 root 里已经销毁的字体。
    root = tk._default_root
    if root is not _ROOT:
        _CACHE.clear()
        _ROOT = root
    key = tuple(spec)
    font = _CACHE.get(key)
    if font is None:
        family = key[0]
        size = int(key[1])
        weight = key[2] if len(key) > 2 else "normal"
        font = ctk.CTkFont(family=family, size=size, weight=weight)
        _CACHE[key] = font
    return font
