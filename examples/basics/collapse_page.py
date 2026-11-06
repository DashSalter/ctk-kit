"""展开页：可折叠面板 ``Collapsible`` 的用法。

展开后的 ``body`` 就是普通容器，按钮、标签、输入框、开关都能直接放进去；
收起时整块从布局里消失，卡片高度跟着缩回去。

与 ``button_page.py`` / ``settings_page.py`` 一样，页面拆成「UI 类 + 事件类」，
每个卡片底部带一个「查看实现」折叠面板。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    Checkbox,
    Collapsible,
    DangerButton,
    FieldLabel,
    FormEntry,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    PrimaryButton,
    Scrollable,
    SecondaryButton,
    Switch,
    TextArea,
    tokens as T,
    CodePanel,
)

#: 代码块字体：等宽，比正文大一点。
CODE_FONT = ("Consolas", 15)

BASIC_CODE = '''from ctk_kit import Collapsible, PrimaryButton

panel = Collapsible(frame, collapsed_text="显示代码", expanded_text="隐藏代码")
panel.pack(fill="x")

# body 是普通容器，按钮 / 标签 / 输入框都能放
PrimaryButton(panel.body, "保存", on_save).pack(padx=10, pady=10)'''

MIXED_CODE = '''from ctk_kit import Checkbox, Collapsible, FormEntry, Switch

panel = Collapsible(card, collapsed_text="显示完整表单", expanded_text="收起表单")
panel.pack(fill="x")

row = Frame(panel.body)
row.pack(fill="x", padx=10, pady=(10, 4))
FieldLabel(row, "项目名称", width=72).pack(side="left")
FormEntry(row, placeholder="输入一个名字").pack(side="left", fill="x", expand=True)

row = Frame(panel.body)
row.pack(fill="x", padx=10, pady=4)
Switch(row).pack(side="left")
Checkbox(row, "记住这次选择").pack(side="left", padx=(16, 0))'''

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

NESTED_CODE = '''box = Card(page, title="塞进已有卡片不影响原排版")
row = Frame(box)
row.pack(fill="x", padx=16, pady=(14, 8))
# 卡片本来的内容
HintLabel(row, "这一行是卡片本来的内容，折叠面板加在它下面。").pack(side="left")
SecondaryButton(row, "原本的按钮").pack(side="right")

panel = Collapsible(box, collapsed_text="展开详情")
panel.pack(fill="x", padx=16)
TextArea(panel.body, height=80, readonly=True).pack(fill="x", padx=10, pady=10)

# 收起后整块从布局里消失，卡片高度跟着缩回去，上面那行位置不变'''

EXPANDED_CODE = '''panel = Collapsible(
    card,
    collapsed_text="显示实现",
    expanded_text="隐藏实现",
    expanded=True,   # 一进来就是展开状态
)
panel.pack(fill="x")'''


class CollapsePageUI(PageBase):
    """展开页 UI：只建控件，事件留给 CollapsePage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "展开")
        self.header.info.configure(text="标题行常驻，body 里可以放任意控件")

        self.feedback = HintLabel(self, "点面板里的控件，回显会出现在这里")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self.build_cards(
            area,
            [
                self._build_buttons,
                self._build_mixed,
                self._build_texts,
                self._build_nested,
                self._build_expanded,
            ],
        )

    def _build_buttons(self, area: tk.Misc) -> None:
        """面板里放按钮组。"""
        box = Card(area, title="面板里放按钮")
        box.pack(fill="x")

        HintLabel(
            box,
            "标题行就是一行文字，点一下展开，再点一下收起；收起时不占高度。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.button_panel = Collapsible(
            box,
            collapsed_text="显示按钮组",
            expanded_text="收起按钮组",
        )
        self.button_panel.pack(fill="x", padx=16)

        row = Frame(self.button_panel.body)
        row.pack(fill="x", padx=10, pady=(10, 6))

        self.p_primary = PrimaryButton(row, "主按钮")
        self.p_primary.pack(side="left")
        self.p_secondary = SecondaryButton(row, "次要按钮")
        self.p_secondary.pack(side="left", padx=(8, 0))
        self.p_outline = SecondaryButton(row, "描边按钮", border=True)
        self.p_outline.pack(side="left", padx=(8, 0))
        self.p_danger = DangerButton(row, "危险按钮")
        self.p_danger.pack(side="left", padx=(8, 0))

        HintLabel(
            self.button_panel.body,
            "body 是普通 CTkFrame，按钮放在里面和放在卡片里没区别。",
        ).pack(fill="x", padx=10, pady=(0, 10))

        CodePanel(
            box,
            BASIC_CODE,
            "panel.body 就是内容容器，按钮、标签、输入框都能直接 pack 进去。",
        )

    def _build_mixed(self, area: tk.Misc) -> None:
        """一个面板里混排表单控件。"""
        box = Card(area, title="标签、输入框、开关也能放")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "一个面板里混排：文字说明、输入框、开关、勾选、按钮。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.mixed = Collapsible(
            box,
            collapsed_text="显示完整表单",
            expanded_text="收起表单",
        )
        self.mixed.pack(fill="x", padx=16)

        row = Frame(self.mixed.body)
        row.pack(fill="x", padx=10, pady=(10, 4))
        FieldLabel(row, "项目名称", width=72).pack(side="left")
        self.name = FormEntry(row, placeholder="输入一个名字")
        self.name.pack(side="left", fill="x", expand=True)

        row = Frame(self.mixed.body)
        row.pack(fill="x", padx=10, pady=4)
        self.switch = Switch(row)
        self.switch.pack(side="left")
        self.checkbox = Checkbox(row, "记住这次选择")
        self.checkbox.pack(side="left", padx=(16, 0))

        row = Frame(self.mixed.body)
        row.pack(fill="x", padx=10, pady=(4, 10))
        self.save = PrimaryButton(row, "保存")
        self.save.pack(side="left")
        self.cancel = SecondaryButton(row, "取消")
        self.cancel.pack(side="left", padx=(8, 0))

        CodePanel(
            box,
            MIXED_CODE,
            "面板里没有特殊规则，按普通容器布局即可。",
        )

    def _build_texts(self, area: tk.Misc) -> None:
        """改收起 / 展开两个状态的文字。"""
        box = Card(area, title="改两个状态的文字")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "collapsed_text 是收起时显示的字，expanded_text 是展开后的字。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.custom = Collapsible(
            box,
            collapsed_text="查看参数说明",
            expanded_text="收起参数说明",
        )
        self.custom.pack(fill="x", padx=16)

        api = TextArea(
            self.custom.body,
            height=300,
            readonly=True,
            show_counter=False,
            bg_color=T.COLOR_INPUT,
        )
        api.textbox.configure(font=CODE_FONT)
        api.textbox._textbox.configure(spacing1=4, spacing2=4, spacing3=4)
        api.set(API_CODE)
        api.pack(fill="x", padx=12, pady=12)

        CodePanel(
            box,
            API_CODE,
            "两种文字在构造时传，也可以用 set_texts() 随时改。",
        )

    def _build_nested(self, area: tk.Misc) -> None:
        """把折叠面板塞进已有卡片。"""
        box = Card(area, title="塞进已有卡片不影响原排版")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        HintLabel(
            row,
            "这一行是卡片本来的内容，折叠面板加在它下面。",
        ).pack(side="left")
        self.orig_button = SecondaryButton(row, "原本的按钮")
        self.orig_button.pack(side="right")

        self.nested = Collapsible(box, collapsed_text="展开详情")
        self.nested.pack(fill="x", padx=16)

        detail = TextArea(
            self.nested.body,
            height=80,
            readonly=True,
            show_counter=False,
            bg_color=T.COLOR_INPUT,
        )
        detail.set(
            "这里放长一点的说明、日志都行；收起后整块从布局里消失，卡片高度跟着缩回去。"
        )
        detail.pack(fill="x", padx=12, pady=(12, 6))
        HintLabel(self.nested.body, "上面的文字和按钮位置没变。").pack(
            fill="x", padx=12, pady=(0, 12)
        )

        CodePanel(
            box,
            NESTED_CODE,
            "折叠面板只是卡片里的一个普通子控件，不会打乱已有内容。",
        )

    def _build_expanded(self, area: tk.Misc) -> None:
        """默认就展开的面板。"""
        box = Card(area, title="默认就展开")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "expanded=True 时一进来就是展开状态。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.opened = Collapsible(
            box,
            collapsed_text="显示实现",
            expanded_text="隐藏实现",
            expanded=True,
        )
        self.opened.pack(fill="x", padx=16)

        code = TextArea(
            self.opened.body,
            height=170,
            readonly=True,
            show_counter=False,
            bg_color=T.COLOR_INPUT,
        )
        code.textbox.configure(font=CODE_FONT)
        code.textbox._textbox.configure(spacing1=4, spacing2=4, spacing3=4)
        code.set(BASIC_CODE)
        code.pack(fill="x", padx=12, pady=12)

        CodePanel(
            box,
            EXPANDED_CODE,
            "expanded 只决定初始状态，之后仍可自由展开 / 收起。",
        )


