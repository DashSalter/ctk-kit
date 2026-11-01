"""选择页：分段、开关、勾选、单选、滑块与进度条。

单独启动：``python -m ctk_kit.showcase.pages.choices``
"""

from __future__ import annotations

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.inputs import (
    checkbox,
    progressbar,
    radio_group,
    segmented,
    slider,
    switch,
)
from ctk_kit.layout import (
    field_label,
    hint_label,
    page_header,
    scrollable,
    section_title,
)
from ctk_kit.theme import color_of

from ..shell import (
    _card_body,
    _card_shell,
    _code_panel,
    _feedback,
    _row,
    _text,
    run_page,
)

TITLE = "选择"

SEGMENTED_CODE = '''from ctk_kit import segmented

segmented(
    row,
    ["全部", "账号", "恢复码", "密钥"],
    command=lambda value: print(value),   # 收选中的文字
    width=300,
    height=34,
    font=FONT_SMALL,
)
# values=[] 时不预设选中项；dynamic_resizing=False 时宽度恒定
# 选中段用 COLOR_ACTIVE，文字自动转白'''

SWITCH_CODE = '''from ctk_kit import switch

toggle = switch(row, command, text="启用", width=44)
# switch(master, command=None, *, text="", width=44)
# text 留空就只显示轨道；command 不接收参数，读状态用 toggle.get()

toggle.select()      # 拨到右边
toggle.deselect()    # 拨回左边
toggle.toggle()

# 圆球色 COLOR_BUTTON_KNOB、悬停色 COLOR_BUTTON_KNOB_HOVER，都在 tokens 里改'''

CHECKBOX_CODE = '''from ctk_kit import checkbox

check = checkbox(row, "记住这台设备", command)
# checkbox(master, text="", command=None, *, width=20, height=20)

check.select()      # 勾上
check.deselect()
check.get()         # 0 / 1

# 选中后填 COLOR_ACTIVE 并打勾；方块圆角是 RADIUS_SMALL - 2'''

RADIO_CODE = '''group, var = radio_group(
    frame,
    ["每次询问", "总是同步", "只在本机保存"],
    command=lambda value: print(value),
    variable=None,   # 传自己的 StringVar 就能从外面读写
    gap=8,           # 选项之间的行距
)
group.pack(fill="x")

var.get()            # 当前选中项的文字
var.set("总是同步")   # 直接改选中项

# 返回 (容器, StringVar)；控件必须共用同一个 variable 才互斥'''

SLIDER_CODE = '''from ctk_kit import slider, progressbar

track = slider(row, on_change, from_=0, to=100, steps=0, width=220)
# command 收 float；steps>0 时只能停在等分点

track.get()
track.set(65)

bar = progressbar(row, value=0.0, width=220, height=6)
# progressbar(master, *, value=0.0, width=220, height=6)
bar.set(0.65)        # 收 0~1

# 滑块把手是 12px 正圆，轨道 = height - 2 * border_width（4px）'''


def build(master) -> ctk.CTkFrame:
    """按钮式的选择控件：分段、开关、勾选、单选、滑块、进度条。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    info.configure(text="分段 / 开关 / 勾选 / 单选 / 滑块 / 进度条")

    feedback = _feedback(page, "点任意选项，回显会出现在这里")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

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

    row = _row(body, bg)
    field_label(row, "空列表").pack(side="left")
    segmented(row, [], width=200).pack(side="left")
    hint_label(
        body, "values=[] 时不预设选中项；dynamic_resizing=False 宽度恒定。"
    ).pack(fill="x", pady=(4, 0))
    _code_panel(body, SEGMENTED_CODE, "command 收到的是选中项的文字。")

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
    toggle.select()
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
    _code_panel(body, SWITCH_CODE, "command 不接收参数，状态用 toggle.get() 读。")

    # --- 勾选 ---
    section_title(area, "勾选框 checkbox")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    row = _row(body, bg)
    check_on = checkbox(
        row, "记住这台设备", lambda: feedback(f"勾选：{bool(check_on.get())}")
    )
    check_on.pack(side="left")
    check_on.select()

    row = _row(body, bg)
    checkbox(row, "启动时自动同步", lambda: feedback("自动同步已切换")).pack(
        side="left"
    )
    hint_label(
        body, "勾选后填主色并打勾；get() 返回 0/1，select() / deselect() 可直接改。"
    ).pack(fill="x")
    _code_panel(body, CHECKBOX_CODE, "和 switch 一样，状态要自己读 get()。")

    # --- 单选 ---
    section_title(area, "单选组 radio_group")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    group, _choice = radio_group(
        body,
        ["每次询问", "总是同步", "只在本机保存"],
        lambda value: feedback(f"单选：{value}"),
    )
    group.pack(fill="x")
    hint_label(
        body, "返回 (容器, StringVar)：同一个 variable 才互斥，读变量拿当前项。"
    ).pack(fill="x")
    _code_panel(body, RADIO_CODE, "传自己的 variable 就能从外部读写选中项。")

    # --- 滑块与进度条 ---
    section_title(area, "滑块 slider / 进度条 progressbar")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    row = _row(body, bg)
    field_label(row, "连续").pack(side="left")

    def on_slide(value: float) -> None:
        bar.set(value / 100.0)
        feedback(f"滑块：{value:.0f}%")

    track = slider(row, on_slide, width=320)
    track.pack(side="left", padx=(8, 12))
    bar = progressbar(row, value=0.0, width=140)
    bar.pack(side="left")

    row = _row(body, bg)
    field_label(row, "分段").pack(side="left")
    slider(row, lambda v: feedback(f"分段档位：{v:.0f}"), steps=4, width=240).pack(
        side="left", padx=(8, 0)
    )

    row = _row(body, bg)
    field_label(row, "细进度条").pack(side="left")
    progressbar(row, value=0.65, width=200, height=6).pack(side="left", padx=(8, 0))
    hint_label(
        body,
        "拖动「连续」的滑块会同步右边进度条；slider 的 command 收 float，"
        "progressbar.set() 收 0~1。",
    ).pack(fill="x")
    _code_panel(body, SLIDER_CODE, "slider 的 get() 读数、set() 赋值，和进度条一起用。")

    return page


def main() -> int:
    return run_page(build, TITLE, height=800)


if __name__ == "__main__":
    raise SystemExit(main())
