# 日期与时间

## 作用

四个控件，覆盖「选日期 / 选时间」的两种用法：

- `Calendar` —— 月视图日历本体，可以单独摆在页面里当一块常驻日历。
- `DatePicker` —— 日期输入框 `[年] - [月] - [日 ▾]`。三段平时可以直接键入，
  点右侧三角形才弹出月视图。
- `TimeField` —— 时间输入框 `[时] : [分] : [秒 ▾]`。交互和 `DatePicker` 一致。
- `TimePicker` —— 时 / 分 / 秒三列滚轮，被 `TimeField` 当弹层用，也可以单独摆。

`DatePicker` 和 `TimeField` 都支持 `readonly=` / `set_readonly(flag)`：
只读时不能键入、点箭头也不弹层，值照常显示。

## 类型

| 类型 | 外观 | 默认宽度 | 用在哪 |
| --- | --- | --- | --- |
| `DatePicker` | 三段 + 右侧箭头 | 140 | 表单里的日期 |
| `TimeField` | 三段 + 右侧箭头 | 140 | 表单里的时间 |
| `Calendar` | 7 列月视图 | 260 | 常驻日历、自定义弹层 |
| `TimePicker` | 三列滚轮 | 自适应 | 常驻时间选择、自定义弹层 |

## 参数

### DatePicker

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `value` | `datetime.date \| None` | `None` | 初始日期 |
| `command` | `Callable[[date], None]` | `None` | 选中 / 键入生效后的回调 |
| `placeholder` | `str` | `"选择日期"` | 保留参数：改成三段之后不再绘制占位文字 |
| `width` | `int` | `140` | 整体宽度（逻辑像素） |
| `readonly` | `bool` | `False` | 初始是否只读 |
| `**kwargs` | — | — | 透传给外层 `CTkFrame`（`fg_color` 等） |

```python
birthday = ctk.DatePicker(row, value=date(2026, 11, 7), command=lambda d: print(d))
birthday.pack(side="left")
```

### TimeField

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `value` | `datetime.time \| None` | `None` | 初始时间 |
| `command` | `Callable[[time], None]` | `None` | 值变化回调 |
| `width` | `int` | `140` | 整体宽度 |
| `readonly` | `bool` | `False` | 初始是否只读 |

```python
alarm = ctk.TimeField(row, value=time(9, 30), command=lambda t: print(t))
alarm.pack(side="left", padx=(10, 0))
```

### Calendar

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `year` / `month` | `int \| None` | `None` | 初始显示的年月，默认今天 |
| `value` | `date \| None` | `None` | 初始选中日期 |
| `command` | `Callable[[date], None]` | `None` | 选中日期回调 |
| `width` | `int` | `260` | 宽度 |

```python
cal = ctk.Calendar(card.body(), value=date.today())
cal.pack(fill="x", padx=16, pady=(0, 12))
```

### TimePicker

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `value` | `time \| None` | `None` | 初始时间 |
| `command` | `Callable[[time], None]` | `None` | 滚到新值时回调 |

```python
wheel = ctk.TimePicker(card.body(), value=time(8, 0))
wheel.pack(padx=16, pady=(0, 12))
```

## 方法

### 读写值

| 控件 | 方法 | 说明 |
| --- | --- | --- |
| `DatePicker` | `get()` | 当前日期；没选过是 `None` |
| | `set(d)` | 直接写入，不弹层、不触发回调 |
| `TimeField` | `get()` / `set(t)` | 同上 |
| `Calendar` | `get()` | 当前选中日期 |
| | `set(d)` | 选中并翻到它所在月份；传 `None` 清空 |
| `TimePicker` | `get()` / `set(t)` | 读 / 写时间，`set()` 不回调 |

```python
birthday.set(date(2026, 12, 1))
print(birthday.get(), alarm.get(), calm.get())
```

### 弹层控制

| 方法 | 说明 |
| --- | --- |
| `open()` | 打开弹层；已经打开就关掉 |
| `close()` | 关掉弹层 |

```python
birthday.open()     # 相当于点了右侧三角形
birthday.close()
```

### 只读

| 方法 | 说明 |
| --- | --- |
| `set_readonly(flag)` | 切换只读：不能键入、点箭头不弹层 |
| `is_readonly()` | 当前是否只读 |

```python
birthday.set_readonly(True)     # 只展示，不可改
birthday.set_readonly(False)    # 恢复
```

### 键入规则

`readonly=False` 时三段可以直接改：

| 控件 | 生效时机 | 非法输入 |
| --- | --- | --- |
| `DatePicker` | 回车、失焦 | 日期不存在（如 2 月 30 日）→ 原样退回 |
| `TimeField` | 回车、失焦 | 越界自动夹回（`99` 点 → `23` 点） |

日期三段**全部清空**时 `get()` 返回 `None`；时间缺段时按 `0` 补齐。

```python
birthday.set_readonly(False)
# 用户键入 2026 / 12 / 01 后回车 → command 收到 date(2026, 12, 1)
```

### 通用方法

继承 `on_click`、`on_focus`、`on_key` 等事件方法，
以及 `enable` / `disable` / `set_enabled` / `is_enabled`。

## 完整示例

```python
from datetime import date, time

import ctk_kit as ctk

app = ctk.App(title="日期时间示例", size=(640, 460))

card = ctk.Card(app, title="时间设置")
card.pack(fill="x", padx=24, pady=24)

row1 = card.row(1)
ctk.FieldLabel(row1, "开始日期").pack(side="left")
d = ctk.DatePicker(row1, value=date.today(), command=lambda v: print("日期", v))
d.pack(side="left", padx=(12, 0))

row2 = card.row(2)
ctk.FieldLabel(row2, "开始时间").pack(side="left")
t = ctk.TimeField(row2, value=time(9, 0), command=lambda v: print("时间", v))
t.pack(side="left", padx=(12, 0))

row3 = card.row(3)
ctk.SoftButton(
    row3, "只读", command=lambda: (d.set_readonly(True), t.set_readonly(True))
).pack(side="left", padx=16)
ctk.SoftButton(
    row3, "可编辑", command=lambda: (d.set_readonly(False), t.set_readonly(False))
).pack(side="left")
ctk.PrimaryButton(
    row3, "打印", command=lambda: print(d.get(), t.get())
).pack(side="left", padx=(10, 0))

# 常驻日历
cal = ctk.Calendar(card.body(), value=date.today())
cal.pack(fill="x", padx=16, pady=(12, 14))

app.mainloop()
```

## 换色

三段文字用 `COLOR_TEXT`（只读时 `COLOR_MUTED`），分隔符与箭头用 `COLOR_FAINT`，
弹层底色固定 `#2B2B2B`（与下拉框、右键菜单一致），选中日期用 `COLOR_ACCENT`。

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_ACCENT": "#f97316"})   # 选中日期、今天高亮
theming.apply_palette({"COLOR_TEXT": "#f1f3f6"})     # 三段文字
```
