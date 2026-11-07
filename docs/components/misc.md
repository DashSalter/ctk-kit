# 其它

## 作用

四个结构型组件和三个小工具：

- `Collapsible` —— 可展开的面板：标题行常驻，内容区按需显示。
- `CodePanel` —— 专用于「查看实现」的折叠面板，带代码高亮。
- `Splitter` —— 可拖动的两栏分隔，左右或上下。
- `Timeline` —— 纵向时间线。
- `divider()` / `vertical_divider()` —— 一条分隔线。
- `empty_hint()` —— 空状态提示（标题 + 说明）。

## 类型

| 类型 | 外观 | 用在哪 |
| --- | --- | --- |
| `Collapsible` | 一个可点的标题条 | 高级选项、补充说明 |
| `CodePanel` | 等宽字的 `▾ 查看实现` | 组件示例展开源码 |
| `Splitter` | 两栏 + 中间细手柄 | 目录 + 内容 |
| `Timeline` | 左侧竖线 + 圆点 | 日志、版本记录 |
| `divider` | 一条细线 | 分段 |
| `empty_hint` | 居中标题 + 灰字 | 列表为空 |

## 参数

### Collapsible

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `collapsed_text` | `str` | `"显示代码"` | 收起时的标题 |
| `expanded_text` | `str` | `"隐藏代码"` | 展开时的标题 |
| `expanded` | `bool` | `False` | 初始是否展开 |
| `button_height` | `int` | `36` | 标题条高度 |
| `on_toggle` | `Callable[[bool], None]` | `None` | 展开 / 收起回调，参数是新的展开状态 |

展开后往里放控件用 `collapse.body`：

```python
collapse = ctk.Collapsible(card.row(1), collapsed_text="高级选项",
                           expanded=False, on_toggle=lambda on: print("展开" if on else "收起"))
collapse.pack(fill="x", padx=16, pady=(0, 8))

ctk.Label(collapse.body, "高级选项的内容放在 collapse.body 里").pack(padx=12, pady=12)
```

### CodePanel

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `code` | `str` | 必填 | 要显示的代码 |
| `note` | `str` | `""` | 代码上方的一句说明 |
| `collapsed_text` | `str` | `"查看实现"` | 收起时文字 |
| `expanded_text` | `str` | `"收起实现"` | 展开时文字 |

```python
ctk.CodePanel(card.body(), "btn = PrimaryButton(app, '保存')", note="最小用法").pack(
    fill="x", padx=16, pady=(0, 12)
)
```

### Splitter

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `orientation` | `str` | `"horizontal"` | `"horizontal"` 左右，`"vertical"` 上下 |
| `initial` | `float` | `0.5` | 初始比例（0–1） |
| `min_size` | `int` | `80` | 每一边的最小像素 |
| `handle` | `int` | `6` | 手柄厚度 |
| `command` | `Callable[[float], None]` | `None` | 拖动结束回调，参数是比例 |

两栏容器是 `split.first` 和 `split.second`：

```python
split = ctk.Splitter(card.body(), initial=0.34, min_size=120)
split.pack(fill="both", expand=True, padx=16, pady=(0, 12))

ctk.Label(split.first, "目录").pack(anchor="w", padx=10, pady=10)
ctk.Label(split.second, "内容").pack(anchor="w", padx=10, pady=10)
```

### Timeline

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `items` | `Sequence[TimelineItem]` | `()` | 每一项：`(标题, 说明, 时间)`、`(标题, 说明, 时间, 是否高亮)` 或同构的 dict |

```python
timeline = ctk.Timeline(card.body(), items=[
    ("创建仓库", "初始化提交", "09:12", True),
    ("第一次发布", "0.1.0", "10:40"),
])
timeline.pack(fill="x", padx=16)
```

### divider / vertical_divider

| 函数 | 参数 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `divider(master, *, pady=(12, 0), text="", dashed=False, color=None)` | `text` | `""` | 线中间的文字，空则是一条整线 |
| | `dashed` | `False` | 虚线 |
| | `color` | `None` | 颜色，默认 `COLOR_BORDER` |
| `vertical_divider(master, *, height=20, padx=(0, 0), color=None)` | `height` | `20` | 竖线的可见高度 |

```python
ctk.divider(card.body(), text="或者")
ctk.vertical_divider(toolbar, height=22, padx=(8, 8)).pack(side="left")
```

### empty_hint

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `title` | `str` | 必填 | 主文字 |
| `detail` | `str` | `""` | 下面那行灰色说明 |

返回一个已经装好文字的透明容器，**摆放由调用方决定**：

```python
hint = ctk.empty_hint(card.body(), "还没有记录", "点右上角新建一条")
hint.pack(fill="both", expand=True, pady=24)
```

## 方法

### Collapsible

| 方法 | 说明 |
| --- | --- |
| `expanded()` | 当前是否展开 |
| `expand()` / `collapse()` | 展开 / 收起 |
| `toggle()` | 切换 |
| `set_expanded(bool)` | 直接设状态 |
| `set_texts(collapsed_text=..., expanded_text=...)` | 换两段标题文字 |

```python
collapse.set_expanded(True)
collapse.set_texts(collapsed_text="更多", expanded_text="收起")
print(collapse.expanded())
```

### CodePanel

| 方法 | 说明 |
| --- | --- |
| `set_code(code)` | 换代码 |
| `set_note(note)` | 换说明文字 |

```python
panel.set_code("btn.set_text('新文字')")
panel.set_note("改文字")
```

### Splitter

| 方法 | 说明 |
| --- | --- |
| `set_ratio(ratio, notify=False)` | 按比例分栏；`notify=True` 时也触发回调 |
| `get_ratio()` | 当前比例 |

```python
split.set_ratio(0.25)
print(split.get_ratio())
```

### Timeline

| 方法 | 说明 |
| --- | --- |
| `set_items(items)` | 整条替换 |
| `add(title, description="", time="", active=False)` | 末尾追加一条 |

```python
timeline.add("补充说明", "修了一个边界", "11:05")
```

## 完整示例

```python
import ctk_kit as ctk

app = ctk.App(title="其它示例", size=(820, 620))

card = ctk.Card(app, title="结构")
card.pack(fill="both", expand=True, padx=24, pady=16)

collapse = ctk.Collapsible(card.row(1), collapsed_text="高级选项")
collapse.pack(fill="x", padx=16, pady=(0, 8))
ctk.Label(collapse.body, "这里的内容默认是收起来的").pack(padx=12, pady=12)

ctk.divider(card.body(), text="分栏")

split = ctk.Splitter(card.body(), initial=0.36, min_size=110)
split.pack(fill="both", expand=True, padx=16, pady=(0, 12))

timeline = ctk.Timeline(split.first, items=[
    ("创建", "初始化", "09:12", True),
    ("发布", "0.12.0", "10:40"),
])
timeline.pack(fill="both", expand=True, padx=8, pady=8)

empty = ctk.empty_hint(split.second, "还没有选中", "左边点一条看详情")
empty.pack(fill="both", expand=True, pady=20)

app.mainloop()
```

## 换色

分隔线和手柄用 `COLOR_BORDER`，时间线的高亮圆点用 `COLOR_ACCENT`，
空状态文字用 `COLOR_MUTED`：

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_BORDER": "#3a3f4b"})
theming.apply_palette({"COLOR_ACCENT": "#f97316"})
```
