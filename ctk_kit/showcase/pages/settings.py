"""设置页：外观模式切换（浅色 / 深色）、版本与运行环境。

单独启动：``python -m ctk_kit.showcase.pages.settings``
"""

from __future__ import annotations

import sys

import customtkinter as ctk

from ctk_kit import __version__
from ctk_kit import tokens as T
from ctk_kit.inputs import segmented
from ctk_kit.layout import field_label, hint_label, page_header, scrollable, section_title
from ctk_kit.theme import color_of, is_dark

from ..shell import _card_body, _card_shell, _feedback, _row, _text, run_page

TITLE = "设置"


def build(master, *, on_theme=None) -> ctk.CTkFrame:
    """外观模式切换：浅色 / 深色；切换后当前页立刻重建，其余页切过去时再建。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    feedback = _feedback(page, "切换外观模式只重建当前页，其余页切过去时再建")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    section_title(area, "外观模式")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    field_label(row, "主题", width=64).pack(side="left")

    def choose(value: str) -> None:
        if on_theme is None:
            feedback("独立页面里没有外层窗口，无法重建；从 ShowcaseApp 进入设置页即可")
            return
        on_theme("light" if value == "浅色" else "dark")

    theme = segmented(row, ["浅色", "深色"], command=choose, width=200)
    theme.pack(side="left")

    def refresh_theme() -> None:
        """切换外观后由外层窗口回调：刷新「当前：X」和分段选中项。"""
        info.configure(text=f"当前：{ctk.get_appearance_mode()}")
        theme.set("深色" if is_dark() else "浅色")

    refresh_theme()
    page.refresh_theme = refresh_theme

    hint_label(
        body,
        "apply_appearance('light' / 'dark')；切换后当前页立刻按新配色重建。",
    ).pack(fill="x", pady=(6, 0))

    section_title(area, "关于")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    for name, value in (
        ("版本", __version__),
        ("Python", sys.version.split()[0]),
        ("customtkinter", getattr(ctk, "__version__", "未知")),
        ("仓库", "gitee.com/kuangjianke/ctk-kit"),
    ):
        row = _row(body, bg)
        _text(
            row,
            name,
            width=14,
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_MUTED),
            bg=bg,
            anchor="w",
        ).pack(side="left")
        _text(
            row,
            value,
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_TEXT),
            bg=bg,
            anchor="w",
        ).pack(side="left")
    hint_label(body, "主题切换只影响外观；数据与筛选状态不受影响。").pack(fill="x")
    return page


def main() -> int:
    return run_page(build, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
