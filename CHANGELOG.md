# 更新记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## 0.10.0 — 2026-11-05

- 新增 `App.set_window_debug()` / `window_debug()`：窗口级 DWM 调试项。
  `hide_frame_border` 写 `DWMWA_VISIBLE_FRAME_BORDER_THICKNESS`（37，Win11
  22H2+）去掉四周 1px 系统边框，不支持时 `window_debug()["frame_border_supported"]`
  为 `False`；`disable_transitions` 写 `DWMWA_TRANSITIONS_FORCEDISABLED`（3）
  关掉窗口出现 / 重建时的过渡动画
- 新增 `App.frame_bounds()`：`DWMWA_EXTENDED_FRAME_BOUNDS`（9），返回窗口含阴影
  的真实屏幕矩形，和 `winfo_rootx()` 那套客户区坐标对比能看出标题栏与边框的占用
- `ctk_kit.win32` 新增 `set_frame_border_thickness()` / `set_transitions_disabled()` /
  `extended_frame_bounds()` 与常量 `DWMWA_VISIBLE_FRAME_BORDER_THICKNESS`（37）/
  `DWMWA_TRANSITIONS_FORCEDISABLED`（3）/ `DWMWA_EXTENDED_FRAME_BOUNDS`（9）
- 示例设置页新增「窗口调试（DWM）」卡片：两个开关 + 一行「读取真实边界」，
  拨动即可看到效果；本机不支持 37 时自动提示
- 示例设置页「毛玻璃微调」的「底色」新增「白」：白色 tint 配高「压暗」就是
  白雾玻璃，背后内容只剩淡淡一层（DWM 的 tint alpha 删不掉模糊层，压不到全不透）
- `SidebarNav` 新增 `divider=True`：侧边栏与页面之间画一条 1px 竖线，底部留
  20 逻辑像素不贴边，切深浅外观跟着换色；传 `False` 不画
- 下拉 / 多选标签 / 层级树的面板在毛玻璃下改为真玻璃：先挂
  `acrylic_window(frame=True)` 再用 `popup.set_glass_geometry()` 校正客户区，
  不再是一块不透明的黑底；浅色外观的玻璃仍用普通实色卡片
- 新增 `App.set_frost_backdrop()` / `clear_frost_backdrop()` / `frost_active`：
  在主窗口下面垫一层「颜色窗口」（`ctk_kit.frost_layer.FrostLayer`），位置、
  尺寸、圆角跟随主窗口，`spread` 可再往外多出一圈；颜色走纯色块，`alpha`
  用 Tk 的 `-alpha` 控透明度。毛玻璃模式自动建一层默认底色（深色配黑、
  浅色配白）
- `ctk_kit.win32` 新增 `set_round_region()`：给窗口裁圆角矩形区域。
  `DWMWA_WINDOW_CORNER_PREFERENCE`（33）对无边框窗口不生效，底层颜色窗口
  只能靠它裁圆角
- `ctk_kit.inputs.Segmented` 新增 `set_enabled()`：禁用后不响应点击，底色
  退回输入框色
- 示例设置页「外观模式」改成浅色 / 深色 / 毛玻璃三项；毛玻璃下多出「启用
  背景颜色」「背景颜色」（黑、白、红、橙、黄、绿、青、蓝、紫九色）、
  「背景透明度」「背景尺寸」四行，未勾选时后三项禁用

### 破坏性变更

- 删除 `ctk_kit.preferences`（`WindowState` 与 `read_*` / `write_*`）：核心库
  不再内置任何持久化。`App` 新增 `state=` 参数，传一个带 `read_geometry` /
  `write_geometry` / `read_appearance` / `write_appearance` /
  `read_color_theme` / `write_color_theme` / `read_backdrop` /
  `write_backdrop` 的对象即可恢复原来的行为；不传则什么都不记，
  `remember_geometry` / `remember_theme` 随之失效。现成实现见
  `examples/basics/window_state.py`（`WindowStateStore`）

### 构建

- 核心模块 `win32` / `glass` / `frost_layer` 改为 **abi3 二进制**发布：源码放在
  私有的 `_src/`（`.gitignore` 忽略），仓库里只有 `ctk_kit/core/*.pyd` 与对应的
  `*.pyi`，和普通 Python 代码分开放。用 `python -m tools.build_core` 编译（Cython +
  `Py_LIMITED_API=0x03090000`），产物文件名不带 `cp3xx` 后缀，Python 3.9+
  都能加载；本地开发可以 `python -m tools.build_core --copy` 直接拷源码
- `ctk_kit/__init__.py` 在导入时检查三个核心模块，缺失时给出明确提示（当前
  Python 版本 / 平台 / 该跑哪条命令），而不是抛一句 `ModuleNotFoundError`
- `.gitignore` 的缓存规则由 `*.py[cod]` 改为 `*.py[co]`：原写法会把 `.pyd`
  一起忽略掉

## 0.9.2 — 2026-11-02

