# 按钮

## 作用

按钮触发一个动作：保存、取消、删除、打开某个面板。ctk-kit 的按钮统一用
`customtkinter.CTkButton` 渲染，圆角、底色、悬停色、字号都来自设计令牌，
所以整站的按钮长得一致，改令牌就能整体换色。

![按钮组件](../assets/buttons.png){ loading=lazy }

工厂函数**只负责创建，不负责摆位**：拿到的是普通的 `CTkButton`，
用 `pack()` / `grid()` / `place()` 自己放。

## 类型

| 类型 | 外观 | 高度 | 圆角 | 用在哪 |
| --- | --- | --- | --- | --- |
| `PrimaryButton` | 强调色底 + 浅字 | 38 | 9 | 一屏里最重要的动作：保存、搜索、立即备份 |
| `SecondaryButton` | 浅灰底 + 正文色字 | 30 | 8 / 9 | 并列动作：取消、刷新、选择目录 |
| `DangerButton` | 淡红底 + 红字 | 30 | 8 | 删除、清空这类不可逆动作 |
| `FlatButton` | 浅灰底，宽度随文字 | 按行高 | 8 | 卡片角落的「复制 / 显示 / 详情」 |
| `SoftButton` | 灰字，更小的内边距 | 按行高 | 6 | 比 `FlatButton` 更安静的小按钮 |

还有一个类 `CTkButton`：不带任何具体配色，只有库的默认样式（38 高、9 圆角、
`COLOR_SOFT` 底、`COLOR_TEXT` 字）。需要自己配一套颜色时直接用它，
其余五个都是在它上面换配色得到的。


## 参数

### 公共参数

五个工厂函数的前三个参数完全一样，`CTkButton` 也一样：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `text` | `str` | 必填 | 按钮文字 |
| `command` | `Callable[[], None]` | `None` | 点击回调，**不接收参数** |
| `width` | `int` | `140` | 宽度（像素） |
| `height` | `int` | `38` | 高度（像素） |
| `corner_radius` | `int` | `9` | 圆角半径 |
| `border_width` | `int` | `0` | 边框宽度 |
| `border_spacing` | `int` | `10` | 文字与边框的内缩 |
| `fg_color` | `str` | `COLOR_SOFT` | 常态底色 |
| `hover_color` | `str` | `COLOR_SOFT_HOVER` | 悬停底色 |
| `border_color` | `str` | `COLOR_BORDER` | 边框颜色 |
| `text_color` | `str` | `COLOR_TEXT` | 文字颜色 |
| `text_color_disabled` | `str` | CustomTkinter 默认 | 禁用态文字颜色 |
| `font` | `tuple \| CTkFont` | `FONT_BODY` | `("微软雅黑", 13)` |
| `state` | `str` | `"normal"` | `"normal"` / `"disabled"` |
| `bg_color` | `str` | `"transparent"` | 父容器底色，一般不用传 |
| `image` | `CTkImage` | `None` | 图标 |
| `compound` | `str` | `"left"` | 图标与文字的位置关系 |
| `textvariable` | `tk.Variable` | `None` | 用变量驱动文字 |
| `hover` | `bool` | `True` | 是否响应悬停 |


```python
ctk.PrimaryButton(row, "保存", command=save).pack(side="left")
ctk.SecondaryButton(row, "取消", command=close, border=True).pack(side="left", padx=(8, 0))
ctk.DangerButton(row, "删除", command=remove).pack(side="left", padx=(8, 0))
ctk.FlatButton(card, "复制", command=copy_text).pack(side="right")
```

## 方法

### 改文字

| 方法 | 说明 |
| --- | --- |
| `set_text("保存中…")` | 改文字，返回自己 |
| `get_text()` | 读回当前文字 |

```python
btn.set_text("保存中…")
btn.set_text("保存")
```

### 启用与禁用

| 方法 | 说明 |
| --- | --- |
| `disable()` | 禁用：变灰、点不动，返回自己 |
| `enable()` | 恢复，返回自己 |
| `toggle_enabled()` | 在启用 / 禁用之间切换，返回自己 |
| `set_enabled(True)` | 按布尔值设，返回自己 |
| `is_enabled()` | 当前是否可用 |

```python
btn.disable()          # 请求期间不许重复点
btn.enable()
```

### 改样式

任何选项都有对应的 `set_xxx(value)` / `get_xxx()`，`set_xxx` 返回控件自己，
可以连着写：

