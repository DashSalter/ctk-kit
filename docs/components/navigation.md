# 导航

## 作用

五个「带用户在内容之间移动」的控件：

- `Tabs` —— 标签页容器：一排标签 + 一个内容区。
- `Steps` —— 横向步骤条：显示当前在第几步，可点击跳转。
- `Wizard` —— 分步向导：步骤条 + 内容区 + 上一步 / 下一步。
- `Breadcrumb` —— 面包屑：显示当前位置的层级路径。
- `MenuBar` —— 横向菜单栏，下拉菜单里还能插输入框和按钮。

侧边栏导航 `SidebarNav` 不在这里，它的页面容器和页面生命周期绑在一起，见
[页面与导航](pages.md)。

## 类型

| 类型 | 外观 | 用在哪 |
| --- | --- | --- |
| `Tabs` | 顶栏标签 + 内容区 | 同一块区域放几组设置 |
| `Steps` | 圆点 + 连线 | 导入流程、向导顶部 |
| `Wizard` | 步骤条 + 内容 + 底部按钮 | 分步表单 |
| `Breadcrumb` | `A › B › C` | 文件浏览、层级页面 |
| `MenuBar` | 一行菜单 + 可插控件 | 桌面应用的顶部 |

## 参数

### Tabs

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `values` | `Sequence[str]` | `()` | 标签文字 |
| `command` | `Callable[[str], None]` | `None` | 切换回调，参数是标签文字 |
| `width` / `height` | `int` | `420` / `260` | 尺寸 |

```python
tabs = ctk.Tabs(card.body(), ["常规", "高级"], width=420, height=220)
tabs.pack(fill="both", expand=True, padx=16, pady=(0, 12))

ctk.Label(tabs.tab("常规"), "常规设置").pack(padx=12, pady=12)
```

### Steps

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `steps` | `Sequence[str]` | `()` | 各步骤名称 |
| `current` | `int` | `1` | 当前第几步（从 1 开始） |
| `command` | `Callable[[int], None]` | `None` | 点击步骤的回调 |
| `clickable` | `bool` | `False` | 是否允许点击跳转 |

```python
steps = ctk.Steps(card.body(), ["选择文件", "确认选项", "开始导入"], current=1,
                  clickable=True, command=lambda i: print("跳到", i))
steps.pack(fill="x", padx=16, pady=12)
```

### Wizard

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `steps` | `Sequence[Tuple[str, PageBuilder]]` | `()` | `(步骤名, 建内容的函数)` |
| `command` | `Callable[[Wizard], None]` | `None` | 最后一步点「完成」时调用 |

```python
def page_one(box):
    ctk.Label(box, "第一步的内容").pack(padx=12, pady=12)


def page_two(box):
    ctk.Label(box, "第二步的内容").pack(padx=12, pady=12)


wiz = ctk.Wizard(card.body(), steps=[("基本信息", page_one), ("确认", page_two)],
                 command=lambda w: print("完成于第", w.get(), "步"))
wiz.pack(fill="both", expand=True)
```

### Breadcrumb

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `items` | `Sequence[Any]` | `()` | 每一级：字符串，或 `(文字, 值)` |
| `command` | `Callable[[Any], None]` | `None` | 点击某一级的回调，参数是那一项的值 |
| `separator` | `str` | `"›"` | 分隔符 |

```python
crumb = ctk.Breadcrumb(card.row(1), items=["备份", "2026-11-07", "backup-01"],
                       command=lambda v: print("跳到", v))
crumb.pack(fill="x", padx=16)
```

### MenuBar

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `items` | `Sequence[Tuple[str, MenuEntries]]` | `()` | `(菜单名, 菜单项列表)` |
| `height` | `int` | `34` | 整条栏高度 |

菜单项列表里：

- `(文字, 回调)` 是一个菜单项；回调可以无参，也可以接一个参数（触发菜单的按钮）
- `"-"` 是分隔线
- `None` 作为回调表示这一项置灰

```python
bar = ctk.MenuBar(
    app,
    items=[
        ("文件", [("新建", new_file), ("打开", open_file), "-", ("退出", app.destroy)]),
        ("编辑", [("撤销", undo), ("重做", redo)]),
    ],
    height=36,
)
bar.pack(fill="x")
```

