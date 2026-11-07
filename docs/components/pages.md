# 页面与侧边栏

## 作用

把程序拆成多个页面：一个侧边栏负责切换，一个重建器负责建页、缓存和销毁，
页面基类负责「先出首屏、剩下的分帧补」。

## PageBase

### 作用

每个页面的基类。把要建的卡片写成一个列表交给 `build_cards`，首屏会同步建前
`cards_first` 张，剩下的分帧补上，切页不会卡住整个窗口。

### 类属性

| 属性 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `cards_first` | `int` | `1` | 首屏同步建几张卡；`0` 表示整页同步建 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `build_cards(area, builders)` | 交给分帧队列去建这组卡片 |
| `build_later(builder)` | 单独把一个构建函数排到后面 |
| `when_built(callback)` | 全部建完后回调（分帧期间不能同步读控件） |
| `on_show()` / `on_hide()` | 页面显示 / 隐藏时的钩子 |

### 示例

```python
class SettingsPage(PageBase):
    cards_first = 2

    def __init__(self, area):
        super().__init__(area)
        self.build_cards(area, [self._build_account, self._build_theme,
                                self._build_about])
        self.when_built(self._fill_values)

    def _build_account(self, area):
        card = Card(area, title="账号")
        card.pack(fill="x", padx=24, pady=(0, 12))

    def _build_theme(self, area):
        Card(area, title="外观").pack(fill="x", padx=24, pady=(0, 12))

    def _build_about(self, area):
        Card(area, title="关于").pack(fill="x", padx=24)

    def _fill_values(self):
        pass        # 这时所有卡片都已经建好
```

## PageRebuilder

### 作用

管理一组页面的创建、显示、重建和回收；`SidebarNav` 内部用它。

### 方法

| 方法 | 说明 |
| --- | --- |
| `show(name)` | 显示某个页面（没建过就建） |
| `frame(name)` | 取某个页面的容器 |
| `build_all(progress=None, names=None)` | 批量预建；`names` 为 `None` 时建全部 |
| `rebuild(name)` | 重建某个页面 |
| `mark_stale()` | 把所有页面标记为需要重建 |
| `prewarm(names)` | 后台按顺序预建这些页面 |
| `cancel_prewarm()` | 取消正在进行的预建 |
| `drop_hidden()` | 销毁所有不在显示的页面（省内存） |
| `add_page(name, factory)` / `remove_page(name)` | 增删页面 |

### 示例

```python
host = Frame(app)          # 页面挂载的容器
def page_factory(name):
    return PageBase(host)  # 实际项目里返回自己的页面类

rebuilder = PageRebuilder(host, page_factory, ["总览", "设置"])
rebuilder.show("总览")
rebuilder.prewarm(["设置"])
```

## SidebarNav

### 作用

左侧导航栏：一列页面按钮，点击切换右侧内容；可以放页脚（头像、设置入口）。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `master` | `tk.Misc` | 必填 | 父窗口 |
| `title` | `str` | 必填 | 侧边栏顶部标题 |
| `pages` | `Mapping[str, Callable]` | 必填 | 页面名 → 构建函数 |
| `subtitle` | `str` | `""` | 标题下面那行小字（一般放版本号） |
| `logo` | `bool` / `str` | `True` | 是否显示图标；传字符串则用该图片 |
| `logo_size` | `int` | `32` | 图标边长 |
| `width` | `int` | `200` | 侧边栏宽度 |
| `padding` | `(int, int)` | `(16, 16)` | 内容区内边距 |
| `bottom_pages` | `Mapping[str, Callable]` | `None` | 固定在底部的页面 |
| `hidden_pages` | `Mapping[str, Callable]` | `None` | 参与路由但不显示在列表里 |
| `footer` | `Callable[[容器], None]` | `None` | 底部自定义内容 |
| `initial` | `str` | 第一个页面 | 初始显示哪一页 |
| `divider` | `bool` | `True` | 右侧是否画一条分隔线 |
| `on_change` | `Callable[[str], None]` | `None` | 换页回调 |
| `on_hide` | `Callable[[容器], None]` | `None` | 页面被隐藏时回调 |

### 方法

| 方法 | 说明 |
| --- | --- |
| `show(name)` | 切到某个页面 |
| `page(name)` | 取某个页面对象 |
| `current` | 当前页面名 |

### 示例

```python
class OverviewPage(PageBase):
    title = "总览"

class SettingsPage(PageBase):
    title = "设置"

nav = SidebarNav(
    app,
    title="ctk-kit",
    pages={"总览": OverviewPage, "设置": SettingsPage},
    subtitle="v0.12.0",
    width=200,
    initial="总览",
    divider=True,
)

nav.show("设置")
print(nav.current)
```
