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
    "clear_window_alpha",
    "disable_acrylic",
    "enable_acrylic",
    "extended_frame_bounds",
    "set_client_rect",
    "set_dwm_attribute",
    "set_frame_border_thickness",
    "set_transitions_disabled",
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
#: ``WCA_ACCENT_POLICY`` 的默认属性号。历史上这里用 30（pywinstyles 用 19），
#: 两者的实际效果差别很大，所以做成可传参数：默认沿用 30 保持原有观感，
#: 想试 tint 是否生效可以传 19。
WCA_ACCENT_POLICY = 19
#: ``SetWindowCompositionAttribute`` 的另一个候选属性号（官方文档值）
WCA_ACCENT_POLICY_OFFICIAL = 19
#: ``ACCENT_ENABLE_BLURBEHIND``（Win11 上 acrylic 用这个，``4`` 已经失效）
ACCENT_ENABLE_BLURBEHIND = 3
#: ``ACCENT_ENABLE_ACRYLICBLURBEHIND``（Win10 1803+，Win11 上会卡顿）
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
#: ``ACCENT_ENABLE_TRANSPARENTGRADIENT``：只做透明渐变，不模糊
ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
#: ``ACCENT_DISABLED``：关掉 accent 合成
ACCENT_DISABLED = 0
#: ``DWMWA_USE_IMMERSIVE_DARK_MODE`` / ``DWMWA_SYSTEMBACKDROP_TYPE``
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38
#: ``DWMWA_WINDOW_CORNER_PREFERENCE``（33）与取值
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2
#: ``DWMWA_TRANSITIONS_FORCEDISABLED``（3）：1 关掉窗口过渡动画
DWMWA_TRANSITIONS_FORCEDISABLED = 3
#: ``DWMWA_EXTENDED_FRAME_BOUNDS``（9）：含阴影的真实屏幕矩形，只读
DWMWA_EXTENDED_FRAME_BOUNDS = 9
#: ``DWMWA_VISIBLE_FRAME_BORDER_THICKNESS``（37，Win11 22H2+）：0 去掉 1px 边框
DWMWA_VISIBLE_FRAME_BORDER_THICKNESS = 37
#: ``DWMWA_BORDER_COLOR``（Win11 22H2+）：不画系统边框
DWMWA_BORDER_COLOR = 34
#: ``DWMWA_CAPTION_COLOR``：标题栏底色，``DWMWA_COLOR_DEFAULT`` 交还给 DWM
DWMWA_CAPTION_COLOR = 35
DWMWA_COLOR_NONE = 0xFFFFFFFE
#: ``DWMWA_COLOR_DEFAULT``：把边框色恢复成系统默认
DWMWA_COLOR_DEFAULT = 0xFFFFFFFF
#: 系统背板类型
BACKDROP_NONE = 0
#: ``DWMSBT_TRANSIENTWINDOW``：亚克力，标题栏和客户区一起糊，但会被系统提亮
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


def set_round_region(window: Any, radius: int, width: int = 0, height: int = 0) -> bool:
    """给窗口裁一个圆角矩形区域，四个角以外直接不画。

    DWM 的 ``DWMWA_WINDOW_CORNER_PREFERENCE``（33）只对有系统边框的窗口
    生效；无边框窗口（``overrideredirect`` + ``WS_THICKFRAME``）拿不到，
    所以在「底层颜色窗口」这种场景只能自己裁区域。

    参数:
        window: 目标窗口。
        radius: 圆角半径（物理像素），``0`` 表示恢复成方角。
        width: 区域宽（物理像素），``0`` 表示取窗口当前宽度。
        height: 区域高（物理像素），``0`` 表示取窗口当前高度。
    """
    if not available:
        return False
    try:
        hwnd = _toplevel_handle(window)
        box_w = int(width or window.winfo_width())
        box_h = int(height or window.winfo_height())
        if box_w <= 1 or box_h <= 1:
            return False
        radius = max(0, int(radius))
        region = windll.gdi32.CreateRoundRectRgn(
            0, 0, box_w + 1, box_h + 1, radius * 2, radius * 2
        )
        windll.user32.SetWindowRgn(hwnd, region, True)
        return True
    except Exception:  # noqa: BLE001 - 窗口还没建好 / 非 Windows
        return False


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


