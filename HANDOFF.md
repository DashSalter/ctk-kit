# ctk-kit 交接（2026-11-07）

> 下一轮方向：**页面翻页流畅度 + 组件加载/绘制速度**。性能相关的实测数据全在第 4 节。

## 1. 一眼看懂

- 路径 `F:\ctk-ui-kit`，分支 `main`，版本 `0.11.0`（本轮之后未发版）。
- 环境：`.venv\Scripts\python.exe`（3.12.9 64bit）、CustomTkinter 6.0.0、Cython 3.3.1、MSVC 2022。
- 远端 `origin` / `gitee` 都指向 <https://gitee.com/kuangjianke/ctk-kit>。
- `ctk_kit/` 是纯 Python 库（55 个模块），`len(__all__) == 130`，约 1.87 万行。
- Windows 底层在 `_src/{win32,glass,frost_layer}.py`，经 `tools/build_core.py` 用 Cython 编成
  `ctk_kit/core/*.pyd`，存根 `ctk_kit/core/win32.pyi`。**改 `_src` 必须重编 pyd**（窗口开着会「拒绝访问」）。
- 示例：`examples/basics/window.py`（`DemoApp`，16 个公开页 + 2 个隐藏页）、
  `examples/demo/`（最小示例：按钮 / 输入框 / 开关 / 主题切换 / 组件分行布局 / 开关状态管理）。
- 文档站：MkDocs + Material，`docs/`，`mkdocs build --strict`，GitHub Pages
  <https://dashsalter.github.io/ctk-kit/>（只有「按钮」页写完了）。

```
.venv\Scripts\python.exe -m compileall -q ctk_kit examples
.venv\Scripts\python.exe -m tools.build_core            # 只在改了 _src 时
.venv\Scripts\python.exe examples\basics\window.py      # 起演示
.venv\Scripts\python.exe -m mkdocs build --strict       # 文档
```

## 2. 本轮（0.11.0 之后）做了什么

### 2.1 运行时换色 `ctk_kit/theming.py`（新模块）

- `apply_palette({令牌: "#RRGGBB"}, root=None, repaint=True, shade=True)`：改 `tokens` 全局并重刷控件树，
  只换「变化的令牌」；`reset_palette()` 回基线。
- 刷新机制：遍历控件树，先对有 `apply_theme()` 的控件调一次（自绘件靠这个），
  再做「旧色 → 新色」字符串替换表（`_single_map`）。**不反查令牌名**，代价是同值令牌会互相牵连
  （目前只有 `COLOR_SOFT` 和 `COLOR_INPUT` 都是 `#22242c`）。
- `set_darken(factor)`：毛玻璃主题下自定义颜色自动暗 20%。
- 只读查询：`find_usage(token)` / `usage_summary(token)` / `describe_usage(token)`。
- `register_redraw(widget, cb)`：给没有 `apply_theme` 的自绘件兜底。

### 2.2 颜色令牌单色化（破坏性）

- `tokens.py` 的 32 个令牌从 `(浅, 深)` 二元组 / 三元组改成**单个 `#RRGGBB` 字符串**，
  对应原来的毛玻璃配色。删掉 `GLASS_COLORS` 与 `_flatten_glass_colors()`。
- `theme.color_of(token)`：字符串原样返回，旧二元组取最后一项（仅为兼容）。
- 主题切换仍保留（`frosted / dark / acrylic / mica`），外观模式固定 dark。

### 2.3 快捷方法 `ctk_kit/sugar.py`（新模块）

- `Enablable`：`enable()` / `disable()` / `toggle_enabled()` / `set_enabled(bool)` / `is_enabled()`。
  混入按钮、输入框、下拉、开关、勾选、单选、分段、滑块、范围滑块、搜索框、颜色选择、文本区、步进器、标签选择。
- `Textual`：`set_text()` / `get_text()`。
- `Valuable`：`get_value()` / `set_value()`，铺到 20 个有 `get()/set()` 的控件。
- `Options`：`__getattr__` 动态给出 `set_<option>` / `get_<option>`（`btn.set_fg_color("#f00").set_height(44)`），
  **只认 `_OPTIONS` 里的名字和 `*_color`**，其余抛 `AttributeError`。
