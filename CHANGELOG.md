# 更新记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## 0.7.0 — 2026-10-29

- 新增四个选择类控件工厂（`ctk_kit/inputs.py`）：
  - `checkbox(master, text="", command=None, *, width=20, height=20)`
  - `radio_group(master, values, command=None, *, variable=None, gap=8)` → `(容器, StringVar)`
  - `slider(master, command=None, *, from_=0.0, to=100.0, steps=0, width=220)`
  - `progressbar(master, *, value=0.0, width=220, height=6)`
- `switch()` 新增 `text` 关键字参数（默认 `""`，保持原有「只有轨道」的观感）
- 选择类控件的配色约定：选中/已填充用 `COLOR_ACCENT`，未选中描边与轨道用
  `COLOR_BORDER_STRONG`，深色主题下不再是一排高饱和蓝
- `switch()` 的轨道从 `COLOR_SOFT` 换成 `COLOR_BORDER_STRONG`、把手换成
  `COLOR_MUTED`：原来的深色组合（`#22242c` 轨道 + `#131418` 把手）压在卡片
  `#181920` 上就是一团黑
- 示例「输入」页补三节：勾选框、单选组、滑块与进度条（滑块拖动联动进度条）
- README 补四个工厂的签名与配色说明；「已知的坑」补 `CTkSlider` 的细轨道靠
  `border_width` 缩出来这一条

## 0.6.0 — 2026-10-29

- 新增 `ctk_kit/pages.py`：`PageRebuilder`
  - 管理「同一个容器里叠放的多个页面」，按需建页、切页、按当前外观重建某一页
  - `switch(mode, window=...)` 一行完成「切全局外观 + 重建当前页 + 其余页标记过期」
  - 其余页在 `show(name)` 时补建；重建走「先建后销」，避免 `bind_all` 把事件
    派发给已销毁的控件；重建后补 `update_idletasks()`，新页一步到位
  - 可选 `on_hide` 钩子，页面被切走时调用
- 新增 `theme.apply_appearance_fast(mode, *, window=None)`
  - 切外观时跳过「一次性重绘所有已注册控件」（省掉约 380 ms），
    对应控件由调用方自己重建
  - 传 `window` 时一并刷新窗口底色与标题栏，并绕开 CTk 的
    `withdraw()` / `deiconify()` 与焦点回填（闪屏、`bad window path name` 的来源）
- 新增 `theme.set_titlebar_dark(window, dark)`：直接用 `DwmSetWindowAttribute`
  设标题栏深浅色，不改变窗口显示状态（仅 Windows 生效）；Windows 11 22H2+ 上
  还会给标题栏、边框、标题文字上色
- 新增 `theme.repaint_window(window, mode)`：只让窗口自己重绘一次，不碰子控件
- 新增 `theme.recolor_tree(widget, bg)`：把侧边栏、状态栏这类容器的父底色统一
  刷成新值，并让子树里的 CTk 控件按新外观重绘（`CTkButton` 的 `_bg_color` 是构造时
  从父容器取死的，只改父容器会留下一圈颜色不对的方块）
- 新增 `examples/fast_theme.py`：最小可运行接入示例（两个页面 + 切换按钮）
- 修复：`segmented()` 的容器底由 `COLOR_INPUT` 改成 `COLOR_SOFT`——浅色下
  `COLOR_INPUT` 和 `COLOR_CARD` 都是 `#ffffff`，分段控件会和卡片同色、看不出边界
- 修复：`set_titlebar_dark()` 除了深浅色模式，还会用 `DWMWA_CAPTION_COLOR`
  （`35`）/ `DWMWA_BORDER_COLOR`（`34`）/ `DWMWA_TEXT_COLOR`（`36`）给标题栏、
  边框、标题文字上色；只设深浅色模式时浅色标题栏会和内容区几乎同色
- 新增令牌 `COLOR_TITLEBAR`（浅色 `#e8ebf1` / 深色 `#1c1e25`）：标题栏专用色，
  刻意比内容区和侧边栏都亮一档，深浅两套都能看出「顶栏」这一层
- 调整 `COLOR_SEG_SELECTED`（浅 `#dbe6fb` / 深 `#3a5a95`）：原来的深色值 `#1b2a44`
  比容器还暗，「哪一段被选中」看不出来；现在深色下选中段明显亮一档
