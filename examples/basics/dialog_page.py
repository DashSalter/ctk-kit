"""弹窗页：信息 / 成功 / 警告 / 错误 / 确认 / 输入。

对话框本体在 :mod:`ctk_kit.dialog`：``alert`` / ``confirm`` / ``prompt``
三个快捷函数，以及想自己排版时用的 ``Dialog``。它们都是**阻塞**的——
调用会停在那里，直到用户点按钮、按 Esc 或关窗。

页面按 examples 的写法拆成「UI 类 + 事件类」：``DialogPageUI`` 只建控件，
``DialogPage`` 在构造时自动 ``bind_events()``。每个卡片底部带「查看实现」。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    CTkButton,
    Card,
    CodePanel,
    FieldLabel,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    Scrollable,
    SecondaryButton,
    tokens as T,
)
from ctk_kit.dialog import alert, confirm, prompt

ALERT_CODE = '''from ctk_kit import alert

alert(app, "已保存到 D:/backup", title="完成", level="success")
# level: "info" / "success" / "warn" / "error"，只影响图标颜色
# detail="路径：D:/backup" 会在正文下面补一行灰色小字
# ok="关闭" 换按钮文字；只有一个按钮，点了就关'''

CONFIRM_CODE = '''from ctk_kit import confirm

if confirm(app, "删除这份备份？", level="warn", danger=True, ok="删除"):
    ...
# 返回 True / False
# 点取消、按 Esc（或 Alt+F4）都是 False
# danger=True 让「删除」这种确认按钮变成危险色'''

PROMPT_CODE = '''from ctk_kit import prompt

name = prompt(app, "给备份起个名字", value="backup-01")
if name is None:
    # 用户取消了
    ...
# 输入框里按回车等同点确定；返回去掉首尾空白的字符串'''

DIALOG_CODE = '''from ctk_kit.dialog import Dialog

choice = Dialog(
    app,
    title="这份备份怎么处理？",
    message="合并会保留已有的文件，覆盖会先清空再写入。",
    level="info",
    buttons=[("取消", None), ("合并", "merge"), ("覆盖", "overwrite")],
).show()
# show() 返回被点按钮的第二个元素；Esc / 关窗返回 None'''


class DialogPageUI(PageBase):
    """只建控件；按钮的动作在事件类里绑。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "弹窗")
        self.header.info.configure(text="信息 / 警告 / 确认 / 输入")

        self.feedback = HintLabel(self, "点上面的按钮，结果会回显在这里")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_alerts(area)
        self._build_confirm(area)
        self._build_prompt(area)
        self._build_custom(area)

    def _build_alerts(self, area: tk.Misc) -> None:
        """四种级别的信息框。"""
        box = Card(area, title="信息框")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "级别", width=72).pack(side="left")
        self.info_button = SecondaryButton(row, "信息", width=84)
        self.info_button.pack(side="left")
        self.success_button = SecondaryButton(row, "成功", width=84)
        self.success_button.pack(side="left", padx=(8, 0))
        self.warn_button = SecondaryButton(row, "警告", width=84)
        self.warn_button.pack(side="left", padx=(8, 0))
        self.error_button = SecondaryButton(row, "错误", width=84)
        self.error_button.pack(side="left", padx=(8, 0))

        HintLabel(
            box,
            "只有一个「知道了」，点它、按 Esc 或 Alt+F4 都能关；图标颜色跟着级别走。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, ALERT_CODE, "alert 不返回值，关掉就结束。")

    def _build_confirm(self, area: tk.Misc) -> None:
        """普通确认与危险确认。"""
        box = Card(area, title="确认框")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "类型", width=72).pack(side="left")
        self.confirm_button = SecondaryButton(row, "普通确认", width=96)
        self.confirm_button.pack(side="left")
        self.danger_button = CTkButton(
            row,
            text="危险操作",
            width=96,
            height=30,
            font=T.FONT_SMALL,
            fg_color=T.COLOR_DANGER,
            hover_color=("#b91c1c", "#dc2626"),
            text_color=T.COLOR_ACCENT_TEXT,
        )
        self.danger_button.pack(side="left", padx=(8, 0))

        HintLabel(
            box,
            "「危险操作」的确认按钮是红的，适合删除、清空这类不可恢复的动作。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, CONFIRM_CODE, "confirm 返回布尔值，直接放进 if 里用。")

    def _build_prompt(self, area: tk.Misc) -> None:
        """带输入框的弹窗。"""
        box = Card(area, title="输入框")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "重命名", width=72).pack(side="left")
        self.prompt_button = SecondaryButton(row, "换个名字", width=96)
        self.prompt_button.pack(side="left")

        HintLabel(
            box,
            "输入框里按回车等同点确定；点取消或按 Esc 返回 None。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, PROMPT_CODE, "prompt 的返回值要么是字符串，要么是 None。")

    def _build_custom(self, area: tk.Misc) -> None:
        """自己排按钮。"""
        box = Card(area, title="自定义按钮")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "三选一", width=72).pack(side="left")
        self.custom_button = SecondaryButton(row, "合并还是覆盖", width=120)
        self.custom_button.pack(side="left")

        HintLabel(
            box,
            "buttons 里每项是 (文字, 返回值)，最后一个按钮是主按钮。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, DIALOG_CODE, "需要几个选项就写几个，返回值自己定。")

    # ------------------------------------------------------------ 钩子
    def _show_alert(self, level: str) -> None:
        """四种级别的信息框：UI 类里空实现，由事件类覆写。"""

    def _show_confirm(self, danger: bool) -> None:
        """确认框：UI 类里空实现，由事件类覆写。"""

    def _show_prompt(self) -> None:
        """输入框：UI 类里空实现，由事件类覆写。"""

    def _show_custom(self) -> None:
        """自定义按钮：UI 类里空实现，由事件类覆写。"""


class DialogPage(DialogPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """几个按钮挂上回调；对话框本身在回调里现建现用。"""
        self.info_button.configure(command=lambda: self._show_alert("info"))
        self.success_button.configure(command=lambda: self._show_alert("success"))
        self.warn_button.configure(command=lambda: self._show_alert("warn"))
        self.error_button.configure(command=lambda: self._show_alert("error"))
        self.confirm_button.configure(command=lambda: self._show_confirm(False))
        self.danger_button.configure(command=lambda: self._show_confirm(True))
        self.prompt_button.configure(command=self._show_prompt)
        self.custom_button.configure(command=self._show_custom)

    def _show_alert(self, level: str) -> None:
        """按级别弹一条信息框。"""
        examples = {
            "info": ("小提示", "这是一条普通信息，看完点「知道了」就行。"),
            "success": ("备份完成", "已把 128 个文件打包到 D:/backup/2026-11-02.zip。"),
            "warn": ("空间不足", "目标磁盘只剩 1.2 GB，建议先清理再继续。"),
            "error": ("写入失败", "无法写入 D:/backup：权限被拒绝。"),
        }
        title, message = examples[level]
        alert(self, message, title=title, level=level)
        self._show(f"信息框（{level}）已关闭")

    def _show_confirm(self, danger: bool) -> None:
        """普通确认 / 危险确认。"""
        if danger:
            ok = confirm(
                self,
                "删除这份备份？",
                title="删除备份",
                detail="路径：D:/backup/2026-11-02",
                level="warn",
                ok="删除",
                danger=True,
            )
        else:
            ok = confirm(
                self,
                "现在开始同步吗？",
                title="开始同步",
                detail="本次大约需要 2 分钟",
                level="info",
            )
        self._show("确认结果：确定" if ok else "确认结果：取消")

    def _show_prompt(self) -> None:
        """带输入框的弹窗；取消返回 None。"""
        name = prompt(
            self,
            "给这份备份起个名字，之后在列表里按这个名字找。",
            title="重命名备份",
            value="backup-2026-11-02",
        )
        if name is None:
            self._show("输入框：已取消")
        else:
            self._show(f"输入框：{name or '（空字符串）'}")

    def _show_custom(self) -> None:
        """三个按钮的自定义对话框。"""
        from ctk_kit.dialog import Dialog

        result = Dialog(
            self,
            title="这份备份怎么处理？",
            message="合并会保留已有文件，覆盖会先清空再写入。",
            level="info",
            buttons=[("取消", None), ("合并", "merge"), ("覆盖", "overwrite")],
        ).show()
        if result is None:
            self._show("自定义弹窗：已取消")
        else:
            self._show(f"自定义弹窗：{result}")

    def _show(self, text: str) -> None:
        """把结果写回底部回显条。"""
        self.feedback.configure(text=text)
