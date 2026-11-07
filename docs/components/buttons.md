# 按钮

![按钮](../assets/guide-buttons.png){ loading=lazy }

## 作用

一句话：点了会执行一件事的方块。主按钮用于「保存 / 确定」，次按钮用于「取消」，
危险按钮用于删除这类不可逆操作。

## PrimaryButton

### 作用

主操作按钮：实心主色底、白色文字，一屏里通常只放一个。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `text` | `str` | `""` | 按钮文字 |
| `command` | `Callable[[], None]` | `None` | 点击回调 |
| `width` | `int` | `110` | 宽度（逻辑像素） |
| `height` | `int` | `38` | 高度 |
| `icon` | `str` | `None` | 左侧图标字符，如 `"+"` |

### 方法

| 方法 | 说明 |
| --- | --- |
| `set_text(text)` | 改文字 |
| `get_text()` | 读文字 |
| `disable()` / `enable()` | 禁用 / 启用；禁用后变灰且点不动 |
| `set_fg_color(color)` | 改底色，`"transparent"` 表示透明 |
| `on_click(fn)` | 再挂一个点击回调（可以挂多个） |

### 示例

```python
save = PrimaryButton(card.body, "保存", command=lambda: print("保存"), width=96)
save.pack(side="left", padx=(16, 8), pady=12)

save.set_text("已保存").disable()
```

## 变体

这四个和 `PrimaryButton` 的参数、方法完全一样，只换配色，按场景挑一个即可：

| 组件 | 外观 | 用在哪 |
| --- | --- | --- |
| `SecondaryButton` | 描边、透明底 | 取消、次要操作 |
| `DangerButton` | 红底 | 删除、清空 |
| `FlatButton` | 无底色，只有文字 | 工具栏、行内链接 |
| `SoftButton` | 浅色底、深色字 | 一排并列的次级操作 |

```python
SecondaryButton(row, "取消", command=lambda: print("取消")).pack(side="left")
DangerButton(row, "删除", command=lambda: print("删除")).pack(side="left")
FlatButton(row, "了解更多", command=lambda: print("文档")).pack(side="left")
SoftButton(row, "复制", command=lambda: print("复制")).pack(side="left")
```
