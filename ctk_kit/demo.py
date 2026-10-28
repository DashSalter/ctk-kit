"""ctk-kit 组件总览。

运行::

    python -m ctk_kit.demo

左侧切换四个页面：列表 / 组件 / 配色 / 表单。
「配色」页把 ``tokens`` 里所有色值连同浅色、深色两个数值一起列出来，
换肤时对着它改最省事。
"""

from __future__ import annotations

import sys
import tkinter as tk

import customtkinter as ctk

from . import __version__
from . import tokens as T
from .buttons import (
    FlatButton,
    SoftButton,
    danger_button,
    primary_button,
    soft_button,
)
from .dropdown import DropField
from .inputs import form_entry, segmented, switch, toolbar_entry
from .layout import (
    card,
    divider,
    empty_hint,
    field_label,
    hint_label,
    page_header,
    scrollable,
    section_title,
)
from .scroll_list import LazyList
from .theme import apply_appearance, color_of

APP_TITLE = "ctk-kit 组件总览"

SAMPLE_ITEMS = [
    {
        "id": f"item-{index}",
        "title": f"示例条目 {index:02d}",
        "subtitle": "一行摘要，放网址、账号或关键词",
        "tag": ["账号", "恢复码", "密钥"][index % 3],
    }
    for index in range(120)
]

COLOR_TOKENS = sorted(name for name in vars(T) if name.startswith("COLOR_"))


def _tone(value, dark: bool) -> str:
    """色值可能是 (浅色, 深色) 二元组，也可能是单色。"""
    if isinstance(value, (tuple, list)):
        return value[1] if dark else value[0]
    return value


def _card_shell(master) -> ctk.CTkFrame:
    return card(master)


def _card_body(box: ctk.CTkFrame) -> tk.Frame:
    """卡片里放原生控件，背景与卡片同色才不会露出缝隙。"""
    body = tk.Frame(box, bg=color_of(T.COLOR_CARD))
    body.pack(fill="both", expand=True, padx=16, pady=14)
    return body


# --------------------------------------------------------------------------- #
#  列表页
def build_list_page(master) -> ctk.CTkFrame:
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, "列表")
    info.configure(text=f"{len(SAMPLE_ITEMS)} 条")

    toolbar = ctk.CTkFrame(page, fg_color="transparent")
    toolbar.pack(fill="x", pady=(14, 12))
    toolbar_entry(toolbar, "输入关键词筛选…").pack(
        side="left", fill="x", expand=True
    )
    primary_button(toolbar, "搜索", lambda: None, width=84, height=40).pack(
        side="left", padx=(10, 0)
    )
    segmented(toolbar, ["全部", "账号", "恢复码", "密钥"], width=300).pack(
        side="left", padx=(10, 0)
    )

    listing = LazyList(page, _sample_card, key_of=lambda item: item["id"])
    listing.pack(fill="both", expand=True)
    listing.render(SAMPLE_ITEMS)

    divider(page, pady=(12, 10))
    footer = ctk.CTkFrame(page, fg_color="transparent")
    footer.pack(fill="x")
    soft_button(footer, "刷新", lambda: None, width=72).pack(side="left")
    danger_button(footer, "清空", lambda: None, width=72).pack(
        side="left", padx=(8, 0)
    )
    hint_label(footer, "滚到底部会自动补下一批").pack(side="right")
    return page


