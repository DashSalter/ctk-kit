"""ctk-kit 全组件展示（Showcase）。

运行::

    python examples/showcase.py
    python examples/showcase.py --page 按钮 --topmost

八个页面把库里每一个公开构件都用一遍：

- 总览    三层结构与组件索引，点「查看」可直接跳页
- 基件    tokens 全量：字体阶梯、状态色、色板、圆角、间距、滚动条宽度
- 按钮    四个工厂函数 + FlatButton / SoftButton，尺寸矩阵、描边、禁用
- 输入    工具栏框、表单框、密码框、分段选择、开关、下拉框
- 布局    页头、分区标题、卡片、分隔线、滚动容器、空态、字段/提示文字
- 列表    LazyList：分批加载、关键词与分类筛选、刷新、清空、空态提示
- 主题    深浅色切换、color_of、repaint_native 现场重绘
- 表单    综合表单：输入 + 下拉 + 分段 + 开关 + 底部动作

每个页面底部都有一条「交互回显」，点按钮或切选项时会写出刚才发生了什么。
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

# 允许从任意目录直接运行：python examples/showcase.py
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ctk_kit import __version__, tokens as T
from ctk_kit.buttons import (
    FlatButton,
    SoftButton,
    danger_button,
    primary_button,
    soft_button,
)
from ctk_kit.dropdown import DropField
from ctk_kit.inputs import form_entry, segmented, switch, toolbar_entry
from ctk_kit.layout import (
    card,
    divider,
    empty_hint,
    field_label,
    hint_label,
    page_header,
    scrollable,
    section_title,
    style_scrollable,
)
from ctk_kit.scroll_list import LazyList
from ctk_kit.theme import apply_appearance, color_of, is_dark, repaint_native

APP_TITLE = "ctk-kit 全组件展示"

PAGES = ("总览", "基件", "按钮", "输入", "布局", "列表", "主题", "表单")

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

# 按字号从大到小排，演示时一眼能看出层级
FONT_TOKENS = [
    ("FONT_TITLE", T.FONT_TITLE),
    ("FONT_CARD_TITLE", T.FONT_CARD_TITLE),
    ("FONT_SECTION", T.FONT_SECTION),
    ("FONT_BODY", T.FONT_BODY),
    ("FONT_SMALL", T.FONT_SMALL),
    ("FONT_TINY", T.FONT_TINY),
    ("FONT_BADGE", T.FONT_BADGE),
]

RADIUS_TOKENS = [
    ("RADIUS_SMALL", T.RADIUS_SMALL),
    ("RADIUS_MEDIUM", T.RADIUS_MEDIUM),
    ("RADIUS_LARGE", T.RADIUS_LARGE),
    ("RADIUS_PILL", T.RADIUS_PILL),
]

SPACE_TOKENS = [
    ("SPACE_XS", T.SPACE_XS),
    ("SPACE_SM", T.SPACE_SM),
    ("SPACE_MD", T.SPACE_MD),
    ("SPACE_LG", T.SPACE_LG),
    ("SPACE_XL", T.SPACE_XL),
]

# 组件索引：(页面名, 一句话说明)
INDEX = [
    ("基件", "字体、状态色、色板、圆角、间距、滚动条宽度"),
    ("按钮", "主按钮 / 次要按钮 / 危险按钮 / 描边 / 微型按钮 / 禁用态"),
    ("输入", "工具栏框、表单框、密码、分段选择、开关、下拉框"),
    ("布局", "页头、分区标题、卡片、分隔线、滚动容器、空态、字段标签"),
    ("列表", "LazyList 懒加载、关键词与分类筛选、刷新、清空、空态"),
    ("主题", "深浅色切换、color_of 取色、repaint_native 重绘原生控件"),
    ("表单", "把输入、下拉、分段、开关与底部动作拼成一张表单"),
]


def _tone(value, dark: bool) -> str:
    """色值可能是 (浅色, 深色) 二元组，也可能是单色。"""
    if isinstance(value, (tuple, list)):
        return value[1] if dark else value[0]
    return value


def _text(master, text: str, *, font, color: str, bg: str, **kwargs) -> tk.Label:
    """原生 tk.Label 的薄封装：字体、颜色、底色三件套总是要一起写。"""
    return tk.Label(master, text=text, font=font, bg=bg, fg=color, **kwargs)


class Feedback:
    """页面底部的交互回显。

    ``count`` 记录回显过几次，测试用它确认按钮真的把动作传到了这里。
    """

    def __init__(self, label: ctk.CTkLabel):
        self.label = label
        self.count = 0

    def __call__(self, text: str) -> None:
        self.count += 1
        self.label.configure(text=text)

    def text(self) -> str:
        return self.label.cget("text")


def _feedback(page, text: str = "等待交互…") -> Feedback:
    """把反馈条挂在页面底部；先于内容 pack，内容再多也不会把它挤掉。"""
    bar = ctk.CTkFrame(page, fg_color="transparent")
    bar.pack(side="bottom", fill="x", pady=(8, 0))
    label = hint_label(bar, text)
    label.pack(fill="x")
    feedback = Feedback(label)
    page.feedback = feedback
    return feedback


def _card_shell(master) -> ctk.CTkFrame:
    return card(master)


def _card_body(box: ctk.CTkFrame) -> tk.Frame:
    """卡片里放原生控件，背景与卡片同色才不会露出缝隙。"""
    body = tk.Frame(box, bg=color_of(T.COLOR_CARD))
    body.pack(fill="both", expand=True, padx=16, pady=14)
    return body


def _row(body, bg: str) -> tk.Frame:
    row = tk.Frame(body, bg=bg)
    row.pack(fill="x", pady=(0, 8))
    return row


# --------------------------------------------------------------------------- #
#  总览页
def build_overview_page(master, *, navigate=None) -> ctk.CTkFrame:
    """三层结构说明 + 组件索引，点「查看」跳到对应页面。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, "总览")
    info.configure(text=f"v{__version__} · {len(PAGES)} 个页面")

    feedback = _feedback(page, "点「查看」可以跳到对应页面")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    section_title(area, "三层结构")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    for name, desc in (
        ("tokens", "设计令牌：深浅两套颜色、字体、圆角与间距"),
        ("theme", "取色、外观切换，以及原生 tk 控件的重绘"),
        ("组件", "buttons / inputs / dropdown / layout / scroll_list"),
    ):
        row = _row(body, bg)
        _text(
            row,
            name,
            width=10,
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_ACCENT),
            bg=bg,
            anchor="w",
        ).pack(side="left")
        _text(
            row,
            desc,
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_MUTED),
            bg=bg,
            anchor="w",
        ).pack(side="left", padx=(8, 0))

    hint_label(
        body,
        "组件层只依赖 tokens 与 theme；换肤时改 tokens 即可，组件不用动。",
    ).pack(fill="x", pady=(2, 0))

    section_title(area, "组件索引")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    for name, desc in INDEX:
        row = _row(body, bg)
        _text(
            row,
            name,
            width=6,
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_TEXT),
            bg=bg,
            anchor="w",
        ).pack(side="left")
        _text(
            row,
            desc,
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_MUTED),
            bg=bg,
            anchor="w",
        ).pack(side="left", padx=(8, 0))

        def go(key: str = name) -> None:
            if navigate is None:
                feedback(f"这里会跳到「{key}」页")
                return
            navigate(key)
            feedback(f"已跳到「{key}」页")

        SoftButton(row, "查看", go).pack(side="right")
    return page