- `App` 新增 `remember_geometry=True`：关闭时用 conf_base 把窗口大小和屏幕
  位置写进 `~/.ctk-kit/window.json`，下次启动自动恢复；最大化/最小化关闭
  不覆盖上次的普通几何，配置损坏时回退到 `size`
- `App` 新增 `remember_theme=True`：记住上次选择的深浅外观与颜色主题，
  下次启动自动恢复；`set_appearance_mode()` / `set_color_theme()` 切换时
  写入配置，传 `save=False` 可临时切换
- 新增依赖 `conf_base>=0.5`（窗口几何与主题持久化）
- `PageRebuilder.build_all(progress=None)`：启动时逐页构建页面，可传
  `progress(done, total, name)` 驱动进度条；`cards_first > 0` 的页面会跳过，
  留到第一次切过去再建
- `PageBase` 新增 `cards_first`（默认 0）：页面声明 `3` 时启动跳过，
  `build_cards(area, builders)` 前 3 张同步、其余按 12ms 分帧；`when_built()`
  在队列清空后回调，示例的「组件」页用它把 `bind_events()` 放到建完之后
- 新增 `LoadingOverlay`：启动遮罩，大 logo + 说明文字 + 4px 进度条，
  `set_progress()` 驱动、`finish()` 撤掉；示例窗口启动时先盖遮罩再逐页构建
- 新增 `ctk_kit.styles`：把侧边栏、卡片、状态栏的颜色集中成样式表，
  `style_of(name, state)` 按当前外观解析，切主题时只 `configure` 换色
- `SidebarNav` / `Card` / `StatusBar` 新增 `apply_theme(mode)`：外壳控件原地
  换色，不销毁重建；`App.register_themeable(widget)` 可登记不在导航里的外壳
- `StatusBar.set_text(tone=...)` 的圆点颜色用 120ms 渐变过渡，级别切换不硬跳
- 新增 `paint.animate_color()`：任意控件颜色逐帧渐变，可取消
- 新增 `fonts.measure_text()`：按文字量宽，不触发几何重排；`Badge` 改用它
- `Table` 表头支持鼠标悬停高亮当前列、显示列边界；拖动列宽只改当前列，
  拖到表头右边缘就停、不再挤占其他列，数据区补列分隔线，列太窄时文字自动截断加省略号
- `Table` 新增 `page_size` 分页：只画当前页，底部复用 `Pagination` 显示总条数与页码；
  新增 `set_page()` / `set_page_size()` 与 `pages` / `page` 属性，`rows()` 仍返回全量
- `Scrollable` 默认 `auto_hide=True`：内容放得下时自动隐藏滚动条，滚动条 lane 提前预留，
  显示/隐藏不会挤动内容
- Windows 启动 / 最大化 / 还原时不再闪黑块：`App` 自动把 `TkTopLevel` 窗口类的
  擦除画刷换成 `COLOR_BG`，切主题时同步更新；新导出 `set_window_brush(window)`

- 新增 `Avatar`：圆形头像（文字或图片），右下角可挂在线状态点；
  圆形与状态点用 Pillow 4 倍超采样绘制，图片头像自动裁圆
- 新增 `Breadcrumb`：面包屑，最后一项当前页不可点，中间项悬停变色、点击回值；
  默认分隔符用 Pillow 画成折线图，边缘没有锯齿
- 新增 `Timeline`：纵向时间线，圆点与竖线串联，支持 `active` 高亮；
  圆点用 Pillow 4 倍超采样绘制
- 新增 `Skeleton`：骨架屏占位条，默认 650ms 呼吸，`start()` / `stop()`
- 新增 `Splitter`：可拖动分栏，左右 / 上下两种方向，夹最小尺寸
- 新增 `Popover`：点击控件弹出的浮动卡片，可放任意控件，点外面关闭
- 新增 `ColorPicker`：预设色板选色，带色块预览和 hex 显示
- 新增 `StatusBar`：底部状态栏，左侧状态点 + 文字、右侧补充信息
- 新增 `Carousel`：卡片轮播，左右箭头 / 圆点切换，可自动播放
- 新增 `TreeView`：树形表格（`ttk.Treeview`），配色按 tokens 调整，支持展开 / 收起与选中回调；
  展开三角用 Pillow 4 倍超采样画成实心三角，替换 clam 的细线空心三角
- 新增 `MenuBar`：顶部菜单栏，下拉复用 `ContextMenu`
- 示例窗「组件」页补第三档演示：头像、面包屑、时间线、骨架屏、分栏、浮动卡片、颜色、状态栏、轮播、菜单栏
- 树形表格示例从「组件」页移到「表格」页，和 `Table` 放一起
- 修 `Splitter` 拖动时手柄来回闪：拖动坐标误用了手柄自身坐标，改为相对分栏容器
- 修 `ColorPicker` 点右侧三角形打开后立刻关闭；三角形字号加大，
  指针还在控件上时不收起