| 写法 | 作用 |
| --- | --- |
| `btn.set_fg_color("#ef4444")` | 换底色 |
| `btn.set_text_color("#ffffff")` | 换文字色 |
| `btn.set_hover_color("#dc2626")` | 换悬停色 |
| `btn.set_font(("微软雅黑", 15))` | 换字体 |
| `btn.set_width(160)` | 改宽度 |
| `btn.get_text()` / `btn.get_fg_color()` | 读回当前值 |

```python
btn.set_fg_color("#ef4444").set_height(44).set_corner_radius(10)
```

支持 `set_xxx` 的名字是按钮的所有选项（`text`、`width`、`height`、
`font`、`state`、`command` 等）和所有以 `_color` 结尾的选项。
名字拼错会直接抛 `AttributeError`，不会悄悄改错东西。

### 点击与回调

| 方法 | 说明 |
| --- | --- |
| `click()` | 以编程方式点一下 |
| `set_command(fn)` | 换点击回调，返回自己 |
| `set_command(fn, *args)` | 换回调并预先绑好参数，返回自己 |

Tk 调 `command` 时永远不传参数，所以参数要在绑定时定死：

```python
btn.set_command(delete_row, 42)               # → delete_row(42)
btn.set_command(delete_row, 42, force=True)   # → delete_row(42, force=True)
btn.set_command(None)                         # 不再响应点击
```

### 事件

常用的鼠标、键盘、尺寸事件有现成方法，回调收到事件对象，传 `None` 解绑：

| 方法 | 事件 |
| --- | --- |
| `on_click(fn)` | 左键按下 |
| `on_double_click(fn)` | 左键双击 |
| `on_right_click(fn)` | 右键按下（做右键菜单时用） |
| `on_enter(fn)` / `on_leave(fn)` | 鼠标移入 / 移出 |
| `on_drag(fn)` | 按住左键拖动 |
| `on_focus(fn)` / `on_blur(fn)` | 键盘焦点进入 / 离开 |
| `on_key(fn)` / `on_key_release(fn)` | 按键按下 / 松开（看 `event.keysym`） |
| `on_scroll(fn)` | 鼠标滚轮 |
| `on_resize(fn)` / `on_move(fn)` | 尺寸 / 位置真的变了才触发 |

```python
btn.on_click(lambda event: print("点在", event.x, event.y))
btn.on_right_click(show_menu)
btn.on_click(None)     # 解绑
```

需要事件对象（鼠标坐标、按了哪个键）时用这些方法；只是「点一下做什么」
用 `command` / `set_command` 就够。

## 完整示例

```python
import ctk_kit as ctk

app = ctk.App(title="按钮示例", size=(640, 420))

card = ctk.Card(app, title="动作")
card.pack(fill="x", padx=24, pady=(24, 12))

# card.row(1) 是第 1 行的容器，同一个编号复用同一个 Frame
ctk.PrimaryButton(card.row(1), "保存", command=lambda: print("保存")).pack(side="left")
ctk.SecondaryButton(card.row(1), "取消", command=app.destroy).pack(
    side="left", padx=(10, 0)
)
ctk.SecondaryButton(card.row(1), "清除", command=lambda: print("清除"), border=True).pack(
    side="left", padx=(10, 0)
)
ctk.DangerButton(card.row(1), "删除", command=lambda: print("删除")).pack(
    side="left", padx=(10, 0)
)

# 卡片角落的小按钮：宽度随文字走
ctk.HintLabel(card.row(2), "改动会立即生效").pack(side="left")
ctk.FlatButton(card.row(2), "复制", command=lambda: print("复制")).pack(side="right")
ctk.SoftButton(card.row(2), "收起").pack(side="right", padx=(0, 8))

app.mainloop()
```

`card.row(index)` 等价于手写 `row = ctk.Frame(card)` + `row.pack(fill="x", padx=16)`，
同一个编号反复调用拿到的是同一个容器，行按编号从上往下排；想改某行的间距直接
`card.row(2, pady=(0, 14))`。

## 换色

按钮的颜色全部来自令牌，改令牌就是改整个程序里所有按钮：

```python
from ctk_kit import theming

# 主按钮底色（同时影响强调文字、分页当前页）
theming.apply_palette({"COLOR_ACCENT": "#f97316"})

# 次要按钮、卡片底色一起用的柔和底色
theming.apply_palette({"COLOR_SOFT": "#242731"})
```

已经在界面上的按钮会立即换色，不需要重建页面。