def _sample_card(parent, item) -> ctk.CTkFrame:
    box = ctk.CTkFrame(
        parent,
        fg_color=T.COLOR_CARD,
        border_width=1,
        border_color=T.COLOR_BORDER,
        corner_radius=T.RADIUS_LARGE,
    )
    bg = color_of(T.COLOR_CARD)

    head = tk.Frame(box, bg=bg)
    head.pack(fill="x", padx=16, pady=(12, 2))
    tk.Label(
        head,
        text=item["title"],
        font=T.FONT_CARD_TITLE,
        bg=bg,
        fg=color_of(T.COLOR_TEXT),
        anchor="w",
    ).pack(side="left")
    tk.Label(
        head,
        text=f" {item['tag']} ",
        font=T.FONT_BADGE,
        bg=color_of(T.COLOR_SEG_SELECTED),
        fg=color_of(T.COLOR_ACCENT),
        padx=4,
        pady=1,
    ).pack(side="left", padx=(8, 0))

    SoftButton(head, "详情", lambda: None).pack(side="right")
    SoftButton(head, "复制", lambda: None).pack(side="right", padx=(0, 6))

    tk.Label(
        box,
        text=item["subtitle"],
        font=T.FONT_SMALL,
        bg=bg,
        fg=color_of(T.COLOR_MUTED),
        anchor="w",
    ).pack(fill="x", padx=16, pady=(0, 12))
    return box


# --------------------------------------------------------------------------- #
#  组件页
def build_widgets_page(master) -> ctk.CTkFrame:
    page = ctk.CTkFrame(master, fg_color="transparent")
    page_header(page, "组件")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))

    # 按钮
    section_title(area, "按钮").pack(fill="x", pady=(0, 8))
    box = _card_shell(area)
    box.pack(fill="x")
    row = _card_body(box)
    primary_button(row, "主按钮", lambda: None).pack(side="left")
    soft_button(row, "次要按钮", lambda: None).pack(side="left", padx=(8, 0))
    soft_button(row, "描边按钮", lambda: None, border=True).pack(
        side="left", padx=(8, 0)
    )
    danger_button(row, "危险按钮", lambda: None).pack(side="left", padx=(8, 0))
    FlatButton(row, "FlatButton", lambda: None).pack(side="left", padx=(8, 0))
    SoftButton(row, "SoftButton", lambda: None).pack(side="left", padx=(8, 0))

    # 输入
    section_title(area, "输入").pack(fill="x", pady=(18, 8))
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    line = tk.Frame(body, bg=color_of(T.COLOR_CARD))
    line.pack(fill="x", pady=(0, 10))
    field_label(line, "工具栏输入").pack(side="left")
    toolbar_entry(line, "输入关键词…").pack(side="left", fill="x", expand=True)

    line = tk.Frame(body, bg=color_of(T.COLOR_CARD))
    line.pack(fill="x", pady=(0, 10))
    field_label(line, "表单输入").pack(side="left")
    form_entry(line, placeholder="普通文本").pack(
        side="left", fill="x", expand=True
    )

    line = tk.Frame(body, bg=color_of(T.COLOR_CARD))
    line.pack(fill="x", pady=(0, 10))
    field_label(line, "密码").pack(side="left")
    form_entry(line, placeholder="密码", password=True).pack(
        side="left", fill="x", expand=True
    )

    line = tk.Frame(body, bg=color_of(T.COLOR_CARD))
    line.pack(fill="x", pady=(0, 10))
    field_label(line, "下拉").pack(side="left")
    DropField(
        line,
        values_provider=lambda: ["选项 A", "选项 B", "选项 C"],
        placeholder="点右侧箭头选择",
    ).pack(side="left", fill="x", expand=True)

    line = tk.Frame(body, bg=color_of(T.COLOR_CARD))
    line.pack(fill="x")
    field_label(line, "分段选择").pack(side="left")
    segmented(line, ["日", "周", "月"], width=240, height=32).pack(side="left")

    # 开关与标签
    section_title(area, "开关与文字").pack(fill="x", pady=(18, 8))
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = tk.Frame(body, bg=color_of(T.COLOR_CARD))
    row.pack(fill="x", pady=(0, 8))
    tk.Label(
        row,
        text="启用某项设置",
        font=T.FONT_BODY,
        bg=color_of(T.COLOR_CARD),
        fg=color_of(T.COLOR_TEXT),
    ).pack(side="left")
    switch(row).pack(side="left", padx=(12, 0))
    hint_label(body, "hint_label：说明文字，字号最小、颜色最淡").pack(
        fill="x", pady=(4, 0)
    )
    tk.Label(
        body,
        text="正文 FONT_BODY 13px / 次要 FONT_SMALL 12px / 极小 FONT_TINY 11px",
        font=T.FONT_BODY,
        bg=color_of(T.COLOR_CARD),
        fg=color_of(T.COLOR_TEXT),
        anchor="w",
    ).pack(fill="x", pady=(6, 0))
    tk.Label(
        body,
        text="次要文字用 COLOR_MUTED，极弱提示用 COLOR_FAINT",
        font=T.FONT_SMALL,
        bg=color_of(T.COLOR_CARD),
        fg=color_of(T.COLOR_MUTED),
        anchor="w",
    ).pack(fill="x", pady=(2, 0))

    # 空态
    section_title(area, "空态").pack(fill="x", pady=(18, 8))
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    empty_hint(body, "这里还没有内容", "空态由 empty_hint() 生成，居中两行").pack(
        fill="x", pady=10
    )
    return page


