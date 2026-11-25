"""带增删改的表格：把「右键菜单 + 编辑窗 + 刷新」这套重复代码收进一个控件。

```python
members = [["陈一", "产品", "产品经理", "chenyi@example.com"]]
table = CrudTable(
    page,
    columns=[("姓名", 130), ("部门", 140), ("角色", 160), ("邮箱", None)],
    rows=members,
    new_row=["新成员", "", "", ""],
)
table.pack(fill="both", expand=True)
```

左键选中一行，右键弹出「向上添加 / 向下添加 / 编辑 / 删除」。添加先弹编辑窗，
点「保存」才真正插入；取消不会改数据。第一列（第一个字段）不能为空。
"""

from __future__ import annotations

from typing import Any, Callable, Iterator, Optional, Protocol, Sequence

import customtkinter as ctk

from . import tokens as T
from .buttons import PrimaryButton, SecondaryButton
from .context_menu import ContextMenu
from .dialog import ChildWindow, confirm
from .inputs import CTkEntry
from .layout import Label, Row
from .table import Table


class _Rows(Protocol):
    """增删改需要的最小列表接口。

    普通 ``list`` 和 ``conf_base`` 的 ``ListProxy`` 都满足；后者每次写入都会
    直接落到配置文件，所以可以直接把配置项传给 ``rows``。
    """

    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> Any: ...
    def __setitem__(self, index: int, value: Any) -> None: ...
    def __delitem__(self, index: int) -> None: ...
    def insert(self, index: int, value: Any) -> None: ...
    def __iter__(self) -> Iterator[Any]: ...


