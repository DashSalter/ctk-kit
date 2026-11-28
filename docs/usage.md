# 使用注意

这篇不是控件手册，而是「写法速查」：把 ctk-kit 里和原生 Tkinter / CustomTkinter
不一样、但能明显少写代码的地方一条条列出来。每条都给出推荐的写法和需要避开的写法。

```python
import ctk_kit as ctk
```

## 1. 容器先选对：Frame、CTkFrame、Card

三个容器都能放控件，区别只在底色和用途：

| 控件 | 默认底色 | 用在哪 |
| --- | --- | --- |
| `ctk.Frame` | 透明 | 纯布局：分组、左右分栏、占位 |
| `ctk.CTkFrame` | 主题默认底色 | 需要一块有背景的区域 |
| `ctk.Card` | 卡片底色 + 1px 边框 + 圆角 | 页面里的一张卡片，可带标题 |

```python
page = ctk.Frame(app)                       # 透明，只负责摆位置
panel = ctk.CTkFrame(page)                  # 主题底色
card = ctk.Card(page, inside_title="账号")  # 卡片，标题在卡片内部
```

!!! note
    `Frame` 没有主题底色是刻意的：它只是布局容器。想要「一块有颜色的区域」
    用 `CTkFrame`，想要「一张卡片」用 `Card`，不要给 `Frame` 硬塞 `fg_color`
    再自己调圆角。

## 2. 建控件和布局可以连成一句

`Card`、`CTkFrame`、`Frame` 的 `pack()` / `grid()` / `place()` 都返回控件自己：

```python
card = ctk.Card(app, inside_title="登录").pack(fill="x", padx=24, pady=(24, 12))
```

`card` 就是那个卡片本身，后面继续 `card.row(...)`、`card.configure(...)` 都没问题，
IDE 也能正常提示类型。

按钮、输入框这类本来就要单独拿变量的控件，直接分两行写更清楚。

## 3. 用 `row()` 分行，不再手算 `grid`

`Card`、`CTkFrame`、`Frame` 都有 `row(index)`：按编号取一行，没有就自动建。

```python
row = card.row(2, fill="x", padx=16, pady=(0, 8))
FieldLabel(row, "用户名").pack(side="left", anchor="nw")
ctk.CTkEntry(row, placeholder="用户名").pack(
    side="left", fill="x", expand=True, padx=(8, 0)
)
ctk.SecondaryButton(row, "取消").pack(side="right")
```

几个规则：

- 同一个编号拿到的是同一行，重复调用不会建第二行；
- 编号不用连续，后建的低编号行会插到前面；
- 字段名用 `FieldLabel(row, "文字")` 放在行首，控件直接建在 `row` 上并 `pack` 到右侧；
- 不传 `pady` 时，第一行 / 中间行 / 最后一行自动分配不同间距；
- 传了 `pady` 就固定用你的值，不再参与自动重排；
- 行里的控件自己 `pack`，`row` 不是卡片，不要再往里套卡片。

```python
box = ctk.Frame(page)
ctk.FieldLabel(box.row(1), "备注").pack(side="left", anchor="nw")
ctk.Label(box.row(1), "……").pack(side="left", fill="x", expand=True, padx=(8, 0))
ctk.FieldLabel(box.row(2), "说明").pack(side="left", anchor="nw")
ctk.Label(box.row(2), "……").pack(side="left", fill="x", expand=True, padx=(8, 0))
```

## 4. 事件统一用 `on_xxx`，不写 `bind`

按钮、输入框、标签这些控件不用记 `"<Button-1>"` 这种字符串：

```python
save.on_click(lambda: save_file())              # 不需要 event 参数
entry.on_key_release(lambda event: search(event.keysym))
app.on_resize(lambda event: relayout(event.width))
```

可用方法：`on_click` / `on_double_click` / `on_right_click` / `on_enter` / `on_leave` /
`on_drag` / `on_focus` / `on_blur` / `on_key` / `on_key_release` / `on_scroll` /
`on_resize` / `on_move`。回调写不写 `event` 参数都行，写了就收到 Tk 事件对象。

!!! note
    表格没有 `on_click`，点击行走构造参数 `command=lambda index: ...`；
    右键菜单用 `attach_menu(...)`，见第 12 节。

## 5. 改文字用 `set_text`，不写 `configure(text=...)`

混入了 `Textual` 的控件（按钮、`Label`、开关、分区标题等）都有：

```python
status.set_text("已保存")
print(status.get_text())

save.set_text("保存中…").set_fg_color("#ef4444")   # 返回自己，可以连着写
```

常用选项都有对应的 `set_xxx` / `get_xxx`：`set_font`、`set_width`、`set_height`、
`set_text_color`、`set_fg_color`、`set_state` 等。

