"""面包屑：显示当前位置，中间层级可以点回去。

用法::

    from ctk_kit import Breadcrumb

    crumb = Breadcrumb(
        card,
        items=["首页", ("文档", "docs"), ("组件", "docs/components")],
        command=lambda value: print("跳到", value),
    )

``items`` 里字符串表示只有文字，``(文字, 值)`` 表示可点。最后一项是当前页，
不可点；其余项悬停变色、点击回调 ``command(value)``。

默认分隔符 ``›`` 用 Pillow 在 4 倍尺寸上画成折线图，比直接渲染字符清楚；
传其他 ``separator`` 时仍按文字显示。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Sequence, Tuple

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .paint import cached

try:  # Pillow 是可选依赖
    from PIL import Image, ImageDraw

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

__all__ = ["Breadcrumb"]

CrumbCommand = Callable[[Any], None]

#: 分隔符图标的逻辑边长。
_SEPARATOR = 12
#: 画图时的超采样倍数。
_SCALE = 4


def _pair(color: Any) -> Tuple[str, str]:
    """把单色或 ``(浅, 深)`` 色对统一成两色。"""
    if isinstance(color, (tuple, list)) and len(color) == 2:
        return str(color[0]), str(color[1])
    return str(color), str(color)


@cached
def _separator_image(color: str) -> "Image.Image":
    """画默认分隔符 ``›``：一条折线，两端和折点都收圆。"""
    total = _SEPARATOR * _SCALE
    image = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    points = [
        (4 * _SCALE, 3 * _SCALE),
        (8 * _SCALE, 6 * _SCALE),
        (4 * _SCALE, 9 * _SCALE),
    ]
    pen.line(
        points,
        fill=color,
        width=max(1, int(1.6 * _SCALE)),
        joint="curve",
    )
    radius = 0.8 * _SCALE
    for x, y in (points[0], points[-1]):
        pen.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    return image


def _separator_ctk() -> ctk.CTkImage:
    """默认分隔符的浅/深两版图。"""
    light, dark = _pair(T.COLOR_FAINT)
    return ctk.CTkImage(
        light_image=_separator_image(light),
        dark_image=_separator_image(dark),
        size=(_SEPARATOR, _SEPARATOR),
    )


class Breadcrumb(ctk.CTkFrame):
    """横向面包屑。

    参数:
        master: 父容器。
        items: 路径项，字符串或 ``(文字, 值)``。
        command: 点击可点项时的回调，参数是这一项的值（没写值就是文字）。
        separator: 层级之间的分隔符，默认 ``›``。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        set_items(items): 换整条路径。
        get_items(): 当前的路径项。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        items: Sequence[Any] = (),
        command: CrumbCommand = None,
        separator: str = "›",
        **kwargs: Any,
    ) -> None:
        """建面包屑；``items`` 最后一项按当前页处理。"""
        super().__init__(master, fg_color="transparent", **kwargs)

        self._command = command
        self._separator = separator
        self._items: list[tuple[str, Any]] = []

        self.set_items(items)

    # --- 对外 ---
    def set_items(self, items: Sequence[Any]) -> None:
        """换整条路径；每一项是字符串或 ``(文字, 值)``。"""
        for child in self.winfo_children():
            child.destroy()

        self._items = []
        for raw in items:
            if isinstance(raw, (tuple, list)) and len(raw) == 2:
                text, value = str(raw[0]), raw[1]
            else:
                text, value = str(raw), raw
            self._items.append((text, value))

        for index, (text, value) in enumerate(self._items):
            current = index == len(self._items) - 1
            label = ctk.CTkLabel(
                self,
                text=text,
                font=get_font(T.FONT_SMALL),
                text_color=T.COLOR_TEXT if current else T.COLOR_MUTED,
                fg_color="transparent",
            )
            label.pack(side="left")
            if not current:
                label.configure(cursor="hand2")
                label.bind(
                    "<Button-1>", lambda _e, v=value: self._emit(v)
                )
                label.bind(
                    "<Enter>",
                    lambda _e, lbl=label: lbl.configure(text_color=T.COLOR_ACTIVE),
                )
                label.bind(
                    "<Leave>",
                    lambda _e, lbl=label: lbl.configure(text_color=T.COLOR_MUTED),
                )

            if not current:
                self._separator_label().pack(side="left", padx=6)

    def get_items(self) -> list[tuple[str, Any]]:
        """当前路径，返回 ``(文字, 值)`` 列表。"""
        return list(self._items)

    # --- 内部 ---
    def _separator_label(self) -> ctk.CTkLabel:
        """默认「›」用 PIL 图；自定义分隔符仍按文字。"""
        if self._separator == "›" and _HAS_PIL:
            return ctk.CTkLabel(
                self,
                text="",
                image=_separator_ctk(),
                width=_SEPARATOR,
                height=_SEPARATOR,
                fg_color="transparent",
            )
        return ctk.CTkLabel(
            self,
            text=self._separator,
            font=get_font(T.FONT_SMALL),
            text_color=T.COLOR_FAINT,
            fg_color="transparent",
        )
    def _emit(self, value: Any) -> None:
        """点击某一级。"""
        if self._command is not None:
            self._command(value)
