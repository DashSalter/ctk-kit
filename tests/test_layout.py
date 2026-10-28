"""布局组件测试：页头、分区标题、卡片、分隔线、滚动容器、空态。"""

from __future__ import annotations

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.layout import (
    card,
    divider,
    empty_hint,
    field_label,
    hint_label,
    page_header,
    scrollable,
    section_title,
    style_scrollable,
)


def _pack_pady(root, points: int) -> int:
    """CTk 控件 pack 时会把 pady 按窗口缩放换算成像素，断言要跟上。"""
    return round(points * ctk.ScalingTracker.get_window_scaling(root))


def test_page_header_returns_container_and_info(root):
    head, info = page_header(root, "全部记录")
    assert isinstance(head, ctk.CTkFrame)
    assert isinstance(info, ctk.CTkLabel)
    assert info.cget("text") == ""
    assert head.winfo_manager() == "pack"

    labels = [w for w in head.winfo_children() if isinstance(w, ctk.CTkLabel)]
    assert any(label.cget("text") == "全部记录" for label in labels)


def test_page_header_info_is_writable(root):
    _, info = page_header(root, "列表")
    info.configure(text="120 条")
    assert info.cget("text") == "120 条"


def test_section_title_style(root):
    label = section_title(root, "外观")
    assert isinstance(label, ctk.CTkLabel)
    assert label.cget("text") == "外观"
    assert label.cget("anchor") == "w"
    assert label.winfo_manager() == "pack"
    assert label.pack_info()["pady"] == (
        _pack_pady(root, T.SPACE_LG),
        _pack_pady(root, T.SPACE_SM - 2),
    )


def test_card_style_and_auto_pack(root):
    frame = card(root)
    assert isinstance(frame, ctk.CTkFrame)
    assert frame.cget("fg_color") == T.COLOR_CARD
    assert frame.cget("border_width") == 1
    assert frame.cget("border_color") == T.COLOR_BORDER
    assert frame.cget("corner_radius") == T.RADIUS_MEDIUM
    assert frame.winfo_manager() == "pack"


def test_divider_is_one_pixel_border_color(root):
    line = divider(root)
    assert line.cget("height") == 1
    assert line.cget("fg_color") == T.COLOR_BORDER
    assert line.winfo_manager() == "pack"


def test_divider_accepts_custom_pady(root):
    line = divider(root, pady=(16, 12))
    assert line.pack_info()["pady"] == (_pack_pady(root, 16), _pack_pady(root, 12))


def test_scrollable_is_styled_ctk_scrollable_frame(root):
    area = scrollable(root)
    assert isinstance(area, ctk.CTkScrollableFrame)
    bar = area._scrollbar
    assert bar.cget("width") == T.SCROLLBAR_WIDTH
    assert bar.cget("fg_color") == "transparent"
    # CTkScrollbar 的 cget 里这两个参数叫 scrollbar_*，configure 时叫 button_*
    assert bar.cget("scrollbar_color") == T.COLOR_SCROLLBAR
    assert bar.cget("scrollbar_hover_color") == T.COLOR_SCROLLBAR_HOVER


def test_style_scrollable_returns_same_object(root):
    area = ctk.CTkScrollableFrame(root)
    assert style_scrollable(area) is area


def test_style_scrollable_tolerates_plain_frame(root):
    plain = ctk.CTkFrame(root)
    # 没有 _scrollbar 私有属性时不报错，原样返回
    assert style_scrollable(plain) is plain


def test_empty_hint_without_detail_has_one_line(root):
    box = empty_hint(root, "还没有内容")
    assert len(box.winfo_children()) == 1


def test_empty_hint_with_detail_has_two_lines(root):
    box = empty_hint(root, "还没有内容", "点右上角新建")
    children = box.winfo_children()
    assert len(children) == 2
    texts = [child.cget("text") for child in children]
    assert texts == ["还没有内容", "点右上角新建"]


def test_field_label_default_width(root):
    label = field_label(root, "名称")
    assert label.cget("text") == "名称"
    assert label.cget("width") == 112
    assert label.cget("anchor") == "w"


def test_field_label_custom_width(root):
    assert field_label(root, "名称", width=80).cget("width") == 80


def test_hint_label_left_aligned(root):
    label = hint_label(root, "带 * 为必填")
    assert label.cget("anchor") == "w"
    assert label.cget("justify") == "left"
    assert label.cget("text_color") == T.COLOR_MUTED
