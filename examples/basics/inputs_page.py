"""输入页：文本框、文件与文件夹选择、拖入取路径、下拉框、大文本区。

从旧示例的「输入」页迁过来，按 examples 里的写法拆成「UI 类 + 事件类」：
``InputsPageUI`` 只建控件，``InputsPage`` 在构造时自动 ``bind_events()``。

能后配的 command 一律在 ``bind_events`` 里挂；``DropZone`` / ``DropField`` /
``TextArea`` 只在构造时接收回调，UI 类留同名钩子方法，事件类覆写即可。
每个卡片底部都带一个「查看实现」折叠面板。
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from typing import Any

from ctk_kit import (
    Card,
    DropField,
    DropZone,
    FieldLabel,
    FormEntry,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    PathField,
    Scrollable,
    Spinner,
    Stepper,
    TextArea,
    attach_edit_menu,
    has_dnd,
    tokens as T,
    CodePanel,
)

#: 代码块字体：等宽，比正文大一点，展开后不用凑近看。
CODE_FONT = ("Consolas", 15)

#: 表单输入的示例行：(标签, FormEntry 参数)
ENTRY_ROWS = [
    ("普通文本", {"placeholder": "不带 placeholder 时也能直接输入"}),
    ("密码", {"placeholder": "输入后按圆点显示", "password": True}),
    ("高 28", {"placeholder": "紧凑行", "height": 28}),
    ("高 48", {"placeholder": "宽松行", "height": 48}),
]

#: 三个下拉框的候选数据；values_provider 每次展开都会重新调用。
DROPDOWN_VALUES = ["选项 A", "选项 B", "选项 C"]
PRESET_VALUES = ["Alpha", "Beta", "Gamma"]

#: 只读日志的预设内容。
SAMPLE_LOG = "22:00  已连接\n22:01  同步 12 条记录\n22:02  完成，用时 1.4s"


def _dropdown_values() -> list[str]:
    """普通下拉框的候选。"""
    return DROPDOWN_VALUES


def _preset_values() -> list[str]:
    """预设值下拉框的候选。"""
    return PRESET_VALUES


def _empty_values() -> list[str]:
    """空候选：展开时列表里什么都没有。"""
    return []


FORM_CODE = '''from ctk_kit import FormEntry

entry = FormEntry(frame, placeholder="请输入名称")
entry.pack(fill="x")
# FormEntry(master, *, show="", placeholder="", height=38, password=False)

FormEntry(frame, password=True)   # 内部 Entry 用 • 打码
FormEntry(frame, show="*")        # 自定义替代字符，password 优先
FormEntry(frame, height=28)       # 紧凑行

# get() / set() 与 CTkEntry 一致；placeholder 在空且失焦时显示
# 返回的就是 ctk.CTkEntry，bind、configure 都照常'''

PATH_CODE = '''from ctk_kit import PathField

field = PathField(frame, mode="file", placeholder="选一个文件")
field.pack(fill="x")
# PathField(master, *, mode="file", placeholder="", height=38,
#           button_text="浏览", title=None, on_change=None, accept_drop=True)

field.get()                     # 当前路径（空字符串表示没选）
field.set(r"D:\\备份\\config.json")
field.browse()                  # 弹对话框；选中就覆盖输入框，取消不动原值

PathField(frame, mode="folder") # 选文件夹时走 askdirectory

# accept_drop=True（默认）时文件/文件夹也能直接拖到输入框上
# on_change(path) 每次内容变化都会回调'''

DROP_CODE = '''from ctk_kit import DropZone

def on_path(path: str) -> None:
    print(path)          # 拖进来的绝对路径

zone = DropZone(frame, on_path, text="把文件拖到这里", hint="松手就填路径")
zone.pack(fill="x")
# DropZone(master, on_path, *, mode="any", height=96,
#          text="把文件或文件夹拖到这里", hint="")

# mode="file" 只收文件、"folder" 只收文件夹、"any" 都收
# 拖放依赖可选包：pip install "ctk-kit[dnd]"；没装时 ctk_kit.has_dnd() 为 False'''

DROPDOWN_CODE = '''from ctk_kit import DropField

field = DropField(
    frame,
    values_provider=lambda: ["选项 A", "选项 B", "选项 C"],
    command=lambda value: print(value),
    placeholder="点右侧箭头选择",
)
field.pack(fill="x")
# DropField(master, *, values_provider, command=None, placeholder="", height=36)

field.get()            # 当前文字
field.set("选项 A")     # 直接写入
# values_provider 每次展开都会重新调用，数据源可以随时变'''

TEXT_CODE = '''from ctk_kit import TextArea

note = TextArea(frame, placeholder="写备注、贴日志…", height=120)
note.pack(fill="x")
# TextArea(master, *, placeholder="", height=200, readonly=False,
#          show_counter=True, on_change=None, bg_color=None, text_color=None,
#          menu=True)

note.get()             # 当前全文
note.set("多行\\n文本")
note.clear()

# 只读日志：readonly=True 禁止编辑、仍可选中复制
TextArea(frame, readonly=True, show_counter=False, bg_color="transparent")'''

MENU_CODE = '''from ctk_kit import CTkEntry, FormEntry, attach_edit_menu

# 默认就带：复制 / 粘贴 / 剪切 / 清空
entry = FormEntry(row, placeholder="右键试试")

# 没选中时剪切、复制自动置灰；剪贴板空时粘贴置灰；框空时清空置灰

FormEntry(row, menu=False)                # 关掉右键菜单

FormEntry(row, menu=[("插入时间戳", stamp)])   # 只用自己的项

# 保留默认四项，再追加自己的
menu = attach_edit_menu(entry)
menu.add_separator()
menu.add_command("插入时间戳", stamp)
menu.add_command("全部选中", select_all)

# menu 是 ContextMenu：clear() 后可以重新定义整套菜单
# TextArea、DropField 内部输入框同样默认带这套菜单'''

#: 输入框右键菜单卡片里的示例文字。
MENU_SAMPLE = "选中几个字再右键，试试剪切和复制"

#: 步进输入的示例代码。
SPINNER_CODE = '''from ctk_kit import Spinner

count = Spinner(frame, from_=1, to=10, increment=1, value=1)
count.pack(side="left")
# Spinner(master, *, from_=0, to=100, increment=1, values=None, value=None,
#         command=None, placeholder="", height=36, width=160, as_int=True)

count.get()          # 1
count.set(5)         # 直接写入

# 小数步长
Spinner(frame, from_=0.0, to=2.0, increment=0.5, as_int=False)

# 一组备选文字：上下箭头在列表里前后移动
Spinner(frame, values=["小", "中", "大"], value="中")

# 数字到边界停住，备选停在首尾；直接改数字后回车会夹回区间里
# command 收到当前值，数字模式是 int / float，备选模式是文字

# 紧凑步进器：[−] 当前值 ▾ [+]，点中间能展开候选
from ctk_kit import Stepper
Stepper(frame, values=["50%", "70%", "100%"], value="70%")
Stepper(frame, from_=0, to=100, increment=10, value=70, suffix="%")'''


class InputsPageUI(PageBase):
    """输入页 UI：只建控件，事件留给 InputsPage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "输入")
        self.header.info.configure(
            text="文本框 / 文件与文件夹 / 拖入 / 下拉 / 大文本"
        )

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "改任意输入，回显会出现在这里")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self.build_cards(
            area,
            [
                self._build_entries,
                self._build_spinner,
                self._build_edit_menu,
                self._build_paths,
                self._build_drop,
                self._build_dropdown,
                self._build_text,
            ],
        )

    def _build_entries(self, area: tk.Misc) -> None:
        """表单输入：普通、密码、两种高度。"""
        box = Card(area, title="表单输入")
        box.pack(fill="x")

        # (行标签, 输入框)：事件类按这个表给每行挂按键回显
        self.entries: list[tuple[str, object]] = []
        for index, (text, kwargs) in enumerate(ENTRY_ROWS):
            row = Frame(box)
            row.pack(fill="x", padx=16, pady=(14 if index == 0 else 0, 8))

            FieldLabel(row, text, width=72).pack(side="left")
            entry = FormEntry(row, **kwargs)
            entry.pack(side="left", fill="x", expand=True)
            self.entries.append((text, entry))

        HintLabel(
            box,
            "password=True 时内部 Entry 用 • 打码；带 placeholder 时 cget('show') 读不到状态。"
            " 每行输入框都默认带右键菜单，下一张卡片演示怎么扩展。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            FORM_CODE,
            "height / password / show 三个参数最常用；返回的就是 CTkEntry，照常 bind。",
        )

    def _build_spinner(self, area: tk.Misc) -> None:
        """步进输入：数字范围、小数步长、一组文字、紧凑步进器。"""
        box = Card(area, title="步进输入")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "数量", width=72).pack(side="left")
        self.spinner = Spinner(
            row, from_=1, to=10, increment=1, value=1, command=self._on_spinner
        )
        self.spinner.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "小数", width=72).pack(side="left")
        self.float_spinner = Spinner(
            row,
            from_=0.0,
            to=2.0,
            increment=0.5,
            value=1.0,
            width=120,
            as_int=False,
            command=self._on_spinner,
        )
        self.float_spinner.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "备选", width=72).pack(side="left")
        self.size_spinner = Spinner(
            row,
            values=["小", "中", "大"],
            value="中",
            width=120,
            command=self._on_spinner,
        )
        self.size_spinner.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "紧凑", width=72).pack(side="left")
        self.stepper = Stepper(
            row,
            values=["50%", "70%", "100%"],
            value="70%",
            command=self._on_spinner,
        )
        self.stepper.pack(side="left")

        HintLabel(
            box,
            "点右侧上 / 下三角加减一步，也可以直接改数字后回车；"
            "数字模式到边界停住，备选模式停在首尾。"
            "「紧凑」那种点中间能展开候选。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            SPINNER_CODE,
            "from_ / to / increment 走数字；传 values 就变成一组文字之间切换。",
        )

    def _build_edit_menu(self, area: tk.Misc) -> None:
        """输入框右键菜单：默认、自定义、关闭三种形态。"""
        box = Card(area, title="输入框右键菜单")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "默认", width=72).pack(side="left")
        self.menu_entry = FormEntry(row)
        self.menu_entry.pack(side="left", fill="x", expand=True)
        self.menu_entry.insert(0, MENU_SAMPLE)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "自定义", width=72).pack(side="left")
        self.custom_entry = FormEntry(row)
        self.custom_entry.pack(side="left", fill="x", expand=True)
        self.custom_entry.insert(0, "右键：默认四项 + 插入时间戳")
        # UI 类先挂上默认四项，再补一项自己的；菜单对象可以反复拿
        menu = attach_edit_menu(self.custom_entry)
        menu.add_separator()
        menu.add_command("插入时间戳", self._insert_stamp)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "关闭", width=72).pack(side="left")
        self.plain_entry = FormEntry(row, menu=False)
        self.plain_entry.pack(side="left", fill="x", expand=True)
        self.plain_entry.insert(0, "menu=False，右键没有菜单")

        HintLabel(
            box,
            "默认项跟着状态走：没选中时剪切 / 复制灰掉，剪贴板空时粘贴灰掉，"
            "框空时清空灰掉。TextArea 和 DropField 里的输入框同样默认带上。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            MENU_CODE,
            "menu=False 关掉；传列表就只用自己的项；attach_edit_menu 返回菜单对象，可继续追加。",
        )

    def _build_paths(self, area: tk.Misc) -> None:
        """文件与文件夹选择：同一个 PathField，两种 mode。"""
        box = Card(area, title="文件 / 文件夹选择")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "文件", width=72).pack(side="left")
        self.file_field = PathField(
            row,
            mode="file",
            placeholder="点「浏览」选文件，或直接把这个文件拖进来",
        )
        self.file_field.pack(side="left", fill="x", expand=True)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "文件夹", width=72).pack(side="left")
        self.dir_field = PathField(
            row,
            mode="folder",
            placeholder="点「浏览」选文件夹，或直接把文件夹拖进来",
        )
        self.dir_field.pack(side="left", fill="x", expand=True)

        HintLabel(
            box,
            'PathField(mode="file") 调 askopenfilename，mode="folder" 调 askdirectory；'
            "选中就把路径写进输入框。不想点按钮时，直接把文件或文件夹拖到输入框上同样生效。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            PATH_CODE,
            "get() / set() / browse() 三个方法够用；拖入由 accept_drop 控制。",
        )

    def _build_drop(self, area: tk.Misc) -> None:
        """拖入取路径：DropZone 收到路径后写进上面那行。"""
        box = Card(area, title="拖入取路径")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "结果", width=72).pack(side="left")
        self.dropped = FormEntry(
            row, placeholder="拖进来的文件或文件夹路径会出现在这里"
        )
        self.dropped.pack(side="left", fill="x", expand=True)

        self.zone = DropZone(
            box,
            self._on_drop,
            text="把文件或文件夹拖到这里",
            hint="松手就把路径写进上面那行",
            height=96,
        )
        self.zone.pack(fill="x", padx=16, pady=(0, 10))

        HintLabel(
            box,
            (
                "不用点按钮：文件、文件夹都能直接拖进来。拖放由可选依赖 tkinterdnd2 提供"
                if has_dnd()
                else '当前没装 tkinterdnd2，拖放不可用：pip install "ctk-kit[dnd]"'
            ),
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            DROP_CODE,
            "on_path 收到绝对路径；mode 用来只收文件或只收文件夹。",
        )

    def _build_dropdown(self, area: tk.Misc) -> None:
        """下拉框：普通、空候选、带预设值。"""
        box = Card(area, title="下拉框")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "普通", width=72).pack(side="left")
        self.dropdown = DropField(
            row,
            values_provider=_dropdown_values,
            command=self._on_dropdown,
            placeholder="点右侧箭头选择",
        )
        self.dropdown.pack(side="left", fill="x", expand=True)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "空候选", width=72).pack(side="left")
        self.empty_dropdown = DropField(
            row,
            values_provider=_empty_values,
            placeholder="候选项为空，点箭头不会弹",
        )
        self.empty_dropdown.pack(side="left", fill="x", expand=True)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "预设值", width=72).pack(side="left")
        self.preset = DropField(
            row,
            values_provider=_preset_values,
            command=self._on_dropdown,
            placeholder="点右侧箭头选择",
        )
        self.preset.pack(side="left", fill="x", expand=True)
        self.preset.set("Alpha")

        self.preset_value = HintLabel(box, "已选：Alpha")
        self.preset_value.pack(fill="x", padx=16, pady=(0, 2))

        HintLabel(
            box, "get() / set() 与输入框一致；选中候选后回调 command(value)。"
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            DROPDOWN_CODE,
            "values_provider 是函数而不是列表，数据变了下次展开就会生效。",
        )

    def _build_text(self, area: tk.Misc) -> None:
        """大文本：可编辑备注 + 只读日志。"""
        box = Card(area, title="大文本")
        box.pack(fill="x", pady=(12, 0))

        self.note = TextArea(
            box,
            placeholder="写备注、粘贴日志、贴长文本…",
            height=120,
            on_change=self._on_note,
        )
        self.note.pack(fill="x", padx=16, pady=(14, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "只读日志", width=72).pack(side="left")
        HintLabel(row, "预设内容，不可编辑，可选中复制").pack(side="left", padx=(8, 0))

        self.log = TextArea(
            box, height=96, readonly=True, show_counter=False, bg_color=T.COLOR_CARD
        )
        self.log.set(SAMPLE_LOG)
        self.log.pack(fill="x", padx=16, pady=(0, 8))

        HintLabel(
            box,
            "readonly=True 时内部 state=disabled；set() 仍可写入，set_readonly() 可随时切换。",
        ).pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            TEXT_CODE,
            "readonly 只是禁止编辑，选中与复制照常；show_counter=False 去掉右下角字数。",
        )

    # --- 只在构造时接收回调的控件：事件类覆写下面四个钩子 ---
    def _on_drop(self, path: str) -> None:
        """DropZone 拖入回调：UI 类里空实现，由事件类覆写。"""

    def _insert_stamp(self, entry: object) -> None:
        """「插入时间戳」菜单项：UI 类里空实现，由事件类覆写。"""

    def _on_dropdown(self, value: str) -> None:
        """DropField 选中候选回调：UI 类里空实现，由事件类覆写。"""

    def _on_spinner(self, value: object) -> None:
        """Spinner 步进回调：UI 类里空实现，由事件类覆写。"""

    def _on_note(self, text: str) -> None:
        """备注 TextArea 的内容变化回调：UI 类里空实现，由事件类覆写。"""


