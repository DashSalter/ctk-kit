# ctk-kit 交接（2026-11-08）

> 下一轮方向：**手风琴（Accordion）组件**。性能优化、文档、主题、配色这些已经收尾，
> 除非用户另说，别再回头动它们。

## 1. 一眼看懂

- 路径 `F:\ctk-ui-kit`，分支 `main`，版本 **0.12.0**（`pyproject.toml:7`、`ctk_kit/__init__.py:42`）。
- 环境：`.venv\Scripts\python.exe`（3.12.9 64bit）、CustomTkinter 6.0.0、Cython 3.3.1、MSVC 2022。
- 远端 `origin` / `gitee` 都指向 <https://gitee.com/kuangjianke/ctk-kit>，两边是同一个仓库。
- `ctk_kit/` 纯 Python 库，`len(__all__) == 130`。
- Windows 底层在 `_src/{win32,glass,frost_layer}.py`，用 `tools/build_core.py` 编成
  `ctk_kit/core/*.pyd`。**注意：`tools/` 和 `article/` 已经移出版本库**（本地还在），
  改 `_src` 时本机照常能编，但别人 clone 下来没有这个脚本。
- 示例：`examples/basics/window.py`（`DemoApp`，16 公开页 + 2 隐藏页）、`examples/demo/`。
- 文档站：MkDocs + Material，`docs/components/` 下有 **15 份组件页**，`mkdocs.yml` 的 nav 已登记，
  配图在 `docs/assets/guide-*.png`。线上 <https://dashsalter.github.io/ctk-kit/>。

```
.venv\Scripts\python.exe -m compileall -q ctk_kit examples
.venv\Scripts\python.exe -m tools.build_core            # 只在改了 _src 时
.venv\Scripts\python.exe examples\basics\window.py      # 起演示
.venv\Scripts\python.exe -m mkdocs build --strict       # 文档（需先装 docs/requirements.txt）
```

## 2. 0.12.0 这一轮做了什么

### 2.1 页面翻页与加载

- `ctk_kit/page.py`：`cards_first` 默认 2（先同步出前两张卡，其余分帧）；`_run_build_step`
  改成「在 `_BUILD_SLICE = 0.012` 秒内尽量多建几张卡，一帧只 `update_idletasks()` 一次」，
  不再每建一张就 `update()`（旧实现比同步建还慢 11–25%）。
- 15 个 `examples/basics/*_page.py` 改成调用 `build_cards(area, [几个 builder])`；
  `settings_page` / `theme_page` 用 `when_built()` 等分帧建完再刷新状态。
- `ctk_kit/pages.py`：`prewarm()` 串行预建相邻页；`_PREWARM_PAUSE = 6.0` 秒内暂停预建；
  `drop_hidden()` 拖动窗口时把看不见的页整棵 `destroy` 掉（`_stop_page_polling` 先停
  `CTkTextbox` 的 `after` 轮询，`window.py` 里 `_install_destroy_guard` 吞掉
  `invalid command name`）。
- 切页横纹：试过 flush、`LockWindowUpdate`、PrintWindow 快照，都无效；最终靠
  「所有页保持 place、只换 z 序」解决，代价是后台页会跟着 resize 重排（已用固定像素尺寸缓解）。

### 2.2 换色 / 主题

- `ctk_kit/theming.py`：`apply_palette(..., skip=)` 只刷可见页，靠 `color_version()` 版本号 +
  `repaint_page()` 在切页时补刷落后页；全树 735 ms → 只刷当前页 102 ms。
- 主题统一成四个名字：**Mica / Frosted / Dark / Acrylic**（`window.py` 的 `_THEME_PRESETS`），
  `set_theme(name)` 一条路径搞定外观、backdrop、暗化、玻璃参数；未知主题抛 `ValueError`。
- 窗口按钮：`theme.set_caption_buttons(window, visible, minimize=, maximize=)` +
  `App.show_window_buttons/show_minimize_button/show_maximize_button`。关整组会连带图标消失
  （系统行为，无解）；恢复按钮时会重新挂图标。

### 2.3 输入类控件

- `sugar.Enablable` 统一：`set_readonly(flag)` / `is_readonly()` / `unlocked()`
  （上下文管理器，只读下临时解锁，写文件/写值用）。
- 覆盖：`CTkEntry`、`SearchBox`、`TextArea`、`PathField`、`Spinner`、`DropField`、
  `DatePicker`、`TimeField`、`ColorPicker`。
- `DatePicker` 改成三段式（年 - 月 - 日，`readonly=False` 时可键入，回车/失焦生效），
  只有右侧三角形弹层；`TimeField` 同样。
- `Radio` 新增 `group="名字"`，同组内部共用一个 `StringVar` 互斥，不用自己建变量。

### 2.4 文档

- `docs/components/` 15 份，结构统一：`## 作用` → 每组件 `## 名称` → `### 作用 / ### 参数 / ### 方法 / ### 示例`；
  只列常用参数与方法，纯配色变体合并到「变体」小节。
