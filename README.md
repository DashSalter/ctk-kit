# ctk-kit

[![CI](https://github.com/DashSalter/ctk-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/DashSalter/ctk-kit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/ctk-kit.svg)](https://pypi.org/project/ctk-kit/)
[![Python](https://img.shields.io/pypi/pyversions/ctk-kit.svg)](https://pypi.org/project/ctk-kit/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

面向 [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) 的轻量界面基件：
一套深浅色设计令牌、一批常用控件，以及一个会自动分页的懒加载列表。
提示信息不再只能当成一行文字写进布局——`Notifier` 把它浮在窗口顶部或底部，
不占地方，几秒后自己消失。
支持 Python 3.8 – 3.14。

写它的起因很朴素——每个 customtkinter 项目都要重新调一遍颜色、圆角、按钮宽度和滚动列表的
分批渲染，调完还很难看齐。ctk-kit 把这些收成一层薄薄的公共件，项目之间可以直接复用。

```
pip install ctk-kit
```

```python
import customtkinter as ctk
from ctk_kit import apply_appearance, primary_button, page_header

apply_appearance("Dark")
app = ctk.CTk()

head, info = page_header(app, "全部记录")
head.pack(fill="x", padx=20, pady=(16, 8))
primary_button(app, "新建", lambda: None).pack()
app.mainloop()
```

看实际效果：示例随包发布，装好 ctk-kit 后可以直接跑：

```
pip install ctk-kit
ctk-kit-showcase
```

也可以从源码运行（不用安装）：

```
git clone https://gitee.com/kuangjianke/ctk-kit
cd ctk-kit
python examples/showcase.py
# 等价写法
python -m ctk_kit.showcase
```

每个页面也能单独启动，改哪一页就只跑哪一页：

```
python -m ctk_kit.showcase.pages.buttons
python -m ctk_kit.showcase.pages.inputs
python -m ctk_kit.showcase.pages.notify --topmost
```

页面代码在 `ctk_kit/showcase/pages/` 下，一页一个文件；`--where` 会打印窗口矩形后退出，方便截图。

展示程序有十个页面：总览、基件、按钮、输入、布局、提示、列表、主题、表单、设置，把每个公开构建都用一遍。
基件页把 25 个色值连同浅/深两套十六进制值一起列出来，换主题时对着它调最直观。

## 四层结构

| 层 | 模块 | 内容 |
| --- | --- | --- |
| 令牌 | `tokens` | `COLOR_*`（全部为浅/深二元组）、`FONT_*`、`RADIUS_*`、`SPACE_*` |
| 主题 | `theme` | `is_dark()`、`color_of()`、`apply_appearance()`、`apply_appearance_fast()`、`set_titlebar_dark()`、`repaint_native()` |
| 页面 | `pages` | `PageRebuilder`：多页面窗口按需重建，切主题不卡 |
| 组件 | `buttons` / `inputs` / `dropdown` / `layout` / `notify` / `scroll_list` / `text` | 见下 |

## 组件

**按钮**（`buttons`）

- `primary_button(master, text, command, *, width=120, height=38, radius=9, font=FONT_BODY)`
- `soft_button(..., width=76, height=30, font=FONT_SMALL, border=False)` —— 次要操作
- `danger_button(...)` —— 删除一类不可逆操作
- `FlatButton(CTkButton)` / `SoftButton(FlatButton)` —— 卡片里的小按钮，宽度按文字实测
  （内部是 `CTkButton` 子类，所以有圆角）

**输入**（`inputs`）

- `toolbar_entry(master, placeholder, *, height=40)` —— 工具条里的搜索框，聚焦时描边变主色
- `form_entry(master, *, show="", placeholder="", height=38, password=False)`
- `segmented(master, values, command=None, *, width=300, height=34, font=FONT_SMALL)`
  —— 容器底用 `COLOR_SOFT`（比卡片深一档），不用 `COLOR_INPUT`：后者浅色值和
  `COLOR_CARD` 都是 `#ffffff`，浅色主题下整组分段会和卡片同色、看不出边界
- `switch(master, command=None, *, text="", width=44)` —— 开关；`text` 留空就只显示轨道
- `checkbox(master, text="", command=None, *, width=20, height=20)` —— 勾选框，选中后填主色打勾
- `radio_group(master, values, command=None, *, variable=None, gap=8)` → `(容器, StringVar)`
  —— 一组互斥单选；`CTkRadioButton` 必须共用同一个 `variable` 才互斥，所以直接给一组
- `slider(master, command=None, *, from_=0.0, to=100.0, steps=0, width=220)` —— 滑块，
  `command` 收 `float`；`steps>0` 时只能停在等分点
- `progressbar(master, *, value=0.0, width=220, height=6)` —— 细进度条，`value` 收 0~1，
  圆角跟随高度

  选择类控件的配色约定：选中/已填充部分用 `COLOR_ACCENT`，未选中描边和轨道用
  `COLOR_BORDER_STRONG`，这样深色主题下不会一排控件全是高饱和蓝

**大文本**（`text`）

- `TextArea(master, *, placeholder="", height=200, readonly=False, show_counter=True, on_change=None, bg_color=None, text_color=None)`
  —— 多行文本区：失焦时显示占位符、底部字数统计、可切换只读；读写用 `get()/set()/clear()`。
  内部底色默认 `COLOR_INPUT`（输入框语义）；当日志面板显示时传 `bg_color=COLOR_CARD` 或
  `bg_color="transparent"`，就不会比所在卡片亮一截，`text_color` 也可单独覆盖

**下拉**（`dropdown`）

- `DropField(master, *, values_provider, command=None, placeholder="", height=36)` —— 自绘候选卡片，
  不用 `CTkComboBox`，因为系统下拉框在深浅色之间很难统一

**布局**（`layout`）

- `page_header(master, title) -> (head, info)` —— 左标题右信息
- `section_title(master, text)`、`card(master)`、`divider(master)`
- `field_label(master, text, *, width=112)`、`hint_label(master, text)`
- `empty_hint(master, title, detail="")` —— 空态
- `scrollable(master)` / `style_scrollable(frame)` —— 统一滚动条的宽度与配色

**提示**（`notify`）

- `Notifier(master, *, duration=None, max_visible=3)` —— 浮在窗口顶部/底部的提示条
  - `.show(message, *, title="", level="info", position="top", style="pill", duration=None, on_close=None)`
    返回这条提示的控件；`level` 取 `"info" / "success" / "warn" / "error"`，
    `position` 取 `"top" / "bottom"`，`style` 取 `"pill"`（一行窄条）或
    `"card"`（带状态图标、标题和关闭按钮）
  - `.dismiss(view)` / `.clear()` / `.count(position=None)` —— 手动关闭或数条数
  - 默认停留：窄条 2.6 秒、卡片 4.5 秒；指针停在提示上暂停计时；`duration=0` 常驻
  - 同一位置最多同时显示 `max_visible` 条，超出时最旧的先关掉
  - 出现与消失有约 80ms 的淡入淡出；超限时先关最旧的再整体重排，不会跳位置
  - 不做全局置顶：提示挂成主窗口的附属窗口（`transient`），只在主窗口之上，
    切到别的应用或最小化主窗口时会一起下去
  - 每条提示都是一个无边框小窗口，和下拉面板同一套做法：窗口由系统裁成圆角，
    圆角以外不绘制，所以压在页面卡片上也不会露出一圈深色底
- `notify(master, message, **kwargs)` —— 按窗口缓存 `Notifier` 的便捷函数，连续调用会正常堆叠

```python
from ctk_kit import Notifier

tips = Notifier(app)
tips.show("已复制到剪贴板")
tips.show("云备份失败", title="网络错误", level="error", style="card", position="bottom")
```

**列表**（`scroll_list`）

- `LazyList(master, render_card, *, key_of=None, first_batch=12, load_more=8, ...)`

  只创建可见的一批卡片，滚到底再补下一批；内容不足以填满视口时自动补齐。
  卡片工厂由调用方提供，所以同一个列表能装任何东西：

  ```python
  def make_card(parent, item):
      card = ctk.CTkFrame(parent, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
      ctk.CTkLabel(card, text=item["title"], anchor="w").pack(fill="x", padx=16, pady=(14, 0))
      return card

  listing = LazyList(frame, make_card, key_of=lambda item: item["id"])
  listing.pack(fill="both", expand=True)
  listing.render(items)
  ```

  数据量很大（几千条）时，传入固定卡高开启虚拟滚动：只把视口附近的卡片放上布局，
  滚出去的卡片留在内存里复用，滚回来直接放回去，不销毁也不重建。

  ```python
  listing = LazyList(frame, make_card, key_of=lambda item: item["id"], item_height=96)
  ```

  虚拟滚动要求卡片高度固定（例如自己 `pack_propagate(False)` 并设置 `height`），
  并把卡片间距算进 `item_height`。`item_height` 用和控件尺寸一样的逻辑单位，
  高 DPI 缩放下由 `LazyList` 自己换算。

## 设计令牌

颜色全部是 `(浅色, 深色)` 二元组，交给 `color_of()` 按当前外观取值：

```python
from ctk_kit import color_of
from ctk_kit.tokens import COLOR_ACCENT

color_of(COLOR_ACCENT)   # 深色下返回 "#2f6fed"
```

`LazyList`、`segmented` 这类控件需要跟随外观重建的，切主题后调用 `apply_appearance(mode)`，
再重建相关控件即可（`repaint_native()` 用于原生 tk 控件，它们的 `configure` 被 CTk 接管过）。

**切主题要重建页面**：CTk 控件的颜色写的是 `(浅色, 深色)` 二元组，按理说外观一变就会自己
重画，但实测在滚动容器、卡片这类层层嵌套的控件上并不总是生效；页面里又常盖着原生
`tk.Frame`（`bg` 在 `build` 时就定死了）。示例窗口的做法是：切换后立刻重建当前页，其余页
记成过期、等切过去时再重建（`show_page` 里先补建）。重建走「先建新页、再销毁旧页」——
页面里的 `CTkScrollableFrame` 在 `__init__` 里挂了 `bind_all`，在按钮回调里当场销毁页面，
事件还会派发给已销毁的控件。

**怎么让切换快**：`ctk.set_appearance_mode()` 会顺序遍历所有已注册控件一次性重绘，
一千多个控件要 380 ms。示例窗口先清空 `AppearanceModeTracker.callback_list` 再调用它——
全局外观状态照常更新，但已有控件一个都不重绘——然后只重建当前页（约 30~70 ms），
一次切换从 0.5 s 降到 0.15 s。拿不到那张表时自动退回官方做法，慢但不会错。
不要顺手把十页全建好：重建一页 30~350 ms，Tk 是单线程的，连着建会让窗口卡住一秒多。

**切主题时别让 CTk 动标题栏**：`CTk._set_appearance_mode` 在 Windows 上会顺手调
`_windows_set_titlebar_color`，把窗口 `withdraw()` 再 `deiconify()`（看起来像闪一层遮罩），
并且记下当时的焦点控件、`after(1, widget.focus)` 还回去——如果切换过程中重建了页面，
那个控件已经销毁，就会抛 `bad window path name`。做法是临时把
`CTk._deactivate_windows_window_header_manipulation` 置 `True` 再调它，标题栏颜色改用
`DwmSetWindowAttribute` 自己设。
另外重建页面后补一次 `update_idletasks()`，新页才会立刻按正确尺寸排好，
不然会先以占位形态显示一下再补内容。

**标题栏要自己染色**：只设 `DWMWA_USE_IMMERSIVE_DARK_MODE`（`20`/`19`）的话，颜色是
系统给的——浅色下约 `#f3f3f3`，和 `COLOR_BG`（`#f4f5f7`）几乎同色，看上去标题栏和内容区
糊成一片，只有深色下才恰好有层次。`:func:`set_titlebar_dark` 会再补三刀（Windows 11 22H2+）：
`DWMWA_CAPTION_COLOR`（`35`）染成 `COLOR_TITLEBAR`、`DWMWA_BORDER_COLOR`（`34`）染成
`COLOR_BORDER`、`DWMWA_TEXT_COLOR`（`36`）染成 `COLOR_TEXT`；老系统上这几个调用返回
非 0，自动退回系统色。注意要等窗口 mapped 之后再调（`after(10, ...)`），否则 DWM 还没接管。

## 切主题不卡

自己写的程序也能拿到和示例窗口一样的效果——几行接入，不用管上面那些内部细节。
完整可运行的版本在 [`examples/fast_theme.py`](examples/fast_theme.py)：

```python
from ctk_kit import PageRebuilder, is_dark, recolor_tree
from ctk_kit import tokens as T

class App(ctk.CTk):
    def __init__(self):
        ...
        self.pages = PageRebuilder(self.body, self._build_page, ("总览", "设置"))

    def _build_page(self, name):
        return {"总览": build_overview, "设置": build_settings}[name](self.body)

    def toggle_theme(self):
        mode = "light" if is_dark() else "dark"
        # 一次做完：全局配色 + 窗口底色 + 当前页重建 + 侧边栏
        self.pages.switch(mode, window=self)
        self._refresh_sidebar(mode)
        self.update_idletasks()

    def _refresh_sidebar(self, mode):
        self.sidebar.configure(fg_color=T.COLOR_SIDE)
        recolor_tree(self.sidebar, T.COLOR_SIDE, deep=False)
```

`pages.switch()` 做了三件事：

1. 用 `apply_appearance_fast()` 更新全局配色和窗口底色，但**不让已有控件逐个重绘**
   （省掉 380 ms）；
2. 重建用户正看着的那一页（30~350 ms），其余页面只打「过期」标记，等切换过去时
   由 `pages.show(name)` 自动补建；
3. 需要的话还能用 `before_rebuild` / `after_rebuild` 钩子刷外壳（侧边栏、状态栏），
   `defer=True` 把页面重建推迟一帧。

**别在切换中途让出事件循环**。早先试过「先刷底色、再让一帧、再重建页面」，想做出
渐变式的观感，结果每一帧都是一半新一半旧（底色浅了卡片还是黑的），比一次做完更花。
现在是一整段同步代码，屏幕只在结束时重绘一次，看到的就是「旧配色 → 新配色」，
干净利落；代价是这 200 ms 左右窗口不响应，但本来也不该在切换中途去点别的。

想更快就只重建当前页、其余页延后——这是 `switch()` 默认就在做的；实测设置页
200 ms、列表页 450 ms（列表页自带六张卡片，重建本身就贵）。

`apply_appearance_fast(mode, window=...)` 单独用也可以：它会把窗口底色和标题栏一起刷好，
并且避开 CTk 那套「withdraw → deiconify → 还焦点」的标题栏处理（那正是切换时闪一下、
以及 `bad window path name` 的来源）。已有的控件仍然要你自己重建或重绘。

`recolor_tree(widget, bg, deep=False)` 用来刷侧边栏、状态栏这类容器：它会把直接子控件的
父底色改成新值，并让 CTk 控件按新外观重绘（`CTkButton` 的 `_bg_color` 是构造时从父容器
取死的，只改父容器会留下一圈颜色不对的方块）。`deep=False` 只走一层——CTk 控件的
`_set_appearance_mode` 本来就会重绘自己的画布和文字，再钻进去是白费力气（侧边栏 41 个
控件 46 ms → 只刷 13 个 24 ms）。容器再套一层（比如侧边栏底部的按钮组）就自己多调一次。

`PageRebuilder` 的约定只有两条：所有页面放进同一个容器，页面由 `factory(name)` 现建。

## 目录

```
ctk_kit/
├─ tokens.py       设计令牌
├─ theme.py        取色 / 外观切换 / 原生控件重绘
├─ pages.py        多页面窗口的页面管理：按需重建、切主题不卡
├─ buttons.py      按钮
├─ inputs.py       输入框 / 分段 / 开关 / 勾选 / 单选 / 滑块 / 进度条
├─ dropdown.py     自绘下拉
├─ layout.py       页头、卡片、分隔线、空态、滚动容器
├─ notify.py       窗口顶部/底部浮层提示
├─ scroll_list.py  懒加载列表
├─ text.py         多行文本区
└─ showcase/
   ├─ __init__.py  主窗口 ShowcaseApp 与 ctk-kit-showcase 入口
   ├─ __main__.py  `python -m ctk_kit.showcase` 入口
   ├─ data.py      页面清单、组件索引与假数据
   ├─ shell.py     公共辅助与单页启动器 run_page
   └─ pages/       十个页面，一页一个文件，都能 python -m 单独启动
      ├─ overview.py
      ├─ foundation.py
      ├─ buttons.py
      ├─ inputs.py
      ├─ layout.py
      ├─ notify.py
      ├─ listing.py
      ├─ theme.py
      ├─ form.py
      └─ settings.py

examples/
├─ showcase.py     仓库里的快捷入口（转发到 ctk_kit.showcase:main）
└─ fast_theme.py   把「切主题不卡」接进自己程序的最小示例
```

## 验证

示例页就是验收工具：改完哪个组件，就只启动用到它的那一页看效果，例如

```
python -m ctk_kit.showcase.pages.buttons    # 只开按钮页
python -m ctk_kit.showcase.pages.notify     # 只开提示页
ctk-kit-showcase --page 设置                # 整体窗口直接打开某一页
```

没有图形环境时窗口打不开，属于预期；仓库不再维护自动化测试套件，界面改动以人工看单页为准。
CI（`.github/workflows/ci.yml`）只做构建与导入自检：打出 wheel、装进干净环境，
`import ctk_kit` 与 `import ctk_kit.showcase.pages` 成功即通过。

## 发布

版本号只写在 `pyproject.toml` 的 `version` 字段里，发布流程全自动：

1. 改 `pyproject.toml` 的 `version`（例如 `0.2.0` → `0.2.1`），同步更新 `CHANGELOG.md`；
2. 提交并 `git push` 到 Gitee；
3. 镜像自动同步到 GitHub，Actions 跑完构建后，会比较 PyPI 上的最新版本——
   本地版本更新才发布，同版本重推不会报错。

首次发布前需要在 PyPI 的 *Publishing* 页面给 GitHub 仓库
`DashSalter/ctk-kit` 添加 Trusted Publisher（workflow 文件名 `ci.yml`，环境留空），
之后由 `pypa/gh-action-pypi-publish` 凭 OIDC 换短期令牌上传，仓库里不需要存密码。

## 已知的坑

这些都是踩过的，记下来省得再踩：

- `CTkLabel` 不支持 `border_width` / `border_color`，想加边框只能裹一层 `CTkFrame`。
- `CTkSegmentedButton` 同样不接受 `border_*`，传了会抛 `ValueError`。
- `CTkSlider` 的细轨道是靠 `border_width`（默认 6）缩出来的：把它设成 0，轨道会
  变成一根和控件一样高的粗条，圆形把手也会被吞进轨道里看不出来。
- `CTkScrollbar.set()` 内部会调 `update_idletasks()`，而 `update_idletasks` 会立刻执行
  `after_idle` 排的回调——用 `after_idle` 排分批渲染会在这个调用里递归建卡，改用 `after(1, ...)`。
- 滚动区域变化后，Tk 会回放一次 `yscrollcommand(0, 1)`。判断「滚到底」不能信回调参数，
  要读 `canvas.yview()`。
- customtkinter 接管了 `tk.Frame.configure`，给原生控件改背景色得走
  `widget.tk.call(widget._w, "configure", "-background", bg)`，否则会碰到已销毁的子控件。
- 提示条是独立的小窗口，位置按 `master` 的屏幕坐标算（相对窗口居中，不是相对屏幕）；
  想让提示只在内容区居中，就把 `master` 传成内容容器。窗口坐标用物理像素，
  而 `geometry` 的宽高是逻辑像素，所以尺寸要再除以窗口缩放。
- `CTkToplevel` 只写 `geometry("+x+y")`（不给宽高）会被忽略，必须同时给尺寸，
  否则多条提示会全部叠在同一个位置。
- 无边框窗口的圆角优先交给 DWM（`DwmSetWindowAttribute` 的
  `DWMWA_WINDOW_CORNER_PREFERENCE`），系统抗锯齿，圆弧是平滑的；不行才退回
  `CreateRoundRectRgn` + `SetWindowRgn`，后者是像素级的，圆弧一定有台阶。
- **每次设 DWM 圆角前都要先 `SetWindowRgn(hwnd, None, True)` 清掉旧 region**：
  布局重排会反复走这条路，残留的 region 会把 DWM 圆角整个挡住，现象是「一会儿
  圆角一会儿直角」。矮窗口同样适用，DWM 并没有对高度设下限。
- 浮层别设 `-topmost`：那样切到别的应用它还会盖在最前面。用
  `window.transient(master)` 挂成附属窗口——只在主窗口之上，主窗口被遮挡、
  最小化时它也跟着隐藏。
- 描边是「底色环 + 内容内缩 1px」画出来的，不是控件的 `border_width`——后者在
  大圆角下画不匀；描边环的圆角半径要和系统圆角（约 8）对齐，否则四角会被裁出豁口。
- 别用 `-transparentcolor` 抠圆角：窗口边缘那一两像素是系统合成的，颜色不等于
  键色，抠完会在四边留下没抠掉的一圈（尤其用深色键色时看着像黑框）。
- `Notifier` 的悬停暂停靠逐个子控件绑定 `<Enter>` / `<Leave>`，`CTkFrame.bind` 只接受
  `add=True` 或 `add="+"`；自绘 canvas 上直接绑标准 Tk 事件即可。

## License

MIT
