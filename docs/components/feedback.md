# 状态与提示

## 作用

一组「告诉用户现在怎么样」的控件，都是只读的，不接受输入：

- `Badge` / `Tag` —— 小徽标：状态、分类、计数。`Tag` 是 `Badge` 的别名。
- `Skeleton` —— 圆角占位条，数据没回来时占住位置并做呼吸动画。
- `LoadingOverlay` —— 铺满父容器的启动遮罩，带 logo、进度条和当前页名。
- `Progress` —— 进度条：连续 / 分格 / 带百分比 / 条纹 / 不确定态。
- `RingProgress` —— 圆环进度，可带刻度、中间显示百分比。
- `Tooltip` —— 悬停提示。
- `StatusBar` —— 窗口底部的一条状态栏。
- `Notifier` —— 窗口顶部 / 底部的浮层提示条，可堆叠、可自动消失。

## 类型

| 类型 | 外观 | 用在哪 |
| --- | --- | --- |
| `Badge` | 小圆角标签，可带圆点 | 列表项状态、表格列 |
| `Skeleton` | 灰色圆角条，呼吸动画 | 加载中的占位 |
| `LoadingOverlay` | 全屏遮罩 + logo + 进度 | 启动时 |
| `Progress` | 细长条 | 上传 / 导出 |
| `RingProgress` | 圆环 | 仪表盘、容量 |
| `Tooltip` | 深色小气泡 | 图标按钮的说明 |
| `StatusBar` | 一行灰底文字 | 主窗口底部 |
| `Notifier` | 浮层条，贴在窗口顶部 | 保存成功 / 失败 |

## 参数

### Badge / Tag

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `text` | `str` | `""` | 文字；`dot=True` 时不显示文字 |
| `color` | `str` | `"accent"` | `accent` / `success` / `warn` / `danger` / `muted`，也可直接给 `#rrggbb` |
| `variant` | `str` | `"soft"` | `"soft"` 淡底彩字 / `"solid"` 彩底白字 / `"outline"` 描边 |
| `size` | `str` | `"md"` | `"sm"` / `"md"` |
| `dot` | `bool` | `False` | 只画一个圆点 |

```python
ctk.Badge(row, "已连接", color="success").pack(side="left")
ctk.Tag(row, "3", color="accent", variant="solid", size="sm").pack(side="left", padx=(8, 0))
ctk.Badge(row, color="danger", dot=True).pack(side="left", padx=(8, 0))
```

### Skeleton

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `width` / `height` | `int` | `200` / `12` | 尺寸 |
| `radius` | `int \| None` | `6` | 圆角，`None` 用默认 |
| `animated` | `bool` | `True` | 是否做呼吸动画 |

```python
ph = ctk.Skeleton(card.row(1), width=240, height=14)
ph.pack(side="left")
```

### LoadingOverlay

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 要盖住的容器（一般就是 `app`） |
| `title` | `str` | `"ctk-kit"` | logo 下方的标题 |
| `message` | `str` | `"正在加载…"` | 初始提示 |
| `logo_size` | `int` | `96` | logo 边长 |

```python
splash = ctk.LoadingOverlay(app, title="ctk-kit", message="正在准备…")
rebuilder.build_all(progress=splash.set_progress)
splash.finish()
```

### Progress

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `value` | `float` | `0.0` | 0–1 |
| `width` / `height` | `int` | `240` / `8` | 尺寸 |
| `steps` | `int` | `0` | 分几格；`0` 表示连续 |
| `show_text` | `bool` | `False` | 右侧是否显示百分比 |
| `striped` | `bool` | `False` | 是否画斜条纹 |
| `color` / `track` | `str \| None` | `None` | 前景色 / 轨道色，默认取令牌 |
| `radius` | `int \| None` | `None` | 圆角 |
| `handle` | `bool` | `False` | 是否在末端画一个圆点 |
| `on_change` | `Callable[[float], None]` | `None` | 值变化回调 |

```python
bar = ctk.Progress(card.row(1), value=0.0, show_text=True, width=260)
bar.pack(side="left")
```

### RingProgress

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `value` | `float` | `0.0` | 0–1 |
| `size` | `int` | `140` | 外径 |
| `thickness` | `int` | `10` | 环宽 |
| `show_text` | `bool` | `True` | 中间是否显示百分比 |
| `ticks` | `int` | `0` | 外圈刻度数量；`0` 表示不画 |
| `color` / `track` | `str \| None` | `None` | 前景 / 轨道色 |
| `ring` | `bool` | `True` | 画环还是只画弧 |
| `tick_len` | `int` | `6` | 刻度长度 |

```python
ring = ctk.RingProgress(card.body(), value=0.68, size=120, ticks=24)
ring.pack(padx=16, pady=12)
```

### Tooltip

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `widget` | `tk.Misc` | 必填 | 挂在哪 |
| `text` | `str \| Callable[[], str]` | `""` | 提示文字；函数形式每次显示时求值 |
| `delay` | `int` | `500` | 悬停多久后出现（毫秒） |
| `wraplength` | `int` | `300` | 折行宽度 |
| `font` | `tuple` | `("微软雅黑", 14)` | 字体 |
| `padding` | `(int, int)` | `(14, 10)` | 内边距 |

