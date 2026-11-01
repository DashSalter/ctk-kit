"""表格页：带固定表头、隔行底色、滚动与空态。

单独启动：``python -m ctk_kit.showcase.pages.table``
"""

from __future__ import annotations

import customtkinter as ctk

from ctk_kit.buttons import SecondaryButton
from ctk_kit.layout import Card, HintLabel, PageHeader
from ctk_kit.table import Table

from ..shell import _card_body, _code_panel, run_page

TITLE = "表格"

CODE = '''from ctk_kit import Table

table = Table(
    frame,
    [
        ("名称", 240, "w"),      # (标题, 宽度, 对齐)
        ("状态", 96, "center"),  # 宽度是逻辑像素
        ("大小", None, "e"),     # None 表示吃掉剩余宽度
    ],
    row_height=36,
    header_height=38,
    max_visible_rows=8,   # 超过这个行数才出现滚动条
    striped=True,         # 隔行淡底色
    empty_text="暂无数据",
)
table.pack(fill="x")
table.set_rows([["配置文件", "正常", "12 KB"]])
table.rows()              # 取当前数据，单元格按 str() 转文本

# 表头固定不滚动；滚动条独占右侧一列，不压在内容上
# 对齐取 "w" / "center" / "e"'''

COLUMNS = [
    ("名称", 240, "w"),
    ("状态", 96, "center"),
    ("更新时间", 170, "w"),
    ("大小", None, "e"),
]

ROWS = [
    ["配置文件 config.json", "正常", "10-30 21:04", "12 KB"],
    ["密钥备份 keys.bak", "已归档", "10-29 18:32", "248 KB"],
    ["日志 app.log", "正常", "10-30 23:58", "3.4 MB"],
    ["缓存 cache.db", "过期", "10-21 09:12", "860 KB"],
    ["导出 report.xlsx", "正常", "10-28 14:05", "1.1 MB"],
    ["图片 photo-001.png", "正常", "10-27 11:40", "2.2 MB"],
    ["图片 photo-002.png", "正常", "10-27 11:41", "2.0 MB"],
    ["草稿 note.md", "草稿", "10-26 20:16", "4 KB"],
    ["归档 old-2025.zip", "已归档", "09-30 08:00", "74 MB"],
    ["安装包 setup.exe", "正常", "10-25 16:22", "58 MB"],
    ["说明 README.txt", "正常", "10-24 10:03", "2 KB"],
    ["临时 tmp.tmp", "过期", "10-20 07:31", "0 KB"],
]


def build(master) -> ctk.CTkFrame:
    """一页演示：固定表头 + 超过可视行数后滚动。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = PageHeader(page, TITLE)
    info.configure(text=f"{len(ROWS)} 行 × {len(COLUMNS)} 列")

    box = Card(page)
    box.pack(fill="x", pady=(14, 0))

    table = Table(box, COLUMNS, max_visible_rows=8)
    table.pack(fill="x", padx=16, pady=16)
    table.set_rows(ROWS)
    page.table = table

    bar = ctk.CTkFrame(page, fg_color="transparent")
    bar.pack(fill="x", pady=(12, 0))
    SecondaryButton(bar, "追加一行", lambda: add_row()).pack(side="left")
    SecondaryButton(bar, "清空", lambda: clear()).pack(side="left", padx=(8, 0))
    SecondaryButton(bar, "恢复", lambda: restore()).pack(side="left", padx=(8, 0))
    feedback = HintLabel(bar, "隔行有淡底色；超过 8 行时内容区可滚动，表头不动。")
    feedback.pack(side="right")

    def refresh() -> None:
        rows = table.rows()
        info.configure(text=f"{len(rows)} 行 × {len(COLUMNS)} 列")

    def add_row() -> None:
        rows = table.rows()
        rows.append([f"新文件 {len(rows) + 1:02d}.dat", "正常", "刚刚", "0 KB"])
        table.set_rows(rows)
        refresh()
        feedback.configure(text=f"追加了一行，现在 {len(rows)} 行")

    def clear() -> None:
        table.set_rows([])
        refresh()
        feedback.configure(text="清空后显示空态提示")

    def restore() -> None:
        table.set_rows(ROWS)
        refresh()
        feedback.configure(text="恢复到初始的 12 行")

    code_box = Card(page)
    code_box.pack(fill="x", pady=(12, 0))
    _code_panel(
        _card_body(code_box),
        CODE,
        "columns 是三元组列表；宽度给 None 的那一列会自动撑满剩余空间。",
    )

    return page


def main() -> int:
    return run_page(build, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
