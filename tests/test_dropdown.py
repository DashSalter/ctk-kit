"""下拉输入框测试：读写、候选面板开合、选中回调、销毁清理。"""

from __future__ import annotations

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.dropdown import _ARROW_CLOSED, _ARROW_OPEN, DropField


def _make_drop(root, values=("选项 A", "选项 B", "选项 C"), command=None):
    source = list(values)
    drop = DropField(
        root,
        values_provider=lambda: list(source),
        command=command,
        placeholder="请选择",
    )
    drop.pack(fill="x")
    return drop


def _popup_buttons(drop):
    body = drop._popup.winfo_children()[0]
    return [w for w in body.winfo_children() if isinstance(w, ctk.CTkButton)]


def test_defaults(root):
    drop = _make_drop(root)
    assert isinstance(drop, ctk.CTkFrame)
    assert drop.cget("height") == 36
    assert drop.cget("border_width") == 1
    assert drop.cget("border_color") == T.COLOR_BORDER
    assert drop.cget("fg_color") == T.COLOR_INPUT
    assert drop.entry.cget("placeholder_text") == "请选择"
    assert drop.arrow.cget("text") == _ARROW_CLOSED
    assert drop.arrow.cget("cursor") == "hand2"


def test_get_and_set(root):
    drop = _make_drop(root)
    assert drop.get() == ""
    drop.set("手填的值")
    assert drop.get() == "手填的值"
    drop.set("")
    assert drop.get() == ""


def test_open_menu_shows_candidates(root):
    drop = _make_drop(root)
    drop.open_menu()
    root.update()

    assert drop._popup is not None
    assert drop._popup.winfo_exists()
    assert drop.arrow.cget("text") == _ARROW_OPEN
    texts = [btn.cget("text") for btn in _popup_buttons(drop)]
    assert texts == ["选项 A", "选项 B", "选项 C"]

    drop._close_menu()
    root.update()
    assert drop._popup is None
    assert drop.arrow.cget("text") == _ARROW_CLOSED


def test_second_open_toggles_closed(root):
    drop = _make_drop(root)
    drop.open_menu()
    root.update()
    assert drop._popup is not None

    drop.open_menu()
    root.update()
    assert drop._popup is None
    assert drop.arrow.cget("text") == _ARROW_CLOSED


def test_empty_provider_does_not_open(root):
    drop = _make_drop(root, values=())
    drop.open_menu()
    root.update()
    assert drop._popup is None
    assert drop.arrow.cget("text") == _ARROW_CLOSED


def test_picking_candidate_sets_value_and_calls_command(root):
    seen = []
    drop = _make_drop(root, command=seen.append)
    drop.open_menu()
    root.update()

    buttons = _popup_buttons(drop)
    buttons[1].invoke()
    root.update()

    assert drop.get() == "选项 B"
    assert seen == ["选项 B"]
    assert drop._popup is None
    assert drop.arrow.cget("text") == _ARROW_CLOSED


def test_destroy_closes_popup(root):
    drop = _make_drop(root)
    drop.open_menu()
    root.update()
    assert drop._popup is not None

    drop.destroy()
    root.update()
    assert drop._popup is None


def test_values_are_read_on_each_open(root):
    current = ["A"]
    drop = DropField(root, values_provider=lambda: list(current))
    drop.pack(fill="x")

    drop.open_menu()
    root.update()
    assert [b.cget("text") for b in _popup_buttons(drop)] == ["A"]
    drop._close_menu()

    current.append("B")
    drop.open_menu()
    root.update()
    assert [b.cget("text") for b in _popup_buttons(drop)] == ["A", "B"]
    drop._close_menu()


def test_arrow_hover_changes_colors(root):
    drop = _make_drop(root)
    drop._set_hover(True)
    root.update()
    assert drop.arrow.cget("text_color") == T.COLOR_TEXT
    assert drop.arrow.cget("fg_color") == T.COLOR_HOVER_FAINT

    drop._set_hover(False)
    root.update()
    assert drop.arrow.cget("text_color") == T.COLOR_MUTED
    assert drop.arrow.cget("fg_color") == "transparent"


def test_popup_body_is_rounded_and_inset(root):
    """面板主体要自带圆角并内缩，窗口裁剪线才不会切掉四角的边框。"""
    drop = _make_drop(root)
    drop.open_menu()
    root.update()
    body = drop._popup.winfo_children()[0]
    assert body.cget("corner_radius") == T.RADIUS_MEDIUM - 1
    info = body.pack_info()
    assert int(info["padx"]) > 0
    assert int(info["pady"]) > 0
    drop._close_menu()