- `Bindable`：`on_click` / `on_double_click` / `on_right_click` / `on_enter` / `on_leave` / `on_drag` /
  `on_focus` / `on_blur` / `on_key` / `on_key_release` / `on_scroll` / `on_resize` / `on_move`。
  混入 `App`、`_ButtonBase`、`CTkEntry`、`SearchBox`、`Badge`。

### 2.4 窗口 API（`ctk_kit/window.py`）

- 主题：`set_theme(name="mica", color=None)` / `set_theme_color()` / `get_theme()` / `get_theme_color()`。
  `_THEME_PRESETS`：`frosted`（毛玻璃，透桌面）/ `dark`（纯深实底）/ `acrylic` / `mica`（默认）。
- 外观专用 setter（18 个，全部 `return self`）：`set_glass_kind` / `set_glass_state` / `set_system_backdrop` /
  `set_tint` / `set_tint_alpha` / `set_window_corners` / `set_border_color` / `set_caption_color` /
  `set_opacity` / `set_veil` / `set_extend` / `set_titlebar_glass` / `set_glass_dark` / `set_wca` /
  `show_titlebar_icon` / `show_titlebar_title` / `hide_frame_border` / `set_transitions`。
- 几何：`set_size` / `get_size` / `set_position` / `get_position` / `center` / `get_scale`。
- 事件：`on_close`、`on_resize` 等（来自 `Bindable`）。

### 2.5 布局

- `Card.row(index=1, fill=..., padx=..., pady=...)`：按编号复用同一行容器，
  `ctk.PrimaryButton(card.row(1), "保存").pack(side="left")`。
- 自动 pady：首行 `(14, 10)`、中间 `(0, 10)`、末行 `(0, 14)`；显式传过 pady 的行不参与重排。
- 参数是显式签名 + `_UNCHANGED` 哨兵（IDE 里显示「未设置」），复用行只更新显式传入的项。

### 2.6 组件

- `ColorPicker`：右键菜单（复制 / 粘贴，粘贴前校验剪贴板是不是颜色）；12 个参考色块移到
  `ColorDialog` 底部；`ColorDialog(colors=...)` 可自定义。
- `Tooltip`：底色 `#2B2B2B`、14px、(14, 10) 内边距，和下拉面板/右键菜单同一套。
- `Segmented` / `Switch` / `Check` / `Radio` / `Progress` / `RingProgress` / `Slider` / `RangeSlider`
  都补了 `apply_theme()`。
- `Switch(value=..., set_value/get_value)`；`Check` 同步。

### 2.7 文档

- `docs/`：MkDocs + Material，`docs/components/buttons.md` 按「作用 / 类型 / 参数 / 方法」四段重写（217 行）。
- `docs/index.md`：主题切换、窗口外观两节。
- `CHANGELOG.md` 的「## 未发布」段记录了上面全部条目。

## 3. 代码结构速查（性能优化会碰到的）

| 文件 | 作用 | 关键点 |
|---|---|---|
| `ctk_kit/window.py` | `App(Bindable, CTk)` | `__init__` 依次：读 state → `set_appearance_mode` → `apply_backdrop` → `_restore_palette` → 建导航；`_refresh_backdrop` 走 `after(10, ...)` |
| `ctk_kit/page.py` | `PageBase(Frame)` | `cards_first`、`build_cards()`、`build_later()`（`after(1, _run_build_step)`，每步 `update()` 一次）；`when_built()` |
| `ctk_kit/pages.py` | `PageRebuilder` | 切页时按需建页、缓存已建页面 |
| `ctk_kit/sidebar.py` | `SidebarNav` | `show(name)` 切换页面；导航区是 `layout.Scrollable` |
| `ctk_kit/styles.py` | `SHEETS` 快照 | `refresh_tokens()` 只重抓背景相关几项 |
| `ctk_kit/theming.py` | 换色 | `_repaint()` 遍历整棵控件树 + `_draw()` |
| `ctk_kit/frames.py` | `Frame` | 所有页/卡片的底座（`CTkFrame` 子类） |
| `ctk_kit/layout.py` | `Card` / `PageHeader` / `Scrollable` | `Card.row()` 的行容器缓存 |
| `ctk_kit/core/*.pyd` | Win32 / 玻璃 | 由 `_src/*.py` 编译，别手改 |