- `SearchBox` 的内部输入框补上右键菜单（复制 / 粘贴 / 剪切 / 清空）
- `TreeView` 行高、字体、斑马纹与滚动条对齐 `Table`：表头 40 高、
  `COLOR_SOFT` 底、隔行淡底色、滚动条用 `CTkScrollbar`
- 新增 `Badge` / `Tag`：只读状态标签，`soft` / `solid` / `outline` 三种样式，
  支持语义色、计数和纯圆点状态；圆角背景用 Pillow 4 倍超采样绘制，边缘没有锯齿
- 新增 `Tabs`：页签视图，封装 `CTkTabview`，统一卡片底、描边和选中色
- 新增 `Calendar` / `DatePicker`：月历与日期选择；周一开始，今天描边、选中实心，
  `DatePicker` 用无边框弹层，贴边翻转、失焦收起
- 新增 `RangeSlider`：双滑块区间选择，两个圆球不会交叉，松手才回调
- 新增 `SearchBox`：带放大镜和清空按钮的搜索框，输入防抖（默认 300ms），回车立即触发
- 新增 `Steps` / `Wizard`：横向步骤条（完成对勾 / 当前数字 / 未开始描边）与分步向导，
  `Wizard` 每步内容由构建函数现建，底部自动带上一步 / 下一步 / 完成
- 示例窗「组件」页补第二档演示：页签、日期、区间滑块、搜索框、步骤与向导
- 新增 `Tooltip`：任意控件的悬停提示，支持延迟、动态文字、贴边翻转
- 新增 `Pagination`：页码条，自动折叠省略号、边界禁用、`command` 翻页回调
- 示例窗新增「组件」页：徽标与标签、悬浮提示、分页条三张卡片，每张都带「查看实现」代码块
- `SidebarNav` 新增 `hidden_pages`（只登记、不占导航位的页面）与 `footer`
  （底部按钮上方的自定义区域）；示例窗底部加账号头像行，点头像进入
  「个人中心」页（大圆头像 + 名称「加点盐」）
- 输入框默认带右键菜单：`CTkEntry` / `ToolbarEntry` / `FormEntry` / `TextArea` / `DropField`
  不用写任何代码就有「复制 / 粘贴 / 剪切 / 清空」，右键落在内层 canvas、文字上也照常弹出
  - 菜单项跟着控件状态走：没选中文字时「剪切 / 复制」灰掉，剪贴板里没有文本时「粘贴」
    灰掉，输入框为空时「清空」灰掉；只读文本区只剩可用的「复制」
  - `menu=True`（默认）挂默认项，`menu=False` 关掉，`menu=[(文字, 函数), ...]` 只用自己的项
  - 默认项顺序是「复制 / 粘贴 / 剪切 / 清空」
- 修右键菜单的「粘贴」位置：右键本身不会移动插入点，原来粘贴总落在上一次的光标处
  （常常是末尾），看着像「粘错地方」。现在弹菜单前先把插入点挪到点击处
  - 粘之前还会撤掉占位符、聚焦输入框：空框不会再出现「粘贴后混进 placeholder 文字」
  - 发 `<<Copy>>` / `<<Cut>>` / `<<Paste>>` 前把焦点还给输入框，点完菜单也能接着打字
- 修 `DropField` 底边描边在部分缩放下消失：`CTkFrame` 绘制时会把高度向下取整到偶数
  （`draw_engine` 的取整选项），控件物理高度是奇数时，最后那 1px 描边整条被裁掉——
  125% / 150% 这类缩放下很容易踩中。构造时关掉取整（`set_round_to_even_numbers(False, False)`），
  按真实高度画，四边与圆角都和原来一样平滑
- 新增 `attach_edit_menu(widget, items=None, *, preset=True, width=132, reset=False)`：默认菜单的底层函数
  - 返回 `ContextMenu`，挂上之后仍可 `add_command` 继续追加
  - 重复调用返回同一个菜单对象，这次传的 `items` 追加到已有菜单末尾；`preset` / `width`
    只在首次挂载时生效（之前重复调用会把 `items` 静默丢掉）
  - `reset=True` 丢掉现在这套重新挂一遍，用来把改乱的菜单恢复成默认四项
  - 单行、多行都行：内部自己找承载文字的 `tk.Entry` / `tk.Text`，`TextArea` 多包的一层也能认出来
- `attach_menu` / `attach_edit_menu` 改用 `add="+"` 绑定右键，不再覆盖控件上已有的绑定；
  同一个控件后挂的菜单替换先挂的，不会叠出两套
- `ContextMenu.add_command(..., enabled=...)`：传布尔或「收控件、返回布尔」的函数，
  弹出时按控件状态决定是否置灰；置灰项文字用 `COLOR_FAINT`，点了不执行，也不再回传 source
- `ContextMenu` 支持运行时增删改菜单项：`has_command(label)` 判断在不在，
  `remove_command(label)` 删掉第一项（顺手清掉因此孤立的分隔线），
  `rename_command(label, new_label)` 换文字但保留回调
