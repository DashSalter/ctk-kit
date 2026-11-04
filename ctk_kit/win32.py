"""Windows 原生的窗口/控件效果，ctypes 实现，不依赖第三方包。

目前只封装用得到的几样：

* :func:`enable_acrylic` —— 给无边框窗口铺一层系统亚克力（DWM 实时模糊）。
* :func:`set_widget_opacity` —— 让单个控件真半透明（``WS_EX_LAYERED``）。

思路来自 `pywinstyles <https://github.com/Akascape/py-window-styles>`_（MIT），
这里只保留需要的部分，省掉一个运行时依赖。
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import POINTER, Structure, byref, c_int, pointer, sizeof, windll
from ctypes.wintypes import DWORD, RECT, ULONG
from typing import Any, Optional

__all__ = [
    "acrylic_window",
    "enable_acrylic",
    "set_client_rect",
    "set_widget_opacity",
    "available",
]

#: 只有 Windows 才有这些 API。
available = sys.platform == "win32"

GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_THICKFRAME = 0x00040000
WS_EX_LAYERED = 0x00080000
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
#: ``WCA_ACCENT_POLICY``（DWM 的窗口合成属性编号；值是 30 而不是 19）
WCA_ACCENT_POLICY = 30
#: ``ACCENT_ENABLE_BLURBEHIND``（Win11 上 acrylic 用这个，``4`` 已经失效）
ACCENT_ENABLE_BLURBEHIND = 3
#: ``DWMWA_USE_IMMERSIVE_DARK_MODE`` / ``DWMWA_SYSTEMBACKDROP_TYPE``
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38
#: ``DWMWA_WINDOW_CORNER_PREFERENCE``（33）与取值
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2
#: ``DWMWA_BORDER_COLOR``（Win11 22H2+）：不画系统边框
DWMWA_BORDER_COLOR = 34
DWMWA_COLOR_NONE = 0xFFFFFFFE
#: 系统背板类型
BACKDROP_ACRYLIC = 3
LWA_ALPHA = 0x02
LWA_COLORKEY = 0x01


class _ACCENT_POLICY(Structure):
    _fields_ = [
        ("AccentState", DWORD),
        ("AccentFlags", DWORD),
        ("GradientColor", DWORD),
        ("AnimationId", DWORD),
    ]


class _WINDOW_COMPOSITION_ATTRIBUTES(Structure):
    _fields_ = [
        ("Attribute", DWORD),
        ("Data", POINTER(_ACCENT_POLICY)),
        ("SizeOfData", ULONG),
    ]


class _MARGINS(Structure):
    _fields_ = [
        ("cxLeftWidth", c_int),
        ("cxRightWidth", c_int),
        ("cyTopHeight", c_int),
        ("cyBottomHeight", c_int),
    ]


def _toplevel_handle(window: Any) -> int:
    """Tk 窗口的顶层 HWND（``winfo_id`` 给的是客户区子窗口）。"""
    hwnd = int(window.winfo_id())
    parent = windll.user32.GetParent(hwnd)
    return parent or hwnd


def client_frame_inset(window: Any) -> tuple[int, int]:
    """窗口外框比客户区多出的宽、高（物理像素）。

    ``overrideredirect`` 的窗口本来是 ``WS_POPUP``，没有非客户区；补上
    ``WS_THICKFRAME`` 后系统才给它一圈缩放边框，客户区随之缩小一圈。
    自己写 WndProc 之前只能用这个差值去换算。
    """
    if not available:
        return (0, 0)
    try:
        hwnd = _toplevel_handle(window)
        style = windll.user32.GetWindowLongW(hwnd, GWL_STYLE) & 0xFFFFFFFF
        ex_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & 0xFFFFFFFF
        probe = 100
        rect = RECT(0, 0, probe, probe)
        if not windll.user32.AdjustWindowRectEx(byref(rect), style, False, ex_style):
            return (0, 0)
        return (rect.right - rect.left - probe, rect.bottom - rect.top - probe)
    except Exception:  # noqa: BLE001
        return (0, 0)


def set_client_rect(
    window: Any,
    width: int,
    height: int,
    x: Optional[int] = None,
    y: Optional[int] = None,
) -> bool:
    """按「客户区尺寸」设置窗口矩形（物理像素），返回是否成功。

    无边框窗口补了 ``WS_THICKFRAME`` 之后，Tk 的 ``geometry()`` 仍按「外框
    = 客户区」算，实际客户区被那圈缩放边框吃掉一圈——125% 缩放下宽高各少
    16px，对话框里的内容就会被压扁。这里用 ``AdjustWindowRectEx`` 把外框
    算准再 ``SetWindowPos``，客户区正好是 ``width`` × ``height``；Tk 收到
    ``WM_SIZE`` 后会把几何记录同步成这个客户区尺寸。

    ``x`` / ``y`` 是外框左上角的屏幕坐标；不传就只改尺寸、不动位置。
    """
    if not available:
        return False
    try:
        hwnd = _toplevel_handle(window)
        inset_w, inset_h = client_frame_inset(window)
        outer_w = max(1, int(width) + inset_w)
        outer_h = max(1, int(height) + inset_h)
        flags = SWP_NOZORDER | SWP_NOACTIVATE
        if x is None or y is None:
            flags |= SWP_NOMOVE
            x = y = 0
        return bool(
            windll.user32.SetWindowPos(
                hwnd, 0, int(x), int(y), outer_w, outer_h, flags
            )
        )
    except Exception:  # noqa: BLE001
        return False


def _set_accent(hwnd: int, state: int, color: Optional[int]) -> None:
    accent = _ACCENT_POLICY()
    accent.AccentState = state
    if color is not None:
        accent.GradientColor = color
    data = _WINDOW_COMPOSITION_ATTRIBUTES()
    data.Attribute = WCA_ACCENT_POLICY
    data.SizeOfData = sizeof(accent)
    data.Data = pointer(accent)
    windll.user32.SetWindowCompositionAttribute(hwnd, pointer(data))


def _extend_frame(hwnd: int) -> None:
    margins = _MARGINS(-1, -1, -1, -1)
    windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, byref(margins))


def enable_acrylic(window: Any, *, tint: Optional[int] = None, dark: bool = True) -> bool:
    """让窗口背景变成系统亚克力，返回是否成功。

    无边框窗口（``overrideredirect(True)``）要先补一个 ``WS_THICKFRAME``：
    DWM 只对「有非客户区」的窗口走玻璃合成，纯 ``WS_POPUP`` 上只会得到
    一层均匀的 tint。补边框不改变 Tk 的外观，窗口仍然没有标题栏。

    ``tint`` 是 ``0xAABBGGRR``（注意 BGR 顺序）；窗口内容需要自己留出
    透明区域，通常是一层半透明卡片（见 :func:`set_widget_opacity`）。
    """
    if not available:
        return False
    try:
        hwnd = _toplevel_handle(window)
        style = windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
        windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style | WS_THICKFRAME)
        windll.user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER,
        )
        window.update_idletasks()
        _set_accent(hwnd, ACCENT_ENABLE_BLURBEHIND, tint)
        _extend_frame(hwnd)
        # 注意：不要再设 DWMWA_SYSTEMBACKDROP_TYPE（38）。它会把窗口换成
        # 系统的主题背板，覆盖掉上面 accent 的 tint，窗口变成亮的。
        if tint is None:
            backdrop = c_int(BACKDROP_ACRYLIC)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_SYSTEMBACKDROP_TYPE, byref(backdrop), sizeof(backdrop)
            )
        if dark:
            value = c_int(1)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, byref(value), sizeof(value)
            )
        # 补了 WS_THICKFRAME 之后，Win11 会给窗口画一圈 1px 边框；窗口获得
        # 焦点时会亮成浅色，看起来像底部闪一条白线。显式关掉这圈边框
        # （22H2 之前不支持这个属性，调用失败无副作用）。
        border = DWORD(DWMWA_COLOR_NONE)
        windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_BORDER_COLOR, byref(border), sizeof(border)
        )
        # 强制 DWM 立刻合成一帧：不然窗口刚显示时还是未激活的亮色底，
        # 要等用户拖动窗口才刷新成玻璃。
        windll.dwmapi.DwmFlush()
        return True
    except Exception:  # noqa: BLE001
        return False


def acrylic_window(
    window: Any,
    *,
    tint: Optional[int] = None,
    corners: bool = True,
    focus: bool = True,
) -> bool:
    """把一个 Toplevel 变成「系统亚克力」浮层，返回是否成功。

    一步做完四件事：窗口底色刷黑、套上 acrylic、按系统规则切圆角、抢焦点。
    黑底是必须的——DWM 只把窗口的空白区域当玻璃，Tk 默认的窗口底色会整块
    盖住它。

    内容层：在黑底窗口里铺一层 ``CTkFrame``（``fg_color`` 用黑色或很深的
    颜色）当 veil，文字/按钮放进 veil。veil 不要调 :func:`set_widget_opacity`
    ——那会把玻璃一起稀释成灰色。
    """
    if not available:
        return False
    try:
        try:
            window.configure(fg_color="#000000")
        except Exception:  # noqa: BLE001
            window.configure(bg="black")
        if not enable_acrylic(window, tint=tint):
            return False
        if corners:
            hwnd = _toplevel_handle(window)
            value = c_int(DWMWCP_ROUND)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, byref(value), sizeof(value)
            )
        if focus:
            window.focus_force()
        return True
    except Exception:  # noqa: BLE001
        return False


def set_widget_opacity(widget: Any, value: float, color: Optional[str] = None) -> bool:
    """把单个控件的 alpha 调低，返回是否成功。

    注意 Tk 自己的 ``tk.Canvas`` 会被标成 layered 却不会真的合成；这个
    接口只对 ``CTkFrame`` 这类「子 HWND 独立绘制」的控件有效。
    """
    if not available:
        return False
    try:
        hwnd = int(widget.winfo_id())
        alpha = max(0, min(255, int(round(255 * value))))
        key = 1
        if color and color.startswith("#") and len(color) == 7:
            red, green, blue = (int(color[i:i + 2], 16) for i in (1, 3, 5))
            key = red | (green << 8) | (blue << 16)
        exstyle = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle | WS_EX_LAYERED)
        windll.user32.SetLayeredWindowAttributes(
            hwnd, key, alpha, LWA_ALPHA | LWA_COLORKEY
        )
        return True
    except Exception:  # noqa: BLE001
        return False
