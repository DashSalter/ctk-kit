"""Showcase 示例程序测试：八个页面都能构建，交互也能把结果回显出来。

Showcase 同时是「文档」和「冒烟测试」：这里的用例保证每个页面构建时不抛异常，
并且按钮 / 分段 / 下拉这些交互真的接到了页面的反馈条上。
"""

from __future__ import annotations

import importlib.util
import sys
import time
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
import pytest

from ctk_kit import tokens as T
from ctk_kit.dropdown import DropField
from ctk_kit.scroll_list import LazyList
from ctk_kit.theme import color_of


def _load_showcase():
    """按路径加载 examples/showcase.py —— 示例脚本不属于 ctk_kit 包。"""
    path = Path(__file__).resolve().parents[1] / "examples" / "showcase.py"
    spec = importlib.util.spec_from_file_location("ctk_kit_showcase", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_showcase = _load_showcase()
ShowcaseApp = _showcase.ShowcaseApp
build_buttons_page = _showcase.build_buttons_page
build_form_page = _showcase.build_form_page
build_foundation_page = _showcase.build_foundation_page
build_inputs_page = _showcase.build_inputs_page
build_layout_page = _showcase.build_layout_page
build_list_page = _showcase.build_list_page
build_overview_page = _showcase.build_overview_page
build_theme_page = _showcase.build_theme_page


def _walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


def _find(widget, cls, text: str):
    for node in _walk(widget):
        if isinstance(node, cls) and node.cget("text") == text:
            return node
    raise AssertionError(f"没找到文本为 {text!r} 的 {cls.__name__}")


def _texts(widget, cls) -> list[str]:
    return [node.cget("text") for node in _walk(widget) if isinstance(node, cls)]


BUILDERS = [
    ("overview", build_overview_page, {}),
    ("foundation", build_foundation_page, {}),
    ("buttons", build_buttons_page, {}),
    ("inputs", build_inputs_page, {}),
    ("layout", build_layout_page, {}),
    ("list", build_list_page, {}),
    ("theme", build_theme_page, {}),
    ("form", build_form_page, {}),
]


@pytest.fixture()
def showcase_app():
    """真实构造一次 ShowcaseApp；窗口全透明，不闪屏。"""
    last_error = None
    for _ in range(3):
        try:
            app = ShowcaseApp()
            break
        except Exception as exc:  # noqa: BLE001 - Windows 上 Tcl 初始化偶发失败
            last_error = exc
            time.sleep(0.1)
    else:
        pytest.skip(f"当前环境无法创建 Tk 窗口：{last_error}")
    try:
        app.attributes("-alpha", 0.0)
    except Exception:  # noqa: BLE001 - 少数 Tk 构建不支持 alpha
        app.withdraw()
    app.update()
    try:
        yield app
    finally:
        app.destroy()


# --------------------------------------------------------------------------- #
#  页面构建
@pytest.mark.parametrize(
    "name, builder, kwargs",
    BUILDERS,
    ids=[case[0] for case in BUILDERS],
)
def test_every_page_builds(root, name, builder, kwargs):
    page = builder(root, **kwargs)
    try:
        assert isinstance(page, ctk.CTkFrame)
        assert page.winfo_children(), f"{name} 页没有任何子控件"
        assert hasattr(page, "feedback"), f"{name} 页缺少 feedback 回显"
        assert page.feedback.text() != ""
    finally:
        page.destroy()


def test_pages_constant_matches_pages_dict(showcase_app):
    assert showcase_app.PAGES == ("总览", "基件", "按钮", "输入", "布局", "列表", "主题", "表单")
    assert set(showcase_app.PAGES) == set(showcase_app._pages)
    assert len(showcase_app._pages) == len(BUILDERS)


# --------------------------------------------------------------------------- #
#  总览
def test_overview_navigate_buttons(root):
    visited: list[str] = []
    page = build_overview_page(root, navigate=visited.append)
    try:
        _find(page, ctk.CTkButton, "查看").invoke()
        assert visited == ["基件"]
        assert page.feedback.text() == "已跳到「基件」页"
    finally:
        page.destroy()


def test_overview_without_navigate_still_reports(root):
    page = build_overview_page(root)
    try:
        _find(page, ctk.CTkButton, "查看").invoke()
        assert page.feedback.count == 1
        assert "基件" in page.feedback.text()
    finally:
        page.destroy()


# --------------------------------------------------------------------------- #
#  基件
def test_foundation_lists_all_tokens(root):
    page = build_foundation_page(root)
    try:
        texts = _texts(page, ctk.CTkLabel) + _texts(page, tk.Label)
        for name in ("FONT_TITLE", "FONT_BADGE", "RADIUS_SMALL", "SPACE_XL"):
            assert any(name in text for text in texts), f"缺少 {name}"
        # 状态色四个徽章
        for level in ("info", "success", "warn", "error"):
            _find(page, ctk.CTkLabel, level)
    finally:
        page.destroy()


# --------------------------------------------------------------------------- #
#  按钮
def test_buttons_page_covers_all_kinds(root):
    page = build_buttons_page(root)
    try:
        buttons = [node for node in _walk(page) if isinstance(node, ctk.CTkButton)]
        texts = {button.cget("text") for button in buttons}
        for expected in (
            "主按钮",
            "次要按钮",
            "描边按钮",
            "危险按钮",
            "FlatButton",
            "SoftButton",
        ):
            assert expected in texts
        assert any(button.cget("state") == "disabled" for button in buttons)
    finally:
        page.destroy()


def test_buttons_page_invokes_feedback(root):
    page = build_buttons_page(root)
    try:
        _find(page, ctk.CTkButton, "主按钮").invoke()
        assert page.feedback.count == 1
        assert "主按钮" in page.feedback.text()
    finally:
        page.destroy()


# --------------------------------------------------------------------------- #
#  输入
def test_inputs_page_has_every_widget(root):
    page = build_inputs_page(root)
    try:
        entries = [node for node in _walk(page) if isinstance(node, ctk.CTkEntry)]
        assert len(entries) >= 5

        segments = [
            node for node in _walk(page) if isinstance(node, ctk.CTkSegmentedButton)
        ]
        assert len(segments) == 3

        switches = [node for node in _walk(page) if isinstance(node, ctk.CTkSwitch)]
        assert len(switches) == 2

        drops = [node for node in _walk(page) if isinstance(node, DropField)]
        assert len(drops) == 3
        assert drops[2].get() == "Alpha"
    finally:
        page.destroy()


def test_inputs_page_segmented_command(root):
    page = build_inputs_page(root)
    try:
        segment = next(
            node for node in _walk(page) if isinstance(node, ctk.CTkSegmentedButton)
        )
        segment._buttons_dict["账号"].invoke()
        assert "账号" in page.feedback.text()
    finally:
        page.destroy()


def test_inputs_page_switch_toggles_feedback(root):
    page = build_inputs_page(root)
    try:
        toggle = next(node for node in _walk(page) if isinstance(node, ctk.CTkSwitch))
        toggle.toggle()
        assert page.feedback.text() == "开关已开启"
        toggle.toggle()
        assert page.feedback.text() == "开关已关闭"
    finally:
        page.destroy()


# --------------------------------------------------------------------------- #
#  布局
def test_layout_page_has_all_parts(root):
    page = build_layout_page(root)
    try:
        dividers = [
            node
            for node in _walk(page)
            if isinstance(node, ctk.CTkFrame) and node.cget("height") == 1
        ]
        assert dividers

        assert any(
            isinstance(node, ctk.CTkScrollableFrame) for node in _walk(page)
        )
        assert "这里还没有内容" in _texts(page, ctk.CTkLabel)
        assert any(
            isinstance(node, ctk.CTkLabel) and node.cget("width") == 112
            for node in _walk(page)
        )
    finally:
        page.destroy()


# --------------------------------------------------------------------------- #
#  列表
def test_list_page_lazy_rendering(root):
    page = build_list_page(root)
    try:
        listing = next(node for node in _walk(page) if isinstance(node, LazyList))
        assert len(listing.cards) == listing.first_batch == 12

        listing.flush()
        assert len(listing.cards) == 120
    finally:
        page.destroy()


def test_list_page_clear_shows_empty_state(root):
    page = build_list_page(root)
    try:
        listing = next(node for node in _walk(page) if isinstance(node, LazyList))
        _find(page, ctk.CTkButton, "清空").invoke()
        assert len(listing.cards) == 1
        assert any(
            node.cget("text") == "列表已清空"
            for node in _walk(listing.inner)
            if isinstance(node, ctk.CTkLabel)
        )
    finally:
        page.destroy()


def test_list_page_show_hint(root):
    page = build_list_page(root)
    try:
        _find(page, ctk.CTkButton, "空态提示").invoke()
        texts = _texts(page, ctk.CTkLabel)
        assert "还没有备份" in texts
        assert "点「刷新」可以重新加载" in texts
    finally:
        page.destroy()


def test_list_page_refresh_restores_items(root):
    page = build_list_page(root)
    try:
        listing = next(node for node in _walk(page) if isinstance(node, LazyList))
        _find(page, ctk.CTkButton, "清空").invoke()
        _find(page, ctk.CTkButton, "刷新").invoke()
        assert len(listing.cards) == listing.first_batch
        assert "120 条" in _texts(page, ctk.CTkLabel)
    finally:
        page.destroy()


def test_list_page_card_buttons_report(root):
    page = build_list_page(root)
    try:
        listing = next(node for node in _walk(page) if isinstance(node, LazyList))
        card = listing.cards[0]
        _find(card, ctk.CTkButton, "详情").invoke()
        assert "详情" in page.feedback.text()
        assert "示例条目 00" in page.feedback.text()
    finally:
        page.destroy()


# --------------------------------------------------------------------------- #
#  主题
def test_theme_page_repaint_native(root):
    page = build_theme_page(root)
    try:
        target = page.repaint_target
        before = target.cget("bg")
        _find(page, ctk.CTkButton, "成功色").invoke()
        assert target.cget("bg") == color_of(T.COLOR_SUCCESS)
        assert target.cget("bg") != before
        assert "重绘" in page.feedback.text()
    finally:
        page.destroy()


def test_theme_page_toggle_callback(root):
    calls: list[str] = []
    page = build_theme_page(root, on_toggle=lambda: calls.append("toggle"))
    try:
        _find(page, ctk.CTkButton, "切换深浅色").invoke()
        assert calls == ["toggle"]
    finally:
        page.destroy()


def test_theme_page_without_toggle_explains(root):
    page = build_theme_page(root)
    try:
        _find(page, ctk.CTkButton, "切换深浅色").invoke()
        assert "ShowcaseApp" in page.feedback.text()
    finally:
        page.destroy()


# --------------------------------------------------------------------------- #
#  表单
def test_form_page_save_reads_all_fields(root):
    page = build_form_page(root)
    try:
        entries = [node for node in _walk(page) if isinstance(node, ctk.CTkEntry)]
        entries[0].insert(0, "公司邮箱")
        entries[1].insert(0, "me@example.com")
        entries[2].insert(0, "s3cret")

        drops = [node for node in _walk(page) if isinstance(node, DropField)]
        drops[0].set("导入")

        _find(page, ctk.CTkButton, "保存").invoke()
        report = page.feedback.text()
        assert "名称=公司邮箱" in report
        assert "账号=me@example.com" in report
        assert "分类=账号" in report
        assert "来源=导入" in report
        assert "通知=开" in report
    finally:
        page.destroy()


def test_form_page_reset_clears_fields(root):
    page = build_form_page(root)
    try:
        entries = [node for node in _walk(page) if isinstance(node, ctk.CTkEntry)]
        entries[0].insert(0, "临时值")
        _find(page, ctk.CTkButton, "重置").invoke()
        assert all(entry.get() == "" for entry in entries)
        assert page.feedback.text() == "已重置表单"
    finally:
        page.destroy()


# --------------------------------------------------------------------------- #
#  主窗口
def test_showcase_app_starts_on_overview(showcase_app):
    assert showcase_app._current == "总览"
    assert showcase_app._pages["总览"].winfo_manager() == "pack"
    assert showcase_app._pages["表单"].winfo_manager() == ""


def test_showcase_app_switches_page(showcase_app):
    showcase_app.show_page("按钮")
    assert showcase_app._current == "按钮"
    assert showcase_app._pages["按钮"].winfo_manager() == "pack"
    assert showcase_app._pages["总览"].winfo_manager() == ""
    assert showcase_app._buttons["按钮"].cget("fg_color") == T.COLOR_SEG_SELECTED


def test_showcase_app_rejects_unknown_page(showcase_app):
    with pytest.raises(ValueError):
        showcase_app.show_page("不存在的页面")


def test_showcase_app_toggle_appearance_rebuilds(showcase_app):
    old = showcase_app._pages["总览"]
    showcase_app.show_page("列表")
    showcase_app.toggle_appearance()

    assert ctk.get_appearance_mode() == "Dark"
    assert showcase_app._current == "列表"
    assert showcase_app._pages["总览"] is not old
    assert showcase_app._pages["列表"].winfo_manager() == "pack"
    assert showcase_app._sidebar.cget("fg_color") == T.COLOR_SIDE
