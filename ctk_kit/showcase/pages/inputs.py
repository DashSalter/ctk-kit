"""输入页：文本框、文件与文件夹选择、拖入取路径、下拉框、大文本。

选择类控件（分段 / 开关 / 勾选 / 单选 / 滑块 / 进度条）在「选择」页。

单独启动：``python -m ctk_kit.showcase.pages.inputs``
"""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.dropdown import DropField
from ctk_kit.files import DropZone, PathField, has_dnd
from ctk_kit.inputs import form_entry
from ctk_kit.layout import (
    field_label,
    hint_label,
    page_header,
    scrollable,
    section_title,
)
from ctk_kit.text import TextArea
from ctk_kit.theme import color_of

from ..shell import _card_body, _card_shell, _code_panel, _feedback, _row, run_page

TITLE = "输入"

FORM_CODE = '''from ctk_kit import form_entry

entry = form_entry(frame, placeholder="请输入名称")
entry.pack(fill="x")
# form_entry(master, *, show="", placeholder="", height=38, password=False)

form_entry(frame, password=True)   # 内部 Entry 用 • 打码
form_entry(frame, show="*")        # 自定义替代字符，password 优先
form_entry(frame, height=28)       # 紧凑行

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
#          show_counter=True, on_change=None, bg_color=None, text_color=None)

note.get()             # 当前全文
note.set("多行\\n文本")
note.clear()

# 只读日志：readonly=True 禁止编辑、仍可选中复制
TextArea(frame, readonly=True, show_counter=False, bg_color="transparent")'''


def _kind(path: str) -> str:
    try:
        return "文件夹" if Path(path).is_dir() else "文件"
    except OSError:
        return "路径"


