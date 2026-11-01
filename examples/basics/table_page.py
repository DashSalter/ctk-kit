"""表格页：固定表头、隔行底色、超过可视行数后滚动，以及空态。

与 ``button_page.py`` / ``collapse_page.py`` 一样，页面拆成「UI 类 + 事件类」：
``TablePageUI`` 只建控件，``TablePage`` 在构造时自动 ``bind_events()``。
每张卡片底部都带一个「查看实现」折叠面板，展开就是对应代码。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    FieldLabel,
    Frame,
    HintLabel,
    PageBase,
    PageHeader,
    Scrollable,
    SecondaryButton,
    Table,
    TextArea,
    tokens as T,
    CodePanel,
)

#: 代码块字体：等宽，比正文大一点，展开后不用凑近看。
CODE_FONT = ("Consolas", 15)

CODE_TABLE = '''from ctk_kit import Table

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

CODE_EMPTY = '''table.set_rows([])
# 没有数据时内容区留两行高，居中显示 empty_text

table.set_rows(ROWS)
# max_visible_rows=4 时，4 行以内不会出现滚动条

table.rows()
# 返回当前数据的浅拷贝；改完再 set_rows 回去才会重绘'''

#: 主表格的列定义：(标题, 宽度, 对齐)；宽度为 None 的列吃掉剩余空间。
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

#: 空态演示用的小表格：3 列，最多同时看 4 行。
EMPTY_COLUMNS = [
    ("步骤", 180, "w"),
    ("结果", 90, "center"),
    ("备注", None, "w"),
]

EMPTY_ROWS = [
    ["读取配置", "通过", "config.json"],
    ["校验签名", "通过", "本地密钥"],
    ["写入缓存", "跳过", "缓存已存在"],
]


class TablePageUI(PageBase):
    """表格页 UI：只建控件，事件留给 TablePage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "表格")
        self.header.info.configure(text=f"{len(ROWS)} 行 × {len(COLUMNS)} 列")

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "点按钮改数据，回显会出现在这里")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_table(area)
        self._build_empty(area)

    def _build_table(self, area: tk.Misc) -> None:
        """固定表头 + 隔行底色 + 超行滚动。"""
        box = Card(area, title="固定表头与滚动")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.add_button = SecondaryButton(row, "追加一行")
        self.add_button.pack(side="left")
        self.clear_button = SecondaryButton(row, "清空")
        self.clear_button.pack(side="left", padx=(8, 0))
        self.restore_button = SecondaryButton(row, "恢复")
        self.restore_button.pack(side="left", padx=(8, 0))

        HintLabel(row, "超过 8 行时内容区可滚动，表头不动。").pack(side="right")

        table_row = Frame(box)
        table_row.pack(fill="x", padx=16, pady=(0, 8))

        self.table = Table(
            table_row,
            COLUMNS,
            row_height=36,
            header_height=38,
            max_visible_rows=8,
            striped=True,
            empty_text="暂无数据",
        )
        self.table.pack(fill="x")
        self.table.set_rows(ROWS)

        HintLabel(
            box,
            "最后一列宽度给 None，会吃掉剩余空间；奇数行铺一层淡底色。",
        ).pack(fill="x", padx=16, pady=(0, 8))

        CodePanel(
            box,
            CODE_TABLE,
            "columns 是三元组列表；宽度给 None 的那一列会自动撑满剩余空间。",
        )

    def _build_empty(self, area: tk.Misc) -> None:
        """空态：没有数据时只留两行高，居中显示 empty_text。"""
        box = Card(area, title="空态与少行")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "空表格", width=68).pack(side="left")
        HintLabel(row, "set_rows([]) 后内容区留两行高，居中显示 empty_text。").pack(
            side="left", padx=(8, 0)
        )

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))

        self.fill_button = SecondaryButton(row, "填入 3 行")
        self.fill_button.pack(side="left")
        self.empty_clear_button = SecondaryButton(row, "清空")
        self.empty_clear_button.pack(side="left", padx=(8, 0))

        HintLabel(row, "max_visible_rows=4：3 行时不出现滚动条。").pack(side="right")

        table_row = Frame(box)
        table_row.pack(fill="x", padx=16, pady=(0, 8))

        self.empty_table = Table(
            table_row,
            EMPTY_COLUMNS,
            max_visible_rows=4,
            empty_text="暂无数据",
        )
        self.empty_table.pack(fill="x")

        HintLabel(
            box,
            "空态和少行共用同一张表：数据变了调 set_rows 即可，不用重建控件。",
        ).pack(fill="x", padx=16, pady=(0, 8))

        CodePanel(
            box,
            CODE_EMPTY,
            "空态由 empty_text 决定；少行时高度会缩到实际行数，不会留一大块空白。",
        )

    def _sync_info(self) -> None:
        """把当前行数写回页头右侧。"""
        self.header.info.configure(text=f"{len(self.table.rows())} 行 × {len(COLUMNS)} 列")


class TablePage(TablePageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """必须实现：注册按钮和事件。"""
        self.add_button.configure(command=self._add_row)
        self.clear_button.configure(command=self._clear)
        self.restore_button.configure(command=self._restore)
        self.fill_button.configure(command=self._fill_empty)
        self.empty_clear_button.configure(command=self._clear_empty)

    def _add_row(self) -> None:
        """在主表格末尾追加一行，行数超过 8 就会长出滚动条。"""
        rows = self.table.rows()
        rows.append([f"新文件 {len(rows) + 1:02d}.dat", "正常", "刚刚", "0 KB"])
        self.table.set_rows(rows)
        self._sync_info()
        self._show(f"追加了一行，现在 {len(rows)} 行")

    def _clear(self) -> None:
        """清空主表格，露出表头和空态。"""
        self.table.set_rows([])
        self._sync_info()
        self._show("主表格已清空：表头保留，内容区显示「暂无数据」")

    def _restore(self) -> None:
        """恢复初始的 12 行。"""
        self.table.set_rows(ROWS)
        self._sync_info()
        self._show(f"恢复到初始的 {len(ROWS)} 行")

    def _fill_empty(self) -> None:
        """给空态表格填 3 行：不超过 4 行，所以没有滚动条。"""
        self.empty_table.set_rows(EMPTY_ROWS)
        self._show(f"空态表格填入了 {len(EMPTY_ROWS)} 行，未超过 4 行，不出现滚动条")

    def _clear_empty(self) -> None:
        """把空态表格清回 empty_text。"""
        self.empty_table.set_rows([])
        self._show("空态表格已清空，内容区重新显示 empty_text")

    def _show(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
