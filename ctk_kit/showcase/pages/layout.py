"""布局页：八个布局构件各来一份，说明什么时候用哪个。

单独启动：``python -m ctk_kit.showcase.pages.layout``
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.layout import (
    divider,
    empty_hint,
    field_label,
    hint_label,
    page_header,
    scrollable,
    section_title,
    style_scrollable,
)
from ctk_kit.theme import color_of

from ..shell import _card_body, _card_shell, _feedback, _row, _text, run_page

TITLE = "布局"


def build(master) -> ctk.CTkFrame:
    """八个布局构件各来一份，说明什么时候用哪个。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    info.configure(text="8 个布局构件")

    feedback = _feedback(page, "布局构件本身没有回调，看结构就行")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    # --- 页头 ---
    section_title(area, "页头 page_header")
    head, head_info = page_header(area, "示例页头")
    head_info.configure(text="右侧信息标签")
    hint_label(
        area, "返回 (容器, 信息标签)；信息标签文案由调用方自己 configure。"
    ).pack(fill="x")

    # --- 分区标题 ---
    section_title(area, "分区标题 section_title")
    hint_label(
        area, "自动 pack，上下留 (SPACE_LG, SPACE_SM-2)；设置页的分区就用它。"
    ).pack(fill="x")

    # --- 卡片 / 分隔线 / 字段 ---
    section_title(area, "卡片 card + 分隔线 divider + 字段标签")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    field_label(body, "字段名").pack(side="left")
    _text(
        body,
        "field_label 固定 112 宽，让右边的输入框对齐成一列。",
        font=T.FONT_SMALL,
        color=color_of(T.COLOR_MUTED),
        bg=bg,
    ).pack(side="left")

    divider(body, pady=(8, 10))
    _text(
        body,
        "divider 是一条 1px 的 COLOR_BORDER，比 ttk.Separator 好控色。",
        font=T.FONT_SMALL,
        color=color_of(T.COLOR_MUTED),
        bg=bg,
        anchor="w",
    ).pack(fill="x")

    # --- 滚动容器 ---
    section_title(area, "滚动容器 scrollable")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    inner = style_scrollable(
        ctk.CTkScrollableFrame(body, fg_color="transparent", height=150)
    )
    inner.pack(fill="x", pady=(0, 8))
    for index in range(1, 21):
        _text(
            inner,
            f"第 {index:02d} 行：内容超过高度时出现窄滚动条（宽 {T.SCROLLBAR_WIDTH}px）。",
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_TEXT),
            bg=color_of(T.COLOR_BG),
            anchor="w",
        ).pack(fill="x", pady=1)
    hint_label(body, "scrollable() 已经调好滚动条；style_scrollable 可装饰已有容器。").pack(
        fill="x"
    )

    # --- 空态 ---
    section_title(area, "空态 empty_hint")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = tk.Frame(body, bg=bg)
    row.pack(fill="x", pady=(0, 8))
    empty_hint(row, "这里还没有内容").pack(side="left", expand=True)
    empty_hint(row, "这里还没有内容", "带 detail 时是两行：主提示 + 补充说明").pack(
        side="left", expand=True
    )
    return page


def main() -> int:
    return run_page(build, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
