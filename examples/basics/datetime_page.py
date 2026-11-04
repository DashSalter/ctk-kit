"""时间日期页：月视图、日期选择、时间输入框、三列滚轮。"""

from __future__ import annotations

import datetime as dt
import tkinter as tk

from ctk_kit import (
    Calendar,
    Card,
    CodePanel,
    DatePicker,
    HintLabel,
    PageBase,
    PageHeader,
    Scrollable,
    TimeField,
    TimePicker,
)

CALENDAR_CODE = '''import datetime as dt

from ctk_kit import Calendar

Calendar(card, value=dt.date(2026, 11, 3), command=lambda d: print(d))'''

PICKER_CODE = '''import datetime as dt

from ctk_kit import DatePicker

picker = DatePicker(card, value=dt.date(2026, 11, 2),
                    command=lambda d: print(d))
picker.get()   # datetime.date
picker.set(dt.date(2026, 12, 1))'''

TIME_FIELD_CODE = '''import datetime as dt

from ctk_kit import TimeField

field = TimeField(card, value=dt.time(0, 0, 0),
                  command=lambda t: print(t))
field.get()   # datetime.time(0, 0)
field.set(dt.time(9, 30, 0))'''

TIME_WHEEL_CODE = '''import datetime as dt

from ctk_kit import TimePicker

picker = TimePicker(card, value=dt.time(9, 30, 0),
                    command=lambda t: print(t))
picker.get()   # datetime.time(9, 30)
picker.set(dt.time(18, 0, 0))'''


class TimeDatePage(PageBase):
    """时间日期页：四张卡片，前两张同步建，时间相关随后补上。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "时间日期")
        self.header.info.configure(text="月视图、日期选择、时间输入框、时分秒滚轮")

        self.feedback = HintLabel(self, "翻月、点日期、点时间框试试")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_cards(area)

    def _build_cards(self, area: tk.Misc) -> None:
        """按顺序建四张卡片。"""
        self.build_cards(
            area,
            [
                self._build_calendar,
                self._build_date_picker,
                self._build_time_field,
                self._build_time_wheel,
            ],
        )

    def _build_calendar(self, area: tk.Misc) -> None:
        """月视图。"""
        box = Card(area, title="月视图")
        box.pack(fill="x")

        HintLabel(
            box,
            "周一开头、前后月补位；固定 6 行，翻月时高度不变。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.calendar = Calendar(box, value=dt.date(2026, 11, 3), command=self._on_date)
        self.calendar.pack(anchor="w", padx=16, pady=(0, 8))

        CodePanel(box, CALENDAR_CODE, "翻月用 prev_month() / next_month()。")

    def _build_date_picker(self, area: tk.Misc) -> None:
        """日期选择框。"""
        box = Card(area, title="日期选择")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "点输入框弹出月视图，选完写回；点弹层外面关闭。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.picker = DatePicker(box, placeholder="选择日期", command=self._on_picked)
        self.picker.pack(anchor="w", padx=16, pady=(0, 8))

        self.date_hint = HintLabel(box, "还没有选日期")
        self.date_hint.pack(fill="x", padx=16, pady=(0, 8))

        CodePanel(box, PICKER_CODE, "get() 返回 datetime.date；set() 不弹层、不回调。")

    def _build_time_field(self, area: tk.Misc) -> None:
        """时间输入框 + 弹层。"""
        box = Card(area, title="时间输入框")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "三段只读，点任意一段弹出滚轮；滚到哪个数字就更新到哪个，没有确定键。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.time_field = TimeField(box, value=dt.time(0, 0, 0), command=self._on_time)
        self.time_field.pack(anchor="w", padx=16, pady=(0, 8))

        self.time_hint = HintLabel(box, "00:00:00")
        self.time_hint.pack(fill="x", padx=16, pady=(0, 8))

        CodePanel(box, TIME_FIELD_CODE, "get() 返回 datetime.time；set() 不回调。")

    def _build_time_wheel(self, area: tk.Misc) -> None:
        """直接嵌在页面上的三列滚轮。"""
        box = Card(area, title="三列滚轮")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "不套输入框时可以直接摆出来：鼠标滚轮或点上下两行。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.time = TimePicker(box, value=dt.time(9, 30, 0), command=self._on_wheel)
        self.time.pack(anchor="w", padx=16, pady=(0, 8))

        self.wheel_hint = HintLabel(box, "09:30:00")
        self.wheel_hint.pack(fill="x", padx=16, pady=(0, 8))

        CodePanel(box, TIME_WHEEL_CODE, "get() 返回 datetime.time；set() 不回调。")

    # --- 事件 ---
    def _on_date(self, value: dt.date) -> None:
        self.feedback.configure(text=f"日历选中 {value.isoformat()}")

    def _on_picked(self, value: dt.date) -> None:
        self.date_hint.configure(text=f"选中了 {value.isoformat()}")
        self.feedback.configure(text=f"日期选择 {value.isoformat()}")

    def _on_time(self, value: dt.time) -> None:
        self.time_hint.configure(text=value.strftime("%H:%M:%S"))
        self.feedback.configure(text=f"时间确定 {value.strftime('%H:%M:%S')}")

    def _on_wheel(self, value: dt.time) -> None:
        self.wheel_hint.configure(text=value.strftime("%H:%M:%S"))
        self.feedback.configure(text=f"滚轮滚到 {value.strftime('%H:%M:%S')}")
