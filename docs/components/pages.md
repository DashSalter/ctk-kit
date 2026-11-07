# 页面与导航

## 作用

ctk-kit 用三个类搭多页应用：

- `PageBase` —— 每一页的基类。负责把一页拆成若干张卡片，并让卡片**分帧构建**
  （先出页头和前几张，其余在后续帧里补），这样切页时窗口不会僵住一两秒。
- `PageRebuilder` —— 管理一组页面容器的生命周期：第一次切到某页才建、
  建好的页留在栈里、切外观时整页重建、拖窗口时丢弃看不见的页。
- `SidebarNav` —— 左侧导航栏 + 右侧页面容器。点导航按钮切页，并负责
  当前页的高亮、相邻页的预建。

大多数情况下只用到 `PageBase` 和 `SidebarNav`；`PageRebuilder` 通常由
`SidebarNav` 内部创建，需要自己管页面时才直接用它。

## 类型

| 类型 | 作用 | 用在哪 |
| --- | --- | --- |
| `PageBase` | 单页基类，提供分帧构建 | 每个页面的类都继承它 |
| `PageRebuilder` | 页面容器的建 / 显示 / 重建 / 丢弃 | 自己搭页面容器时 |
| `SidebarNav` | 导航栏 + 页面容器 | 主窗口的骨架 |

## 参数

### PageBase

`PageBase(master)` 只有一个参数，但有一个**类属性**要留意：

| 项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `cards_first` | `int` | `1` | 类属性：切到这一页时同步建几张卡，其余进分帧队列 |

```python
class SettingsPage(ctk.PageBase):
    cards_first = 2        # 这页的页头 + 前两张卡同步建，剩下的分帧
```

`cards_first` 的取值：

| 值 | 行为 | 什么时候用 |
| --- | --- | --- |
| `0` | 整页同步建 | 卡片很少（1–2 张）的页面 |
| `1`（默认） | 只同步建第一张 | 大多数页面 |
| `2`–`3` | 同步建更多 | 首屏内容重要的页面（如首页） |

### PageRebuilder

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `host` | `tk.Misc` | 必填 | 页面容器（所有页面都 `place` 在它上面） |
| `factory` | `Callable[[str], tk.Misc]` | 必填 | 按页名建一个页面容器 |
| `pages` | `Sequence[str]` | 必填 | 页面名，按顺序 |
| `on_hide` | `Callable[[tk.Misc], None]` | `None` | 某页被切走时的钩子 |
| `first_of` | `Callable[[str], int]` | `None` | 传入页名返回 `cards_first`，启动预建时用它判断哪些页可以跳过 |

```python
rebuilder = ctk.PageRebuilder(
    host=body,
    factory=lambda name: pages[name](body),
    pages=["总览", "设置"],
    on_hide=lambda page: page.on_hide(),
)
```

### SidebarNav

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父容器 |
| `title` | `str` | 必填 | 侧边栏顶部的标题 |
| `pages` | `Mapping[str, PageBuilder]` | 必填 | 页名 → 建页函数 |
| `subtitle` | `str` | `""` | 标题下面的副标题 |
| `logo` | `bool \| str` | `True` | `True` 用库自带 logo，也可传图片路径 |
| `logo_size` | `int` | `32` | logo 边长 |
| `logo_dim` | `float \| None` | `None` | logo 压暗程度 |
| `width` | `int \| float` | `200` | 侧边栏宽度 |
| `padding` | `(int, int)` | `(16, 16)` | 内容区的左右 / 上下内边距 |
| `bottom_pages` | `Mapping[str, PageBuilder]` | `None` | 放在底部的页面（个人中心、设置） |
| `hidden_pages` | `Mapping[str, PageBuilder]` | `None` | 注册但不在导航里显示的页面 |
| `footer` | `Callable[[CTkFrame], None]` | `None` | 底部自定义区域 |
| `bottom_width` | `int` | `176` | 底部按钮宽度 |
| `initial` | `str \| None` | `None` | 启动时显示哪一页，默认第一页 |
| `divider` | `bool` | `True` | 侧边栏右侧有没有分隔线 |
| `on_change` | `Callable[[str], None]` | `None` | 切页回调，参数是页名 |
| `on_hide` | `Callable[[tk.Misc], None]` | `None` | 某页被切走时调用 |

```python
nav = ctk.SidebarNav(
    app,
    title="ctk-kit",
    subtitle="v0.12.0 · 示例",
    pages={"总览": OverviewPage, "设置": SettingsPage},
    bottom_pages={"关于": AboutPage},
    initial="总览",
    width=200,
    on_change=lambda name: print("切到", name),
)
```

`pages` 的值可以是 `PageBase` 子类，也可以是 `lambda master: PageBase 实例`。

## 方法

### PageBase：分帧构建

| 方法 | 说明 |
| --- | --- |
| `build_cards(area, [fn1, fn2, ...])` | 把一页的卡片交给分帧队列；前 `cards_first` 张同步建 |
| `build_later(fn)` | 把任意构建任务排到后续帧（不在卡片列表里的零散控件用） |
| `when_built(callback)` | 所有排队任务都建完后调用一次；可注册多个 |
| `on_show()` | 页面被切到前台时调用，覆写它 |
| `on_hide()` | 页面被切走、或按新外观重建销毁前调用，覆写它 |
| `bind_events()` | 建议在这里集中写事件绑定 |

