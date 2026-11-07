# 媒体

## 作用

和图片、颜色打交道的五个控件：

- `Avatar` —— 圆形头像：首字母 / 图片 / 状态点。
- `Carousel` —— 卡片式轮播，支持自动播放和左右切换。
- `ImageViewer` —— 可缩放、可拖动的图片显示区。
- `ColorPicker` —— 带色块预览的下拉选色。
- `ColorDialog` —— 完整取色面板（色相 / 饱和度 / 明度 + HEX / RGB / HSV / HSL 输入）。

## 类型

| 类型 | 外观 | 用在哪 |
| --- | --- | --- |
| `Avatar` | 圆形，可带右下角状态点 | 用户、成员列表 |
| `Carousel` | 横向滑动的卡片 | 公告、推荐位 |
| `ImageViewer` | 深色画布，图片居中 | 图片预览 |
| `ColorPicker` | 色块 + 箭头，点开一列色块 | 主题色选择 |
| `ColorDialog` | 取色板 + 数值输入 | 精确调色 |

## 参数

### Avatar

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `text` | `str` | `""` | 没有图片时显示的文字，取第一个字 |
| `image` | `CTkImage \| None` | `None` | 头像图片，优先于文字 |
| `size` | `int` | `40` | 直径（逻辑像素） |
| `dim` | `float \| None` | `None` | 压暗系数，`0.8` 表示暗 20% |
| `color` | `Any` | `"accent"` | 底色，可传令牌名或颜色值 |
| `status` | `str \| None` | `None` | 状态点的颜色；传 `None` 不显示 |
| `command` | `Callable[[], None]` | `None` | 点击回调 |

```python
avatar = ctk.Avatar(card.row(1), text="张三", size=44, status=ctk.COLOR_SUCCESS)
avatar.pack(padx=16, pady=8)
```

### Carousel

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `items` | `Sequence[Any]` | `()` | 每一项交给 `command` 去画 |
| `height` | `int` | `180` | 高度 |
| `autoplay` | `int` | `0` | 自动切换间隔（毫秒），`0` 不自动 |
| `command` | `Callable[[tk.Misc, Any, int], None]` | `None` | 画第 `index` 项时调用，往第 1 个参数的容器里画 |

```python
def draw_slide(box, item, index):
    ctk.Label(box, item["title"], font=ctk.get_font(16)).pack(anchor="w", padx=16, pady=(12, 4))
    ctk.Label(box, item["body"], text_color=ctk.COLOR_MUTED).pack(anchor="w", padx=16)


carousel = ctk.Carousel(card.body(), items=slides, height=170,
                        autoplay=4000, command=draw_slide)
carousel.pack(fill="x", padx=16, pady=(0, 12))
```

### ImageViewer

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `height` | `int` | `320` | 高度 |
| `min_zoom` | `float` | `1.0` | 最小缩放 |
| `max_zoom` | `float` | `8.0` | 最大缩放 |
| `empty_text` | `str` | `"还没有图片"` | 空状态文字 |
| `empty_image` | `bool` | `True` | 空状态是否画一个占位图 |
| `on_zoom` | `Callable[[float], None]` | `None` | 缩放变化回调 |

```python
viewer = ctk.ImageViewer(card.body(), height=300, empty_text="拖一张图片进来")
viewer.set_image("cover.png")
viewer.pack(fill="x", padx=16)
```

### ColorPicker

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `value` | `str` | `"#2563eb"` | 当前颜色 |
| `colors` | `Sequence[str] \| None` | `None` | 候选色；不传用内置色板 |
| `command` | `Callable[[str], None]` | `None` | 选色回调，参数是 `#rrggbb` |
| `width` | `int` | `130` | 宽度 |

```python
picker = ctk.ColorPicker(card.row(1), value="#2563eb",
                         colors=["#2563eb", "#16a34a", "#dc2626", "#f59e0b"],
                         command=lambda c: print("选了", c))
picker.pack(padx=16)
```

