"""设计令牌的契约测试。

令牌是这套组件的地基：颜色写错一个字符，所有控件都会跟着坏，但界面只是
「颜色不对」，不会抛异常。所以这里把格式和层级关系全部钉死。
"""

from __future__ import annotations

import re

import pytest

from ctk_kit import tokens as T

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def _colors():
    return {
        name: value
        for name, value in vars(T).items()
        if name.startswith("COLOR_")
    }


def _fonts():
    return {
        name: value
        for name, value in vars(T).items()
        if name.startswith("FONT_") and name != "FONT_NAME"
    }


def test_color_tokens_exist():
    assert len(_colors()) >= 20


@pytest.mark.parametrize("name,value", sorted(_colors().items()))
def test_color_token_is_light_dark_pair(name, value):
    assert isinstance(value, (tuple, list)), f"{name} 必须是 (浅色, 深色) 二元组"
    assert len(value) == 2, f"{name} 必须正好两个色值"
    for tone in value:
        assert isinstance(tone, str), f"{name} 的色值必须是字符串"
        assert _HEX.match(tone), f"{name} 的 {tone!r} 不是 #rrggbb"


def test_status_colors_cover_all_levels():
    assert set(T.STATUS_COLORS) == {"info", "success", "warn", "error"}
    assert T.STATUS_COLORS["success"] == T.COLOR_SUCCESS
    assert T.STATUS_COLORS["warn"] == T.COLOR_WARNING
    assert T.STATUS_COLORS["error"] == T.COLOR_ERROR
    assert T.STATUS_COLORS["info"] == T.COLOR_MUTED


def test_font_name_is_set():
    assert isinstance(T.FONT_NAME, str)
    assert T.FONT_NAME.strip()


@pytest.mark.parametrize("name,spec", sorted(_fonts().items()))
def test_font_tokens_are_tuples(name, spec):
    assert isinstance(spec, tuple), f"{name} 应该是 (字体, 字号[, 样式])"
    assert 2 <= len(spec) <= 3
    assert spec[0] == T.FONT_NAME
    assert isinstance(spec[1], int) and spec[1] > 0
    if len(spec) == 3:
        assert spec[2] in {"bold", "italic", "underline", "overstrike"}


def test_font_sizes_are_ordered_from_title_down():
    sizes = [
        T.FONT_TITLE[1],
        T.FONT_CARD_TITLE[1],
        T.FONT_SECTION[1],
        T.FONT_BODY[1],
        T.FONT_SMALL[1],
        T.FONT_TINY[1],
        T.FONT_BADGE[1],
    ]
    assert sizes == sorted(sizes, reverse=True)


def test_radius_tokens_are_ordered():
    assert 0 < T.RADIUS_SMALL < T.RADIUS_MEDIUM < T.RADIUS_LARGE
    assert T.RADIUS_PILL >= 100


def test_spacing_tokens_are_ordered():
    assert 0 < T.SPACE_XS < T.SPACE_SM < T.SPACE_MD < T.SPACE_LG < T.SPACE_XL


def test_scrollbar_width_is_sane():
    assert isinstance(T.SCROLLBAR_WIDTH, int)
    assert 4 <= T.SCROLLBAR_WIDTH <= 24
