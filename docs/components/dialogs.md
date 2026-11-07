# 对话框与菜单

## 作用

三件「临时浮出来」的东西：

- `Dialog` —— 等待用户操作的模态卡片窗口：提示、确认、输入、多按钮。
- `Popover` —— 点某个控件后弹出的浮动小卡片，用来放筛选、详情、快捷操作。
- `ContextMenu` —— 右键菜单，可以挂在任意控件上。

日常用得最多的是三个模块级快捷函数 `ctk.alert()` / `ctk.confirm()` / `ctk.prompt()`，
它们就是 `Dialog` 的预设封装。

## 类型

| 类型 | 外观 | 是否阻塞 | 用在哪 |
| --- | --- | --- | --- |
| `Dialog` | 居中卡片 + 标题 / 正文 / 按钮行 | 是（`show()` 等待） | 确认删除、输入新名字 |
| `alert()` | 只有一个「知道了」 | 是 | 告知结果 |
| `confirm()` | 确定 / 取消 | 是，返回 `bool` | 危险操作前 |
| `prompt()` | 一个输入框 + 确定 / 取消 | 是，返回 `str \| None` | 输入名字 |
| `Popover` | 贴着控件的小卡片 | 否 | 筛选器、列设置 |
| `ContextMenu` | 竖排菜单 | 否 | 右键操作 |

## 参数

### Dialog

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父窗口 |
| `title` | `str` | `""` | 标题 |
| `message` | `str` | `""` | 正文，自动换行 |
| `detail` | `str` | `""` | 正文下面的小字，可放路径、影响范围 |
| `level` | `str` | `"info"` | `"info"` / `"success"` / `"warn"` / `"error"`，决定图标颜色 |
| `buttons` | `Sequence[tuple]` | `None` | `[(文字, 返回值), ...]`；**最后一个**是主按钮 |
| `prompt` | `str \| None` | `None` | 给了初值就多一个输入框 |
| `danger` | `bool` | `False` | 主按钮是否用危险色 |
| `width` | `int` | `392` | 宽度（逻辑像素） |
| `glass` | `bool` | `True` | 是否用毛玻璃底 |
| `glass_refresh_ms` | `int` | `300` | 毛玻璃刷新间隔 |
| `glass_blur` / `glass_upscale` / `glass_blur_scale` | — | `20` / `2.0` / `0.5` | 模糊强度与采样参数 |
| `backdrop` | `str` | `"acrylic"` | 背景合成方式 |
| `corners` | `int` | `0` | `0` 跟随系统圆角，其它值是自定义圆角 |
| `gradient_top` / `gradient_bottom` | `str \| None` | `None` | 给卡片底色加竖向渐变 |

```python
dlg = ctk.Dialog(app, title="删除备份", message="这会删掉 3 个文件。", level="warn",
                 danger=True, buttons=[("取消", False), ("删除", True)])
if dlg.show():
    ...
```

### alert / confirm / prompt

| 函数 | 签名 | 返回 |
| --- | --- | --- |
| `alert` | `alert(master, message, *, title="", level="info", ok="知道了", detail="")` | `None` |
| `confirm` | `confirm(master, message, *, title="", level="warn", ok="确定", cancel="取消", detail="", danger=False)` | `bool`：点 `ok` 为 `True` |
| `prompt` | `prompt(master, message, *, title="", value="", ok="确定", cancel="取消", detail="")` | 输入的文字；取消为 `None` |

```python
ctk.alert(app, "导出完成", title="完成", level="success")

if ctk.confirm(app, "删除这份备份？", danger=True, ok="删除"):
    remove_backup()

name = ctk.prompt(app, "给备份起个名字", value="backup-01")
if name:
    print("新名字", name)
```

### Popover

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `widget` | `tk.Misc` | 必填 | 弹出锚点（通常是个按钮） |
| `content` | `Callable[[tk.Misc], None]` | `None` | 往弹层里填内容 |
| `width` | `int` | `240` | 宽度 |
| `placement` | `str` | `"bottom"` | `"bottom"` / `"top"` |
| `padding` | `int` | `12` | 内边距 |
| `glass` | `bool` | `True` | 是否毛玻璃底 |
| `acrylic` | `bool` | `False` | 是否用 DWM 亚克力 |
| `acrylic_tint` | `int \| None` | 系统默认 | 亚克力的 tint |

