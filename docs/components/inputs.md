# 输入框

## 作用

四个输入控件，覆盖三种场景：

- `CTkEntry` —— 单行文本。带圆角、占位符、右键菜单（剪切 / 复制 / 粘贴 / 全选 / 插入时间戳）。
- `Spinner` —— 单行文本 + 上下箭头。既可以走数字区间，也可以在一组备选文字里切换。
- `SearchBox` —— 带放大镜和清空按钮的搜索框，输入有防抖，`command` 不会每敲一个字就触发。
- `TextArea` —— 多行文本区，带占位符、字数统计和只读模式。

四个都支持 `readonly=` 与 `set_readonly(flag)`：只读时键盘输入被拒，
但 `set()` 这类程序写入仍然有效（内部会临时解锁再锁回）。

## 类型

| 类型 | 外观 | 默认高度 | 用在哪 |
| --- | --- | --- | --- |
| `CTkEntry` | 圆角填充框，1px 描边 | 38 | 姓名、备注、路径 |
| `Spinner` | 输入框 + 右侧上下箭头 | 36 | 数量、百分比、档位 |
| `SearchBox` | 左侧放大镜 + 右侧清空 | 38 | 列表 / 表格上方 |
| `TextArea` | 大块圆角区域 + 右下角计数 | 200 | 备注、日志、JSON |

## 参数

### CTkEntry

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `menu` | `Any` | `True` | `True` 挂默认右键菜单；传 `False` 关掉，传自定义菜单对象则用它 |
| `readonly` | `bool` | `False` | 初始是否只读 |
| `**kwargs` | — | — | 透传给 `CTkEntry`：`width`、`height`、`placeholder_text`、`font`、`justify` 等 |

```python
entry = ctk.CTkEntry(row, placeholder_text="输入名称", width=220)
entry.pack(side="left")
```

### Spinner

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `from_` / `to` | `float` | `0` / `100` | 数字模式的范围 |
| `increment` | `float` | `1` | 每次点箭头的步长 |
| `values` | `Sequence[str] \| None` | `None` | 传了就走「备选文字」模式，忽略 `from_`/`to` |
| `value` | `Any` | `None` | 初始值 |
| `command` | `Callable[[Any], None]` | `None` | 值变化回调，参数是新值 |
| `placeholder` | `str` | `""` | 输入框占位文字 |
| `height` | `int` | `36` | 高度 |
| `width` | `int` | `160` | 宽度 |
| `as_int` | `bool` | `True` | 数字模式返回 `int` 还是 `float` |
| `readonly` | `bool` | `False` | 初始是否只读 |

```python
# 数字
qty = ctk.Spinner(row, from_=1, to=99, value=1, command=print)
qty.pack(side="left")

# 备选文字
level = ctk.Spinner(row, values=["低", "中", "高"], value="中")
level.pack(side="left", padx=(10, 0))
```

### SearchBox

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `placeholder` | `str` | `"搜索"` | 占位文字 |
| `command` | `Callable[[str], None]` | `None` | 防抖后的回调，参数是当前文字 |
| `width` | `int` | `240` | 宽度 |
| `height` | `int` | `38` | 高度 |
| `delay` | `int` | `300` | 防抖毫秒数：停止输入这么久才触发回调 |
| `readonly` | `bool` | `False` | 初始是否只读 |
| `**kwargs` | — | — | 透传 |

```python
search = ctk.SearchBox(row, placeholder="搜索组件", command=lambda t: print("搜", t))
search.pack(side="left")
```

### TextArea

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `placeholder` | `str` | `""` | 空内容时显示的灰字 |
| `height` | `int` | `200` | 高度 |
| `readonly` | `bool` | `False` | 初始是否只读 |
| `show_counter` | `bool` | `True` | 右下角是否显示字数 |
| `on_change` | `Callable[[str], None]` | `None` | 内容变化回调 |
| `bg_color` | `Any` | `None` | 底色，默认取 `COLOR_INPUT` |
| `text_color` | `Any` | `None` | 文字色，默认取 `COLOR_TEXT` |
| `menu` | `Any` | `True` | 右键菜单 |

