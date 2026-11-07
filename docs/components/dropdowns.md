# 下拉与步进

## 作用

四个「从有限选项里选一个」的控件，外观都做成一块填充式圆角框：

- `DropField` —— 输入框 + 下拉箭头。可以手打，也可以点箭头从候选里挑。
- `TagSelectField` —— 多选标签下拉：选中的项变成标签排进框里，标签右侧小叉可删。
- `TreeSelectField` —— 层级树下拉：分组节点点开才显示子项，子项逐级缩进。
- `Stepper` —— 紧凑步进器 `[ − ] 当前值 ▾ [ + ]`，适合百分比、档位这类少量取值。

四者的候选都由 `values_provider` / `values` 提供，**每次展开时重新取**，
所以候选可以是动态的（数据库、其它控件的当前状态）。

## 类型

| 类型 | 外观 | 默认高度 | 用在哪 |
| --- | --- | --- | --- |
| `DropField` | 输入框 + 箭头，可手打 | 36 | 可选可填的字段（城市、分类） |
| `TagSelectField` | 标签堆在框里 | 36 | 多选筛选（标签、权限） |
| `TreeSelectField` | 输入框 + 箭头，弹出树 | 36 | 层级选择（部门、目录） |
| `Stepper` | `− 值 ▾ +` | 36 | 缩放比例、字号、数量 |

## 参数

### DropField

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `values_provider` | `Callable[[], Sequence[str]]` | 必填 | 每次展开时调用，返回候选列表 |
| `command` | `Callable[[str], None]` | `None` | 选中 / 输入后的回调 |
| `placeholder` | `str` | `""` | 输入框占位文字 |
| `height` | `int` | `36` | 高度 |
| `disabled` | `Sequence[str] \| None` | `None` | 初始禁用哪些候选 |
| `glass` | `bool` | `True` | 候选面板是否用毛玻璃底 |
| `readonly` | `bool` | `False` | 初始是否只读（不能输入、不能展开） |

```python
city = ctk.DropField(
    row,
    values_provider=lambda: ["北京", "上海", "广州"],
    placeholder="选择城市",
    command=lambda v: print("选了", v),
)
city.pack(side="left")
```

### TagSelectField

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `values_provider` | `Callable[[], Sequence[str]]` | 必填 | 候选列表 |
| `command` | `Callable[[list], None]` | `None` | 标签变化回调，参数是当前标签列表 |
| `placeholder` | `str` | `""` | 没有标签时的占位文字 |
| `height` | `int` | `36` | 高度 |
| `values` | `Sequence[str] \| None` | `None` | 初始已选标签 |
| `disabled` | `Sequence[str] \| None` | `None` | 初始禁用哪些候选 |

```python
tags = ctk.TagSelectField(
    row,
    values_provider=lambda: ["紧急", "重要", "延期"],
    values=["重要"],
    command=lambda vs: print("当前标签", vs),
)
tags.pack(fill="x")
```

### TreeSelectField

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `values_provider` | `Callable[[], Sequence]` | 必填 | 返回树；元素可以是字符串或 `(组名, [子项...])` |
| `command` | `Callable[[str], None]` | `None` | 选中叶子节点后的回调 |
| `placeholder` | `str` | `""` | 占位文字 |
| `height` | `int` | `36` | 高度 |
| `value` | `str` | `""` | 初始值 |
| `disabled` | `Sequence[str] \| None` | `None` | 初始禁用哪些**叶子**节点 |

```python
dept = ctk.TreeSelectField(
    row,
    values_provider=lambda: [("研发", ["前端", "后端"]), ("设计", ["交互", "视觉"])],
    placeholder="选择部门",
)
dept.pack(side="left")
```

### Stepper

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `values` | `Sequence \| None` | `None` | 传了就按列表步进，忽略 `from_`/`to`/`increment` |
| `from_` / `to` | `float` | `0` / `100` | 数值范围 |
| `increment` | `float` | `1` | 每次加减多少 |
| `value` | `Any` | `None` | 初始值 |
| `command` | `Callable[[object], None]` | `None` | 值变化回调 |
| `width` / `height` | `int` | `170` / `36` | 尺寸 |
| `suffix` | `str` | `"%"` | 数值后面跟的单位 |
| `decimals` | `int` | `0` | 小数位数 |

