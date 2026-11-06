"""提示页：窗口顶部 / 底部的浮层提示，级别、形态与位置。

与 ``button_page.py`` / ``collapse_page.py`` 一样拆成「UI 类 + 事件类」：
``NotifyPageUI`` 只建控件，``NotifyPage`` 在构造时自动 ``bind_events()``。
提示统一走 ``self.app.notify(...)``——``App`` 自带提示层（``self.notifier``），
页面里不用自己建 ``Notifier``，切页时提示也不会被页面带走。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    DangerButton,
    FormEntry,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    PrimaryButton,
    Scrollable,
    SecondaryButton,
    SoftButton,
    TextArea,
    Tooltip,
    tokens as T,
    CodePanel,
)

#: 代码块字体：等宽，比正文大一点，展开后不用凑近看。
CODE_FONT = ("Consolas", 15)

#: 级别与中文名：按钮文字和提示内容共用一份，避免两边写岔。
LEVEL_LABELS = {
    "info": "信息",
    "success": "成功",
    "warn": "警告",
    "error": "错误",
}

LEVEL_CODE = '''app.notify("这是一条信息提示")                    # info
app.notify("保存成功", level="success")
app.notify("磁盘快满了", level="warn")
app.notify("连接失败，请重试", level="error")

# 级别只改颜色：取 tokens.STATUS_COLORS[level]
# 窄条（pill）默认 2.6 秒后自动消失'''

STYLE_CODE = '''app.notify("已复制到剪贴板", style="pill")

app.notify("连接超时，请检查网络后重试",
           title="云备份失败", level="error", style="card")

# pill：一行文字 + 级别色圆点，2.6 秒
# card：图标 + 标题 + 正文 + 关闭按钮，4.5 秒'''

POSITION_CODE = '''app.notify("贴在窗口顶部", position="top")
app.notify("贴在窗口底部", position="bottom")

# 距窗口边缘 16px，窗口缩放时自动跟随
# 同一位置的多条提示纵向堆叠，最新的贴边'''

STACK_CODE = '''app.notify("第一条")
app.notify("第二条")     # 同一位置向下堆叠
app.notify("第三条")

app.notify("正在导出…", style="card", duration=0)   # 常驻
app.notifier.clear()                             # 一次关掉全部

# 最多同时 3 条（max_visible），超出时最旧的先关掉
# 指针停在提示上会暂停计时，移开继续倒数'''

TOOLTIP_CODE = '''from ctk_kit import Tooltip

Tooltip(save_button, "保存当前草稿")
Tooltip(entry, lambda: f"当前长度 {len(entry.get())}", delay=300)'''


class NotifyPageUI(PageBase):
    """提示页 UI：只建控件，事件留给 NotifyPage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "提示")
        self.header.info.configure(text="4 个级别 · 2 种形态 · 2 个位置 · 悬浮提示")

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "点按钮，提示会浮在窗口边缘")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self.build_cards(
            area,
            [
                self._build_level,
                self._build_style,
                self._build_position,
                self._build_stack,
                self._build_tooltip,
            ],
        )

    def _build_level(self, area: tk.Misc) -> None:
        """级别：四种状态色。"""
        box = Card(area, title="级别 level")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.level_buttons = {}
        for level, label in LEVEL_LABELS.items():
            button = SecondaryButton(row, f"{label} {level}", width=110)
            button.pack(side="left", padx=(0, 8))
            self.level_buttons[level] = button

        HintLabel(
            box,
            "级别只改颜色，取 tokens.STATUS_COLORS；窄条形态 2.6 秒后自动消失。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            LEVEL_CODE,
            "level 收 info / success / warn / error，传错会抛 ValueError。",
        )

    def _build_style(self, area: tk.Misc) -> None:
        """形态：窄条 pill 与卡片 card。"""
        box = Card(area, title="形态 style")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.pill_button = SecondaryButton(row, "窄条 pill", width=110)
        self.pill_button.pack(side="left")

        self.card_button = SecondaryButton(row, "卡片 card", width=110)
        self.card_button.pack(side="left", padx=(8, 0))

        HintLabel(
            box,
            "窄条适合「已复制」这类过程提示；卡片带图标、标题与关闭按钮，"
            "适合错误和警告。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            STYLE_CODE,
            "两种形态的默认停留时间不同：pill 2.6 秒，card 4.5 秒。",
        )

    def _build_position(self, area: tk.Misc) -> None:
        """位置：贴窗口顶部还是底部。"""
        box = Card(area, title="位置 position")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.top_button = PrimaryButton(row, "顶部 top", width=110)
        self.top_button.pack(side="left")

        self.bottom_button = PrimaryButton(row, "底部 bottom", width=110)
        self.bottom_button.pack(side="left", padx=(8, 0))

        HintLabel(
            box,
            "顶部靠上边缘、底部靠下边缘，距边 16px；窗口缩放时提示跟着走。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            POSITION_CODE,
            "位置不影响布局：提示是独立的无边框小窗口，不占页面高度。",
        )

    def _build_stack(self, area: tk.Misc) -> None:
        """堆叠与常驻：连发、常驻卡片、一次清空。"""
        box = Card(area, title="堆叠与常驻")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.burst_button = SecondaryButton(row, "连发三条", width=100)
        self.burst_button.pack(side="left")

        self.sticky_button = SecondaryButton(row, "常驻卡片", width=100)
        self.sticky_button.pack(side="left", padx=(8, 0))

        self.clear_button = DangerButton(row, "全部关掉", width=100)
        self.clear_button.pack(side="left", padx=(8, 0))

        HintLabel(
            box,
            "同一位置的提示向下堆叠，最多同时 3 条；duration=0 时不自动消失。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            STACK_CODE,
            "常驻卡片要点右上角 ✕ 或调用 clear() 才会关掉。",
        )

    def _build_tooltip(self, area: tk.Misc) -> None:
        """悬浮提示：按钮和输入框挂一行说明，和通知提示是同一套浮层风格。"""
        box = Card(area, title="悬浮提示")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.save_button = PrimaryButton(row, "保存")
        self.save_button.pack(side="left")

        self.delay_button = SoftButton(row, "延迟 300ms")
        self.delay_button.pack(side="left", padx=(8, 0))

        self.tip_entry = FormEntry(row, placeholder="输入几个字，再悬停")
        self.tip_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        self.edge_button = SoftButton(row, "靠右边缘")
        self.edge_button.pack(side="right", padx=(8, 0))

        HintLabel(
            box,
            "默认停 0.5 秒弹出；文字可以传函数，每次悬停都重新算。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            TOOLTIP_CODE,
            "提示窗口不抢焦点；贴着屏幕边缘时会自动翻到上方。",
        )