```python
def fill(box):
    ctk.Label(box, "按时间排序").pack(anchor="w")
    ctk.Switch(box, text="只看失败").pack(anchor="w", pady=(8, 0))

pop = ctk.Popover(btn, content=fill, width=220)
btn.on_click(lambda event: pop.toggle())
```

### ContextMenu

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `width` | `int` | `132` | 菜单宽度 |
| `font` | `tuple` | `("微软雅黑", 12)` | 字体 |

```python
menu = ctk.ContextMenu(app, width=150)
menu.add_command("复制", copy).add_separator().add_command("删除", remove)
```

## 方法

### Dialog

| 方法 | 说明 |
| --- | --- |
| `show()` | 显示并等待用户操作，返回按下的按钮对应的值 |

`show()` 会阻塞到用户点按钮或关掉窗口。返回值来自 `buttons` 里那组 `(文字, 返回值)`。

### Popover

| 方法 | 说明 |
| --- | --- |
| `show()` | 打开；已经开着就什么也不做 |
| `hide()` | 关掉 |
| `toggle()` | 开着就关，关着就开 |

```python
pop.show()
pop.hide()
```

### ContextMenu

| 方法 | 说明 |
| --- | --- |
| `add_command(label, command=None, *, enabled=None)` | 追加一项，返回菜单自己 |
| `add_separator()` | 追加分隔线 |
| `add_command(...).add_separator()` | 可以连着写 |
| `clear()` | 清空所有项 |
| `has_command(label)` | 有没有叫 `label` 的项 |
| `remove_command(label)` | 删掉第一个叫 `label` 的项 |
| `rename_command(label, new_label)` | 改名 |
| `show(x, y, *, source=None)` | 在屏幕坐标处弹出 |
| `close()` / `visible()` | 收起 / 是否正显示 |

```python
menu.add_command("重命名", rename, enabled=True)
menu.show(event.x_root, event.y_root, source=widget)
print(menu.visible())
```

### 给控件挂右键菜单

不想自己管 `show()` 时，用这两个函数一次挂好：

| 函数 | 说明 |
| --- | --- |
| `attach_menu(widget, items)` | 挂自定义菜单；`items` 是 `[(文字, 回调), ...]`，返回菜单对象 |
| `attach_edit_menu(widget)` | 挂「复制 / 粘贴 / 剪切 / 清空」输入框菜单，返回菜单对象 |

```python
ctk.attach_menu(tile, [("复制", copy), ("删除", remove)])
ctk.attach_edit_menu(entry)      # 输入框自带，一般不用手动调
```

## 完整示例

```python
import ctk_kit as ctk

app = ctk.App(title="对话框示例", size=(620, 420))

card = ctk.Card(app, title="对话框")
card.pack(fill="x", padx=24, pady=24)

row = card.row(1)


def do_confirm():
    if ctk.confirm(app, "删除后无法恢复。", title="删除备份", danger=True, ok="删除"):
        ctk.notify(app, "已删除", level="success")


def do_prompt():
    name = ctk.prompt(app, "给备份起个名字", value="backup-01", title="新建备份")
    if name:
        ctk.alert(app, f"将创建 {name}", title="已记录", level="info")


ctk.PrimaryButton(row, "确认框", command=do_confirm).pack(side="left", padx=16)
ctk.SecondaryButton(row, "输入框", command=do_prompt).pack(side="left")
ctk.Avatar(row, text="志", command=lambda: print("点头像")).pack(side="left", padx=(10, 0))

app.mainloop()
```

## 换色

对话框的图标颜色由 `level` 决定（`COLOR_ACCENT` / `COLOR_SUCCESS` / `COLOR_WARN` /
`COLOR_DANGER`），按钮用主 / 次要按钮的同一套颜色，背景走毛玻璃。

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_DANGER": "#f43f5e"})    # 危险按钮与错误图标
theming.apply_palette({"COLOR_ACCENT": "#f97316"})    # 主按钮与信息图标
```

右键菜单与弹层的底色固定 `#2B2B2B`，与下拉框、日期弹层保持一致。
