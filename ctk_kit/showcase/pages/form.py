"""表单页：把输入、下拉、分段、开关与底部动作拼成一张真实表单。

单独启动：``python -m ctk_kit.showcase.pages.form``
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.buttons import primary_button, soft_button
from ctk_kit.dropdown import DropField
from ctk_kit.inputs import form_entry, segmented, switch
from ctk_kit.layout import (
    divider,
    field_label,
    hint_label,
    page_header,
    scrollable,
    section_title,
)
from ctk_kit.theme import color_of

from ..shell import _card_body, _card_shell, _feedback, _row, _text, run_page

TITLE = "表单"


def build(master) -> ctk.CTkFrame:
    """把输入、下拉、分段、开关与底部动作拼成一张真实表单。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    info.configure(text="输入 + 下拉 + 分段 + 开关")

    feedback = _feedback(page, "填完点「保存」，会回显读到的值")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    section_title(area, "基本信息")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    entries: dict = {}
    for label, placeholder, password in (
        ("名称", "例如：公司邮箱", False),
        ("账号", "登录用的账号", False),
        ("密码", "选填，可点右侧生成", True),
    ):
        row = _row(body, bg)
        field_label(row, label).pack(side="left")
        entry = form_entry(row, placeholder=placeholder, password=password)
        entry.pack(side="left", fill="x", expand=True)
        entries[label] = entry

    row = _row(body, bg)
    field_label(row, "分类").pack(side="left")
    category = segmented(row, ["账号", "恢复码", "密钥"], width=280)
    category.pack(side="left")

    row = _row(body, bg)
    field_label(row, "来源").pack(side="left")
    source = DropField(
        row,
        values_provider=lambda: ["手动录入", "导入", "浏览器插件"],
        placeholder="选择来源",
    )
    source.pack(side="left", fill="x", expand=True)

    row = tk.Frame(body, bg=bg)
    row.pack(fill="x")
    _text(
        row,
        "保存后通知我",
        font=T.FONT_BODY,
        color=color_of(T.COLOR_TEXT),
        bg=bg,
    ).pack(side="left")
    notify = switch(row)
    notify.pack(side="left", padx=(12, 0))
    notify.select()

    divider(body, pady=(14, 12))
    footer = tk.Frame(body, bg=bg)
    footer.pack(fill="x")
    hint_label(footer, "带 * 为必填；保存后立即加密写入").pack(side="left")

    def save() -> None:
        summary = " / ".join(
            f"{name}={widget.get() or '空'}" for name, widget in entries.items()
        )
        feedback(
            f"保存：{summary} / 分类={category.get()} / 来源={source.get() or '空'} / "
            f"通知={'开' if notify.get() else '关'}"
        )

    def reset() -> None:
        for widget in entries.values():
            widget.delete(0, "end")
        source.set("")
        category.set("账号")
        notify.deselect()
        feedback("已重置表单")

    primary_button(footer, "保存", save, width=104).pack(side="right")
    soft_button(footer, "重置", reset, width=80, height=38, border=True).pack(
        side="right", padx=(0, 10)
    )
    return page


def main() -> int:
    return run_page(build, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
