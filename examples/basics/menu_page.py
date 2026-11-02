"""菜单页：给任意控件挂右键菜单，回调第一个参数是被点的控件。

与 ``button_page.py`` / ``collapse_page.py`` 一样拆成「UI 类 + 事件类」：
``MenuPageUI`` 只建控件，``MenuPage`` 在 ``bind_events()`` 里挂菜单。
菜单本身是 ``ctk_kit`` 的圆角面板（``ContextMenu``），配色跟随深浅色，
不是系统原生 ``tk.Menu``。
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime

from ctk_kit import (
    Card,
    CodePanel,
    ContextMenu,
    DangerButton,
    FieldLabel,
    FormEntry,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    PrimaryButton,
    Scrollable,
    SecondaryButton,
    TextArea,
    attach_edit_menu,
    attach_menu,
    tokens as T,
)

#: 代码块字体：等宽，比正文大一点，展开后不用凑近看。
CODE_FONT = ("Consolas", 15)

#: 第一张卡片里的三个按钮：左键点它回显，右键弹菜单。
FILE_NAMES = ("配置文件.json", "日志 app.log", "草稿 note.md")

#: 可右键区块里的提示文字，复制菜单项复制的就是这一句。
ZONE_TEXT = "这一整块都能右键，菜单由 attach_menu(deep=True) 挂上去"

MENU_CODE = '''from ctk_kit import PrimaryButton, attach_menu


def on_rename(button):              # 第一个参数就是被右键的按钮
    print("重命名", button.cget("text"))


save = PrimaryButton(row, "保存")
save.pack(side="left")

# 文字配函数：一行挂上菜单；函数可以无参，也可以接一个参数
attach_menu(save, [
    ("复制名称", lambda btn: print("复制", btn.cget("text"))),
    ("重命名", on_rename),
    ("删除", lambda btn: on_delete(btn, "草稿 A")),
])'''

PARAM_CODE = '''def read_text(button):
    print(button.cget("text"), type(button).__name__)


def mark(button):
    button.configure(text="已标记 ✓")   # 菜单里能直接改被点的控件


attach_menu(target, [
    ("读我的文字", read_text),
    ("标成已标记", mark),
    ("恢复原样", reset_mark),
])'''

MANUAL_CODE = '''from ctk_kit import ContextMenu, attach_menu

menu = ContextMenu(page, width=140)
menu.add_command("重新加载", reload)
menu.add_separator()
menu.add_command("关闭菜单", menu.close)

# 位置和 source 都自己给：source 会作为回调的第一个参数
menu.show(event.x_root, event.y_root, source=event.widget)

# 容器加上 deep=True：右键落在里面的子控件上也能弹
attach_menu(zone, [("复制提示文字", on_copy)], deep=True)'''

INPUT_CODE = '''from ctk_kit import FormEntry, TextArea, attach_edit_menu

# 不用做任何事：复制 / 粘贴 / 剪切 / 清空 已经在
entry = FormEntry(row, placeholder="右键试试")

# 增：拿到菜单对象接着加
menu = attach_edit_menu(entry)
menu.add_separator()
menu.add_command("插入时间戳", stamp)

# 改：按原来的文字找到那一项，换成新文字
menu.rename_command("插入时间戳", "插入当前时间")

# 删：按文字删掉（重名只删第一个）
menu.remove_command("剪切")

# 恢复默认：丢掉现在这套，重新挂一遍
attach_edit_menu(entry, reset=True)

# TextArea（多行）同样默认带；menu=False 可以关掉
note = TextArea(frame, height=120)'''

#: 输入框卡片里的示例文字。
INPUT_SAMPLE = "选中几个字再右键，看看哪些项是灰的"

#: 演示增删改时用的菜单项名：原名与改名后的文字。
CUSTOM_LABEL = "插入时间戳"
RENAMED_LABEL = "插入当前时间"


class MenuPageUI(PageBase):
    """菜单页 UI：只建控件，菜单和回调留给 MenuPage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "菜单")
        self.header.info.configure(text="右键任意按钮或区块")

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "右键上面的控件，菜单会出现在鼠标位置")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_attach(area)
        self._build_params(area)
        self._build_manual(area)
        self._build_inputs(area)

    def _build_attach(self, area: tk.Misc) -> None:
        """一行 attach_menu 挂上菜单。"""
        box = Card(area, title="给控件挂右键菜单")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.file_buttons = {}
        for index, name in enumerate(FILE_NAMES):
            factory = (PrimaryButton, SecondaryButton, DangerButton)[index % 3]
            button = factory(row, name, width=140)
            button.pack(side="left", padx=(0 if index == 0 else 8, 0))
            self.file_buttons[name] = button

        HintLabel(
            box,
            "左键点按钮回显到下面；右键弹出菜单，菜单项执行完也会回显。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            MENU_CODE,
            "attach_menu(控件, [(文字, 函数), ...])；额外参数用 lambda 收住。",
        )

    def _build_params(self, area: tk.Misc) -> None:
        """回调拿到的第一个参数：被右键的控件本身。"""
        box = Card(area, title="回调拿到的第一个参数")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        FieldLabel(row, "目标控件", width=72).pack(side="left")
        self.target = SecondaryButton(row, "点我右键", width=130)
        self.target.pack(side="left", padx=(4, 0))

        HintLabel(
            box,
            "每个菜单项都拿到这个按钮对象：能读它的文字，也能改它的文字。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            PARAM_CODE,
            "需要更多参数就用 lambda btn: fn(btn, 别的)，按钮仍是第一个参数。",
        )

    def _build_manual(self, area: tk.Misc) -> None:
        """自己控制弹出时机：ContextMenu + deep 挂载。"""
        box = Card(area, title="自己控制弹出时机")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.zone = Frame(row, fg_color=T.COLOR_SOFT, corner_radius=T.RADIUS_MEDIUM)
        self.zone.pack(fill="x", expand=True)
        HintLabel(self.zone, ZONE_TEXT).pack(fill="x", padx=16, pady=14)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))

        self.manual_button = PrimaryButton(row, "用 ContextMenu 弹出", width=180)
        self.manual_button.pack(side="left")
        FieldLabel(row, "位置和 source 都由代码给", width=170).pack(
            side="left", padx=(12, 0)
        )

        HintLabel(
            box,
            "上面整块用 attach_menu(deep=True) 挂菜单；按钮则手动调用 "
            "ContextMenu.show()。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            MANUAL_CODE,
            "deep=True 会把容器里的子控件一起挂上，右键落在文字上也能弹出。",
        )

    def _build_inputs(self, area: tk.Misc) -> None:
        """输入框默认菜单：不用手挂，增删改也在同一张卡片里演示。"""
        box = Card(area, title="输入框默认就带菜单")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "单行", width=72).pack(side="left")
        self.menu_entry = FormEntry(row)
        self.menu_entry.pack(side="left", fill="x", expand=True)
        self.menu_entry.insert(0, INPUT_SAMPLE)

        self.menu_note = TextArea(box, height=96)
        self.menu_note.pack(fill="x", padx=16, pady=(0, 8))
        self.menu_note.set("多行文本区也默认带同一套菜单；只读时复制可用、清空会灰掉。")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        self.menu_add_btn = SecondaryButton(row, "+ 插入时间戳", None, width=140)
        self.menu_add_btn.pack(side="left")
        self.menu_rename_btn = SecondaryButton(row, "改名", None, width=84)
        self.menu_rename_btn.pack(side="left", padx=(8, 0))
        self.menu_remove_btn = SecondaryButton(row, "删除", None, width=84)
        self.menu_remove_btn.pack(side="left", padx=(8, 0))
        self.menu_reset_btn = SecondaryButton(row, "恢复默认", None, width=110)
        self.menu_reset_btn.pack(side="left", padx=(8, 0))

        HintLabel(
            box,
            "每行输入框都自带复制 / 粘贴 / 剪切 / 清空，不用 attach_menu。"
            "四个按钮改的是同一个菜单对象：点完右键输入框，就能看到增删改的结果。",
        ).pack(fill="x", padx=16, pady=(0, 14))

        CodePanel(
            box,
            INPUT_CODE,
            "想换内容就传列表，想关就 menu=False；更多写法见「输入」页。",
        )


