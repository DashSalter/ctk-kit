"""按钮页：四个工厂函数 + 两个类，连同尺寸矩阵与禁用态。

单独启动：``python -m ctk_kit.showcase.pages.buttons``
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.buttons import (
    FlatButton,
    SoftButton,
    danger_button,
    primary_button,
    soft_button,
)
from ctk_kit.layout import hint_label, page_header, scrollable, section_title
from ctk_kit.theme import color_of

from ..shell import _card_body, _card_shell, _feedback, _row, run_page

TITLE = "按钮"


def build(master) -> ctk.CTkFrame:
    """四个工厂函数 + 两个类，连同尺寸矩阵与禁用态。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    info.configure(text="4 个工厂函数 + 2 个类")

    feedback = _feedback(page, "点任意按钮，回显会出现在这里")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    section_title(area, "基础按钮")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    primary_button(row, "主按钮", lambda: feedback("点了「主按钮」")).pack(side="left")
    soft_button(row, "次要按钮", lambda: feedback("点了「次要按钮」")).pack(
        side="left", padx=(8, 0)
    )
    soft_button(
        row, "描边按钮", lambda: feedback("点了「描边按钮」（border=True）"), border=True
    ).pack(side="left", padx=(8, 0))
    danger_button(row, "危险按钮", lambda: feedback("点了「危险按钮」")).pack(
        side="left", padx=(8, 0)
    )
    hint_label(
        body, "主按钮 38 高；次要/危险按钮 30 高；描边版只是多一圈细边。"
    ).pack(fill="x")

    section_title(area, "微型按钮（宽度按文字实测）")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    FlatButton(row, "FlatButton", lambda: feedback("点了 FlatButton")).pack(
        side="left"
    )
    SoftButton(row, "SoftButton", lambda: feedback("点了 SoftButton")).pack(
        side="left", padx=(8, 0)
    )
    FlatButton(row, "更长的文字会自动加宽", lambda: feedback("长文字的宽度是算出来的")).pack(
        side="left", padx=(8, 0)
    )
    hint_label(body, "卡片里的「复制 / 详情」就用这两个，不会浪费横向空间。").pack(
        fill="x"
    )

    section_title(area, "尺寸矩阵")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    for width, height in ((84, 30), (120, 38), (160, 46)):
        primary_button(
            row,
            f"{width}×{height}",
            lambda w=width, h=height: feedback(f"主按钮 {w}×{h}"),
            width=width,
            height=height,
        ).pack(side="left", padx=(0, 8))
    row = _row(body, bg)
    for width in (60, 76, 120):
        soft_button(
            row,
            f"次要 {width}",
            lambda w=width: feedback(f"次要按钮宽 {w}"),
            width=width,
        ).pack(side="left", padx=(0, 8))
    row = tk.Frame(body, bg=bg)
    row.pack(fill="x")
    for height in (26, 30, 38):
        danger_button(
            row,
            f"危险 {height} 高",
            lambda h=height: feedback(f"危险按钮高 {h}"),
            height=height,
        ).pack(side="left", padx=(0, 8))

    section_title(area, "禁用态")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    for factory, text in (
        (primary_button, "主按钮"),
        (soft_button, "次要按钮"),
        (danger_button, "危险按钮"),
    ):
        button = factory(row, text, lambda: None)
        button.configure(state="disabled")
        button.pack(side="left", padx=(0, 8))
    hint_label(body, "state='disabled' 后仍保持原来的配色，只降低不透明度。").pack(
        fill="x"
    )
    return page


def main() -> int:
    return run_page(build, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