# --------------------------------------------------------------------------- #
#  基件页：tokens 全量
def build_foundation_page(master) -> ctk.CTkFrame:
    """tokens 里的每一组值都摆出来：字体、状态色、色板、圆角、间距。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, "基件")
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


# --------------------------------------------------------------------------- #
#  按钮页
def build_buttons_page(master) -> ctk.CTkFrame:
    """四个工厂函数 + 两个类，连同尺寸矩阵与禁用态。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, "按钮")
    info.configure(text="4 个工厂函数 + 2 个类")

    feedback = _feedback(page, "点任意按钮，回显会出现在这里")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    section_title(area, "基础按钮")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    primary_button(row, "主按钮", lambda: feedback("点了「主按钮」")).pack(side="left")
    soft_button(row, "次要按钮", lambda: feedback("点了「次要按钮」")).pack(
        side="left", padx=(8, 0)
    )
    soft_button(
        row, "描边按钮", lambda: feedback("点了「描边按钮」（border=True）"), border=True
    ).pack(side="left", padx=(8, 0))
    danger_button(row, "危险按钮", lambda: feedback("点了「危险按钮」")).pack(
        side="left", padx=(8, 0)
    )
    hint_label(
        body, "主按钮 38 高；次要/危险按钮 30 高；描边版只是多一圈细边。"
    ).pack(fill="x")

    section_title(area, "微型按钮（宽度按文字实测）")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    FlatButton(row, "FlatButton", lambda: feedback("点了 FlatButton")).pack(
        side="left"
    )
    SoftButton(row, "SoftButton", lambda: feedback("点了 SoftButton")).pack(
        side="left", padx=(8, 0)
    )
    FlatButton(row, "更长的文字会自动加宽", lambda: feedback("长文字的宽度是算出来的")).pack(
        side="left", padx=(8, 0)
    )
    hint_label(body, "卡片里的「复制 / 详情」就用这两个，不会浪费横向空间。").pack(
        fill="x"
    )

    section_title(area, "尺寸矩阵")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    for width, height in ((84, 30), (120, 38), (160, 46)):
        primary_button(
            row,
            f"{width}×{height}",
            lambda w=width, h=height: feedback(f"主按钮 {w}×{h}"),
            width=width,
            height=height,
        ).pack(side="left", padx=(0, 8))
    row = _row(body, bg)
    for width in (60, 76, 120):
        soft_button(
            row,
            f"次要 {width}",
            lambda w=width: feedback(f"次要按钮宽 {w}"),
            width=width,
        ).pack(side="left", padx=(0, 8))
    row = tk.Frame(body, bg=bg)
    row.pack(fill="x")
    for height in (26, 30, 38):
        danger_button(
            row,
            f"危险 {height} 高",
            lambda h=height: feedback(f"危险按钮高 {h}"),
            height=height,
        ).pack(side="left", padx=(0, 8))

    section_title(area, "禁用态")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    for factory, text in (
        (primary_button, "主按钮"),
        (soft_button, "次要按钮"),
        (danger_button, "危险按钮"),
    ):
        button = factory(row, text, lambda: None)
        button.configure(state="disabled")
        button.pack(side="left", padx=(0, 8))
    hint_label(body, "state='disabled' 后仍保持原来的配色，只降低不透明度。").pack(
        fill="x"
    )
    return page