# --------------------------------------------------------------------------- #
#  配色页
def build_colors_page(master) -> ctk.CTkFrame:
    page = ctk.CTkFrame(master, fg_color="transparent")
    _, info = page_header(page, "配色")
    info.configure(text=f"{len(COLOR_TOKENS)} 个色值")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))

    grid = tk.Frame(area, bg=color_of(T.COLOR_BG))
    grid.pack(fill="both", expand=True)
    grid.grid_columnconfigure(0, weight=1, uniform="swatch")
    grid.grid_columnconfigure(1, weight=1, uniform="swatch")

    dark = ctk.get_appearance_mode() == "Dark"
    for index, name in enumerate(COLOR_TOKENS):
        value = getattr(T, name)
        _swatch(grid, name, value, dark).grid(
            row=index // 2,
            column=index % 2,
            sticky="ew",
            padx=(0, 10) if index % 2 == 0 else (0, 0),
            pady=(0, 10),
        )
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
        tk.Label(
            cell,
            text=tone,
            font=T.FONT_TINY,
            bg=color_of(T.COLOR_CARD),
            fg=color_of(T.COLOR_FAINT),
        ).pack()

    tk.Label(
        body,
        text=name,
        font=T.FONT_SMALL,
        bg=color_of(T.COLOR_CARD),
        fg=color_of(T.COLOR_TEXT),
        anchor="w",
    ).pack(anchor="w")
    tk.Label(
        body,
        text=f"浅 {light}    深 {shade}",
        font=T.FONT_TINY,
        bg=color_of(T.COLOR_CARD),
        fg=color_of(T.COLOR_MUTED),
        anchor="w",
    ).pack(anchor="w", pady=(2, 0))
    tk.Label(
        body,
        text="当前生效：" + (shade if dark else light),
        font=T.FONT_TINY,
        bg=color_of(T.COLOR_CARD),
        fg=color_of(T.COLOR_ACCENT),
        anchor="w",
    ).pack(anchor="w", pady=(2, 0))
    return box


# --------------------------------------------------------------------------- #
#  表单页
def build_form_page(master) -> ctk.CTkFrame:
    page = ctk.CTkFrame(master, fg_color="transparent")
    page_header(page, "表单")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))

    section_title(area, "基本信息").pack(fill="x", pady=(0, 8))
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    for label, placeholder, password in (
        ("名称", "例如：公司邮箱", False),
        ("账号", "登录用的账号", False),
        ("密码", "选填，可点右侧生成", True),
    ):
        line = tk.Frame(body, bg=color_of(T.COLOR_CARD))
        line.pack(fill="x", pady=(0, 10))
        field_label(line, label).pack(side="left")
        form_entry(line, placeholder=placeholder, password=password).pack(
            side="left", fill="x", expand=True
        )

    line = tk.Frame(body, bg=color_of(T.COLOR_CARD))
    line.pack(fill="x")
    field_label(line, "分类").pack(side="left")
    segmented(line, ["账号", "恢复码", "密钥"], width=280).pack(side="left")

    divider(body, pady=(14, 12))
    footer = tk.Frame(body, bg=color_of(T.COLOR_CARD))
    footer.pack(fill="x")
    hint_label(footer, "带 * 为必填；保存后立即加密写入").pack(side="left")
    primary_button(footer, "保存", lambda: None, width=104).pack(side="right")
    soft_button(footer, "取消", lambda: None, width=80, height=38, border=True).pack(
        side="right", padx=(0, 10)
    )
    return page


