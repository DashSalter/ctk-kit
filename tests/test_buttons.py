"""按钮组件测试：默认尺寸、配色、命令回调、按文字自适应的微型按钮。"""

from __future__ import annotations

import tkinter.font as tkfont

import customtkinter as ctk
import pytest

from ctk_kit import tokens as T
from ctk_kit.buttons import (
    FlatButton,
    SoftButton,
    _measurer,
    danger_button,
    primary_button,
    soft_button,
)


def test_primary_button_defaults(root):
    btn = primary_button(root, "保存")
    assert isinstance(btn, ctk.CTkButton)
    assert btn.cget("text") == "保存"
    assert btn.cget("width") == 120
    assert btn.cget("height") == 38
    assert btn.cget("corner_radius") == T.RADIUS_SMALL + 1
    assert btn.cget("fg_color") == T.COLOR_ACCENT
    assert btn.cget("hover_color") == T.COLOR_ACCENT_HOVER
    assert btn.cget("text_color") == T.COLOR_ACCENT_TEXT


def test_primary_button_accepts_custom_size(root):
    btn = primary_button(root, "搜索", width=84, height=40, radius=20)
    assert btn.cget("width") == 84
    assert btn.cget("height") == 40
    assert btn.cget("corner_radius") == 20


def test_primary_button_invokes_command(root):
    calls = []
    btn = primary_button(root, "保存", lambda: calls.append("clicked"))
    btn.invoke()
    assert calls == ["clicked"]


def test_soft_button_defaults(root):
    btn = soft_button(root, "取消")
    assert btn.cget("width") == 76
    assert btn.cget("height") == 30
    assert btn.cget("corner_radius") == T.RADIUS_SMALL
    assert btn.cget("fg_color") == T.COLOR_SOFT
    assert btn.cget("hover_color") == T.COLOR_SOFT_HOVER
    assert btn.cget("text_color") == T.COLOR_TEXT
    assert btn.cget("border_width") == 0
    assert btn.cget("border_color") == T.COLOR_SOFT


def test_soft_button_border_variant(root):
    btn = soft_button(root, "取消", border=True)
    assert btn.cget("border_width") == 1
    assert btn.cget("border_color") == T.COLOR_BORDER


def test_soft_button_corner_grows_for_tall_buttons(root):
    short = soft_button(root, "A", height=30)
    tall = soft_button(root, "A", height=38)
    assert short.cget("corner_radius") == T.RADIUS_SMALL
    assert tall.cget("corner_radius") == T.RADIUS_SMALL + 1


def test_danger_button_uses_danger_tokens(root):
    btn = danger_button(root, "清空")
    assert btn.cget("fg_color") == T.COLOR_DANGER_SOFT
    assert btn.cget("hover_color") == T.COLOR_DANGER_SOFT_HOVER
    assert btn.cget("text_color") == T.COLOR_DANGER
    assert btn.cget("width") == 76
    assert btn.cget("height") == 30


def test_commands_receive_no_arguments(root):
    seen = []
    btn = danger_button(root, "删除", lambda: seen.append(True))
    btn.invoke()
    assert seen == [True]


def test_flat_button_width_follows_measured_text(root):
    measure = tkfont.Font(root=root, font=T.FONT_TINY)
    btn = FlatButton(root, "复制")
    assert btn.cget("width") == measure.measure("复制") + 20
    assert btn.cget("height") == measure.metrics("linespace") + 6


def test_flat_button_respects_custom_padding(root):
    measure = tkfont.Font(root=root, font=T.FONT_TINY)
    btn = FlatButton(root, "详情", padx=14, pady=5)
    assert btn.cget("width") == measure.measure("详情") + 28
    assert btn.cget("height") == measure.metrics("linespace") + 10


def test_flat_button_uses_current_tone_colors(root):
    btn = FlatButton(root, "详情")
    assert btn.cget("fg_color") == T.COLOR_SOFT[0]
    assert btn.cget("hover_color") == T.COLOR_SOFT_HOVER[0]
    assert btn.cget("text_color") == T.COLOR_TEXT[0]


def test_flat_button_accepts_overrides(root):
    btn = FlatButton(
        root,
        "详情",
        bg="#101010",
        hover="#202020",
        fg="#303030",
        radius=4,
    )
    assert btn.cget("fg_color") == "#101010"
    assert btn.cget("hover_color") == "#202020"
    assert btn.cget("text_color") == "#303030"
    assert btn.cget("corner_radius") == 4


def test_soft_button_class_is_muted_and_tighter(root):
    measure = tkfont.Font(root=root, font=T.FONT_TINY)
    btn = SoftButton(root, "显示")
    # SoftButton 只把前景参数 fg 传给 FlatButton（映射到 text_color），底色仍是 soft
    assert btn.cget("fg_color") == T.COLOR_SOFT[0]
    assert btn.cget("text_color") == T.COLOR_MUTED[0]
    assert btn.cget("width") == measure.measure("显示") + 16
    assert btn.cget("height") == measure.metrics("linespace") + 4
    assert btn.cget("corner_radius") == T.RADIUS_SMALL - 2


def test_is_ctk_button_subclass():
    assert issubclass(FlatButton, ctk.CTkButton)
    assert issubclass(SoftButton, FlatButton)


def test_measurer_caches_by_font_spec(root):
    first = _measurer(T.FONT_TINY)
    second = _measurer(T.FONT_TINY)
    other = _measurer(T.FONT_BODY)
    assert first is second
    assert other is not first
