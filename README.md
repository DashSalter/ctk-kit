# ctk-kit

[![Docs](https://img.shields.io/badge/docs-ctk--kit-4f46e5.svg)](https://dashsalter.github.io/ctk-kit/)
[![CI](https://github.com/DashSalter/ctk-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/DashSalter/ctk-kit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/ctk-kit.svg)](https://pypi.org/project/ctk-kit/)
[![Python](https://img.shields.io/pypi/pyversions/ctk-kit.svg)](https://pypi.org/project/ctk-kit/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

📖 **完整文档：<https://dashsalter.github.io/ctk-kit/>** —— 每个控件的参数、方法、可复制示例。

面向 [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) 的界面基件：
一套毛玻璃设计令牌和一批开箱即用的控件。支持 Python 3.8 – 3.14。

CustomTkinter 的公开接口（`CTk`、`CTkButton`、`CTkImage` 等）也全部从 `ctk_kit`
转出；根窗口 `App` 还多收标题、尺寸、外观这些构造参数。建窗口和摆控件都只
import 这一个包就够了。

## 安装

```
pip install ctk-kit
```

`pip` 会一并装上 Pillow 与 conf_base：Pillow 负责勾选/单选指示符、`Spinner`
箭头、`Progress` / `RingProgress` 的圆角与圆弧抗锯齿，`ImageViewer` 也需要它；
conf_base 用来记住窗口大小和位置。

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
- `icon=True`：窗口图标（标题栏左上角 + 任务栏），默认用内置 logo；
  传 `False` 不设，传字符串则用自定义的 `.ico` / `.png`
- `remember_geometry=True`：关闭时记住窗口大小和位置，下次启动自动恢复；
  需要有 `state`（见下）；传 `False` 关掉
- `remember_theme=True`：记住上次选择的外观和颜色主题，下次启动自动恢复；
  同样需要 `state`；传 `False` 关掉

窗口标题栏颜色也会自动跟随外观（Windows 11 22H2+ 真正上色），不需要再手动调
`set_titlebar_dark`。

### 记住窗口大小和位置

核心库**不内置持久化**：数据存哪、用什么格式是使用方的事。要用就把一个「状态
存储」对象传给 `state`，它需要提供这几个方法：

| 方法 | 说明 |
| --- | --- |
| `read_geometry()` | 返回 `(宽, 高, x, y)`，没有记录返回 `None` |
| `write_geometry(width, height, x, y)` | 保存几何（宽高逻辑像素、x/y 屏幕物理像素） |
| `read_appearance()` / `write_appearance(mode)` | `light` / `dark` / `system` |
| `read_color_theme()` / `write_color_theme(name)` | 主题名或文件路径 |
| `read_backdrop()` / `write_backdrop(mode)` | `none` / `acrylic` |

`examples/basics/window_state.py` 是一个现成的实现（用 `conf_base` 写到
`~/.ctk-kit/window.json`），可以直接抄：

```python
from window_state import WindowStateStore

app = App(title="备份", size=(880, 560), state=WindowStateStore())
app.mainloop()
```

不传 `state` 就什么都不记，`remember_geometry` / `remember_theme` 也就没有作用。
最大化/最小化关闭时不会覆盖上次的普通几何；配置损坏或字段缺失时静默回退到
`size`。

### 记住外观和颜色主题

`App` 默认也会记：调用 `app.set_appearance_mode(...)` 或
`app.set_color_theme(...)` 时，把选择写进同一个配置文件，下次启动自动恢复。

```python
app = App(title="备份", state=WindowStateStore())   # 启动时沿用上次的浅色/深色和主题
app.set_appearance_mode("light")   # 同时写进配置
app.set_color_theme("green")       # 只影响之后创建的控件
```

临时切换不想影响下次启动，传 `save=False`：

```python
app.set_appearance_mode("dark", save=False)
```

不想要这个行为就传 `remember_theme=False`（或者干脆不传 `state`）。

自定义配色也走同一个存储：状态对象提供 `read_palette()` / `write_palette(palette)`
即可，`App.apply_palette(...)` 会自动写入，下次启动在**建控件之前**恢复：

```python
app.apply_palette({"COLOR_ACCENT": "#e11d48"})   # 立即换色并保存
app.reset_palette()                              # 恢复默认配色
```

### 内置 logo

仓库里带一张 logo，放在 `ctk_kit/logo/`，`App` 默认就挂上：

| 文件 | 用途 |
| --- | --- |
| `logo.png` | 1024 主图，透明背景 |
| `logo-16.png` … `logo-256.png` | 预渲染的小图，运行时不用再缩放 |
| `logo.ico` | 多尺寸 Windows 图标 |
| `logo-source.jpg` | 原始手绘图，留档用 |

```python
from ctk_kit import ICON_PATH, LOGO_PATH, load_logo, set_window_icon

set_window_icon(some_toplevel)        # 给别的窗口也挂上
photo = load_logo(96)                 # 拿一张 PhotoImage 放到 canvas / label
print(LOGO_PATH, ICON_PATH)           # 需要原图路径时
```

`ImageViewer` 的空状态默认画这张 logo：没设置图片时中间显示图标，下面一行
「还没有图片」。不想要图标就 `ImageViewer(frame, empty_image=False)`，回到纯文字。

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
| `badge` | `Badge` `Tag` | 只读状态标签 / 计数徽标 / 状态点 |
| `inputs` | `ToolbarEntry` `FormEntry` `Segmented` `Switch` `Checkbox` `radio_group` `Slider` `ProgressBar` `Spinner` `bind_focus_border` | |
| `tabs` | `Tabs` | 页签视图，封装 `CTkTabview` |
| `calendar` | `Calendar` `DatePicker` | 月历 / 日期选择，周一开始 |
| `range` | `RangeSlider` | 双滑块区间选择 |
| `search` | `SearchBox` | 带放大镜和清空按钮的搜索框 |
| `steps` | `Steps` `Wizard` | 步骤条 / 分步向导 |
| `avatar` | `Avatar` | 圆形头像 + 右下状态点 |
| `breadcrumb` | `Breadcrumb` | 面包屑，中间层级可点 |
| `carousel` | `Carousel` | 卡片轮播，可自动播放 |
| `color` | `ColorPicker` | 预设色板选色 |
| `menubar` | `MenuBar` | 顶部菜单栏，下拉复用 `ContextMenu` |
| `popover` | `Popover` | 点击弹出的浮动卡片 |
| `placeholder` | `Skeleton` | 加载占位条，默认呼吸 |
| `splitter` | `Splitter` | 可拖动分栏 |
| `statusbar` | `StatusBar` | 底部状态栏 |
| `timeline` | `Timeline` | 纵向时间线 |
| `treeview` | `TreeView` | 树形表格（基于 `ttk.Treeview`） |
| `choices` | `Check` `Radio` | 勾选 / 单选的指示符，Pillow 抗锯齿绘制 |
| `text` | `TextArea` | |
| `dropdown` | `DropField` | 单选下拉 |
| `select` | `TagSelectField` `TreeSelectField` | 多选标签 / 层级树，面板行为与 `DropField` 一致 |
| `layout` | `Card` `PageHeader` `SectionTitle` `divider` `vertical_divider` `FieldLabel` `HintLabel` `empty_hint` `Scrollable` `style_scrollable` `style_scrollbar` | `Card.body` 拿内容容器 |
| `misc` | `Progress` `RingProgress` | 进度条 / 圆环：连续、分格、条纹、不确定态、刻度 |
| `notify` | `Notifier` `notify` | |
| `dialog` | `Dialog` `alert` `confirm` `prompt` | 模态，无边框圆角卡片 |
| `scroll_list` | `LazyList` | |
| `context_menu` | `ContextMenu` `attach_menu` `attach_edit_menu` | 输入框默认带菜单 |
| `collapse` | `Collapsible` | 可折叠面板 |
| `code_panel` | `CodePanel` | 卡片底部的「查看实现」折叠代码块；`set_code` 换代码 |
| `files` | `PathField` `DropZone` `pick_path` `has_dnd` | 拖放需要 `tkinterdnd2` |
| `frames` | `Frame` | 默认透明底的布局容器 |
| `table` | `Table` | `set_rows` / `add_row` / `remove_row` / `set_page` / `set_page_size` |
| `image_view` | `ImageViewer` | 依赖 Pillow（已在必需依赖里） |
| `pages` | `PageRebuilder` | 多页面窗口；`add_page` / `remove_page`，页面可写 `on_show` / `on_hide` |
| `page` | `PageBase` | 页面基类：注入 `app`，子类建议实现 `bind_events`，可选 `on_show` / `on_hide` |
| `loading` | `LoadingOverlay` | 启动遮罩：大 logo + 说明 + 进度条，`set_progress()` / `finish()` |
| `pagination` | `Pagination` | 页码条；`Table(page_size=…)` 的底部分页也用它 |
| `sidebar` | `SidebarNav` | 侧边栏 + 页面管理，`add_page` / `remove_page`，见下 |
| `tooltip` | `Tooltip` | 任意控件的悬停提示 |
| `theme` / `tokens` / `theming` | `apply_appearance` `color_of` `apply_palette` 等 | 外观、设计令牌与运行时换色 |
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

### 徽标与标签（`badge`）

`Badge` 是一个只读的小色块，`Tag` 是它的别名：

```python
from ctk_kit import Badge, Tag

Badge(card, "已同步", color="success")             # 淡绿底、绿字
Badge(card, "3", color="danger", variant="solid")  # 红底白字的计数
Badge(card, dot=True, color="warning")              # 一个状态点
Tag(card, "草稿", variant="outline")                # 描边标签
```

- `Badge(master, text="", *, color="accent", variant="soft", size="md", dot=False)`
  - `color`：`"accent"` / `"primary"` / `"success"` / `"warning"` / `"danger"` /
    `"error"` / `"info"` / `"neutral"`，也可以直接给颜色或 `(浅色, 深色)` 色对
  - `variant`：`"soft"`（淡底，默认）/ `"solid"`（实底）/ `"outline"`（描边）
  - `size`：`"sm"`（20 高、小一号字）/ `"md"`（24 高，默认）
  - `dot=True`：只画圆点，不显示文字
  - `.set_text(text)` / `.configure(text=...)` 换文字

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
  开关，`text` 留空就只显示轨道；`command` 收开关状态。轨道和圆球是 Pillow
  4 倍超采样画的图，边缘没有锯齿；圆球色是 `COLOR_KNOB`（和勾选框的勾、单选框的
  中心点同色），鼠标移上去换成 `COLOR_KNOB_HOVER`（都在 `tokens` 里改）
- `Checkbox(master, text="", command=None, *, width=20, height=20)`
  勾选框，选中后填主色打勾
- `radio_group(master, values, command=None, *, variable=None, gap=8)` → `(容器, StringVar)`
  一组互斥单选；`gap` 是行距，`variable` 可以传自己的 `StringVar` 进去
- `Slider(master, command=None, *, from_=0.0, to=100.0, steps=0, width=220)`
  滑块，`command` 收 `float`；`steps>0` 时只能停在等分点
- `ProgressBar(master, *, value=0.0, width=220, height=6)`
  细进度条，`value` 收 0~1
- `Progress(master, *, value=0.0, width=240, height=8, steps=0, show_text=False,
  striped=False, color=None, track=None, radius=None, handle=False, on_change=None)`
  进度条的完整版，比 `ProgressBar` 多几种形态
  - `steps>0` 时分格显示，达标的格子点亮
  - `show_text=True` 时右侧显示百分比
  - `striped=True` 时已完成部分画成 45° 斜条纹
  - `radius=0` 换成直角端点；`height=2~4` 就是细线样式
  - `handle=True` 在进度端画一个圆点把手，拖着就能改值，`on_change` 收 0~1  - `start_indeterminate()` / `stop_indeterminate()`：不确定态，一段色块来回滚
  - `color` / `track` 可单独换已完成色和轨道色
- `RingProgress(master, *, value=0.0, size=140, thickness=10, show_text=True,
  ticks=0, color=None, track=None, ring=True, tick_len=6)`
  圆环进度
  - `ticks>0` 时环外画一圈刻度，走过的刻度用主色；`ticks` 就是刻度密度
  - `ring=False` 只画刻度、不画圆环本体（纯刻度圈）
  - `tick_len` 控制每根刻度多长，默认 6
  - 有刻度时圆环自动往里收，不会和刻度重叠
  - 整块尺寸由 `size` 固定，不随容器拉伸
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
- `Stepper(master, *, values=None, from_=0, to=100, increment=1, value=None,
  command=None, width=170, height=36, suffix="%", decimals=0)`
  紧凑步进器：`[ − ] 当前值 ▾ [ + ]`
  - 左右两个按钮加减一步，点中间展开候选
  - `values` 给一组备选，或 `from_` / `to` / `increment` 走数值范围
  - `suffix` 拼在数值后面，`decimals` 控制显示几位小数
  - `get()` / `set(value)`；`command` 每次变化后收到当前值

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
- `Scrollable(master, *, auto_hide=True, **kwargs)`：透明底、滚动条已统一样式的滚动容器；
  `auto_hide=True` 时内容放得下自动隐藏滚动条，滚动条位置提前预留，显示/隐藏不会挤动内容
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

### 悬浮提示（`tooltip`）

鼠标停在控件上 0.5 秒后，下方弹一条说明；移开或按下控件就收起：

```python
from ctk_kit import Tooltip

Tooltip(save_button, "保存当前草稿")
Tooltip(status_entry, lambda: f"当前长度 {len(status_entry.get())}", delay=300)
```

- `Tooltip(widget, text="", *, delay=500, wraplength=300, font=FONT_SMALL, padding=(10, 6))`
  - `text` 可以是字符串，也可以是「返回字符串」的函数，每次弹出前现取
  - `.show()` / `.hide()` / `.set_text(text)` / `.destroy()`
  - 提示窗口不抢焦点、不进任务栏；贴着屏幕边缘时自动往上或往左收

### 对话框（`dialog`）

模态面板，和上面非阻塞的提示浮层（`notify`）分工不同：`alert` / `confirm` /
`prompt` 会停在那里等用户操作，直到点按钮或按 Esc 才返回。

没有系统标题栏，弹出就是一块圆角卡片。弹出期间主窗口**可以拖**，对话框跟着走；
但客户区点不了、滚轮也滚不动（`grab_set` + 在父窗口上拦 `<MouseWheel>`——
CTk 的滚动走 `bind_all`，光靠 grab 拦不住）。位置会夹在屏幕内——父窗口拖到
屏幕外时，对话框仍然可见、能点。

```python
from ctk_kit import alert, confirm, prompt

alert(app, "已保存到 D:/backup", title="完成", level="success")

if confirm(app, "删除这份备份？", title="删除备份", level="warn", danger=True, ok="删除"):
    ...

name = prompt(app, "给备份起个名字", title="重命名", value="backup-01")
if name is None:
    ...  # 用户按了取消
```

- `alert(master, message, *, title="", level="info", ok="知道了", detail="")`：只有一个按钮，返回 `None`
- `confirm(master, message, *, title="", level="warn", ok="确定", cancel="取消", detail="", danger=False)`
  - 返回 `True` / `False`；点取消、按 Esc、直接关窗都是 `False`
  - `danger=True` 让确认按钮变危险色
- `prompt(master, message, *, title="", value="", ok="确定", cancel="取消", detail="")`
  - 返回输入的字符串；取消或 Esc 返回 `None`；输入框里按回车等同确定
  - 初始值放在 `value` 里
- `Dialog(master, *, title="", message="", detail="", level="info", buttons=None, prompt=None, danger=False, width=392)`
  - 需要自己排版时用：`buttons=[(文字, 返回值), ...]`，最后一个按钮是主按钮（排最右）
  - `.show()` 阻塞到用户操作，返回被点按钮的 `value`；Esc / 关窗返回 `None`
  - `prompt` 传字符串就多显示一个输入框，确认时返回输入的文字（注意与
    `prompt()` 函数同名，这里只是初始值）
  - `level` 只影响左上角图标的颜色：`"info"` / `"success"` / `"warn"` / `"error"`
  - `detail` 在正文下面补一行灰色小字；`width` 固定宽度，高度跟着内容走
  - 对话框是一次性的：`show()` 结束就销毁，别拿同一个实例再调一次
- 对话框本身没有标题栏、不能拖；位置由父窗口决定。无边框窗口也没有右上角的
  关闭按钮，退出靠按钮、Esc 或 Alt+F4。

示例窗的「弹窗」页（`examples/basics/dialog_page.py`）把四种级别的信息框、
普通 / 危险确认、输入框和自定义三按钮都摆了一遍。

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

### 分页（`pagination`）

```python
from ctk_kit import Pagination

pager = Pagination(card, total=238, page_size=20, command=load_page)
pager.pack(fill="x")


def load_page(page):
    table.set_rows(fetch(page))
```

- `Pagination(master, total=0, page_size=10, *, current=1, command=None, siblings=1, show_total=False)`
  - `command(page)`：用户点页码 / 上一页 / 下一页时调用；`set_page` / `set_total` 不触发
  - `siblings`：当前页两边各留几页，多出来的折成「…」
  - `show_total=True`：左边显示「共 N 条」
  - `.set_page(page, notify=False)` / `.set_total(total)` / `.set_page_size(size)`
  - `.page` / `.pages` 读当前页和总页数

### 页签（`tabs`）

```python
from ctk_kit import Tabs

tabs = Tabs(card, values=["常规", "高级", "关于"], command=lambda name: print(name))
tabs.pack(fill="both", expand=True)
tabs.tab("常规")  # 这一页的容器
```

- `Tabs(master, *, values=(), command=None, width=420, height=260)`
  - `command(name)`：用户切换页签时调用；`set()` / 构造时选第一页不触发
  - `.add(name)` / `.tab(name)` / `.get()` / `.set(name)`
  - 底色、描边、选中色和「分段」控件一致，选中页签白字

### 日期（`calendar`）

```python
import datetime as dt

from ctk_kit import Calendar, DatePicker

cal = Calendar(card, value=dt.date(2026, 11, 3), command=lambda day: print(day))
cal.pack(padx=16, pady=16)

picker = DatePicker(card, value=dt.date(2026, 11, 3), placeholder="选择日期")
picker.pack(fill="x", padx=16, pady=(0, 16))
```

- `Calendar(master, *, year=None, month=None, value=None, command=None, width=260)`
  - 周一开始，今天描边、选中实心；`command(datetime.date)` 在点日期时调用
  - `.get()` / `.set(dt.date(2026, 11, 3))` / `.prev_month()` / `.next_month()`
- `DatePicker(master, *, value=None, placeholder="选择日期", command=None)`
  - 点输入框弹月历，选完写回；`get()` 返回 `datetime.date`，面板贴边翻转，失焦收起
  - `.get()` / `.set(value)` / `.open()` / `.close()`

### 区间滑块与搜索框（`range` / `search`）

```python
from ctk_kit import RangeSlider, SearchBox

RangeSlider(card, from_=0, to=100, values=(20, 80), command=lambda lo, hi: print(lo, hi))

SearchBox(card, placeholder="搜索组件…", command=lambda text: print(text))
```

- `RangeSlider(master, *, from_=0, to=100, values=None, width=240, height=28, step=0, command=None)`
  - 拖两个圆球选区间，松手才回调 `command(low, high)`；两个球不会交叉
  - `.get()` / `.set(low, high, notify=False)`；`step` 不为 0 时按步长吸附
- `SearchBox(master, *, placeholder="搜索", command=None, width=240, height=38, delay=300)`
  - 输入停下 `delay` 毫秒后回调，回车立即回调；`×` 清空
  - `.get()` / `.set(text)` / `.clear()` / `.search()`；`configure(command=...)` 换回调

### 步骤与向导（`steps`）

```python
from ctk_kit import CTkLabel, PrimaryButton, Steps, Wizard

Steps(card, steps=["选择文件", "设置参数", "开始备份"], current=2)


def pick_page(parent, wizard):
    PrimaryButton(parent, "选好了", command=lambda: wizard.next()).pack()


def confirm_page(parent, wizard):
    CTkLabel(parent, text="确认后开始。").pack()


Wizard(card, steps=[("选择文件", pick_page), ("确认", confirm_page)], command=lambda w: print("完成"))
```

- `Steps(master, *, steps=(), current=1, command=None, clickable=False)`
  - 完成对勾、当前数字、未开始描边；`clickable=True` 时点步骤跳转
  - `.get()` / `.set_current(step, notify=False)`
- `Wizard(master, *, steps=(), command=None)`
  - `steps` 是 `(标题, 构建函数)`；构建函数签名 `(parent, wizard)`，往 `parent` 放这一页的内容
  - 底部自动带「上一步 / 下一步」，最后一页按钮变「完成」并回调 `command(wizard)`
  - `.go_to(step)` / `.next()` / `.back()` / `.get()`

### 头像（`avatar`）

圆形头像，文字或图片都行；右下角可以挂一个在线状态点。

```python
from ctk_kit import Avatar

Avatar(card, text="ZK", size=44, status="online").pack(side="left")
Avatar(card, text="李", size=44, color="success", status="busy").pack(
    side="left", padx=12
)
```

`set_text()` / `set_image()` / `set_status()` 直接改；状态点支持
`online` / `away` / `busy` / `offline`。圆形底、状态点和图片裁圆都用
Pillow 4 倍超采样，放大看边缘也是平的。

### 面包屑与时间线（`breadcrumb` / `timeline`）

```python
from ctk_kit import Breadcrumb, Timeline

Breadcrumb(
    card,
    items=["首页", ("文档", "docs"), ("组件", "docs/components")],
    command=lambda value: print("跳到", value),
)

Timeline(card, items=[
    {"title": "创建仓库", "time": "09:12", "description": "初始化 main"},
    {"title": "发布 0.9.2", "time": "10:05", "active": True},
])
```

面包屑最后一项是当前页，不可点；`Timeline` 也可以先用空列表建好，再
`add()` 追加。默认分隔符 `›` 是 Pillow 画的折线图，时间线圆点同样用
4 倍超采样，边缘没有锯齿。

### 骨架屏（`placeholder`）

```python
from ctk_kit import Skeleton

Skeleton(card, width=220, height=14).pack(anchor="w", pady=4)
Skeleton(card, width=160, height=14).pack(anchor="w", pady=4)
```

默认在两种底色之间呼吸；`animated=False` 或 `stop()` 停住。

### 分栏（`splitter`）

```python
from ctk_kit import Splitter

split = Splitter(card, initial=0.32, min_size=100)
split.pack(fill="both", expand=True)
CTkLabel(split.first, text="目录").pack()
CTkLabel(split.second, text="内容").pack()
```

拖动中间手柄改比例，`set_ratio()` / `get_ratio()` 读写。

### 浮动卡片（`popover`）

```python
from ctk_kit import Popover, PrimaryButton

def build(parent):
    CTkLabel(parent, text="筛选条件").pack(padx=12, pady=(12, 4))
    PrimaryButton(parent, "应用").pack(padx=12, pady=(4, 12))

button = PrimaryButton(card, "筛选")
Popover(button, content=build, width=200)
```

点控件打开，点外面关闭；和 `Tooltip` 的区别是能放按钮、输入框等任意控件。

### 颜色（`color`）

```python
from ctk_kit import ColorPicker

picker = ColorPicker(card, value="#2563eb", command=lambda c: print(c))
picker.pack()
picker.get()       # 当前颜色
picker.set("#dc2626")
```

默认 12 个预设色，也可以用 `colors=` 换自己的色板。

### 状态栏（`statusbar`）

```python
from ctk_kit import StatusBar

bar = StatusBar(root, text="就绪", right="12 项")
bar.pack(side="bottom", fill="x")
bar.set_text("正在保存…", tone="warning")
```

`tone` 可选 `neutral` / `success` / `warning` / `danger`。

### 轮播（`carousel`）

```python
from ctk_kit import Carousel

Carousel(card, items=[
    ("更快", "页面切换不再重建整个窗口"),
    ("更轻", "组件按需创建"),
], height=160, autoplay=3000)
```

`show(index)` / `next()` / `prev()`；`autoplay=0` 关闭自动播放。

### 菜单栏（`menubar`）

```python
from ctk_kit import MenuBar

MenuBar(root, items=[
    ("文件", [("新建", new_file), ("打开", open_file), "-", ("退出", quit)]),
    ("编辑", [("撤销", undo), ("重做", redo)]),
]).pack(side="top", fill="x")
```

下拉复用 `ContextMenu`，圆角和悬停色跟右键菜单一致。

### 树形表格（`treeview`）

```python
from ctk_kit import TreeView

tree = TreeView(card, columns=("大小", "修改时间"), height=6)
src = tree.insert("", "src", text="src", open=True)
tree.insert(src, "main", text="main.py", values=("3.2 KB", "09:12"))
tree.insert(src, "ui", text="ui.py", values=("8.4 KB", "09:30"))
```

基于 `ttk.Treeview`，配色按 tokens 调过；切主题后调 `refresh_style()`。

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

- `Table(master, columns, *, row_height=40, header_height=40, max_visible_rows=8, striped=True, empty_text="暂无数据", page_size=0)`
  - `columns` 每项 `(标题, 宽度, 对齐)`：宽度是逻辑像素，`None` 表示吃掉剩余宽度；
    对齐取 `"w"` / `"center"` / `"e"`
  - `row_height` 行高；`header_height` 表头高
  - `max_visible_rows` 超过这个行数才出现滚动条，否则高度按行数自适应
  - `striped` 隔行底色
  - `empty_text` 没有数据时居中显示的文字
  - `page_size` 每页行数；大于 0 时底部出现分页条，表格只画当前页，
    `max_visible_rows` 不再生效；传 0 回到滚动模式
  - 方法：`set_rows(rows)` 整批替换、`add_row(row)` 追加一行、`remove_row(index)` 删除一行、
    `set_page(page)` / `set_page_size(size)` 翻页 / 改每页行数，
    `rows()` 取数据（分页时也是全量，单元格按 `str()` 转文本）
  - 属性：`pages` 总页数、`page` 当前页、`page_size` 每页行数

```python
from ctk_kit import Table

table = Table(frame, [("名称", 220, "w"), ("状态", 90, "center"), ("大小", None, "e")])
table.pack(fill="x")
table.set_rows([["配置文件", "正常", "12 KB"]])

# 分页：全量数据交给表格，内部只画当前页
paged = Table(frame, COLUMNS, page_size=20)
paged.set_rows(rows)
paged.set_page(2)
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
- `hidden_pages`：只登记、不生成导航按钮的页面（例如从头像点进去的
  「个人中心」），`show(name)` 仍然可以切过去
- `footer`：底部按钮上方的自定义区域，回调接收底部容器；可以放账号行，
  头像行排在 `bottom_pages` 按钮的上方
- `width`：整数是固定逻辑像素（如 `200`）；`0` 到 `1` 之间的小数是宽度比例
  （如 `0.16`），窗口拉宽时侧边栏跟着变宽
- `divider`：默认 `True`，在侧边栏和页面区之间画一条 1px 竖向分隔线，切深浅
  外观时跟着换色；传 `False` 不画
- `logo`：大标题左侧的图标，默认 `True` 用内置 logo；`False` 不显示，传字符串
  用自定义图片路径；`logo_size` 控制边长（默认 32 逻辑像素）
- 拖动窗口边缘时页面区会先保持旧尺寸，松手约 320ms 后再按新尺寸重排，
  避免大页面在拖动过程中逐帧重画
- 方法：`show(name)` 切页、`page(name)` 取/建某一页的容器、
  `add_page(name, builder, bottom=False)` / `remove_page(name)` 动态增删页面、
  `set_appearance_mode(mode)` / `apply_theme(mode)` / `toggle_appearance()` 切外观
  （外壳原地换色，只重建当前页）
- 属性：`current`、`frames`、`names`、`rebuilder`（底层的 `PageRebuilder`）
- `App` 也内置了同名转发：`app.set_appearance_mode("light")` /
  `app.toggle_appearance()`、`app.show_page(name)` / `app.current_page`。窗口上挂了
  `nav`（即 `app.nav` 是 `SidebarNav`）时自动转给它、只重建当前页；没有导航时
  直接切外观并重绘已有控件。中文 `"浅色"` / `"深色"` 也可以直接传。
- 不在导航里的外壳控件（状态栏、独立卡片等）实现 `apply_theme(mode)` 后，
  用 `app.register_themeable(widget)` 登记，切外观时会跟着换色、不重建。

底层 `PageRebuilder` 也可以单独用：

- `PageRebuilder(host, factory, pages, *, on_hide=None, first_of=None)`
  - `factory(name)` 返回该页的控件
  - `pages` 是页面名序列
  - `on_hide(name)` 页面切走时回调
  - `first_of(name)` 返回页面的 `cards_first`；启动时 `build_all()` 会跳过
    返回值 > 0 的页面，等第一次切过去再建
  - `add_page(name)` / `remove_page(name)` 动态增删页面
  - 方法：`build_all(progress=None)` 启动时逐页构建（跳过 `cards_first > 0`
    的页面），可传回调 `progress(done, total, name)` 驱动进度条；
    `show(name)` 切页、`rebuild(name)` 重建某一页
  - 页面切到前台时调用它的 `on_show()`；切走或重建销毁前调用 `on_hide()`
    （`PageBase` 已提供空实现，按需覆写）

页面在启动时由 `build_all()` 逐页建。组件多、构建慢的页面可以声明
`cards_first`，让它在启动时跳过、第一次切过去再建；页内前几张同步出现，
其余按 12ms 时间片补：

```python
class ExtrasPage(PageBase):
    cards_first = 3      # 0 = 整页同步建；3 = 前 3 张同步、其余分帧

    def __init__(self, master):
        super().__init__(master)
        area = Scrollable(self)
        area.pack(fill="both", expand=True)
        self.build_cards(area, [
            self._build_badges,
            self._build_tooltip,
            self._build_pagination,
            ...
        ])
```

`build_cards(area, builders, first=None)` 不传 `first` 时读 `self.cards_first`，
0 表示全部同步。分帧队列清空后 `when_built(callback)` 回调一次，适合把
`bind_events()` 放到那里。

仓库示例用 `LoadingOverlay` 做启动遮罩：

```python
from ctk_kit import LoadingOverlay

splash = LoadingOverlay(app, title="ctk-kit")
app.update()
try:
    nav.rebuilder.build_all(progress=splash.set_progress)
finally:
    splash.finish()
```

- `LoadingOverlay(master, *, title="ctk-kit", message="正在加载…", logo_size=96)`：
  铺满父容器的遮罩，内含大 logo、说明文字和 4px 进度条；
  `set_progress(done, total, name)` 驱动进度，`finish()` 撤掉。
- `build_all(progress=None)` 逐页构建，每建完一页调一次
  `progress(done, total, name)`；`cards_first > 0` 的页面留到第一次显示。
- 页面在 `__init__` 里直接 `bind_events()` 的页面要求启动时建完；用
  `build_cards` 分帧的页面改成 `self.when_built(self.bind_events)`。

示例窗口启动约 4.5 秒（「组件」页不预建），切到「组件」时先出前 3 张卡片、
其余约 2 秒内补齐。

## 设计令牌与外观

颜色令牌就是普普通通的 `"#RRGGBB"` 字符串，只有**一套毛玻璃配色**：

```python
from ctk_kit.tokens import COLOR_ACCENT

COLOR_ACCENT = "#3E4059"
```

`color_of(token)` 拿到的就是它本身（保留这个函数只为兼容旧代码，老代码里传
`(浅色, 深色)` 二元组也仍然可用，取最后一项）。

这套令牌是给 Windows 毛玻璃窗口配的：背景做成 `#000000` 的透明键色，控件
颜色直接写在 `tokens` 里，改一处全局生效，不再分深浅两套。

- `apply_appearance(mode)`：切外观（`"light"` / `"dark"` / `"system"`），已有控件跟着重绘
- `apply_appearance_fast(mode, *, window=None)`：切外观但**不重绘已有控件**（切主题不卡），
  之后自己重建或重绘需要的部分；`window` 传了就把窗口底色和标题栏一起刷
- `is_dark()`：当前是不是深色
- `repaint_native(widget, bg)`：给原生 tk 控件补刷背景色
- `recolor_tree(widget, bg, mode=None, *, deep=True)`：整棵子树按新外观重刷；
  `deep=False` 只刷直接子层
- `set_titlebar_dark(window, dark)`：Windows 下把标题栏也切成深色
- `set_window_brush(window, color=None)`：Windows 下把窗口类的擦除背景画刷换成
  `color`（默认当前 `COLOR_BG`），消除启动、最大化、还原时系统先刷黑底再渲染的
  闪黑块；`App` 构造、切主题、重建标题栏时自动调用
- `style_of(name, state, mode=None)`：从 `ctk_kit.styles` 取外壳控件的样式表，
  返回可直接解包给 `configure(**...)` 的颜色；`SidebarNav` / `Card` /
  `StatusBar` 的 `apply_theme()` 就是用它
- `App.set_glass_options(**kwargs)` / `App.glass_options()`：运行时调整窗玻璃参数
  （`kind` / `alpha` / `wca` / `state` / `backdrop` / `corners` / `border` /
  `caption` / `color` / `veil` / `opacity` / `frame` / `extend` / `titlebar` /
  `dark`），示例设置页的「毛玻璃微调」卡片就是它的面板
- `App.set_window_debug(hide_frame_border=..., disable_transitions=...)` /
  `App.window_debug()`：窗口级 DWM 调试项。`hide_frame_border` 写
  `DWMWA_VISIBLE_FRAME_BORDER_THICKNESS`（37，Win11 22H2+）去掉四周那条 1px
  系统边框，系统不支持时 `window_debug()["frame_border_supported"]` 为 `False`；
  `disable_transitions` 写 `DWMWA_TRANSITIONS_FORCEDISABLED`（3）关掉窗口出现、
  重建时的过渡动画。示例设置页的「窗口调试（DWM）」卡片就是它
- `App.frame_bounds()`：`DWMWA_EXTENDED_FRAME_BOUNDS`（9），窗口含阴影的真实
  屏幕矩形 `(left, top, right, bottom)`（物理像素），和 `winfo_rootx()` 那套
  客户区坐标并排看，能看出标题栏和边框各占多少
- `App.set_frost_backdrop(color, *, alpha=0x38, glass=False, spread=0)` /
  `App.clear_frost_backdrop()` / `App.frost_active`：在主窗口下面垫一层「颜色
  窗口」，尺寸、位置、圆角都跟着主窗口走，`spread` 让它再往外多出一圈。
  底图是纯色时 `alpha` 控透明度（0 全透、255 最实）；`glass=True` 会改成
  系统毛玻璃（这条路径会带 `WS_THICKFRAME`，尺寸要重新校正，问题较多，
  设置页没有开放）。毛玻璃模式下只开 `acrylic` 时会自动建一层默认底色
  （深色配黑、浅色配白）
- `theming.apply_palette({...})`：**运行时换色**——改 `tokens` 全局值，把已经存在
  的控件颜色属性一起换掉并重绘，之后新建的控件自动用新色；返回实际改掉的令牌名。
  颜色写 `"#RRGGBB"`，未知令牌会被忽略；`repaint=False`
  只改令牌不刷界面（启动阶段用）。`reset_palette()` 还原默认配色，
  `current_palette()` 取当前全部令牌，`palette_changes()` 取被覆盖的那些，
  `save_palette()` / `load_palette()` 读写整份调色板 JSON。毛玻璃下
  `COLOR_BG` / `COLOR_SIDE` 仍保持透明键色，用户挑的普通底色记成基准，切回不透明
  时生效。自绘控件（canvas / Pillow）无法靠换属性刷新，用
  `theming.register_redraw(widget, fn)` 登记重绘回调
- `App.apply_palette(updates, *, save=True)` / `App.reset_palette(*, save=True)`：
  上面那套的窗口级封装，会顺带把覆盖写进状态存储（`read_palette` / `write_palette`），
  启动时自动恢复。示例左侧导航的「主题」页就是它的面板
- `paint.animate_color(widget, option, start, end, duration=150)`：把某个颜色
  选项从 `start` 渐变到 `end`，返回可 `cancel()` 的句柄；同一控件同一选项
  不会叠加多套定时器
- `fonts.measure_text(text, font)`：按字体量一行文字的宽度，不触发几何重排

字体、圆角、间距、滚动条宽度也都在 `ctk_kit/tokens.py` 里，各组件默认值直接引用它们，
改一处全局生效。

## License

MIT
