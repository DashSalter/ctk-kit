# 选择控件

## 作用

六个「选一个 / 选多个 / 拖一个值」的控件：

- `Check` —— 勾选框：实心圆角方块 + 白色对勾。
- `Radio` —— 单选项：圆形指示符，多个共享同一个 `StringVar` 才互斥。
- `Switch` —— 开关：胶囊轨道 + 圆球，用 Pillow 画的抗锯齿图片。
- `Segmented` —— 分段选择：浅一档的容器底，选中块滑到目标段。
- `Slider` —— 滑块：轨道淡，已滑过的部分和圆钮是主色。
- `RangeSlider` —— 双滑块，选一个区间。

## 类型

| 类型 | 外观 | 默认尺寸 | 用在哪 |
| --- | --- | --- | --- |
| `Check` | 22×22 方形 + 对勾 | 22 | 多选、确认项 |
| `Radio` | 22×22 圆形 | 22 | 互斥选项 |
| `Switch` | 44 宽胶囊 | 44 | 设置页的开关 |
| `Segmented` | 一块底 + 滑块 | 300×34 | 2–5 个短选项（日 / 周 / 月） |
| `Slider` | 细轨道 + 圆钮 | 220 宽 | 连续数值 |
| `RangeSlider` | 双圆钮 + 中间高亮 | 240×28 | 价格 / 时间区间 |

## 参数

### Check

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `text` | `str` | `""` | 右侧文字 |
| `command` | `Callable[[], None]` | `None` | 勾选变化回调（**不接收参数**） |
| `width` / `height` | `int` | `22` / `22` | 指示符尺寸 |
| `variable` | `tk.IntVar \| None` | `None` | 绑定变量，多个勾选框可以共用一个 |
| `font` | `Any` | `None` | 文字字体 |

```python
agree = ctk.Check(row, "记住本次选择", command=lambda: print(agree.get_value()))
agree.pack(side="left")
```

### Radio

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `text` | `str` | `""` | 右侧文字 |
| `value` | `str` | `""` | 这一项代表的值 |
| `variable` | `tk.StringVar \| None` | `None` | **同一个变量**才能互斥 |
| `command` | `Callable[[], None]` | `None` | 选中回调 |
| `width` / `height` | `int` | `22` / `22` | 指示符尺寸 |

```python
choice = tk.StringVar(value="a")
for key, label in (("a", "按名称"), ("b", "按时间")):
    ctk.Radio(row, label, key, variable=choice).pack(side="left", padx=(0, 12))
```

### Switch

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `command` | `Callable[[], None]` | `None` | 拨动回调 |
| `text` | `str` | `""` | 开关右侧文字 |
| `width` | `int` | `44` | 轨道宽度 |
| `value` | `bool` | `False` | 初始是否打开 |

```python
dark = ctk.Switch(row, command=lambda: print(dark.get_value()), text="深色", value=True)
dark.pack(side="left")
```

### Segmented

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `values` | `Sequence[str]` | `()` | 各段文字 |
| `command` | `Callable[[str], None]` | `None` | 切换回调，参数是选中段的文字 |
| `width` / `height` | `int` | `300` / `34` | 尺寸 |
| `font` | `tuple` | `("微软雅黑", 12)` | 文字字体 |
| `corner_radius` | `int` | `8` | 圆角 |

```python
seg = ctk.Segmented(row, ["日", "周", "月"], command=lambda v: print("周期", v))
seg.pack(side="left")
```

### Slider

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `command` | `Callable[[float], None]` | `None` | 拖动回调，参数是当前值 |
| `from_` / `to` | `float` | `0.0` / `100.0` | 范围 |
| `steps` | `int` | `0` | 分几档；`0` 表示连续 |
| `width` | `int` | `220` | 宽度 |
| `state` | `str` | `"normal"` | `"normal"` / `"disabled"` |

```python
scale = ctk.Slider(row, command=lambda v: print(round(v)), from_=0, to=200)
scale.pack(side="left")
```

### RangeSlider

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `from_` / `to` | `float` | `0.0` / `100.0` | 范围 |
| `values` | `Sequence[float] \| None` | `None` | 初始区间 `(下限, 上限)` |
| `width` / `height` | `int` | `240` / `28` | 尺寸 |
| `step` | `float` | `0.0` | 步长；`0` 表示连续 |
| `command` | `Callable[[float, float], None]` | `None` | 回调，参数是 `(low, high)` |