- 示例窗「输入」页新增「输入框右键菜单」卡片（默认 / 自定义 / 关闭三种写法），
  「菜单」页补一张「输入框默认就带菜单」卡片：单行与多行输入框，外加
  「+ 插入时间戳」「改名」「删除」「恢复默认」四个按钮，演示增删改的实际效果
- 新增两种下拉样式，加上原来的 `DropField` 一共三种
  - `TagSelectField`：多选标签。选中的值变成圆角标签排进框里，点标签本身即可删掉；
    值不重复，已选中的项再点一次是取消选中；标签多了横向滚动、滚轮可滚，
    没有输入框；`get()` 返回列表，`command` 收到整个列表
    - 标签就是一个 `CTkLabel`：底色、圆角、文字在同一个控件上，里面不再套 ×；
      底色用 `COLOR_ACTIVE`、文字转白，和分段控件的选中段一致
    - 候选行和 `DropField` 用同一个做法：一行一个 `CTkButton`，高度 32、上下各留 1px、
      圆角 `RADIUS_SMALL`，三张下拉列表的行距一致
    - 已选中的候选行底色只比卡片色亮一点点（`#1b262b`），靠青色文字区分，
      选很多项也不会整块面板发亮
    - 候选超过面板高度时右侧出现细滚动条（`CTkScrollbar` + `style_scrollbar`），
      放得下时自动收起
  - `TreeSelectField`：层级树。数据是嵌套的 `("分组", ["子项", ...])` 元组，字符串等于叶子；
    分组节点只能展开 / 收起（右侧 `▶` / `▼` 跟着变），不可选中，子项逐级缩进；
    展开与收起只增删受影响的那几行、不重建整个列表，再重算面板高度与上下翻转；只有叶子能选
  - 两者共用新的 `ctk_kit/select.py` 里的面板实现（`_PopupPanel`），跟随窗口、贴边翻转、
    滚出可视区自动收起的行为与 `DropField` 一致
  - 两条下拉面板都补了前台判断：面板是 `overrideredirect` + `topmost`，切应用 / 切虚拟桌面 /
    换显示器时 `<FocusOut>` 不一定能收到，原来会有一段时间压在新窗口上面。现在每 60ms 的
    位置轮询里顺带问一次 `GetForegroundWindow`，前台不是本程序就直接收起；鼠标移到面板上
    也会再确认一次
- 示例窗新增「下拉」页（`examples/basics/select_page.py`）：单选 / 多选标签 / 层级树三张卡片，
  每张都带「查看实现」
- 三个下拉都支持禁用个别候选项：`disable(value)` / `enable(value)` / `is_disabled(value)` /
  `get_disabled()` / `set_disabled(values)` / `clear_disabled()`，构造时也能传 `disabled=[...]`
  - 禁用的项在面板里置灰、点击不响应；面板开着时改禁用集合会立刻刷新
  - 多选里如果某项已经在标签中，`disable()` 会顺手把它从标签里移除
- 新增 `Spinner`：带上下箭头的步进输入框，示例在「输入」页
  - 数字模式走 `from_` / `to` / `increment`，到边界停住；`as_int=False` 时返回 `float`
  - 列表模式传 `values=[...]`，上下箭头在备选文字里前后移动
  - 直接改数字后回车会夹回区间；箭头是 canvas 画的小三角，不依赖字体符号
  - 箭头先 pack，输入框后 pack，否则 `expand` 的输入框会把箭头挤成 5px
- 新增对话框：`alert` / `confirm` / `prompt` / `Dialog`（`ctk_kit/dialog.py`）
  - 无边框圆角卡片，没有系统标题栏
  - 模态：`grab_set` 挡住客户区输入，父窗口上临时绑 `<MouseWheel>` 拦住滚轮
    （CTk 的滚动走 `bind_all`，光靠 grab 拦不住）
  - 主窗口仍然可以拖，对话框跟着走：父窗口的 `<Configure>` 里直接重排、不隔帧——
    Windows 上 Tk 处理 `WM_MOVE` 时是同步分发 `<Configure>` 的，隔帧会退回主循环，
    拖动过程中就完全不跟手
    - 先按 `event.widget` 过滤掉子控件冒泡上来的事件：滚动页面时每帧几十个
      `<Configure>`，不过滤会跟着重排几十次
  - 打开期间临时 `-topmost`：无边框窗口不参与 WM 的层级管理，拖动主窗口时
    会被压到下面，看起来像「消失了」；关窗后恢复
  - 修拖动时对话框尺寸自增长：原来每帧读 `winfo_height()` 再 `geometry()`，
    高度会被自己的 geometry 反复放大（实测从 261 一路涨到 998）。首次定位时把
    尺寸存进 `_frame_size`，之后 `_reposition` 只用这个固定值，也不再碰
    `update_idletasks`
  - 位置夹在屏幕内，窗口拖到屏幕外也点得到
  - `level` 决定图标颜色（info / success / warn / error），`detail` 在正文下面补小字
  - `confirm` 返回布尔；`prompt` 返回字符串或 None；`Dialog` 按 `buttons=[(文字, 返回值)]` 返回被点的值
  - `danger=True` 让确认按钮变危险色
  - 示例新增「弹窗」页