class MenuPage(MenuPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """必须实现：注册按钮和事件（菜单在这里挂）。"""
        # attach_menu 返回的 ContextMenu 留着引用，避免被当成垃圾回收
        self.menus = []

        for name, button in self.file_buttons.items():
            button.configure(command=lambda n=name: self._echo(f"左键点了「{n}」"))
            self.menus.append(
                attach_menu(
                    button,
                    [
                        ("复制名称", lambda btn: self._copy_name(btn)),
                        ("重命名", self._rename),
                        ("删除", lambda btn, n=name: self._delete(btn, n)),
                    ],
                )
            )

        self.menus.append(
            attach_menu(
                self.target,
                [
                    ("读我的文字", self._read_text),
                    ("标成已标记", self._mark),
                    ("恢复原样", self._reset_mark),
                ],
            )
        )

        self.menus.append(
            attach_menu(
                self.zone,
                [
                    ("复制提示文字", lambda: self._copy_zone()),
                    ("", None),
                    ("关闭菜单", lambda: self._echo("菜单项执行完了")),
                ],
                deep=True,
            )
        )

        self.manual_menu = ContextMenu(self, width=150)
        self.manual_menu.add_command("重新加载", lambda: self._echo("菜单项「重新加载」"))
        self.manual_menu.add_separator()
        self.manual_menu.add_command(
            "把区块标成已处理", lambda: self._echo("区块已标记为处理完成")
        )

        self.manual_button.configure(command=self._open_manual)

        # 输入框菜单的增 / 改 / 删 / 恢复
        self.menu_add_btn.configure(command=self._add_menu_item)
        self.menu_rename_btn.configure(command=self._rename_menu_item)
        self.menu_remove_btn.configure(command=self._remove_menu_item)
        self.menu_reset_btn.configure(command=self._reset_menu)

    def _copy_name(self, button: tk.Misc) -> None:
        """复制被右键按钮的文字到剪贴板。"""
        name = str(button.cget("text"))
        self.clipboard_clear()
        self.clipboard_append(name)
        self._echo(f"已复制：{name}")

    def _rename(self, button: tk.Misc) -> None:
        """菜单项只回显来源，不改控件。"""
        self._echo(f"「重命名」来自按钮：{button.cget('text')}")

    def _delete(self, button: tk.Misc, extra: str) -> None:
        """额外参数用 lambda 收住后传进来。"""
        self._echo(f"「删除」来自按钮：{button.cget('text')}，附带参数：{extra}")

    def _read_text(self, button: tk.Misc) -> None:
        """读被右键控件的文字与类型。"""
        self._echo(
            f"按钮文字是「{button.cget('text')}」，类型 {type(button).__name__}"
        )

    def _mark(self, button: tk.Misc) -> None:
        """直接改被右键控件的文字。"""
        button.configure(text="已标记 ✓")
        self._echo("这一项改的就是按钮自己的文字")

    def _reset_mark(self, button: tk.Misc) -> None:
        """把文字改回去。"""
        button.configure(text="点我右键")
        self._echo("文字已改回去")

    def _copy_zone(self) -> None:
        """复制区块里的提示文字。"""
        self.clipboard_clear()
        self.clipboard_append(ZONE_TEXT)
        self._echo("已复制区块里的提示文字")

    def _open_manual(self) -> None:
        """手动弹菜单：位置取指针，source 交给按钮。"""
        x, y = self.manual_button.winfo_pointerxy()
        self.manual_menu.show(x, y, source=self.manual_button)

    # --- 输入框菜单的增 / 改 / 删 ---
    def _edit_menu(self) -> ContextMenu:
        """输入框上那个默认菜单对象（拿到的始终是同一个）。"""
        return attach_edit_menu(self.menu_entry)

    def _add_menu_item(self) -> None:
        """增：往默认四项后面加一项自己的。"""
        menu = self._edit_menu()
        if menu.has_command(CUSTOM_LABEL) or menu.has_command(RENAMED_LABEL):
            self._echo("菜单里已经有这一项了，右键输入框看看")
            return
        menu.add_separator()
        menu.add_command(CUSTOM_LABEL, self._insert_stamp)
        self._echo(f"已添加「{CUSTOM_LABEL}」；右键输入框，点它会插入当前时间")

    def _rename_menu_item(self) -> None:
        """改：换掉这一项的文字，回调保持不变。"""
        menu = self._edit_menu()
        if menu.has_command(CUSTOM_LABEL):
            menu.rename_command(CUSTOM_LABEL, RENAMED_LABEL)
            self._echo(f"「{CUSTOM_LABEL}」已改名为「{RENAMED_LABEL}」")
        elif menu.has_command(RENAMED_LABEL):
            menu.rename_command(RENAMED_LABEL, CUSTOM_LABEL)
            self._echo(f"「{RENAMED_LABEL}」已改回「{CUSTOM_LABEL}」")
        else:
            self._echo("菜单里还没有这一项，先点「+ 插入时间戳」")

    def _remove_menu_item(self) -> None:
        """删：按文字把这一项从菜单里去掉。"""
        menu = self._edit_menu()
        for label in (CUSTOM_LABEL, RENAMED_LABEL):
            if menu.has_command(label):
                menu.remove_command(label)
                self._echo(f"已删除「{label}」，右键输入框确认一下")
                return
        self._echo("现在没有可删的自定义项，先点「+ 插入时间戳」")

    def _reset_menu(self) -> None:
        """恢复默认四项：丢掉现在这套重新挂一遍。"""
        attach_edit_menu(self.menu_entry, reset=True)
        self._echo("菜单已恢复成默认的复制 / 粘贴 / 剪切 / 清空")

    def _insert_stamp(self, entry: tk.Misc) -> None:
        """在光标处插入当前时间。"""
        entry.insert("insert", datetime.now().strftime("%H:%M:%S "))
        self._echo(f"已插入时间戳：{entry.get() or '（空）'}")

    def _echo(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
