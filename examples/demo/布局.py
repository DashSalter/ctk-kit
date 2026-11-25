"""布局示例：两个标签页，只演示最常用的 pack 和 grid。

- 一维排列（横排、竖排）用 pack，靠 ``side`` / ``fill`` / ``expand``；
- 二维对齐、按比例分空间用 grid，先配 ``weight``，再用 ``sticky`` 贴住格子。

每个标签页一个 ``build_xxx(page)`` 函数，加页面只写一个函数、再挂到 ``Tabs`` 上。
"""

import ctk_kit as ctk
from ctk_kit import tokens as T

app = ctk.App(title="布局示例", size=(980, 720), min_size=(840, 620))

tabs = ctk.Tabs(app, values=["pack 一维排列", "grid 网格"], height=560)
tabs.pack(fill="both", expand=True, padx=24, pady=24)


def block(master, text: str, *, height: int = 0, color: str = T.COLOR_SOFT):
    """一块带文字的灰底区域，方便看清布局把空间分给了谁。"""
    frame = ctk.CTkFrame(master, fg_color=color, corner_radius=T.RADIUS_SMALL)
    if height:
        frame.configure(height=height)
        frame.pack_propagate(False)
    ctk.Label(frame, text=text, text_color=T.COLOR_MUTED).pack(expand=True)
    return frame


def build_pack(page) -> None:
    """pack：一行左右排、左右分栏、上下三段。"""
    bar = ctk.Frame(page).pack(fill="x")

    ctk.PrimaryButton(bar, "新建").pack(side="left")
    ctk.SecondaryButton(bar, "导入").pack(side="left", padx=(8, 0))
    ctk.SecondaryButton(bar, "设置").pack(side="right")

    ctk.divider(page, pady=(12, 12))

    body = ctk.Frame(page)
    body.pack(fill="both", expand=True)

    # 左边固定 140；关掉 propagate 之后 width 才不会被内容顶开
    side = block(body, "侧栏\n固定 140")
    side.configure(width=140)
    side.pack(side="left", fill="y")
    side.pack_propagate(False)

    content = ctk.Frame(body)
    content.pack(side="left", fill="both", expand=True, padx=(12, 0))

    # 上 / 中 / 下：只有中间 expand，窗口变高时长的是中间
    block(content, "顶栏", height=40).pack(fill="x")
    block(content, "中间内容（fill=both, expand=True）").pack(fill="both", expand=True, pady=8)
    block(content, "底栏", height=36).pack(fill="x")


def build_grid(page) -> None:
    """grid：三列按权重分宽、sticky 贴满、columnspan 跨列。"""
    for column, weight in enumerate((1, 2, 1)):
        page.grid_columnconfigure(column, weight=weight)
    for row in (0, 1):
        page.grid_rowconfigure(row, weight=1)

    def cell(text: str, row: int, column: int, **options) -> None:
        """把一块灰底放进指定格子，统一 ``sticky="nsew"`` 贴满。"""
        block(page, text).grid(row=row, column=column, sticky="nsew", **options)

    cell("第 1 列\nweight=1", 0, 0, padx=(0, 6), pady=(0, 6))
    cell("第 2 列\nweight=2", 0, 1, padx=6, pady=(0, 6))
    cell("第 3 列\nweight=1", 0, 2, padx=(6, 0), pady=(0, 6))
    # columnspan 跨列；rowspan 同理，只是换方向
    cell("跨第 1-2 列（columnspan=2）", 1, 0, columnspan=2, padx=(0, 6), pady=(6, 0))
    cell("右下角\n（靠 sticky 贴满）", 1, 2, padx=(6, 0), pady=(6, 0))


build_pack(tabs.tab("pack 一维排列"))
build_grid(tabs.tab("grid 网格"))

app.mainloop()
