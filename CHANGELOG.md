# 更新记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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
