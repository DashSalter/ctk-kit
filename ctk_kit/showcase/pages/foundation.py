"""基件页：tokens 全量（字体、状态色、色板、圆角、间距）。

单独启动：``python -m ctk_kit.showcase.pages.foundation``
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.layout import hint_label, page_header, scrollable, section_title
from ctk_kit.theme import color_of, is_dark

from ..data import COLOR_TOKENS, FONT_TOKENS, RADIUS_TOKENS, SPACE_TOKENS
from ..shell import (
    _card_body,
    _card_shell,
    _feedback,
    _row,
    _text,
    _tone,
    run_page,
)

TITLE = "基件"


def build(master) -> ctk.CTkFrame:
    """tokens 里的每一组值都摆出来：字体、状态色、色板、圆角、间距。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    info.configure(text=f"{len(COLOR_TOKENS)} 个色值 · {len(FONT_TOKENS)} 套字体")

    feedback = _feedback(page, "这些值都来自 ctk_kit.tokens")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    # --- 字体阶梯 ---
    section_title(area, "字体阶梯")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    for name, font in FONT_TOKENS:
        row = _row(body, bg)
        _text(
            row,
            name,
            width=18,
            font=T.FONT_TINY,
            color=color_of(T.COLOR_FAINT),
            bg=bg,
            anchor="w",
        ).pack(side="left")
        _text(
            row,
            "示例文字 Sample 0123",
            font=font,
            color=color_of(T.COLOR_TEXT),
            bg=bg,
            anchor="w",
        ).pack(side="left")
    hint_label(
        body, f"FONT_NAME = {T.FONT_NAME!r}；换平台时只改 tokens 里这一行。"
    ).pack(fill="x", pady=(2, 0))

    # --- 状态色 ---
    section_title(area, "状态色 STATUS_COLORS")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = tk.Frame(body, bg=bg)
    row.pack(fill="x", pady=(0, 6))
    for level, color in T.STATUS_COLORS.items():
        ctk.CTkLabel(
            row,
            text=level,
            width=68,
            height=26,
            corner_radius=T.RADIUS_PILL,
            fg_color=color,
            text_color=T.COLOR_ACCENT_TEXT,
            font=T.FONT_TINY,
        ).pack(side="left", padx=(0, 8))
    hint_label(body, "提示条按级别取色：info / success / warn / error。").pack(
        fill="x"
    )

    # --- 色板 ---
    section_title(area, "色板（左浅色 / 右深色）")
    grid = tk.Frame(area, bg=color_of(T.COLOR_BG))
    grid.pack(fill="both", expand=True)
    grid.grid_columnconfigure(0, weight=1, uniform="swatch")
    grid.grid_columnconfigure(1, weight=1, uniform="swatch")
    dark = is_dark()
    for index, name in enumerate(COLOR_TOKENS):
        _swatch(grid, name, getattr(T, name), dark).grid(
            row=index // 2,
            column=index % 2,
            sticky="ew",
            padx=(0, 10) if index % 2 == 0 else (0, 0),
            pady=(0, 10),
        )

    # --- 尺寸 ---
    section_title(area, "圆角、间距与滚动条")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    row = tk.Frame(body, bg=bg)
    row.pack(fill="x", pady=(0, 10))
    _text(
        row, "圆角", width=10, font=T.FONT_SMALL, color=color_of(T.COLOR_MUTED), bg=bg
    ).pack(side="left")
    for name, radius in RADIUS_TOKENS:
        cell = tk.Frame(row, bg=bg)
        cell.pack(side="left", padx=(0, 16))
        ctk.CTkFrame(
            cell,
            width=44,
            height=44,
            corner_radius=min(radius, 22),
            fg_color=T.COLOR_ACCENT,
            border_width=0,
        ).pack()
        _text(
            cell,
            f"{name}\n{radius}",
            font=T.FONT_TINY,
            color=color_of(T.COLOR_MUTED),
            bg=bg,
            justify="left",
        ).pack(pady=(4, 0))

    row = tk.Frame(body, bg=bg)
    row.pack(fill="x", pady=(0, 10))
    _text(
        row, "间距", width=10, font=T.FONT_SMALL, color=color_of(T.COLOR_MUTED), bg=bg
    ).pack(side="left")
    for name, value in SPACE_TOKENS:
        cell = tk.Frame(row, bg=bg)
        cell.pack(side="left", padx=(0, 14))
        tk.Frame(
            cell,
            width=value,
            height=14,
            bg=color_of(T.COLOR_ACCENT),
            highlightthickness=0,
        ).pack()
        _text(
            cell,
            f"{name} = {value}",
            font=T.FONT_TINY,
            color=color_of(T.COLOR_FAINT),
            bg=bg,
        ).pack(pady=(4, 0))

    row = tk.Frame(body, bg=bg)
    row.pack(fill="x")
    _text(
        row,
        f"滚动条宽 {T.SCROLLBAR_WIDTH}px",
        font=T.FONT_SMALL,
        color=color_of(T.COLOR_MUTED),
        bg=bg,
    ).pack(side="left")
    tk.Frame(
        row,
        width=T.SCROLLBAR_WIDTH,
        height=46,
        bg=color_of(T.COLOR_SCROLLBAR),
        highlightthickness=0,
    ).pack(side="left", padx=(10, 0))
    return page


def _swatch(master, name: str, value, dark: bool) -> ctk.CTkFrame:
    box = ctk.CTkFrame(
        master,
        fg_color=T.COLOR_CARD,
        border_width=1,
        border_color=T.COLOR_BORDER,
        corner_radius=T.RADIUS_MEDIUM,
    )
    body = tk.Frame(box, bg=color_of(T.COLOR_CARD))
    body.pack(fill="x", padx=12, pady=10)

    light = _tone(value, False)
    shade = _tone(value, True)

    chips = tk.Frame(body, bg=color_of(T.COLOR_CARD))
    chips.pack(side="right")
    for tone, color in (("浅", light), ("深", shade)):
        cell = tk.Frame(chips, bg=color_of(T.COLOR_CARD))
        cell.pack(side="left", padx=(6, 0))
        tk.Frame(
            cell,
            width=34,
            height=34,
            bg=color,
            highlightthickness=1,
            highlightbackground=color_of(T.COLOR_BORDER),
        ).pack()
        _text(
            cell,
            tone,
            font=T.FONT_TINY,
            color=color_of(T.COLOR_FAINT),
            bg=color_of(T.COLOR_CARD),
        ).pack()

    _text(
        body,
        name,
        font=T.FONT_SMALL,
        color=color_of(T.COLOR_TEXT),
        bg=color_of(T.COLOR_CARD),
        anchor="w",
    ).pack(anchor="w")
    _text(
        body,
        f"浅 {light}    深 {shade}",
        font=T.FONT_TINY,
        color=color_of(T.COLOR_MUTED),
        bg=color_of(T.COLOR_CARD),
        anchor="w",
    ).pack(anchor="w", pady=(2, 0))
    _text(
        body,
        "当前生效：" + (shade if dark else light),
        font=T.FONT_TINY,
        color=color_of(T.COLOR_ACCENT),
        bg=color_of(T.COLOR_CARD),
        anchor="w",
    ).pack(anchor="w", pady=(2, 0))
    return box


def main() -> int:
    return run_page(build, TITLE, height=860)


if __name__ == "__main__":
    raise SystemExit(main())