# --------------------------------------------------------------------------- #
#  输入页
def build_inputs_page(master) -> ctk.CTkFrame:
    """五类输入控件，每种都给一个能改状态、能回显的实例。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, "输入")
    info.configure(text="工具栏框 / 表单框 / 分段 / 开关 / 下拉")

    feedback = _feedback(page, "改任意输入，回显会出现在这里")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    # --- 工具栏输入 ---
    section_title(area, "工具栏输入 toolbar_entry")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    field_label(row, "搜索").pack(side="left")
    search = toolbar_entry(row, "输入关键词，聚焦时描边变强调色")
    search.pack(side="left", fill="x", expand=True)
    search.bind("<KeyRelease>", lambda _e: feedback(f"关键词：{search.get() or '（空）'}"))
    hint_label(body, "40 高、圆角 12；FocusIn 时 border_color 变 COLOR_ACCENT。").pack(
        fill="x"
    )

    # --- 表单输入 ---
    section_title(area, "表单输入 form_entry")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    for text, kwargs in (
        ("普通文本", {"placeholder": "不带 placehold 时也能直接输入"}),
        ("密码", {"placeholder": "输入后按圆点显示", "password": True}),
        ("高 28", {"placeholder": "紧凑行", "height": 28}),
        ("高 48", {"placeholder": "宽松行", "height": 48}),
    ):
        row = _row(body, bg)
        field_label(row, text).pack(side="left")
        entry = form_entry(row, **kwargs)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind(
            "<KeyRelease>",
            lambda _e, name=text, widget=entry: feedback(
                f"{name}：{widget.get() or '（空）'}"
            ),
        )
    hint_label(
        body,
        "password=True 时内部 Entry 用 • 打码；带 placeholder 时 cget('show') 读不到状态。",
    ).pack(fill="x")

    # --- 分段选择 ---
    section_title(area, "分段选择 segmented")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    field_label(row, "分类").pack(side="left")
    segmented(
        row,
        ["全部", "账号", "恢复码", "密钥"],
        lambda value: feedback(f"分段选中：{value}"),
        width=300,
    ).pack(side="left")

    row = _row(body, bg)
    field_label(row, "紧凑").pack(side="left")
    segmented(row, ["日", "周", "月"], width=200, height=30).pack(side="left")

    row = tk.Frame(body, bg=bg)
    row.pack(fill="x")
    field_label(row, "空列表").pack(side="left")
    segmented(row, [], width=200).pack(side="left")
    hint_label(body, "values=[] 时不预设选中项；dynamic_resizing=False 宽度恒定。").pack(
        fill="x", pady=(4, 0)
    )

    # --- 开关 ---
    section_title(area, "开关 switch")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    _text(
        row,
        "启用某项设置",
        font=T.FONT_BODY,
        color=color_of(T.COLOR_TEXT),
        bg=bg,
    ).pack(side="left")
    toggle = switch(
        row, lambda: feedback("开关已开启" if toggle.get() else "开关已关闭")
    )
    toggle.pack(side="left", padx=(12, 0))
    hint_label(body, "只留轨道、去掉文字，progress_color 跟随主色。").pack(fill="x")

    row = _row(body, bg)
    _text(
        row,
        "紧凑尺寸",
        font=T.FONT_BODY,
        color=color_of(T.COLOR_TEXT),
        bg=bg,
    ).pack(side="left")
    switch(row, lambda: feedback("紧凑开关已切换"), width=60).pack(
        side="left", padx=(12, 0)
    )

    # --- 下拉框 ---
    section_title(area, "下拉框 DropField")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    row = _row(body, bg)
    field_label(row, "普通").pack(side="left")
    DropField(
        row,
        values_provider=lambda: ["选项 A", "选项 B", "选项 C"],
        command=lambda value: feedback(f"下拉选中：{value}"),
        placeholder="点右侧箭头选择",
    ).pack(side="left", fill="x", expand=True)

    row = _row(body, bg)
    field_label(row, "空候选").pack(side="left")
    DropField(
        row,
        values_provider=lambda: [],
        placeholder="候选项为空，点箭头不会弹",
    ).pack(side="left", fill="x", expand=True)

    row = _row(body, bg)
    field_label(row, "预设值").pack(side="left")
    preset = DropField(
        row,
        values_provider=lambda: ["Alpha", "Beta", "Gamma"],
        placeholder="点右侧箭头选择",
    )
    preset.pack(side="left", fill="x", expand=True)
    preset.set("Alpha")
    preset_value = hint_label(body, "已选：Alpha")
    preset_value.pack(fill="x")
    preset.entry.bind(
        "<KeyRelease>",
        lambda _e: preset_value.configure(text=f"已选：{preset.get() or '（空）'}"),
    )
    hint_label(
        body, "get() / set() 与输入框一致；选中候选后回调 command(value)。"
    ).pack(fill="x")
    return page


# --------------------------------------------------------------------------- #
#  布局页
def build_layout_page(master) -> ctk.CTkFrame:
    """八个布局构件各来一份，说明什么时候用哪个。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, "布局")
    info.configure(text="8 个布局构件")

    feedback = _feedback(page, "布局构件本身没有回调，看结构就行")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    # --- 页头 ---
    section_title(area, "页头 page_header")
    head, head_info = page_header(area, "示例页头")
    head_info.configure(text="右侧信息标签")
    hint_label(
        area, "返回 (容器, 信息标签)；信息标签文案由调用方自己 configure。"
    ).pack(fill="x")

    # --- 分区标题 ---
    section_title(area, "分区标题 section_title")
    hint_label(
        area, "自动 pack，上下留 (SPACE_LG, SPACE_SM-2)；设置页的分区就用它。"
    ).pack(fill="x")

    # --- 卡片 / 分隔线 / 字段 ---
    section_title(area, "卡片 card + 分隔线 divider + 字段标签")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    field_label(body, "字段名").pack(side="left")
    _text(
        body,
        "field_label 固定 112 宽，让右边的输入框对齐成一列。",
        font=T.FONT_SMALL,
        color=color_of(T.COLOR_MUTED),
        bg=bg,
    ).pack(side="left")

    divider(body, pady=(8, 10))
    _text(
        body,
        "divider 是一条 1px 的 COLOR_BORDER，比 ttk.Separator 好控色。",
        font=T.FONT_SMALL,
        color=color_of(T.COLOR_MUTED),
        bg=bg,
        anchor="w",
    ).pack(fill="x")

    # --- 滚动容器 ---
    section_title(area, "滚动容器 scrollable")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    inner = style_scrollable(
        ctk.CTkScrollableFrame(body, fg_color="transparent", height=150)
    )
    inner.pack(fill="x", pady=(0, 8))
    for index in range(1, 21):
        _text(
            inner,
            f"第 {index:02d} 行：内容超过高度时出现窄滚动条（宽 {T.SCROLLBAR_WIDTH}px）。",
            font=T.FONT_SMALL,
            color=color_of(T.COLOR_TEXT),
            bg=color_of(T.COLOR_BG),
            anchor="w",
        ).pack(fill="x", pady=1)
    hint_label(body, "scrollable() 已经调好滚动条；style_scrollable 可装饰已有容器。").pack(
        fill="x"
    )

    # --- 空态 ---
    section_title(area, "空态 empty_hint")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = tk.Frame(body, bg=bg)
    row.pack(fill="x", pady=(0, 8))
    empty_hint(row, "这里还没有内容").pack(side="left", expand=True)
    empty_hint(row, "这里还没有内容", "带 detail 时是两行：主提示 + 补充说明").pack(
        side="left", expand=True
    )
    return page


