"""组件页：徽标、悬浮提示、分页条。

三个都是 0.9.2 新加的小件：``Badge`` / ``Tag`` 用来标状态，``Tooltip``
给任意控件补一行悬停说明，``Pagination`` 配表格或列表翻页。

和别的页面一样拆成「UI 类 + 事件类」：UI 类只建控件，事件类在构造时
``bind_events()``，每个卡片底部带一个「查看实现」折叠代码块。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Badge,
    Card,
    CodePanel,
    FormEntry,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    Pagination,
    PrimaryButton,
    Scrollable,
    SoftButton,
    Tag,
    Tooltip,
)

BADGE_CODE = '''from ctk_kit import Badge, Tag
Badge(card, "已同步", color="success")              # 淡绿底、绿字
Badge(card, "3", color="danger", variant="solid")   # 红底白字计数
Badge(card, dot=True, color="warning")               # 一个状态点
Tag(card, "草稿", variant="outline")                 # 描边标签'''

TOOLTIP_CODE = '''from ctk_kit import Tooltip

Tooltip(save_button, "保存当前草稿")
Tooltip(entry, lambda: f"当前长度 {len(entry.get())}", delay=300)'''

PAGINATION_CODE = '''from ctk_kit import Pagination

pager = Pagination(card, total=238, page_size=20, command=load_page)
pager.pack(fill="x")


def load_page(page):
    table.set_rows(fetch(page))'''

_BADGE_TEXT = ["点我换文字", "已同步", "3", "草稿", "待处理"]


class ExtrasPageUI(PageBase):
    """组件页 UI：徽标、悬浮提示、分页条三张卡片。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "组件")
        self.header.info.configure(text="徽标 / 悬浮提示 / 分页条")

        self.feedback = HintLabel(self, "翻页、点徽标、把鼠标停在按钮上试试")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_badges(area)
        self._build_tooltip(area)
        self._build_pagination(area)

        self._badge_index = 0

    def _build_badges(self, area: tk.Misc) -> None:
        """三种形态、语义色、尺寸和状态点。"""
        box = Card(area, title="徽标与标签")
        box.pack(fill="x")

        HintLabel(
            box,
            "soft 是淡底、solid 是实底、outline 只描边；dot=True 只画圆点。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 6))
        for text, color in (
            ("已同步", "success"),
            ("进行中", "accent"),
            ("待处理", "warning"),
            ("失败", "danger"),
            ("草稿", "neutral"),
        ):
            Badge(row, text, color=color).pack(side="left", padx=(0, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 6))
        for text, color in (
            ("成功", "success"),
            ("主色", "accent"),
            ("警告", "warning"),
            ("危险", "danger"),
            ("中性", "neutral"),
        ):
            Badge(row, text, color=color, variant="solid").pack(
                side="left", padx=(0, 8)
            )

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        Tag(row, "描边标签", variant="outline").pack(side="left", padx=(0, 8))
        Badge(row, "sm", size="sm").pack(side="left", padx=(0, 8))
        for color in ("success", "warning", "danger"):
            Badge(row, dot=True, color=color).pack(side="left", padx=(0, 5))

        self.badge_demo = Badge(box, _BADGE_TEXT[0], color="accent")
        self.badge_demo.pack(anchor="w", padx=16, pady=(0, 12))
        self.badge_demo.configure(cursor="hand2")

        CodePanel(
            box,
            BADGE_CODE,
            "Tag 是 Badge 的别名；set_text() 可以在运行时换文字。",
        )

    def _build_tooltip(self, area: tk.Misc) -> None:
        """按钮和输入框挂悬停提示。"""
        box = Card(area, title="悬浮提示")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "默认停 0.5 秒弹出；文字可以传函数，每次悬停都重新算。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 10))
        self.save_button = PrimaryButton(row, "保存")
        self.save_button.pack(side="left")
        self.delay_button = SoftButton(row, "延迟 300ms")
        self.delay_button.pack(side="left", padx=(8, 0))
        self.tip_entry = FormEntry(row, placeholder="输入几个字，再悬停")
        self.tip_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        CodePanel(
            box,
            TOOLTIP_CODE,
            "提示窗口不抢焦点；贴着屏幕边缘时会自动翻到上方。",
        )

    def _build_pagination(self, area: tk.Misc) -> None:
        """页码条 + 代码改页 / 清空数据的对照。"""
        box = Card(area, title="分页条")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "238 条、每页 20 条，共 12 页；点页码只更新回显，不重新请求。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.pager = Pagination(box, total=238, page_size=20, show_total=True)
        self.pager.pack(fill="x", padx=16, pady=(0, 8))

        self.page_hint = HintLabel(box, "当前第 1 / 12 页")
        self.page_hint.pack(fill="x", padx=16, pady=(0, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 12))
        self.page5 = SoftButton(row, "代码跳到第 5 页")
        self.page5.pack(side="left")
        self.clear_btn = SoftButton(row, "清空数据")
        self.clear_btn.pack(side="left", padx=(8, 0))
        self.restore_btn = SoftButton(row, "恢复 238 条")
        self.restore_btn.pack(side="left", padx=(8, 0))

        CodePanel(
            box,
            PAGINATION_CODE,
            "set_page() / set_total() 不触发 command；用户点按钮才回调。",
        )


class ExtrasPage(ExtrasPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """挂提示、徽标点击和分页按钮。"""
        self.tips = [
            Tooltip(self.save_button, "保存当前草稿"),
            Tooltip(self.delay_button, "延迟 0.3 秒才弹出", delay=300),
            Tooltip(
                self.tip_entry,
                lambda: f"当前输入了 {len(self.tip_entry.get())} 个字符",
                delay=200,
            ),
        ]
        self.badge_demo.bind("<Button-1>", self._cycle_badge)
        self.pager.configure(command=self._on_page)
        self.page5.configure(command=self._jump_five)
        self.clear_btn.configure(command=self._clear)
        self.restore_btn.configure(command=self._restore)

    def _on_page(self, page: int) -> None:
        """用户点页码：更新页数和回显。"""
        self._sync_page_hint()
        self.feedback.configure(text=f"翻到第 {page} 页，这里可以接着请求数据")

    def _cycle_badge(self, _event: tk.Event) -> None:
        """点徽标换一段文字，演示 set_text。"""
        self._badge_index = (self._badge_index + 1) % len(_BADGE_TEXT)
        text = _BADGE_TEXT[self._badge_index]
        self.badge_demo.set_text(text)
        self.feedback.configure(text=f"徽标文字换成「{text}」")

    def _jump_five(self) -> None:
        """代码改页，不触发 command。"""
        self.pager.set_page(5)
        self._sync_page_hint()
        self.feedback.configure(text="set_page(5)：已跳到第 5 页，没有触发 command")

    def _clear(self) -> None:
        """清空数据，只剩第 1 页。"""
        self.pager.set_total(0)
        self._sync_page_hint()
        self.feedback.configure(text="set_total(0)：只剩第 1 页")

    def _restore(self) -> None:
        """恢复 238 条。"""
        self.pager.set_total(238)
        self._sync_page_hint()
        self.feedback.configure(text="set_total(238)：12 页回来了")

    def _sync_page_hint(self) -> None:
        """把页码回显同步到分页条。"""
        self.page_hint.configure(
            text=f"当前第 {self.pager.page} / {self.pager.pages} 页"
        )
