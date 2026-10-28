# 更新记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## 未发布

- 新增 `TextArea`：带占位符、字数统计与只读模式的多行文本区
- 示例输入页增加大文本演示（普通备注 + 只读日志）
- 示例底栏改为「设置」入口，新增设置页：浅色 / 深色切换、版本与运行环境
- 下拉面板改用 DWM 圆角（Win11）、`SetWindowRgn` 兜底，面板边框沿窗口弧线走
- 滚动容器滚轮加快：`CTkScrollableFrame` 每格 60px，`LazyList` 每格 60px
- 测试：新增 `tests/test_text.py`，设置页与下拉圆角补用例

## 0.1.0 — 2026-10-28

首个版本。

- 设计令牌：24 组深浅色颜色、7 档字体、圆角与间距常量
- 组件：主/次/危险按钮、卡片小按钮、输入框、分段选择、开关、自绘下拉
- 布局：页头、节标题、卡片、分隔线、字段标签、说明文字、空态、滚动容器
- `LazyList`：分批渲染的懒加载列表，卡片工厂可替换
- 示例：`examples/showcase.py` 九页全组件展示（运行 `python examples/showcase.py`）
- 测试：pytest 套件，覆盖令牌、主题、按钮、输入、下拉、布局、懒加载列表与示例页
