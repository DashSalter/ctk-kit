"""列表页：LazyList 的增量渲染、关键词筛选、空态与重建。

与 ``button_page.py`` / ``collapse_page.py`` 一样拆成「UI 类 + 事件类」：
``ListingPageUI`` 只建控件，``ListingPage`` 在构造时自动 ``bind_events()``。
``LazyList`` 负责分批把卡片塞进列表、滚动到底部再加载下一批；
``render_card(parent, item)`` 只负责造一张卡片，摆位交给列表自己做。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    FieldLabel,
    Frame,
    HintLabel,
    LazyList,
    PageBase,
    PageHeader,
    PrimaryButton,
    Scrollable,
    SecondaryButton,
    Segmented,
    TextArea,
    ToolbarEntry,
    tokens as T,
    CodePanel,
)

#: 代码块字体：等宽，比正文大一点，展开后不用凑近看。
CODE_FONT = ("Consolas", 15)

#: 示例数据：真实项目里换成接口返回值即可（结构保持一致）。
SAMPLE_ITEMS = [
    {
        "id": f"item-{index}",
        "title": f"示例条目 {index:02d}",
        "subtitle": "一行摘要，放网址、账号或关键词",
        "tag": ["账号", "恢复码", "密钥"][index % 3],
    }
    for index in range(120)
]

#: 分类选项：第一项是「全部」，其余与 item["tag"] 对齐。
TAG_CHOICES = ["全部", "账号", "恢复码", "密钥"]

#: 列表参数：首屏 8 条，之后每次 6 条；行高固定才能开虚拟滚动。
FIRST_BATCH = 8
LOAD_MORE = 6
ITEM_HEIGHT = 96
ITEM_CARD_HEIGHT = 86
LIST_HEIGHT = 380

FILTER_CODE = '''keyword = search.get().strip()
choice = category.get()

items = [
    item for item in SAMPLE_ITEMS
    if (not keyword or keyword in item["title"])
    and (choice == "全部" or item["tag"] == choice)
]

listing.invalidate()                 # 数据变了，丢掉旧卡片
listing.render(
    items,
    empty_title="没有匹配的条目",
    empty_detail="换个关键词或分类再试一次",
)
header.info.configure(text=f"{len(items)} / {len(SAMPLE_ITEMS)} 条")'''

LIST_CODE = '''from ctk_kit import LazyList

listing = LazyList(
    body,
    render_card,                 # (parent, item) -> 一张卡片控件
    key_of=lambda item: item["id"],
    first_batch=8,               # 首屏 8 条
    load_more=6,                 # 滚到底再补 6 条
    item_height=96,              # 行高固定，开启虚拟滚动
)
listing.pack(fill="both", expand=True)

listing.render(items)            # 只建控件，摆位由列表负责
listing.show_hint("还没有备份", "点「刷新」可以重新加载")
listing.invalidate()             # 下次 render 强制重建'''

ITEM_CODE = '''def render_card(parent, item):
    card = Card(parent, height=86)
    card.pack_propagate(False)   # 行高固定，虚拟滚动才不会叠压

    head = Frame(card)
    head.pack(fill="x", padx=14, pady=(12, 0))
    FieldLabel(head, item["title"], width=140).pack(side="left")
    FieldLabel(head, item["tag"], width=56).pack(side="left", padx=(8, 0))
    HintLabel(card, item["subtitle"]).pack(fill="x", padx=16)
    return card                  # 不要自己 pack：LazyList 会摆'''


class ListingPageUI(PageBase):
    """列表页 UI：只建控件，筛选和按钮事件留给 ListingPage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "列表")
        self.header.info.configure(
            text=f"共 {len(SAMPLE_ITEMS)} 条 · 首屏 {FIRST_BATCH} 条"
        )

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "输入关键词或切换分类，列表会立即重建")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_filter(area)
        self._build_list(area)

    def _build_filter(self, area: tk.Misc) -> None:
        """搜索框 + 分类分段控件。"""
        box = Card(area, title="搜索与筛选")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.search = ToolbarEntry(row, "输入关键词筛选…")
        self.search.pack(side="left", fill="x", expand=True)

        self.search_button = PrimaryButton(row, "搜索", width=84, height=40)
        self.search_button.pack(side="left", padx=(10, 0))

        self.category = Segmented(row, TAG_CHOICES, width=280)
        self.category.pack(side="left", padx=(10, 0))

        HintLabel(
            box,
            "关键词匹配标题、分类匹配 tag，两个条件同时生效；"
            "输入时也会即时筛选。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            FILTER_CODE,
            "筛选就是重新 render 一次：列表按 id 复用卡片，只补新增的。",
        )

    def _build_list(self, area: tk.Misc) -> None:
        """懒加载列表 + 底部操作按钮。"""
        box = Card(area, title="懒加载列表")
        box.pack(fill="x", pady=(12, 0))

        body = Frame(box)
        body.pack(fill="x", padx=16, pady=(14, 8))

        self.listing = LazyList(
            body,
            self._render_item,
            key_of=lambda item: item["id"],
            first_batch=FIRST_BATCH,
            load_more=LOAD_MORE,
            item_height=ITEM_HEIGHT,
            gap=(0, 10),
            padx=(0, 8),
        )
        # 列表自己滚，给一个固定高度，卡片不会被内容撑变形。
        # LazyList 内部用 grid 摆 canvas，所以 pack/grid 两种传播都要关掉，
        # 否则 height 会被 canvas 的请求高度盖住。
        self.listing.configure(height=LIST_HEIGHT)
        self.listing.pack_propagate(False)
        self.listing.grid_propagate(False)
        self.listing.pack(fill="both", expand=True)

        row = Frame(body)
        row.pack(fill="x", pady=(10, 0))

        self.refresh_button = SecondaryButton(row, "刷新", width=72)
        self.refresh_button.pack(side="left")

        self.clear_button = SecondaryButton(row, "清空", width=72)
        self.clear_button.pack(side="left", padx=(8, 0))

        self.hint_button = SecondaryButton(row, "空态提示", width=96)
        self.hint_button.pack(side="left", padx=(8, 0))

        self.rebuild_button = SecondaryButton(row, "重建", width=72)
        self.rebuild_button.pack(side="left", padx=(8, 0))

        FieldLabel(row, "滚到底部自动加载下一批", width=190).pack(
            side="left", padx=(12, 0)
        )

        HintLabel(
            box,
            f"共 {len(SAMPLE_ITEMS)} 条数据，首屏 {FIRST_BATCH} 条，"
            f"每次滚动再补 {LOAD_MORE} 条。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            LIST_CODE,
            "第一次加载不需要 force；数据没变时 render 直接返回，不重建。",
        )
        CodePanel(box, ITEM_CODE, "render_card 只造卡片，摆位由 LazyList 负责。")

        # 首屏：直接渲染全部数据，LazyList 自己只放前 FIRST_BATCH 条
        self.listing.render(SAMPLE_ITEMS)

    def _render_item(self, parent: tk.Misc, item: dict) -> tk.Misc:
        """给 LazyList 用的卡片工厂：只建控件并返回，不要自己 pack。"""
        card = Card(parent, height=ITEM_CARD_HEIGHT)
        card.pack_propagate(False)

        head = Frame(card)
        head.pack(fill="x", padx=14, pady=(12, 0))

        FieldLabel(head, item["title"], width=140).pack(side="left")

        tag = FieldLabel(head, item["tag"], width=56)
        tag.configure(text_color=T.COLOR_ACCENT)
        tag.pack(side="left", padx=(8, 0))

        HintLabel(card, item["subtitle"]).pack(fill="x", padx=16, pady=(2, 12))
        return card


