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
    DangerButton,
    PrimaryButton,
    SecondaryButton,
)
from ctk_kit.layout import HintLabel, PageHeader, Scrollable, SectionTitle
from ctk_kit.theme import color_of

from ..shell import _card_body, _card_shell, _code_panel, _feedback, _row, run_page

TITLE = "按钮"

BASIC_CODE = '''from ctk_kit import PrimaryButton, SecondaryButton, DangerButton

PrimaryButton(frame, "保存", on_save)
# PrimaryButton(master, text, command=None, *, width=120, height=38,
#                radius=9, font=FONT_BODY)

SecondaryButton(frame, "取消", on_cancel)
# SecondaryButton(master, text, command=None, *, width=76, height=30,
#             font=FONT_SMALL, border=False)   # border=True 多一圈细边

DangerButton(frame, "删除", on_delete)
# DangerButton(master, text, command=None, *, width=76, height=30,
#               font=FONT_SMALL)'''

MICRO_CODE = '''from ctk_kit import FlatButton, SoftButton

FlatButton(frame, "复制", on_copy)
# 宽度由文字实测宽度 + padx * 2 算出来，文字长了自动变宽
# FlatButton(master, text, command=None, *, bg=None, hover=None, fg=None,
#            font=FONT_TINY, padx=10, pady=3, radius=8)

SoftButton(frame, "收起", on_collapse)
# SoftButton(master, text, command=None)
# 内部就是 fg=COLOR_MUTED、padx=8、pady=2 的 FlatButton'''

SIZE_CODE = '''PrimaryButton(frame, "160×46", on_click, width=160, height=46)
SecondaryButton(frame, "次要 120", on_click, width=120)
DangerButton(frame, "危险 38 高", on_click, height=38)

# 只给 width：高度沿用各自的默认值（主按钮 38、次要/危险 30）
# 只给 height：宽度沿用默认值（主 120、次 76）
# SecondaryButton 的高度超过 30 时，圆角自动从 8 加到 9'''

DISABLED_CODE = '''button = PrimaryButton(frame, "已禁用", None)
button.configure(state="disabled")
# 也可以是 SecondaryButton / DangerButton / FlatButton
# state="disabled" 保留原来的配色，只降低不透明度，不会变成灰块'''


def build(master) -> ctk.CTkFrame:
    """四个工厂函数 + 两个类，连同尺寸矩阵与禁用态。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = PageHeader(page, TITLE)
    info.configure(text="4 个工厂函数 + 2 个类")

    feedback = _feedback(page, "点任意按钮，回显会出现在这里")

    area = Scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    SectionTitle(area, "基础按钮")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    PrimaryButton(row, "主按钮", lambda: feedback("点了「主按钮」")).pack(side="left")
    SecondaryButton(row, "次要按钮", lambda: feedback("点了「次要按钮」")).pack(
        side="left", padx=(8, 0)
    )
    SecondaryButton(
        row, "描边按钮", lambda: feedback("点了「描边按钮」（border=True）"), border=True
    ).pack(side="left", padx=(8, 0))
    DangerButton(row, "危险按钮", lambda: feedback("点了「危险按钮」")).pack(
        side="left", padx=(8, 0)
    )
    HintLabel(
        body, "主按钮 38 高；次要/危险按钮 30 高；描边版只是多一圈细边。"
    ).pack(fill="x")
    _code_panel(
        body,
        BASIC_CODE,
        "三个工厂函数的签名都在上面；command 不接收参数，要传参就用 lambda 包一层。",
    )

    SectionTitle(area, "微型按钮（宽度按文字实测）")
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
    HintLabel(body, "卡片里的「复制 / 详情」就用这两个，不会浪费横向空间。").pack(
        fill="x"
    )
    _code_panel(
        body,
        MICRO_CODE,
        "两个类不用传宽高，宽度按文字实测；要改配色就传 bg / hover / fg。",
    )

    SectionTitle(area, "尺寸矩阵")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    for width, height in ((84, 30), (120, 38), (160, 46)):
        PrimaryButton(
            row,
            f"{width}×{height}",
            lambda w=width, h=height: feedback(f"主按钮 {w}×{h}"),
            width=width,
            height=height,
        ).pack(side="left", padx=(0, 8))
    row = _row(body, bg)
    for width in (60, 76, 120):
        SecondaryButton(
            row,
            f"次要 {width}",
            lambda w=width: feedback(f"次要按钮宽 {w}"),
            width=width,
        ).pack(side="left", padx=(0, 8))
    row = tk.Frame(body, bg=bg)
    row.pack(fill="x")
    for height in (26, 30, 38):
        DangerButton(
            row,
            f"危险 {height} 高",
            lambda h=height: feedback(f"危险按钮高 {h}"),
            height=height,
        ).pack(side="left", padx=(0, 8))
    _code_panel(
        body,
        SIZE_CODE,
        "width / height 都是像素；省略哪个就用那个函数的默认值。",
    )

    SectionTitle(area, "禁用态")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    for factory, text in (
        (PrimaryButton, "主按钮"),
        (SecondaryButton, "次要按钮"),
        (DangerButton, "危险按钮"),
    ):
        button = factory(row, text, lambda: None)
        button.configure(state="disabled")
        button.pack(side="left", padx=(0, 8))
    HintLabel(body, "state='disabled' 后仍保持原来的配色，只降低不透明度。").pack(
        fill="x"
    )
    _code_panel(
        body,
        DISABLED_CODE,
        "禁用只改 state，不用换一套配色；恢复用 state=\"normal\"。",
    )
    return page


def main() -> int:
    return run_page(build, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
