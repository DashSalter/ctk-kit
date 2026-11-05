# ctk-kit 交接（2026-11-06）

## 项目现状

- 路径 `F:\ctk-ui-kit`，分支 `main`，最近提交 `4e72ad1`「浮层统一深色配色、取色面板重做、滑块与分段选择自绘」。
- `ctk_kit/` 是纯 Python 库（约 56 个模块）；Windows 底层在 `_src/{win32,glass,frost_layer}.py`，
  用 `tools/build_core.py` 经 Cython 编成 `ctk_kit/core/*.pyd`，对应存根 `ctk_kit/core/win32.pyi`。
- 示例入口 `examples/basics/window.py`（`DemoApp`，左侧导航切页），设置页 `settings_page.py`。
- 环境：`.venv\Scripts\python.exe`（3.12.9 64bit）、Cython 3.3.1、MSVC 2022、CustomTkinter 6.0.0。

### 构建 / 运行

```
.venv\Scripts\python.exe -m tools.build_core          # 重编三个 pyd
.venv\Scripts\python.exe examples\basics\window.py    # 起演示
.venv\Scripts\python.exe -m compileall -q ctk_kit examples
```

改 `_src/*.py` 后**必须重编 pyd**才生效；示例进程开着时旧 pyd 会被占用，报「拒绝访问」，
先关窗口再编（实在要热换：把旧 pyd 改名 `.old`，再把 `build\lib.win-amd64-cpython-312\ctk_kit\core\*.pyd` 拷过来）。

## 上一轮（11-05 → 11-06）完成的事

| 主题 | 落点 |
| --- | --- |
| 标题栏图标 / 标题可临时隐藏 | `window.titlebar_items()` / `set_titlebar_items(icon=, title=)`；底层 `win32.blank_icon/caption_icon/set_caption_icon/set_window_text/window_text`；设置页「标题栏」卡片 |
| 取色面板重做 | `color.ColorDialog`：HSV 色域 + 明度条、Mica 底、`_BOARD_DIM=0.25` 预压暗、`_marker_image` 抗锯齿圆环、库内控件（FormEntry / Segmented / 主次按钮） |
| Slider 自绘 | `inputs.Slider`（Pillow 4x 超采样，`_SLIDER_SCALE/_TRACK/_KNOB`），修掉 CTkSlider 圆点锯齿，补 `state` |
| Segmented 修复 | 自绘 canvas 改名 `_seg_canvas`（撞名会被 CTk 刷成窗口底色）；canvas 四边内缩 `0.35R` 让出圆角 |
| 浮层统一 | 右键菜单 / 下拉 / 多选 / 层级树 / 提示：`#2B2B2B` 底、`#575A63` 悬停，**全部不挂玻璃** |
| 选中行 | `select._SELECTED_ROW_BG = "#464A54"`（比悬停暗一档），文字用 `T.COLOR_TEXT` |
| 图片压暗 | `branding.dim_image()` / `dim_ratio(alpha)`，跟随「背景透明度」：255→0、0→`DIM_MAX(0.5)` |
| 透明度联动 | `window._frost_cap()` / `_clamp_frost_alpha()`：整体透明度自动把背景透明度压下去（只降不升） |
| 设置页精简 | 主题收为四项（毛玻璃 / 深空 / Acrylic / Mica），去掉背景色、合成方式、调试开关等入口 |

## 本轮：自定义主题页面 + 颜色单色化

需求：页面上改颜色 → 已存在的组件立刻变色 → 重启后保留。

**做法**：新建 `ctk_kit/theming.py`，直接改 `tokens` 里的模块级颜色常量，再把已存在控件的
颜色属性按「旧色 → 新色」替换表换掉并就地重绘，不需要重建控件。

随后按用户要求把颜色体系**单色化**：原来 `tokens` 是 `(浅色, 深色)` 二元组（个别带第三项
毛玻璃色），现在只有一套毛玻璃配色，令牌就是 `"#RRGGBB"` 字符串。外观模式仍固定深色，
设置页的「毛玻璃 / 深空 / Acrylic / Mica」切换只影响 `set_glass_options()`，与配色无关。

### 新增 / 改动清单

