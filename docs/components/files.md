# 文件与路径

## 作用

三个跟本地文件打交道的工具：

- `PathField` —— 输入框 + 「浏览」按钮，选完直接把路径填进去；也能接住拖进来的文件。
- `DropZone` —— 一块虚线区域，把文件或文件夹拖进来就回调路径。
- `pick_path()` —— 直接弹系统选择框，返回选中的路径（取消返回空串）。

## 类型

| 类型 | 外观 | 用在哪 |
| --- | --- | --- |
| `PathField` | 输入框 + 右侧按钮 | 导出路径、安装目录 |
| `DropZone` | 虚线框 + 提示文字 | 拖文件导入 |
| `pick_path()` | 系统对话框 | 任何需要选路径的地方 |

## 参数

### PathField

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `mode` | `str` | `"file"` | `"file"` / `"dir"` / `"any"`，决定对话框类型 |
| `placeholder` | `str` | `""` | 空的时候显示的灰字 |
| `height` | `int` | `38` | 高度 |
| `button_text` | `str` | `"浏览"` | 按钮文字 |
| `title` | `str \| None` | `None` | 对话框标题 |
| `on_change` | `Callable[[str], None]` | `None` | 内容变化回调（输入或选择） |
| `accept_drop` | `bool` | `True` | 是否接受拖进来的文件 |
| `readonly` | `bool` | `False` | 只读：不能输入、按钮置灰 |

```python
field = ctk.PathField(card.row(1), mode="file", placeholder="选择导出位置",
                      on_change=lambda p: print("现在:", p))
field.pack(fill="x", padx=16, pady=(0, 10))
```

### DropZone

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `on_path` | `Callable[[str], None]` | 必填 | 松手时的回调，参数是路径 |
| `mode` | `str` | `"any"` | 只接受 `"file"` / `"dir"` / `"any"` |
| `height` | `int` | `96` | 高度 |
| `text` | `str` | `"把文件或文件夹拖到这里"` | 主提示 |
| `hint` | `str` | `""` | 副提示，灰色小字 |

```python
drop = ctk.DropZone(card.body(), lambda p: print("放进来了", p),
                    mode="file", height=110, hint="支持 .png / .jpg")
drop.pack(fill="x", padx=16, pady=12)
```

### pick_path()

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 用来定位对话框的父窗口 |
| `mode` | `str` | `"file"` | `"file"` / `"dir"` / `"any"` |
| `title` | `str \| None` | `None` | 对话框标题 |
| `initialdir` | `str \| None` | `None` | 初始目录 |
| `filetypes` | `list \| None` | `None` | 过滤条件，如 `[("图片", "*.png *.jpg")]` |

返回值：选中的路径；取消时返回 `""`。

```python
path = ctk.pick_path(app, mode="dir", title="选择安装目录")
if path:
    print("选中", path)
```

## 方法

### PathField

| 方法 | 说明 |
| --- | --- |
| `browse()` | 打开系统选择框（只读时直接返回空串） |
| `get()` / `get_value()` | 当前路径 |
| `set(path)` / `set_value(path)` | 直接写入，不弹框 |
| `clear()` | 清空 |
| `set_readonly(bool)` | 只读切换 |
| `is_readonly()` | 是否只读 |

```python
field.set(r"D:\out")
print(field.get())
field.clear()
field.set_readonly(True)
```

### DropZone

没有额外方法；`on_path` 在每次松手时都会调一次。

## 完整示例

```python
import ctk_kit as ctk

app = ctk.App(title="文件示例", size=(760, 560))

card = ctk.Card(app, title="导入")
card.pack(fill="x", padx=24, pady=24)

field = ctk.PathField(card.row(1), mode="file", placeholder="还没有选择文件",
                      on_change=lambda p: status.configure(text=f"选中：{p or '无'}"))
field.pack(fill="x", padx=16, pady=(0, 10))

drop = ctk.DropZone(card.row(2), lambda p: field.set(p),
                    mode="file", height=110, hint="松手后路径会自动填到上面")
drop.pack(fill="x", padx=16, pady=(0, 10))

status = ctk.HintLabel(card.row(3), "选中：无")
status.pack(padx=16, pady=(0, 12))

app.mainloop()
```

## 换色

虚线框和按钮用 `COLOR_BORDER` / `COLOR_SOFT`，拖进来的高亮用 `COLOR_ACCENT`：

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_BORDER": "#3a3f4b"})
theming.apply_palette({"COLOR_ACCENT": "#f97316"})
```