- 程序图标：`App` 默认挂上内置 logo，标题栏左上角和任务栏都是它
  - `icon=True`（默认）用内置图；`icon=False` 不设；`icon="路径"` 用自定义 `.ico` / `.png`
  - 新模块 `ctk_kit/branding.py`：`set_window_icon(window)` 给任意窗口挂图标，
    `load_logo(size)` 拿一张缓存好的 `PhotoImage`（给 canvas / label 用），
    以及 `LOGO_PATH` / `ICON_PATH` / `logo_path(size)`
  - 资源在 `ctk_kit/logo/`：`logo.png`（1024 透明主图）、`logo-16…256.png`（预渲染小图）、
    `logo.ico`（多尺寸 Windows 图标）、`logo-source.jpg`（原始手绘图留档）
- `SidebarNav` 顶部大标题左侧显示内置 logo：`logo=True`（默认）/ `False` / 自定义路径，
  `logo_size` 控制边长（默认 32 逻辑像素）；切深浅色时跟着刷新背景
- `ImageViewer` 空状态默认画 logo：没图时中间显示图标，下面一行提示文字；
  `empty_image=False` 回到原来的纯文字
- 新增 `ctk_kit/misc.py` 里的 `Progress`：进度条的完整版  - 连续 / 分格（`steps`）/ 带百分比（`show_text`）/ 斜条纹（`striped`）/
    不确定态（`start_indeterminate()`）
  - `radius` 控制端点圆角，传 0 换成直角；`height=2~4` 就是细线样式
  - `handle=True` 在进度端画一个圆点把手，拖着就能改值
  - 把手不画背景色描边（会盖掉轨道、看起来像一圈黑框）；圆点位置夹在
    两端之内，拖到 0% / 100% 也不会被切掉一半
  - `color` / `track` 可单独换已完成色和轨道色
  - 绘制照 ttkbootstrap 的 `Meter` 做法：Pillow 在 3 倍尺寸上画圆角矩形和斜纹，
    再用 LANCZOS 缩回目标尺寸，圆角和条纹边缘是平滑的
- 新增 `RingProgress`：圆环进度
  - `ticks>0` 时环外画一圈刻度，走过的刻度用主色；有刻度时圆环自动往里收
  - `ring=False` 只画刻度、不画圆环本体（纯刻度圈），`ticks` 就是刻度密度，
    `tick_len` 控制刻度长度
  - 中心百分比可以关掉；尺寸由 `size` 固定
  - 同样走 Pillow 3 倍超采样，圆环弧线不再是 canvas 那种硬阶梯
  - 没装 Pillow 时退回 canvas 直角色块 / 硬边弧，功能照常
- 勾选框与单选圆点改用 Pillow 画指示符（`ctk_kit/choices.py`：`Check` / `Radio`）  - 4 倍尺寸画好再 LANCZOS 缩回，圆形和圆角方块边缘不再是一格一格的阶梯
  - `Checkbox()` 现在返回 `Check`，`radio_group()` 内部改用 `Radio`；两者都保留
    `get()` / `select()` / `deselect()` / `configure(command=...)`，调用方不用改
  - 没装 Pillow 时退回 canvas 画圆/方框
- 开关（`Switch`）改用 Pillow 4 倍超采样绘制轨道和圆球：不再依赖 canvas 的
  圆角矩形/椭圆图元，胶囊两端和圆球边缘的锯齿消失
  - `Switch` 从返回 `CTkSwitch` 改为自绘控件，`get()` / `select()` / `deselect()` /
    `toggle()` / `configure(command=...)` 保持兼容，调用方不用改
  - 尺寸仍是 36×18 的轨道、12 的圆球，`width` 语义不变
- `Spinner` 箭头改用 Pillow 图片（和 ttkbootstrap 的 Spinbox 一样用固定尺寸的
  caret 图）：canvas 画多边形时中点取整会让上下两个三角差 1px，图片没有这个问题
- 新增 `Stepper`：紧凑步进器 `[ − ] 当前值 ▾ [ + ]`
  - 左右两个按钮加减一步；点中间展开候选（复用 `_PopupPanel`）
  - `values` 给一组备选，或 `from_` / `to` / `increment` 走数值范围
  - `suffix` / `decimals` 控制显示；`get()` / `set()` / `command` 与 `Spinner` 一致
  - 示例「输入」页的步进卡片加了一行「紧凑」
- Pillow 改为必需依赖：`pyproject.toml` 的 `dependencies` 里加上 `pillow>=9`，
  原来的 `ctk-kit[image]` 可选组去掉（`pip install ctk-kit` 会直接装上）
- `divider` 加了 `text`（线中间带一行字）、`dashed`（虚线）、`color`（线色）三个参数；
  新增 `vertical_divider` 画 1px 竖线
  - 纯 tk 的线不认令牌里的 `(浅色, 深色)` 元组，内部统一先解析成当前色
  - 虚线用 canvas 画短线段，宽度变化时重画