def _set_accent(
    hwnd: int, state: int, color: Optional[int], attribute: int = WCA_ACCENT_POLICY
) -> None:
    accent = _ACCENT_POLICY()
    accent.AccentState = state
    if color is not None:
        accent.GradientColor = color
    data = _WINDOW_COMPOSITION_ATTRIBUTES()
    data.Attribute = attribute
    data.SizeOfData = sizeof(accent)
    data.Data = pointer(accent)
    windll.user32.SetWindowCompositionAttribute(hwnd, pointer(data))


def _extend_frame(hwnd: int) -> None:
    _set_margins(hwnd, -1, -1, -1, -1)


def _set_margins(hwnd: int, left: int, top: int, right: int, bottom: int) -> None:
    margins = _MARGINS(left, top, right, bottom)
    windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, byref(margins))


def set_dwm_attribute(window: Any, attribute: int, value: Optional[int]) -> bool:
    """直接给 DWM 写一个整数属性，返回是否调用成功。

    ``value=None`` 写 ``0xFFFFFFFF``（``DWMWA_COLOR_DEFAULT``），把属性恢复
    成系统默认。常用属性见 :data:`DWMWA_WINDOW_CORNER_PREFERENCE` 等常量。
    """
    if not available:
        return False
    try:
        hwnd = _toplevel_handle(window)
        data = c_int(-1 if value is None else int(value))
        windll.dwmapi.DwmSetWindowAttribute(hwnd, attribute, byref(data), sizeof(data))
        windll.dwmapi.DwmFlush()
        return True
    except Exception:  # noqa: BLE001 - 属性不被这个系统版本支持
        return False


def _dwm_set_int(window: Any, attribute: int, value: int) -> bool:
    """写一个 DWORD 型 DWM 属性，返回 HRESULT 是否为 0（成功）。"""
    if not available:
        return False
    try:
        hwnd = _toplevel_handle(window)
        data = c_int(int(value))
        result = windll.dwmapi.DwmSetWindowAttribute(
            hwnd, attribute, byref(data), sizeof(data)
        )
        windll.dwmapi.DwmFlush()
        return result == 0
    except Exception:  # noqa: BLE001 - 属性不被这个系统版本支持
        return False


def set_frame_border_thickness(window: Any, thickness: int = 0) -> bool:
    """``DWMWA_VISIBLE_FRAME_BORDER_THICKNESS``（37）：0 去掉那条 1px 边框。

    比 ``DWMWA_BORDER_COLOR = COLOR_NONE`` 更彻底：那个只是把颜色刷成透明，
    边框本身还在，窗口拿到焦点时仍可能闪一条浅色线。仅 Win11 22H2+ 支持，
    老系统上返回 ``False``、不做任何事。
    """
    return _dwm_set_int(window, DWMWA_VISIBLE_FRAME_BORDER_THICKNESS, thickness)


def set_transitions_disabled(window: Any, disabled: bool = True) -> bool:
    """``DWMWA_TRANSITIONS_FORCEDISABLED``（3）：关掉 DWM 的窗口过渡动画。

    切玻璃、重建页面时少一帧「旧内容残留」；代价是窗口出现/消失也没有淡入
    淡出。
    """
    return _dwm_set_int(window, DWMWA_TRANSITIONS_FORCEDISABLED, 1 if disabled else 0)


def extended_frame_bounds(window: Any) -> Optional[tuple[int, int, int, int]]:
    """``DWMWA_EXTENDED_FRAME_BOUNDS``（9）：窗口含阴影的真实屏幕矩形。

    返回 ``(left, top, right, bottom)``（物理像素）；读不到时返回 ``None``。
    比 ``winfo_rootx()`` 那套（客户区坐标）多出阴影和边框，弹层要贴屏幕边
    时用它算才对得齐。
    """
    if not available:
        return None
    try:
        hwnd = _toplevel_handle(window)
        rect = RECT()
        result = windll.dwmapi.DwmGetWindowAttribute(
            hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, byref(rect), sizeof(rect)
        )
        if result != 0:
            return None
        return (rect.left, rect.top, rect.right, rect.bottom)
    except Exception:  # noqa: BLE001 - 非 Windows 或系统太老
        return None


