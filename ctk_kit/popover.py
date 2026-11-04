"""悬浮卡片：点一下控件，旁边弹一块内容。

和 ``Tooltip`` 的区别：Tooltip 是悬停显示的一段文字，鼠标移开就消失；
Popover 是点击打开、可以放按钮 / 输入框等任意控件，点外面才关。

用法::

    from ctk_kit import Popover, PrimaryButton

    def build(parent):
        CTkLabel(parent, text="筛选条件").pack(padx=12, pady=(12, 4))
        PrimaryButton(parent, "应用").pack(padx=12, pady=(4, 12))

    button = PrimaryButton(card, "筛选")
    Popover(button, content=build, width=220)
"""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Any, Callable, Optional, Tuple

import customtkinter as ctk

from . import tokens as T
from .dialog import _round_corners
from .glass import backdrop_image
from .popup import scaled_geometry

__all__ = ["Popover"]

PopoverContent = Optional[Callable[[ctk.CTkFrame], None]]


class Popover:
    """点控件弹出的浮动卡片。

    参数:
        widget: 触发弹层的控件。
        content: 构建内容的函数，参数是弹层内部容器。
        width: 弹层宽度（逻辑像素），默认 240。
        placement: ``bottom``（默认）或 ``top``。
        padding: 预留，暂未使用。
        glass: 是否给卡片铺一张「背后屏幕模糊图」，默认开；截图失败自动退回纯色。

    方法:
        show() / hide() / toggle(): 手动控制。
        destroy(): 关掉并解绑点击事件。
    """

    def __init__(
        self,
        widget: tk.Misc,
        *,
        content: PopoverContent = None,
        width: int = 240,
        placement: str = "bottom",
        padding: int = 12,
        glass: bool = True,
    ) -> None:
        """给 ``widget`` 挂上点击切换弹层的行为。"""
        self._widget = widget
        self._content = content
        self._width = width
        self._placement = placement
        self._padding = padding
        self._glass = glass
        self._window: Optional[ctk.CTkToplevel] = None
        self._backdrop: Optional[ctk.CTkLabel] = None
        self._photo: Optional[ctk.CTkImage] = None
        self._bind_id = widget.bind("<Button-1>", self._on_click, add="+")

    # --- 对外 ---
    def show(self) -> None:
        """打开弹层；已经开着就什么也不做。"""
        if self._window is not None and self._window.winfo_exists():
            return

        window = ctk.CTkToplevel(self._widget)
        window.withdraw()
        window.overrideredirect(True)
        try:
            window.attributes("-topmost", True)
        except tk.TclError:
            pass

        # 描边画在窗口上：整窗铺描边色，卡片四边各内缩 1px，四角跟着圆角
        # 一起弯，不会像控件 border 那样在弧段上有粗细差。
        window.configure(fg_color=T.COLOR_BORDER)
        frame = ctk.CTkFrame(
            window,
            fg_color=T.COLOR_CARD,
            border_width=0,
            # 圆角跟系统 DWM 圆角（8）对齐：卡片比窗口更圆时，四角会露出一
            # 圈比 1px 粗的描边，看起来右边、下边比左边厚。
            corner_radius=T.RADIUS_SMALL,
        )
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        # 背景先建、放在底层；图等内容排好、量出尺寸后再补上
        self._backdrop = ctk.CTkLabel(frame, text="", fg_color="transparent")
        self._backdrop.place(x=0, y=0, relwidth=1, relheight=1)
        if self._content is not None:
            self._content(frame)

        window.update_idletasks()
        try:
            scaling = window._get_window_scaling()
        except Exception:  # noqa: BLE001
            scaling = 1.0
        if self._width:
            # width 是逻辑像素，测量值是物理像素，统一成物理再交给 geometry。
            width = max(1, int(round(self._width * scaling)))
        else:
            width = frame.winfo_reqwidth()
        height = frame.winfo_reqheight()
        # 几何尺寸按窗口算：左右各 1px 的描边也要算进去。
        width += 2
        height += 2
        x, y = self._place(width, height)
        # 宽高是物理像素，geometry 会再乘窗口缩放，交给 scaled_geometry 除回去；
        # 不这么做的话 125% / 150% 缩放下窗口会被放大，描边看着右边、下边厚。
        window.geometry(scaled_geometry(window, width, height, x, y))
        # 截图必须在 deiconify 之前：这时屏幕上还是浮层背后的真实内容
        self._apply_backdrop(x, y, width, height, scaling)
        # 窗口圆角跟卡片同半径：DWM 圆角半径由系统定，卡片比它更圆时，
        # 四角会露出一圈比 1px 粗的描边。
        _round_corners(window, T.RADIUS_SMALL)
        window.deiconify()
        window.lift()
        window.focus_force()
        window.bind("<FocusOut>", lambda _e: window.after(60, self._maybe_hide))
        self._window = window

    def hide(self) -> None:
        """关掉弹层。"""
        window = self._window
        self._window = None
        self._backdrop = None
        self._photo = None
        if window is not None:
            try:
                window.destroy()
            except Exception:  # noqa: BLE001 - 窗口可能已经没了
                pass

    def toggle(self) -> None:
        """开着就关，关着就开。"""
        if self._window is not None and self._window.winfo_exists():
            self.hide()
        else:
            self.show()

    def destroy(self) -> None:
        """关掉弹层并解绑控件的点击事件。"""
        self.hide()
        try:
            self._widget.unbind("<Button-1>", self._bind_id)
        except Exception:  # noqa: BLE001
            pass

    # --- 内部 ---
    def _on_click(self, _event: tk.Event = None) -> None:
        """控件被点一下。"""
        self.toggle()

    def _place(self, width: int, height: int) -> Tuple[int, int]:
        """放在控件下方居中；贴边就翻到上方或往里收。"""
        widget = self._widget
        x = widget.winfo_rootx() + (widget.winfo_width() - width) // 2
        if self._placement == "top":
            y = widget.winfo_rooty() - height - 6
        else:
            y = widget.winfo_rooty() + widget.winfo_height() + 6

        screen_w = widget.winfo_screenwidth()
        screen_h = widget.winfo_screenheight()
        x = max(8, min(x, screen_w - width - 8))
        y = max(8, min(y, screen_h - height - 40))
        return x, y

    def _apply_backdrop(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        scaling: float,
    ) -> None:
        """把截下来的模糊图塞进背景标签；截图失败就保持纯色卡片。"""
        if not self._glass or self._backdrop is None:
            return
        with contextlib.suppress(Exception):
            image = backdrop_image(
                x,
                y,
                width,
                height,
                scaling=scaling,
                radius=T.RADIUS_SMALL,
            )
            if image is None:
                return
            photo = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(
                    max(1, int(round(width / scaling))),
                    max(1, int(round(height / scaling))),
                ),
            )
            self._photo = photo
            self._backdrop.configure(image=photo)

    def _maybe_hide(self) -> None:
        """焦点离开后，指针也不在弹层或触发控件上才关。"""
        if self._window is None:
            return
        try:
            x, y = self._window.winfo_pointerxy()
            under = self._window.winfo_containing(x, y)
        except Exception:  # noqa: BLE001
            under = None
        if under is not None:
            path = str(under)
            if path.startswith(str(self._window)) or path.startswith(str(self._widget)):
                return
        try:
            focus = self._window.focus_get()
        except Exception:  # noqa: BLE001
            focus = None
        if focus is not None and str(focus).startswith(str(self._window)):
            return
        self.hide()