class NotifyPage(NotifyPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.when_built(self.bind_events)

    def bind_events(self) -> None:
        """必须实现：注册按钮和事件。"""
        for level, button in self.level_buttons.items():
            button.configure(command=lambda lv=level: self._pop_level(lv))

        self.pill_button.configure(
            command=lambda: self._pop(
                "已复制到剪贴板", style="pill", level="success"
            )
        )
        self.card_button.configure(
            command=lambda: self._pop(
                "连接超时，请检查网络后重试",
                title="云备份失败",
                level="error",
                style="card",
            )
        )

        self.top_button.configure(
            command=lambda: self._pop("贴在窗口顶部", position="top")
        )
        self.bottom_button.configure(
            command=lambda: self._pop("贴在窗口底部", position="bottom")
        )

        self.burst_button.configure(command=self._burst)
        self.sticky_button.configure(command=self._sticky)
        self.clear_button.configure(command=self._clear)

        self.tips = [
            Tooltip(self.save_button, "保存当前草稿"),
            Tooltip(self.delay_button, "延迟 0.3 秒才弹出", delay=300),
            Tooltip(
                self.tip_entry,
                lambda: f"当前输入了 {len(self.tip_entry.get())} 个字符",
                delay=200,
            ),
            Tooltip(self.edge_button, "窗口贴边时提示会翻到左边或上方"),
        ]

    def _pop_level(self, level: str) -> None:
        """按级别弹一条窄条提示。"""
        self._pop(f"这是一条{LEVEL_LABELS[level]}提示", level=level)

    def _pop(self, message: str, **kwargs) -> None:
        """弹提示（走 App 自带的提示层），并把参数写回底部回显。"""
        self.app.notify(message, **kwargs)
        where = "顶部" if kwargs.get("position", "top") == "top" else "底部"
        shape = "卡片" if kwargs.get("style", "pill") == "card" else "窄条"
        self._echo(f"{where} · {shape} · 已弹出：{message}")

    def _burst(self) -> None:
        """连发三条，演示同一位置的堆叠与数量上限。"""
        for delay, text in ((0, "第一条"), (160, "第二条"), (320, "第三条")):
            self.after(delay, lambda t=text: self._pop(f"{t}：同一位置向下堆叠"))
        self._echo("连发三条；超出 max_visible（默认 3）时最旧的先关掉")

    def _sticky(self) -> None:
        """常驻卡片：duration=0，需要手动关闭。"""
        self._pop(
            "这条不会自动消失，点右上角 ✕ 或下面的「全部关掉」",
            title="需要手动确认",
            level="warn",
            style="card",
            duration=0,
        )

    def _clear(self) -> None:
        """一次关掉全部提示。"""
        self.app.notifier.clear()
        self._echo("已关掉所有提示")

    def _echo(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
