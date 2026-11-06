"""选择页：分段、开关、勾选、单选。

从旧示例的「选择」页迁过来，按 examples 里的写法拆成「UI 类 + 事件类」：
``ChoicesPageUI`` 只建控件，``ChoicesPage`` 在构造时自动 ``bind_events()``。

``Switch`` / ``Checkbox`` 的 command 可以后配，全部放在 ``bind_events`` 里；
``Segmented`` 的 command 绑在内部重绘逻辑上，只能在构造时传，所以 UI 类留
同名钩子方法，事件类覆写。
每个卡片底部都带一个「查看实现」折叠面板。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    CTkLabel,
    Card,
    Checkbox,
    FieldLabel,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    Scrollable,
    Segmented,
    Switch,
    TextArea,
    radio_group,
    tokens as T,
    CodePanel,
)

#: 代码块字体：等宽，比正文大一点，展开后不用凑近看。
CODE_FONT = ("Consolas", 15)

#: 分段选择的候选：主分类与紧凑版各一组。
SEGMENT_VALUES = ["全部", "账号", "恢复码", "密钥"]
COMPACT_VALUES = ["日", "周", "月"]

#: 单选组的三项。
RADIO_VALUES = ["每次询问", "总是同步", "只在本机保存"]

SEGMENTED_CODE = '''from ctk_kit import Segmented

Segmented(
    row,
    ["全部", "账号", "恢复码", "密钥"],
    command=lambda value: print(value),   # 收选中的文字
    width=300,
    height=34,
    font=FONT_SMALL,
)
# values=[] 时不预设选中项；dynamic_resizing=False 时宽度恒定
# 选中段用 COLOR_ACTIVE，文字自动转白'''

SWITCH_CODE = '''from ctk_kit import Switch

toggle = Switch(row, command, text="启用", width=44, value=True)
# Switch(master, command=None, *, text="", width=44, value=False)
# text 留空就只显示轨道；value 是初始状态；command 不接收参数

toggle.set_value(True)    # 打开（不触发 command）
toggle.set_value(False)   # 关闭
toggle.get_value()        # True / False
toggle.toggle()           # 拨动一次，会触发 command

# 圆球色共用 COLOR_KNOB（和勾选框的勾、单选框的中心点同色），在 tokens 里改'''

CHECKBOX_CODE = '''from ctk_kit import Checkbox

check = Checkbox(row, "记住这台设备", command)
# Checkbox(master, text="", command=None, *, width=20, height=20)

check.set_value(True)   # 勾上
check.set_value(False)  # 取消
check.get_value()       # True / False

# 选中后填 COLOR_ACTIVE 并打勾；方块圆角是 RADIUS_SMALL - 2'''

RADIO_CODE = '''group, var = radio_group(
    frame,
    ["每次询问", "总是同步", "只在本机保存"],
    command=lambda value: print(value),
    variable=None,   # 传自己的 StringVar 就能从外面读写
    gap=8,           # 选项之间的行距
)
group.pack(fill="x")

var.get()            # 当前选中项的文字
var.set("总是同步")   # 直接改选中项

# 返回 (容器, StringVar)；控件必须共用同一个 variable 才互斥'''


class ChoicesPageUI(PageBase):
    """选择页 UI：只建控件，事件留给 ChoicesPage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "选择")
        self.header.info.configure(text="分段 / 开关 / 勾选 / 单选")

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "点任意选项，回显会出现在这里")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_segmented(area)
        self._build_switches(area)
        self._build_checks(area)
        self._build_radio(area)

    def _build_segmented(self, area: tk.Misc) -> None:
        """分段选择：常规、紧凑与空列表三种。"""
        box = Card(area, title="分段选择")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "分类", width=72).pack(side="left")
        self.segmented = Segmented(row, SEGMENT_VALUES, self._on_segment, width=300)
        self.segmented.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "紧凑", width=72).pack(side="left")
        self.compact = Segmented(
            row, COMPACT_VALUES, self._on_compact, width=200, height=30
        )
        self.compact.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "空列表", width=72).pack(side="left")
        self.empty_segment = Segmented(row, [], width=200)
        self.empty_segment.pack(side="left")

        HintLabel(
            box, "values=[] 时不预设选中项；宽度恒定，切换不会挤动右侧元素。"
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, SEGMENTED_CODE, "command 收到的是选中项的文字。")

    def _build_switches(self, area: tk.Misc) -> None:
        """开关：只留轨道，状态自己读 get()。"""
        box = Card(area, title="开关")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        CTkLabel(
            row, text="启用某项设置", font=T.FONT_BODY, text_color=T.COLOR_TEXT
        ).pack(side="left")
        self.toggle = Switch(row, value=True)
        self.toggle.pack(side="left", padx=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        CTkLabel(
            row, text="紧凑尺寸", font=T.FONT_BODY, text_color=T.COLOR_TEXT
        ).pack(side="left")
        self.compact_switch = Switch(row, width=60)
        self.compact_switch.pack(side="left", padx=(12, 0))

        HintLabel(box, "只留轨道、去掉文字，progress_color 跟随主色。").pack(
            fill="x", padx=16, pady=(0, 10)
        )

        CodePanel(box, SWITCH_CODE, "command 不接收参数，状态用 toggle.get_value() 读。")

    def _build_checks(self, area: tk.Misc) -> None:
        """勾选：选中后填主色并打勾。"""
        box = Card(area, title="勾选框")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        self.device_check = Checkbox(row, "记住这台设备")
        self.device_check.pack(side="left")
        self.device_check.set_value(True)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        self.sync_check = Checkbox(row, "启动时自动同步")
        self.sync_check.pack(side="left")

        HintLabel(
            box, "勾选后填主色并打勾；get() 返回 0/1，select() / deselect() 可直接改。"
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, CHECKBOX_CODE, "和 Switch 一样，状态要自己读 get()。")

    def _build_radio(self, area: tk.Misc) -> None:
        """单选组：返回 (容器, StringVar)。"""
        box = Card(area, title="单选组")
        box.pack(fill="x", pady=(12, 0))

        self.radio_group, self.radio_var = radio_group(box, RADIO_VALUES)
        self.radio_group.pack(fill="x", padx=16, pady=(14, 8))

        HintLabel(
            box, "返回 (容器, StringVar)：同一个 variable 才互斥，读变量拿当前项。"
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, RADIO_CODE, "传自己的 variable 就能从外部读写选中项。")

    # --- 分段控件：command 必须构造时传（内部靠它重绘选中段文字），事件类覆写 ---
    def _on_segment(self, value: str) -> None:
        """主分类分段的切换回调：UI 类里空实现，由事件类覆写。"""

    def _on_compact(self, value: str) -> None:
        """紧凑分段的切换回调：UI 类里空实现，由事件类覆写。"""


class ChoicesPage(ChoicesPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """注册开关、勾选与单选的 command。"""
        self.toggle.configure(command=self._on_toggle)
        self.compact_switch.configure(command=self._on_compact_switch)
        self.device_check.configure(command=self._on_device_check)
        self.sync_check.configure(command=self._on_sync_check)

        # radio_group 只在构造时收 command；建好之后逐个改内部单选框的 command，
        # 选中项本身由共享的 StringVar 维护。
        for button in self.radio_group.winfo_children():
            button.configure(command=self._on_radio)

    def _on_toggle(self) -> None:
        """开关只回调、不带参数，状态自己读。"""
        self._show("开关已开启" if self.toggle.get_value() else "开关已关闭")

    def _on_compact_switch(self) -> None:
        """紧凑开关没有文字，只回显一次切换。"""
        self._show("紧凑开关已切换")

    def _on_device_check(self) -> None:
        """勾选框同样返回 0/1。"""
        self._show(f"勾选：{self.device_check.get_value()}")

    def _on_sync_check(self) -> None:
        """第二个勾选框：只说切换了。"""
        self._show("自动同步已切换")

    def _on_radio(self) -> None:
        """单选框的 command 不带参数，当前项从 StringVar 读。"""
        self._show(f"单选：{self.radio_var.get()}")

    def _on_segment(self, value: str) -> None:
        """主分类分段：command 收到选中项文字。"""
        self._show(f"分段选中：{value}")

    def _on_compact(self, value: str) -> None:
        """紧凑分段：日 / 周 / 月。"""
        self._show(f"紧凑分段：{value}")

    def _show(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