class CollapsePage(CollapsePageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.when_built(self.bind_events)

    def bind_events(self) -> None:
        """注册面板里的按钮、开关、勾选和折叠回调。"""
        self._bind_toggle(self.button_panel, "按钮组")
        self._bind_toggle(self.mixed, "表单")
        self._bind_toggle(self.custom, "参数说明")
        self._bind_toggle(self.nested, "详情")
        self._bind_toggle(self.opened, "实现")

        self.p_primary.configure(command=lambda: self._show("面板里的主按钮"))
        self.p_secondary.configure(command=lambda: self._show("面板里的次要按钮"))
        self.p_outline.configure(command=lambda: self._show("面板里的描边按钮"))
        self.p_danger.configure(command=lambda: self._show("面板里的危险按钮"))

        self.switch.configure(command=lambda: self._show("面板里的开关被拨动"))
        self.checkbox.configure(command=lambda: self._show("面板里的勾选被切换"))
        self.save.configure(command=lambda: self._show("面板里的保存"))
        self.cancel.configure(command=lambda: self._show("面板里的取消"))
        self.orig_button.configure(command=lambda: self._show("卡片原本的按钮"))

    def _bind_toggle(self, panel: Collapsible, label: str) -> None:
        """折叠面板的标题栏点击：切换后把状态写回回显条。"""
        panel.button.configure(command=lambda: self._toggle(panel, label))

    def _toggle(self, panel: Collapsible, label: str) -> None:
        panel.toggle()
        state = "展开" if panel.expanded else "收起"
        self._show(f"{label}已{state}")

    def _show(self, text: str) -> None:
        self.feedback.configure(text=text)
