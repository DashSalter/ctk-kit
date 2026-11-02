"""杂项页：多种样式的进度条与分割线。

按 examples 里的写法拆成「UI 类 + 事件类」：``MiscPageUI`` 只建控件，
``MiscPage`` 在构造时自动 ``bind_events()``。

进度条用 ``Progress``（比 ``inputs.ProgressBar`` 多分格、百分比、不确定态），
分割线用 ``layout.divider`` 的 ``text`` / ``dashed`` 参数和 ``vertical_divider``。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    CTkLabel,
    Card,
    CodePanel,
    FieldLabel,
    FlatButton,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    Progress,
    RingProgress,
    Scrollable,
    Slider,
    divider,
    tokens as T,
    vertical_divider,
)

PROGRESS_CODE = '''from ctk_kit import Progress

# 连续：最普通的细条
bar = Progress(frame, value=0.35, width=240)
bar.set(0.6)          # 0~1
bar.get()

# 分格：steps 格，达标的格子点亮
Progress(frame, steps=5, value=0.6, height=10)

# 带百分比文字
Progress(frame, value=0.45, show_text=True, height=10)

# 不确定态：一段色块来回滚，表示「不知道还要多久」
busy = Progress(frame, width=240)
busy.start_indeterminate()
busy.stop_indeterminate()

# 颜色都能换：color=已完成色，track=轨道色'''

RING_CODE = '''from ctk_kit import RingProgress

ring = RingProgress(frame, value=0.35, size=140)
ring.set(0.6)          # 0~1
ring.get()

# 带刻度：ticks 是刻度根数（密度），走过的用主色
RingProgress(frame, value=0.65, size=160, thickness=8, ticks=24)

# 只要刻度、不要圆环：纯刻度圈
RingProgress(frame, value=0.72, size=160, ticks=40, tick_len=10, ring=False)

# 有刻度时圆环会自动往里收，不会和刻度重叠
# show_text=False 去掉中间的百分比'''

DIVIDER_CODE = '''from ctk_kit import divider, vertical_divider

divider(frame)                       # 1px 实线
divider(frame, text="或")             # 线中间带一行字
divider(frame, dashed=True)          # 虚线（canvas 画的短线段）

# 竖向：同一行里隔开几块内容
vertical_divider(row, height=20, padx=(12, 12))

divider(frame, color="#ff8800")      # 线色也能单独给'''


class MiscPageUI(PageBase):
    """杂项页 UI：只建控件，事件留给 MiscPage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "杂项")
        self.header.info.configure(text="进度条 / 分割线")

        self.feedback = HintLabel(self, "拖滑块或点按钮，回显会出现在这里")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_progress(area)
        self._build_ring(area)
        self._build_divider(area)

    def _build_progress(self, area: tk.Misc) -> None:
        """进度条：连续 / 分格 / 百分比 / 不确定态。"""
        box = Card(area, title="进度条")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "连续", width=72).pack(side="left")
        self.plain = Progress(row, value=0.35, width=260)
        self.plain.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "分格", width=72).pack(side="left")
        self.stepped = Progress(row, value=0.6, steps=5, height=10, width=260)
        self.stepped.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "带文字", width=72).pack(side="left")
        self.labeled = Progress(row, value=0.45, height=10, show_text=True, width=260)
        self.labeled.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "不确定", width=72).pack(side="left")
        self.busy = Progress(row, value=0.3, width=260)
        self.busy.pack(side="left")
        self.busy_button = FlatButton(row, "播放", self._on_busy_toggle)
        self.busy_button.pack(side="left", padx=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "拖动", width=72).pack(side="left")
        self.driver = Slider(row, width=260)
        self.driver.pack(side="left")
        self.driver.set(35)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "条纹", width=72).pack(side="left")
        self.striped = Progress(row, value=0.6, height=12, striped=True, width=260)
        self.striped.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "细线", width=72).pack(side="left")
        self.thin = Progress(row, value=0.55, height=3, radius=0, width=260)
        self.thin.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "可拖", width=72).pack(side="left")
        self.handle_bar = Progress(
            row,
            value=0.4,
            height=6,
            handle=True,
            width=260,
            on_change=self._on_handle_drag,
        )
        self.handle_bar.pack(side="left")

        HintLabel(
            box,
            "滑块拖动时所有进度条一起走；「播放」按钮切换不确定态；"
            "「可拖」那条可以直接拖圆点改值。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, PROGRESS_CODE, "value 收 0~1，显示文字时四舍五入成百分比。")

    def _build_ring(self, area: tk.Misc) -> None:
        """圆环进度：普通圆环与带刻度两种。"""
        box = Card(area, title="圆环进度")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        self.ring = RingProgress(row, value=0.35, size=140)
        self.ring.pack(side="left", padx=(0, 28))
        self.ring_ticks = RingProgress(
            row, value=0.65, size=160, thickness=8, ticks=24
        )
        self.ring_ticks.pack(side="left", padx=(0, 28))
        self.ring_dial = RingProgress(
            row, value=0.72, size=160, tick_len=10, ticks=40, ring=False
        )
        self.ring_dial.pack(side="left")

        HintLabel(
            box,
            "ticks>0 时环外多一圈刻度，走过的刻度用主色；ring=False 只留刻度"
            "（纯刻度圈），ticks 就是刻度密度。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            RING_CODE,
            "set() 收 0~1，圆环尺寸由 size 固定，不随容器拉伸。",
        )

    def _build_divider(self, area: tk.Misc) -> None:
        """分割线：实线 / 带文字 / 虚线 / 竖向。"""
        box = Card(area, title="分割线")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(box, "实线").pack(fill="x", padx=16, pady=(14, 0))
        divider(box, color=T.COLOR_BORDER_INPUT, pady=(6, 12))

        HintLabel(box, "带文字").pack(fill="x", padx=16, pady=(0, 0))
        divider(box, text="或者", color=T.COLOR_BORDER_INPUT, pady=(6, 12))

        HintLabel(box, "虚线").pack(fill="x", padx=16, pady=(0, 0))
        divider(box, dashed=True, color=T.COLOR_BORDER_INPUT, pady=(6, 12))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(4, 12))
        for index, text in enumerate(("左", "中", "右")):
            if index:
                vertical_divider(
                    row, height=18, padx=(12, 12), color=T.COLOR_BORDER_INPUT
                )
            CTkLabel(
                row,
                text=text,
                font=T.FONT_BODY,
                text_color=T.COLOR_TEXT,
                fg_color="transparent",
            ).pack(side="left")

        HintLabel(
            box, "竖向分割线就是 1px 宽的 Frame，放在同一行里隔开几块内容。"
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, DIVIDER_CODE, "text 给了就从左边起排一行字，右边接实线。")


class MiscPage(MiscPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """滑块与按钮的 command 都在这里挂。"""
        self.driver.configure(command=self._on_slide)

    def _on_slide(self, value: float) -> None:
        """拖动主滑块：所有进度条和圆环一起走。"""
        ratio = value / 100.0
        self.plain.set(ratio)
        self.stepped.set(ratio)
        self.labeled.set(ratio)
        self.busy.set(ratio)
        self.striped.set(ratio)
        self.thin.set(ratio)
        self.handle_bar.set(ratio)
        self.ring.set(ratio)
        self.ring_ticks.set(ratio)
        self.ring_dial.set(ratio)
        self._show(f"进度：{ratio * 100:.0f}%")

    def _on_busy_toggle(self) -> None:
        """切换不确定态动画，并更新按钮文字。"""
        if self.busy.animating:
            self.busy.stop_indeterminate()
            self.busy_button.configure(text="播放")
            self._show("不确定态：已停止")
        else:
            self.busy.start_indeterminate()
            self.busy_button.configure(text="停止")
            self._show("不确定态：动画中")

    def _on_handle_drag(self, value: float) -> None:
        """拖动带把手的进度条：回显当前值。"""
        self._show(f"拖动进度：{value * 100:.0f}%")

    def _show(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