- 示例窗新增「杂项」页（`examples/basics/misc_page.py`）：进度条五种形态 + 分割线四种样式；
  原来「选择」页的进度条挪到杂项页，滑块卡片也一并去掉（拖动演示由带把手的进度条覆盖）

## 0.9.1 — 2026-11-02

- 修 `DropField` 的候选面板在页面滚动时乱跑：原来靠顶层窗口的 `<Configure>` 跟随，
  而 Tk 会把子控件的 Configure 冒泡到顶层，滚动时被反复触发、面板越滚越偏、最后跑到窗口外
  - 窗口**移动**时面板立刻整体平移（尺寸没变说明只是挪位置）；窗口**缩放**时左边不动，
    只把越过右边 / 下边的部分裁掉——窗口右边界推过来时面板跟着变窄，不会被整块推走
  - 裁完连一行都放不下就收起；停手 300 ms 后按新尺寸完整归位一次
  - 判断依据是顶层窗口自己的 `<Configure>`，子控件冒泡上来的一律忽略
  - 页面滚动不会产生顶层 Configure，交给每 60 ms 一次的位置比对兜底
  - 下方放不下自动翻到输入框上方；上下都放不下就裁到可用高度并在面板内部滚动
  - 候选超过 8 项时面板内部滚动条生效（自己绑 canvas，不用 `CTkScrollableFrame`——
    后者 `bind_all` 会抢全应用的滚轮）
  - 控件被滚出可视区时面板自动收起，不再挂在窗口外
  - 窗户缩小时面板跟着收窄；窄到放不下一个面板时直接收起，不再硬塞到窗口左边缘
  - 窗口刚变尺寸的那一帧子控件还没重排完，位置对齐推迟到 `after_idle`，避免用旧坐标算错
- 右键菜单几处修正（`ContextMenu` / `attach_menu`）
  - 整个应用同时只留一个菜单：右键另一个控件时上一个自动收起（之前每个控件一个实例，
    连点三个按钮会叠出三个菜单）
  - `attach_menu` 新增 `deep=True`：连容器里的子控件一起绑。原来只绑容器自身和它露在外面的
    canvas，右键落在里面的文字上没反应、面板右侧的空白也点不到
  - 弹出位置改用 `winfo_pointerxy()` 取真实鼠标坐标，不再依赖 `event.x_root`——事件从
    内部 canvas 冒上来时那个值会偏，菜单会跑得离鼠标很远
  - 屏幕边界改用 `winfo_vrootwidth / vrootheight`（物理像素）。`winfo_screenwidth()` 是
    逻辑值（本机 1707，物理 2560），和指针坐标混用会算出「右边永远放不下」，菜单就被一路
    夹到左边；右边真的放不下时才翻到鼠标左侧，右边缘贴着鼠标
- 示例窗拖动窗口时不再卡顿：页面外壳改成用 `place` 管尺寸，拖动期间停止更新
  （相当于冻结布局），停手 320 ms 后再按新尺寸重排
  - 输入页实测每次 resize 从约 220 ms 降到约 70 ms；剩下的是 CTk 根窗口与侧边栏的固有重绘
  - 代价：拖动过程中内容保持原宽度（变宽时右侧露出底色），松手瞬间归位
  - 顺带记一笔：`place` 的 x / y / width / height 是屏幕像素，不会像 `wm geometry`
    那样被 DPI 缩放，混用会算错尺寸
  - 修外壳换成原生 `tk.Frame` 后切浅色主题内容区还是黑的问题：`tk.Frame` 的颜色写死在
    构造时不会跟外观走，切主题时要手动刷；页面容器的 `fg_color` 也从 `"transparent"`
    改成 `COLOR_BG`，否则透明查找链在原生外壳处断掉，CTk 拿不到颜色会退回深色

## 0.9.0 — 2026-11-01

- 新增 `Table`（`ctk_kit/table.py`）：带固定表头的表格
  - 表头和内容各用一块 canvas 自绘，配色全部从 `tokens` 取；不用 `ttk.Treeview`，
    因为它在 Windows 上走系统主题，表头、行、滚动条的配色没法跟深浅色对齐
  - `columns` 每项是 `(标题, 宽度, 对齐)`，宽度为 `None` 的列吃掉剩余宽度
  - 表头固定不滚动；行数超过 `max_visible_rows` 才出现滚动条，否则高度按行数自适应
  - 滚动条独占表格右侧一列，不压在内容上，并且跨表头与内容两行、从上到下铺满
  - 隔行淡底色、空数据居中提示、鼠标滚轮滚动
