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
    FlatButton,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    Scrollable,
    TagSelectField,
    TreeSelectField,
    tokens as T,
)
from ctk_kit.theme import color_of

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

#: 带标签的候选：值是文件名，标签是大小 / 类型。
TAGGED_VALUES = ["报告.pdf", "数据.xlsx", "照片.png"]

_TAGGED_TAGS = {
    "报告.pdf": ["1.2 MB", "PDF"],
    "数据.xlsx": ["3.4 MB", "Excel"],
}

#: 层级树的示例数据：字符串是叶子，``("分组", [...])`` 展开后是缩进子项。
TREE_VALUES = [
    "A1",
    "B2",
    ("层级 C", ["C1", "C2", "C3", ("更深一层", ["D1", "D2"])]),
    ("层级 E", ["E1", "E2"]),
]

SINGLE_CODE = '''from ctk_kit import DropField

row = card.row(1, fill="x", padx=16, pady=(14, 8))
field = DropField(
    row.label("选择"),
    values_provider=lambda: ["选项 A", "选项 B", "选项 C"],
    command=lambda value: print(value),
    placeholder="点右侧箭头选择",
)
field.pack(fill="x")
# DropField(master, *, values_provider, command=None, placeholder="", height=36)

field.get()             # 当前文字
field.set("选项 A")      # 直接写入
# values_provider 每次展开都会重新调用，数据源可以随时变'''

TAGGED_CODE = '''from ctk_kit import DropField

row = card.row(1, fill="x", padx=16, pady=(14, 8))
field = DropField(
    row.label("文件"),
    values=["报告.pdf", "数据.xlsx", "照片.png"],
    tags={
        "报告.pdf": ["1.2 MB", "PDF"],
        "数据.xlsx": ["3.4 MB", "Excel"],
    },
    placeholder="候选右侧带标签",
)
field.pack(fill="x")

field.get()                    # "报告.pdf"，值本身不变
field.get_tags("报告.pdf")      # ["1.2 MB", "PDF"]
field.get_current_tags()       # 当前选中项的标签

field.set_tag("照片.png", ["860 KB", "PNG"])   # 单独补一行的标签
field.set_tags({"报告.pdf": ["2.0 MB", "PDF"]})  # 整体替换

# 标签只影响候选行的显示，不参与 get() / command()
# 悬停在值或标签上，整行一起高亮'''

TAGS_CODE = '''from ctk_kit import TagSelectField

row = card.row(1, fill="x", padx=16, pady=(14, 8))
tags = TagSelectField(
    row.label("多选"),
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
# 点标签直接删掉；标签多了横向滚动'''

