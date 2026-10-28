"""页面骨架：页头、分区卡片、分隔线、滚动容器、空状态。

一套页面按这个顺序搭出来，视觉就不会散：

    page_header  →  section(title)  →  card 里的若干行  →  divider  →  footer

除滚动容器外，这里的工厂都会顺手 ``pack``（``fill="x"``），因为它们的位置
在页面骨架里是固定的；按钮、输入框这类需要自己摆位。
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from . import tokens as T


def page_header(master: tk.Misc, title: str) -> tuple[ctk.CTkFrame, ctk.CTkLabel]:
    """页面顶部：左边标题，右边统计信息。

    返回 ``(容器, 信息标签)``，调用方拿到信息标签后自己 ``configure(text=...)``，
    容器已经 ``pack(fill="x")``。

    参数:
        master: 父容器。
        title: 左侧大标题。

    返回:
        ``(head, info)``：``head`` 是透明容器，``info`` 是右侧灰色小字标签。
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


def section_title(master: tk.Misc, text: str) -> ctk.CTkLabel:
    """分区标题（设置页的「外观」「备份」这一层）。

    参数:
        master: 父容器。
        text: 标题文字。

    返回:
        已 ``pack(fill="x", pady=(16, 6))`` 的标签。
    """
    label = ctk.CTkLabel(
        master, text=text, font=T.FONT_SECTION, text_color=T.COLOR_TEXT, anchor="w"
    )
    label.pack(fill="x", pady=(T.SPACE_LG, T.SPACE_SM - 2))
    return label


def card(master: tk.Misc) -> ctk.CTkFrame:
    """圆角卡片容器：内容都往这里放。

    参数:
        master: 父容器。

    返回:
        已 ``pack(fill="x")`` 的卡片 Frame（1px 边框、10 圆角）。
    """
    frame = ctk.CTkFrame(
        master,
        fg_color=T.COLOR_CARD,
        border_width=1,
        border_color=T.COLOR_BORDER,
        corner_radius=T.RADIUS_MEDIUM,
    )
    frame.pack(fill="x")
    return frame


def divider(master: tk.Misc, *, pady: tuple[int, int] = (T.SPACE_MD, 0)) -> ctk.CTkFrame:
    """1px 分隔线；用 Frame 而不是 ttk.Separator，颜色好控制。

    参数:
        master: 父容器。
        pady: ``(上, 下)`` 外边距，默认 ``(12, 0)``。

    返回:
        已 ``pack(fill="x")`` 的 1px 高 Frame。
    """
    line = ctk.CTkFrame(master, height=1, fg_color=T.COLOR_BORDER)
    line.pack(fill="x", pady=pady)
    return line


def style_scrollable(frame: ctk.CTkScrollableFrame) -> ctk.CTkScrollableFrame:
    """把 CTkScrollableFrame 的滚动条调成窄条淡色。

    CTkScrollableFrame 的滚动条藏在 ``_scrollbar`` 私有属性里，只能这样拿；
    CTk 升级时如果改名，这里会静默失效（不报错，只是回到默认样式）。

    参数:
        frame: ``CTkScrollableFrame`` 实例；传入其它控件时原样返回。

    返回:
        同一个 ``frame``，方便链式调用。
    """
    bar = getattr(frame, "_scrollbar", None)
    if bar is not None:
        bar.configure(
            width=T.SCROLLBAR_WIDTH,
            fg_color="transparent",
            button_color=T.COLOR_SCROLLBAR,
            button_hover_color=T.COLOR_SCROLLBAR_HOVER,
        )
    canvas = getattr(frame, "_parent_canvas", None)
    if canvas is not None:
        # CTk 默认 yscrollincrement=1，一格滚轮只挪 20px；调到 3 倍（60px）
        canvas.configure(yscrollincrement=3)
    return frame


def scrollable(master: tk.Misc) -> ctk.CTkScrollableFrame:
    """已经配好滚动条样式的滚动容器（透明底）。

    参数:
        master: 父容器。

    返回:
        尚未摆位的 ``CTkScrollableFrame``；由调用方决定 ``pack`` 还是 ``grid``。
    """
    return style_scrollable(ctk.CTkScrollableFrame(master, fg_color="transparent"))


def empty_hint(master: tk.Misc, title: str, detail: str = "") -> ctk.CTkFrame:
    """居中的空状态：一行主提示 + 一行补充说明。

    参数:
        master: 父容器。
        title: 主提示（如「这里还没有内容」）。
        detail: 补充说明；为空时只显示一行。

    返回:
        透明容器，已经装好 1~2 行灰色文字；摆放由调用方决定。
    """
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


def field_label(master: tk.Misc, text: str, *, width: int = 112) -> ctk.CTkLabel:
    """卡片内左对齐的字段名，宽度固定让右边控件能对齐成一列。

    参数:
        master: 父容器。
        text: 字段名。
        width: 固定宽度（像素），默认 112。

    返回:
        尚未摆位的 ``CTkLabel``（``anchor="w"``）。
    """
    return ctk.CTkLabel(
        master,
        text=text,
        font=T.FONT_SMALL,
        text_color=T.COLOR_MUTED,
        width=width,
        anchor="w",
    )


def hint_label(master: tk.Misc, text: str) -> ctk.CTkLabel:
    """字段下方的说明文字。

    参数:
        master: 父容器。
        text: 说明内容，支持 ``\\n`` 换行。

    返回:
        尚未摆位的 ``CTkLabel``（左对齐、多行左对齐）。
    """
    return ctk.CTkLabel(
        master,
        text=text,
        font=T.FONT_SMALL,
        text_color=T.COLOR_MUTED,
        anchor="w",
        justify="left",
    )
