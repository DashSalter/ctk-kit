# 表格与列表

![表格与列表](../assets/guide-table.png){ loading=lazy }

## 作用

展示「多条数据」的四个控件：表格、树、懒加载列表、页码条。

## Table

### 作用

带表头的表格，隔行淡底；超过 `max_visible_rows` 后滚动，也可以分页。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `columns` | `Sequence[(标题, 宽度, 对齐)]` | 必填 | 宽度传 `None` 表示吃掉剩余宽度 |
| `row_height` | `int` | `40` | 行高 |
| `max_visible_rows` | `int` | `8` | 最多显示几行 |
| `page_size` | `int` | `0` | 每页行数，大于 0 时出现分页条 |
| `empty_text` | `str` | `"暂无数据"` | 空数据提示 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `set_rows(rows)` | 整批替换数据 |
| `add_row(row)` | 追加一行 |
| `set_page(n)` | 跳页 |
| `pages()` / `page()` | 总页数 / 当前页 |

### 示例

```python
table = Table(
    card.body,
    [("名称", 220, "w"), ("大小", 90, "e"), ("时间", None, "e")],
    max_visible_rows=6,
)
table.set_rows([
    ["backup-01.zip", "12 MB", "2026-11-07 12:03"],
    ["backup-02.zip", "8 MB", "2026-11-06 22:41"],
])
table.pack(fill="x", padx=16, pady=(0, 12))
```

## TreeView

### 作用

带表头的树：节点可以展开 / 收起，每个节点还能带几列附加数据。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `columns` | `Sequence[str]` | `()` | 除树列之外的列标题 |
| `height` | `int` | `8` | 可见行数 |
| `command` | `Callable[[str], None]` | `None` | 选中回调，参数是 iid |

### 方法

| 方法 | 说明 |
| --- | --- |
| `insert(parent="", iid=None, *, text="", values=(), open=False)` | 插一行，返回 iid |
| `delete(iid)` | 删掉该行和子节点 |
| `clear()` | 清空 |
| `get_selected()` | 当前选中的 iid |
| `expand_all()` / `collapse_all()` | 全部展开 / 收起 |

### 示例

```python
tree = TreeView(card.body, columns=("大小", "类型"), height=6)
root = tree.insert(text="文档")
tree.insert(root, text="a.txt", values=("2 KB", "文本"))
tree.pack(fill="x", padx=16, pady=(0, 12))
```

## LazyList

### 作用

滚到底才继续建下一条的列表；一屏几百条也不卡，适合日志、搜索结果。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `render_card` | `Callable[[容器, 数据], 控件]` | 必填 | 往一个空容器里画一条，**返回这张卡的顶层控件**（由列表负责摆放） |
| `first_batch` | `int` | `12` | 首屏建几条 |
| `load_more` | `int` | `8` | 到底再建几条 |
| `load_threshold` | `float` | `0.92` | 滚到 92% 处开始续建 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `render(items)` | 重画列表 |
| `reset()` | 回到首屏 |
| `invalidate()` | 强制下次重建 |
| `show_hint(text)` | 空列表时显示一句提示 |

### 示例

```python
def render(box, item):
    return Label(box, item["name"])

records = [{"name": "第一条"}, {"name": "第二条"}]
lst = LazyList(card.body, render, first_batch=10)
lst.render(records)
lst.pack(fill="both", expand=True)
```

## Pagination

### 作用

`‹ 1 2 3 ›` 页码条；可以单独用，也可以和 `Table` 配合。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `total` | `int` | `0` | 总条数 |
| `page_size` | `int` | `10` | 每页条数 |
| `current` | `int` | `1` | 当前页 |
| `command` | `Callable[[int], None]` | `None` | 翻页回调 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `set_page(n)` | 跳页（超出范围会夹回） |
| `set_total(n)` | 改总条数 |
| `pages()` / `page()` | 总页数 / 当前页 |

### 示例

```python
pager = Pagination(card.body, total=128, page_size=10,
                   command=lambda p: load_page(p))
pager.pack(fill="x", padx=16, pady=(0, 12))
```
