"""自定义主题页：挑几个最常用的颜色，改完立刻能在预览区看到效果。

颜色都在 ``ctk_kit.tokens`` 里，``theming.apply_palette()`` 会同时改令牌和
控件上持有的颜色属性，因此这里不需要重建页面，也不用重启。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    Check,
    ColorPicker,
    FieldLabel,
    FormEntry,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    PrimaryButton,
    ProgressBar,
    Radio,
    Scrollable,
    SecondaryButton,
    Segmented,
    Switch,
    Tooltip,
    theming,
)

#: 页面上可改的颜色令牌，按「行」分组：(令牌名, 显示名, 用在了哪些组件上)。
#: 同一行的取色器并排显示，用途文字挂成悬停提示，省出横向空间。
_PALETTE_ROWS = (
    (("COLOR_ACCENT", "主颜色", "用在 主按钮、强调文字、分页的当前页"),),
    (
        ("COLOR_ACTIVE", "选项主色", "用在 分段的选中块、开关、勾选、单选、滑块"),
        ("COLOR_KNOB", "选项辅助色", "用在 开关的圆球、勾选框的勾、单选框的中心点"),
        ("COLOR_KNOB_HOVER", "选项悬停色", "鼠标移到开关 / 勾选 / 单选上时的高亮"),
    ),
    (
        ("COLOR_PROGRESS", "进度条前景色", "用在 进度条的已完成段"),
        (
            "COLOR_PROGRESS_TRACK",
            "进度条背景色",
            "用在 进度条的轨道、滑块的未填充段",
        ),
    ),
)

#: 拍平后的一份清单，回填取色器、接线、回显都按它遍历。
_PALETTE_FIELDS = tuple(field for row in _PALETTE_ROWS for field in row)


class ThemePageUI(PageBase):

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "自定义主题")
        self.header.info.configure(text="改完立即生效")

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(
            self, "提示：改完立即生效，并写进状态存储，下次启动自动恢复"
        )
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_preview(area)
        self._build_palette(area)
        self.refresh_palette()

    def _build_preview(self, area: tk.Misc) -> None:
        """一块预览：改下面的颜色时，这里的控件要跟着变。"""
        box = Card(area, title="预览")
        box.pack(fill="x")

        # 第一行：两种按钮 + 窄输入框
        first = Frame(box)
        first.pack(fill="x", padx=16, pady=(14, 8))
        self.preview_button = PrimaryButton(first, "主按钮", width=100)
        self.preview_button.pack(side="left")
        self.preview_secondary = SecondaryButton(first, "次按钮", width=100)
        self.preview_secondary.pack(side="left", padx=(10, 0))
        self.preview_entry = FormEntry(first, placeholder="输入框")
        self.preview_entry.configure(width=140)
        self.preview_entry.pack(side="left", padx=(10, 0))

        # 第二行：分段选择（开 / 关）+ 开关 + 勾选框
        second = Frame(box)
        second.pack(fill="x", padx=16, pady=(0, 8))
        self.preview_segment = Segmented(second, ["开", "关"], width=120)
        self.preview_segment.pack(side="left")
        self.preview_switch = Switch(second, text="开关")
        self.preview_switch.pack(side="left", padx=(16, 0))
        self.preview_switch.select()
        self.preview_check = Check(second, "勾选框")
        self.preview_check.pack(side="left", padx=(16, 0))
        self.preview_check.select()

        # 第三行：两个单选项（共享一个变量才互斥）+ 进度条
        third = Frame(box)
        third.pack(fill="x", padx=16, pady=(0, 14))
        self._radio_var = tk.StringVar(value="甲")
        self.preview_radio_one = Radio(
            third, "单选框一", "甲", variable=self._radio_var
        )
        self.preview_radio_one.pack(side="left")
        self.preview_radio_two = Radio(
            third, "单选框二", "乙", variable=self._radio_var
        )
        self.preview_radio_two.pack(side="left", padx=(14, 0))
        self.preview_bar = ProgressBar(third, value=0.6, width=140)
        self.preview_bar.pack(side="left", padx=(16, 0))

    def _build_palette(self, area: tk.Misc) -> None:
        """一张卡片装下可改的令牌；同一行的取色器并排，用途文字悬停才显示。"""
        box = Card(area, title="颜色")
        box.pack(fill="x", pady=(12, 0))

        self._pickers: dict[str, ColorPicker] = {}

        for index, fields in enumerate(_PALETTE_ROWS):
            row = Frame(box)
            row.pack(
                fill="x", padx=16, pady=(14, 8) if index == 0 else (0, 8)
            )
            for column, (token, title, usage) in enumerate(fields):
                FieldLabel(row, title, width=84).pack(
                    side="left", padx=(0 if column == 0 else 14, 0)
                )
                picker = ColorPicker(row, width=124)
                picker.pack(side="left", padx=(4, 0))
                Tooltip(picker, usage, delay=300)
                self._pickers[token] = picker

        footer = Frame(box)
        footer.pack(fill="x", padx=16, pady=(4, 14))
        self.reset_button = SecondaryButton(
            footer, "恢复默认配色", self.on_reset, width=116
        )
        self.reset_button.pack(side="left", padx=(88, 10))
        HintLabel(footer, "会写进状态存储，下次启动自动恢复").pack(side="left")

    def refresh_palette(self) -> None:
        """按当前令牌值回填取色器。"""
        palette = theming.current_palette()
        for token, _title, _usage in _PALETTE_FIELDS:
            picker = self._pickers.get(token)
            if picker is None:
                continue
            picker.set(palette.get(token, "#000000"))

    def on_show(self) -> None:
        """切回本页时重新读一遍：颜色可能在别处被改过。"""
        self.refresh_palette()


class ThemePage(ThemePageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        for token, _title, _usage in _PALETTE_FIELDS:
            picker = self._pickers.get(token)
            if picker is not None:
                picker.configure(
                    command=lambda value, name=token: self.on_color(name, value)
                )

    def on_color(self, token: str, value: str) -> None:
        """某个令牌取了新色：改令牌 + 立刻刷一遍界面。"""
        self.app.apply_palette({token: value})
        title = next(
            (title for name, title, _u in _PALETTE_FIELDS if name == token), token
        )
        self.feedback.configure(text=f"{title}：已改成 {value}（已保存）")
        self.refresh_palette()

    def on_reset(self) -> None:
        """恢复全部默认配色，并清掉已经保存的覆盖。"""
        self.app.reset_palette()
        self.refresh_palette()
        self.feedback.configure(text="已恢复默认配色")