- 新增 `ImageViewer`（`ctk_kit/image_view.py`）：图片查看器
  - 滚轮以光标位置为中心缩放，按住左键拖动看局部，双击回到「适配窗口」；
    另有 `fit()` / `set_zoom()` / `zoom()` / `set_image()`，`on_zoom` 回调用来显示倍率
  - 只对「画布上看得见的那一块」重采样，渲染尺寸与放大倍率无关——否则放大到 8 倍
    会去生成一张上亿像素的位图，越放越卡
  - 缩小时用 LANCZOS、放大时用 BICUBIC；拖动时只平移已有的位图，挪到头了才重采样
  - `min_zoom` 默认 `1.0`，最小就是「适配窗口」，不会缩成一团小图；
    目标尺寸由取整后的源矩形反算，宽高比与原图严格一致
  - Pillow 成为可选依赖：`pip install "ctk-kit[image]"`。没装时 `import ctk_kit`
    照常可用，只有访问 `ctk_kit.ImageViewer` 时才提示安装
- 新增 `ContextMenu`（`ctk_kit/context_menu.py`）与 `attach_menu()`
  - `attach_menu(按钮, [("编辑", on_edit), ...])` 一行给任意控件挂右键菜单；
    回调接一个参数时，拿到的就是被右键的那个控件，额外传参用 `lambda btn: fn(btn, ...)`
  - 菜单不用 `tk.Menu`：无边框 `CTkToplevel` 铺底做 1px 描边、DWM 裁圆角，
    悬停色 `COLOR_SOFT_HOVER`，与下拉面板、提示浮窗同一套做法
  - 点中某项先关菜单再执行回调；点到外面、按 Esc、切走窗口（失焦）都会收起
  - 菜单开着时拖动或缩放主窗口，菜单按同样的位移跟着走
- 示例窗新增「菜单」页：挂菜单、回调拿控件、自己控制弹出时机，附示例代码
- 示例窗新增「表格」「图片」「选择」「展开」四页，都能 `python -m ctk_kit.showcase.pages.<名字>` 单独启动
- `pyproject.toml` 增加 `[project.optional-dependencies] image = ["pillow>=9"]`
- 新增 `Collapsible`（`ctk_kit/collapse.py`）：可折叠面板
  - 标题行常驻（`▼ 显示代码` / `▲ 隐藏代码`），点击向下展开 `body`，再点收起；
    收起时内容区完全退出布局，不会在卡片里留下一块空白
  - `collapsed_text` / `expanded_text` 分别控制两个状态的文字，`expanded` 可让面板默认展开，
    `on_toggle(expanded)` 拿到新状态
  - 另有 `expand()` / `collapse()` / `toggle()` / `set_expanded()` / `set_texts()`，
    标题那一行就是 `panel.button`，想换字号颜色直接改
- 新增 `PathField` / `DropZone` / `pick_path` / `has_dnd`（`ctk_kit/files.py`）
  - `PathField` 是「输入框 + 浏览按钮」，`mode="file"` 选文件、`"folder"` 选文件夹，
    选中后路径覆盖输入框内容；`accept_drop=True` 时文件/文件夹也能直接拖到输入框上
  - `DropZone` 是一个拖放区，松手回调路径，`mode` 可过滤文件/文件夹
  - 拖放依赖可选的 `tkinterdnd2`：`pip install "ctk-kit[dnd]"`；没装时按钮选择照常可用，
    `DropZone` 显示成不可拖的提示
- 示例窗「输入」页拆成「输入」「选择」两页：输入页只留文本框、文件与文件夹选择、
  拖入取路径、下拉、大文本；分段、开关、勾选、单选、滑块、进度条移到「选择」页
- 新增「展开」页：`Collapsible` 的基础用法、两个状态文字、嵌进已有卡片、默认展开
- 示例窗的按钮、输入、选择、表格、图片、提示、菜单七页，每块功能下面都多了一个
  折叠的「查看实现」：点开是这段控件的示例代码和参数说明，代码用 14 号等宽字体，
  高度按行数算，收起时只占一行标题
- `COLOR_ACTIVE` / `COLOR_ACTIVE_HOVER` 整体提亮一档：选中态（分段、开关轨道、勾选、
  单选、滑块、进度条）在深浅两套底色上都更容易一眼看出
- 新增 `COLOR_BUTTON_KNOB` / `COLOR_BUTTON_KNOB_HOVER`：开关圆球与它的悬停色单独可调
- `radio_group` 的 `border_width_checked` 从 6 改成 4：CTk 选中态画的是「粗环 + 中间挖空」，
  挖空直径 = 宽度 - 2×该值，取 6 时只剩 6px，150% 缩放下被取整成方块

## 0.8.1 — 2026-10-31

- `slider()` 的把手从 16px 收到 12px（`height=12`、`border_width=4`，轨道仍是
  4px）：正圆把手的直径等于控件高度，16 的圆点压在 4px 细轨道上偏重，看着比
  轨道抢眼；高度降下来后 `border_width` 要一起改，否则轨道会被压没
- README 的 `slider` 签名说明和「已知的坑」补上 `轨道 = height - 2 * border_width`
  这条换算，换把手大小时不会把轨道压没

## 0.8.0 — 2026-10-29