def build(master) -> ctk.CTkFrame:
    """文本输入、路径选择与拖入，每种都给一个能改状态、能回显的实例。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    info.configure(text="文本框 / 文件与文件夹 / 拖入 / 下拉 / 大文本")

    feedback = _feedback(page, "改任意输入，回显会出现在这里")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    # --- 表单输入 ---
    section_title(area, "表单输入 form_entry")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    for text, kwargs in (
        ("普通文本", {"placeholder": "不带 placeholder 时也能直接输入"}),
        ("密码", {"placeholder": "输入后按圆点显示", "password": True}),
        ("高 28", {"placeholder": "紧凑行", "height": 28}),
        ("高 48", {"placeholder": "宽松行", "height": 48}),
    ):
        row = _row(body, bg)
        field_label(row, text).pack(side="left")
        entry = form_entry(row, **kwargs)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind(
            "<KeyRelease>",
            lambda _e, name=text, widget=entry: feedback(
                f"{name}：{widget.get() or '（空）'}"
            ),
        )
    hint_label(
        body,
        "password=True 时内部 Entry 用 • 打码；带 placeholder 时 cget('show') 读不到状态。",
    ).pack(fill="x")
    _code_panel(
        body,
        FORM_CODE,
        "height / password / show 三个参数最常用；返回的就是 CTkEntry，照常 bind。",
    )

    # --- 文件与文件夹选择 ---
    section_title(area, "文件 / 文件夹选择 PathField")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    row = _row(body, bg)
    field_label(row, "文件").pack(side="left")
    file_field = PathField(
        row,
        mode="file",
        placeholder="点「浏览」选文件，或直接把这个文件拖进来",
        on_change=lambda value: feedback(f"文件：{value or '（空）'}"),
    )
    file_field.pack(side="left", fill="x", expand=True)

    row = _row(body, bg)
    field_label(row, "文件夹").pack(side="left")
    dir_field = PathField(
        row,
        mode="folder",
        placeholder="点「浏览」选文件夹，或直接把文件夹拖进来",
        on_change=lambda value: feedback(f"文件夹：{value or '（空）'}"),
    )
    dir_field.pack(side="left", fill="x", expand=True)

    hint_label(
        body,
        "PathField(mode=\"file\") 调 askopenfilename，mode=\"folder\" 调 askdirectory；"
        "选中就把路径写进输入框。不想点按钮时，直接把文件或文件夹拖到输入框上同样生效。",
    ).pack(fill="x")
    _code_panel(
        body,
        PATH_CODE,
        "get() / set() / browse() 三个方法够用；拖入由 accept_drop 控制。",
    )

    # --- 拖入取路径 ---
    section_title(area, "拖入取路径 DropZone")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    row = _row(body, bg)
    field_label(row, "结果").pack(side="left")
    dropped = form_entry(row, placeholder="拖进来的文件或文件夹路径会出现在这里")
    dropped.pack(side="left", fill="x", expand=True)

    def on_drop(path: str) -> None:
        dropped.delete(0, "end")
        dropped.insert(0, path)
        feedback(f"拖入{_kind(path)}：{path}")

    zone = DropZone(
        body,
        on_drop,
        text="把文件或文件夹拖到这里",
        hint="松手就把路径写进上面那行",
        height=96,
    )
    zone.pack(fill="x", pady=(10, 0))

    hint_label(
        body,
        (
            "不用点按钮：文件、文件夹都能直接拖进来。拖放由可选依赖 tkinterdnd2 提供"
            if has_dnd()
            else "当前没装 tkinterdnd2，拖放不可用：pip install \"ctk-kit[dnd]\""
        ),
    ).pack(fill="x")
    _code_panel(
        body,
        DROP_CODE,
        "on_path 收到绝对路径；mode 用来只收文件或只收文件夹。",
    )

    # --- 下拉框 ---
    section_title(area, "下拉框 DropField")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    row = _row(body, bg)
    field_label(row, "普通").pack(side="left")
    DropField(
        row,
        values_provider=lambda: ["选项 A", "选项 B", "选项 C"],
        command=lambda value: feedback(f"下拉选中：{value}"),
        placeholder="点右侧箭头选择",
    ).pack(side="left", fill="x", expand=True)

    row = _row(body, bg)
    field_label(row, "空候选").pack(side="left")
    DropField(
        row,
        values_provider=lambda: [],
        placeholder="候选项为空，点箭头不会弹",
    ).pack(side="left", fill="x", expand=True)

    row = _row(body, bg)
    field_label(row, "预设值").pack(side="left")
    preset = DropField(
        row,
        values_provider=lambda: ["Alpha", "Beta", "Gamma"],
        placeholder="点右侧箭头选择",
    )
    preset.pack(side="left", fill="x", expand=True)
    preset.set("Alpha")
    preset_value = hint_label(body, "已选：Alpha")
    preset_value.pack(fill="x")
    preset.entry.bind(
        "<KeyRelease>",
        lambda _e: preset_value.configure(text=f"已选：{preset.get() or '（空）'}"),
    )
    hint_label(
        body, "get() / set() 与输入框一致；选中候选后回调 command(value)。"
    ).pack(fill="x")
    _code_panel(
        body,
        DROPDOWN_CODE,
        "values_provider 是函数而不是列表，数据变了下次展开就会生效。",
    )

    # --- 大文本 ---
    section_title(area, "大文本 TextArea")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    note = TextArea(
        body,
        placeholder="写备注、粘贴日志、贴长文本…",
        height=120,
        on_change=lambda text: feedback(f"备注当前 {len(text)} 字"),
    )
    note.pack(fill="x")
    hint_label(
        body, "placeholder 在失焦且为空时显示；on_change 收到最新全文。"
    ).pack(fill="x")

    row = _row(body, bg)
    field_label(row, "只读日志").pack(side="left")
    hint_label(row, "预设内容，不可编辑，可选中复制").pack(side="left", padx=(8, 0))

    log = TextArea(
        body, height=96, readonly=True, show_counter=False, bg_color=T.COLOR_CARD
    )
    log.set(
        "22:00  已连接\n"
        "22:01  同步 12 条记录\n"
        "22:02  完成，用时 1.4s"
    )
    log.pack(fill="x")
    hint_label(
        body,
        "readonly=True 时内部 state=disabled；set() 仍可写入，set_readonly() 可随时切换。",
    ).pack(fill="x")
    _code_panel(
        body,
        TEXT_CODE,
        "readonly 只是禁止编辑，选中与复制照常；show_counter=False 去掉右下角字数。",
    )

    return page


def main() -> int:
    return run_page(build, TITLE, height=860)


if __name__ == "__main__":
    raise SystemExit(main())