## 4. 性能现状（下一轮从这里开始）

### 4.1 已知数据（本机 2560×1440、DPI 125%）

| 指标 | 数值 | 说明 |
|---|---|---|
| `import ctk_kit` | **326 ms** | 含 Pillow、customtkinter、pyd |
| `DemoApp()` 构造 | **0.81–1.08 s** | 292 个控件，含首页分帧构建 |
| 玻璃合成挂上 | +893 ms | `_refresh_backdrop` 之后 |
| frost layer 建好 | +999 ms | 窗口在 ~400ms 已显示，这半秒透桌面 |
| `theming.apply_palette` 一次 | **76 ms** | 改 1 个令牌、重刷全树 |
| `theming.reset_palette` | **94 ms** | 同上 |
| 200 次 idle `update()` | 118 ms | 每次 ~0.6 ms，是事件循环空转的基线 |

复现脚本（临时，已删过）：起 `DemoApp` → 记 `performance_counter` 差值 → 遍历 `winfo_children()` 数控件。

### 4.2 已确认的瓶颈方向

1. **CTk 每个控件都用 Pillow 现画背景图**：圆角矩形、开关、勾选、滑块都是 `Image.new` + `draw` 生成的
   PNG，再包成 `CTkImage`。换色 / 改尺寸 / 首次布局都会重新生成。
   我们自己的 `@cached` 只覆盖 badge / breadcrumb 等少数几个，**CTk 自身的不在缓存里**。
2. **切页是「销毁重建」**：`PageRebuilder` 缓存已建页面，但每个页面首次切过去才建，
   页面内用 `build_later` 按 12ms 时间片补卡片（每步 `self.update()` 一次）。
   → 首次切页会有明显的「逐块出现」；反过来，`update()` 每步都跑，会打断动画。
3. **换色是整树遍历**：`_repaint()` 对 292 个控件逐个 `_patch_widget` + `_draw()`，
   76ms 里大部分是 CTk 的 `_draw()`。
4. **启动期透明窗口**：`backdrop="acrylic"` 时窗口底/侧栏是 veil 色（透明键），
   玻璃合成要等 `after(10, _refresh_backdrop)`，这期间透出桌面。

### 4.3 可选的优化方向（未开工，按性价比排序）

- **A. 控件绘制缓存**：给 CTk 的 `_draw()` 加一层按「尺寸 + 圆角 + 颜色」的 LRU 图缓存
  （库级 monkeypatch 或子类重写），换色时不用重新 Pillow 画图。
- **B. 切页预建**：`PageRebuilder` 增加「相邻页预建」（切到第 N 页时，空闲后台建 N±1），
  用户感知的等待变短；或者切页时先把新页 `place` 上来再撤旧页（已有部分逻辑）。
- **C. 分帧策略调整**：`build_later` 的 `after(1)` 改成「同一帧内连续建到 12ms 用完」的循环
  （现在每步都 `update()`，一帧只建一张）。
- **D. 启动不透明预热**：`backdrop` 生效前先给 `COLOR_BG` 不透明底，玻璃挂上后再切 veil。
- **E. 批量更新 API**：`App.batch()` 上下文管理器（挂起重绘、退出统一刷），配合高频数据刷新。
- **F. 后台任务 API**：`App.background(fn)` / `App.every(ms, fn)`（线程池 + `queue.Queue` + `after` 轮询）。

### 4.4 参考：一篇外部文章的分析结论

