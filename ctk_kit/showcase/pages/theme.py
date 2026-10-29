"""主题页：深浅色切换、color_of 取色与 repaint_native 现场演示。

单独启动：``python -m ctk_kit.showcase.pages.theme``
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.buttons import soft_button
from ctk_kit.layout import hint_label, page_header, scrollable, section_title
from ctk_kit.theme import color_of, is_dark, repaint_native

from ..shell import _card_body, _card_shell, _feedback, _row, _text, run_page

TITLE = "主题"


def build(master, *, on_toggle=None) -> ctk.CTkFrame:
    """深浅色切换、color_of 取色与 repaint_native 现场演示。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    info.configure(text="当前：" + ctk.get_appearance_mode())

    feedback = _feedback(page, "点下面的按钮切换外观")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    section_title(area, "当前外观")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    for name, value in (
        ("ctk.get_appearance_mode()", ctk.get_appearance_mode()),
        ("is_dark()", str(is_dark())),
        ("color_of(COLOR_BG)", color_of(T.COLOR_BG)),
    ):
        row = _row(body, bg)
        _text(
            row,
            name,
            width=30,
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

    section_title(area, "切换动作")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)

    def toggle() -> None:
        if on_toggle is None:
            feedback("独立页面里没有外层窗口，无法重建；在 ShowcaseApp 里点侧边栏按钮即可")
            return
        on_toggle()

    soft_button(row, "切换深浅色", toggle, width=176).pack(side="left")
    hint_label(
        body,
        "apply_appearance('light' / 'dark')；切换后原生 tk 控件要自己重绘。",
    ).pack(fill="x")

    section_title(area, "color_of：给原生控件取色")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = tk.Frame(body, bg=bg)
    row.pack(fill="x", pady=(0, 6))
    for name, token in (
        ("COLOR_ACCENT", T.COLOR_ACCENT),
        ("COLOR_CARD", T.COLOR_CARD),
        ("COLOR_TEXT", T.COLOR_TEXT),
    ):
        cell = tk.Frame(row, bg=bg)
        cell.pack(side="left", padx=(0, 18))
        tk.Frame(
            cell,
            width=64,
            height=36,
            bg=color_of(token),
            highlightthickness=1,
            highlightbackground=color_of(T.COLOR_BORDER),
        ).pack()
        _text(
            cell,
            f"{name}\n{color_of(token)}",
            font=T.FONT_TINY,
            color=color_of(T.COLOR_MUTED),
            bg=bg,
            justify="left",
        ).pack(pady=(4, 0))
    hint_label(body, "(浅色, 深色) 二元组按当前外观取值；普通字符串原样返回。").pack(
        fill="x"
    )

    section_title(area, "repaint_native：重绘原生控件")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    target = tk.Frame(
        body,
        width=200,
        height=44,
        bg="#3b82f6",
        highlightthickness=0,
    )
    target.pack(anchor="w", pady=(0, 8))
    page.repaint_target = target

    row = _row(body, bg)
    for text, token in (
        ("强调色", T.COLOR_ACCENT),
        ("成功色", T.COLOR_SUCCESS),
        ("危险色", T.COLOR_DANGER),
    ):
        soft_button(
            row,
            text,
            lambda name=text, color=token: (
                repaint_native(target, color_of(color)),
                feedback(f"原生 Frame 已重绘为 {name}（{color_of(color)}）"),
            ),
            width=80,
        ).pack(side="left", padx=(0, 8))
    hint_label(
        body,
        "原生 tk 控件不会跟着 CTk 变主题；改 Tcl 选项绕开 CTk 的重绘路径，控件已销毁时静默忽略。",
    ).pack(fill="x")
    return page


def main() -> int:
    return run_page(build, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