TREE_CODE = '''from ctk_kit import TreeSelectField

row = card.row(1, fill="x", padx=16, pady=(14, 8))
tree = TreeSelectField(
    row.label("层级"),
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
        self.header.info.configure(text="单选 / 候选标签 / 多选标签 / 层级树")

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "点开任意下拉，回显会出现在这里")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self.build_cards(
            area,
            [
                self._build_single,
                self._build_tagged,
                self._build_tags,
                self._build_tree,
            ],
        )

    def _build_single(self, area: tk.Misc) -> None:
        """单选：普通与带预设值两种。"""
        box = Card(area, title="单选")
        box.pack(fill="x")

        row = box.row(1, fill="x", padx=16, pady=(14, 8))
        self.single = DropField(
            row.label("普通"),
            values_provider=_single_values,
            command=self._on_single,
            placeholder="点右侧箭头选择",
        )
        self.single.pack(fill="x")

        row = box.row(2, fill="x", padx=16, pady=(0, 8))
        self.preset = DropField(
            row.label("预设值"),
            values_provider=_preset_values,
            command=self._on_single,
            placeholder="点右侧箭头选择",
        )
        self.preset.pack(fill="x")
        self.preset.set("Alpha")

        row = box.row(3, fill="x", padx=16, pady=(0, 8))
        self.disabled_field = DropField(
            row.label("禁用项"),
            values_provider=_preset_values,
            placeholder="Beta 一开始就是禁用的",
            disabled=["Beta"],
        )
        self.disabled_field.pack(fill="x")

        row = box.row(4, fill="x", padx=16, pady=(0, 8))
        self.disabled_button = FlatButton(row, "解除 Beta", self._on_toggle_disabled)
        self.disabled_button.pack(side="left")

        HintLabel(
            box,
            "禁用的候选项置灰、点不了：disable() / enable() / is_disabled() / "
            "get_disabled() / set_disabled() / clear_disabled()。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            SINGLE_CODE,
            "values_provider 是函数而不是列表，数据变了下次展开就会生效。",
        )

    def _build_tagged(self, area: tk.Misc) -> None:
        """带标签的候选：标签画在每一行右侧。"""
        box = Card(area, title="候选标签")
        box.pack(fill="x", pady=(12, 0))

        row = box.row(1, fill="x", padx=16, pady=(14, 8))
        self.tagged = DropField(
            row.label("文件"),
            values=TAGGED_VALUES,
            tags=dict(_TAGGED_TAGS),
            command=self._on_tagged,
            placeholder="点右侧箭头看标签",
        )
        self.tagged.pack(fill="x")

        row = box.row(2, fill="x", padx=16, pady=(0, 8))
        self.tagged_button = FlatButton(row, "给 照片.png 补标签", self._on_add_tag)
        self.tagged_button.pack(side="left")

        self.tagged_value = HintLabel(box, "标签：（还没选）")
        self.tagged_value.pack(fill="x", padx=16, pady=(0, 2))

        HintLabel(
            box,
            "tags 是「候选 → 标签列表」的字典，画在候选行右侧；get() 仍只返回值本身，"
            "标签用 get_tags(value) / get_current_tags() 读，set_tag() 单独补一行。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            TAGGED_CODE,
            "标签只用于显示，不影响值、搜索和 command 的参数。",
        )

    def _build_tags(self, area: tk.Misc) -> None:
        """多选标签：选中的值变成标签排进框里。"""
        box = Card(area, title="多选标签")
        box.pack(fill="x", pady=(12, 0))

        row = box.row(1, fill="x", padx=16, pady=(14, 8))
        self.tags = TagSelectField(
            row.label("语言"),
            values_provider=_tag_values,
            command=self._on_tags,
            placeholder="点箭头多选",
            values=["Python", "Go"],
        )
        self.tags.pack(fill="x")

        self.tags_value = HintLabel(box, "已选：Python、Go")
        self.tags_value.pack(fill="x", padx=16, pady=(0, 2))

        HintLabel(
            box,
            "已选中的项再点一次是取消选中；标签不重复。点标签本身就能删掉，"
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

        row = box.row(1, fill="x", padx=16, pady=(14, 8))
        self.tree = TreeSelectField(
            row.label("分组"),
            values_provider=_tree_values,
            command=self._on_tree,
            placeholder="点箭头展开分组",
        )
        self.tree.pack(fill="x")

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
        self.when_built(self.bind_events)

    def bind_events(self) -> None:
        """三个下拉的 command 都在构造时传好了，这里只补输入框的实时回显。"""
        self.single.entry.on_key_release(self._on_single_key)
        self.tree.entry.on_key_release(self._on_tree_key)

    def _on_single(self, value: str) -> None:
        """单选：回显选中的值。"""
        self._show(f"单选：{value}")

    def _on_tagged(self, value: str) -> None:
        """带标签下拉选中：回显值和它的标签。"""
        tags = self.tagged.get_tags(value)
        text = " · ".join(tags) if tags else "无"
        self.tagged_value.configure(text=f"已选：{value}（{text}）")
        self._show(f"带标签：{value}（{text}）")

    def _on_add_tag(self) -> None:
        """给「照片.png」补一行标签，演示 set_tag。"""
        self.tagged.set_tag("照片.png", ["860 KB", "PNG"])
        self.tagged_button.disable()
        self._show("已给 照片.png 补上标签，重新展开就能看到")

    def _on_tags(self, values: list) -> None:
        """多选：同步「已选」行并回显整个列表。"""
        text = "、".join(values) if values else "（空）"
        self.tags_value.configure(text=f"已选：{text}")
        self._show(f"多选：{values}")

    def _on_tree(self, value: str) -> None:
        """层级树选中叶子：回显。"""
        self.tree_value.configure(text=f"已选：{value}")
        self._show(f"层级选中：{value}")

    def _on_toggle_disabled(self) -> None:
        """切换 Beta 的禁用状态，并更新按钮文字。"""
        if self.disabled_field.is_disabled("Beta"):
            self.disabled_field.enable("Beta")
            self.disabled_button.configure(text="禁用 Beta")
            self._show("已解除 Beta 的禁用")
        else:
            self.disabled_field.disable("Beta")
            self.disabled_button.configure(text="解除 Beta")
            self._show("Beta 已禁用，点它不会有反应")

    def _on_single_key(self, _event: tk.Event) -> None:
        """手动改单选输入框时也回显。"""
        self._show(f"单选输入：{self.single.get() or '（空）'}")

    def _on_tree_key(self, _event: tk.Event) -> None:
        """手动改层级输入框时也回显。"""
        self._show(f"层级输入：{self.tree.get() or '（空）'}")

    def _show(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