```python
class InputPage(ctk.PageBase):
    cards_first = 2

    def __init__(self, master):
        super().__init__(master)
        ctk.PageHeader(self, "输入")
        area = ctk.Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self.build_cards(area, [self._build_entry, self._build_text])

        # 建完再读卡片里的控件，不能建之前读
        self.when_built(self._sync_counter)

    def _build_entry(self, area):
        card = ctk.Card(area, title="文本框")
        card.pack(fill="x")
        self.entry = ctk.CTkEntry(card.row(1), width=220)
        self.entry.pack(side="left", padx=16, pady=(0, 12))

    def _sync_counter(self):
        print("页面建完了", self.entry.get())
```

!!! tip "为什么要分帧"
    一页有十几张卡时，同步建完要 0.6–1.7 秒，这段时间窗口完全不动。
    `build_cards` 把每张卡排进队列，每帧最多花 12 ms，切页时先出第一屏，
    剩下的在后续帧里补——总耗时接近，但**首帧从一秒多降到几十毫秒**。

### PageRebuilder

| 方法 / 属性 | 说明 |
| --- | --- |
| `show(name)` | 显示某一页；没建过就建，配色过期就重建 |
| `frame(name)` | 取某页容器，没建就建（但不显示） |
| `prewarm([names])` | 预建页面，不显示；下次切过去只需 `lift` |
| `cancel_prewarm()` | 放弃排队的预建（用户已经切页，别抢主线程） |
| `drop_hidden()` | 销毁除当前页外的所有页面，返回销毁页数 |
| `build_all(progress=None, names=None)` | 启动时批量预建，可逐页汇报进度 |
| `rebuild(name)` | 按当前外观重建一页（先建新的挂上，再销毁旧的） |
| `mark_stale()` | 把所有页标成「配色过期」，下次切过去时重建 |
| `switch(mode, defer=False)` | 切外观：更新配色后重建当前页 |
| `add_page(name)` / `remove_page(name)` | 动态增删页面 |
| `pages` / `current` / `frames` / `stale` | 页名列表 / 当前页名 / 已建容器 / 过期页集合 |
| `hidden_roots()` | 已经建好、但当前没在显示的页面容器 |

```python
rebuilder.prewarm(["组件", "表格"])      # 提前建好，切过去只要 20 ms
rebuilder.drop_hidden()                  # 拖窗户时先丢掉看不见的页
print(rebuilder.pages, rebuilder.current)
```

### SidebarNav

| 方法 / 属性 | 说明 |
| --- | --- |
| `show(name)` | 显示某一页并高亮对应的导航按钮 |
| `page(name)` | 取某页容器（没建就先建） |
| `add_page(name, builder)` / `remove_page(name)` | 动态增删一页 |
| `current` | 当前页名 |
| `names` | 全部页名，按当前顺序 |
| `frames` | 页名 → 已建容器 |
| `set_appearance_mode(mode)` | 切换外观：外壳原地换色，只重建当前页 |
| `toggle_appearance()` | 深浅色切换 |
| `apply_theme()` | 只刷外壳颜色，不重建页面 |

```python
nav.show("设置")
print(nav.current, nav.names)
nav.toggle_appearance()
```

### 通用方法

`PageBase`、`SidebarNav` 都是 Tk 容器，`pack` / `grid` / `place` 照常可用；
`PageBase` 内的控件同样继承 `set_text` / `on_click` / `enable` / `disable` 等方法。

## 完整示例

```python
import ctk_kit as ctk


class HomePage(ctk.PageBase):
    cards_first = 2

    def __init__(self, master):
        super().__init__(master)
        ctk.PageHeader(self, "首页")

        area = ctk.Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))
        self.build_cards(area, [self._build_a, self._build_b, self._build_c])

    def _build_a(self, area):
        card = ctk.Card(area, title="欢迎")
        card.pack(fill="x")
        ctk.HintLabel(card, "点左侧导航切换页面。").pack(
            fill="x", padx=16, pady=(10, 14)
        )

    def _build_b(self, area):
        card = ctk.Card(area, title="操作")
        card.pack(fill="x", pady=(12, 0))
        ctk.PrimaryButton(card.row(1), "打印一条").pack(
            side="left", padx=16, pady=(0, 14)
        )

    def _build_c(self, area):
        card = ctk.Card(area, title="说明")
        card.pack(fill="x", pady=(12, 0))
        ctk.HintLabel(card, "这张卡在后面的帧里才建出来。").pack(
            fill="x", padx=16, pady=(10, 14)
        )


class SettingsPage(ctk.PageBase):
    def __init__(self, master):
        super().__init__(master)
        ctk.PageHeader(self, "设置")
        card = ctk.Card(self, title="外观")
        card.pack(fill="x", pady=(14, 0))
        ctk.SecondaryButton(
            card.row(1), "切换深浅色", command=lambda: app.toggle_appearance()
        ).pack(side="left", padx=16, pady=(0, 14))


app = ctk.App(title="多页示例", size=(900, 620))

nav = ctk.SidebarNav(
    app,
    title="ctk-kit",
    subtitle="多页示例",
    pages={"首页": HomePage, "设置": SettingsPage},
    initial="首页",
)

app.mainloop()
```

## 换色

切外观时不要重建整棵树：`SidebarNav.set_appearance_mode()` 会原地刷新外壳，
并通过 `PageRebuilder.switch()` 只重建**当前页**，其他页面标成过期、等切过去再建。

```python
app.toggle_appearance()          # 推荐入口
nav.toggle_appearance()          # 等价写法

from ctk_kit import theming
theming.apply_palette({"COLOR_ACCENT": "#f97316"})   # 只换色，不切深浅
```

被标成过期的页面在 `show()` 时会自动补刷新，不会出现「切过去还是旧配色」。