- 改进切主题的观感：`PageRebuilder.switch()` 支持 `before_rebuild` / `after_rebuild`
  钩子与 `defer`；示例窗口采用最简单的一版——一次同步做完（全局配色 → 窗口底色 →
  当前页整块重建 → 侧边栏），屏幕只在结束时重绘一次，不会出现「底色变了、卡片
  还是黑的」半新半旧；修复切主题时中间一大块仍停在旧底色的问题（透明容器的
  `bg_color` 是构造时取死的）
- 改进：`recolor_tree()` 新增 `deep=False`，只刷直接子控件（侧边栏 41 个控件
  46 ms → 13 个 24 ms）
- 修复：侧边栏底部「设置」按钮属于第二层容器，切主题后没被刷到、会留一块深色
- 修复：列表页徽标（`账号`/`恢复码`/`密钥`）原本用 `COLOR_SEG_SELECTED` 做底，
  深色下提亮后变成蓝底蓝字；改用 `COLOR_SOFT`
- 修复：侧边栏选中项改用主色实底 + 白字（原来用 `COLOR_SEG_SELECTED` 底 +
  `COLOR_ACCENT` 字，深色下蓝底蓝字）
- 示例窗口与 `examples/fast_theme.py` 启动时也会调一次 `set_titlebar_dark()`
- 示例窗口改用上述 API：`ShowcaseApp` 的页面管理交给 `PageRebuilder`，
  删掉 `_apply_global_appearance()`、`_rebuild_page()`、`_stale` 等私有实现
- README 新增「切主题不卡」一节，给出第三方程序的完整接入示例

## 0.5.0 — 2026-10-29

- 示例拆包：`ctk_kit/showcase.py` 变更为 `ctk_kit/showcase/` 包，十个页面各自成文件
  - `ctk_kit/showcase/pages/` 下每页一个模块（`overview` / `foundation` / `buttons` /
    `inputs` / `layout` / `notify` / `listing` / `theme` / `form` / `settings`）
  - 每个模块都能单独启动：`python -m ctk_kit.showcase.pages.buttons`
  - 公共辅助移到 `shell.py`（含 `run_page` 单页启动器），页面清单与假数据移到 `data.py`
  - `ctk-kit-showcase` 与 `python -m ctk_kit.showcase` 仍打开全部十个页面，`--page` 参数不变
- 修复 `ShowcaseApp.toggle_appearance()` 传 `"Light"` / `"Dark"` 导致切换后总是深色
  （`apply_appearance` 只认小写 `"light"`）
- 修复切换深浅色后页面配色错乱（浅色背景配深色卡片、深色文字压在深色底上）
  - 切换后立刻重建当前页；其余页记成过期，切过去时（`show_page`）再按新外观重建
  - 重建走「先建新页、再销毁旧页」：页面里有 `CTkScrollableFrame` 的 `bind_all`
    全局绑定，在按钮回调里当场销毁页面会让事件继续派发给已销毁的控件
    （`bad window path name`）
  - 切主题提速：先清空 `AppearanceModeTracker.callback_list` 再调
    `ctk.set_appearance_mode()`，跳过「一次性重绘 1500+ 个控件」的 380 ms，
    只重建当前页；拿不到内部表时自动退回官方做法
  - 侧边栏跟着重设底色：`CTkButton` 的 `_bg_color` 在构造时从父容器取死，只调
    `_set_appearance_mode` 会留下颜色不对的方框
  - 修复切主题时抛 `_tkinter.TclError: bad window path name ...`：`CTk._set_appearance_mode`
    会记下当前焦点控件、`after(1, widget.focus)` 还回去，而那个控件已被重建销毁；
    现在临时打开 `_deactivate_windows_window_header_manipulation` 跳过这段
  - 修复切主题时整窗闪一下（像盖了层遮罩）：同上，不再 `withdraw()` /
    `deiconify()`，标题栏颜色改用 `DwmSetWindowAttribute` 直接设
  - 重建页面后补一次 `update_idletasks()`，新页直接按正确尺寸出现
- 提示条改成「每条一个无边框小窗口」：与下拉面板同一套做法，窗口由系统裁成圆角，
  圆角以外不绘制，压在页面卡片上不再露出一圈深色底或黑角
  - 描边改成「底色环 + 内容内缩 1px」，四边宽度一致、圆角处连续不断
  - 两种形态统一用 `RADIUS_SMALL` 的小圆角（贴近 Windows 系统圆角），
    `pill` 不再画成胶囊形，四角不会再被裁出豁口
  - 圆角统一交给 DWM 抗锯齿绘制；设置前先清掉旧 region，避免重排后圆角
    被残留 region 挡住又变回直角
  - 裁剪半径与描边环圆角对齐，直边不会被切掉一条
  - 位置按 `master` 的屏幕坐标计算，主窗口移动 / 缩放时跟着边缘走
  - 同一位置最新的提示离边缘最近，其余向里堆叠
  - 超过 `max_visible` 时先关最旧的再重排，位置一步到位，不再出现
    「新卡片闪一下 / 留下一个空框」
  - 出现与消失各约 80ms 淡入淡出，不再突兀
  - 不再全局置顶：提示挂成主窗口的附属窗口，切到别的应用或最小化主窗口时
    一起隐藏，不会一直浮在最前面
