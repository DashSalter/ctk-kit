"""总览页：三层结构说明 + 组件索引。

单独启动：``python -m ctk_kit.showcase.pages.overview``
"""

from __future__ import annotations

import customtkinter as ctk

from ctk_kit import __version__
from ctk_kit import tokens as T
from ctk_kit.buttons import SoftButton
from ctk_kit.layout import hint_label, page_header, scrollable, section_title
from ctk_kit.theme import color_of

from ..data import INDEX, PAGES
from ..shell import _card_body, _card_shell, _feedback, _row, _text, run_page

TITLE = "总览"


def build(master, *, navigate=None) -> ctk.CTkFrame:
    """三层结构说明 + 组件索引，点「查看」跳到对应页面。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    info.configure(text=f"v{__version__} · {len(PAGES)} 个页面")

    feedback = _feedback(page, "点「查看」可以跳到对应页面")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    section_title(area, "三层结构")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    for name, desc in (
        ("tokens", "设计令牌：深浅两套颜色、字体、圆角与间距"),
        ("theme", "取色、外观切换，以及原生 tk 控件的重绘"),
        ("组件", "buttons / inputs / dropdown / layout / scroll_list"),
    ):
        row = _row(body, bg)
        _text(
            row,
            name,
            width=10,
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_ACCENT),
            bg=bg,
            anchor="w",
        ).pack(side="left")
        _text(
            row,
            desc,
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_MUTED),
            bg=bg,
            anchor="w",
        ).pack(side="left", padx=(8, 0))

    hint_label(
        body,
        "组件层只依赖 tokens 与 theme；换肤时改 tokens 即可，组件不用动。",
    ).pack(fill="x", pady=(2, 0))

    section_title(area, "组件索引")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    for name, desc in INDEX:
        row = _row(body, bg)
        _text(
            row,
            name,
            width=6,
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_TEXT),
            bg=bg,
            anchor="w",
        ).pack(side="left")
        _text(
            row,
            desc,
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_MUTED),
            bg=bg,
            anchor="w",
        ).pack(side="left", padx=(8, 0))

        def go(key: str = name) -> None:
            if navigate is None:
                feedback(f"这里会跳到「{key}」页")
                return
            navigate(key)
            feedback(f"已跳到「{key}」页")

        SoftButton(row, "查看", go).pack(side="right")
    return page


def main() -> int:
    return run_page(build, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
