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


def test_wheel_scrolls_one_step_of_sixty_pixels(root):
    """一格滚轮只走 60px：yscrollincrement 必须是 1，否则会跳掉小半屏。"""
    listing = make_list(root, make_items(40), first_batch=40)
    root.update()
    canvas = listing.canvas
    assert int(canvas.cget("yscrollincrement")) == 1

    box = canvas.bbox("all")
    content_height = box[3] - box[1]
    first = canvas.yview()[0]
    listing.scroll_units(1)
    root.update()
    moved = (canvas.yview()[0] - first) * content_height
    assert abs(moved - 60) <= 2


def test_reset_returns_to_first_batch(root):
    """reset 把长列表缩回首屏，滚动位置回到顶部。"""
    listing = make_list(root, make_items(30), first_batch=5)
    listing.flush()
    assert len(listing.cards) == 30

    listing.reset()
    root.update()
    assert len(listing.cards) == 5
    assert listing.canvas.yview()[0] == 0


# --------------------------------------------------------------------------- #
#  虚拟滚动（item_height 固定卡高）
def make_fixed_card(parent, item):
    frame = ctk.CTkFrame(parent, height=86)
    frame.pack_propagate(False)
    ctk.CTkLabel(frame, text=str(item["id"])).pack()
    return frame


def make_virtual_list(root, count=120, height=96):
    listing = LazyList(
        root,
        make_fixed_card,
        key_of=lambda item: item["id"],
        item_height=height,
    )
    listing.pack(fill="both", expand=True)
    listing.render(make_items(count))
    root.update()
    return listing


def test_virtual_mode_builds_only_viewport_cards(root):
    """虚拟模式只建视口附近的卡片，内层高度按总条数撑开。"""
    listing = make_virtual_list(root)
    assert len(listing.cards) < 25
    scale = ctk.ScalingTracker.get_widget_scaling(listing)
    assert int(listing.inner.cget("height")) == int(120 * 96 * scale)


def test_virtual_mode_reuses_cards_after_scrolling_back(root, settle):
    """滚到底再滚回顶部：卡片对象不销毁，直接重新布局。"""
    listing = make_virtual_list(root)
    listing.canvas.yview_moveto(1.0)
    settle(root, 0.1)
    bottom = {id(card) for card in listing.cards}

    listing.canvas.yview_moveto(0.0)
    settle(root, 0.1)
    assert len(listing.cards) == len(bottom)
    assert {id(card) for card in listing.cards} <= bottom


def test_virtual_mode_places_only_visible_cards(root, settle):
    """视口外的卡片被 place_forget 收起，但仍留在内存里。"""
    listing = make_virtual_list(root)
    listing.canvas.yview_moveto(1.0)
    settle(root, 0.1)
    placed = [card for card in listing.cards if card.winfo_manager() == "place"]
    assert 0 < len(placed) < len(listing.cards)


def test_virtual_reset_reuses_cards_without_rebuild(root, settle):
    """reset 只回顶，不重建卡片。"""
    listing = make_virtual_list(root)
    listing.canvas.yview_moveto(1.0)
    settle(root, 0.1)
    count = len(listing.cards)
    listing.reset()
    root.update()
    assert len(listing.cards) == count
    assert float(listing.canvas.yview()[0]) == 0.0


def test_virtual_flush_builds_all_but_places_only_viewport(root):
    """flush 建全部卡片，但只把视口附近的放上布局。"""
    listing = make_virtual_list(root)
    listing.flush()
    root.update()
    assert len(listing.cards) == 120
    placed = [card for card in listing.cards if card.winfo_manager() == "place"]
    assert len(placed) < 120


def test_fast_drag_coalesces_virtual_sync(root, settle):
    """拖动滚动条时连续回调合并成一帧一次，不会每个像素都建卡。"""
    listing = make_virtual_list(root)
    for ratio in (0.1, 0.2, 0.35, 0.5, 0.7, 0.9):
        listing.canvas.yview_moveto(ratio)
        root.update_idletasks()  # yscrollcommand 本身是 idle 回调
    # 还没到执行时间：只排队了一个任务，后面几次回调只更新目标位置
    assert listing._sync_job is not None
    settle(root, 0.1)
    assert listing._sync_job is None
    assert listing._pending_view is None

    placed = [card for card in listing.cards if card.winfo_manager() == "place"]
    assert placed
