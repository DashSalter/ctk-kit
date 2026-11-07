# 窗口

## 作用

`App` 是整个程序的窗口：创建它就有标题栏、深浅色切换、毛玻璃背景、
记住上次的大小和位置，以及关闭时的清理。

## App

### 作用

主窗口。继承 `customtkinter.CTk`，可以像普通窗口一样 `pack` 内容。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `title` | `str` | `"ctk-kit"` | 窗口标题 |
| `size` | `(int, int)` | `(1000, 700)` | 初始宽高 |
| `min_size` | `(int, int)` | `(360, 240)` | 最小宽高 |
| `appearance` | `str` | `None` | `"dark"` / `"light"` / `"system"` |
| `theme` | `str` | `None` | CTk 的颜色主题（`blue` / `dark-blue` / `green`），不是下面的窗口主题 |
| `center` | `bool` | `True` | 是否在屏幕上居中 |
| `backdrop` | `str` | `None` | 启动时是否开玻璃：`"acrylic"` / `"none"`；窗口主题用 `set_theme()` 切 |
| `icon` | `str` | `None` | 窗口图标路径 |
| `remember_geometry` | `bool` | `True` | 记住上次的尺寸与位置 |
| `remember_theme` | `bool` | `True` | 记住上次的深浅色 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `set_theme(name)` | 切主题：`"Mica"` / `"Frosted"` / `"Dark"` / `"Acrylic"`，一次改好外观、玻璃、tint |
| `get_theme()` | 当前主题名（小写） |
| `set_theme_color(color)` | 只改当前主题的底色，不换主题 |
| `set_appearance_mode(mode)` | 切深浅色，整个窗口一起换 |
| `apply_palette(updates)` | 改一组颜色令牌并重绘 |
| `reset_palette()` | 恢复默认配色 |
| `set_backdrop(mode)` | 底层开关：`"acrylic"`（开玻璃）/ `"none"`（关） |
| `set_frost_backdrop(color)` | 在窗口背后加一层毛玻璃 |
| `show_window_buttons(visible)` | 显示 / 隐藏标题栏那三个按钮 |
| `show_minimize_button(visible)` | 只控制最小化按钮 |
| `show_maximize_button(visible)` | 只控制最大化按钮 |
| `show_titlebar_icon(visible)` | 显示 / 隐藏标题栏图标 |
| `show_titlebar_title(visible)` | 显示 / 隐藏标题栏标题 |
| `go(page)` | 跳到某个页面（配合 `SidebarNav`） |
| `toast(text, level="info")` | 右上角弹一条提示 |
| `close()` | 关闭窗口 |

### 示例

```python
import ctk_kit as ctk

app = ctk.App(title="我的工具", size=(900, 600), backdrop="acrylic")
ctk.Label(app, "你好").pack(padx=24, pady=24)

app.set_appearance_mode("light")
app.apply_palette({"COLOR_ACCENT": "#f97316"})
app.mainloop()
```
