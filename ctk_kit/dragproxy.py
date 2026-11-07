"""拖动窗口边框时，把尺寸变化交给一个替身窗口，主窗口内容不动。

Windows 上拖边角改尺寸，系统会持续给窗口发 WM_SIZE，Tk 每帧都要重排并
重画整窗内容，控件多的页面一次就要一两百毫秒，看起来就是卡。

这里做的是：在 ``WM_NCLBUTTONDOWN`` 命中窗口边框时，不再让系统去拖主窗口，
而是自己跟踪鼠标、只调整一个空的替身窗口；松手时把最终尺寸一次性交给主
窗口。拖动全程主窗口一帧都没变，所以内容不重排，拖动始终跟手。

只在 Windows 上生效；拿不到句柄或出现任何异常时直接放行，退回系统默认行为。
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import sys
import tkinter as tk
from typing import Optional

__all__ = ["DragProxy"]

#: 命中的边框方向（Win32 HT* 常量）。
_HT_LEFT = 10
_HT_RIGHT = 11
_HT_TOP = 12
_HT_TOPLEFT = 13
_HT_TOPRIGHT = 14
_HT_BOTTOM = 15
_HT_BOTTOMLEFT = 16
_HT_BOTTOMRIGHT = 17
_EDGES = frozenset(
    {
        _HT_LEFT,
        _HT_RIGHT,
        _HT_TOP,
        _HT_TOPLEFT,
        _HT_TOPRIGHT,
        _HT_BOTTOM,
        _HT_BOTTOMLEFT,
        _HT_BOTTOMRIGHT,
    }
)

_WM_NCLBUTTONDOWN = 0x00A1
_GWL_WNDPROC = -4
_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_NOZORDER = 0x0004
_SWP_NOACTIVATE = 0x0010
_VK_LBUTTON = 0x01

#: 拖动时多久跟一次鼠标（毫秒）。太大会拖影，太小只是多几次空转。
_TICK_MS = 15

#: 主窗口的最小尺寸（物理像素），避免拖成 0。
_MIN_W = 240
_MIN_H = 160


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def _user32():
    return ctypes.windll.user32


class DragProxy:
    """把「拖边框改尺寸」换成「拖一个空窗口」，松手后再交给主窗口。"""

    def __init__(
        self,
        window: tk.Misc,
        *,
        bg: Optional[str] = None,
        alpha: float = 0.92,
    ) -> None:
        self.window = window.winfo_toplevel()
        self.bg = bg or "#202124"
        self.alpha = alpha
        self.hwnd = 0
        self._old_proc = 0
        self._proc = None
        self._active = False
        self._edge = 0
        self._mask: Optional[tk.Toplevel] = None
        self._start = (0, 0)
        self._rect = (0, 0, 0, 0)
        self._job: Optional[str] = None
        self._install()

    # -- 安装 / 卸载 ---------------------------------------------------

    def _install(self) -> None:
        if sys.platform != "win32":
            return
        try:
            user32 = _user32()
            user32.GetParent.restype = ctypes.c_void_p
            user32.GetParent.argtypes = [ctypes.c_void_p]
            user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
            user32.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
            user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
            user32.SetWindowLongPtrW.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.c_ssize_t,
            ]
            user32.CallWindowProcW.restype = ctypes.c_ssize_t
            user32.CallWindowProcW.argtypes = [
                ctypes.c_ssize_t,
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.c_size_t,
                ctypes.c_ssize_t,
            ]
            inner = int(self.window.winfo_id())
            hwnd = int(user32.GetParent(ctypes.c_void_p(inner)) or 0) or inner
            self.hwnd = hwnd
            self._old_proc = int(
                user32.GetWindowLongPtrW(ctypes.c_void_p(hwnd), _GWL_WNDPROC)
            )
            self._proc = ctypes.WINFUNCTYPE(
                ctypes.c_ssize_t,
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.c_size_t,
                ctypes.c_ssize_t,
            )(self._wndproc)
            user32.SetWindowLongPtrW(
                ctypes.c_void_p(hwnd), _GWL_WNDPROC, self._proc
            )
        except Exception:  # noqa: BLE001 - 拿不到就退回系统默认行为
            self.hwnd = 0

    def uninstall(self) -> None:
        """恢复原来的窗口过程。"""
        self._cancel()
        if not self.hwnd:
            return
        try:
            user32 = _user32()
            user32.SetWindowLongPtrW(
                ctypes.c_void_p(self.hwnd), _GWL_WNDPROC, self._old_proc
            )
        except Exception:  # noqa: BLE001 - 窗口已经没了
            pass
        self.hwnd = 0

    # -- 窗口过程 -------------------------------------------------------

    def _wndproc(self, hwnd, message, wparam, lparam):
        try:
            if message == _WM_NCLBUTTONDOWN and wparam in _EDGES and not self._active:
                if self._begin(wparam):
                    # 自己接管拖动，别让系统再去拖主窗口。
                    return 0
        except Exception:  # noqa: BLE001 - 回调里绝不能抛
            pass
        try:
            user32 = _user32()
            return user32.CallWindowProcW(
                self._old_proc, hwnd, message, wparam, lparam
            )
        except Exception:  # noqa: BLE001
            return 0

    # -- 拖动过程 -------------------------------------------------------

    def _begin(self, edge: int) -> bool:
        try:
            user32 = _user32()
            user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(_RECT)]
            rect = _RECT()
            if not user32.GetWindowRect(ctypes.c_void_p(self.hwnd), ctypes.byref(rect)):
                return False
            pt = wt.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            self._start = (pt.x, pt.y)
            self._rect = (rect.left, rect.top, rect.right, rect.bottom)
            self._edge = int(edge)
            self._mask = self._make_mask(rect)
            self._active = True
            self._job = self.window.after(_TICK_MS, self._tick)
            return True
        except Exception:  # noqa: BLE001
            self._active = False
            return False

    def _make_mask(self, rect: _RECT) -> tk.Toplevel:
        mask = tk.Toplevel(self.window)
        mask.overrideredirect(True)
        mask.configure(bg=self.bg)
        try:
            mask.attributes("-alpha", max(0.05, min(1.0, self.alpha)))
            mask.attributes("-toolwindow", True)
        except tk.TclError:
            pass
        mask.geometry(
            f"{rect.right - rect.left}x{rect.bottom - rect.top}"
            f"+{rect.left}+{rect.top}"
        )
        mask.update_idletasks()
        return mask

    def _tick(self) -> None:
        self._job = None
        if not self._active:
            return
        try:
            user32 = _user32()
            if not (user32.GetAsyncKeyState(_VK_LBUTTON) & 0x8000):
                self._finish()
                return
            pt = wt.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            self._place_mask(self._geometry_for(pt.x, pt.y))
            self._job = self.window.after(_TICK_MS, self._tick)
        except tk.TclError:
            self._cancel()

    def _geometry_for(self, x: int, y: int) -> tuple:
        left, top, right, bottom = self._rect
        dx, dy = x - self._start[0], y - self._start[1]
        edge = self._edge
        if edge in (_HT_LEFT, _HT_TOPLEFT, _HT_BOTTOMLEFT):
            left += dx
        if edge in (_HT_RIGHT, _HT_TOPRIGHT, _HT_BOTTOMRIGHT):
            right += dx
        if edge in (_HT_TOP, _HT_TOPLEFT, _HT_TOPRIGHT):
            top += dy
        if edge in (_HT_BOTTOM, _HT_BOTTOMLEFT, _HT_BOTTOMRIGHT):
            bottom += dy
        if right - left < _MIN_W:
            if edge in (_HT_LEFT, _HT_TOPLEFT, _HT_BOTTOMLEFT):
                left = right - _MIN_W
            else:
                right = left + _MIN_W
        if bottom - top < _MIN_H:
            if edge in (_HT_TOP, _HT_TOPLEFT, _HT_TOPRIGHT):
                top = bottom - _MIN_H
            else:
                bottom = top + _MIN_H
        return left, top, right, bottom

    def _place_mask(self, geometry: tuple) -> None:
        mask = self._mask
        if mask is None:
            return
        left, top, right, bottom = geometry
        mask.geometry(f"{right - left}x{bottom - top}+{left}+{top}")

    def _finish(self) -> None:
        left, top, right, bottom = self._current()
        self._cancel()
        try:
            user32 = _user32()
            user32.SetWindowPos.argtypes = [
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_uint,
            ]
            user32.SetWindowPos(
                ctypes.c_void_p(self.hwnd),
                None,
                left,
                top,
                right - left,
                bottom - top,
                _SWP_NOZORDER | _SWP_NOACTIVATE,
            )
        except Exception:  # noqa: BLE001 - 失败就留给用户再拖一次
            pass
        self.window.event_generate("<<ResizeProxyFinished>>", when="tail")

    def _current(self) -> tuple:
        mask = self._mask
        if mask is None:
            return self._rect
        try:
            return (
                mask.winfo_rootx(),
                mask.winfo_rooty(),
                mask.winfo_rootx() + mask.winfo_width(),
                mask.winfo_rooty() + mask.winfo_height(),
            )
        except tk.TclError:
            return self._rect

    def _cancel(self) -> None:
        self._active = False
        if self._job is not None:
            try:
                self.window.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None
        mask, self._mask = self._mask, None
        if mask is not None:
            try:
                mask.destroy()
            except tk.TclError:
                pass