| 文件 | 内容 |
| --- | --- |
| `ctk_kit/theming.py`（新） | `apply_palette(updates, *, root=None, repaint=True)` / `reset_palette()` / `current_palette()` / `palette_changes()` / `refresh()` / `register_redraw(widget, cb)` / `save_palette()` / `load_palette()` / `find_usage()` / `usage_summary()` / `describe_usage()` |
| `ctk_kit/tokens.py` | 整体重写：32 个令牌改成单色字符串，删 `_flatten_glass_colors()` 与 `GLASS_COLORS` |
| `ctk_kit/theme.py` | `color_of()` 对 str 原样返回、对旧元组取最后一项；删 `_GLASS_TINTS` / `glass_tint()` / `_BASE_GLASS_COLORS`；`apply_backdrop()` 玻璃时只把 `COLOR_BG`/`COLOR_SIDE` 换成 veil，切回时还原基准；保留 `current_veil()` |
| `ctk_kit/styles.py` | `pick()` 对旧元组取 `[1] if is_dark else [0]`；删 `_glass_active()` |
| `ctk_kit/badge.py` | `_resolve_color()` 返回单色；`_fill()` / `_render()` / `_image()` 去掉 `mode` 参数，深浅共用一张图 |
| `ctk_kit/inputs.py` | `Segmented.apply_theme()`；`_switch_picture()` 改成单色画一张、深浅共用 |
| `ctk_kit/statusbar.py` | `_tone_color()` 不再做 `token[1]` / `token[0]`（单色化后会取到字符） |
| `ctk_kit/buttons.py` / `avatar.py` | 构造时误用 `color_of()` 的地方改回直接传令牌 |
| `ctk_kit/window.py` | `App.apply_palette()` / `App.reset_palette()`；`App.__init__` 在 `apply_backdrop()` 之后、建控件之前 `_restore_palette()` |
| `ctk_kit/color.py` | `ColorPicker.configure(command=..., value=...)`；右键菜单「复制颜色」（用 `context_menu.attach_menu`） |
| `ctk_kit/__init__.py` | 导出 `theming` |
| `examples/basics/window_state.py` | `palette` 段 + `read_palette()` / `write_palette()`（JSON，单色字符串；旧的两项数组读时取最后一项） |
| `examples/basics/theme_page.py`（新） | 独立的「主题」页：两项（主按钮色 / 分段选择色，每项写明用在哪些组件）+ 预览卡片（主按钮 / 次按钮 / 窄输入框 / 分段选择开·关 / 开关 / 勾选框 / 单选框 / 进度条），改完立刻变色并写盘；「恢复默认配色」 |
| `README.md` / `CHANGELOG.md` | 用法与「未发布」条目（含破坏性变更说明） |

### theming 的关键细节（改它之前先读）

1. **换色靠「旧色 → 新色」替换表**，不再反查令牌名。`_single_map(before, after)` 只记录
   本次真正改过的令牌对应的颜色变化，扫描控件时把字符串颜色属性按表替换。原因是深色下
   多个令牌同值（`COLOR_SOFT` / `COLOR_INPUT` 都是 `#22242c`），按「值 → 令牌」反查根本
   分不清。**代价**：两个令牌同值时，改其中一个会连带改到另一个的控件（目前只有
   `COLOR_SOFT` / `COLOR_INPUT` 这一对，主题页没把它们放进可改项）。
2. **`_BASELINE` 是模块级立即求值**。曾经写成惰性初始化，导致第一次 `reset_palette()`
   抓到的「基线」已经是改过的值，返回空列表。别改回 `if _BASELINE is None: ...`。
3. **毛玻璃下的底色**：`COLOR_BG` / `COLOR_SIDE` 在 acrylic 模式必须是透明键色（veil），
   否则玻璃失效。`apply_palette()` 会把这俩令牌在玻璃下强制写回 veil，用户挑的颜色经
   `rebase_token()` 记成基准，切回不透明时生效。
4. **`styles.SHEETS` 是导入时快照**：`_sync_sheets()` 负责把 `Card` / `SidebarNav` /
   `StatusBar` 那几张表里的颜色重新抓一遍，漏了会出现「卡片标题变色、卡片底不变」。
5. **自绘控件靠 `apply_theme()` 自动带动**：canvas / Pillow 画的组件（`Segmented`、
   `choices`、`select` 的面板、`table`、`misc` 圆环、`range`、`scrolling`…）颜色写在
   画布图元上，换属性无效。`theming._repaint()` 遍历控件树，对**每个有 `apply_theme()`
   的控件**都调一次（无参），所以只要组件实现了 `apply_theme()` 就会跟着换色，不用逐个
   登记。`register_redraw(widget, cb)` 只留给没有 `apply_theme()` 的自绘件，回调不带参数。
   注意 `apply_theme()` 要自己防「控件还没布局」（`_layout()` 里已有 `width <= 1` 早退）。
   实测 DemoApp：`COLOR_ACCENT` 2 处、`COLOR_SOFT` 30 处、`COLOR_CARD` 69 处、
   `COLOR_TEXT` 12 处、`COLOR_MUTED` 109 处都能换干净；`COLOR_ACTIVE` 属性上 0 处，
   但 7 个 `Segmented` 的滑块全部重画。
