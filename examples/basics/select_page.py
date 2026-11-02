"""下拉页：单选、多选标签、层级树三种下拉样式。

按 examples 里的写法拆成「UI 类 + 事件类」：``SelectPageUI`` 只建控件，
``SelectPage`` 在构造时自动 ``bind_events()``，交互都写在事件类里。

三种下拉的面板行为一致（跟随窗口、贴边翻转、滚出可视区自动收起），
区别只在候选长什么样、选中之后往哪放。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    CodePanel,
    DropField,
    FieldLabel,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    Scrollable,
    TagSelectField,
    TreeSelectField,
    tokens as T,
)

#: 单选的候选。
SINGLE_VALUES = ["选项 A", "选项 B", "选项 C"]
PRESET_VALUES = ["Alpha", "Beta", "Gamma"]

#: 多选标签的候选：故意多给几个，用来试横向滚动。
TAG_VALUES = [
    "Python",
    "Java",
    "Go",
    "Rust",
    "C++",
    "Kotlin",
    "Swift",
    "PHP",
    "Ruby",
    "Lua",
]

#: 层级树的示例数据：字符串是叶子，``("分组", [...])`` 展开后是缩进子项。
TREE_VALUES = [
    "A1",
    "B2",
    ("层级 C", ["C1", "C2", "C3", ("更深一层", ["D1", "D2"])]),
    ("层级 E", ["E1", "E2"]),
]

SINGLE_CODE = '''from ctk_kit import DropField

field = DropField(
    frame,
    values_provider=lambda: ["选项 A", "选项 B", "选项 C"],
    command=lambda value: print(value),
    placeholder="点右侧箭头选择",
)
field.pack(fill="x")
# DropField(master, *, values_provider, command=None, placeholder="", height=36)

field.get()             # 当前文字
field.set("选项 A")      # 直接写入
# values_provider 每次展开都会重新调用，数据源可以随时变'''

TAGS_CODE = '''from ctk_kit import TagSelectField

tags = TagSelectField(
    frame,
    values_provider=lambda: ["Python", "Java", "Go"],
    command=lambda values: print(values),   # 收整个列表
    placeholder="点箭头多选",
    values=["Python"],                      # 初始标签
)
tags.pack(fill="x")
# TagSelectField(master, *, values_provider, command=None,
#                placeholder="", height=36, values=None)

tags.get()              # ['Python', 'Go']，按选中顺序
tags.set(["Rust"])      # 整体替换
tags.clear()            # 清空

# 已选中的项再点一次 = 取消选中；标签不重复
# 标签右侧的小叉可以单独删；标签多了横向滚动'''

TREE_CODE = '''from ctk_kit import TreeSelectField

tree = TreeSelectField(
    frame,
    values_provider=lambda: [
        "A1",                                  # 叶子，直接可选
        ("层级 C", ["C1", "C2", "C3"]),          # 分组，点开才显示子项
        ("层级 E", [("更深", ["D1"])]),          # 子项还能继续嵌套
    ],
    command=lambda value: print(value),
    placeholder="点箭头展开分组",
)
tree.pack(fill="x")
# TreeSelectField(master, *, values_provider, command=None,
#                 placeholder="", height=36, value="")

tree.get()              # 当前值
tree.set("C2")          # 直接写入

# 分组节点本身不能被选中：点它只切换展开 / 收起，右侧 ▶ ▼ 跟着变
# 子项逐级缩进；只有叶子能选，选完面板自动收起'''


def _single_values() -> list[str]:
    """单选的候选。"""
    return SINGLE_VALUES


def _preset_values() -> list[str]:
    """带预设值那一个的候选。"""
    return PRESET_VALUES


def _tag_values() -> list[str]:
    """多选标签的候选。"""
    return TAG_VALUES


def _tree_values() -> list:
    """层级树的候选。"""
    return TREE_VALUES


class SelectPageUI(PageBase):
    """下拉页 UI：只建控件，事件留给 SelectPage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "下拉")
        self.header.info.configure(text="单选 / 多选标签 / 层级树")

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "点开任意下拉，回显会出现在这里")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_single(area)
        self._build_tags(area)
        self._build_tree(area)

    def _build_single(self, area: tk.Misc) -> None:
        """单选：普通与带预设值两种。"""
        box = Card(area, title="单选")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "普通", width=72).pack(side="left")
        self.single = DropField(
            row,
            values_provider=_single_values,
            command=self._on_single,
            placeholder="点右侧箭头选择",
        )
        self.single.pack(side="left", fill="x", expand=True)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "预设值", width=72).pack(side="left")
        self.preset = DropField(
            row,
            values_provider=_preset_values,
            command=self._on_single,
            placeholder="点右侧箭头选择",
        )
        self.preset.pack(side="left", fill="x", expand=True)
        self.preset.set("Alpha")

        HintLabel(
            box, "选中候选后写进输入框并收起面板；get() / set() 与输入框一致。"
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            SINGLE_CODE,
            "values_provider 是函数而不是列表，数据变了下次展开就会生效。",
        )

    def _build_tags(self, area: tk.Misc) -> None:
        """多选标签：选中的值变成标签排进框里。"""
        box = Card(area, title="多选标签")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "语言", width=72).pack(side="left")
        self.tags = TagSelectField(
            row,
            values_provider=_tag_values,
            command=self._on_tags,
            placeholder="点箭头多选",
            values=["Python", "Go"],
        )
        self.tags.pack(side="left", fill="x", expand=True)

        self.tags_value = HintLabel(box, "已选：Python、Go")
        self.tags_value.pack(fill="x", padx=16, pady=(0, 2))

        HintLabel(
            box,
            "已选中的项再点一次是取消选中；标签不重复。标签右侧小叉可单独删，"
            "标签多了横向滚动；没有输入框，点标签区空白也能展开候选。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            TAGS_CODE,
            "get() 返回列表，command 收到的是整个列表，面板点选后不会关。",
        )

    def _build_tree(self, area: tk.Misc) -> None:
        """层级树：分组点开才显示子项。"""
        box = Card(area, title="层级树")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "分组", width=72).pack(side="left")
        self.tree = TreeSelectField(
            row,
            values_provider=_tree_values,
            command=self._on_tree,
            placeholder="点箭头展开分组",
        )
        self.tree.pack(side="left", fill="x", expand=True)

        self.tree_value = HintLabel(box, "已选：（还没选）")
        self.tree_value.pack(fill="x", padx=16, pady=(0, 2))

        HintLabel(
            box,
            "分组节点本身不能被选中，点它只切换展开 / 收起，右侧 ▶ ▼ 跟着变；"
            "子项逐级缩进，只有叶子能选。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            TREE_CODE,
            "数据就是嵌套的 (文字, 子项) 元组，字符串等于没有子项的叶子。",
        )

    # --- 三个下拉的 command 只能在构造时传，UI 类留钩子，事件类覆写 ---
    def _on_single(self, value: str) -> None:
        """单选下拉选中回调：UI 类里空实现，由事件类覆写。"""

    def _on_tags(self, values: list) -> None:
        """多选标签变化回调：UI 类里空实现，由事件类覆写。"""

    def _on_tree(self, value: str) -> None:
        """层级树选中回调：UI 类里空实现，由事件类覆写。"""


class SelectPage(SelectPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """三个下拉的 command 都在构造时传好了，这里只补输入框的实时回显。"""
        self.single.entry.bind("<KeyRelease>", self._on_single_key)
        self.tree.entry.bind("<KeyRelease>", self._on_tree_key)

    def _on_single(self, value: str) -> None:
        """单选：回显选中的值。"""
        self._show(f"单选：{value}")

    def _on_tags(self, values: list) -> None:
        """多选：同步「已选」行并回显整个列表。"""
        text = "、".join(values) if values else "（空）"
        self.tags_value.configure(text=f"已选：{text}")
        self._show(f"多选：{values}")

    def _on_tree(self, value: str) -> None:
        """层级树选中叶子：回显。"""
        self.tree_value.configure(text=f"已选：{value}")
        self._show(f"层级选中：{value}")

    def _on_single_key(self, _event: tk.Event) -> None:
        """手动改单选输入框时也回显。"""
        self._show(f"单选输入：{self.single.get() or '（空）'}")

    def _on_tree_key(self, _event: tk.Event) -> None:
        """手动改层级输入框时也回显。"""
        self._show(f"层级输入：{self.tree.get() or '（空）'}")

    def _show(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