```python
ctk.Tooltip(icon_btn, "刷新列表")
ctk.Tooltip(status, lambda: f"最后同步 {last_sync}")
```

### StatusBar

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `text` | `str` | `"就绪"` | 左侧文字 |
| `tone` | `str` | `"neutral"` | `neutral` / `success` / `warn` / `error`，决定文字色 |
| `right` | `str` | `""` | 右侧文字 |

```python
bar = ctk.StatusBar(app, text="就绪", right="v0.12.0")
bar.pack(side="bottom", fill="x")
```

### Notifier

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父窗口 |
| `duration` | `float \| None` | `None` | 自动消失秒数；`None` 用默认值，传 `0` 表示常驻 |
| `max_visible` | `int` | `3` | 同时最多显示几条 |

```python
notifier = ctk.Notifier(app, duration=2.5, max_visible=3)
notifier.show("已保存", level="success")
```

## 方法

### 徽标与占位

| 方法 | 说明 |
| --- | --- |
| `badge.set_text("已完成")` | 换文字；圆点徽标没有文字，调用被忽略 |
| `skeleton.start()` / `stop()` | 开始 / 停止呼吸动画 |

```python
badge.set_text("已完成")
skeleton.start()
skeleton.stop()
```

### 进度

| 控件 | 方法 | 说明 |
| --- | --- | --- |
| `Progress` | `get()` / `set(v)` | 读写（0–1），`set` 会先夹紧再重画 |
| | `start_indeterminate()` | 切成不确定态：一段色块来回滚 |
| | `stop_indeterminate()` | 退出不确定态，回到按 `value` 显示 |
| | `animating()` | 当前是否在跑不确定动画 |
| `RingProgress` | `get()` / `set(v)` | 读写（0–1） |
| `LoadingOverlay` | `set_progress(index, total, name)` | 更新进度与当前页名 |
| | `finish()` | 撤掉遮罩 |

```python
bar.set(0.35)
bar.start_indeterminate()
bar.stop_indeterminate()

splash.set_progress(3, 18, "组件")
splash.finish()
```

### 提示

| 控件 | 方法 | 说明 |
| --- | --- | --- |
| `Tooltip` | `set_text(...)` | 换文字；正在显示时立刻重排 |
| | `show()` / `hide()` | 立刻弹出 / 收起 |
| | `text()` | 当前文字（传函数时重新求值） |
| `StatusBar` | `set_text(text, tone=None)` | 改左侧文字，`tone` 不传就保持原色 |
| | `set_right(text)` | 改右侧文字 |
| `Notifier` | `show(message, **kwargs)` | 弹一条 |
| | `dismiss(msg_id)` / `clear()` | 关一条 / 全关 |
| | `count()` | 当前显示几条 |

```python
status.set_text("已连接", tone="success")
status.set_right("12:03")

tip.set_text("已刷新")
notifier.show("同步失败", level="error")
```

### 快捷函数

不想自己建 `Notifier` 时，用模块级 `notify()`，它用默认参数当场弹一条：

```python
ctk.notify(app, "已复制到剪贴板")
```

## 完整示例

```python
import ctk_kit as ctk

app = ctk.App(title="状态示例", size=(640, 520))

card = ctk.Card(app, title="徽标")
card.pack(fill="x", padx=24, pady=(24, 12))

row = card.row(1)
ctk.Badge(row, "在线", color="success").pack(side="left", padx=16)
ctk.Badge(row, "失败", color="danger", variant="solid").pack(side="left")
ctk.Badge(row, color="warn", dot=True).pack(side="left", padx=(8, 0))

prog_card = ctk.Card(app, title="进度")
prog_card.pack(fill="x", padx=24, pady=(0, 12))

bar = ctk.Progress(prog_card.row(1), value=0.4, show_text=True, width=280)
bar.pack(side="left", padx=16, pady=(0, 12))

ring = ctk.RingProgress(prog_card.row(2), value=0.72, size=110, ticks=18)
ring.pack(side="left", padx=16, pady=(0, 12))

# 底部状态栏
status = ctk.StatusBar(app, text="就绪", right="v0.12.0")
status.pack(side="bottom", fill="x")

# 提示按钮
btn = ctk.PrimaryButton(prog_card.row(3), "保存")
btn.pack(side="left", padx=16, pady=(0, 14))
ctk.Tooltip(btn, "写入到本地文件")

btn.on_click(lambda event: app.notify("已保存", level="success"))

app.mainloop()
```

## 换色

状态色是一组独立令牌，徽标、进度、状态栏共用：

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_SUCCESS": "#22c55e"})
theming.apply_palette({"COLOR_WARN": "#f59e0b"})
theming.apply_palette({"COLOR_DANGER": "#f43f5e"})
```

`Progress` / `RingProgress` 在换色后会自动重画；徽标与状态栏在重建时取新令牌。
