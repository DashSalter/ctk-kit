"""无边框弹层窗口的公共处理：圆角裁剪。

右键菜单、下拉面板、提示、通知、对话框这些无边框窗口都要把窗口本身裁成
圆角，做法完全一样：优先让 Win11 的 DWM 画系统圆角（边缘由系统抗锯齿，
没有阶梯）；DWM 不可用（旧系统）时退回 ``SetWindowRgn`` 硬裁剪，那圈锯齿
是 GDI 区域的固有代价。

抽在这里，各组件只传窗口和圆角半径，不再各留一份 ``ctypes`` 代码。
"""

from __future__ import annotations

import contextlib
import sys
import tkinter as tk
from typing import Optional

from . import tokens as T

__all__ = ["round_window_corners"]


def round_window_corners(
    window: tk.Misc,
    radius: Optional[float] = None,
    scaling: Optional[float] = None,
) -> None:
    """把无边框窗口裁成圆角（Windows）；其它平台什么都不做。

    参数:
        window: 要处理的窗口（``CTkToplevel`` / ``tk.Toplevel``）。
        radius: 圆角半径（逻辑像素）；不传用 :data:`tokens.RADIUS_MEDIUM`。
        scaling: 缩放系数；不传自己从窗口取。
    """
    if sys.platform != "win32":
        return
    with contextlib.suppress(Exception):
        import ctypes

        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()
        # 先清掉旧 region：控件重排会反复走这里，残留的 region 会把 DWM
        # 圆角整个挡住，看起来就是四角又变直了。
        ctypes.windll.user32.SetWindowRgn(hwnd, None, True)
        # DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2
        preference = ctypes.c_int(2)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)
        )
        if result == 0:
            return
        if scaling is None:
            try:
                scaling = window.winfo_toplevel()._get_window_scaling()
            except Exception:  # noqa: BLE001
                scaling = window.winfo_fpixels("1i") / 96.0
        if radius is None:
            radius = T.RADIUS_MEDIUM
        width = window.winfo_width()
        height = window.winfo_height()
        if width <= 2 or height <= 2:
            return
        # CreateRoundRectRgn 收的是椭圆宽高（直径）
        diameter = max(2, int(radius * 2 * scaling))
        region = ctypes.windll.gdi32.CreateRoundRectRgn(
            0, 0, width + 1, height + 1, diameter, diameter
        )
        ctypes.windll.user32.SetWindowRgn(hwnd, region, True)
