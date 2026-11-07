# 文件

![文件](../assets/guide-files.png){ loading=lazy }

## 作用

选路径和收拖放：一个「输入框 + 浏览按钮」，一个「把文件拖进来」。

> 取值型控件同时支持 `set_value(...)` / `get_value()` 与简写 `set(...)` / `get()`，两者完全等价；下文统一用 `set_value` / `get_value`。

## PathField

### 作用

路径输入框 + 「浏览」按钮；默认还接受拖放，把文件拖进输入框就填好路径。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `mode` | `str` | `"file"` | `"file"` 选文件 / `"folder"` 选文件夹 |
| `placeholder` | `str` | `""` | 占位文字 |
| `button_text` | `str` | `"浏览"` | 按钮文字 |
| `accept_drop` | `bool` | `True` | 是否接受拖放 |
| `on_change` | `Callable[[str], None]` | `None` | 内容变化回调 |
| `readonly` | `bool` | `False` | 只读时不能改、也不能点浏览 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `get_value()` / `set_value(path)` | 读 / 写路径（`set_value` 会触发 `on_change`；等价于 `get()` / `set()`） |
| `clear()` | 清空 |
| `browse()` | 弹选择框，返回选中的路径，取消返回 `""` |
| `set_readonly(flag)` | 只读开关 |

### 示例

```python
path = PathField(card.body, mode="folder", placeholder="选择一个目录",
                 on_change=lambda p: print("现在指向", p))
path.pack(fill="x", padx=16, pady=(0, 12))

print(path.get_value())
```

## DropZone

### 作用

一块虚线框区域，把文件或文件夹拖进去，松手后回调完整路径。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `on_path` | `Callable[[str], None]` | 必填 | 拖入后的回调，参数是路径 |
| `mode` | `str` | `"any"` | `"any"` / `"file"` / `"folder"` |
| `height` | `int` | `96` | 高度 |
| `text` | `str` | `"把文件或文件夹拖到这里"` | 主文字 |
| `hint` | `str` | `""` | 下面一行灰色提示 |

### 示例

```python
zone = DropZone(card.body, on_path=lambda p: print("收到", p), mode="file")
zone.pack(fill="x", padx=16, pady=(0, 12))
```

## pick_path

### 作用

直接弹系统的文件 / 文件夹选择框，不建控件。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父窗口 |
| `mode` | `str` | `"file"` | `"file"` / `"folder"` |
| `title` | `str` | `None` | 对话框标题 |
| `initialdir` | `str` | `None` | 起始目录 |
| `filetypes` | `Sequence[(说明, 通配符)]` | `None` | 文件类型过滤 |

### 示例

```python
path = pick_path(app, mode="file", title="选择配置",
                 filetypes=[("JSON", "*.json")])
if path:
    load(path)
```