# --------------------------------------------------------------------------- #
#  主窗口
class DemoApp(ctk.CTk):
    PAGES = ("列表", "组件", "配色", "表单")

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        width, height = 1120, 740
        self.update_idletasks()
        left = max(0, (self.winfo_screenwidth() - width) // 2)
        top = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"{width}x{height}+{left}+{top}")
        self.minsize(900, 600)
        self.configure(fg_color=T.COLOR_BG)

        self._current = "列表"
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._pages: dict[str, ctk.CTkFrame] = {}

        self._sidebar = ctk.CTkFrame(
            self, width=200, corner_radius=0, fg_color=T.COLOR_SIDE
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)
        self._build_sidebar()

        self._area = ctk.CTkFrame(self, fg_color="transparent")
        self._area.pack(side="left", fill="both", expand=True, padx=24, pady=(18, 16))

        self._build_pages()
        self.show_page("列表")

    # ------------------------------------------------------------------ #
    def _build_sidebar(self) -> None:
        ctk.CTkLabel(
            self._sidebar,
            text="ctk-kit",
            font=(T.FONT_NAME, 16, "bold"),
            text_color=T.COLOR_TEXT,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(22, 1))
        ctk.CTkLabel(
            self._sidebar,
            text=f"v{__version__} · 组件总览",
            font=T.FONT_TINY,
            text_color=T.COLOR_MUTED,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 20))

        for name in self.PAGES:
            button = ctk.CTkButton(
                self._sidebar,
                text=name,
                height=38,
                corner_radius=T.RADIUS_SMALL,
                anchor="w",
                font=T.FONT_BODY,
                fg_color="transparent",
                hover_color=T.COLOR_SOFT,
                text_color=T.COLOR_MUTED,
                border_spacing=10,
                command=lambda key=name: self.show_page(key),
            )
            button.pack(fill="x", padx=10, pady=3)
            self._buttons[name] = button

        bottom = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=12, pady=(0, 16))
        soft_button(bottom, "切换深浅色", self.toggle_appearance, width=176).pack()

    def _build_pages(self) -> None:
        for page in self._pages.values():
            page.destroy()
        self._pages = {
            "列表": build_list_page(self._area),
            "组件": build_widgets_page(self._area),
            "配色": build_colors_page(self._area),
            "表单": build_form_page(self._area),
        }

    def show_page(self, name: str) -> None:
        self._current = name
        for key, page in self._pages.items():
            if key == name:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()
        for key, button in self._buttons.items():
            active = key == name
            button.configure(
                fg_color=T.COLOR_SEG_SELECTED if active else "transparent",
                text_color=T.COLOR_ACCENT if active else T.COLOR_MUTED,
            )

    def toggle_appearance(self) -> None:
        mode = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        apply_appearance(mode)
        self.configure(fg_color=T.COLOR_BG)
        self._sidebar.configure(fg_color=T.COLOR_SIDE)
        # 原生 tk 控件不会自己变色，整页重建最省事
        self._build_pages()
        self.show_page(self._current)


def main() -> int:
    apply_appearance("Dark")
    app = DemoApp()
    if "--page" in sys.argv:
        app.show_page(sys.argv[sys.argv.index("--page") + 1])
    if "--topmost" in sys.argv:
        app.attributes("-topmost", True)
    if "--where" in sys.argv:
        # 调试用：打印窗口矩形后退出，便于外部截图
        def report() -> None:
            print(
                f"{app.winfo_rootx()},{app.winfo_rooty()},"
                f"{app.winfo_width()},{app.winfo_height()}",
                flush=True,
            )
            app.destroy()

        app.after(900, report)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
