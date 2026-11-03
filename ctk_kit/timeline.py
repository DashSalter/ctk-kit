"""时间线：按时间顺序列事件，左侧圆点和竖线把它们串起来。

用法::

    from ctk_kit import Timeline

    Timeline(card, items=[
        {"title": "创建仓库", "time": "09:12", "description": "初始化 main"},
        {"title": "推送首个提交", "time": "09:30"},
        {"title": "发布 0.1.0", "time": "10:05", "active": True},
    ])

也可以先建空的，再 ``add()`` 追加。``active=True`` 的那条圆点用主色。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .paint import cached

try:  # Pillow 是可选依赖
    from PIL import Image, ImageDraw

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

__all__ = ["Timeline"]

TimelineItem = Union[str, Dict[str, Any], Sequence[Any]]

#: 圆点逻辑直径。
_DOT = 10
#: 画圆时的超采样倍数。
_SCALE = 4


def _pair(color: Any) -> Tuple[str, str]:
    """把单色或 ``(浅, 深)`` 色对统一成两色。"""
    if isinstance(color, (tuple, list)) and len(color) == 2:
        return str(color[0]), str(color[1])
    return str(color), str(color)


@cached
def _dot_image(color: str) -> "Image.Image":
    """画时间线圆点，4 倍尺寸抗锯齿。"""
    total = _DOT * _SCALE
    image = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    ImageDraw.Draw(image).ellipse((0, 0, total - 1, total - 1), fill=color)
    return image


def _dot_ctk(active: bool) -> ctk.CTkImage:
    """圆点的浅/深两版图。"""
    color = T.COLOR_ACTIVE if active else T.COLOR_BORDER_STRONG
    light, dark = _pair(color)
    return ctk.CTkImage(
        light_image=_dot_image(light),
        dark_image=_dot_image(dark),
        size=(_DOT, _DOT),
    )


class Timeline(ctk.CTkFrame):
    """纵向时间线。

    参数:
        master: 父容器。
        items: 事件序列；每一项可以是字符串（只当标题）、
            ``(标题, 描述, 时间)``，或带 ``title`` / ``description`` /
            ``time`` / ``active`` 的字典。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        set_items(items): 换整组事件。
        add(title, description="", time="", active=False): 追加一条。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        items: Sequence[TimelineItem] = (),
        **kwargs: Any,
    ) -> None:
        """建时间线。"""
        super().__init__(master, fg_color="transparent", **kwargs)
        self._items: List[Dict[str, Any]] = [
            self._normalize(item) for item in items
        ]
        self._rebuild()

    # --- 对外 ---
    def set_items(self, items: Sequence[TimelineItem]) -> None:
        """换整组事件并重建。"""
        self._items = [self._normalize(item) for item in items]
        self._rebuild()

    def add(
        self,
        title: str,
        description: str = "",
        time: str = "",
        active: bool = False,
    ) -> None:
        """追加一条事件。"""
        self._items.append(
            {
                "title": str(title),
                "description": str(description),
                "time": str(time),
                "active": bool(active),
            }
        )
        self._rebuild()

    # --- 内部 ---
    def _normalize(self, raw: TimelineItem) -> Dict[str, Any]:
        """把字符串 / 元组 / 字典统一成字典。"""
        if isinstance(raw, dict):
            return {
                "title": str(raw.get("title", "")),
                "description": str(raw.get("description", "")),
                "time": str(raw.get("time", "")),
                "active": bool(raw.get("active", False)),
            }
        if isinstance(raw, str):
            return {"title": raw, "description": "", "time": "", "active": False}
        values = list(raw) + ["", "", ""]
        return {
            "title": str(values[0]),
            "description": str(values[1]),
            "time": str(values[2]),
            "active": False,
        }

    def _rebuild(self) -> None:
        """按当前事件重建整条时间线。"""
        for child in self.winfo_children():
            child.destroy()

        total = len(self._items)
        for index, item in enumerate(self._items):
            last = index == total - 1
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x")

            rail = ctk.CTkFrame(row, fg_color="transparent", width=24)
            rail.pack(side="left", fill="y")
            rail.pack_propagate(False)
            if not last:
                ctk.CTkFrame(
                    rail,
                    fg_color=T.COLOR_BORDER,
                    width=2,
                    corner_radius=1,
                ).place(x=11, y=0, relheight=1)
            if _HAS_PIL:
                ctk.CTkLabel(
                    rail,
                    text="",
                    image=_dot_ctk(item["active"]),
                    width=_DOT,
                    height=_DOT,
                    fg_color="transparent",
                ).place(x=7, y=5)
            else:
                ctk.CTkFrame(
                    rail,
                    width=_DOT,
                    height=_DOT,
                    corner_radius=_DOT // 2,
                    fg_color=(
                        T.COLOR_ACTIVE
                        if item["active"]
                        else T.COLOR_BORDER_STRONG
                    ),
                ).place(x=7, y=5)

            content = ctk.CTkFrame(row, fg_color="transparent")
            content.pack(
                side="left",
                fill="x",
                expand=True,
                pady=(0, 0 if last else 14),
            )

            head = ctk.CTkFrame(content, fg_color="transparent")
            head.pack(fill="x")
            ctk.CTkLabel(
                head,
                text=item["title"],
                font=get_font((T.FONT_NAME, 13, "bold")),
                text_color=T.COLOR_TEXT,
                anchor="w",
            ).pack(side="left")
            if item["time"]:
                ctk.CTkLabel(
                    head,
                    text=item["time"],
                    font=get_font(T.FONT_TINY),
                    text_color=T.COLOR_MUTED,
                    anchor="e",
                ).pack(side="right")

            if item["description"]:
                ctk.CTkLabel(
                    content,
                    text=item["description"],
                    font=get_font(T.FONT_SMALL),
                    text_color=T.COLOR_MUTED,
                    anchor="w",
                    justify="left",
                ).pack(fill="x", pady=(2, 0))