# --------------------------------------------------------------------------- #
#  列表页
def build_list_page(master) -> ctk.CTkFrame:
    """LazyList 的完整用法：分批加载、筛选、刷新、清空、空态提示。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, "列表")
    info.configure(text=f"{len(SAMPLE_ITEMS)} 条")

    area = ctk.CTkFrame(page, fg_color="transparent")
    area.pack(fill="both", expand=True, pady=(14, 0))

    toolbar = ctk.CTkFrame(area, fg_color="transparent")
    toolbar.pack(fill="x", pady=(0, 12))
    search = toolbar_entry(toolbar, "输入关键词筛选…")
    search.pack(side="left", fill="x", expand=True)
    primary_button(toolbar, "搜索", lambda: apply_filter(), width=84, height=40).pack(
        side="left", padx=(10, 0)
    )
    category = segmented(
        toolbar,
        ["全部", "账号", "恢复码", "密钥"],
        lambda _value: apply_filter(),
        width=300,
    )
    category.pack(side="left", padx=(10, 0))

    listing = LazyList(
        area,
        lambda parent, item: _sample_card(parent, item, feedback),
        key_of=lambda item: item["id"],
    )
    listing.pack(fill="both", expand=True)

    divider(area, pady=(12, 10))
    footer = ctk.CTkFrame(area, fg_color="transparent")
    footer.pack(fill="x")
    # feedback 要先于 listing.render 定义：render_card 闭包会在首屏渲染时用到它
    feedback = Feedback(hint_label(footer, "滚到底部会自动补下一批"))
    feedback.label.pack(side="right")
    page.feedback = feedback

    def apply_filter(*, force: bool = False) -> None:
        keyword = search.get().strip()
        choice = category.get()
        items = [
            item
            for item in SAMPLE_ITEMS
            if (not keyword or keyword in item["title"])
            and (choice == "全部" or item["tag"] == choice)
        ]
        listing.invalidate()
        listing.render(
            items,
            empty_title="没有匹配的条目",
            empty_detail="换个关键词或分类再试一次",
            force=force,
        )
        info.configure(text=f"{len(items)} 条")
        feedback(f"筛选完成：{len(items)} 条")

    def clear() -> None:
        listing.render([], empty_title="列表已清空", empty_detail="点「刷新」恢复全部")
        info.configure(text="0 条")
        feedback("已清空列表")

    soft_button(footer, "刷新", lambda: apply_filter(force=True), width=72).pack(
        side="left"
    )
    danger_button(footer, "清空", clear, width=72).pack(side="left", padx=(8, 0))
    soft_button(
        footer,
        "空态提示",
        lambda: (
            listing.show_hint("还没有备份", "点「刷新」可以重新加载"),
            feedback("已切到空态提示"),
        ),
        width=88,
    ).pack(side="left", padx=(8, 0))
    soft_button(
        footer,
        "重建",
        lambda: (listing.invalidate(), apply_filter(), feedback("已 invalidate 并重建")),
        width=72,
    ).pack(side="left", padx=(8, 0))

    search.bind("<KeyRelease>", lambda _e: apply_filter())
    listing.render(SAMPLE_ITEMS)
    return page


def _sample_card(parent, item, feedback: Feedback | None = None) -> ctk.CTkFrame:
    box = ctk.CTkFrame(
        parent,
        fg_color=T.COLOR_CARD,
        border_width=1,
        border_color=T.COLOR_BORDER,
        corner_radius=T.RADIUS_LARGE,
    )
    bg = color_of(T.COLOR_CARD)

    def report(text: str) -> None:
        if feedback is not None:
            feedback(text)

    head = tk.Frame(box, bg=bg)
    head.pack(fill="x", padx=16, pady=(12, 2))
    _text(
        head,
        item["title"],
        font=T.FONT_CARD_TITLE,
        color=color_of(T.COLOR_TEXT),
        bg=bg,
        anchor="w",
    ).pack(side="left")
    _text(
        head,
        f" {item['tag']} ",
        font=T.FONT_BADGE,
        color=color_of(T.COLOR_ACCENT),
        bg=color_of(T.COLOR_SEG_SELECTED),
        padx=4,
        pady=1,
    ).pack(side="left", padx=(8, 0))

    SoftButton(head, "详情", lambda: report(f"详情：{item['title']}")).pack(side="right")
    SoftButton(head, "复制", lambda: report(f"复制：{item['title']}")).pack(
        side="right", padx=(0, 6)
    )

    _text(
        box,
        item["subtitle"],
        font=T.FONT_SMALL,
        color=color_of(T.COLOR_MUTED),
        bg=bg,
        anchor="w",
    ).pack(fill="x", padx=16, pady=(0, 12))
    return box


# --------------------------------------------------------------------------- #
#  主题页
def build_theme_page(master, *, on_toggle=None) -> ctk.CTkFrame:
    """深浅色切换、color_of 取色与 repaint_native 现场演示。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, "主题")
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