- 移除自动化测试套件：删除 `tests/`、`pyproject.toml` 的 `test` 可选依赖与 pytest 配置；
  CI 只保留构建与导入自检，界面改动以单页启动人工验证为准

## 0.4.0 — 2026-10-29

- 新增 `Notifier`：浮在窗口顶部或底部的提示条，不占布局
  - 四种级别 `info` / `success` / `warn` / `error`，颜色取 `tokens.STATUS_COLORS`
  - 两种形态：`pill` 一行胶囊、`card` 带状态图标、标题、正文与关闭按钮
  - 两个位置：`top` / `bottom`，贴边 16px，窗口缩放时跟随；同一位置向下堆叠
  - 默认停留胶囊 2.6 秒、卡片 4.5 秒；指针悬停暂停计时；`duration=0` 常驻
  - `max_visible`（默认 3）限制同位置条数，超出时最旧的先关掉
  - `dismiss()` / `clear()` / `count()` 手动管理，`on_close` 回调
- 新增便捷函数 `notify(master, message, **kwargs)`：按窗口缓存 `Notifier`，连续调用自然堆叠
- 示例新增「提示」页（十个页面）：四种级别、两个位置、两种形态、组合、
  堆叠与常驻，以及只读的用法代码示例

## 0.3.0 — 2026-10-28

- `LazyList` 新增 `item_height` 参数：开启虚拟滚动，只布局视口附近的卡片，
  滚出视口的卡片保留在内存里复用、不销毁，滚回来直接重新布局
- 示例列表页改用虚拟滚动（120 条数据只渲染视口附近的卡片）
- 窗口缩放合并成一次布局，虚拟列表拖动窗口时不再反复重排
- 修复虚拟滚动在 DPI 缩放下滚动错位（CTk 的 `place` 会按窗口缩放放大坐标，
  内层总高要乘同一个系数）
- `TextArea` 新增 `bg_color` / `text_color` 参数：内部底色默认仍是输入框色，
  当日志面板显示时可传 `COLOR_CARD` 或 `"transparent"` 与所在卡片融合
- 示例随 wheel 发布：新增 `ctk_kit/showcase.py` 与 `ctk-kit-showcase` 命令，
  `pip install ctk-kit` 之后直接运行 `ctk-kit-showcase` 就能看九个示例页；
  仓库里的 `examples/showcase.py` 改为转发到 `ctk_kit.showcase:main` 的薄壳

## 0.2.0 — 2026-10-28

- 新增 `TextArea`：带占位符、字数统计与只读模式的多行文本区
- 示例输入页增加大文本演示（普通备注 + 只读日志）
- 示例底栏改为「设置」入口，新增设置页：浅色 / 深色切换、版本与运行环境
- 下拉面板改用 DWM 圆角（Win11）、`SetWindowRgn` 兜底，面板边框沿窗口弧线走
- 下拉面板跟随主窗口移动与缩放，字段隐藏或窗口最小化时自动收起
- 滚动容器滚轮加快：`CTkScrollableFrame` 每格 60px，`LazyList` 每格 60px
- 修复 `LazyList` 滚轮一格跳半屏：canvas 的 `yscrollincrement` 定为 1，单位即像素
- 测试：新增 `tests/test_text.py`，设置页、下拉圆角与滚轮步长补用例

## 0.1.0 — 2026-10-28

首个版本。

- 设计令牌：24 组深浅色颜色、7 档字体、圆角与间距常量
- 组件：主/次/危险按钮、卡片小按钮、输入框、分段选择、开关、自绘下拉
- 布局：页头、节标题、卡片、分隔线、字段标签、说明文字、空态、滚动容器
- `LazyList`：分批渲染的懒加载列表，卡片工厂可替换
- 示例：`examples/showcase.py` 九页全组件展示（运行 `python examples/showcase.py`）
- 测试：pytest 套件，覆盖令牌、主题、按钮、输入、下拉、布局、懒加载列表与示例页
