# 窗口

## 作用

`App` 就是 `customtkinter.CTk` 的子类，负责窗口本身：尺寸、位置、外观模式、
DWM 毛玻璃背景、标题栏的图标与按钮，以及窗口关闭时的收尾。

它对 `CTk` 的增强集中在三件事：

1. **构造参数更省事**：`size=`、`min_size=`、`center=` 直接写在构造里，不用构造完再调。
2. **Windows 合成**：`backdrop="acrylic"` 打开 DWM 亚克力 / Mica，随系统实时模糊。
3. **配色与外观**：`apply_palette()` 让整棵控件树运行时换色，`set_appearance_mode()`
   切换深浅时不用逐个控件改。

## 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `title` | `str \| None` | `None` | 窗口标题，设成 `None` 就不改系统标题 |
| `size` | `Sequence[int] \| None` | `None` | 初始尺寸 `(宽, 高)`，**逻辑像素**（125% 缩放时 800 实际占 1000 屏像素） |
| `min_size` | `Sequence[int] \| None` | `None` | 最小尺寸 `(宽, 高)`，同一套单位 |
| `appearance` | `str \| None` | `None` | `"light"` / `"dark"` / `"system"`；`None` 表示沿用上次记住的值 |
| `theme` | `str \| None` | `None` | 窗口合成主题：`"acrylic"` / `"mica"` / `"frosted"` / `"dark"` |
| `center` | `bool` | `False` | 是否把窗口居中到屏幕 |
| `notifier` | `bool` | `True` | 是否自动建一个提示条管理器（`app.notify(...)` 要用） |
| `icon` | `Any` | `True` | `True` 用库自带 logo，也可传图片路径或 `CTkImage` |
| `remember_geometry` | `bool` | `True` | 关闭时把窗口位置和尺寸存到 `~/.ctk-kit/window.json`，下次打开还原 |
| `remember_theme` | `bool` | `True` | 记住上次的外观模式 |
| `backdrop` | `str \| None` | `"acrylic"` | 桌面背景合成方式；`"none"` 表示用不透明底色 |
| `state` | `Any` | `None` | 传入 `WindowStateStore()` 时，位置 / 尺寸 / 外观都交给它持久化 |
| `**kwargs` | — | — | 透传给 `CTk`（`fg_color` 等） |

```python
app = ctk.App(
    title="ctk-kit 演示",
    size=(1200, 800),
    min_size=(380, 220),
    center=True,
    backdrop="acrylic",
)
```

## 方法

### 尺寸与位置

| 方法 | 说明 |
| --- | --- |
| `set_size((w, h))` | 改尺寸，逻辑像素，返回自己 |
| `get_size()` | 当前 `(宽, 高)`，同一套单位 |
| `set_position((x, y))` | 把窗口左上角移到屏幕坐标，返回自己 |
| `get_position()` | 当前左上角屏幕坐标 `(x, y)` |
| `center()` | 移到屏幕中央，返回自己 |
| `get_scale()` | 系统缩放比例（100% → `1.0`，125% → `1.25`） |
| `frame_bounds()` | 含阴影的真实屏幕矩形 `(left, top, right, bottom)`，物理像素 |

```python
app.set_size((1000, 700)).center()
print(app.get_size(), app.get_position(), app.get_scale())
```

### 外观与配色

| 方法 | 说明 |
| --- | --- |
| `set_appearance_mode("dark")` | 切深浅色；窗口里挂了 `SidebarNav` 时由它接管（只重建当前页） |
| `toggle_appearance()` | 在浅色 / 深色之间切换 |
| `set_theme("mica")` | 换窗口合成主题，返回自己 |
| `set_theme_color("#101014")` | 只改当前主题的底色，不换主题 |
| `get_theme()` / `get_theme_color()` | 读回主题名 / 底色 |
| `set_color_theme(path)` | 换 CustomTkinter 的颜色主题文件，**只影响之后创建的控件** |
| `apply_palette({"COLOR_ACCENT": "#f97316"})` | 改令牌并立刻刷新整棵树，返回被改动的令牌 |
| `reset_palette()` | 恢复默认配色，返回被改动的令牌名 |

```python
from ctk_kit import theming

app.apply_palette({"COLOR_ACCENT": "#f97316"})
theming.apply_palette({"COLOR_CARD": "#16181f"})   # 等价写法
```

### 毛玻璃与背景