class ListingPage(ListingPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """必须实现：注册按钮和事件。"""
        self.search_button.configure(command=self.apply_filter)
        self.search.on_key_release(lambda _event: self.apply_filter())
        self.category.configure(command=lambda _value: self.apply_filter())

        self.refresh_button.configure(command=self.refresh)
        self.clear_button.configure(command=self.clear_list)
        self.hint_button.configure(command=self.show_empty)
        self.rebuild_button.configure(command=self.rebuild)

    def apply_filter(self, force: bool = False) -> None:
        """按关键词与分类重新筛选，再交给 LazyList 重建。"""
        keyword = self.search.get().strip()
        choice = self.category.get()

        items = [
            item
            for item in SAMPLE_ITEMS
            if (not keyword or keyword in item["title"])
            and (choice == "全部" or item["tag"] == choice)
        ]

        self.header.info.configure(text=f"{len(items)} / {len(SAMPLE_ITEMS)} 条")
        self.listing.invalidate()
        self.listing.render(
            items,
            empty_title="没有匹配的条目",
            empty_detail="换个关键词或分类再试一次",
            force=force,
        )
        self._echo(
            f"{choice} · 关键词「{keyword or '无'}」 · 命中 {len(items)} 条"
        )

    def refresh(self) -> None:
        """刷新：带 force=True，数据没变也重建一次。"""
        self.apply_filter(force=True)
        self._echo(f"已刷新并重建：{self.header.info.cget('text')}")

    def clear_list(self) -> None:
        """清空：给空列表，列表会显示「没有匹配的条目」。"""
        self.listing.invalidate()
        self.listing.render(
            [],
            empty_title="列表已清空",
            empty_detail="点「刷新」可以恢复全部条目",
            force=True,
        )
        self.header.info.configure(text=f"0 / {len(SAMPLE_ITEMS)} 条")
        self._echo("已清空列表；点「刷新」恢复全部")

    def show_empty(self) -> None:
        """空态提示：不经过 render，直接摆一块提示上去。"""
        self.listing.show_hint("还没有备份", "点「刷新」可以重新加载")
        self._echo("空态由 show_hint 直接摆上去，不经过 render")

    def rebuild(self) -> None:
        """重建：先失效签名，再按当前条件重新渲染。"""
        self.rebuild_button.configure(text="重建中…")
        self.after(120, self._rebuild_now)

    def _rebuild_now(self) -> None:
        self.rebuild_button.configure(text="重建")
        self.listing.invalidate()
        self.apply_filter(force=True)
        self._echo("已失效签名并重建，滚动位置回到顶部")

    def _echo(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
