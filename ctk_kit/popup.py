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
from .core.win32 import (
    acrylic_window,
    client_frame_inset,
    enable_acrylic,
    set_client_rect,
    set_dwm_attribute,
)

# 浮层玻璃的 tint：只有 RGB、alpha=0，DWM 不会把它当成不透明底。
_POPUP_TINT = 0x00000000


__all__ = [
    "enable_popup_glass",
    "glass_veil",
    "round_window_corners",
    "scaled_geometry",
    "set_glass_geometry",
]


def glass_veil() -> Optional[str]:
    """浮层该不该用玻璃：该用时返回透明键色 ``"#000000"``，否则 ``None``。

    只有「玻璃底色 + 深色外观」才挂系统玻璃；浅色下窗口本身是白的，
    再挂玻璃反而糊成一片，不如保持原来的实色卡片。
    """
    import customtkinter as ctk

    from .theme import current_backdrop

    if current_backdrop() != "acrylic":
        return None
    if ctk.get_appearance_mode().lower() != "dark":
        return None
    return "#000000"


def enable_popup_glass(window: tk.Misc, *, frame: bool = True) -> bool:
    """把系统亚克力挂到一个独立的浮层窗口上，tint 沿用主窗口的。

    ``Toplevel`` 不会自己带上主窗口那层 accent 合成，玻璃下就会留一块
    不透明的深色；菜单、下拉面板、提示都是这么补一次的，这里收成共用。
    """
    # 走弹窗那套配方：attribute=30 + accent=3 + 无 alpha 的 tint。
    # 带 alpha 的 tint（主窗口的 0xE6）只在窗口非激活时才被当成「只是模糊」，
    # 一旦浮层拿到焦点，DWM 就按不透明合成，整块变黑；alpha=0 的 tint
    # 不会出现这个问题。
    ok = enable_acrylic(
        window,
        tint=_POPUP_TINT,
        accent=3,
        attribute=30,
        dark=True,
        # DWM 只给「带标准边框样式」的顶层窗口做玻璃合成；不补这个样式，
        # 窗口就只是个半透明的灰块，没有真正的模糊。
        # 第一次（窗口还隐藏时）传 True 补样式；重新挂的时候传 False，
        # 否则 SetWindowPos(FRAMECHANGED) 会重算非客户区，可见的窗口会抖一下。
        frame=frame,
        extend=True,
    )
    set_dwm_attribute(window, 33, 2)
    return ok


def scaled_geometry(
    window: tk.Misc,
    width: int,
    height: int,
    x: Optional[int] = None,
    y: Optional[int] = None,
) -> str:
    """拼 ``CTkToplevel.geometry`` 用的几何串（宽高按物理像素给）。

    ``CTkToplevel.geometry`` 会再把宽高乘一遍窗口缩放，而 ``winfo_reqwidth()``
    这类量出来的值已经是物理像素；直接传进去会被放大（125% 缩放下窗口大
    25%，1px 的描边在右边、下边看起来就比左边厚）。这里先除回去，让窗口的
    物理尺寸正好等于传入值。``x`` / ``y`` 是屏幕物理像素，不参与换算。

    参数:
        window: 目标窗口（``CTkToplevel``）。
        width: 宽度（物理像素）。
        height: 高度（物理像素）。
        x: 屏幕横坐标（物理像素）。
        y: 屏幕纵坐标（物理像素）。
    """
    scaling = 1.0
    with contextlib.suppress(Exception):
        scaling = window._get_window_scaling() or 1.0
    scaled_w = max(1, int(round(width / scaling)))
    scaled_h = max(1, int(round(height / scaling)))
    text = f"{scaled_w}x{scaled_h}"
    if x is not None and y is not None:
        text += f"+{int(x)}+{int(y)}"
    return text


def set_glass_geometry(
    window: tk.Misc,
    width: int,
    height: int,
    left: int,
    top: int,
    *,
    settle: bool = True,
) -> None:
    """把补过 ``WS_THICKFRAME`` 的玻璃窗口摆好，让**客户区**正好是给定尺寸。

    :func:`ctk_kit.win32.enable_acrylic` 会给无边框窗口补一圈缩放边框，
    之后 Tk 的 ``geometry()`` 仍按「外框 = 客户区」算，实际客户区会小一圈
    （125% 缩放下宽高各少 16px）。这里先把外框算大，再用
    :func:`ctk_kit.win32.set_client_rect` 校正一次。

    参数:
        window: 目标窗口（``CTkToplevel``）。
        width: 客户区宽度（物理像素）。
        height: 客户区高度（物理像素）。
        left: 屏幕横坐标（物理像素）。
        top: 屏幕纵坐标（物理像素）。
    """
    inset_w, inset_h = client_frame_inset(window)
    scaling = 1.0
    with contextlib.suppress(Exception):
        scaling = window._get_window_scaling() or 1.0
    outer_w = max(1, int(round((width + inset_w) / scaling)))
    outer_h = max(1, int(round((height + inset_h) / scaling)))
    with contextlib.suppress(Exception):
        if settle:
            window.geometry(f"{outer_w}x{outer_h}+{left}+{top}")
            # 摆放只做一次：外框 = 客户区 + 固定那圈边框。之后只挪位置，
            # 尺寸不动，客户区就不会重排，面板里的内容也不会错位。
            window.update_idletasks()
            set_client_rect(window, width, height, left, top)
        else:
            window.geometry(f"+{left}+{top}")


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