- 输入类控件（`toolbar_entry`、`form_entry`、`TextArea`、`DropField`）统一成
  「填充底 + 1px 描边」：`COLOR_INPUT` 从 `("#ffffff" / "#1d1f26")` 调到
  `("#eef1f6" / "#22242c")`，描边用 `COLOR_BORDER_INPUT`（浅 `#b0b9c6` / 深 `#343a47`）
  - 1px 的已知代价：Tk 的 canvas 不做抗锯齿，150% 缩放下竖直边和圆角会落在半格上
    被吃掉，深色主题下往往只剩一条水平底边、白主题下则是圆角偏淡。换来的是比 2px
    细，也不会再出现 0.7.0 那种对角两段粗、两段断的样子
  - 聚焦不再改描边宽度和颜色，`border_width` 恒为 1：宽度一变 CTk 会重排内部
    grid，文字会左右跳；一圈主色描边在输入状态下也显得吵
  - `COLOR_BORDER_INPUT` 与 `BORDER_FOCUS_WIDTH` 都保留，前者就是这圈 1px 的颜色，
    后者给 `bind_focus_border()` 的默认宽度
- `bind_focus_border()` 变成可选工具，库里的控件不再默认调用它；签名扩展为
  `bind_focus_border(widget, *, source=None, idle_color=None, width=BORDER_FOCUS_WIDTH, on_width=None)`
  - `source`：焦点事件不会从子控件冒泡到父控件，复合控件要把绑定目标指向真正的
    输入控件（`DropField` 那种场景），否则外框永远不变色
  - `idle_color`：失焦时的描边颜色，默认取控件底色
  - 聚焦/失焦只换 `border_color`，不改 `border_width`，内容才不会左右跳
- `DropField` 删掉 `_inset_children()`：描边宽度固定 1，子控件内缩常量 1 即可，
  不再需要随焦点切换重排
- `TextArea(bg_color="transparent")` 不再抛 `ValueError`：CTk 的 `border_color`
  不接受透明色，现在沿父链取第一个实色当填充色
- 示例「输入」页的提示文案、README 的边框三档与「已知的坑」同步改写

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
- 新增令牌 `COLOR_ACTIVE` / `COLOR_ACTIVE_HOVER`（浅 `#1b94a7` / 深 `#3891a3`）：
  勾选、单选、开关、滑块、进度条、分段选中段的激活色都走它，比主色偏青一档、
  比输入框底色（深色 `#1d1f26`）明显亮；想换色只改这两个值
- 输入类控件的边框改用新令牌 `COLOR_BORDER_INPUT`（浅 `#aab2c0` / 深 `#3a4050`）：
  浅色下 `#e3e6eb` 贴在白卡片上几乎看不出边；而 1px 描边要想在圆角弧线上不被
  抗锯齿摊薄成虚线，边框色必须够深，所以单独给输入框一档更深的颜色。
  涉及 `toolbar_entry`、`form_entry`、`TextArea`、`DropField`
- 新增 `bind_focus_border()` 与令牌 `BORDER_FOCUS_WIDTH`（默认 2）：聚焦时边框临时
  加粗到 2px 并换 `COLOR_ACCENT`，失焦复原成 1px。1px 的聚焦色在圆角两端接不上，
  2px 才闭合成一个圈；四个输入类控件都绑了它
- `DropField` 的子控件内缩量保持 1（= `border_width`），聚焦加粗到 2 时同步内缩到 2，
  否则 `CTkEntry` 会压住外框描边，边框一段粗一段断
- `segmented()` 的选中段改用 `COLOR_ACTIVE`，与开关、勾选、单选、滑块、进度条
  的激活色统一：选中段文字自动切成 `COLOR_ACCENT_TEXT`、其余段回到 `COLOR_TEXT`
  （`CTkSegmentedButton` 只有一份 `text_color`，青底和浅底没法共用同一种字色，
  所以在 `set()` 与点击回调里分别重设）
- 移除令牌 `COLOR_SEG_SELECTED`：分段控件的选中态已经并入 `COLOR_ACCENT`
- 示例「输入」页补三节：勾选框、单选组、滑块与进度条（滑块拖动联动进度条）
- `TextArea` 的滚动条改用统一令牌：`scrollbar_button_color` / `scrollbar_button_hover_color`
  取 `COLOR_SCROLLBAR` / `COLOR_SCROLLBAR_HOVER`，并补上 `SCROLLBAR_WIDTH` 宽度与
  `SCROLLBAR_SPACING` 间距，和 `scrollable()` 的滚动条完全一致
- 新增 `style_scrollbar(bar)` 与令牌 `SCROLLBAR_SPACING`（默认 4）：`CTkScrollbar`
  的滑块宽度 = 宽度 − 2 × 间距，`CTkTextbox` 内部的滚动条间距是 0，所以同样的
  `width=12` 在文本区里会画成 12 宽的粗条、在滚动容器里才 4 宽。两处现在共用
  `style_scrollbar()`
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