- 每份顶部一张 `docs/assets/guide-<name>.png`，由 `PrintWindow` 抓真实控件生成。
- `README.md` 重写成「优势 / 特点 / 功能」导向（原来 1057 行的参数手册已删）。

### 2.5 其他

- `pyproject.toml`：`conf_base` 从必需依赖移到 `[demo]` 可选组，核心库零持久化代码。
- `notify.py`：级别图标改用 Pillow 4 倍超采样画真圆（原来用 `CTkLabel` 的 `corner_radius`，
  22px 下是折线近似，边缘有锯齿）。
- 淡入结束后统一 `clear_window_alpha()` 摘掉 `WS_EX_LAYERED`（layered 窗口在 125% 缩放下
  文字会被 DWM 重采样发虚），涉及 `notify / dropdown / select / context_menu / tooltip / dialog`。
- `App.destroy()` 改成 `tk.call("destroy", ".")` 一次性销毁整棵树：3185 个控件从 ~2.5 s 降到 ~0.36 s。

## 3. 代码结构速查

| 关注点 | 位置 |
| --- | --- |
| 窗口、背景、玻璃、主题 | `ctk_kit/window.py` |
| 页面基类、分帧建卡 | `ctk_kit/page.py` |
| 页面栈、预建、丢页 | `ctk_kit/pages.py` |
| 侧边导航 | `ctk_kit/sidebar.py` |
| 换色 | `ctk_kit/theming.py` |
| 颜色令牌 | `ctk_kit/tokens.py` |
| 卡片 / 滚动容器 | `ctk_kit/layout.py` |
| 折叠面板（单节） | `ctk_kit/collapse.py` |
| 提示 toast | `ctk_kit/notify.py` |
| 窗口特效 | `ctk_kit/core/*.pyd` ← `_src/*.py` |

## 4. 性能现状（只作参考，不是待办）

- `import ctk_kit` 约 300 ms；`DemoApp()` 构造约 780 ms。
- 首次切组件页：首帧 186 ms 可见，整页建完约 1.7 s；已建好的页切回 0–24 ms。
- `apply_palette` 全树 735 ms → 只刷当前页 102 ms。
- resize 时单页重绘约 150 ms（Tk 内部成本，`cProfile` 里没有 Python 热点，别再优化了）。

## 5. 坑（务必先看）

- **不要用 PowerShell `Set-Content` / `Out-File` 改源码**（GBK 会把 UTF-8 读坏）。
  只用 `edit` / `write`，或 Python `io.open(..., encoding="utf-8", newline="\n")`。
- CTk 的 `place()` 不接受 `width` / `height`（会抛 `ValueError`），要改尺寸用 `place_configure`。
- `_src` 里的 pyd 在示例进程开着时被占用，编译会「拒绝访问」，先关窗口。
- `Card.body` 是属性，不是方法。
- `Switch(master, command, *, text=)`：第二个位置参数是 `command`，文字必须用 `text=`。
- `DropField` / `TagSelectField` 用 `values_provider=`，不是 `values=`。
- `ContextMenu` 是 `show(x, y, source=None)`，不是 `popup(event)`。
- 系统标题栏是非客户区，Tk 控件放不进去；要放只能自绘整条标题栏（已试过，用户不要）。
- 别调 `page.on_color()`，会写盘 `C:\Users\admin\.ctk-kit\window.json`。

## 6. 下一步：手风琴组件

用户原话：「我打算后面弄手提琴方面的组件」（手风琴 / Accordion）。

现状：`ctk_kit/collapse.py` 已有单节 `Collapsible`，
构造 `Collapsible(master, *, collapsed_text="显示代码", expanded_text="隐藏代码", expanded=False,
button_height=36, on_toggle=None, **kwargs)`，方法 `expand() / collapse() / toggle() /
set_expanded(flag) / set_texts(collapsed, expanded)`，内容容器是 `collapse.body`。

建议新增 `Accordion`（新文件 `ctk_kit/accordion.py`，复用 Collapsible，不要重写动画）：

```python
acc = Accordion(card.body, mode="single")      # single 互斥 / multiple 可多开
panel = acc.add("基本信息")                    # 返回内容容器，往里放控件
acc.expand(0); acc.collapse(0); acc.toggle(1)
acc.expanded_items() -> list[int]
```

要点：

- `mode="single"` 时展开某节先收起同组其它节；`mode="multiple"` 各管各的。
- 每节标题右侧可放一句 `count` / `detail` 摘要（折叠时也能看到）。
- 节之间用 `layout.divider()` 或 `pady` 分隔，别用嵌套 CTkFrame 加深。
- 写完后：`docs/components/misc.md` 补一节（照现有结构），`examples/basics/collapse_page.py`
  加一张演示卡，`CHANGELOG.md`「未发布」加一条。

## 7. 验收清单

1. `compileall -q ctk_kit examples` 无错。
2. `python -c "import ctk_kit"` 无错。
3. 起 `examples/basics/window.py`，切几页看有没有横纹、拖动窗口是否还卡。
4. 文档：`mkdocs build --strict`（或至少检查新 md 的代码块能编译、图片路径存在）。
5. 提交前 `git status` 确认 `article/` 与 `tools/` 没有被重新加进来。
