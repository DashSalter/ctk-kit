# 下拉选择

![下拉](../assets/guide-dropdowns.png){ loading=lazy }

## 作用

四个「点开再选」的控件：普通下拉、多标签选择、树形选择、左右加减的步进器。

> 取值型控件统一用 `get()` 读、`set(...)` 写。

## DropField

### 作用

点击展开一个下拉面板，选中后写回输入框；面板底部还可以放自定义按钮。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `values` | `Sequence[str]` | `None` | 静态候选，构造时读一次；与 `values_provider` 二选一 |
| `values_provider` | `Callable[[], Sequence]` | `None` | 返回候选的函数，**每次展开都会重新调用**，拿最新数据；与 `values` 二选一（都传时 `values` 优先） |
| `tags` | `Mapping[str, Sequence[str]]` | `None` | 静态「候选 → 标签列表」字典，只影响显示 |
| `tags_provider` | `Callable[[str], Sequence[str]]` | `None` | 按候选实时返回标签；`tags` 里查不到的才调用它 |
| `placeholder` | `str` | `""` | 占位文字 |
| `height` | `int` | `36` | 高度 |
| `command` | `Callable[[Any], None]` | `None` | 选中回调 |
| `disabled` | `Sequence` | `None` | 初始就置灰的项 |
| `readonly` | `bool` | `False` | 只读时点不开 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `set(value)` / `get()` | 写 / 读当前值 |
| `get_tags(value)` / `get_current_tags()` | 读某个候选 / 当前值的标签列表 |
| `set_tag(value, tags)` | 单独设置某一行的标签 |
| `set_tags(mapping)` / `clear_tags()` | 整体替换 / 清空标签 |
| `set_values(values)` | 换候选项 |
| `open_menu()` / `close_menu()` | 手动开 / 关面板 |
| `disable(item)` / `enable(item)` | 禁用 / 恢复某一项 |
| `get_disabled()` / `clear_disabled()` | 读 / 清空被禁用的项 |

### 示例

```python
# values_provider 每次展开都会重新调用，这里返回什么，列表就显示什么
field = DropField(card.body, values_provider=lambda: ["每天", "每周", "每月"])
field.set("每周")
field.pack(fill="x", padx=16, pady=(0, 12))

field.disable("每月")            # 这一项变灰不可选
field.set("每天")
```

候选行右侧也可以带标签：`tags` 是「候选 → 标签列表」的字典，只影响显示，`get()` 仍然只返回值本身。

```python
files = DropField(
    card.body,
    values=["报告.pdf", "数据.xlsx", "照片.png"],
    tags={
        "报告.pdf": ["1.2 MB", "PDF"],
        "数据.xlsx": ["3.4 MB", "Excel"],
    },
)
files.get()                    # "报告.pdf"
files.get_tags("报告.pdf")      # ["1.2 MB", "PDF"]
files.get_current_tags()       # 当前选中项的标签
files.set_tag("照片.png", ["860 KB", "PNG"])   # 单独补一行的标签
```

## TagSelectField

### 作用

多选：选项以标签形式排列，选中的标签亮起，值是选中标签组成的列表。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `values_provider` | `Callable[[], Sequence[str]]` | 必填 | 返回全部标签；每次展开重新调用 |
| `values` | `Sequence[str]` | `None` | 初始选中的标签 |
| `command` | `Callable[[list], None]` | `None` | 选中变化回调 |
| `disabled` | `Sequence[str]` | `None` | 初始就置灰的标签 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `get()` / `set(list)` | 读 / 写选中的标签（等价于 `get()` / `set()`） |
| `disable(tag)` / `enable(tag)` | 置灰 / 恢复某一项 |
| `get_disabled()` / `clear_disabled()` | 读 / 清空被禁用的项 |

### 示例

```python
tags = TagSelectField(
    card.body,
    values_provider=lambda: ["前端", "后端", "设计"],
    values=["前端"],
)
tags.pack(fill="x", padx=16, pady=(0, 12))
print(tags.get())        # ['前端']
```

## TreeSelectField

### 作用

树形下拉：适合「省 → 市 → 区」这种层级，点父节点展开。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `values_provider` | `Callable[[], Sequence]` | 必填 | 返回整棵树；元素是 `"叶子"` 或 `("分组", [子项...])` |
| `value` | `str` | `""` | 初始选中的节点标题 |
| `command` | `Callable[[str], None]` | `None` | 选中回调 |
| `disabled` | `Sequence[str]` | `None` | 初始就置灰的叶节点 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `get()` / `set(title)` | 读 / 写选中值（等价于 `get()` / `set()`） |
| `disable(title)` / `enable(title)` | 置灰 / 恢复某个叶节点 |

### 示例

```python
tree = TreeSelectField(card.body, values_provider=lambda: [
    ("浙江", [("杭州", [("西湖区", [])]), ("宁波", [])]),
    ("江苏", [("南京", [])]),
])
tree.pack(fill="x", padx=16, pady=(0, 12))
```

## Stepper

### 作用

`− 70% +` 这样的左右步进器，点击两端加减一步，也可以直接改中间的数值。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `from_` | `float` | `0` | 最小值 |
| `to` | `float` | `100` | 最大值 |
| `increment` | `float` | `1` | 步长 |
| `value` | `float` | `None` | 初始值 |
| `suffix` | `str` | `""` | 数值后缀，如 `"%"` |
| `command` | `Callable[[float], None]` | `None` | 值变化回调 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `get()` / `set(value)` | 读 / 写当前值（等价于 `get()` / `set()`） |
| `set_range(from_, to)` | 改范围 |

### 示例

```python
zoom = Stepper(card.body, from_=10, to=200, value=70, suffix="%")
zoom.pack(padx=16, pady=(0, 12))
```