```python
price = ctk.RangeSlider(row, from_=0, to=1000, values=(200, 800),
                        command=lambda lo, hi: print(lo, hi))
price.pack(side="left")
```

## 方法

### 取值与设值

| 控件 | 方法 | 说明 |
| --- | --- | --- |
| `Check` | `get_value()` | 当前是否勾上（`bool`） |
| | `get()` | `0` / `1`，兼容 `CTkCheckBox` 的老写法 |
| | `set_value(bool)` | 设置勾选状态，**不触发** `command` |
| | `select()` / `deselect()` | `set_value(True/False)` 的旧名字 |
| `Radio` | `get_value()` | 共享变量当前的值 |
| | `set_value(v)` | 把共享变量设成 `v`，匹配的那一项自动选中 |
| | `select()` | 选中这一项 |
| `Switch` | `get_value()` | 当前是否打开 |
| | `get()` | `0` / `1` |
| | `set_value(bool)` | 设置状态，不触发 `command` |
| | `select()` / `deselect()` | 拨到右 / 左，不触发 `command` |
| | `toggle()` | 拨一次并触发 `command` |
| `Segmented` | `get()` | 当前选中段的文字 |
| | `set(v)` | 选中 `v`，**会触发** `command` |
| `Slider` | `get()` | 当前值 |
| | `set(v, notify=False)` | 改值并重画；`notify=True` 时也触发回调 |
| `RangeSlider` | `get()` | 当前区间 `(low, high)` |
| | `set(low, hi, notify=False)` | 改区间，越界夹紧，`low > hi` 自动对调 |
| | `set_value((low, hi))` | 等价于 `set(*values)` |

```python
agree.set_value(True)
print(agree.get_value())

seg.set("月")                 # 会触发 command
scale.set(42, notify=True)

price.set_value((300, 900))
print(price.get())            # (300.0, 900.0)
```

### 启用与禁用

| 方法 | 说明 |
| --- | --- |
| `enable()` / `disable()` / `set_enabled(bool)` | 启用 / 禁用 |
| `is_enabled()` | 当前是否可用 |

`Slider` 的禁用态会同时停掉拖动与键盘；`Switch`、`Check`、`Radio` 禁用后变灰。

```python
scale.disable()
```

### 换色钩子

这几个控件都是自绘的，切外观或改令牌后由库自动调 `apply_theme()`；
如果手动改了颜色想立刻重画，也可以直接调用：

```python
seg.apply_theme()
scale.apply_theme()
price.apply_theme()
switch.apply_theme()
```

## 完整示例

```python
import tkinter as tk

import ctk_kit as ctk

app = ctk.App(title="选择示例", size=(640, 520))

card = ctk.Card(app, title="偏好")
card.pack(fill="x", padx=24, pady=24)

# 勾选
ctk.Check(card.row(1), "启动时恢复上次窗口", command=lambda: print("勾选变化")).pack(
    side="left", padx=16, pady=(0, 10)
)

# 单选：共享一个变量才互斥
mode = tk.StringVar(value="name")
row = card.row(2)
ctk.FieldLabel(row, "排序", width=64).pack(side="left")
for key, label in (("name", "名称"), ("time", "时间")):
    ctk.Radio(row, label, key, variable=mode).pack(side="left", padx=(0, 12))

# 开关
ctk.Switch(card.row(3), text="自动保存").pack(side="left", padx=16, pady=(0, 10))

# 分段
seg = ctk.Segmented(card.row(4), ["日", "周", "月"], command=lambda v: print(v))
seg.pack(side="left", padx=16, pady=(0, 10))

# 滑块
scale = ctk.Slider(card.row(5), from_=0, to=200, width=260)
scale.pack(side="left", padx=16, pady=(0, 10))

# 双滑块
price = ctk.RangeSlider(card.row(6), from_=0, to=1000, values=(200, 800))
price.pack(side="left", padx=16, pady=(0, 14))

app.mainloop()
```

## 换色

选中态统一用 `COLOR_ACCENT`，轨道 / 容器底用 `COLOR_SOFT`，关闭态用 `COLOR_MUTED`：

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_ACCENT": "#f97316"})   # 对勾、选中球、滑块圆钮
theming.apply_palette({"COLOR_SOFT": "#242731"})     # 分段容器底、滑轨
```