## 方法

### Tabs

| 方法 | 说明 |
| --- | --- |
| `tab(name)` | 取某个标签页的内容容器 |
| `set(name)` | 切换标签，并把选中标签文字改成白色 |
| `add(name)` | 加一个标签页，返回内容容器 |

```python
tabs.add("关于")
ctk.Label(tabs.tab("关于"), "v0.12.0").pack(padx=12, pady=12)
tabs.set("高级")
```

### Steps / Wizard

| 控件 | 方法 | 说明 |
| --- | --- | --- |
| `Steps` | `get()` | 当前第几步（1 开始） |
| | `set_current(n, notify=False)` | 跳到第 `n` 步 |
| | `set_value(n)` | 同 `set_current` |
| `Wizard` | `get()` | 当前第几步 |
| | `go_to(n)` | 跳到第 `n` 步并重建内容 |
| | `next()` | 下一步；最后一步时触发完成回调 |
| | `back()` | 上一步 |

```python
steps.set_current(2)
wiz.next()
wiz.back()
```

### Breadcrumb

| 方法 | 说明 |
| --- | --- |
| `set_items([...])` | 换整条路径 |
| `get_items()` | 当前路径，返回 `(文字, 值)` 列表 |

```python
crumb.set_items(["备份", "2026-11-07", "backup-02"])
print(crumb.get_items())
```

### MenuBar

| 方法 | 说明 |
| --- | --- |
| `add_menu(label, entries)` | 追加一个菜单，返回它的按钮 |
| `add_entry(placeholder, *, side="left", width=180, command=None)` | 加一个输入框；按回车时 `command` 收到当前文字 |
| `add_button(text, command, *, side="left", width=None)` | 加一个和菜单按钮同样式的按钮 |
| `add_search(placeholder="搜索", *, side="right", width=200)` | 加一个搜索框，默认靠右 |
| `add_widget(widget, *, side="left")` | 把已经建好的控件摆进来 |
| `close()` | 收起所有打开的下拉 |
| `trailing` | 靠右的容器；自己建控件时用它当 `master` |

```python
bar.add_menu("视图", [("放大", zoom_in), ("缩小", zoom_out)])
bar.add_entry("搜索项目", width=200, command=lambda text: print("搜", text))
bar.add_button("设置", open_settings)
bar.add_search("全站搜索", side="right")
```

`add_widget()` 的 `master` 规则：靠左的控件建在 `bar` 上，靠右的建在
`bar.trailing` 上，否则会抛 `ValueError`。

```python
switch = ctk.Switch(bar.trailing, text="自动保存")
bar.add_widget(switch, side="right")
```

## 完整示例

```python
import ctk_kit as ctk

app = ctk.App(title="导航示例", size=(820, 600))

bar = ctk.MenuBar(
    app,
    items=[
        ("文件", [("新建", lambda: print("新建")), "-", ("退出", app.destroy)]),
        ("帮助", [("关于", lambda: print("关于"))]),
    ],
)
bar.pack(fill="x")
bar.add_button("设置", lambda: print("设置"))

card = ctk.Card(app, title="导入")
card.pack(fill="both", expand=True, padx=24, pady=16)

crumb = ctk.Breadcrumb(card.row(1), items=["导入", "第 2 步"])
crumb.pack(fill="x", padx=16, pady=(0, 8))

steps = ctk.Steps(card.row(2), ["选择文件", "确认", "完成"], current=2, clickable=True)
steps.pack(fill="x", padx=16, pady=(0, 8))

tabs = ctk.Tabs(card.body(), ["常规", "高级"], height=200)
tabs.pack(fill="both", expand=True, padx=16, pady=(0, 12))
ctk.Label(tabs.tab("常规"), "常规选项").pack(padx=12, pady=12)
ctk.Label(tabs.tab("高级"), "高级选项").pack(padx=12, pady=12)

app.mainloop()
```

## 换色

选中标签、当前步骤、可点击的面包屑都用 `COLOR_ACCENT`，
未到达的步骤用 `COLOR_FAINT`：

```python
from ctk_kit import theming

theming.apply_palette({"COLOR_ACCENT": "#f97316"})
theming.apply_palette({"COLOR_FAINT": "#5b6270"})
```
