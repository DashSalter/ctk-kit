"""菜单页：一行代码给按钮挂右键菜单，回调能拿到被点的控件。

单独启动：``python -m ctk_kit.showcase.pages.menu``
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.buttons import DangerButton, PrimaryButton, SecondaryButton
from ctk_kit.context_menu import ContextMenu, attach_menu
from ctk_kit.layout import HintLabel, PageHeader, Scrollable, SectionTitle
from ctk_kit.text import TextArea
from ctk_kit.theme import color_of

from ..shell import _card_body, _card_shell, _code_panel, _feedback, _row, run_page

TITLE = "菜单"

SAMPLE_CODE = '''\
from ctk_kit import attach_menu, PrimaryButton


def on_edit(button):           # 第一个参数就是被右键的按钮
    print("编辑", button.cget("text"))


def on_delete(button, name):   # 额外传参用 lambda 收住
    print("删除", name, button.cget("text"))


save = PrimaryButton(page, "保存")
save.pack(side="left")

# 一行挂上菜单：文字配函数，函数可无参，也可接一个参数
attach_menu(save, [
    ("编辑", on_edit),
    ("删除", lambda btn: on_delete(btn, "草稿 A")),
])

# 想自己控制弹出时机，就直接用 ContextMenu
menu = ContextMenu(page)
menu.add_command("重新加载", reload)

def open_menu(event):
    menu.show(event.x_root, event.y_root, source=event.widget)
    return "break"
'''


def _copy(text: str, root: tk.Misc) -> None:
    root.clipboard_clear()
    root.clipboard_append(text)


def build(master) -> ctk.CTkFrame:
    """给按钮挂菜单、回调拿按钮、自己弹菜单，三段演示加示例代码。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = PageHeader(page, TITLE)
    info.configure(text="右键任意按钮")

    feedback = _feedback(page, "右键上面那些按钮，菜单会出现在鼠标位置。")

    area = Scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    # ---------------------------------------------------------------- 挂菜单
    SectionTitle(area, "一行代码挂上菜单")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)

    def on_rename(button: tk.Misc) -> None:
        feedback(f"「重命名」来自按钮：{button.cget('text')}")

    def on_delete(button: tk.Misc, extra: str) -> None:
        feedback(f"「删除」来自按钮：{button.cget('text')}，附带的参数：{extra}")

    files = ["配置文件.json", "日志 app.log", "草稿 note.md"]
    menus = []
    for index, name in enumerate(files):
        factory = (PrimaryButton, SecondaryButton, DangerButton)[index % 3]
        button = factory(row, name, lambda n=name: feedback(f"左键点了「{n}」"))
        button.pack(side="left", padx=(0 if index == 0 else 8, 0))
        menus.append(
            attach_menu(
                button,
                [
                    (
                        "复制名称",
                        lambda btn: (
                            _copy(str(btn.cget("text")), page),
                            feedback(f"已复制：{btn.cget('text')}"),
                        ),
                    ),
                    ("重命名", on_rename),
                    ("删除", lambda btn, n=name: on_delete(btn, n)),
                ],
            )
        )
    page.menus = menus

    HintLabel(
        body,
        "attach_menu(按钮, [(文字, 函数), ...])：函数接一个参数时，拿到的就是被右键的按钮。",
    ).pack(fill="x", pady=(4, 0))

    # ---------------------------------------------------------------- 回调参数
    SectionTitle(area, "回调拿到的第一个参数")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    target = SecondaryButton(row, "点我右键", lambda: feedback("左键点了「点我右键」"))
    target.pack(side="left")
    HintLabel(
        body,
        "菜单里的每个函数都拿到这个按钮对象，可以读它的文字、改它的状态；"
        "需要更多参数就用 lambda btn: fn(btn, 别的)。",
    ).pack(fill="x", pady=(4, 0))

    def read_text(button: tk.Misc) -> None:
        feedback(f"按钮文字是「{button.cget('text')}」，类型 {type(button).__name__}")

    def add_mark(button: tk.Misc) -> None:
        button.configure(text="已标记 ✓")
        feedback("这一项改的就是按钮自己的文字，所以菜单里能直接操作被点的控件")

    def reset_mark(button: tk.Misc) -> None:
        button.configure(text="点我右键")
        feedback("文字已改回去")

    attach_menu(
        target,
        [("读我的文字", read_text), ("把我标成已标记", add_mark), ("恢复原样", reset_mark)],
    )

    # ---------------------------------------------------------------- 自己弹
    SectionTitle(area, "自己控制弹出时机")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    zone = ctk.CTkFrame(body, fg_color=T.COLOR_SOFT, corner_radius=T.RADIUS_MEDIUM)
    zone.pack(fill="x", pady=(0, 8))
    HintLabel(zone, "这一整块都可以右键，菜单由 ContextMenu 手动弹出").pack(
        padx=16, pady=14
    )

    # deep=True：连容器里的文字一起挂，右键落在文字上也能弹
    attach_menu(
        zone,
        [
            ("复制提示文字", lambda: feedback("复制了提示文字")),
            ("", None),
            ("关闭菜单", lambda: feedback("菜单项执行完了")),
        ],
        deep=True,
    )
    HintLabel(
        body,
        "attach_menu(控件, [...], deep=True)：菜单项、分隔线、弹出位置都自己说了算。",
    ).pack(fill="x")

    # ---------------------------------------------------------------- 示例代码
    SectionTitle(area, "示例代码")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    _code_panel(
        body,
        SAMPLE_CODE,
        "回调接一个参数时拿到的就是被右键的控件；额外传参用 lambda 包一层。",
    )

    return page


def main() -> int:
    return run_page(build, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
