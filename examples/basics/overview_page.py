"""总览页：三层结构说明 + 组件索引。

与其它页面一样拆成「UI 类 + 事件类」；组件索引里的「查看」会跳到对应页面，
示例里没有的页面（表单 / 基件 / 主题）只回显一句提示。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    __version__,
    Card,
    FieldLabel,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    Scrollable,
    SoftButton,
)

#: 组件索引：(页面名, 一句话说明)
INDEX = [
    ("基件", "字体、状态色、色板、圆角、间距、滚动条宽度"),
    ("按钮", "主按钮 / 次要按钮 / 危险按钮 / 描边 / 微型按钮 / 禁用态"),
    ("输入", "文本框、文件与文件夹选择、拖入取路径、下拉框、大文本区"),
    ("选择", "分段、开关、勾选、单选"),
    ("展开", "可折叠面板：一行标题 + 向下展开的内容区，标题文字可改"),
    ("表格", "固定表头、隔行底色、列宽自适应、超过可视行数后滚动"),
    ("图片", "图片显示、滚轮缩放、按住左键拖动看局部、双击复位"),
    ("提示", "窗口顶部/底部的浮层提示：四种级别、两种形态、堆叠与常驻"),
    ("菜单", "给任意控件挂右键菜单：回调第一个参数是被点的控件，可额外传参"),
    ("列表", "LazyList 懒加载、关键词与分类筛选、刷新、清空、空态"),
    ("主题", "深浅色切换、color_of 取色、repaint_native 重绘原生控件"),
    ("表单", "把输入、下拉、分段、开关与底部动作拼成一张表单"),
    ("设置", "外观模式切换（浅色 / 深色）、版本与运行环境"),
]

#: 示例窗口里实际有的页面；不在里面的只回显提示。
AVAILABLE = ("按钮", "展开", "总览", "输入", "选择", "表格", "图片", "提示", "菜单", "列表", "设置")


class OverviewPageUI(PageBase):
    """总览页 UI：三层结构说明 + 组件索引。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "总览")
        self.header.info.configure(text=f"v{__version__} · {len(INDEX)} 个组件页")

        self.feedback = HintLabel(self, "点「查看」可以跳到对应页面")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_layers(area)
        self._build_index(area)

    def _build_layers(self, area: tk.Misc) -> None:
        """三层结构：tokens → theme → 组件。"""
        box = Card(area, title="三层结构")
        box.pack(fill="x")

        for name, desc in (
            ("tokens", "设计令牌：深浅两套颜色、字体、圆角与间距"),
            ("theme", "取色、外观切换，以及原生 tk 控件的重绘"),
            ("组件", "buttons / inputs / dropdown / layout / scroll_list"),
        ):
            row = Frame(box)
            row.pack(fill="x", padx=16, pady=(12, 0))
            FieldLabel(row, name, width=68).pack(side="left")
            HintLabel(row, desc).pack(side="left", padx=(8, 0))

        HintLabel(
            box,
            "组件层只依赖 tokens 与 theme；换肤时改 tokens 即可，组件不用动。",
        ).pack(fill="x", padx=16, pady=(12, 14))

    def _build_index(self, area: tk.Misc) -> None:
        """组件索引：每行一个「查看」按钮。"""
        box = Card(area, title="组件索引")
        box.pack(fill="x", pady=(12, 0))

        self.view_buttons = {}
        for name, desc in INDEX:
            row = Frame(box)
            row.pack(fill="x", padx=16, pady=(10, 0))
            FieldLabel(row, name, width=68).pack(side="left")
            HintLabel(row, desc).pack(side="left", padx=(8, 0))
            button = SoftButton(row, "查看")
            button.pack(side="right")
            self.view_buttons[name] = button

        HintLabel(box, "点「查看」跳到对应页面；示例里没做的页面只回显提示。").pack(
            fill="x", padx=16, pady=(12, 14)
        )


class OverviewPage(OverviewPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """给每个「查看」按钮绑跳转。"""
        for name, button in self.view_buttons.items():
            button.configure(command=lambda n=name: self._go(n))

    def _go(self, name: str) -> None:
        """跳到目标页；目标不在示例里时只回显提示。"""
        nav = getattr(self.app, "nav", None)
        if nav is not None and name in nav.names:
            nav.show(name)
            self.feedback.configure(text=f"已跳到「{name}」页")
        else:
            self.feedback.configure(text=f"示例里没有「{name}」页")