### ColorDialog

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `value` | `str` | `"#2563eb"` | 初始颜色 |
| `title` | `str` | `"选择颜色"` | 标题 |
| `command` | `Callable[[str], None]` | `None` | 确定回调 |
| `icon` | `str \| None` | `None` | 标题栏图标 |
| `colors` | `Sequence[str] \| None` | `None` | 常用色快捷行 |

```python
ctk.ColorDialog(app, value="#2563eb", command=print).show()
```

## 方法

### Avatar

| 方法 | 说明 |
| --- | --- |
| `set_text(text)` | 换文字 |
| `set_image(image)` | 换图片，传 `None` 回到文字 |
| `set_status(color)` | 换状态点颜色，传 `None` 隐藏 |

```python
avatar.set_text("李四")
avatar.set_status(ctk.COLOR_WARNING)
```

### Carousel

| 方法 | 说明 |
| --- | --- |
| `show(index, notify=False)` | 切到第 `index` 项（从 0 开始） |
| `next()` / `prev()` | 下一项 / 上一项，首尾循环 |
| `start()` / `stop()` | 开始 / 停止自动播放 |

```python
carousel.next()
carousel.start()
carousel.show(0)
```

### ImageViewer

| 方法 | 说明 |
| --- | --- |
| `set_image(source)` | 设图片：路径 / `PIL.Image` / `CTkImage`；传 `None` 清空 |
| `fit()` | 缩放到刚好放得下 |
| `set_zoom(value)` | 直接设缩放倍数（自动夹在 `min_zoom`～`max_zoom`） |
| `zoom(times)` | 在当前倍数上乘 `times` |

```python
viewer.fit()
viewer.zoom(1.25)
viewer.set_zoom(2.0)
```

### ColorPicker

| 方法 | 说明 |
| --- | --- |
| `get()` / `get_value()` | 当前颜色 |
| `set(color)` / `set_value(color)` | 设颜色（不触发回调） |
| `open()` / `close()` | 展开 / 收起候选色板 |
| `set_enabled(bool)` / `enable()` / `disable()` | 启用与禁用 |
| `set_readonly(bool)` | 只读：能看不能改 |
| `is_enabled()` / `is_readonly()` | 查询状态 |

```python
picker.set("#16a34a")
print(picker.get())
picker.disable()
```

### ColorDialog

| 方法 | 说明 |
| --- | --- |
| `show()` | 弹出面板，确定后调 `command` |

## 完整示例

```python
import ctk_kit as ctk

app = ctk.App(title="媒体示例", size=(820, 620))

card = ctk.Card(app, title="媒体")
card.pack(fill="both", expand=True, padx=24, pady=16)

row = card.row(1)
ctk.Avatar(row, text="张三", size=44, status=ctk.COLOR_SUCCESS).pack(side="left", padx=(16, 12))

picker = ctk.ColorPicker(row, value="#2563eb",
                         colors=["#2563eb", "#16a34a", "#dc2626", "#f59e0b"],
                         command=lambda c: print("颜色", c))
picker.pack(side="left")

ctk.PrimaryButton(row, "打开取色面板",
                  lambda: ctk.ColorDialog(app, value=picker.get(), command=picker.set).show()
                  ).pack(side="left", padx=12)

carousel = ctk.Carousel(card.body(), items=[{"t": f"公告 {i}"} for i in range(1, 4)],
                        height=120,
                        command=lambda box, item, i: ctk.Label(box, item["t"]).pack(
                            padx=16, pady=16, anchor="w"))
carousel.pack(fill="x", padx=16, pady=12)

viewer = ctk.ImageViewer(card.body(), height=220)
viewer.pack(fill="both", expand=True, padx=16, pady=(0, 16))

app.mainloop()
```

## 换色

头像底色用 `COLOR_ACCENT`，轮播指示点用 `COLOR_FAINT` / `COLOR_ACCENT`，
图片区底色是 `COLOR_SOFT`：

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_ACCENT": "#f97316"})
theming.apply_palette({"COLOR_SOFT": "#242731"})
```