用户拿 <https://www.php.cn/faq/2892962.html> 问过是否有帮助。结论：**对库本身约 20% 有用**，
它讲的是应用层写法（别用 `after(0)`、少 `config()`、线程池走队列、少嵌套）。
其中两条我们已满足（全库无 `after(0)`；分帧用 `after(1)`），两条是缺口（没有后台任务 API、没有批量更新）。
文章里「批量更新先 `pack_forget` 再 `pack` 更快」「别用 `try/except queue.Empty`」两句是错的，别照抄。

## 5. 坑（务必先看）

1. **绝对不要用 PowerShell 的 `Set-Content` / `Out-File` 改源码或 JSON**。该环境 `Get-Content` 默认按 GBK 读，
   UTF-8 源码会被写坏（本轮 `ctk_kit/window.py` 被毁过一次，277 行乱码）。
   改文件只用 `edit` / `write` 工具，或 Python 里 `io.open(path, "w", encoding="utf-8", newline="\n")`。
   要写 JSON 且不能带 BOM：`[IO.File]::WriteAllText($p, $s, (New-Object System.Text.UTF8Encoding($false)))`。
2. **CTk 的 `withdraw()` / `deiconify()` 被重写过**：窗口还没真正存在时调用会置
   `_withdraw_called_before_window_exists`，而 CTk 的 `mainloop()` 看到这个标志就不再 deiconify，
   结果窗口永远不出现。要绕过必须用 `tk.Wm.withdraw(self)` / `tk.Wm.deiconify(self)`。
   （本轮试过「先隐藏、算完尺寸再显示」来消掉启动闪白，结果就是这个坑，已整段回退。）
3. **DPI**：`geometry("700x500")` 是逻辑像素，`winfo_width()` 返回屏幕像素（125% 缩放下 700→875）。
   `App.get_size()` 会按 `_pixel_scale()` 换算回来。
4. **`bind()` 默认替换已有绑定**：`sugar._bind_event` / `_bind_configure` 必须带 `"+"`，
   否则后注册的会顶掉前面的（本轮 `on_resize` 顶掉过 `<Configure>` 监听）。
5. **`save_palette` / `window_state` 写入**：`C:\Users\admin\.ctk-kit\window.json` 是用户真实状态，
   测试别调 `page.on_color()`（会写盘），用 `theming.apply_palette(..., root=app)`。
6. **示例进程开着时 pyd 被占用**：重编 `core/*.pyd` 前先关窗口。
7. **`tokens` 不要再写二元组**：已经单色化，写元组会让 `color_of()` 取最后一项，行为不直观。

## 6. 未完成 / 悬而未决

- **性能优化两个方向**（本轮研究目标）：翻页流畅度、组件加载与绘制速度。见 4.3 的 A–F。
- 启动闪白 / 透桌面：方案 D（不透明预热）未做。
- 字体块（字号 / 颜色 / 加粗，一号 = 页面标题字体）：用户提过，调研完成，**未开工**。
  事实：`tokens.py:23-38` 是静态 `FontSpec`，34 个模块引用；`CTkLabel.cget("font")` 原样返回 tuple，
  所以「遍历控件比对 font tuple 再 `configure(font=新tuple)`」可行。
- 阶段 2：其余自绘组件（`select` 面板、`dropdown`、`table`、`steps`、`timeline`、`calendar`、`tabs`、
  `breadcrumb`、`carousel`、`splitter`、`treeview`、`search`、`timepicker`）补 `apply_theme()`。
- 文档站只有「按钮」一页，其余组件页待写（按 buttons.md 的四段结构）。
- `article/`（CSDN / 掘金宣传稿 + 9 张配图）已提交但未发布；`image/` 下 8 张旧截图（浅色旧版）没入库，
  `我的后续计划.txt` 是用户自己的笔记，别提交。

## 7. 验收清单（改完跑一遍）

```
.venv\Scripts\python.exe -m compileall -q ctk_kit examples
.venv\Scripts\python.exe examples\basics\window.py         # 16 页都能切、换色生效、主题能切
.venv\Scripts\python.exe -m mkdocs build --strict
```