6. **`ColorPicker` 右键菜单**：用 `context_menu.attach_menu(self, [("复制颜色", self._copy_color)], deep=True)`，
   `_copy_color()` 只写剪贴板。

## 别重复踩的坑

1. **Win11 的 accent 玻璃对 Tk 窗口没有真实模糊**。黑白棋盘探针（面板压在棋盘上，内部纹理一格不透）
   证明过：Dialog、下拉、菜单都一样。所谓「毛玻璃感」来自半透明 + accent=3 叠的约 25% 白。
   所以上一轮把所有浮层的玻璃全撤了，统一纯色，避免「开窗惊动 DWM → 主窗口闪一下」。
2. `attributes("-alpha", ...)` 会把窗口变 layered，同时摘掉玻璃，两者不能共存。
3. `CTkFrame` 的 `corner_radius` 是 canvas 多边形拼的，无抗锯齿；125% 缩放下大半径右侧有明显台阶，
   `DropField` 已降到 6。彻底平滑要换 Pillow 4x 自绘底。
4. **不要给子类用 `self._canvas` 当自绘画布**，CTk 内部会拿它刷窗口底色（Segmented 踩过）。
5. 浮层不要用 `CTkScrollableFrame`（内部 `bind_all` 抢全应用滚轮），用 `layout.Scrollable`。
6. 面板里出现滚动条会吃掉右侧宽度，预留固定宽度没用（滚动条仍额外占），改成给行按钮左右各 10。
7. 颜色已经单色化，**别再往 `tokens` 里写二元组**：`color_of()` 会取最后一项，但
   `styles.pick()`、`badge._resolve_color()` 这些兼容分支只为旧代码留着，新代码直接写
   `"#RRGGBB"`。

## 未提交改动（下次开工先看）

- 本轮全部：`ctk_kit/theming.py`(新)、`ctk_kit/tokens.py`、`ctk_kit/theme.py`、
  `ctk_kit/styles.py`、`ctk_kit/badge.py`、`ctk_kit/buttons.py`、`ctk_kit/avatar.py`、
  `ctk_kit/statusbar.py`、`ctk_kit/window.py`、`ctk_kit/color.py`、
  `ctk_kit/inputs.py`、`ctk_kit/__init__.py`、`examples/basics/theme_page.py`(新)、
  `examples/basics/window.py`、`examples/basics/window_state.py`、
  `examples/basics/settings_page.py`（移出配色卡片）、`README.md`、`CHANGELOG.md`、`HANDOFF.md`。
- 更早遗留、还没验收：`ctk_kit/select.py`（面板滚动条 `_PANEL_SCROLLBAR = "#4A5060"` /
  `_PANEL_SCROLLBAR_HOVER = "#5F6678"`）、`ctk_kit/sidebar.py`（导航区包 `layout.Scrollable`
  + `pack_propagate(False)`，窗口太矮时出滚动条）。
- 未跟踪：`我的后续计划.txt`（用户笔记，不要入库）、`tests/` 里一堆 `tmp_*` 探针脚本和截图。

## 下一步

1. **人眼验收**：跑 DemoApp → 「主题」页 → 改主按钮色 / 分段选择色，看预览和整窗按钮是否
   立刻变；点「恢复默认配色」；重启看是否记住。`compileall` + `import ctk_kit` 冒烟。
   截图脚本不要写——`ImageGrab` 抓玻璃窗口会抓到合成前后的差异，容易误判。
2. **阶段 2：自绘组件补 `apply_theme` + `register_redraw`**（工作量大，按使用频率排）：
   `select`（多选 / 层级树面板）→ `dropdown` → `table` → `choices`（Check/Radio）→
   `range` → `misc`（圆环）→ `scrolling` → `search` / `timepicker` / `dialog` / `popover`。
   每个组件的套路：颜色常量抽成方法 -> 重绘时重新取 `theme.color_of(...)` -> 构造末尾
   `theming.register_redraw(self, self._redraw)`。
3. 令牌编辑项可以再扩：主题页现在列 2 个，`COLOR_SOFT` / `COLOR_INPUT` 同值，放进去
   之前要先解决「同值令牌互相改」的问题（要么给控件记令牌名，要么把两者颜色错开）。
4. `pyproject.toml` 版本还是 `0.10.0`，发版前记得连同 `CHANGELOG.md` 的「未发布」一起改。
