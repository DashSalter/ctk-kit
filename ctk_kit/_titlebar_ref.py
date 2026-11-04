"""自绘标题栏的参考实现（摘自 CustomTkinterTitlebar，暂不接入）。

来源
----
CustomTkinterTitlebar ``v1.0.8.7``，MIT License，
https://github.com/littlewhitecloud/CustomTkinterTitlebar
原文：``customtitlebar/titlebar.py``（``CTT.setup`` / ``CTT.moving``）。

这里只留两块与窗口行为有关的核心逻辑。**import 本模块没有任何副作用**，
当前也没有任何代码路径会调用它；等真要做自绘标题栏时再接线。

两块逻辑
--------
1. :func:`drag_window` —— 按住某块区域拖动整个窗口。走 ``WM_SYSCOMMAND``
   的 ``SC_MOVE``，由 Windows 自己接管移动：Aero Snap、摇动取消、跨屏
   DPI 切换都不用自己算。原文 ``titlebar.py:132-138``。
2. :func:`install_titlebar_hook` —— 子类化窗口过程，在 ``WM_NCCALCSIZE``
   里把系统标题栏那一溜并进客户区，于是可以自己画标题栏，同时保留 DWM
   的窗口动画、阴影、圆角和任务栏行为。原文 ``titlebar.py:109-130``。

为什么没启用
------------
本库的毛玻璃是「补 ``WS_THICKFRAME``，让 DWM 认为窗口有非客户区」实现的
（见 :func:`ctk_kit.win32.acrylic_window`）。而 ``WM_NCCALCSIZE`` 干的正好
相反：把非客户区并回客户区。两者要同时用，就得重做窗口创建流程，让玻璃
改走 ``DWMWA_SYSTEMBACKDROP_TYPE`` 之类的路。参考实现先留着。

注意
----
- 只在 64 位 Windows 上成立：用的是 ``SetWindowLongPtrW``。
- 回调对象必须一直活着（见 :func:`install_titlebar_hook` 里的引用挂载），
  否则窗口过程会指向已被回收的地址。
"""

from __future__ import annotations

from ctypes import WINFUNCTYPE, Structure, c_uint64, c_void_p, windll
from ctypes.wintypes import RECT
from typing import Any, Callable, Optional

from .win32 import (
    SWP_FRAMECHANGED,
    SWP_NOMOVE,
    SWP_NOZORDER,
    SWP_NOSIZE,
    _toplevel_handle,
    available,
)

__all__ = ["drag_window", "install_titlebar_hook"]

# ---- 原文里直接用、win32.py 没有收的常量 ----
WM_NCCALCSIZE = 0x0083
WM_SYSCOMMAND = 0x0112
SC_MOVE = 0xF010
HTCAPTION = 2
GWL_WNDPROC = -4


class _NCCALCSIZE_PARAMS(Structure):
    """``WM_NCCALCSIZE`` 的 lParam 结构，这里只用前三个矩形。"""

    _fields_ = [
        ("rgrc", RECT * 3),
        ("lppos", c_void_p),
    ]


def drag_window(window: Any) -> bool:
    """按住发起调用的窗口拖动整窗，成功返回 ``True``。

    必须在鼠标按下/移动的事件回调里调用：``ReleaseCapture`` 先放开当前的
    鼠标捕获，再让系统进入 ``SC_MOVE`` 的模态循环，之后的移动、吸附、
    松手全由 Windows 处理。
    """
    if not available:
        return False
    try:
        hwnd = _toplevel_handle(window)
        windll.user32.ReleaseCapture()
        windll.user32.SendMessageW(hwnd, WM_SYSCOMMAND, SC_MOVE | HTCAPTION, 0)
        return True
    except Exception:  # noqa: BLE001 - 原生调用失败不该拖垮界面
        return False


def install_titlebar_hook(
    window: Any, height: int
) -> Optional[Callable[..., Any]]:
    """把系统标题栏占据的高度让给客户区，返回 wndproc 回调。

    参数:
        window: 任意 Tk 窗口；内部会换算到顶层 HWND。
        height: 让出的高度，物理像素（系统标题栏在 125% 缩放下约 31~39）。

    返回的 ``Callable`` 必须一直持有；本函数已经把它挂在
    ``window._titlebar_wndproc`` 上，调用方不用再管。
    """
    if not available:
        return None
    try:
        hwnd = _toplevel_handle(window)
        old_proc = windll.user32.GetWindowLongPtrW(hwnd, GWL_WNDPROC)
    except Exception:  # noqa: BLE001
        return None

    prototype = WINFUNCTYPE(c_uint64, c_uint64, c_uint64, c_uint64, c_uint64)

    def wndproc(hwnd_: Any, msg: Any, wparam: Any, lparam: Any) -> Any:
        if msg == WM_NCCALCSIZE and wparam:
            try:
                params = _NCCALCSIZE_PARAMS.from_address(lparam)
                params.rgrc[0].top -= int(height)
            except Exception:  # noqa: BLE001 - 结构体异常就按系统默认走
                pass
        return windll.user32.CallWindowProcW(old_proc, hwnd_, msg, wparam, lparam)

    handler = prototype(wndproc)
    windll.user32.SetWindowLongPtrW(hwnd, GWL_WNDPROC, handler)
    # 回调必须挂在窗口上，否则 Python 侧回收后窗口过程就指向野指针。
    window._titlebar_wndproc = handler
    # 让系统按新的非客户区重算一次，等价于原文 titlebar.py:130。
    windll.user32.SetWindowPos(
        hwnd,
        0,
        0,
        0,
        0,
        0,
        SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED,
    )
    return handler
