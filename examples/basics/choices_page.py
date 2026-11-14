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
    RadioGroup,
    Scrollable,
    Segmented,
    Switch,
    TextArea,
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

check = Checkbox(row, "记住这台设备", command, value=True)
# Checkbox(master, text="", command=None, *, width=20, height=20, value=False)

check.set_value(True)   # 勾上
check.set_value(False)  # 取消
check.get_value()       # True / False

# value 是初始状态，默认 False（不勾）；选中后填 COLOR_ACTIVE 并打勾'''

RADIO_CODE = '''from ctk_kit import RadioGroup

group = RadioGroup(
    row,
    ["每次询问", "总是同步", "只在本机保存"],
    value="每次询问",
    on_change=lambda value: print(value),
)
group.pack(side="left")

# 一组选项一个控件，读和改都走它
group.get_value()          # "每次询问"
group.set_value("总是同步") # 程序切换，不触发 on_change'''


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

        self.build_cards(
            area,
            [
                self._build_segmented,
                self._build_switches,
                self._build_checks,
                self._build_radio,
            ],
        )

    def _build_segmented(self, area: tk.Misc) -> None:
        """分段选择：常规、紧凑与空列表三种。"""
        box = Card(area, title="分段选择")
        box.pack(fill="x")

        row = box.row(1, fill="x", padx=16, pady=(14, 8))
        self.segmented = Segmented(
            row.label("分类"), SEGMENT_VALUES, self._on_segment, width=300
        )
        self.segmented.pack(anchor="w")

        row = box.row(2, fill="x", padx=16, pady=(0, 8))
        self.compact = Segmented(
            row.label("紧凑"), COMPACT_VALUES, self._on_compact, width=200, height=30
        )
        self.compact.pack(anchor="w")

        row = box.row(3, fill="x", padx=16, pady=(0, 8))
        self.empty_segment = Segmented(row.label("空列表"), [], width=200)
        self.empty_segment.pack(anchor="w")

        HintLabel(
            box, "values=[] 时不预设选中项；宽度恒定，切换不会挤动右侧元素。"
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, SEGMENTED_CODE, "command 收到的是选中项的文字。")

    def _build_switches(self, area: tk.Misc) -> None:
        """开关：只留轨道，状态自己读 get()。"""
        box = Card(area, title="开关")
        box.pack(fill="x", pady=(12, 0))

        row = box.row(1, fill="x", padx=16, pady=(14, 8))
        label = CTkLabel(
            row, text="启用某项设置", font=T.FONT_BODY, text_color=T.COLOR_TEXT
        )
        label.pack(side="left")
        self.toggle = Switch(row, value=True)
        self.toggle.pack(side="left", padx=(12, 0))

        row = box.row(2, fill="x", padx=16, pady=(0, 8))
        label = CTkLabel(
            row, text="紧凑尺寸", font=T.FONT_BODY, text_color=T.COLOR_TEXT
        )
        label.pack(side="left")
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

        self.device_check = Checkbox(box, "记住这台设备", value=True)
        self.device_check.pack(anchor="w", padx=16, pady=(14, 8))

        self.sync_check = Checkbox(box, "启动时自动同步")
        self.sync_check.pack(anchor="w", padx=16, pady=(0, 8))

        HintLabel(
            box, "value=True 初始就勾上；get() 返回 0/1，select() / deselect() 可直接改。"
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, CHECKBOX_CODE, "和 Switch 一样，状态要自己读 get()。")

    def _build_radio(self, area: tk.Misc) -> None:
        """单选组：一个控件管一组选项，读和改都走它。"""
        box = Card(area, title="单选组")
        box.pack(fill="x", pady=(12, 0))

        self.radio_group = RadioGroup(box, RADIO_VALUES, value=RADIO_VALUES[0])
        self.radio_group.pack(anchor="w", padx=16, pady=(14, 8))

        HintLabel(
            box, "一组选项一个控件；get_value() / set_value() 直接读写。"
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, RADIO_CODE, "不用自己建 StringVar，也不用逐个 Radio。")

    # --- 分段控件：command 必须构造时传（内部靠它重绘选中段文字），事件类覆写 ---
    def _on_segment(self, value: str) -> None:
        """主分类分段的切换回调：UI 类里空实现，由事件类覆写。"""

    def _on_compact(self, value: str) -> None:
        """紧凑分段的切换回调：UI 类里空实现，由事件类覆写。"""


class ChoicesPage(ChoicesPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.when_built(self.bind_events)

    def bind_events(self) -> None:
        """注册开关、勾选与单选的 command。"""
        self.toggle.configure(command=self._on_toggle)
        self.compact_switch.configure(command=self._on_compact_switch)
        self.device_check.configure(command=self._on_device_check)
        self.sync_check.configure(command=self._on_sync_check)
        self.radio_group.on_change = self._on_radio

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

    def _on_radio(self, value: str) -> None:
        """单选组切换：回调直接收到选中的值。"""
        self._show(f"单选：{value}")

    def _on_segment(self, value: str) -> None:
        """主分类分段：command 收到选中项文字。"""
        self._show(f"分段选中：{value}")

    def _on_compact(self, value: str) -> None:
        """紧凑分段：日 / 周 / 月。"""
        self._show(f"紧凑分段：{value}")

    def _show(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
