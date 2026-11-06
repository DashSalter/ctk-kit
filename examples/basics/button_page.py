"""按钮页：四个工厂函数 + 两个类，连同尺寸矩阵与禁用态。

与 ``collapse_page.py`` / ``settings_page.py`` 一样，页面拆成「UI 类 + 事件类」：
``ButtonPageUI`` 只建控件，``ButtonPage`` 在构造时自动 ``bind_events()``。
每个卡片底部都带一个「查看实现」折叠面板，展开就是对应代码。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    DangerButton,
    FlatButton,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    PrimaryButton,
    Scrollable,
    SecondaryButton,
    SoftButton,
    TextArea,
    tokens as T,
    CodePanel,
)

#: 代码块字体：等宽，比正文大一点，展开后不用凑近看。
CODE_FONT = ("Consolas", 15)

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


class ButtonPageUI(PageBase):
    """按钮页 UI：只写界面，不绑事件。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "按钮")
        self.header.info.configure(text="4 个工厂函数 + 2 个类")

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "点任意按钮，回显会出现在这里")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        # 每张卡单独构造，切过来先出页头和前两张，其余随后补上
        self.build_cards(
            area,
            [
                self._build_basic,
                self._build_micro,
                self._build_sizes,
                self._build_disabled,
            ],
        )

    def _build_basic(self, area: tk.Misc) -> None:
        """基础按钮：主 / 次要 / 描边 / 危险。"""
        box = Card(area, title="基础按钮")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.primary = PrimaryButton(row, "主按钮")
        self.primary.pack(side="left")

        self.secondary = SecondaryButton(row, "次要按钮")
        self.secondary.pack(side="left", padx=(8, 0))

        self.outline = SecondaryButton(row, "描边按钮", border=True)
        self.outline.pack(side="left", padx=(8, 0))

        self.danger = DangerButton(row, "危险按钮")
        self.danger.pack(side="left", padx=(8, 0))

        HintLabel(
            box,
            "主按钮 38 高；次要/危险按钮 30 高；描边版只是多一圈细边。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            BASIC_CODE,
            "三个工厂函数的签名都在上面；command 不接收参数，要传参就用 lambda 包一层。",
        )

    def _build_micro(self, area: tk.Misc) -> None:
        """微型按钮：宽度按文字实测。"""
        box = Card(area, title="微型按钮（宽度按文字实测）")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.flat = FlatButton(row, "FlatButton")
        self.flat.pack(side="left")

        self.soft = SoftButton(row, "SoftButton")
        self.soft.pack(side="left", padx=(8, 0))

        self.long_flat = FlatButton(row, "更长的文字会自动加宽")
        self.long_flat.pack(side="left", padx=(8, 0))

        HintLabel(
            box,
            "卡片里的「复制 / 详情」就用这两个，不会浪费横向空间。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            MICRO_CODE,
            "两个类不用传宽高，宽度按文字实测；要改配色就传 bg / hover / fg。",
        )

    def _build_sizes(self, area: tk.Misc) -> None:
        """尺寸矩阵：只改宽或只改高。"""
        box = Card(area, title="尺寸矩阵")
        box.pack(fill="x", pady=(12, 0))

        self.size_buttons = []

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        for width, height in ((84, 30), (120, 38), (160, 46)):
            button = PrimaryButton(row, f"{width}×{height}", width=width, height=height)
            button.pack(side="left", padx=(0, 8))
            self.size_buttons.append(button)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        for width in (60, 76, 120):
            button = SecondaryButton(row, f"次要 {width}", width=width)
            button.pack(side="left", padx=(0, 8))
            self.size_buttons.append(button)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 14))
        for height in (26, 30, 38):
            button = DangerButton(row, f"危险 {height} 高", height=height)
            button.pack(side="left", padx=(0, 8))
            self.size_buttons.append(button)

        HintLabel(
            box,
            "width / height 都是像素；省略哪个就用那个函数的默认值。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            SIZE_CODE,
            "width / height 都是像素；省略哪个就用那个函数的默认值。",
        )

    def _build_disabled(self, area: tk.Misc) -> None:
        """禁用态：只改 state，保留原配色。"""
        box = Card(area, title="禁用态")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        for factory, text in (
            (PrimaryButton, "主按钮"),
            (SecondaryButton, "次要按钮"),
            (DangerButton, "危险按钮"),
        ):
            button = factory(row, text)
            button.configure(state="disabled")
            button.pack(side="left", padx=(0, 8))

        HintLabel(
            box,
            "state='disabled' 后仍保持原来的配色，只降低不透明度。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            DISABLED_CODE,
            "禁用只改 state，不用换一套配色；恢复用 state=\"normal\"。",
        )


class ButtonPage(ButtonPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.when_built(self.bind_events)

    def bind_events(self) -> None:
        """必须实现：注册按钮和事件。"""
        self.primary.configure(command=lambda: self._show("点了「主按钮」"))
        self.secondary.configure(command=lambda: self._show("点了「次要按钮」"))
        self.outline.configure(command=lambda: self._show("点了「描边按钮」（border=True）"))
        self.danger.configure(command=lambda: self._show("点了「危险按钮」"))
        self.flat.configure(command=lambda: self._show("点了 FlatButton"))
        self.soft.configure(command=lambda: self._show("点了 SoftButton"))
        self.long_flat.configure(command=lambda: self._show("长文字的宽度是算出来的"))
        for button in self.size_buttons:
            text = button.cget("text")
            button.configure(command=lambda t=text: self._show(f"点了「{t}」"))

    def _show(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