class InputsPage(InputsPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.when_built(self.bind_events)

    def bind_events(self) -> None:
        """注册输入、路径选择、下拉与拖入的事件。"""
        for name, entry in self.entries:
            entry.bind(
                "<KeyRelease>",
                lambda _event, n=name, w=entry: self._show(
                    f"{n}：{w.get() or '（空）'}"
                ),
            )

        self._bind_path("文件", self.file_field)
        self._bind_path("文件夹", self.dir_field)
        self.preset.entry.on_key_release(self._on_preset_key)
        # 菜单挂上之后还能继续追加：这里演示「创建后再补一项」
        attach_edit_menu(self.custom_entry).add_command(
            "全部选中", lambda: self.custom_entry.select_range(0, "end")
        )

    def _bind_path(self, name: str, field: PathField) -> None:
        """路径字段：浏览按钮与输入框改动都回显到页面底部。"""
        field.button.configure(command=lambda: self._browse(name, field))
        for sequence in ("<KeyRelease>", "<FocusOut>"):
            field.entry.bind(
                sequence,
                lambda _event, n=name, f=field: self._show(
                    f"{n}：{f.get() or '（空）'}"
                ),
                add="+",
            )

    def _browse(self, name: str, field: PathField) -> None:
        """弹系统对话框；取消时 PathField 不会改原值。"""
        picked = field.browse()
        if not picked:
            self._show(f"{name}：取消了选择")
            return
        self._show(f"{name}：{picked}")

    def _on_drop(self, path: str) -> None:
        """把拖进来的路径写进结果行，并说明是文件还是文件夹。"""
        self.dropped.delete(0, "end")
        self.dropped.insert(0, path)
        self._show(f"拖入{self._kind(path)}：{path}")

    def _on_dropdown(self, value: str) -> None:
        """下拉选中候选：回显并在预设值那一行同步「已选」。"""
        self._show(f"下拉选中：{value}")
        if value in PRESET_VALUES:
            self.preset_value.configure(text=f"已选：{value}")

    def _on_note(self, text: str) -> None:
        """备注文本区每改一次就报一次字数。"""
        self._show(f"备注当前 {len(text)} 字")

    def _on_spinner(self, value: Any) -> None:
        """步进输入：回显当前值。"""
        self._show(f"步进：{value}")

    def _insert_stamp(self, entry: Any) -> None:
        """在光标处插入当前时间；这是「自定义菜单项」的演示。"""
        entry.insert("insert", datetime.now().strftime("%H:%M:%S "))
        self._show(f"已插入时间戳：{entry.get() or '（空）'}")

    def _on_preset_key(self, _event: tk.Event) -> None:
        """手动改预设值输入框时，同步下面的「已选」行。"""
        self.preset_value.configure(text=f"已选：{self.preset.get() or '（空）'}")

    @staticmethod
    def _kind(path: str) -> str:
        """拖入的路径是文件夹还是文件。"""
        try:
            return "文件夹" if Path(path).is_dir() else "文件"
        except OSError:
            return "路径"

    def _show(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
