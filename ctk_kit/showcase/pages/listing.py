"""列表页：LazyList 的完整用法——分批加载、筛选、刷新、清空、空态提示。

单独启动：``python -m ctk_kit.showcase.pages.listing``
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.buttons import SoftButton, danger_button, primary_button, soft_button
from ctk_kit.inputs import segmented, toolbar_entry
from ctk_kit.layout import divider, hint_label, page_header
from ctk_kit.scroll_list import LazyList
from ctk_kit.theme import color_of

from ..data import SAMPLE_ITEMS
from ..shell import Feedback, _text, run_page

TITLE = "列表"


def build(master) -> ctk.CTkFrame:
    """LazyList 的完整用法：分批加载、筛选、刷新、清空、空态提示。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    info.configure(text=f"{len(SAMPLE_ITEMS)} 条")

    area = ctk.CTkFrame(page, fg_color="transparent")
    area.pack(fill="both", expand=True, pady=(14, 0))

    toolbar = ctk.CTkFrame(area, fg_color="transparent")
    toolbar.pack(fill="x", pady=(0, 12))
    search = toolbar_entry(toolbar, "输入关键词筛选…")
    search.pack(side="left", fill="x", expand=True)
    primary_button(toolbar, "搜索", lambda: apply_filter(), width=84, height=40).pack(
        side="left", padx=(10, 0)
    )
    category = segmented(
        toolbar,
        ["全部", "账号", "恢复码", "密钥"],
        lambda _value: apply_filter(),
        width=300,
    )
    category.pack(side="left", padx=(10, 0))

    listing = LazyList(
        area,
        lambda parent, item: _sample_card(parent, item, feedback),
        key_of=lambda item: item["id"],
        item_height=96,
    )
    listing.pack(fill="both", expand=True)
    page.listing = listing

    divider(area, pady=(12, 10))
    footer = ctk.CTkFrame(area, fg_color="transparent")
    footer.pack(fill="x")
    # feedback 要先于 listing.render 定义：render_card 闭包会在首屏渲染时用到它
    feedback = Feedback(hint_label(footer, "滚到底部会自动补下一批"))
    feedback.label.pack(side="right")
    page.feedback = feedback

    def apply_filter(*, force: bool = False) -> None:
        keyword = search.get().strip()
        choice = category.get()
        items = [
            item
            for item in SAMPLE_ITEMS
            if (not keyword or keyword in item["title"])
            and (choice == "全部" or item["tag"] == choice)
        ]
        listing.invalidate()
        listing.render(
            items,
            empty_title="没有匹配的条目",
            empty_detail="换个关键词或分类再试一次",
            force=force,
        )
        info.configure(text=f"{len(items)} 条")
        feedback(f"筛选完成：{len(items)} 条")

    def clear() -> None:
        listing.render([], empty_title="列表已清空", empty_detail="点「刷新」恢复全部")
        info.configure(text="0 条")
        feedback("已清空列表")

    soft_button(footer, "刷新", lambda: apply_filter(force=True), width=72).pack(
        side="left"
    )
    danger_button(footer, "清空", clear, width=72).pack(side="left", padx=(8, 0))
    soft_button(
        footer,
        "空态提示",
        lambda: (
            listing.show_hint("还没有备份", "点「刷新」可以重新加载"),
            feedback("已切到空态提示"),
        ),
        width=88,
    ).pack(side="left", padx=(8, 0))
    soft_button(
        footer,
        "重建",
        lambda: (listing.invalidate(), apply_filter(), feedback("已 invalidate 并重建")),
        width=72,
    ).pack(side="left", padx=(8, 0))

    search.bind("<KeyRelease>", lambda _e: apply_filter())
    listing.render(SAMPLE_ITEMS)
    return page


def _sample_card(parent, item, feedback: Feedback = None) -> ctk.CTkFrame:
    # 固定高度：LazyList 虚拟滚动靠 item_height 定位，卡片自己不能随内容变高
    box = ctk.CTkFrame(
        parent,
        fg_color=T.COLOR_CARD,
        border_width=1,
        border_color=T.COLOR_BORDER,
        corner_radius=T.RADIUS_LARGE,
        height=86,
    )
    box.pack_propagate(False)
    bg = color_of(T.COLOR_CARD)

    def report(text: str) -> None:
        if feedback is not None:
            feedback(text)

    head = tk.Frame(box, bg=bg)
    head.pack(fill="x", padx=16, pady=(12, 2))
    _text(
        head,
        item["title"],
        font=T.FONT_CARD_TITLE,
        color=color_of(T.COLOR_TEXT),
        bg=bg,
        anchor="w",
    ).pack(side="left")
    _text(
        head,
        f" {item['tag']} ",
        font=T.FONT_BADGE,
        color=color_of(T.COLOR_ACCENT),
        bg=color_of(T.COLOR_SOFT),
        padx=4,
        pady=1,
    ).pack(side="left", padx=(8, 0))

    SoftButton(head, "详情", lambda: report(f"详情：{item['title']}")).pack(side="right")
    SoftButton(head, "复制", lambda: report(f"复制：{item['title']}")).pack(
        side="right", padx=(0, 6)
    )

    _text(
        box,
        item["subtitle"],
        font=T.FONT_SMALL,
        color=color_of(T.COLOR_MUTED),
        bg=bg,
        anchor="w",
    ).pack(fill="x", padx=16, pady=(0, 12))
    return box


def main() -> int:
    return run_page(build, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