!!! note
    `set_text` 是 ctk-kit 自己的控件才有的。原生 `ctk.CTkLabel` 仍然只能用
    `configure(text=...)`；想要短写法，用 `ctk.Label`。

## 6. 取值统一 `get()` / `set(value)`

输入框、开关、分段、滑块、步进、日期、取色器都是同一套：

```python
name = name_entry.get()
name_entry.set("张三")

blur = blur_seg.get()          # 字典写法时返回映射后的值
blur_seg.set(8)
```

需要临时改一次只读控件：

```python
with field.unlocked():
    field.set("程序写入的值")
```

## 7. 只读和禁用也是一句话

```python
entry = ctk.CTkEntry(card, readonly=True)   # 能选中复制，改不了
entry.set_readonly(False)                   # 随时切换

button.disable()
button.enable()
button.toggle_enabled()
```

按钮禁用后会变灰、点不动；输入类只读时键盘拒收、下拉不展开，但 `set()` 仍然有效。

## 8. `bind_config`：界面直接绑配置

`conf_base` 的配置项可以直接绑到控件上，不用手写读配置、写配置：

```python
note_area.bind_config(UiPrefs.note)
name_entry.bind_config(UiPrefs.name)
path_field.bind_config(UiPrefs.folder)
```

- 构造后立刻用配置值填控件；
- 输入、切换、拖动会实时写回配置项（`conf_base` 会立即落盘）；
- 配置被别处修改时，控件同步更新；
- 解绑用 `unbind_config()`。

支持的控件：输入框、文本区、路径框、开关、勾选、单选/单选组、分段、下拉、
树选择、标签选择、取色器、步进器、滑块、区间滑块、日期/时间控件。类型转换
（`str` / `int` / `float` / `bool` / `list` / `date` / `time`）由绑定层处理。

也可以不写控件方法，用函数形式：

```python
ctk.bind_config(name_entry, UiPrefs.name)
```

!!! warning
    改配置值要用 `UiPrefs.name.value = "张三"`，不要写 `UiPrefs.name = "张三"`：
    后者是给类属性赋值，会把配置描述符替换成普通值，配置从此失效。

## 9. 分段、滑块、步进：值和回调更直接

`Segmented` 同时支持列表和字典；字典的键是显示文字，`get()` 返回对应的值。
`command` 收到的是分段控件本身：

```python
blur = ctk.Segmented(
    card,
    {"无": 0, "轻": 8, "强": 18},
    command=lambda widget: apply_blur(widget.get()),
)
```

滑块拖动结束才保存用 `release_command`，避免拖动过程反复写盘：

```python
volume = ctk.Slider(
    card,
    from_=0,
    to=100,
    command=on_drag,          # 拖动中，参数是数值
    release_command=save,     # 松手时，参数是数值
)
volume.set(70)                # 滑块没有 value 参数，初值用 set()
```

`Stepper` 是紧凑步进器（`[−] 70% [+]`），`Spinner` 是带上下箭头的输入框；
数值范围用 `from_` / `to` / `increment`，固定候选值用 `values=[...]`。

## 10. `PathField`：选完路径就自动载入

```python
path = ctk.PathField(
    card,
    mode="folder",
    placeholder="选择音乐文件夹",
    on_pick=lambda picked: load_folder(picked),
)
```

- `on_pick` 只在「浏览对话框选中」或「拖放」时触发，适合选完就读取；
- `on_change` 每次键入都会触发，适合做实时校验，不适合扫描目录；
- `set()` 和手工输入不会触发 `on_pick`，避免程序改路径时误扫描；
- 想重新读取当前路径，放一个「刷新」按钮再调一次读取逻辑即可。

拖放功能需要额外装可选依赖：`pip install "ctk-kit[dnd]"`。没装时仍然可以点按钮选择。

## 11. 表格：分页、局部更新、右键增删改

普通表格：

```python
table = ctk.Table(
    card,
    columns=[("姓名", 120), ("部门", 140), ("邮箱", None)],
    rows=members,
    max_visible_rows=8,
    page_size=50,                       # 大于 0 才分页
    command=lambda index: show(index),  # 下标是全量数据的下标
)
```

- `columns` 只写列名时自动分配宽度；宽度写 `None` 表示吃掉剩余宽度；
- `rows()` 返回全部数据的文本副本；`get_selected()` 读选中行；`select(index)` 选中并自动翻页；
- 单行改动用 `insert_row()` / `update_row()` / `remove_row()`，只重画当前页；
- 大批量换数据再用 `set_rows()`。

需要右键「向上添加 / 向下添加 / 编辑 / 删除」时，直接用 `CrudTable`：

```python
crud = ctk.CrudTable(
    card,
    columns=[("姓名", 120), ("部门", 140)],
    rows=members,
    on_change=lambda rows: print("数据变了", len(rows)),
)
```

`CrudTable` 的数据就是传进去的那个列表，增删改直接改它。配合 `conf_base`
时可以直接传配置项，每次操作都会立即落盘：

