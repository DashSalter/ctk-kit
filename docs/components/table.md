# 表格与列表

## 作用

四个展示「多条数据」的控件：

- `Table` —— 带固定表头的表格。列宽自适应、隔行底色、超过可视行数后滚动，可选分页。
- `TreeView` —— 带表头的树形视图，可以展开 / 收起节点。
- `LazyList` —— 竖向懒加载列表：滚到底部才继续建后面的项，一屏几百条也不卡。
- `Pagination` —— 页码条，可以和 `Table` 或 `LazyList` 配合。

## 类型

| 类型 | 外观 | 用在哪 |
| --- | --- | --- |
| `Table` | 表头 + 行，隔行淡底 | 备份列表、用户列表 |
| `TreeView` | 表头 + 可展开的树 | 目录、分类 |
| `LazyList` | 一列卡片 | 时间线式列表、搜索结果 |
| `Pagination` | `‹ 1 2 3 ›` | 表格 / 列表底部 |

## 参数

### Table

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `columns` | `Sequence[Sequence]` | 必填 | 每列是 `(标题, 宽度, 对齐)`；宽度 `None` 表示吃掉剩余宽度 |
| `row_height` | `int` | `40` | 行高 |
| `header_height` | `int` | `40` | 表头高 |
| `max_visible_rows` | `int` | `8` | 最多显示几行，超出后滚动 |
| `striped` | `bool` | `True` | 隔行淡底色 |
| `empty_text` | `str` | `"暂无数据"` | 空数据提示 |
| `page_size` | `int` | `0` | 每页行数；大于 0 时底部出现分页条 |

```python
table = ctk.Table(
    card.body(),
    [("名称", 200, "w"), ("大小", 90, "e"), ("时间", None, "e")],
    max_visible_rows=6,
)
table.set_rows([
    ["backup-01.zip", "12 MB", "2026-11-07 12:03"],
    ["backup-02.zip", "8 MB", "2026-11-06 22:41"],
])
table.pack(fill="x", padx=16, pady=(0, 12))
```

### TreeView

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `columns` | `Sequence[str]` | `()` | 除树列之外的各列表头 |
| `height` | `int` | `8` | 可见行数 |
| `command` | `Callable[[str], None]` | `None` | 选中回调，参数是 iid |

```python
tree = ctk.TreeView(card.body(), columns=("大小", "类型"), height=6)
root = tree.insert(text="文档")
tree.insert(root, text="a.txt", values=("2 KB", "文本"))
```

### LazyList

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `render_card` | `Callable[[tk.Misc, Any], None]` | 必填 | 往一个空容器里画一条 |
| `key_of` | `Callable[[Any], str] \| None` | `None` | 从数据取唯一键，用于复用 |
| `first_batch` | `int` | `12` | 首屏建几条 |
| `load_more` | `int` | `8` | 滚到底再建几条 |
| `load_delay_ms` | `int` | `90` | 续建前的延迟，避免滚动中卡顿 |
| `load_threshold` | `float` | `0.92` | 滚到 92% 处开始续建 |
| `gap` | `(int, int)` | `(0, 10)` | 卡片之间的上下间距 |
| `padx` | `(int, int)` | `(0, 8)` | 左右内边距 |
| `item_height` | `int \| None` | `None` | 固定项高时传入，滚动条计算更准 |

```python
def render(box, item):
    card = ctk.Frame(box)
    card.pack(fill="x")
    ctk.Label(card, item["name"]).pack(side="left", padx=8)

lst = ctk.LazyList(card.body(), render, first_batch=10)
lst.render(items)
lst.pack(fill="both", expand=True)
```

### Pagination

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `total` | `int` | `0` | 总条数 |
| `page_size` | `int` | `10` | 每页条数 |
| `current` | `int` | `1` | 当前页码 |
| `command` | `Callable[[int], None]` | `None` | 翻页回调，参数是新页码 |
| `siblings` | `int` | `1` | 当前页两侧各显示几个页码 |
| `show_total` | `bool` | `False` | 是否显示总条数 |

