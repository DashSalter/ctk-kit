"""懒加载列表测试：分批、去重、强制重画、空态与滚动加载。"""

from __future__ import annotations

import customtkinter as ctk
import pytest

from ctk_kit.scroll_list import LazyList
from ctk_kit.theme import apply_appearance


def make_card(parent, item):
    frame = ctk.CTkFrame(parent, height=80)
    ctk.CTkLabel(frame, text=str(item["id"])).pack()
    return frame


def make_items(count: int):
    return [{"id": f"item-{i}"} for i in range(count)]


def make_list(root, items, **kwargs):
    options = {"key_of": lambda item: item["id"]}
    options.update(kwargs)
    listing = LazyList(root, make_card, **options)
    listing.pack(fill="both", expand=True)
    listing.render(items)
    return listing


def test_first_batch_is_rendered_immediately(root):
    listing = make_list(root, make_items(30), first_batch=5, load_more=2)
    assert len(listing.cards) == 5
    assert [card.winfo_manager() for card in listing.cards] == ["pack"] * 5


def test_flush_builds_everything(root):
    items = make_items(30)
    listing = make_list(root, items, first_batch=5)
    listing.flush()
    assert len(listing.cards) == len(items)


def test_empty_render_shows_hint(root):
    listing = make_list(root, [])
    assert len(listing.cards) == 1
    texts = [
        child.cget("text")
        for child in listing.cards[0].winfo_children()
        if isinstance(child, ctk.CTkLabel)
    ]
    assert texts == ["这里还没有内容"]


def test_empty_render_accepts_custom_text(root):
    listing = LazyList(root, make_card)
    listing.pack(fill="both", expand=True)
    listing.render([], empty_title="还没有备份", empty_detail="点右上角新建")
    texts = [
        child.cget("text")
        for child in listing.cards[0].winfo_children()
        if isinstance(child, ctk.CTkLabel)
    ]
    assert texts == ["还没有备份", "点右上角新建"]


def test_same_data_is_not_rebuilt(root):
    items = make_items(10)
    listing = make_list(root, items, first_batch=4)
    first_card = listing.cards[0]

    listing.render(items)

    assert listing.cards[0] is first_card


def test_force_rebuilds(root):
    items = make_items(10)
    listing = make_list(root, items, first_batch=4)
    first_card = listing.cards[0]

    listing.render(items, force=True)

    assert listing.cards[0] is not first_card


def test_changed_key_rebuilds(root):
    items = make_items(10)
    listing = LazyList(root, make_card, key_of=lambda item: (item["id"], item.get("v")))
    listing.pack(fill="both", expand=True)
    listing.render(items)
    first_card = listing.cards[0]

    changed = [dict(item, v=2) for item in items]
    listing.render(changed)

    assert listing.cards[0] is not first_card


def test_invalidate_forces_next_render(root):
    items = make_items(10)
    listing = make_list(root, items, first_batch=4)
    first_card = listing.cards[0]

    listing.invalidate()
    listing.render(items)

    assert listing.cards[0] is not first_card


def test_appearance_change_rebuilds(root):
    items = make_items(10)
    listing = make_list(root, items, first_batch=4)
    first_card = listing.cards[0]

    apply_appearance("dark")
    listing.render(items)

    assert listing.cards[0] is not first_card


def test_show_hint_replaces_list(root):
    listing = make_list(root, make_items(10), first_batch=4)
    listing.show_hint("还没有备份", "点右上角新建")

    assert len(listing.cards) == 1
    texts = [
        child.cget("text")
        for child in listing.cards[0].winfo_children()
        if isinstance(child, ctk.CTkLabel)
    ]
    assert texts == ["还没有备份", "点右上角新建"]


def test_show_hint_twice_is_noop(root):
    listing = make_list(root, make_items(10), first_batch=4)
    listing.show_hint("空")
    box = listing.cards[0]

    listing.show_hint("空")

    assert listing.cards[0] is box


def test_cards_returns_copy(root):
    listing = make_list(root, make_items(10), first_batch=3)
    cards = listing.cards
    cards.clear()
    assert len(listing.cards) == 3


def test_defaults(root):
    listing = LazyList(root, make_card)
    assert listing.first_batch == 12
    assert listing.load_more == 8
    assert listing.load_delay_ms == 90
    assert listing.load_threshold == pytest.approx(0.92)


def test_scroll_units_are_safe_on_short_content(root):
    listing = make_list(root, make_items(5), first_batch=3)
    listing.scroll_units(1)
    listing.scroll_units(-1)
    root.update()


def test_render_after_flush_is_noop_for_same_data(root):
    items = make_items(20)
    listing = make_list(root, items, first_batch=4)
    listing.flush()
    assert len(listing.cards) == 20

    # 数据签名没变，render 直接返回，不会把列表缩回首屏
    listing.render(items)
    assert len(listing.cards) == 20


def test_scrolling_to_bottom_loads_more(root, settle):
    items = make_items(120)
    listing = make_list(root, items, first_batch=4, load_more=4)
    assert len(listing.cards) == 4

    listing.canvas.yview_moveto(1.0)
    settle(root, 0.4)

    assert len(listing.cards) > 4
    assert len(listing.cards) <= len(items)


def test_destroy_is_safe(root):
    listing = make_list(root, make_items(10), first_batch=3)
    listing.destroy()
    root.update()
