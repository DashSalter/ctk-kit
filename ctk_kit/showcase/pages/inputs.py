"""输入页：六类输入控件，每种都给一个能改状态、能回显的实例。

单独启动：``python -m ctk_kit.showcase.pages.inputs``
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.dropdown import DropField
from ctk_kit.inputs import form_entry, segmented, switch, toolbar_entry
from ctk_kit.layout import (
    field_label,
    hint_label,
    page_header,
    scrollable,
    section_title,
)
from ctk_kit.text import TextArea
from ctk_kit.theme import color_of

from ..shell import _card_body, _card_shell, _feedback, _row, _text, run_page

TITLE = "输入"


def build(master) -> ctk.CTkFrame:
    """六类输入控件，每种都给一个能改状态、能回显的实例。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    info.configure(text="工具栏框 / 表单框 / 分段 / 开关 / 下拉 / 大文本")

    feedback = _feedback(page, "改任意输入，回显会出现在这里")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    # --- 工具栏输入 ---
    section_title(area, "工具栏输入 toolbar_entry")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    field_label(row, "搜索").pack(side="left")
    search = toolbar_entry(row, "输入关键词，聚焦时描边变强调色")
    search.pack(side="left", fill="x", expand=True)
    search.bind("<KeyRelease>", lambda _e: feedback(f"关键词：{search.get() or '（空）'}"))
    hint_label(body, "40 高、圆角 12；FocusIn 时 border_color 变 COLOR_ACCENT。").pack(
        fill="x"
    )

    # --- 表单输入 ---
    section_title(area, "表单输入 form_entry")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    for text, kwargs in (
        ("普通文本", {"placeholder": "不带 placehold 时也能直接输入"}),
        ("密码", {"placeholder": "输入后按圆点显示", "password": True}),
        ("高 28", {"placeholder": "紧凑行", "height": 28}),
        ("高 48", {"placeholder": "宽松行", "height": 48}),
    ):
        row = _row(body, bg)
        field_label(row, text).pack(side="left")
        entry = form_entry(row, **kwargs)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind(
            "<KeyRelease>",
            lambda _e, name=text, widget=entry: feedback(
                f"{name}：{widget.get() or '（空）'}"
            ),
        )
    hint_label(
        body,
        "password=True 时内部 Entry 用 • 打码；带 placeholder 时 cget('show') 读不到状态。",
    ).pack(fill="x")

    # --- 分段选择 ---
    section_title(area, "分段选择 segmented")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    field_label(row, "分类").pack(side="left")
    segmented(
        row,
        ["全部", "账号", "恢复码", "密钥"],
        lambda value: feedback(f"分段选中：{value}"),
        width=300,
    ).pack(side="left")

    row = _row(body, bg)
    field_label(row, "紧凑").pack(side="left")
    segmented(row, ["日", "周", "月"], width=200, height=30).pack(side="left")

    row = tk.Frame(body, bg=bg)
    row.pack(fill="x")
    field_label(row, "空列表").pack(side="left")
    segmented(row, [], width=200).pack(side="left")
    hint_label(body, "values=[] 时不预设选中项；dynamic_resizing=False 宽度恒定。").pack(
        fill="x", pady=(4, 0)
    )

    # --- 开关 ---
    section_title(area, "开关 switch")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    _text(
        row,
        "启用某项设置",
        font=T.FONT_BODY,
        color=color_of(T.COLOR_TEXT),
        bg=bg,
    ).pack(side="left")
    toggle = switch(
        row, lambda: feedback("开关已开启" if toggle.get() else "开关已关闭")
    )
    toggle.pack(side="left", padx=(12, 0))
    hint_label(body, "只留轨道、去掉文字，progress_color 跟随主色。").pack(fill="x")

    row = _row(body, bg)
    _text(
        row,
        "紧凑尺寸",
        font=T.FONT_BODY,
        color=color_of(T.COLOR_TEXT),
        bg=bg,
    ).pack(side="left")
    switch(row, lambda: feedback("紧凑开关已切换"), width=60).pack(
        side="left", padx=(12, 0)
    )

    # --- 下拉框 ---
    section_title(area, "下拉框 DropField")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    row = _row(body, bg)
    field_label(row, "普通").pack(side="left")
    DropField(
        row,
        values_provider=lambda: ["选项 A", "选项 B", "选项 C"],
        command=lambda value: feedback(f"下拉选中：{value}"),
        placeholder="点右侧箭头选择",
    ).pack(side="left", fill="x", expand=True)

    row = _row(body, bg)
    field_label(row, "空候选").pack(side="left")
    DropField(
        row,
        values_provider=lambda: [],
        placeholder="候选项为空，点箭头不会弹",
    ).pack(side="left", fill="x", expand=True)

    row = _row(body, bg)
    field_label(row, "预设值").pack(side="left")
    preset = DropField(
        row,
        values_provider=lambda: ["Alpha", "Beta", "Gamma"],
        placeholder="点右侧箭头选择",
    )
    preset.pack(side="left", fill="x", expand=True)
    preset.set("Alpha")
    preset_value = hint_label(body, "已选：Alpha")
    preset_value.pack(fill="x")
    preset.entry.bind(
        "<KeyRelease>",
        lambda _e: preset_value.configure(text=f"已选：{preset.get() or '（空）'}"),
    )
    hint_label(
        body, "get() / set() 与输入框一致；选中候选后回调 command(value)。"
    ).pack(fill="x")

    # --- 大文本 ---
    section_title(area, "大文本 TextArea")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    note = TextArea(
        body,
        placeholder="写备注、粘贴日志、贴长文本…",
        height=120,
        on_change=lambda text: feedback(f"备注当前 {len(text)} 字"),
    )
    note.pack(fill="x")
    hint_label(
        body, "placeholder 在失焦且为空时显示；on_change 收到最新全文。"
    ).pack(fill="x")

    row = _row(body, bg)
    field_label(row, "只读日志").pack(side="left")
    hint_label(row, "预设内容，不可编辑，可选中复制").pack(side="left", padx=(8, 0))

    log = TextArea(
        body, height=96, readonly=True, show_counter=False, bg_color=T.COLOR_CARD
    )
    log.set(
        "22:00  已连接\n"
        "22:01  同步 12 条记录\n"
        "22:02  完成，用时 1.4s"
    )
    log.pack(fill="x")
    hint_label(
        body, "readonly=True 时内部 state=disabled；set() 仍可写入，set_readonly() 可随时切换。"
    ).pack(fill="x")
    return page


def main() -> int:
    return run_page(build, TITLE, height=860)


if __name__ == "__main__":
    raise SystemExit(main())
