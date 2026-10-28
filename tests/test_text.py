"""TextArea：占位符、字数统计、只读模式。"""

from __future__ import annotations

import customtkinter as ctk

import ctk_kit
from ctk_kit import TextArea, tokens as T


def _inner(area: TextArea):
    """CTkTextbox 内部的 tk.Text；不同构建里字段名都是 ``_textbox``。"""
    return getattr(area.textbox, "_textbox", area.textbox)


def test_creates_ctk_textbox_with_default_height(root):
    area = TextArea(root)
    assert isinstance(area.textbox, ctk.CTkTextbox)
    assert area.textbox.cget("height") == 200
    assert area.cget("fg_color") == "transparent"


def test_without_placeholder_starts_empty(root):
    area = TextArea(root)
    assert area.get() == ""
    assert area.textbox.get("1.0", "end-1c") == ""
    assert area.counter.cget("text") == "0 字"


def test_placeholder_is_shown_and_cleared_on_focus(root):
    area = TextArea(root, placeholder="写下备注")
    assert area.get() == ""
    assert area.textbox.get("1.0", "end-1c") == "写下备注"
    assert area.textbox.cget("text_color") == T.COLOR_FAINT

    _inner(area).event_generate("<FocusIn>")
    root.update()
    assert area.textbox.get("1.0", "end-1c") == ""
    assert area.get() == ""


def test_placeholder_comes_back_after_focus_out_when_empty(root):
    area = TextArea(root, placeholder="占位")
    _inner(area).event_generate("<FocusIn>")
    root.update()
    _inner(area).event_generate("<FocusOut>")
    root.update()
    assert area.get() == ""
    assert area.textbox.get("1.0", "end-1c") == "占位"


def test_set_and_get_roundtrip(root):
    area = TextArea(root)
    area.set("第一行\n第二行")
    assert area.get() == "第一行\n第二行"
    assert area.textbox.cget("text_color") == T.COLOR_TEXT
    assert area.counter.cget("text") == "7 字 · 2 行"


def test_clear_restores_placeholder(root):
    area = TextArea(root, placeholder="占位")
    area.set("内容")
    area.clear()
    assert area.get() == ""
    assert area.textbox.get("1.0", "end-1c") == "占位"


def test_clear_without_placeholder_leaves_empty(root):
    area = TextArea(root)
    area.set("内容")
    area.clear()
    assert area.get() == ""
    assert area.textbox.get("1.0", "end-1c") == ""


def test_on_change_receives_latest_text(root):
    seen = []
    area = TextArea(root, on_change=seen.append)
    assert seen == []  # 构造时不回调
    area.set("abc")
    assert seen == ["abc"]
    area.clear()
    assert seen[-1] == ""


def test_readonly_disables_editing_but_set_still_works(root):
    area = TextArea(root, readonly=True)
    assert area.readonly is True
    assert _inner(area).cget("state") == "disabled"

    area.set("只读内容")
    assert area.get() == "只读内容"
    assert _inner(area).cget("state") == "disabled"

    area.set_readonly(False)
    assert area.readonly is False
    assert _inner(area).cget("state") == "normal"


def test_readonly_keeps_placeholder_on_focus(root):
    area = TextArea(root, placeholder="只读占位", readonly=True)
    _inner(area).event_generate("<FocusIn>")
    root.update()
    assert area.textbox.get("1.0", "end-1c") == "只读占位"
    assert area.get() == ""


def test_counter_can_be_hidden(root):
    area = TextArea(root, show_counter=False)
    assert isinstance(area.counter, ctk.CTkLabel)
    assert area.counter.winfo_manager() == ""


def test_textbox_colors_use_tokens(root):
    area = TextArea(root)
    assert area.textbox.cget("fg_color") == T.COLOR_INPUT
    assert area.textbox.cget("border_color") == T.COLOR_BORDER


def test_bg_color_and_text_color_can_be_overridden(root):
    """日志场景：底色跟卡片走，不再比周围亮一截。"""
    area = TextArea(root, bg_color=T.COLOR_CARD, text_color=T.COLOR_MUTED)
    assert area.textbox.cget("fg_color") == T.COLOR_CARD
    assert area.textbox.cget("text_color") == T.COLOR_MUTED

    area.set("日志")
    assert area.textbox.cget("text_color") == T.COLOR_MUTED


def test_is_exported():
    assert ctk_kit.TextArea is TextArea
    assert "TextArea" in ctk_kit.__all__
