# 布局与卡片

## 作用

ctk-kit 的页面由一组卡片竖向堆叠而成。`Card` 是一块带圆角和标题的内容容器，
`Frame` 是不带任何装饰的纯容器，`Scrollable` 是配好滚动条的滚动容器；
`PageHeader` 画页面标题，`SectionTitle` 画分组标题，`FieldLabel` / `HintLabel` /
`Label` 负责三档文字。

这一组控件解决的是同一件事：**让每一页的结构一致**。卡片间距、行间距、
字段名宽度都来自库里的默认值，所以不用每页手调 `pady`。

## 类型

| 类型 | 外观 | 典型高度 | 用在哪 |
| --- | --- | --- | --- |
| `Card` | 圆角卡片 + 可选标题行 | 自适应 | 页面里的每一块内容 |
| `Card.body()` | 卡片内部的透明容器 | 自适应 | 需要自己排布时直接往里放 |
| `Card.row(i)` | 卡片内的一行，横向 | 自适应 | 一行里摆几个控件 |
| `Frame` | 全透明，无边无底 | 自适应 | 纯分组、对齐用 |
| `Scrollable` | 透明滚动容器 + 自动隐藏滚动条 | 自适应 | 内容可能超出可视区 |
| `PageHeader` | 左标题 + 右侧信息 | 约 48 | 每页顶部，构造时自动 `pack` |
| `SectionTitle` | 小号加粗标题 | 约 30 | 一张卡里再分组 |
| `FieldLabel` | 固定宽度、右对齐字段名 | 约 32 | 表单左侧的字段名 |
| `HintLabel` | 小号灰字，可换行 | 自适应 | 字段下方的说明 |
| `Label` | 正文色普通文字 | 自适应 | 一般文字 |

## 参数

### Card

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `title` | `str` | `""` | 卡片标题；空字符串表示不画标题行 |
| `**kwargs` | — | — | 透传给 `CTkFrame`（`fg_color`、`corner_radius`、`border_width` 等） |

```python
card = ctk.Card(page, title="表单输入")
card.pack(fill="x", padx=24, pady=(0, 12))
```

### Frame

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `**kwargs` | — | — | 透传给 `CTkFrame`，默认 `fg_color="transparent"` |

`Frame` 和直接 `ctk.CTkFrame(parent, fg_color="transparent")` 的区别只有一个：
它默认就是透明的，不用每次手写 `fg_color`。

```python
row = ctk.Frame(card)
row.pack(fill="x", padx=16, pady=(0, 10))
```

### Scrollable

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `auto_hide` | `bool` | `True` | 内容放得下时自动隐藏右侧滚动条 |
| `**kwargs` | — | — | 透传给 `CTkScrollableFrame` |

```python
scroll = ctk.Scrollable(page, auto_hide=True)
scroll.pack(fill="both", expand=True, padx=20, pady=10)
```

### PageHeader / SectionTitle / FieldLabel / HintLabel / Label

| 控件 | 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `PageHeader` | `master` / `title` | `tk.Misc` / `str` | 必填 | 页面标题 |
| `SectionTitle` | `master` / `text` | `tk.Misc` / `str` | 必填 | 分组标题，构造时就已经 `pack` |
| `FieldLabel` | `master` / `text` / `width` | `tk.Misc` / `str` / `int` | 必填 / `112` | 固定宽度，保证同列字段名对齐 |
| `HintLabel` | `master` / `text` | `tk.Misc` / `str` | 必填 | 自动换行的灰字 |
| `Label` | `master` / `text` / `text_color` | `tk.Misc` / `str` / `str` | `""` / `#f1f3f6` | 正文文字 |

```python
# 页头在构造时就 pack 成一行了，不用再摆位置
header = ctk.PageHeader(page, "组件")
header.info.configure(text="v0.12.0")      # 右侧那行信息

ctk.SectionTitle(card, "基础")
ctk.FieldLabel(row, "名称", width=88).pack(side="left")
ctk.HintLabel(row, "改动会立即生效").pack(side="left", padx=(12, 0))
```

想给页头加外边距时，把它放进一个带 `padx` 的容器里，或者构造后
`header.pack_configure(padx=24)`。

## 方法

### 卡片内容

| 方法 | 说明 |
| --- | --- |
| `card.body()` | 卡片内容容器；不想用 `row()` 时直接往里 `pack` |
| `card.row(index, **kwargs)` | 取第 `index` 行；没有就建一个，同一个编号复用同一个容器 |
| `card.apply_theme()` | 按当前令牌重刷卡片和标题颜色，不重建控件 |

`row()` 的行按编号从上往下排，`**kwargs` 是这一行的 `pack` 参数：

```python
card.row(1).pack_configure(fill="x")             # 改已有行
card.row(2, pady=(0, 14))                        # 新行 + 自定义下间距
ctk.FlatButton(card.row(1), "复制").pack(side="right")
```

### 滚动容器

| 方法 | 说明 |
| --- | --- |
| `scroll.suspend_scrollbar()` | 构建期间冻结滚动条重绘（批量塞控件时用） |
| `scroll.resume_scrollbar()` | 解除冻结，并按最后一次参数补画一次 |

```python
scroll.suspend_scrollbar()
for name in names:
    ctk.Label(scroll, name).pack(fill="x")
scroll.resume_scrollbar()
```

### 通用方法

`Label`、`SectionTitle`、`FieldLabel`、`HintLabel`、`PageHeader` 都继承库里的通用混入：

- `set_text(...)` / `get_text()` — 改 / 读文字
- `on_click`、`on_enter`、`on_leave`、`on_double_click` 等事件绑定
- `enable()` / `disable()` / `set_enabled(bool)` / `is_enabled()`

`Card`、`Frame`、`Scrollable` 是容器，用 `pack` / `grid` / `place` 摆放即可。

## 完整示例

```python
import ctk_kit as ctk

app = ctk.App(title="布局示例", size=(640, 460))

header = ctk.PageHeader(app, "设置")
header.info.configure(text="v0.12.0")

card = ctk.Card(app, title="外观")
card.pack(fill="x", padx=24, pady=(0, 12))

# 第一行：字段名 + 值
ctk.FieldLabel(card.row(1), "主题").pack(side="left")
ctk.Label(card.row(1), "跟随系统").pack(side="left", padx=(12, 0))

# 第二行：说明文字独占一行
ctk.HintLabel(card.row(2), "切换外观后当前页会重建，配色不会残留。").pack(
    fill="x", padx=16, pady=(0, 12)
)

# 第三张卡：可滚动的内容
scroll_card = ctk.Card(app, title="全部组件")
scroll_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

scroll = ctk.Scrollable(scroll_card.body())
scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))
for i in range(1, 31):
    ctk.Label(scroll, f"第 {i} 项").pack(fill="x", pady=2)

app.mainloop()
```

## 换色

布局控件几乎不出现硬编码颜色：卡片底色是 `COLOR_CARD`、标题是 `COLOR_TEXT`、
说明文字是 `COLOR_MUTED`，全部来自令牌。

```python
from ctk_kit import theming

# 卡片更暗一点
theming.apply_palette({"COLOR_CARD": "#15161c"})

# 说明文字更亮一点
theming.apply_palette({"COLOR_MUTED": "#a8b0bb"})
```

改完立刻生效。已经缓存的 `Card.row()` 容器不受影响，颜色通过 `apply_theme()` 刷新。