```python
note = ctk.TextArea(card, placeholder="写点什么…", height=160, on_change=print)
note.pack(fill="x", padx=16, pady=(0, 12))
```

## 方法

### 读写内容

| 控件 | 方法 | 说明 |
| --- | --- | --- |
| `CTkEntry` | `set(text)` / `set_text(text)` | 整体替换内容 |
| | `get_text()` | 读回内容（等价于 `get()`） |
| | `append(text)` | 追加到末尾 |
| | `clear()` | 清空 |
| `Spinner` | `get()` | 数字模式返回 `int`/`float`，文字模式返回那一项 |
| | `set(value)` | 直接写入，不触发回调、不做越界钳制 |
| `SearchBox` | `get()` / `set(text)` | 读 / 写，`set(..., notify=True)` 也触发回调 |
| | `clear()` | 清空并立刻触发一次回调 |
| | `search()` | 立刻触发回调，不等防抖 |
| | `focus()` | 让输入框拿到焦点 |
| `TextArea` | `get()` | 全文；占位符显示中返回空字符串 |
| | `set(text)` | 整体替换；传 `""` 恢复占位符 |
| | `append(text)` | 追加并刷新字数、触发 `on_change` |
| | `insert(at, text)` | 在 Tk 索引处插入（`"1.0"` / `"end"`） |
| | `clear()` | 等价于 `set("")` |

```python
entry.set("已完成").append("（备份）")
print(entry.get_text())

note.set("第一行\n第二行")
note.insert("end", "\n第三行")
print(len(note.get()))
```

### 只读与启用

| 方法 | 说明 |
| --- | --- |
| `set_readonly(flag)` | 切换只读：键盘输入被拒，但 `set()` 仍能写 |
| `is_readonly()` | 当前是否只读 |
| `enable()` / `disable()` / `set_enabled(bool)` | 启用 / 禁用 |
| `is_enabled()` | 当前是否可用（禁用 > 只读 > 正常） |

```python
entry.set_readonly(True)     # 只能看、只能复制
entry.set("程序仍然能写")     # 内部临时解锁再锁回
entry.set_readonly(False)
```

### 字数与占位符

`TextArea` 的字数统计跟随 `on_change` 自动刷新；`placeholder` 只是空内容时
显示的一段灰字，`get()` 不会把它当成内容返回。

## 完整示例

```python
import ctk_kit as ctk

app = ctk.App(title="输入示例", size=(620, 520))

card = ctk.Card(app, title="表单")
card.pack(fill="x", padx=24, pady=24)

row1 = card.row(1)
ctk.FieldLabel(row1, "名称").pack(side="left")
name = ctk.CTkEntry(row1, width=200, placeholder_text="组件名称")
name.pack(side="left", padx=(12, 0))

row2 = card.row(2)
ctk.FieldLabel(row2, "数量").pack(side="left")
qty = ctk.Spinner(row2, from_=1, to=20, value=1)
qty.pack(side="left", padx=(12, 0))

row3 = card.row(3)
search = ctk.SearchBox(row3, width=220, command=lambda t: print("搜索:", t))
search.pack(side="left")
ctk.SoftButton(row3, "清空", command=search.clear).pack(side="left", padx=(10, 0))

note = ctk.TextArea(card, placeholder="备注…", height=120)
note.pack(fill="x", padx=16, pady=(4, 12))

row4 = card.row(4)
ctk.PrimaryButton(
    row4,
    "只读开关",
    command=lambda: name.set_readonly(not name.is_readonly()),
).pack(side="left", padx=16, pady=(0, 14))

app.mainloop()
```

## 换色

输入框的颜色来自令牌：底色 `COLOR_INPUT`、描边 `COLOR_BORDER`、
占位符 `COLOR_MUTED`、正文 `COLOR_TEXT`、搜索框的放大镜与清空按钮用 `COLOR_MUTED`。

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_INPUT": "#1d1f27"})
theming.apply_palette({"COLOR_BORDER": "#33363f"})
```

`SearchBox` 的图标颜色在换色后由 `apply_theme()` 自动重画；
`TextArea` 的底色可以直接用构造参数 `bg_color=` 覆盖单个实例。
