"""输入控件测试：搜索框聚焦态、表单输入、分段选择、开关。"""

from __future__ import annotations

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.inputs import form_entry, segmented, switch, toolbar_entry


def test_toolbar_entry_defaults(root):
    entry = toolbar_entry(root, "输入关键词")
    assert isinstance(entry, ctk.CTkEntry)
    assert entry.cget("placeholder_text") == "输入关键词"
    assert entry.cget("height") == 40
    assert entry.cget("corner_radius") == T.RADIUS_LARGE
    assert entry.cget("border_width") == 1
    assert entry.cget("border_color") == T.COLOR_BORDER
    assert entry.cget("fg_color") == T.COLOR_INPUT


def test_toolbar_entry_accepts_custom_height(root):
    entry = toolbar_entry(root, "搜索", height=32)
    assert entry.cget("height") == 32


def test_toolbar_entry_border_turns_accent_on_focus(root):
    entry = toolbar_entry(root, "搜索")
    entry.pack(fill="x")
    root.update()

    assert entry.cget("border_color") == T.COLOR_BORDER

    # CTkEntry.bind 把回调代理到了内部 Entry 上，事件要对内层发才会命中
    entry._entry.event_generate("<FocusIn>")
    root.update()
    assert entry.cget("border_color") == T.COLOR_ACCENT

    entry._entry.event_generate("<FocusOut>")
    root.update()
    assert entry.cget("border_color") == T.COLOR_BORDER


def test_form_entry_defaults(root):
    entry = form_entry(root, placeholder="普通文本")
    assert isinstance(entry, ctk.CTkEntry)
    assert entry.cget("height") == 38
    assert entry.cget("corner_radius") == T.RADIUS_SMALL
    assert entry.cget("border_width") == 1
    assert entry.cget("fg_color") == T.COLOR_INPUT
    assert entry.cget("placeholder_text") == "普通文本"


def test_form_entry_password_does_not_break(root):
    # CTkEntry 带 placeholder 时会把内部 Entry 的 show 清空，cget("show")
    # 读不到打码状态（见 inputs.form_entry 的 docstring），所以这里只保证
    # 构造成功、占位符还在。
    entry = form_entry(root, password=True, placeholder="密码")
    assert entry.cget("placeholder_text") == "密码"
    entry.insert(0, "secret")
    assert entry.get() == "secret"


def test_form_entry_accepts_show_argument(root):
    entry = form_entry(root, show="*")
    entry.insert(0, "abc")
    assert entry.get() == "abc"


def test_segmented_defaults_and_first_value(root):
    seg = segmented(root, ["日", "周", "月"])
    assert isinstance(seg, ctk.CTkSegmentedButton)
    assert seg.cget("values") == ["日", "周", "月"]
    assert seg.get() == "日"
    assert seg.cget("width") == 300
    assert seg.cget("height") == 34
    assert seg.cget("corner_radius") == T.RADIUS_SMALL
    assert seg.cget("selected_color") == T.COLOR_SEG_SELECTED
    assert seg.cget("unselected_color") == T.COLOR_INPUT


def test_segmented_set_changes_selection(root):
    seg = segmented(root, ["A", "B", "C"])
    seg.set("C")
    assert seg.get() == "C"


def test_segmented_without_values_has_empty_selection(root):
    seg = segmented(root, [])
    assert seg.get() == ""


def test_segmented_command_is_wired(root):
    seen = []
    seg = segmented(root, ["A", "B"], command=seen.append)

    # set() 只改选中项，不触发回调；点击按钮才走 from_button_callback
    seg.set("A")
    assert seen == []

    seg.set("B", from_button_callback=True)
    assert seen == ["B"]


def test_switch_defaults(root):
    widget = switch(root)
    assert isinstance(widget, ctk.CTkSwitch)
    assert widget.cget("text") == ""
    assert widget.cget("width") == 44
    assert widget.cget("progress_color") == T.COLOR_ACCENT
    assert widget.get() == 0


def test_switch_toggle_calls_command(root):
    seen = []
    widget = switch(root, command=lambda: seen.append(widget.get()))
    widget.toggle()
    assert widget.get() == 1
    assert seen == [1]
    widget.toggle()
    assert widget.get() == 0
    assert seen == [1, 0]


def test_switch_accepts_custom_width(root):
    assert switch(root, width=60).cget("width") == 60