def clear_window_alpha(window: Any) -> bool:
    """去掉 Tk ``-alpha`` 留下的 ``WS_EX_LAYERED``，返回是否真的清掉了。

    ``wm attributes -alpha`` 只要设过一次，窗口就带上 ``WS_EX_LAYERED``，
    即使后来把值改回 1.0 也还是 layered —— 而 DWM 只对非 layered 窗口做
    玻璃合成。想把毛玻璃拿回来，必须把扩展样式里的这一位摘掉，再让
    DWM 重算一次窗口框架。
    """
    if not available:
        return False
    try:
        hwnd = _toplevel_handle(window)
        ex_style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & 0xFFFFFFFF
        if not ex_style & WS_EX_LAYERED:
            return False
        windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style & ~WS_EX_LAYERED)
        windll.user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE,
        )
        windll.dwmapi.DwmFlush()
        return True
    except Exception:  # noqa: BLE001 - 非 Windows 或窗口已经销毁
        return False


def enable_acrylic(
    window: Any,
    *,
    tint: Optional[int] = None,
    dark: bool = True,
    system_backdrop: Any = 0,
    frame: bool = True,
    accent: int = ACCENT_ENABLE_BLURBEHIND,
    attribute: int = WCA_ACCENT_POLICY,
    extend: bool = True,
) -> bool:
    """让窗口背景变成系统亚克力，返回是否成功。

    无边框窗口（``overrideredirect(True)``）要先补一个 ``WS_THICKFRAME``：
    DWM 只对「有非客户区」的窗口走玻璃合成，纯 ``WS_POPUP`` 上只会得到
    一层均匀的 tint。补边框不改变 Tk 的外观，窗口仍然没有标题栏。
    ``frame=False`` 跳过这一步——标准窗口本来就有边框，多余的一次
    ``SetWindowPos(FRAMECHANGED)`` 会让 DWM 重算非客户区，标题栏的玻璃
    可能跟着被重置。

    ``tint`` 是 ``0xAABBGGRR``（注意 BGR 顺序），alpha 越高玻璃越暗；窗口内容
    需要自己留出透明区域，通常是一层纯黑底（见 :func:`acrylic_window`）。

    ``accent`` 决定 accent 状态：``3`` 是模糊（默认），``4`` 是 Win10 的
    亚克力（Win11 上可能卡顿），``2`` 只做透明渐变不模糊。

    ``extend`` 控制是否 ``DwmExtendFrameIntoClientArea(-1)``：整个客户区都
    算玻璃区域，纯黑像素才被当作透明。

    ``system_backdrop`` 非 0 时改用系统背板（``2`` Mica / ``3`` 亚克力），
    **标题栏也会一起糊上**，这是 accent 策略做不到的（Win11 的 accent 只管
    客户区）。代价是 tint 交给系统，亮度和透明度不能再调，两者不能同时用。
    """
    if not available:
        return False
    try:
        hwnd = _toplevel_handle(window)
        if frame:
            style = windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style | WS_THICKFRAME)
            windll.user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER,
            )
            window.update_idletasks()
        kind = BACKDROP_ACRYLIC if system_backdrop is True else int(system_backdrop or 0)
        if kind:
            # 系统背板：标题栏和客户区一起糊，亮度交给系统深色主题。
            # 不吃 tint，所以不叠 accent；客户区仍要 extend，纯黑像素才会
            # 被当成透明、露出背板。
            if extend:
                _extend_frame(hwnd)
            else:
                _set_margins(hwnd, 0, 0, 0, 0)
            backdrop = c_int(kind)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_SYSTEMBACKDROP_TYPE, byref(backdrop), sizeof(backdrop)
            )
        else:
            _set_accent(hwnd, accent, tint, attribute)
            if extend:
                _extend_frame(hwnd)
            else:
                _set_margins(hwnd, 0, 0, 0, 0)
            # accent 路径下不要再设 38：它会把窗口换成系统背板，覆盖 tint。
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


def disable_acrylic(window: Any) -> bool:
    """关掉 :func:`enable_acrylic` 开的玻璃，返回是否成功。

    只撤销合成相关的属性（accent、客户区延伸、系统背板、边框色），
    ``WS_THICKFRAME`` 保持不动：主窗口本来就有边框，摘掉它反而让 Tk 的
    geometry 语义变回「外框 = 客户区」，尺寸会跳一下。
    """
    if not available:
        return False
    try:
        hwnd = _toplevel_handle(window)
        _set_accent(hwnd, ACCENT_DISABLED, None)
        margins = _MARGINS(0, 0, 0, 0)
        windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, byref(margins))
        backdrop = c_int(BACKDROP_NONE)
        windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_SYSTEMBACKDROP_TYPE, byref(backdrop), sizeof(backdrop)
        )
        border = DWORD(DWMWA_COLOR_DEFAULT)
        windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_BORDER_COLOR, byref(border), sizeof(border)
        )
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
