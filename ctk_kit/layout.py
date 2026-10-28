"""页面骨架：页头、分区卡片、分隔线、滚动容器、空状态。

一套页面按这个顺序搭出来，视觉就不会散：

    page_header  →  section(title)  →  card 里的若干行  →  divider  →  footer
"""

from __future__ import annotations

import customtkinter as ctk

from . import tokens as T


def page_header(master, title: str) -> tuple[ctk.CTkFrame, ctk.CTkLabel]:
    """页面顶部：左边标题，右边统计信息。

    返回 ``(容器, 信息标签)``，调用方拿到信息标签后自己 ``configure(text=...)``。
    """
    head = ctk.CTkFrame(master, fg_color="transparent")
    head.pack(fill="x")
    ctk.CTkLabel(head, text=title, font=T.FONT_TITLE, text_color=T.COLOR_TEXT).pack(
        side="left"
    )
    info = ctk.CTkLabel(
        head, text="", font=T.FONT_TINY, text_color=T.COLOR_MUTED, anchor="e"
    )
    info.pack(side="right", pady=(9, 0))
    return head, info


def section_title(master, text: str) -> ctk.CTkLabel:
    """分区标题（设置页的「外观」「备份」这一层）。"""
    label = ctk.CTkLabel(
        master, text=text, font=T.FONT_SECTION, text_color=T.COLOR_TEXT, anchor="w"
    )
    label.pack(fill="x", pady=(T.SPACE_LG, T.SPACE_SM - 2))
    return label


def card(master) -> ctk.CTkFrame:
    """圆角卡片容器：内容都往这里放。"""
    frame = ctk.CTkFrame(
        master,
        fg_color=T.COLOR_CARD,
        border_width=1,
        border_color=T.COLOR_BORDER,
        corner_radius=T.RADIUS_MEDIUM,
    )
    frame.pack(fill="x")
    return frame


def divider(master, *, pady=(T.SPACE_MD, 0)) -> ctk.CTkFrame:
    """1px 分隔线；用 Frame 而不是 ttk.Separator，颜色好控制。"""
    line = ctk.CTkFrame(master, height=1, fg_color=T.COLOR_BORDER)
    line.pack(fill="x", pady=pady)
    return line


def style_scrollable(frame):
    """把 CTkScrollableFrame 的滚动条调成窄条淡色。

    CTkScrollableFrame 的滚动条藏在 ``_scrollbar`` 私有属性里，只能这样拿；
    CTk 升级时如果改名，这里会静默失效（不报错，只是回到默认样式）。
    """
    bar = getattr(frame, "_scrollbar", None)
    if bar is not None:
        bar.configure(
            width=T.SCROLLBAR_WIDTH,
            fg_color="transparent",
            button_color=T.COLOR_SCROLLBAR,
            button_hover_color=T.COLOR_SCROLLBAR_HOVER,
        )
    return frame


def scrollable(master) -> ctk.CTkScrollableFrame:
    """已经配好滚动条样式的滚动容器。"""
    return style_scrollable(ctk.CTkScrollableFrame(master, fg_color="transparent"))


def empty_hint(master, title: str, detail: str = "") -> ctk.CTkFrame:
    """居中的空状态：一行主提示 + 一行补充说明。"""
    box = ctk.CTkFrame(master, fg_color="transparent")
    ctk.CTkLabel(box, text=title, font=T.FONT_BODY, text_color=T.COLOR_MUTED).pack()
    if detail:
        ctk.CTkLabel(
            box,
            text=detail,
            font=T.FONT_SMALL,
            text_color=T.COLOR_MUTED,
            justify="center",
        ).pack(pady=(6, 0))
    return box


def field_label(master, text: str, *, width: int = 112) -> ctk.CTkLabel:
    """卡片内左对齐的字段名，宽度固定让右边控件能对齐成一列。"""
    return ctk.CTkLabel(
        master,
        text=text,
        font=T.FONT_SMALL,
        text_color=T.COLOR_MUTED,
        width=width,
        anchor="w",
    )


def hint_label(master, text: str) -> ctk.CTkLabel:
    """字段下方的说明文字。"""
    return ctk.CTkLabel(
        master,
        text=text,
        font=T.FONT_SMALL,
        text_color=T.COLOR_MUTED,
        anchor="w",
        justify="left",
    )
