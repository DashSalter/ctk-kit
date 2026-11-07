# 其它

![杂项](../assets/guide-misc.png){ loading=lazy }

## 作用

几个结构型组件和三个小工具：折叠面板、代码面板、分栏、时间线、分隔线、空状态。

## Collapsible

### 作用

点标题行展开 / 收起内容的面板；内容放在 `collapse.body` 里。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `collapsed_text` | `str` | `"显示代码"` | 收起时的文字 |
| `expanded_text` | `str` | `"隐藏代码"` | 展开时的文字 |
| `expanded` | `bool` | `False` | 初始是否展开 |
| `on_toggle` | `Callable[[bool], None]` | `None` | 展开状态回调 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `expanded()` | 当前是否展开 |
| `expand()` / `collapse()` / `toggle()` | 展开 / 收起 / 切换 |
| `set_expanded(flag)` | 直接设置 |
| `set_texts(collapsed_text=..., expanded_text=...)` | 换两段文字 |

### 示例

```python
collapse = Collapsible(card.row(1), collapsed_text="高级选项")
collapse.pack(fill="x", padx=16, pady=(0, 8))

Label(collapse.body, "这些内容默认是收起来的").pack(padx=12, pady=12)
collapse.expand()
```

## CodePanel

### 作用

专给「查看实现」用的折叠面板，展开后显示一段代码，带高亮。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `code` | `str` | 必填 | 代码内容 |
| `note` | `str` | `""` | 代码上方的一句说明 |
| `collapsed_text` | `str` | `"查看实现"` | 收起时文字 |
| `expanded_text` | `str` | `"收起实现"` | 展开时文字 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `set_code(code)` | 换代码 |
| `set_note(note)` | 换说明 |

### 示例

```python
CodePanel(card.body, "btn = PrimaryButton(app, '保存')", note="最小用法").pack(
    fill="x", padx=16, pady=(0, 12)
)
```

## Splitter

### 作用

两栏之间一条可拖动的手柄，左右或上下分栏。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `orientation` | `str` | `"horizontal"` | `"horizontal"` 左右 / `"vertical"` 上下 |
| `initial` | `float` | `0.5` | 初始比例 |
| `min_size` | `int` | `80` | 每边最小像素 |
| `command` | `Callable[[float], None]` | `None` | 拖动结束回调 |

### 属性

| 属性 | 说明 |
| --- | --- |
| `first` / `second` | 两个容器，往里放内容 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `set_ratio(ratio, notify=False)` | 按比例分栏 |
| `get_ratio()` | 读当前比例 |

### 示例

```python
split = Splitter(card.body, initial=0.34, min_size=120)
split.pack(fill="both", expand=True, padx=16)

Label(split.first, "目录").pack(anchor="w", padx=10, pady=10)
Label(split.second, "内容").pack(anchor="w", padx=10, pady=10)
split.set_ratio(0.25)
```

## Timeline

### 作用

纵向时间线：左侧一条竖线串起圆点，每个点是「标题 + 说明 + 时间」。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `items` | `Sequence[tuple]` | `()` | 每项是 `(标题, 说明, 时间)` 或再加一个 `True` 表示高亮 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `set_items(items)` | 整条替换 |
| `add(title, description="", time="", active=False)` | 追加一条 |

### 示例

```python
timeline = Timeline(card.body, items=[
    ("创建仓库", "初始化提交", "09:12", True),
    ("第一次发布", "0.1.0", "10:40"),
])
timeline.pack(fill="x", padx=16)
timeline.add("补充说明", "修了一个边界", "11:05")
```

## divider / vertical_divider

### 作用

一条分隔线；横的分段，竖的在工具栏里隔开按钮。

### 参数

| 函数 | 参数 | 说明 |
| --- | --- | --- |
| `divider(master, *, pady=(12,0), text="", dashed=False, color=None)` | `text` | 线中间的文字，空则是整条线 |
| `vertical_divider(master, *, height=20, padx=(0,0), color=None)` | `height` | 竖线可见高度 |

### 示例

```python
divider(card.body, text="或者")
toolbar = Frame(card.body)
toolbar.pack(fill="x")
vertical_divider(toolbar, height=22).pack(side="left", padx=8)
```

## empty_hint

### 作用

空状态提示：一行主文字 + 一行灰字说明，返回一个透明容器，摆放自己定。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `title` | `str` | 必填 | 主文字 |
| `detail` | `str` | `""` | 下面那行灰色说明 |

### 示例

```python
hint = empty_hint(card.body, "还没有记录", "点右上角新建一条")
hint.pack(fill="both", expand=True, pady=24)
```