| 方法 | 说明 |
| --- | --- |
| `set_backdrop("acrylic")` | `"acrylic"` / `"mica"` / `"none"`；开了之后窗口底与侧边栏画纯黑透出桌面模糊 |
| `toggle_backdrop()` | 在不透明与毛玻璃之间切换 |
| `current_backdrop()` | 当前是哪种背景 |
| `set_frost_backdrop(color, alpha)` | 开一个底层同尺寸窗口做「磨砂」效果 |
| `clear_frost_backdrop()` | 关掉底层颜色窗口 |
| `frost_active()` / `frost_layer()` | 是否开着 / 底层窗口对象本身 |
| `glass_options()` | 当前毛玻璃参数 |
| `set_glass_options(**kwargs)` | 改毛玻璃参数并立即生效 |
| `set_glass_kind(...)` | 换 DWM 的合成方式 |
| `set_glass_state(4)` | 直接写 `AccentState`：`0` 关、`2` 透明、`3` 模糊、`4` 亚克力 |
| `set_system_backdrop(2)` | 直接写 `DWMWA_SYSTEMBACKDROP_TYPE`：`1` 无、`2` Mica、`3` 亚克力、`4` 标签 |
| `set_tint("#000000")` / `set_tint_alpha(180)` | 玻璃 tint 的底色 / 压暗程度（0–255，越高越黑） |
| `set_opacity(0.96)` | 整个窗口的透明度 |
| `set_window_corners(2)` | `0` 系统默认、`1` 不圆、`2` 圆、`3` 小圆 |
| `set_border_color("#2b2b2b")` / `set_caption_color(...)` | 边框色 / 标题栏色 |

```python
app.set_backdrop("acrylic").set_tint("#000000").set_tint_alpha(200)
```

### 标题栏

| 方法 | 说明 |
| --- | --- |
| `show_titlebar_icon(bool)` | 显示 / 隐藏标题栏左上角的图标 |
| `show_titlebar_title(bool)` | 显示 / 隐藏标题栏上的标题文字 |
| `show_window_buttons(bool)` | 整组显示 / 隐藏右侧三个窗口按钮 |
| `show_minimize_button(bool)` | 单独显示 / 隐藏最小化按钮 |
| `show_maximize_button(bool)` | 单独显示 / 隐藏最大化按钮 |
| `window_buttons_visible()` | 三个按钮是否整组显示 |
| `minimize_button_visible()` / `maximize_button_visible()` | 单个按钮是否显示（整组关掉时也算不显示） |
| `titlebar_items()` | `{"icon": bool, "title": bool}` |
| `set_titlebar_items(icon=..., title=...)` | 一次改图标和标题的显隐，返回改完后的状态 |
| `hide_frame_border()` | 去掉窗口四周那条 1px 系统边框（Win11 22H2+） |

!!! note "关闭按钮不能单独隐藏"
    最小化、最大化各占一个独立的样式位，可以单独关。关闭按钮和系统菜单绑定，
    只能随整组一起关；整组关掉时 Windows 也不再画标题栏图标槽，左上角图标会一起消失，
    恢复整组按钮时库会重新挂一次图标。

```python
app.show_window_buttons(False)        # 三个都不显示
app.show_minimize_button(False)       # 只藏最小化，关闭和最大化还在
print(app.titlebar_items())           # {'icon': True, 'title': True}
```

### 页面与关闭

| 方法 | 说明 |
| --- | --- |
| `show_page("设置")` | 切到某一页，等价于 `self.nav.show(name)` |
| `current_page()` | 当前页面名；没挂 `SidebarNav` 时是 `None` |
| `on_close(fn)` | 注册关闭前回调，返回自己；传 `None` 恢复默认 |
| `notify("已保存")` | 弹一条提示，等价于 `self.notifier.show(...)` |
| `register_themeable(widget)` | 登记一个带 `apply_theme()` 的外壳控件，切外观时自动调用 |
| `set_transitions(...)` | 窗口出现 / 消失 / 重建时的 DWM 过渡动画 |

```python
def _ask():
    ctk.confirm(app, "退出？", "未保存的改动会丢失")

app.on_close(_ask)
app.notify("已保存")
```

## 完整示例

```python
import ctk_kit as ctk

app = ctk.App(title="窗口示例", size=(720, 480), center=True, backdrop="acrylic")

card = ctk.Card(app, title="窗口")
card.pack(fill="x", padx=24, pady=24)

row = card.row(1)
ctk.PrimaryButton(row, "切换外观", command=app.toggle_appearance).pack(side="left")
ctk.SecondaryButton(row, "藏按钮", command=lambda: app.show_window_buttons(False)).pack(
    side="left", padx=(10, 0)
)
ctk.SecondaryButton(row, "恢复按钮", command=lambda: app.show_window_buttons(True)).pack(
    side="left", padx=(10, 0)
)
ctk.DangerButton(row, "关闭", command=app.destroy).pack(side="left", padx=(10, 0))

app.mainloop()
```

## 换色

窗口自身的颜色（底色、标题栏、边框）走 DWM，控件颜色走令牌：

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_BG": "#0f1115"})     # 窗口底色
app.set_tint("#000000").set_tint_alpha(200)         # 玻璃压暗程度
app.set_window_corners(2)                           # Win11 圆角
```

`set_color_theme()` 只影响之后创建的控件；想让已经存在的控件换色，用
`apply_palette()` / `theming.apply_palette()`。
