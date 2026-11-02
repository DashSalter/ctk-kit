# ctk-kit

[![CI](https://github.com/DashSalter/ctk-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/DashSalter/ctk-kit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/ctk-kit.svg)](https://pypi.org/project/ctk-kit/)
[![Python](https://img.shields.io/pypi/pyversions/ctk-kit.svg)](https://pypi.org/project/ctk-kit/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

面向 [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) 的界面基件：
一套深浅色设计令牌和一批开箱即用的控件。支持 Python 3.8 – 3.14。

CustomTkinter 的公开接口（`CTk`、`CTkButton`、`CTkImage` 等）也全部从 `ctk_kit`
转出；根窗口 `App` 还多收标题、尺寸、外观这些构造参数。建窗口和摆控件都只
import 这一个包就够了。

## 安装

```
pip install ctk-kit
```

图片查看器需要 Pillow，单独作为可选项（不装也能用其余全部控件，只有 `ImageViewer`
和 `CTkImage` 用不了）：

```
pip install "ctk-kit[image]"
```

## 快速开始

```python
from ctk_kit import App, Card, PageHeader, PrimaryButton

app = App(title="全部记录", size=(880, 560), min_size=(640, 400), appearance="dark")

header = PageHeader(app, "全部记录")
header.info.configure(text="共 12 条")
header.pack(fill="x", padx=20, pady=(16, 8))

box = Card(app)
box.pack(fill="x", padx=20)
PrimaryButton(box, "新建", lambda: app.notify("已保存")).pack(padx=16, pady=16)

app.mainloop()
```

想看全部控件的实际效果，运行仓库里的示例窗口：

```
python examples/basics/window.py
```

### 原生窗口与控件

customtkinter 的公开接口全部从 `ctk_kit` 转出，应用代码不用再 `import customtkinter`：

```python
from ctk_kit import App, CTkButton, CTkFrame

app = App(title="备份", size=(880, 560), min_size=(640, 400))
bar = CTkFrame(app)
CTkButton(bar, text="保存").pack()
```

`App` 是 `CTk` 的便捷子类，构造时多收这几个参数：

- `title="..."`：窗口标题，等价于 `app.title(...)`
- `size=(宽, 高)`：初始尺寸，等价于 `app.geometry("宽x高")`
- `min_size=(宽, 高)`：最小尺寸，等价于 `app.minsize(...)`
- `appearance="light" | "dark" | "system"`：建窗前设置外观
- `theme="blue" | "dark-blue" | "green" | 主题文件路径`：建窗前设置配色主题
- `center=True`：窗口建好后居中
- `notifier=True`：自动建好提示层 `self.notifier`，可以直接 `app.notify(...)`

窗口标题栏颜色也会自动跟随外观（Windows 11 22H2+ 真正上色），不需要再手动调
`set_titlebar_dark`。

`CTk` 本身仍然原样导出，需要完全原生的入口时直接用它。

- 窗口：`CTk`、`CTkToplevel`、`CTkInputDialog`
- 容器：`CTkFrame`、`CTkScrollableFrame`、`CTkTabview`
- 基础控件：`CTkLabel` `CTkButton` `CTkEntry` `CTkTextbox` `CTkCheckBox`
  `CTkRadioButton` `CTkSwitch` `CTkSlider` `CTkProgressBar` `CTkComboBox`
  `CTkOptionMenu` `CTkSegmentedButton` `CTkScrollbar`
- 字体、图片与绘制基类：`CTkFont` `CTkImage` `CTkCanvas` `CTkBaseClass`
- 外观：`set_appearance_mode(mode)` / `get_appearance_mode()` / `set_default_color_theme(name)`

除 `App`、`CTkEntry`、`CTkButton` 和 `Frame` 外，这些就是 customtkinter 自己的类，
参数、行为、回调完全一致，类型标注和 IDE 跳转照常。`App` 是加标题、尺寸等构造参数的
便捷子类；`CTkEntry` 是默认套用库输入框样式的子类——填充底、1px 描边、圆角、placeholder
灰字都从 `tokens` 取，并默认带「复制 / 粘贴 / 剪切 / 清空」右键菜单（`menu=False` 关掉）；`CTkButton` 是默认套用库按钮样式的子类——正文微软雅黑、
38 高、9 圆角、浅灰底深色字；`Frame` 是默认 `fg_color="transparent"` 的布局容器。
它们的参数都与原生同名类相同，显式传同名参数即可覆盖。
`CTkImage` 和 customtkinter 里一样需要 Pillow，但只在真正创建图片对象时才会用到。

和本库 `apply_appearance` 的分工：`set_appearance_mode` 是 CTk 原生语义，
`"system"` 表示跟随系统；`apply_appearance` 是本库的封装，只认小写 `"light"`，
其余取值（含 `"system"`）一律按深色处理。

## 组件

全部从 `ctk_kit` 顶层导入：

| 模块 | 提供 | 备注 |
| --- | --- | --- |
| `buttons` | `PrimaryButton` `SecondaryButton` `DangerButton` `FlatButton` `SoftButton` | |
| `inputs` | `ToolbarEntry` `FormEntry` `Segmented` `Switch` `Checkbox` `radio_group` `Slider` `ProgressBar` `bind_focus_border` | |
| `text` | `TextArea` | |
| `dropdown` | `DropField` | 单选下拉 |
| `select` | `TagSelectField` `TreeSelectField` | 多选标签 / 层级树，面板行为与 `DropField` 一致 |
| `layout` | `Card` `PageHeader` `SectionTitle` `divider` `vertical_divider` `FieldLabel` `HintLabel` `empty_hint` `Scrollable` `style_scrollable` `style_scrollbar` | `Card.body` 拿内容容器 |
| `misc` | `Progress` | 进度条：连续 / 分格 / 百分比 / 不确定态 |
| `notify` | `Notifier` `notify` | |
| `scroll_list` | `LazyList` | |
| `context_menu` | `ContextMenu` `attach_menu` `attach_edit_menu` | 输入框默认带菜单 |
| `collapse` | `Collapsible` | 可折叠面板 |
| `code_panel` | `CodePanel` | 卡片底部的「查看实现」折叠代码块；`set_code` 换代码 |
| `files` | `PathField` `DropZone` `pick_path` `has_dnd` | 拖放需要 `tkinterdnd2` |
| `frames` | `Frame` | 默认透明底的布局容器 |
| `table` | `Table` | `set_rows` / `add_row` / `remove_row` |
| `image_view` | `ImageViewer` | 需要 Pillow |
| `pages` | `PageRebuilder` | 多页面窗口；`add_page` / `remove_page`，页面可写 `on_show` / `on_hide` |
| `page` | `PageBase` | 页面基类：注入 `app`，子类建议实现 `bind_events`，可选 `on_show` / `on_hide` |
| `sidebar` | `SidebarNav` | 侧边栏 + 页面管理，`add_page` / `remove_page`，见下 |
| `theme` / `tokens` | `apply_appearance` `color_of` 等 | 外观与设计令牌 |
| `customtkinter` | `CTk` `App` `CTkButton` `CTkFrame` `CTkImage` `CTkFont` `set_appearance_mode` 等 | 原生类原样转出；`App` / `CTkEntry` / `CTkButton` / `Frame` 是带库默认样式或默认参数的子类，见上 |

### 按钮（`buttons`）

- `PrimaryButton(master, text, command, *, width=120, height=38, radius=9, font=FONT_BODY)`
  主操作，实心主色
- `SecondaryButton(master, text, command, *, width=76, height=30, font=FONT_SMALL, border=False)`
  次要操作，灰底；`border=True` 时加 1px 描边
- `DangerButton(master, text, command, *, width=76, height=30, font=FONT_SMALL)`
  删除一类不可逆操作，红底
- `FlatButton(master, text, command, *, bg=None, hover=None, fg=None, font=FONT_TINY, padx=10, pady=3, radius=8)`
  卡片里的小按钮，宽度按文字实测
  - `bg` / `hover` / `fg` 分别覆盖底色、悬停色、文字色（默认都从令牌取）
- `SoftButton(master, text, command)` —— `FlatButton` 的灰底版

这些工厂返回的都是 `CTkButton`，`command` 收一个无参回调。

### 输入（`inputs`）

- `ToolbarEntry(master, placeholder, *, height=40, menu=True)`
  工具条里的搜索框，填充底 + 1px 描边
- `FormEntry(master, *, show="", placeholder="", height=38, password=False, menu=True)`
  表单里的输入框；`show="•"` 或 `password=True` 走密文
- 上面两个输入框、以及 `ctk_kit.CTkEntry` 本身都支持
  `set(text)` / `append(text)` / `clear()`（覆盖、追加、清空）
- 输入框默认带「复制 / 粘贴 / 剪切 / 清空」右键菜单，`menu=False` 关掉，
  `menu=[(文字, 函数), ...]` 换成自己的项；想基于默认项扩展用 `attach_edit_menu`，
  见「右键菜单」一节
- `Segmented(master, values, command=None, *, width=300, height=34, font=FONT_SMALL)`
  分段选择；`command` 收选中的文字
- `Switch(master, command=None, *, text="", width=44)`
  开关，`text` 留空就只显示轨道；`command` 收开关状态。圆球色是
  `COLOR_BUTTON_KNOB`，悬停色是 `COLOR_BUTTON_KNOB_HOVER`（都在 `tokens` 里改）
- `Checkbox(master, text="", command=None, *, width=20, height=20)`
  勾选框，选中后填主色打勾
- `radio_group(master, values, command=None, *, variable=None, gap=8)` → `(容器, StringVar)`
  一组互斥单选；`gap` 是行距，`variable` 可以传自己的 `StringVar` 进去
- `Slider(master, command=None, *, from_=0.0, to=100.0, steps=0, width=220)`
  滑块，`command` 收 `float`；`steps>0` 时只能停在等分点
- `ProgressBar(master, *, value=0.0, width=220, height=6)`
  细进度条，`value` 收 0~1
- `Progress(master, *, value=0.0, width=240, height=8, steps=0, show_text=False,
  color=None, track=None)`
  进度条的完整版，比 `ProgressBar` 多几种形态
  - `steps>0` 时分格显示，达标的格子点亮
  - `show_text=True` 时右侧显示百分比
  - `start_indeterminate()` / `stop_indeterminate()`：不确定态，一段色块来回滚
  - `color` / `track` 可单独换已完成色和轨道色
- `Spinner(master, *, from_=0, to=100, increment=1, values=None, value=None,
  command=None, placeholder="", height=36, width=160, as_int=True)`
  带上下箭头的步进输入框
  - 数字模式：`from_` / `to` / `increment`，到边界停住；`as_int=False` 时 `get()` 收 `float`
  - 列表模式：传 `values=["小", "中", "大"]`，上下箭头在列表里前后移动，同样停在首尾
  - 也可以直接改数字后回车，会夹回区间里；`set()` 写入不触发 `command`
  - 箭头是 canvas 画的两个小三角，不依赖字体符号
- `bind_focus_border(widget, *, source=None, idle_color=None, width=2, on_width=None)`
  给任意控件绑「聚焦才出现描边」的样式；`source` 是真正接焦点事件的子控件，
  `idle_color` 是不聚焦时的描边色，`on_width(width)` 在每次切换时回调

### 多行文本（`text`）

- `TextArea(master, *, placeholder="", height=200, readonly=False, show_counter=True, on_change=None, bg_color=None, text_color=None, menu=True)`
  - `placeholder` 失焦时显示
  - `show_counter=True` 在底部右侧显示字数
  - `readonly=True` 只读
  - `on_change(text)` 每次内容变化回调
  - `bg_color` 默认 `COLOR_INPUT`；当日志面板用，传 `COLOR_CARD` 或 `"transparent"`
  - `text_color` 单独覆盖文字色
  - `menu` 含义同输入框：默认带右键菜单，`False` 关掉
  - 方法：`get()` / `set(text)` / `clear()` / `append(text)` / `insert(text, at="end")`；
    插入和追加会自动刷新字数并触发 `on_change`，只读时也能写入（写完仍保持只读）

### 下拉（`dropdown` / `select`）

- `DropField(master, *, values_provider, command=None, placeholder="", height=36, disabled=None)`
  - `values_provider()` 每次展开时调用，返回候选文字列表
  - `command` 收选中的文字
  - 面板贴输入框展开；下方放不下会自动翻到上方，候选超过 8 项时面板内部滚动
  - 移动窗口时面板立刻跟随；缩放窗口时左边不动、右边界推过来就把面板裁窄，停手后归位
  - 页面滚动会改变控件位置但不产生顶层事件，由 60 ms 一次的位置比对补上；控件滚出可视区就自动收起
  - 窗口变窄时面板跟着收窄，窄到放不下就直接收起，不会伸出窗口
  - 方法：`get()` / `set(value)` / `clear()`（`set` 不触发 `command`）
- `TagSelectField(master, *, values_provider, command=None, placeholder="", height=36, values=None, disabled=None)`
  多选标签：选中的值变成青色标签排进框里，点标签本身即可删掉
  - 值不重复；已选中的项再点一次是取消选中
  - 没有输入框：点标签区空白或右侧箭头展开候选；标签多了横向滚动（滚轮可滚，停在标签上也能滚）
  - `command` 收到当前全部标签的列表；面板点选后不关，方便连续多选
  - 方法：`get()` → `list` / `set(values)` / `clear()` / `open_menu()`
- `TreeSelectField(master, *, values_provider, command=None, placeholder="", height=36, value="", disabled=None)`
  层级树：`values_provider()` 返回嵌套的 `("分组", ["子项", ...])` 元组，字符串等于叶子
  - 分组节点只能展开 / 收起，右侧 `▶` / `▼` 跟着变；分组本身不可选中
  - 子项逐级缩进；展开 / 收起只增删受影响的那几行、不重建整个列表，再重算面板高度与翻转
  - 只有叶子能选，选中后写进输入框、收起面板并回调 `command(value)`
  - 方法：`get()` / `set(value)` / `open_menu()`
- 三个下拉都支持禁用个别候选项，接口一样：
  - `disable(value)` / `enable(value)` / `is_disabled(value) -> bool`
  - `get_disabled() -> list` / `set_disabled(values)` / `clear_disabled()`
  - 也可以构造时传 `disabled=[...]`；面板开着时改会立刻刷新
  - 禁用的项在列表里置灰、点了不响应；多选里如果它已经在标签中，`disable()` 会顺手移除

### 布局（`layout`）

- `PageHeader(master, title)` → `PageHeader`：左标题右信息，右侧标签用 `header.info` 访问（也兼容 `head, info = PageHeader(...)` 解包）
- `SectionTitle(master, text)`：分区标题
- `Card(master, *, title="")`：圆角卡片；传 `title` 时在卡片上方放标题（标题在卡片外，卡片要用 pack 放置）
- `divider(master, *, pady=(12, 0), text="", dashed=False, color=None)`：分隔线
  - `text` 给了就从左边起排一行字，右边接实线；`dashed=True` 画虚线
  - `color` 可单独指定线色（默认 `COLOR_BORDER`）
- `vertical_divider(master, *, height=20, padx=(0, 0), color=None)`：1px 宽竖线，
  用来隔开同一行里的几块内容
- `FieldLabel(master, text, *, width=112)`：表单左侧字段名
- `HintLabel(master, text)`：灰色说明文字
- `empty_hint(master, title, detail="")`：空态
- `Scrollable(master, **kwargs)`：透明底、滚动条已统一样式的滚动容器（参数同 `CTkScrollableFrame`）
- `style_scrollable(frame)` / `style_scrollbar(bar)`：把已有滚动控件的宽度与配色统一

### 浮层提示（`notify`）

`App` 自带提示层，不用手动建 `Notifier`：

```python
app.notify("已复制到剪贴板", level="success")
app.notify("云备份失败", title="网络错误", level="error", style="card", position="bottom")
```

- `Notifier(master, *, duration=None, max_visible=3)`
  - `.show(message, *, title="", level="info", position="top", style="pill", duration=None, on_close=None)`
    - `level`：`"info"` / `"success"` / `"warn"` / `"error"`
    - `position`：`"top"` / `"bottom"`
    - `style`：`"pill"`（一行窄条）或 `"card"`（带图标、标题和关闭按钮）
    - `duration`：停留秒数；`0` 常驻；不传用默认（窄条 2.6 秒、卡片 4.5 秒）
    - `on_close()`：提示消失后回调
    - 返回这条提示的控件，可以传给 `.dismiss()` 手动关掉
  - `.dismiss(view)` 关掉某一条；`.clear()` 全关；`.count(position=None)` 数条数
  - 同一位置最多 `max_visible` 条，超出时最旧的先关
- `notify(master, message, **kwargs)`：按窗口缓存 `Notifier` 的便捷函数，参数同 `show()`；
  传入 `App` 时会直接复用它的 `self.notifier`，不会建出第二个提示层
- 不需要提示的窗口可以 `App(notifier=False)`，此时没有 `self.notifier`

```python
from ctk_kit import App

app = App(title="备份", size=(880, 560))
app.notify("已复制到剪贴板", level="success")
app.notifier.show("云备份失败", title="网络错误", level="error", style="card")
```

### 懒加载列表（`scroll_list`）

- `LazyList(master, render_card, *, key_of=None, first_batch=12, load_more=8, load_delay_ms=90, load_threshold=0.92, gap=(0, 10), padx=(0, 8), item_height=None)`
  - `render_card(parent, item)` 返回一张卡片（同步、必须立刻建成）
  - `key_of(item)` 返回唯一键，用于复用已有卡片
  - `first_batch` 首屏建多少张；`load_more` 每次补多少张
  - `load_threshold` 滚到还剩多少比例时补下一批
  - `gap` 卡片纵距；`padx` 左右内缩
  - `item_height` 传了才开启虚拟滚动（卡片高度必须固定），适合几千条数据
  - 方法：`render(items, *, empty_title="这里还没有内容", empty_detail="", force=False)`

```python
listing = LazyList(frame, make_card, key_of=lambda item: item["id"])
listing.pack(fill="both", expand=True)
listing.render(items)
```

### 右键菜单（`context_menu`）

- `attach_menu(widget, items=None, *, width=132, event="<Button-3>", deep=False)` → `ContextMenu`
  - `items` 每项是 `(文字, 函数)`
  - 函数接一个参数时，拿到的就是被右键的那个控件；额外传参用 `lambda btn: fn(btn, ...)`
  - `text` 为空的项渲染成分隔线
  - `deep=True` 时连容器里的子控件一起挂上：给卡片、面板这类容器用，右键落在里面的
    文字上也会弹出（默认只绑容器自身和它露在外面的那层 canvas）
- `ContextMenu(master, *, width=132, font=FONT_SMALL)`
  - `.add_command(文字, 回调, *, enabled=None)`（返回自身）、`.add_separator()`、`.clear()`
  - `.has_command(文字)` 判断在不在；`.remove_command(文字)` 删掉第一项（顺手清掉孤立的分隔线）；
    `.rename_command(文字, 新文字)` 换显示文字、保留回调——三个都返回自身，可以链式写
  - `enabled` 传布尔或「收控件、返回布尔」的函数，弹出时按控件状态决定是否置灰
  - `.show(x, y, source=None)` / `.close()` / `.visible`
  - 同一个应用里同时只会有一个菜单：右键另一个控件时，上一个会自动收起来
  - `source` 是回调第一个参数拿到的控件
- `attach_edit_menu(widget, items=None, *, preset=True, width=132, reset=False)` → `ContextMenu`
  - 输入框的「复制 / 粘贴 / 剪切 / 清空」预设，`CTkEntry` / `FormEntry` / `ToolbarEntry` /
    `TextArea` / `DropField` 默认已经挂好，一般不用自己调
  - 项跟着状态走：没选中时「剪切 / 复制」灰、剪贴板空时「粘贴」灰、框空时「清空」灰
  - 返回菜单对象，可以继续 `add_separator()` / `add_command(...)`；重复调用拿到的是同一个
    菜单，这次传的 `items` 追加到末尾
  - `reset=True` 丢掉现有菜单重新挂一遍，改乱了可以用它恢复成默认四项

菜单开着时：拖动或缩放主窗口它会跟着走；点到外面、按 Esc、窗口失焦都会收起。

```python
from ctk_kit import attach_menu, PrimaryButton

save = PrimaryButton(frame, "保存")
attach_menu(save, [
    ("编辑", lambda btn: print("编辑", btn.cget("text"))),
    ("删除", lambda btn: print("删除", btn.cget("text"))),
])
```

输入框的菜单不用手挂，默认就有；增删改都围绕同一个菜单对象：

```python
from ctk_kit import FormEntry, attach_edit_menu

entry = FormEntry(frame)          # 右键已有复制 / 粘贴 / 剪切 / 清空
menu = attach_edit_menu(entry)    # 拿到的是同一个菜单对象

menu.add_separator()                                  # 增
menu.add_command("插入时间戳", lambda w: w.insert("insert", "12:00:00 "))

menu.rename_command("插入时间戳", "插入当前时间")       # 改：文字变化，回调不变
menu.remove_command("剪切")                            # 删：按文字删第一项

attach_edit_menu(entry, reset=True)                   # 恢复默认四项

FormEntry(frame, menu=False)      # 不要右键菜单
FormEntry(frame, menu=[("只保留这一项", fn)])   # 完全自定义
```

### 表格（`table`）

- `Table(master, columns, *, row_height=40, header_height=40, max_visible_rows=8, striped=True, empty_text="暂无数据")`
  - `columns` 每项 `(标题, 宽度, 对齐)`：宽度是逻辑像素，`None` 表示吃掉剩余宽度；
    对齐取 `"w"` / `"center"` / `"e"`
  - `row_height` 行高；`header_height` 表头高
  - `max_visible_rows` 超过这个行数才出现滚动条，否则高度按行数自适应
  - `striped` 隔行底色
  - `empty_text` 没有数据时居中显示的文字
  - 方法：`set_rows(rows)` 整批替换、`add_row(row)` 追加一行、`remove_row(index)` 删除一行、
    `rows()` 取当前数据（单元格按 `str()` 转文本）

```python
from ctk_kit import Table

table = Table(frame, [("名称", 220, "w"), ("状态", 90, "center"), ("大小", None, "e")])
table.pack(fill="x")
table.set_rows([["配置文件", "正常", "12 KB"]])
```

### 图片（`image_view`，需要 Pillow）

- `ImageViewer(master, *, height=320, min_zoom=1.0, max_zoom=8.0, empty_text="还没有图片", on_zoom=None)`
  - `set_image(path | Path | PIL.Image | None)`：换图；`None` 回到空态
  - `fit()`：缩放到适配窗口；`set_zoom(倍数)`：指定倍数；`zoom()`：读当前倍数
  - `min_zoom` 默认 `1.0`（最小就是适配窗口）；要缩得更小自己传更小的值
  - `max_zoom` 上限倍数
  - `empty_text` 没有图片时的提示
  - `on_zoom(倍数)` 倍数变化时回调
  - 滚轮以光标为中心缩放；按住左键拖动看局部；双击回到适配窗口

```python
from ctk_kit import ImageViewer

viewer = ImageViewer(frame, height=420, on_zoom=lambda z: print(f"{z:.0%}"))
viewer.pack(fill="both", expand=True)
viewer.set_image(r"D:\photos\shot.png")
```

### 可折叠面板（`collapse`）
- `Collapsible(master, *, collapsed_text="显示代码", expanded_text="隐藏代码", expanded=False, button_height=36, on_toggle=None)`
  - `collapsed_text` / `expanded_text`：收起、展开两个状态下的标题文字
  - `expanded`：初始是否展开
  - `button_height`：标题行高度
  - `on_toggle(expanded)`：状态变化回调，参数是新状态
  - 属性 `body`：内容容器，往里 pack 子控件；`button`：标题那个 `CTkButton`
  - 方法：`expand()` / `collapse()` / `toggle()` / `set_expanded(flag)` / `set_texts(collapsed_text=…, expanded_text=…)`
  - 只有标题行常驻，收起时内容区完全退出布局，不会给卡片留空隙

```python
from ctk_kit import Collapsible

panel = Collapsible(card, collapsed_text="查看实现", expanded_text="收起实现")
panel.pack(fill="x")
TextArea(panel.body, readonly=True).pack(fill="x", padx=10, pady=10)
```

### 文件与拖放（`files`，拖放需要 `tkinterdnd2`）

- `PathField(master, *, mode="file", placeholder="", height=38, button_text="浏览", title=None, on_change=None, accept_drop=True)`
  - `mode="file"` 选文件、`"folder"` 选文件夹；选中后路径**覆盖**输入框内容
  - `accept_drop=True` 时文件/文件夹可以直接拖到输入框上
  - 方法：`get()` / `set(path)` / `clear()` / `browse()`（弹对话框并返回选中路径）
- `DropZone(master, on_path, *, mode="any", height=96, text="把文件或文件夹拖到这里", hint="")`
  - `on_path(path)` 松手后回调；`mode` 取 `"any"` / `"file"` / `"folder"` 过滤类型
  - `text` 主提示，`hint` 是下面那行小字
- `pick_path(master, *, mode="file", title=None, initialdir=None, filetypes=None)` → `str`
  弹系统对话框，取消返回空字符串
- `has_dnd()` → `bool`：当前环境是否装了 `tkinterdnd2`。

拖放是可选能力：`pip install "ctk-kit[dnd]"`。没装时 `PathField` 的按钮照常可用，
`DropZone` 会显示成不可拖的提示。

### 多页面（`pages` / `sidebar`）

`SidebarNav` 把「左侧导航 + 右侧翻页」整个封装好：大标题、小标题、任意数量的
导航按钮、切页高亮、页面按需创建都在里面。

```python
from ctk_kit import App, SidebarNav

app = App(title="备份", size=(1000, 680))
nav = SidebarNav(
    app,
    title="备份",
    subtitle="v0.9.1 · 本地备份工具",
    pages={"任务": build_tasks, "设置": build_settings},
)
nav.pack(fill="both", expand=True)
nav.show("任务")
app.mainloop()
```

- `pages` 是 `{页面名: 建页函数}`；建页函数接收一个父容器，返回这一页的控件。
  也可以直接传**页面类**：类构造接收父容器，实例就是页面，页面里用
  `master.winfo_toplevel()` 就能拿到 App：
  `pages={"任务": TaskPage, "设置": SettingsPage}`
- `bottom_pages`：不放进导航列表、放在侧边栏底部的页面（例如「设置」）；
  底部按钮用次要样式，`bottom_width` 控制宽度（默认 176）
- `width`：整数是固定逻辑像素（如 `200`）；`0` 到 `1` 之间的小数是宽度比例
  （如 `0.16`），窗口拉宽时侧边栏跟着变宽
- 拖动窗口边缘时页面区会先保持旧尺寸，松手约 320ms 后再按新尺寸重排，
  避免大页面在拖动过程中逐帧重画
- 方法：`show(name)` 切页、`page(name)` 取/建某一页的容器、
  `add_page(name, builder, bottom=False)` / `remove_page(name)` 动态增删页面、
  `set_appearance_mode(mode)` / `toggle_appearance()` 切外观（只重建当前页）
- 属性：`current`、`frames`、`names`、`rebuilder`（底层的 `PageRebuilder`）
- `App` 也内置了同名转发：`app.set_appearance_mode("light")` /
  `app.toggle_appearance()`、`app.show_page(name)` / `app.current_page`。窗口上挂了
  `nav`（即 `app.nav` 是 `SidebarNav`）时自动转给它、只重建当前页；没有导航时
  直接切外观并重绘已有控件。中文 `"浅色"` / `"深色"` 也可以直接传。

底层 `PageRebuilder` 也可以单独用：

- `PageRebuilder(host, factory, pages, *, on_hide=None)`
  - `factory(name)` 返回该页的控件
  - `pages` 是页面名序列
  - `on_hide(name)` 页面切走时回调
  - `add_page(name)` / `remove_page(name)` 动态增删页面
  - 方法：`build_all()` 把所有页面都建出来（启动时用）、`show(name)` 切页、
    `rebuild(name)` 重建某一页
  - 页面切到前台时调用它的 `on_show()`；切走或重建销毁前调用 `on_hide()`
    （`PageBase` 已提供空实现，按需覆写）

## 设计令牌与外观

颜色全部是 `(浅色, 深色)` 二元组，用 `color_of()` 按当前外观取值：

```python
from ctk_kit import color_of
from ctk_kit.tokens import COLOR_ACCENT

color_of(COLOR_ACCENT)   # 深色下返回 "#2f6fed"
```

- `apply_appearance(mode)`：切外观（`"light"` / `"dark"` / `"system"`），已有控件跟着重绘
- `apply_appearance_fast(mode, *, window=None)`：切外观但**不重绘已有控件**（切主题不卡），
  之后自己重建或重绘需要的部分；`window` 传了就把窗口底色和标题栏一起刷
- `is_dark()`：当前是不是深色
- `repaint_native(widget, bg)`：给原生 tk 控件补刷背景色
- `recolor_tree(widget, bg, mode=None, *, deep=True)`：整棵子树按新外观重刷；
  `deep=False` 只刷直接子层
- `set_titlebar_dark(window, dark)`：Windows 下把标题栏也切成深色

字体、圆角、间距、滚动条宽度也都在 `ctk_kit/tokens.py` 里，各组件默认值直接引用它们，
改一处全局生效。

## License

MIT