```python
pager = ctk.Pagination(card.row(2), total=128, page_size=10, current=1,
                       command=lambda p: print("翻到", p))
pager.pack(fill="x", padx=16)
```

## 方法

### Table

| 方法 | 说明 |
| --- | --- |
| `set_rows(rows)` | 整批替换数据（分页时也传全量） |
| `add_row(row)` | 末尾追加一行 |
| `remove_row(index)` | 删除指定下标 |
| `rows()` | 全部数据的浅拷贝 |
| `set_page(n)` | 跳到某页；不分页时什么也不做 |
| `set_page_size(n)` | 改每页行数；传 `0` 关闭分页 |
| `pages()` / `page()` / `page_size()` | 总页数 / 当前页 / 每页行数 |

```python
table.set_rows(data)
table.add_row(["backup-03.zip", "4 MB", "2026-11-07 13:20"])
table.set_page(2)
print(table.pages(), table.page())
```

### TreeView

| 方法 | 说明 |
| --- | --- |
| `insert(parent="", iid=None, *, text="", values=(), open=False)` | 插一行，返回 iid |
| `delete(iid)` | 删掉该行及子节点 |
| `clear()` | 清空所有根节点 |
| `get_selected()` | 当前选中的 iid |
| `get_values(iid)` | 某一行的 values |
| `expand_all()` / `collapse_all()` | 全部展开 / 收起 |
| `refresh_style()` | 按当前深浅色重新取色 |

```python
iid = tree.insert("", text="图片", open=True)
tree.insert(iid, text="a.png", values=("120 KB", "PNG"))
print(tree.get_values(iid))
tree.expand_all()
```

### LazyList

| 方法 | 说明 |
| --- | --- |
| `render(items)` | 重画列表；数据没变时直接返回 |
| `show_hint(text)` | 只显示一条提示（空列表时） |
| `invalidate()` | 丢掉缓存标记，下次 `render` 一定重建 |
| `cards()` | 当前已建出的卡片（副本） |
| `flush()` | 一次性补齐所有卡片 |
| `reset()` | 回到首屏，只留 `first_batch` 张 |
| `scroll_units(steps)` | 按行滚动，正数向下 |

```python
lst.render(filtered)
lst.reset()
lst.scroll_units(3)
```

### Pagination

| 方法 / 属性 | 说明 |
| --- | --- |
| `set_page(n)` | 跳页，超出范围会夹到首 / 末页 |
| `set_total(n)` | 改总条数；当前页超出时退到最后一页 |
| `set_page_size(n)` | 改每页条数；同上 |
| `pages()` / `page()` | 总页数 / 当前页 |

```python
pager.set_total(256)
pager.set_page_size(20)
print(pager.pages(), pager.page())
```

## 完整示例

```python
import ctk_kit as ctk

ROWS = [
    [f"backup-{i:02d}.zip", f"{i * 3} MB", f"2026-11-{i:02d} 12:03"]
    for i in range(1, 13)
]

app = ctk.App(title="表格示例", size=(760, 560))

card = ctk.Card(app, title="备份")
card.pack(fill="x", padx=24, pady=24)

table = ctk.Table(
    card.body(),
    [("名称", 220, "w"), ("大小", 90, "e"), ("时间", None, "e")],
    max_visible_rows=6,
)
table.set_rows(ROWS)
table.pack(fill="x", padx=16, pady=(0, 8))

pager = ctk.Pagination(card.body(), total=len(ROWS), page_size=6, current=1,
                       command=lambda p: print("翻到第", p))
pager.pack(fill="x", padx=16, pady=(0, 12))

app.mainloop()
```

## 换色

表头用 `COLOR_SOFT`，隔行底色是卡片色压一档，文字 `COLOR_TEXT` / `COLOR_MUTED`，
选中行用 `COLOR_ACCENT`：

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_SOFT": "#242731"})     # 表头、斑马纹
theming.apply_palette({"COLOR_ACCENT": "#f97316"})   # 分页当前页、选中行
```

`TreeView` 换色后需要调一次 `refresh_style()`（`ttk.Treeview` 的样式不走令牌重绘）。
