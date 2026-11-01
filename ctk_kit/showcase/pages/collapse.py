"""展开页：可折叠面板 Collapsible 的用法。

展开后的 ``body`` 就是普通容器，按钮、标签、输入框、开关都能直接放进去。

单独启动：``python -m ctk_kit.showcase.pages.collapse``
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.buttons import DangerButton, PrimaryButton, SecondaryButton
from ctk_kit.collapse import Collapsible
from ctk_kit.inputs import Checkbox, FormEntry, Switch
from ctk_kit.layout import HintLabel, PageHeader, Scrollable, SectionTitle
from ctk_kit.text import TextArea
from ctk_kit.theme import color_of

from ..shell import CODE_FONT, _card_body, _card_shell, _feedback, _row, _text, run_page

TITLE = "展开"

BASIC_CODE = '''from ctk_kit import Collapsible

panel = Collapsible(frame, collapsed_text="显示代码", expanded_text="隐藏代码")
panel.pack(fill="x")

# body 是普通容器，按钮 / 标签 / 输入框都能放
PrimaryButton(panel.body, "保存", on_save).pack(padx=10, pady=10)'''

API_CODE = '''Collapsible(
    master,
    *,
    collapsed_text="显示代码",   # 收起时标题栏的文字
    expanded_text="隐藏代码",    # 展开时标题栏的文字
    expanded=False,              # 初始是否展开
    button_height=36,            # 标题栏高度
    on_toggle=None,              # 状态变化回调，收 bool
)

panel.body          # 内容容器，往里 pack 控件
panel.button        # 标题栏那个 CTkButton，可以改字号 / 颜色
panel.expanded      # 当前是否展开
panel.expand()      # 展开
panel.collapse()    # 收起
panel.toggle()      # 切换
panel.set_expanded(True)
panel.set_texts(collapsed_text="查看更多", expanded_text="收起")'''


def build(master) -> ctk.CTkFrame:
    """折叠面板里能放什么：按钮、标签、输入框、开关都行。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = PageHeader(page, TITLE)
    info.configure(text="标题行常驻，body 里可以放任意控件")

    feedback = _feedback(page, "点面板里的控件，回显会出现在这里")

    area = Scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)
    soft = color_of(T.COLOR_SOFT)

    # --- 按钮 ---
    SectionTitle(area, "面板里放按钮")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    HintLabel(
        body, "标题行就是一行文字，点一下展开，再点一下收起；收起时不占高度。"
    ).pack(fill="x")

    button_panel = Collapsible(
        body,
        collapsed_text="显示按钮组",
        expanded_text="收起按钮组",
        on_toggle=lambda expanded: feedback(
            "按钮组已展开" if expanded else "按钮组已收起"
        ),
    )
    button_panel.pack(fill="x", pady=(10, 0))

    row = tk.Frame(button_panel.body, bg=soft)
    row.pack(fill="x", padx=10, pady=(10, 6))
    PrimaryButton(row, "主按钮", lambda: feedback("面板里的主按钮")).pack(side="left")
    SecondaryButton(row, "次要按钮", lambda: feedback("面板里的次要按钮")).pack(
        side="left", padx=(8, 0)
    )
    SecondaryButton(
        row, "描边按钮", lambda: feedback("面板里的描边按钮"), border=True
    ).pack(side="left", padx=(8, 0))
    DangerButton(row, "危险按钮", lambda: feedback("面板里的危险按钮")).pack(
        side="left", padx=(8, 0)
    )

    row = tk.Frame(button_panel.body, bg=soft)
    row.pack(fill="x", padx=10, pady=(0, 10))
    HintLabel(row, "body 是普通 CTkFrame，按钮放在里面和放在卡片里没区别。").pack(
        side="left"
    )

    # --- 标签与其它控件 ---
    SectionTitle(area, "标签、输入框、开关也能放")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    HintLabel(body, "一个面板里混排：文字说明、输入框、开关、勾选、按钮。").pack(
        fill="x"
    )

    mixed = Collapsible(
        body,
        collapsed_text="显示完整表单",
        expanded_text="收起表单",
        on_toggle=lambda expanded: feedback("表单已展开" if expanded else "表单已收起"),
    )
    mixed.pack(fill="x", pady=(10, 0))

    row = tk.Frame(mixed.body, bg=soft)
    row.pack(fill="x", padx=10, pady=(10, 4))
    _text(
        row,
        "项目名称",
        font=T.FONT_SMALL,
        color=color_of(T.COLOR_MUTED),
        bg=soft,
        width=9,
    ).pack(side="left")
    FormEntry(row, placeholder="输入一个名字").pack(
        side="left", fill="x", expand=True
    )

    row = tk.Frame(mixed.body, bg=soft)
    row.pack(fill="x", padx=10, pady=4)
    _text(
        row,
        "选项",
        font=T.FONT_SMALL,
        color=color_of(T.COLOR_MUTED),
        bg=soft,
        width=9,
    ).pack(side="left")
    Switch(row, lambda: feedback("面板里的开关被拨动")).pack(side="left")
    Checkbox(row, "记住这次选择", lambda: feedback("面板里的勾选被切换")).pack(
        side="left", padx=(16, 0)
    )

    row = tk.Frame(mixed.body, bg=soft)
    row.pack(fill="x", padx=10, pady=(4, 10))
    PrimaryButton(row, "保存", lambda: feedback("面板里的保存")).pack(side="left")
    SecondaryButton(row, "取消", lambda: feedback("面板里的取消")).pack(
        side="left", padx=(8, 0)
    )

    # --- 自定义文字 ---
    SectionTitle(area, "改两个状态的文字")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    HintLabel(
        body, "collapsed_text 是收起时显示的字，expanded_text 是展开后的字。"
    ).pack(fill="x")

    custom = Collapsible(
        body,
        collapsed_text="查看参数说明",
        expanded_text="收起参数说明",
    )
    custom.pack(fill="x", pady=(10, 0))
    api = TextArea(
        custom.body,
        height=320,
        readonly=True,
        show_counter=False,
        bg_color=T.COLOR_CARD,
    )
    api.textbox.configure(font=CODE_FONT)
    api.set(API_CODE)
    api.pack(fill="x", padx=10, pady=(10, 10))

    # --- 塞进已有卡片 ---
    SectionTitle(area, "塞进已有卡片不影响原排版")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    row = _row(body, bg)
    _text(
        row,
        "这一行是卡片本来的内容，折叠面板加在它下面。",
        font=T.FONT_SMALL,
        color=color_of(T.COLOR_MUTED),
        bg=bg,
    ).pack(side="left")
    SecondaryButton(row, "原本的按钮", lambda: feedback("卡片原本的按钮")).pack(
        side="right"
    )

    nested = Collapsible(body, collapsed_text="展开详情")
    nested.pack(fill="x", pady=(10, 0))
    detail = TextArea(
        nested.body,
        height=80,
        readonly=True,
        show_counter=False,
        bg_color=T.COLOR_CARD,
    )
    detail.set("这里放长一点的说明、日志都行；收起后整块从布局里消失，卡片高度跟着缩回去。")
    detail.pack(fill="x", padx=10, pady=(10, 4))
    HintLabel(nested.body, "上面的文字和按钮位置没变。").pack(
        fill="x", padx=10, pady=(0, 10)
    )

    # --- 初始展开 ---
    SectionTitle(area, "默认就展开")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    HintLabel(body, "expanded=True 时一进来就是展开状态。").pack(fill="x")

    opened = Collapsible(body, collapsed_text="显示实现", expanded_text="隐藏实现", expanded=True)
    opened.pack(fill="x", pady=(10, 0))
    code = TextArea(
        opened.body,
        height=190,
        readonly=True,
        show_counter=False,
        bg_color=T.COLOR_CARD,
    )
    code.textbox.configure(font=CODE_FONT)
    code.set(BASIC_CODE)
    code.pack(fill="x", padx=10, pady=(10, 10))

    return page


def main() -> int:
    return run_page(build, TITLE, height=860)


if __name__ == "__main__":
    raise SystemExit(main())