# --------------------------------------------------------------------------- #
#  表单页
def build_form_page(master) -> ctk.CTkFrame:
    """把输入、下拉、分段、开关与底部动作拼成一张真实表单。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, "表单")
    info.configure(text="输入 + 下拉 + 分段 + 开关")

    feedback = _feedback(page, "填完点「保存」，会回显读到的值")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    section_title(area, "基本信息")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    entries: dict[str, ctk.CTkEntry] = {}
    for label, placeholder, password in (
        ("名称", "例如：公司邮箱", False),
        ("账号", "登录用的账号", False),
        ("密码", "选填，可点右侧生成", True),
    ):
        row = _row(body, bg)
        field_label(row, label).pack(side="left")
        entry = form_entry(row, placeholder=placeholder, password=password)
        entry.pack(side="left", fill="x", expand=True)
        entries[label] = entry

    row = _row(body, bg)
    field_label(row, "分类").pack(side="left")
    category = segmented(row, ["账号", "恢复码", "密钥"], width=280)
    category.pack(side="left")

    row = _row(body, bg)
    field_label(row, "来源").pack(side="left")
    source = DropField(
        row,
        values_provider=lambda: ["手动录入", "导入", "浏览器插件"],
        placeholder="选择来源",
    )
    source.pack(side="left", fill="x", expand=True)

    row = tk.Frame(body, bg=bg)
    row.pack(fill="x")
    _text(
        row,
        "保存后通知我",
        font=T.FONT_BODY,
        color=color_of(T.COLOR_TEXT),
        bg=bg,
    ).pack(side="left")
    notify = switch(row)
    notify.pack(side="left", padx=(12, 0))
    notify.select()

    divider(body, pady=(14, 12))
    footer = tk.Frame(body, bg=bg)
    footer.pack(fill="x")
    hint_label(footer, "带 * 为必填；保存后立即加密写入").pack(side="left")

    def save() -> None:
        summary = " / ".join(
            f"{name}={widget.get() or '空'}" for name, widget in entries.items()
        )
        feedback(
            f"保存：{summary} / 分类={category.get()} / 来源={source.get() or '空'} / "
            f"通知={'开' if notify.get() else '关'}"
        )

    def reset() -> None:
        for widget in entries.values():
            widget.delete(0, "end")
        source.set("")
        category.set("账号")
        notify.deselect()
        feedback("已重置表单")

    primary_button(footer, "保存", save, width=104).pack(side="right")
    soft_button(footer, "重置", reset, width=80, height=38, border=True).pack(
        side="right", padx=(0, 10)
    )
    return page


# --------------------------------------------------------------------------- #
#  主窗口
class ShowcaseApp(ctk.CTk):
    PAGES = PAGES

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        width, height = 1180, 780
        self.update_idletasks()
        left = max(0, (self.winfo_screenwidth() - width) // 2)
        top = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"{width}x{height}+{left}+{top}")
        self.minsize(960, 640)
        self.configure(fg_color=T.COLOR_BG)

        self._current = "总览"
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
        self.show_page("总览")

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
            text=f"v{__version__} · 完整演示",
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
        area = self._area
        self._pages = {
            "总览": build_overview_page(area, navigate=self.show_page),
            "基件": build_foundation_page(area),
            "按钮": build_buttons_page(area),
            "输入": build_inputs_page(area),
            "布局": build_layout_page(area),
            "列表": build_list_page(area),
            "主题": build_theme_page(area, on_toggle=self.toggle_appearance),
            "表单": build_form_page(area),
        }

    def show_page(self, name: str) -> None:
        if name not in self._pages:
            raise ValueError(f"未知页面：{name!r}；可选 {list(self.PAGES)}")
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
    app = ShowcaseApp()
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
