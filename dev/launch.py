"""快速启动一个示例页，省得每次都敲完整的模块路径。

用法::

    run 按钮                # 只看按钮页
    run notify --topmost    # 英文模块名也行，后面的参数原样透传
    run 3                   # 用序号也行
    run list                # 列出所有页面
    run                     # 不带参数：弹出页面选择器，点一下即打开

这里的 ``run`` 指仓库根目录的 ``run.bat``：它会自动切到仓库根目录，
并优先使用 ``.venv`` 里的解释器；装好环境后也可以直接
``python dev/launch.py 按钮``。

页面在子进程里启动，所以关掉页面窗口就回到命令行，不会把这里的进程
一起带走；``--where`` 这类参数也照常生效。
"""

from __future__ import annotations

import subprocess
import sys
from typing import List, Optional

# 顺序与侧边栏一致：序号从 1 开始。
PAGES = (
    ("overview", "总览"),
    ("foundation", "基件"),
    ("buttons", "按钮"),
    ("inputs", "输入"),
    ("layout", "布局"),
    ("notify", "提示"),
    ("listing", "列表"),
    ("theme", "主题"),
    ("form", "表单"),
    ("settings", "设置"),
)

_MODULES = {module for module, _ in PAGES}
_TITLES = {title: module for module, title in PAGES}
_INDEXES = {str(index): module for index, (module, _) in enumerate(PAGES, start=1)}


def resolve(word: str) -> Optional[str]:
    """把页名、模块名或序号换成模块名；认不出来返回 ``None``。"""
    word = word.strip()
    if word in _MODULES:
        return word
    if word in _TITLES:
        return _TITLES[word]
    if word in _INDEXES:
        return _INDEXES[word]
    return None


def list_pages() -> None:
    """打印可用页面。"""
    print("可用页面：")
    for index, (module, title) in enumerate(PAGES, start=1):
        print("  {:>2}. {:<4} {}".format(index, title, module))
    print()
    print("用法：run 按钮   |   run notify --topmost   |   run 3   |   run list")


def launch(module: str, extra: List[str]) -> int:
    """在子进程里启动某一页，返回它的退出码。"""
    command = [sys.executable, "-m", "ctk_kit.showcase.pages." + module]
    command.extend(extra)
    print("$ " + " ".join(command))
    return subprocess.call(command)


def choose() -> Optional[str]:
    """弹出页面选择器；没有图形环境时返回 ``None``，由调用方打印清单。"""
    try:
        import customtkinter as ctk

        from ctk_kit import tokens as T
        from ctk_kit.buttons import soft_button
        from ctk_kit.layout import hint_label, page_header
        from ctk_kit.theme import apply_appearance
    except Exception:  # noqa: BLE001 - 没有 ctk 或没有图形环境
        return None

    try:
        apply_appearance("dark")
        app = ctk.CTk()
    except Exception:  # noqa: BLE001 - 连窗口都建不出来
        return None

    app.title("ctk-kit · 选一个页面")
    app.configure(fg_color=T.COLOR_BG)
    width, height = 520, 400
    app.update_idletasks()
    left = max(0, (app.winfo_screenwidth() - width) // 2)
    top = max(0, (app.winfo_screenheight() - height) // 2)
    app.geometry("{}x{}+{}+{}".format(width, height, left, top))

    body = ctk.CTkFrame(app, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=20, pady=16)
    _, info = page_header(body, "选一个页面")
    info.configure(text="点一下即打开")

    grid = ctk.CTkFrame(body, fg_color="transparent")
    grid.pack(fill="both", expand=True, pady=(12, 0))

    picked = {"module": None}

    def pick(module: str) -> None:
        picked["module"] = module
        app.destroy()

    for index, (module, title) in enumerate(PAGES):
        button = soft_button(grid, title, lambda m=module: pick(m), width=120, height=34)
        button.grid(row=index // 3, column=index % 3, padx=6, pady=6, sticky="ew")
    for column in range(3):
        grid.grid_columnconfigure(column, weight=1)

    hint_label(body, "Esc 关闭").pack(anchor="w", pady=(10, 0))
    app.bind("<Escape>", lambda event: app.destroy())
    app.protocol("WM_DELETE_WINDOW", app.destroy)
    app.mainloop()
    return picked["module"]


def main(argv: List[str]) -> int:
    if not argv:
        module = choose()
        if module is None:
            list_pages()
            return 0
        return launch(module, [])

    head, extra = argv[0], argv[1:]
    if head in ("list", "ls", "-l", "--list", "?"):
        list_pages()
        return 0

    module = resolve(head)
    if module is None:
        print("没有叫 {!r} 的页面。".format(head))
        print()
        list_pages()
        return 2
    return launch(module, extra)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
