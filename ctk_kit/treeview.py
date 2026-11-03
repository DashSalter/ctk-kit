"""树形表格：层级数据，点箭头展开 / 收起。

底层是 ``ttk.Treeview``（Tk 自带的树控件），配色和行高按 ctk-kit 的
tokens 调过，跟卡片、表格放在一起不突兀。主题切换后调
:meth:`TreeView.refresh_style` 重新取色。

用法::

    from ctk_kit import TreeView

    tree = TreeView(card, columns=("大小", "修改时间"), height=8)
    src = tree.insert("", "src", text="src", open=True)
    tree.insert(src, "main", text="main.py", values=("3.2 KB", "09:12"))
    tree.insert(src, "ui", text="ui.py", values=("8.4 KB", "09:30"))
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional, Sequence

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .layout import style_scrollbar
from .theme import color_of

try:  # Pillow 是可选依赖
    from PIL import Image, ImageDraw, ImageTk

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

__all__ = ["TreeView"]

SelectCommand = Optional[Callable[[tuple], None]]


def _mix(color: str, base: str, ratio: float) -> str:
    """把 ``color`` 按 ``ratio`` 混进 ``base``，得到柔和的选中底色。"""
    color = color.lstrip("#")
    base = base.lstrip("#")
    parts = []
    for i in (0, 2, 4):
        left = int(color[i : i + 2], 16)
        right = int(base[i : i + 2], 16)
        parts.append(f"{round(left * (1 - ratio) + right * ratio):02x}")
    return "#" + "".join(parts)


class TreeView(ctk.CTkFrame):
    """带表头的树形视图。

    参数:
        master: 父容器。
        columns: 除树列外的数据列名。
        height: 可见行数，默认 8。
        command: 选中行变化时的回调，参数是这一行的 values（元组）。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        insert(parent="", text="", values=(), iid=None, open=False): 插一行。
        delete(iid): 删一行（连同子节点）。
        clear(): 清空。
        get_selected(): 当前选中的 iid；没有选中时返回 ``None``。
        get_values(iid): 某一行的 values。
        expand_all() / collapse_all(): 全部展开 / 收起。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        columns: Sequence[str] = (),
        height: int = 8,
        command: SelectCommand = None,
        **kwargs: Any,
    ) -> None:
        """建树形视图；``columns`` 不含树列本身。"""
        super().__init__(
            master,
            fg_color=T.COLOR_CARD,
            corner_radius=0,
            border_width=0,
            **kwargs,
        )

        self._columns = list(columns)
        self._command = command
        self._style = ttk.Style(self)
        # 有 Pillow 就自己画实心三角，clam 自带的是细线空心三角，放大后很糊
        self._custom_indicator = _HAS_PIL
        self._arrow_open = None
        self._arrow_closed = None
        self._arrow_blank = None
        self._apply_style()

        self._tree = ttk.Treeview(
            self,
            columns=self._columns,
            show="tree headings",
            height=height,
            style="Ctk.Treeview",
            selectmode="browse",
        )
        self._scroll = ctk.CTkScrollbar(
            self, command=self._tree.yview, orientation="vertical"
        )
        style_scrollbar(self._scroll)
        self._tree.configure(yscrollcommand=self._scroll.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
        self._scroll.pack(side="right", fill="y", padx=(0, 1), pady=1)

        self._tree.heading("#0", text="名称", anchor="w")
        self._tree.column("#0", width=180, minwidth=80, anchor="w")
        for column in self._columns:
            self._tree.heading(column, text=column, anchor="w")
            self._tree.column(column, width=100, minwidth=60, anchor="w")

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<<TreeviewOpen>>", lambda _e: self._sync_rows(), add="+")
        self._tree.bind("<<TreeviewClose>>", lambda _e: self._sync_rows(), add="+")
        if self._custom_indicator:
            self._tree.bind("<Button-1>", self._on_click, add="+")
        self._make_arrows()
        self._style_rows()
        self._sync_rows()

    # --- 对外 ---
    def insert(
        self,
        parent: str = "",
        iid: Optional[str] = None,
        *,
        text: str = "",
        values: Sequence[Any] = (),
        open: bool = False,
    ) -> str:
        """插一行，返回它的 iid。``parent`` 是父节点的 iid，空串表示根。"""
        new_iid = self._tree.insert(
            parent,
            "end",
            iid=iid,
            text=text,
            values=tuple(values),
            open=open,
        )
        self._sync_rows()
        return new_iid

    def delete(self, iid: str) -> None:
        """删掉一行及其子节点。"""
        self._tree.delete(iid)
        self._sync_rows()

    def clear(self) -> None:
        """清空所有根节点。"""
        for item in self._tree.get_children(""):
            self._tree.delete(item)
        self._sync_rows()

    def get_selected(self) -> Optional[str]:
        """当前选中的 iid。"""
        selected = self._tree.selection()
        return selected[0] if selected else None

    def get_values(self, iid: str) -> tuple:
        """某一行的 values。"""
        return tuple(self._tree.item(iid, "values"))

    def expand_all(self) -> None:
        """全部展开。"""
        for iid in self._walk():
            self._tree.item(iid, open=True)
        self._sync_rows()

    def collapse_all(self) -> None:
        """全部收起（根节点保持展开，否则看不到子项）。"""
        for iid in self._walk():
            if self._tree.parent(iid) != "":
                self._tree.item(iid, open=False)
        self._sync_rows()

    def refresh_style(self) -> None:
        """重新按当前深浅色取色；切主题后调一下。"""
        self._apply_style()
        self._style_rows()
        self._make_arrows()
        self._sync_rows()

    # --- 内部 ---
    def _walk(self, parent: str = "") -> list:
        """深度优先列出所有节点。"""
        result = []
        for iid in self._tree.get_children(parent):
            result.append(iid)
            result.extend(self._walk(iid))
        return result

    def _make_arrows(self) -> None:
        """按当前缩放和主题重画实心三角。"""
        if not self._custom_indicator:
            return
        size = max(8, int(round(10 * self._scaling())))
        color = color_of(T.COLOR_MUTED)
        self._arrow_closed = self._arrow_photo(size, False, color)
        self._arrow_open = self._arrow_photo(size, True, color)
        self._arrow_blank = ImageTk.PhotoImage(
            Image.new("RGBA", (size, size), (0, 0, 0, 0))
        )

    def _arrow_photo(self, size: int, opened: bool, color: str):
        """4 倍超采样画一个实心三角，再 LANCZOS 缩到目标尺寸。"""
        scale = 4
        edge = size * scale
        pad = edge * 0.18
        image = Image.new("RGBA", (edge, edge), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        if opened:
            points = [(pad, pad), (edge - pad, pad), (edge / 2, edge - pad)]
        else:
            points = [(pad, pad), (pad, edge - pad), (edge - pad, edge / 2)]
        draw.polygon(points, fill=color)
        image = image.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(image)

    def _scaling(self) -> float:
        """当前屏幕缩放，用来把 10 逻辑像素换成物理像素。"""
        try:
            return self.winfo_fpixels("1i") / 96.0
        except tk.TclError:
            return 1.0

    def _sync_rows(self) -> None:
        """重排斑马纹，并按展开状态换上实心三角。"""
        self._restripe()
        if not self._custom_indicator:
            return
        for iid in self._walk():
            if self._tree.get_children(iid):
                opened = bool(self._tree.item(iid, "open"))
                image = self._arrow_open if opened else self._arrow_closed
            else:
                image = self._arrow_blank
            self._tree.item(iid, image=image)

    def _on_click(self, event: tk.Event) -> Optional[str]:
        """点三角时切换展开，不改变选中。"""
        if not self._custom_indicator:
            return None
        iid = self._tree.identify_row(event.y)
        if not iid:
            return None
        if self._tree.identify_region(event.x, event.y) != "tree":
            return None
        if self._tree.identify_element(event.x, event.y) != "image":
            return None
        if not self._tree.get_children(iid):
            return None
        opened = bool(self._tree.item(iid, "open"))
        self._tree.item(iid, open=not opened)
        self._sync_rows()
        return "break"

    def _style_rows(self) -> None:
        """隔行淡底色，和表格的斑马纹一致。"""
        self._tree.tag_configure("_odd", background=color_of(T.COLOR_HOVER_FAINT))

    def _restripe(self) -> None:
        """按可见行的顺序重新打隔行标签。"""
        index = 0

        def apply(parent: str) -> None:
            nonlocal index
            for iid in self._tree.get_children(parent):
                tags = [tag for tag in self._tree.item(iid, "tags") if tag != "_odd"]
                if index % 2 == 1:
                    tags.append("_odd")
                self._tree.item(iid, tags=tuple(tags))
                index += 1
                # 收起节点的子行不显示，不参与交替
                if self._tree.item(iid, "open"):
                    apply(iid)

        apply("")

    def _on_select(self, _event: tk.Event = None) -> None:
        """选中行变化时回调 values。"""
        if self._command is None:
            return
        iid = self.get_selected()
        if iid is not None:
            self._command(self.get_values(iid))

    def _apply_style(self) -> None:
        """把 ttk 的 Treeview / 滚动条配成 ctk 的配色。"""
        style = self._style
        try:
            # clam 才认 background / fieldbackground；vista 主题会忽略这些
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Ctk.Treeview",
            background=color_of(T.COLOR_CARD),
            fieldbackground=color_of(T.COLOR_CARD),
            foreground=color_of(T.COLOR_TEXT_SOFT),
            rowheight=40,
            borderwidth=0,
            relief="flat",
            font=get_font(T.FONT_TABLE),
        )
        # 选中用主色兑进卡片底，别拿满饱和的主色整行铺满；文字保持正文色。
        selected = _mix(
            color_of(T.COLOR_ACTIVE), color_of(T.COLOR_CARD), 0.82
        )
        style.map(
            "Ctk.Treeview",
            background=[("selected", selected)],
            foreground=[("selected", color_of(T.COLOR_TEXT))],
        )
        style.configure(
            "Ctk.Treeview.Heading",
            background=color_of(T.COLOR_SOFT),
            foreground=color_of(T.COLOR_MUTED),
            relief="flat",
            borderwidth=0,
            padding=(8, 10),
            font=get_font(T.FONT_TABLE_HEAD),
        )
        style.map(
            "Ctk.Treeview.Heading",
            background=[("active", color_of(T.COLOR_SOFT_HOVER))],
        )
        # clam 会给 Treeview 画一圈浅色外框，叠在卡片描边上显得又白又粗；
        # 只留内容区，外框交给外层 CTkFrame 的 1px border。
        try:
            style.layout("Ctk.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        except tk.TclError:
            pass

        # 默认 Item 自带细线空心三角；自己画的实心三角占用 Treeitem.image，
        # 所以把 indicator 从布局里去掉，只留图片 / 文字。
        if self._custom_indicator:
            try:
                style.layout(
                    "Ctk.Treeview.Item",
                    [
                        (
                            "Treeitem.padding",
                            {
                                "sticky": "nswe",
                                "children": [
                                    ("Treeitem.image", {"side": "left", "sticky": ""}),
                                    (
                                        "Treeitem.focus",
                                        {
                                            "side": "left",
                                            "sticky": "",
                                            "children": [
                                                (
                                                    "Treeitem.text",
                                                    {"side": "left", "sticky": ""},
                                                )
                                            ],
                                        },
                                    ),
                                ],
                            },
                        )
                    ],
                )
            except tk.TclError:
                pass