```python
ctk.Stepper(row, from_=50, to=200, increment=5, value=100, suffix="%").pack(side="left")
ctk.Stepper(row, values=["小", "中", "大"], value="中").pack(side="left", padx=(10, 0))
```

## 方法

### 读写值

| 控件 | 方法 | 说明 |
| --- | --- | --- |
| `DropField` | `get()` / `set(v)` | 读 / 写输入框内容，`set()` 不触发回调 |
| | `set_text(v)` / `get_text()` | 同义方法，方便统一调用 |
| | `clear()` | 等价于 `set("")` |
| `TagSelectField` | `get()` | 当前标签列表（按添加顺序） |
| | `set([...])` / `clear()` | 整体替换 / 清空 |
| `TreeSelectField` | `get()` / `set(v)` | 读 / 写选中值 |
| `Stepper` | `get()` / `set(v)` | 读 / 写当前值（`set` 不触发回调） |

```python
print(city.get(), tags.get(), dept.get(), pct.get())
city.set("上海")
tags.set(["紧急", "延期"])
```

### 展开与关闭

| 方法 | 说明 |
| --- | --- |
| `open_menu()` | 展开候选面板；已经展开时再调用会收起 |
| `close()`（内部） | 收起面板，切换页面时库会自动收起 |

### 禁用候选项

三个下拉都支持「整块禁用」和「禁用其中几项」：

| 方法 | 说明 |
| --- | --- |
| `disable()` | 不带参数：整块禁用 |
| `disable(value)` | 禁用某一个候选 |
| `enable()` / `enable(value)` | 对应地恢复 |
| `is_disabled(value=None)` | 不给参数时问整块，给了参数问那一项 |
| `get_disabled()` | 当前被禁用的候选列表 |
| `set_disabled([...])` | 整体设置；`None` / `[]` 等于全部解除 |
| `clear_disabled()` | 解除全部 |

```python
city.disable("广州")          # 广州这一项灰掉、点不了
city.disable()                # 整个控件禁用
print(city.get_disabled())    # ['广州']
city.clear_disabled()
```

### 只读

`DropField` 支持 `readonly=` / `set_readonly(flag)` / `is_readonly()`：
只读时不能输入、点箭头也不展开，值照常显示。

```python
city.set_readonly(True)
```

### 通用方法

四个控件都继承 `set_text` / `get_text`、`on_click` 等事件方法，
以及 `enable` / `disable` / `is_enabled`。

## 完整示例

```python
import ctk_kit as ctk

app = ctk.App(title="下拉示例", size=(640, 480))

card = ctk.Card(app, title="筛选")
card.pack(fill="x", padx=24, pady=24)

row1 = card.row(1)
ctk.FieldLabel(row1, "城市", width=72).pack(side="left")
city = ctk.DropField(
    row1,
    values_provider=lambda: ["北京", "上海", "广州", "深圳"],
    placeholder="选择城市",
)
city.pack(side="left", padx=(12, 0))

row2 = card.row(2)
ctk.FieldLabel(row2, "标签", width=72).pack(side="left")
tags = ctk.TagSelectField(
    row2,
    values_provider=lambda: ["紧急", "重要", "延期"],
    placeholder="加标签",
)
tags.pack(side="left", fill="x", expand=True, padx=(12, 0))

row3 = card.row(3)
ctk.FieldLabel(row3, "部门", width=72).pack(side="left")
dept = ctk.TreeSelectField(
    row3,
    values_provider=lambda: [("研发", ["前端", "后端"]), ("设计", ["交互"])],
    placeholder="选择部门",
)
dept.pack(side="left", padx=(12, 0))

row4 = card.row(4)
ctk.FieldLabel(row4, "缩放", width=72).pack(side="left")
ctk.Stepper(row4, from_=50, to=200, increment=10, value=100).pack(
    side="left", padx=(12, 0)
)

ctk.PrimaryButton(
    card.row(5),
    "打印当前值",
    command=lambda: print(city.get(), tags.get(), dept.get()),
).pack(side="left", padx=16, pady=(4, 14))

app.mainloop()
```

## 换色

下拉框本体用 `COLOR_INPUT` / `COLOR_BORDER`，候选面板用固定的 `#2B2B2B`
（与右键菜单、日期弹层保持一致），选中项高亮用 `COLOR_ACCENT`。

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_INPUT": "#1d1f27"})
theming.apply_palette({"COLOR_ACCENT": "#f97316"})   # 选中项与标签底色
```
