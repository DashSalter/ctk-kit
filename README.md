# ctk-kit

[![CI](https://github.com/DashSalter/ctk-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/DashSalter/ctk-kit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/ctk-kit.svg)](https://pypi.org/project/ctk-kit/)
[![Python](https://img.shields.io/pypi/pyversions/ctk-kit.svg)](https://pypi.org/project/ctk-kit/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

面向 [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) 的界面基件：
一套深浅色设计令牌和一批开箱即用的控件。支持 Python 3.8 – 3.14。

## 安装

```
pip install ctk-kit
```

图片查看器需要 Pillow，单独作为可选项（不装也能用其余全部控件）：

```
pip install "ctk-kit[image]"
```

## 快速开始

```python
import customtkinter as ctk
from ctk_kit import apply_appearance, card, page_header, primary_button

apply_appearance("dark")
app = ctk.CTk()

head, info = page_header(app, "全部记录")
head.pack(fill="x", padx=20, pady=(16, 8))

box = card(app)
box.pack(fill="x", padx=20)
primary_button(box, "新建", lambda: None).pack(padx=16, pady=16)

app.mainloop()
```

想看全部控件的实际效果，装好后直接运行 `ctk-kit-showcase`。

## 组件

全部从 `ctk_kit` 顶层导入：

| 模块 | 提供 | 备注 |
| --- | --- | --- |
| `buttons` | `primary_button` `soft_button` `danger_button` `FlatButton` `SoftButton` | |
| `inputs` | `toolbar_entry` `form_entry` `segmented` `switch` `checkbox` `radio_group` `slider` `progressbar` `bind_focus_border` | |
| `text` | `TextArea` | |
| `dropdown` | `DropField` | |
| `layout` | `page_header` `section_title` `card` `divider` `field_label` `hint_label` `empty_hint` `scrollable` `style_scrollable` `style_scrollbar` | |
| `notify` | `Notifier` `notify` | |
| `scroll_list` | `LazyList` | |
| `context_menu` | `ContextMenu` `attach_menu` | |
| `collapse` | `Collapsible` | 可折叠面板 |
| `files` | `PathField` `DropZone` `pick_path` `has_dnd` | 拖放需要 `tkinterdnd2` |
| `table` | `Table` | |
| `image_view` | `ImageViewer` | 需要 Pillow |
| `pages` | `PageRebuilder` | 多页面窗口 |
| `theme` / `tokens` | `apply_appearance` `color_of` 等 | 外观与设计令牌 |

### 按钮（`buttons`）

- `primary_button(master, text, command, *, width=120, height=38, radius=9, font=FONT_BODY)`
  主操作，实心主色
- `soft_button(master, text, command, *, width=76, height=30, font=FONT_SMALL, border=False)`
  次要操作，灰底；`border=True` 时加 1px 描边
- `danger_button(master, text, command, *, width=76, height=30, font=FONT_SMALL)`
  删除一类不可逆操作，红底
- `FlatButton(master, text, command, *, bg=None, hover=None, fg=None, font=FONT_TINY, padx=10, pady=3, radius=8)`
  卡片里的小按钮，宽度按文字实测
  - `bg` / `hover` / `fg` 分别覆盖底色、悬停色、文字色（默认都从令牌取）
- `SoftButton(master, text, command)` —— `FlatButton` 的灰底版

这些工厂返回的都是 `ctk.CTkButton`，`command` 收一个无参回调。

### 输入（`inputs`）

- `toolbar_entry(master, placeholder, *, height=40)`
  工具条里的搜索框，填充底 + 1px 描边
- `form_entry(master, *, show="", placeholder="", height=38, password=False)`
  表单里的输入框；`show="•"` 或 `password=True` 走密文
- `segmented(master, values, command=None, *, width=300, height=34, font=FONT_SMALL)`
  分段选择；`command` 收选中的文字
- `switch(master, command=None, *, text="", width=44)`
  开关，`text` 留空就只显示轨道；`command` 收开关状态。圆球色是
  `COLOR_BUTTON_KNOB`，悬停色是 `COLOR_BUTTON_KNOB_HOVER`（都在 `tokens` 里改）
- `checkbox(master, text="", command=None, *, width=20, height=20)`
  勾选框，选中后填主色打勾
- `radio_group(master, values, command=None, *, variable=None, gap=8)` → `(容器, StringVar)`
  一组互斥单选；`gap` 是行距，`variable` 可以传自己的 `StringVar` 进去
- `slider(master, command=None, *, from_=0.0, to=100.0, steps=0, width=220)`
  滑块，`command` 收 `float`；`steps>0` 时只能停在等分点
- `progressbar(master, *, value=0.0, width=220, height=6)`
  细进度条，`value` 收 0~1
- `bind_focus_border(widget, *, source=None, idle_color=None, width=2, on_width=None)`
  给任意控件绑「聚焦才出现描边」的样式；`source` 是真正接焦点事件的子控件，
  `idle_color` 是不聚焦时的描边色，`on_width(width)` 在每次切换时回调

### 多行文本（`text`）

- `TextArea(master, *, placeholder="", height=200, readonly=False, show_counter=True, on_change=None, bg_color=None, text_color=None)`
  - `placeholder` 失焦时显示
  - `show_counter=True` 在底部右侧显示字数
  - `readonly=True` 只读
  - `on_change(text)` 每次内容变化回调
  - `bg_color` 默认 `COLOR_INPUT`；当日志面板用，传 `COLOR_CARD` 或 `"transparent"`
  - `text_color` 单独覆盖文字色
  - 方法：`get()` / `set(text)` / `clear()`

### 下拉（`dropdown`）

- `DropField(master, *, values_provider, command=None, placeholder="", height=36)`
  - `values_provider()` 每次展开时调用，返回候选文字列表
  - `command` 收选中的文字
  - 面板贴输入框展开；下方放不下会自动翻到上方，候选超过 8 项时面板内部滚动
  - 移动窗口时面板立刻跟随；缩放窗口时左边不动、右边界推过来就把面板裁窄，停手后归位
  - 页面滚动会改变控件位置但不产生顶层事件，由 60 ms 一次的位置比对补上；控件滚出可视区就自动收起
  - 窗口变窄时面板跟着收窄，窄到放不下就直接收起，不会伸出窗口

### 布局（`layout`）

- `page_header(master, title)` → `(head, info)`：左标题右信息
- `section_title(master, text)`：分区标题
- `card(master)`：白底卡片，1px 描边、圆角
- `divider(master, *, pady=(12, 0))`：分隔线
- `field_label(master, text, *, width=112)`：表单左侧字段名
- `hint_label(master, text)`：灰色说明文字
- `empty_hint(master, title, detail="")`：空态
- `scrollable(master)`：统一配色的滚动容器
- `style_scrollable(frame)` / `style_scrollbar(bar)`：把已有滚动控件的宽度与配色统一

### 浮层提示（`notify`）

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
- `notify(master, message, **kwargs)`：按窗口缓存 `Notifier` 的便捷函数，参数同 `show()`

```python
from ctk_kit import Notifier

tips = Notifier(app)
tips.show("已复制到剪贴板", level="success")
tips.show("云备份失败", title="网络错误", level="error", style="card", position="bottom")
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
  - `.add_command(文字, 回调)`（返回自身）、`.add_separator()`、`.clear()`
  - `.show(x, y, source=None)` / `.close()` / `.visible`
  - 同一个应用里同时只会有一个菜单：右键另一个控件时，上一个会自动收起来
  - `source` 是回调第一个参数拿到的控件

菜单开着时：拖动或缩放主窗口它会跟着走；点到外面、按 Esc、窗口失焦都会收起。

```python
from ctk_kit import attach_menu, primary_button

save = primary_button(frame, "保存")
attach_menu(save, [
    ("编辑", lambda btn: print("编辑", btn.cget("text"))),
    ("删除", lambda btn: print("删除", btn.cget("text"))),
])
```

### 表格（`table`）

- `Table(master, columns, *, row_height=36, header_height=38, max_visible_rows=8, striped=True, empty_text="暂无数据")`
  - `columns` 每项 `(标题, 宽度, 对齐)`：宽度是逻辑像素，`None` 表示吃掉剩余宽度；
    对齐取 `"w"` / `"center"` / `"e"`
  - `row_height` 行高；`header_height` 表头高
  - `max_visible_rows` 超过这个行数才出现滚动条，否则高度按行数自适应
  - `striped` 隔行底色
  - `empty_text` 没有数据时居中显示的文字
  - 方法：`set_rows(rows)` 整批替换、`rows()` 取当前数据（单元格按 `str()` 转文本）

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
  - 方法：`get()` / `set(path)` / `browse()`（弹对话框并返回选中路径）
- `DropZone(master, on_path, *, mode="any", height=96, text="把文件或文件夹拖到这里", hint="")`
  - `on_path(path)` 松手后回调；`mode` 取 `"any"` / `"file"` / `"folder"` 过滤类型
  - `text` 主提示，`hint` 是下面那行小字
- `pick_path(master, *, mode="file", title=None, initialdir=None, filetypes=None)` → `str`
  弹系统对话框，取消返回空字符串
- `has_dnd()` → `bool`：当前环境是否装了 `tkinterdnd2`。

拖放是可选能力：`pip install "ctk-kit[dnd]"`。没装时 `PathField` 的按钮照常可用，
`DropZone` 会显示成不可拖的提示。

### 多页面（`pages`）

- `PageRebuilder(host, factory, pages, *, on_hide=None)`
  - `factory(name)` 返回该页的控件
  - `pages` 是页面名序列
  - `on_hide(name)` 页面切走时回调
  - 方法：`build_all()` 把所有页面都建出来（启动时用）、`show(name)` 切页、
    `rebuild(name)` 重建某一页

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
