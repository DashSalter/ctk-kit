# ctk-kit

[![CI](https://github.com/DashSalter/ctk-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/DashSalter/ctk-kit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/ctk-kit.svg)](https://pypi.org/project/ctk-kit/)
[![Python](https://img.shields.io/pypi/pyversions/ctk-kit.svg)](https://pypi.org/project/ctk-kit/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

面向 [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) 的轻量界面基件：
一套深浅色设计令牌、一批常用控件，以及一个会自动分页的懒加载列表。
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

展示程序有九个页面：总览、基件、按钮、输入、布局、列表、主题、表单、设置，把每个公开构建都用一遍。
基件页把 24 个色值连同浅/深两套十六进制值一起列出来，换主题时对着它调最直观。

## 三层结构

| 层 | 模块 | 内容 |
| --- | --- | --- |
| 令牌 | `tokens` | `COLOR_*`（全部为浅/深二元组）、`FONT_*`、`RADIUS_*`、`SPACE_*` |
| 主题 | `theme` | `is_dark()`、`color_of()`、`apply_appearance()`、`repaint_native()` |
| 组件 | `buttons` / `inputs` / `dropdown` / `layout` / `scroll_list` | 见下 |

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
- `switch(master, command=None, *, width=44)`

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

## 目录

```
ctk_kit/
├─ tokens.py       设计令牌
├─ theme.py        取色 / 外观切换 / 原生控件重绘
├─ buttons.py      按钮
├─ inputs.py       输入框 / 分段选择 / 开关
├─ dropdown.py     自绘下拉
├─ layout.py       页头、卡片、分隔线、空态、滚动容器
├─ scroll_list.py  懒加载列表
├─ text.py         多行文本区
└─ showcase.py     全组件展示（随包发布，`ctk-kit-showcase`）

examples/
└─ showcase.py     仓库里的快捷入口（转发到 ctk_kit.showcase:main）
```

## 测试

```bash
pip install -e ".[test]"
pytest
```

测试跑在真实 Tk 窗口里（窗口全透明，不会在屏幕上闪），覆盖令牌、主题、按钮、输入框、
下拉、布局、懒加载列表、大文本区，以及 `ctk_kit/showcase.py` 的九个示例页；没有图形环境时相关用例自动 skip。

CI 在 GitHub Actions 上跑 Python 3.8 – 3.14 全矩阵（`.github/workflows/ci.yml`），
无头环境下用 Xvfb 提供虚拟屏幕；`CI` 环境变量存在时如果建不出窗口会直接失败，而不是静默跳过。

## 发布

版本号只写在 `pyproject.toml` 的 `version` 字段里，发布流程全自动：

1. 改 `pyproject.toml` 的 `version`（例如 `0.2.0` → `0.2.1`），同步更新 `CHANGELOG.md`；
2. 提交并 `git push` 到 Gitee；
3. 镜像自动同步到 GitHub，Actions 跑完测试与构建后，会比较 PyPI 上的最新版本——
   本地版本更新才发布，同版本重推不会报错。

首次发布前需要在 PyPI 的 *Publishing* 页面给 GitHub 仓库
`DashSalter/ctk-kit` 添加 Trusted Publisher（workflow 文件名 `ci.yml`，环境留空），
之后由 `pypa/gh-action-pypi-publish` 凭 OIDC 换短期令牌上传，仓库里不需要存密码。

## 已知的坑

这些都是踩过的，记下来省得再踩：

- `CTkLabel` 不支持 `border_width` / `border_color`，想加边框只能裹一层 `CTkFrame`。
- `CTkSegmentedButton` 同样不接受 `border_*`，传了会抛 `ValueError`。
- `CTkScrollbar.set()` 内部会调 `update_idletasks()`，而 `update_idletasks` 会立刻执行
  `after_idle` 排的回调——用 `after_idle` 排分批渲染会在这个调用里递归建卡，改用 `after(1, ...)`。
- 滚动区域变化后，Tk 会回放一次 `yscrollcommand(0, 1)`。判断「滚到底」不能信回调参数，
  要读 `canvas.yview()`。
- customtkinter 接管了 `tk.Frame.configure`，给原生控件改背景色得走
  `widget.tk.call(widget._w, "configure", "-background", bg)`，否则会碰到已销毁的子控件。

## License

MIT