class CrudTable(ctk.CTkFrame):
    """表格 + 右键增删改；``rows`` 就是你的数据 list，内部直接修改它。"""

    def __init__(
        self,
        master: Any,
        *,
        columns: Sequence[tuple],
        rows: Optional[_Rows] = None,
        new_row: Optional[Sequence[str]] = None,
        max_visible_rows: int = 10,
        empty_text: str = "暂无数据",
        on_change: Optional[Callable[[_Rows], None]] = None,
        **kwargs: Any,
    ) -> None:
        """建表格和右键菜单。

        参数:
            columns: 列定义 ``(标题, 宽度, 对齐)``，与 :class:`Table` 相同；
                表单也按这些标题生成字段。宽度可写 ``None`` 吃掉剩余空间。
            rows: 二维数据，控件直接读写这个对象、不复制。可以传普通 ``list``，
                也可以传 ``conf_base`` 的 ``ListProxy``（增删改会立即落盘）。
            new_row: 点「添加」时编辑窗的初始值；默认全部为空字符串。
            max_visible_rows / empty_text: 透传给 :class:`Table`。
            on_change: 添加、编辑、删除成功后回调，参数是 ``rows`` 本身。
            **kwargs: 其余参数交给 ``CTkFrame``。
        """
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._titles = [column[0] for column in columns]
        self._rows = rows if rows is not None else []
        self._new_row = list(new_row) if new_row is not None else [""] * len(columns)
        if len(self._new_row) != len(self._titles):
            raise ValueError("new_row 的字段数量要和 columns 一致")
        self._on_change = on_change

        self.table = Table(
            self,
            columns=columns,
            max_visible_rows=max_visible_rows,
            empty_text=empty_text,
        )
        self.table.pack(fill="both", expand=True)

        self._menu = ContextMenu(self.table, width=120)

        def has_row(_source: Any) -> bool:
            """只有选中行时，添加/编辑/删除才可点。"""
            return self.table.get_selected() is not None

        self._menu.add_command("向上添加", lambda: self._add(-1), enabled=has_row)
        self._menu.add_command("向下添加", lambda: self._add(1))
        self._menu.add_separator()
        self._menu.add_command("编辑", self._edit, enabled=has_row)
        self._menu.add_command("删除", self._remove, enabled=has_row)
        self.table._canvas.bind("<Button-3>", self._on_right_click, add="+")

        self.refresh()

    # ------------------------------------------------------------ 对外
    def set_rows(self, rows: _Rows) -> None:
        """换一份数据并重画；之后增删改都作用在这份新数据上。"""
        self._rows = rows
        self.refresh()

    def refresh(self, select_index: Optional[int] = None) -> None:
        """按 ``rows`` 重画表格，可顺便选中某一行。"""
        self.table.set_rows(list(self._rows))
        self.table.select(select_index)

    def row_count(self) -> int:
        """当前数据一共有多少行。"""
        return len(self._rows)

    def rows(self) -> list[list[str]]:
        """全部数据的文本副本；分页时也是全量，不是当前页。

        复制后再改不会影响表格；要改数据请走增删改或 :meth:`set_rows`。
        """
        return self.table.rows()

    # ------------------------------------------------------------ 内部
    def _on_right_click(self, event: Any) -> str:
        """右键落在行上先选中；空表时也允许在空白处右键添加。"""
        index = self.table.row_at(event.y)
        if index is None and self._rows:
            return "break"
        self.table.select(index)
        self._menu.show(*self.table.winfo_pointerxy(), source=self.table)
        return "break"

    def _add(self, offset: int) -> None:
        """打开空白编辑窗；确认后才插入到选中行上方 / 下方（或末尾）。"""
        index = self.table.get_selected()
        target = 0 if index is None else (index if offset < 0 else index + 1)
        self._open_form(None, target)

    def _edit(self) -> None:
        """编辑当前选中行。"""
        index = self.table.get_selected()
        if index is not None:
            self._open_form(index, None)

    def _remove(self) -> None:
        """删除当前选中行，先确认。"""
        index = self.table.get_selected()
        if index is None:
            return
        first = self._rows[index][0] if self._rows[index] else ""
        if not confirm(
            self,
            f"确定删除「{first}」吗？",
            title="删除",
            ok="删除",
            danger=True,
        ):
            return
        del self._rows[index]
        self.table.remove_row(index)
        self._changed()

    def _changed(self) -> None:
        """数据变了：回调业务方。"""
        if self._on_change is not None:
            self._on_change(self._rows)

    def _open_form(self, index: Optional[int], insert_at: Optional[int]) -> None:
        """编辑窗：``index`` 为 None 表示新增，保存后插到 ``insert_at``。"""
        editing = index is not None
        current = self._rows[index] if editing else self._new_row
        win = ChildWindow(
            self,
            title="编辑" if editing else "添加",
            width=430,
            height=150 + 46 * len(self._titles),
            modal=True,
        )
        form = ctk.CTkFrame(win, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=18, pady=(16, 0))

        entries = []
        for column, title in enumerate(self._titles):
            row = Row(form)
            row.pack(fill="x", pady=5)
            entry = CTkEntry(row.label(title, width=56), placeholder=f"输入{title}")
            entry.pack(fill="x")
            entry.insert(0, str(current[column]))
            entries.append(entry)

        error = Label(form, "", text_color=T.COLOR_DANGER)
        error.pack(fill="x", pady=(4, 0))

        footer = ctk.CTkFrame(win, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=14)
        PrimaryButton(footer, "保存", width=88, command=lambda: save()).pack(side="right")
        SecondaryButton(footer, "取消", width=88, command=win.close).pack(
            side="right", padx=(0, 8)
        )

        def save() -> None:
            """校验首列非空后写回数据，刷新并选中对应行。"""
            values = [entry.get().strip() for entry in entries]
            if not values[0]:
                error.set_text(f"{self._titles[0]}不能为空")
                return
            if editing:
                self._rows[index] = values
                self.table.update_row(index, values)
                target = index
            else:
                self._rows.insert(insert_at, values)
                self.table.insert_row(insert_at, values)
                target = insert_at
            win.close()
            self.table.select(target)
            self._changed()

        win.show()