```python
class Prefs(ConfigBase):
    data = Section("data")
    members = data.field(default=[])

crud = ctk.CrudTable(card, columns=[...], rows=Prefs.members)
```

几千行数据完全够用；到几万行以上再考虑 SQLite 之类的存储。

## 12. 提示、对话框、右键菜单

窗口自带提示层：

```python
app.notify("保存成功", level="success")
app.notify("网络失败", level="error", position="bottom", style="card")
```

`level` 可选 `info` / `success` / `warn` / `error`；`position` 可选 `top` / `bottom`。

对话框是函数式调用：

```python
ctk.alert(app, "文件已导出", title="完成")
if ctk.confirm(app, "确定删除这条记录？", danger=True):
    delete()

text = ctk.prompt(app, "重命名", value="旧名字")   # 取消返回 None
```

右键菜单不用自己拼 Tk 菜单：

```python
ctk.attach_menu(
    table,
    [
        ("编辑", lambda widget: edit(widget)),
        ("删除", lambda widget: remove(widget)),
    ],
    deep=True,   # 卡片、面板这类容器传 True，子控件上的右键也能弹
)
```

需要动态置灰、复杂菜单结构时，用 `ctk.ContextMenu` 自己 `add_command(..., enabled=...)`
再在 `on_right_click` 里 `show(x_root, y_root)`。

## 13. 页面骨架与布局件

```python
header = ctk.PageHeader(page, "账号设置")       # 左边标题，右边提示
header.info.set_text("已自动保存")              # info 是 ctk.Label，也有 set_text

scroll = ctk.Scrollable(page)                   # 内容超长自动出滚动条
scroll.pack(fill="both", expand=True)

tabs = ctk.Tabs(card, values=("常规", "高级", "关于"))
tabs.pack(fill="x")
ctk.Label(tabs.tab("常规"), "……").pack(fill="x")

split = ctk.Splitter(page, initial=0.34, min_size=120)
split.pack(fill="both", expand=True)
ctk.Label(split.first, "目录").pack(anchor="w")
ctk.Label(split.second, "内容").pack(anchor="w")
```

- 页面里先 `PageHeader`，再 `Card`，卡片之间用 `ctk.divider(page)`；
- 需要两栏拖动分隔用 `Splitter`，左右 / 上下由 `orientation` 控制；
- 内容可能超出一屏用 `Scrollable`，批量加内容前后可以 `suspend_scrollbar()` / `resume_scrollbar()`；
- 空状态用 `ctk.empty_hint(page, "暂无数据", "点右上角新建")`，不要再手写一行灰字。

## 14. 主题与背景

```python
app = ctk.App(title="我的工具", size=(960, 600))
app.set_theme("frosted")     # mica / frosted / dark / acrylic
app.set_frost_backdrop(image="background.jpg", blur=16)
```

主题名固定四种；`set_frost_backdrop` 支持背景图片（传路径或 PIL 图），`color` / `alpha`
会变成叠在图片上的蒙层。非 Windows 平台会自动退化为纯色，不会崩。

## 15. 容易踩的坑

- **`Frame` 透明不是没布局**：它只是没有背景色，摆放控件照常。
- **`Card` 的外部 `title` 只能用 `pack`**：标题是卡片外的独立控件；用 `inside_title`
  就没有这个限制。
- **`row()` 参数只有传了才生效**：行已存在时，不传的项保持原样。
- **`bind_config` 是实时写**：输入框每次按键都会写配置；数据量大时用
  `release_command` 或保存按钮控制写入时机。
- **`PathField` 的 `on_pick` 不响应用 `set()`**：程序改路径不会误触发扫描。
- **拖放要装依赖**：`pip install "ctk-kit[dnd]"`。
- **`app.notify` 需要提示层**：`App(notifier=False)` 时没有提示层，改用 `ctk.notify(app, ...)`。
- **读表格数据用 `rows()`**：它返回副本，改副本不会影响表格；改数据走增删改或 `set_rows()`。

## 老写法 → 新写法

| 老写法 | ctk-kit 写法 |
| --- | --- |
| `label.configure(text="完成")` | `label.set_text("完成")` |
| `btn.cget("text")` | `btn.get_text()` |
| `btn.configure(state="disabled")` | `btn.disable()` |
| `widget.bind("<Button-1>", fn)` | `widget.on_click(fn)` |
| `entry.bind("<KeyRelease>", fn)` | `entry.on_key_release(fn)` |
| 手动读配置、写配置 | `widget.bind_config(Prefs.item)` |
| 自己拼 Tk 菜单 | `ctk.attach_menu(widget, [...])` |
| 自己 `after` 弹提示 | `app.notify("已保存")` |
| 表格整表重建 | `insert_row()` / `update_row()` / `remove_row()` |
