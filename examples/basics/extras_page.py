"""组件页：徽标、悬浮提示、分页条、页签、日期、区间滑块、搜索框、步骤条。

前半是 0.9.2 第一档的小件（``Badge`` / ``Tag`` / ``Tooltip`` / ``Pagination``），
后半是第二档：``Tabs`` 页签、``Calendar`` / ``DatePicker`` 日期、``RangeSlider``
区间、``SearchBox`` 搜索、``Steps`` / ``Wizard`` 步骤与向导。

和别的页面一样拆成「UI 类 + 事件类」：UI 类只建控件，事件类在构造时
``bind_events()``，每个卡片底部带一个「查看实现」折叠代码块。
"""

from __future__ import annotations

import datetime as dt
import tkinter as tk

from ctk_kit import (
    Avatar,
    Badge,
    Breadcrumb,
    Card,
    Carousel,
    CodePanel,
    ColorDialog,
    ColorPicker,
    CTkLabel,
    FormEntry,
    Frame,
    HintLabel,
    MenuBar,
    PageBase,
    PageHeader,
    Pagination,
    Popover,
    PrimaryButton,
    RangeSlider,
    Scrollable,
    SearchBox,
    Skeleton,
    SoftButton,
    Splitter,
    StatusBar,
    Steps,
    Tabs,
    Tag,
    Timeline,
    Tooltip,
    Wizard,
)

BADGE_CODE = '''from ctk_kit import Badge, Tag
Badge(card, "已同步", color="success")              # 淡绿底、绿字
Badge(card, "3", color="danger", variant="solid")   # 红底白字计数
Badge(card, dot=True, color="warning")               # 一个状态点
Tag(card, "草稿", variant="outline")                 # 描边标签'''

TOOLTIP_CODE = '''from ctk_kit import Tooltip

Tooltip(save_button, "保存当前草稿")
Tooltip(entry, lambda: f"当前长度 {len(entry.get())}", delay=300)'''

PAGINATION_CODE = '''from ctk_kit import Pagination

pager = Pagination(card, total=238, page_size=20, command=load_page)
pager.pack(fill="x")


def load_page(page):
    table.set_rows(fetch(page))'''

_BADGE_TEXT = ["点我换文字", "已同步", "3", "草稿", "待处理"]

TABS_CODE = '''from ctk_kit import Tabs

tabs = Tabs(card, values=["常规", "高级", "关于"], command=on_tab)
tabs.pack(fill="both", expand=True)


def on_tab(name):
    print("切到", name)'''

RANGE_SEARCH_CODE = '''from ctk_kit import RangeSlider, SearchBox

RangeSlider(card, from_=0, to=100, values=(20, 80),
            command=lambda lo, hi: print(lo, hi))
SearchBox(card, placeholder="搜索组件…", command=lambda text: print(text))'''

STEPS_CODE = '''from ctk_kit import PrimaryButton, Steps, Wizard

Steps(card, steps=["选择文件", "设置参数", "开始备份"], current=2)


def pick_page(parent, wizard):
    PrimaryButton(parent, "选好了", command=wizard.next).pack()


Wizard(card, steps=[("选择文件", pick_page), ("确认", confirm_page)])'''

AVATAR_CODE = '''from ctk_kit import Avatar, Breadcrumb, Timeline

Avatar(card, text="ZK", status="online")
Breadcrumb(card, items=["首页", ("文档", "docs"), "组件"],
           command=lambda value: print("点的是", value))
Timeline(card, items=[
    ("创建仓库", "第一次提交", "09:12"),
    {"title": "发布 0.9.2", "time": "进行中", "active": True},
])'''

SKELETON_SPLIT_CODE = '''from ctk_kit import CTkLabel, Skeleton, Splitter

Skeleton(card, width=220, height=14)          # start() / stop()
split = Splitter(card, height=140, initial=0.45, min_size=80)
split.pack(fill="x")
CTkLabel(split.first, text="左侧").pack(expand=True)
CTkLabel(split.second, text="右侧").pack(expand=True)'''

POPOVER_COLOR_CODE = '''from ctk_kit import ColorDialog, ColorPicker, FormEntry, Popover


def build_form(parent):
    FormEntry(parent, placeholder="关键词").pack(fill="x")


popover = Popover(button, content=build_form)   # 点按钮切换
ColorPicker(card, value="#2563eb", command=lambda color: print(color))

# 完整取色面板：阻塞到关闭，返回 #rrggbb，取消返回 None
picked = ColorDialog(card, value="#2563eb").show()'''

ACRYLIC_POPOVER_CODE = '''from ctk_kit import Popover

popover = Popover(button, acrylic=True, content=build_form)
# 窗口本身走系统 DWM 亚克力：整块直接透出背后内容，不截图、不用刷新
# 需要窗口拿到焦点才模糊，失焦会变成系统灰（Windows 自身行为）'''

STATUS_CAROUSEL_CODE = '''from ctk_kit import Carousel, StatusBar

StatusBar(card, text="就绪", right="v0.9.2")
Carousel(card, height=150, items=[("总览", "三层结构"), ("组件", "常用控件")])'''

MENUBAR_CODE = '''from ctk_kit import MenuBar

bar = MenuBar(card)
bar.add_menu("文件", [("新建", new_file), ("打开", open_file), "-",
                      ("退出", quit_app)])'''


def _wizard_name(parent: tk.Misc, _wizard: Wizard) -> None:
    """向导第一步：一个名称输入框。"""
    CTkLabel(parent, text="第一步：给备份任务起个名字。").pack(anchor="w")
    FormEntry(parent, placeholder="例如：每周备份").pack(fill="x", pady=(8, 0))


def _wizard_confirm(parent: tk.Misc, _wizard: Wizard) -> None:
    """向导第二步：一句确认。"""
    CTkLabel(parent, text="第二步：确认后开始。").pack(anchor="w")


class ExtrasPageUI(PageBase):
    """组件页 UI：徽标、悬浮提示、分页条三张卡片。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "组件")
        self.header.info.configure(
            text="徽标、提示、分页、页签、日期、区间、搜索、步骤、头像、分栏、浮层、轮播"
        )

        self.feedback = HintLabel(self, "翻页、点徽标、把鼠标停在按钮上试试")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_cards(area)

        self._badge_index = 0
        self._skeleton_on = True

    def _build_cards(self, area: tk.Misc) -> None:
        """按顺序建 12 张卡片；前 3 张同步，其余分帧。"""
        self.build_cards(
            area,
            [
                self._build_badges,
                self._build_tooltip,
                self._build_pagination,
                self._build_tabs,
                self._build_range_search,
                self._build_steps,
                self._build_avatar_path,
                self._build_skeleton_split,
                self._build_popover_color,
                self._build_status_carousel,
                self._build_menubar,
            ],
        )

    def _build_badges(self, area: tk.Misc) -> None:
        """三种形态、语义色、尺寸和状态点。"""
        box = Card(area, title="徽标与标签")
        box.pack(fill="x")

        HintLabel(
            box,
            "soft 是淡底、solid 是实底、outline 只描边；dot=True 只画圆点。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 6))
        for text, color in (
            ("已同步", "success"),
            ("进行中", "accent"),
            ("待处理", "warning"),
            ("失败", "danger"),
            ("草稿", "neutral"),
        ):
            Badge(row, text, color=color).pack(side="left", padx=(0, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 6))
        for text, color in (
            ("成功", "success"),
            ("主色", "accent"),
            ("警告", "warning"),
            ("危险", "danger"),
            ("中性", "neutral"),
        ):
            Badge(row, text, color=color, variant="solid").pack(
                side="left", padx=(0, 8)
            )

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        Tag(row, "描边标签", variant="outline").pack(side="left", padx=(0, 8))
        Badge(row, "sm", size="sm").pack(side="left", padx=(0, 8))
        for color in ("success", "warning", "danger"):
            Badge(row, dot=True, color=color).pack(side="left", padx=(0, 5))

        self.badge_demo = Badge(box, _BADGE_TEXT[0], color="accent")
        self.badge_demo.pack(anchor="w", padx=16, pady=(0, 12))
        self.badge_demo.configure(cursor="hand2")

        CodePanel(
            box,
            BADGE_CODE,
            "Tag 是 Badge 的别名；set_text() 可以在运行时换文字。",
        )

    def _build_tooltip(self, area: tk.Misc) -> None:
        """按钮和输入框挂悬停提示。"""
        box = Card(area, title="悬浮提示")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "默认停 0.5 秒弹出；文字可以传函数，每次悬停都重新算。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 10))
        self.save_button = PrimaryButton(row, "保存")
        self.save_button.pack(side="left")
        self.delay_button = SoftButton(row, "延迟 300ms")
        self.delay_button.pack(side="left", padx=(8, 0))
        self.tip_entry = FormEntry(row, placeholder="输入几个字，再悬停")
        self.tip_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.edge_button = SoftButton(row, "靠右边缘")
        self.edge_button.pack(side="right", padx=(8, 0))

        CodePanel(
            box,
            TOOLTIP_CODE,
            "提示窗口不抢焦点；贴着屏幕边缘时会自动翻到上方。",
        )

    def _build_pagination(self, area: tk.Misc) -> None:
        """页码条 + 代码改页 / 清空数据的对照。"""
        box = Card(area, title="分页条")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "238 条、每页 20 条，共 12 页；点页码只更新回显，不重新请求。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.pager = Pagination(box, total=238, page_size=20, show_total=True)
        self.pager.pack(fill="x", padx=16, pady=(0, 8))

        self.page_hint = HintLabel(box, "当前第 1 / 12 页")
        self.page_hint.pack(fill="x", padx=16, pady=(0, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        self.page5 = SoftButton(row, "代码跳到第 5 页")
        self.page5.pack(side="left")
        self.clear_btn = SoftButton(row, "清空数据")
        self.clear_btn.pack(side="left", padx=(8, 0))
        self.restore_btn = SoftButton(row, "恢复 238 条")
        self.restore_btn.pack(side="left", padx=(8, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 12))
        self.size10 = SoftButton(row, "每页 10 条")
        self.size10.pack(side="left")
        self.size20 = SoftButton(row, "每页 20 条")
        self.size20.pack(side="left", padx=(8, 0))
        self.size50 = SoftButton(row, "每页 50 条")
        self.size50.pack(side="left", padx=(8, 0))

        CodePanel(
            box,
            PAGINATION_CODE,
            "set_page() / set_total() 不触发 command；用户点按钮才回调。",
        )

    def _build_tabs(self, area: tk.Misc) -> None:
        """页签：三个标签，切换只更新回显。"""
        box = Card(area, title="页签")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "Tabs 封装 CTkTabview：底色、描边、选中色和分段控件一致。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.tabs = Tabs(box, values=["常规", "高级", "关于"])
        self.tabs.pack(fill="x", padx=16, pady=(0, 10))
        for name, text in (
            ("常规", "常用设置放在这一页。"),
            ("高级", "低频选项收进这里。"),
            ("关于", "ctk-kit 0.9.2"),
        ):
            CTkLabel(self.tabs.tab(name), text=text).pack(
                anchor="w", padx=16, pady=24
            )

        CodePanel(box, TABS_CODE, "tab(name) 拿到这一页的容器，往里放控件。")

    def _build_range_search(self, area: tk.Misc) -> None:
        """区间滑块 + 搜索框。"""
        box = Card(area, title="区间与搜索")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "区间滑块两个圆球不会交叉，松手才回调；搜索框输入防抖，回车立即触发。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 10))
        self.range = RangeSlider(row, from_=0, to=100, values=(20, 80))
        self.range.pack(side="left")
        self.range_hint = HintLabel(row, "20 – 80")
        self.range_hint.pack(side="left", padx=(12, 0))

        self.search = SearchBox(box, placeholder="搜索组件…")
        self.search.pack(fill="x", padx=16, pady=(0, 8))

        CodePanel(
            box, RANGE_SEARCH_CODE, "set() 不触发 command；搜索框清空也会回调。"
        )

    def _build_steps(self, area: tk.Misc) -> None:
        """步骤条 + 两步向导。"""
        box = Card(area, title="步骤与向导")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "Steps 展示进度，clickable=True 可点；Wizard 每步内容由构建函数现建。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.steps = Steps(
            box,
            steps=["选择文件", "设置参数", "开始备份"],
            current=2,
            clickable=True,
        )
        self.steps.pack(fill="x", padx=16, pady=(0, 10))

        self.wizard = Wizard(
            box,
            steps=[("填写名称", _wizard_name), ("确认", _wizard_confirm)],
        )
        self.wizard.pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(box, STEPS_CODE, "向导的完成回调拿到的就是 Wizard 本身。")

    def _build_avatar_path(self, area: tk.Misc) -> None:
        """头像、面包屑与时间线。"""
        box = Card(area, title="头像、面包屑与时间线")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "头像右下角的状态点表示在线状态；面包屑中间层级可点；时间线用圆点和竖线串起来。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 10))
        Avatar(row, text="ZK", size=44, status="online").pack(side="left")
        Avatar(row, text="李", size=44, color="success", status="busy").pack(
            side="left", padx=(10, 0)
        )
        Avatar(row, text="AI", size=44, color="warning", status="away").pack(
            side="left", padx=(10, 0)
        )
        Avatar(row, text="?", size=44, color="neutral", status="offline").pack(
            side="left", padx=(10, 0)
        )

        self.crumb = Breadcrumb(
            box,
            items=["首页", ("文档", "docs"), ("组件", "extras")],
            command=self._on_crumb,
        )
        self.crumb.pack(fill="x", padx=16, pady=(0, 10))

        self.timeline = Timeline(
            box,
            items=[
                ("创建仓库", "ctk-kit 第一次提交", "09:12"),
                ("补齐组件", "第一档、第二档完成", "11:40"),
                {
                    "title": "发布 0.9.2",
                    "description": "等待验收",
                    "time": "进行中",
                    "active": True,
                },
            ],
        )
        self.timeline.pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            AVATAR_CODE,
            "Avatar 的 image 传 CTkImage；Timeline 的 active 那条圆点用主色。",
        )

    def _build_skeleton_split(self, area: tk.Misc) -> None:
        """骨架屏 + 分栏。"""
        box = Card(area, title="骨架屏与分栏")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "加载中的占位可以用骨架屏；分栏拖动中间手柄，比例会回显到页面底部。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        self.skeleton1 = Skeleton(row, width=220, height=14)
        self.skeleton1.pack(side="left")
        self.skeleton2 = Skeleton(row, width=120, height=14)
        self.skeleton2.pack(side="left", padx=(10, 0))
        self.skeleton_btn = SoftButton(row, "暂停呼吸")
        self.skeleton_btn.pack(side="right")

        self.split = Splitter(
            box,
            height=140,
            initial=0.45,
            min_size=80,
            command=self._on_split,
        )
        self.split.pack(fill="x", padx=16, pady=(0, 10))
        CTkLabel(self.split.first, text="左侧面板").pack(expand=True)
        CTkLabel(self.split.second, text="右侧面板").pack(expand=True)

        CodePanel(
            box,
            SKELETON_SPLIT_CODE,
            "Skeleton 的呼吸动画可以 stop()；Splitter 夹住 min_size，拖不到边。",
        )

    def _build_popover_color(self, area: tk.Misc) -> None:
        """浮动卡片 + 颜色选择。"""
        box = Card(area, title="浮动卡片与颜色")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "Popover 点按钮弹出，点外面关闭；ColorPicker 选完色回显 hex；"
            "「取色面板…」打开完整色板，支持 RGB / HSV / HSL 与 hex 输入。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 10))
        self.filter_button = SoftButton(row, "筛选条件")
        self.filter_button.pack(side="left")
        self.acrylic_button = SoftButton(row, "系统玻璃")
        self.acrylic_button.pack(side="left", padx=(10, 0))
        self.color_picker = ColorPicker(row, value="#2563eb", command=self._on_color)
        self.color_picker.pack(side="left", padx=(12, 0))
        self.color_hint = HintLabel(row, "#2563eb")
        self.color_hint.pack(side="left", padx=(10, 0))

        dialog_row = Frame(box)
        dialog_row.pack(fill="x", padx=16, pady=(0, 10))
        self.color_dialog_button = SoftButton(dialog_row, "取色面板…")
        self.color_dialog_button.pack(side="left")
        self.color_dialog_hint = HintLabel(dialog_row, "#2563eb")
        self.color_dialog_hint.pack(side="left", padx=(10, 0))

        self.popover = Popover(
            self.filter_button,
            content=self._build_filter_popover,
            width=220,
        )
        self.acrylic_popover = Popover(
            self.acrylic_button,
            content=self._build_acrylic_popover,
            width=240,
            acrylic=True,
        )

        CodePanel(
            box,
            POPOVER_COLOR_CODE,
            "content 是一个「往父容器里建控件」的函数，弹层每次打开都会重跑。",
        )

        CodePanel(
            box,
            ACRYLIC_POPOVER_CODE,
            "acrylic=True 用系统亚克力：窗口本身是玻璃，透出的是真实背后内容；"
            "窗口失焦会变灰，这是 Windows 的行为。",
        )

    def _build_status_carousel(self, area: tk.Misc) -> None:
        """状态栏 + 轮播。"""
        box = Card(area, title="状态栏与轮播")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "状态栏左侧是状态点 + 文字；轮播可以点箭头或圆点切换。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.status = StatusBar(box, text="就绪", right="ctk-kit 0.9.2")
        self.status.pack(fill="x", padx=16, pady=(0, 8))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        for text, tone in (
            ("保存成功", "success"),
            ("注意", "warning"),
            ("出错", "danger"),
        ):
            SoftButton(
                row,
                text,
                command=lambda label=text, value=tone: self._set_tone(value, label),
            ).pack(side="left", padx=(0, 8))

        self.carousel = Carousel(
            box,
            height=150,
            items=[
                ("总览", "三层结构：tokens → theme → 组件"),
                ("组件", "常用控件都在，按功能分页展示"),
                ("文档", "每个组件都有参数表和示例"),
            ],
        )
        self.carousel.pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            STATUS_CAROUSEL_CODE,
            "状态栏适合放全局提示；轮播传 autoplay=3000 会自动切。",
        )

    def _build_menubar(self, area: tk.Misc) -> None:
        """菜单栏，下拉复用 ContextMenu。"""
        box = Card(area, title="菜单栏")
        box.pack(fill="x", pady=(12, 0))

        HintLabel(
            box,
            "菜单栏放在内容顶部，下拉的样式、分隔线和快捷键复用右键菜单。",
        ).pack(fill="x", padx=16, pady=(14, 8))

        self.menubar = MenuBar(box)
        self.menubar.pack(fill="x", padx=16, pady=(0, 10))

        CodePanel(
            box,
            MENUBAR_CODE,
            "add_menu() 返回菜单按钮；菜单项传 (文字, 回调)，用 \"-\" 加分隔线。",
        )


class ExtrasPage(ExtrasPageUI):
    """事件类：等卡片全部建完再自动调用 bind_events()。"""

    #: 前 3 张卡片同步建，其余分帧；启动遮罩会跳过这一页。
    cards_first = 3

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        # 卡片是分帧补建的，等队列清空后再统一绑事件
        self.when_built(self.bind_events)

    def bind_events(self) -> None:
        """挂提示、徽标点击和分页按钮。"""
        self.tips = [
            Tooltip(self.save_button, "保存当前草稿"),
            Tooltip(self.delay_button, "延迟 0.3 秒才弹出", delay=300),
            Tooltip(
                self.tip_entry,
                lambda: f"当前输入了 {len(self.tip_entry.get())} 个字符",
                delay=200,
            ),
            Tooltip(self.edge_button, "窗口贴边时提示会翻到左边或上方"),
        ]
        self.badge_demo.bind("<Button-1>", self._cycle_badge)
        self.pager.configure(command=self._on_page)
        self.page5.configure(command=self._jump_five)
        self.clear_btn.configure(command=self._clear)
        self.restore_btn.configure(command=self._restore)
        self.size10.configure(command=lambda: self._set_size(10))
        self.size20.configure(command=lambda: self._set_size(20))
        self.size50.configure(command=lambda: self._set_size(50))
        self.tabs.configure(command=self._on_tab)
        self.range.configure(command=self._on_range)
        self.search.configure(command=self._on_search)
        self.steps.configure(command=self._on_step)
        self.wizard.configure(command=self._on_finish)
        self.skeleton_btn.configure(command=self._toggle_skeleton)
        self.color_dialog_button.configure(command=self._on_color_dialog)
        self.menubar.add_menu(
            "文件",
            [
                ("新建", lambda: self._menu("新建")),
                ("打开", lambda: self._menu("打开")),
                "-",
                ("退出", lambda: self._menu("退出（示例不真退）")),
            ],
        )
        self.menubar.add_menu(
            "编辑",
            [
                ("复制", lambda: self._menu("复制")),
                ("粘贴", lambda: self._menu("粘贴")),
            ],
        )

    def _on_page(self, page: int) -> None:
        """用户点页码：更新页数和回显。"""
        self._sync_page_hint()
        self.feedback.configure(text=f"翻到第 {page} 页，这里可以接着请求数据")

    def _cycle_badge(self, _event: tk.Event) -> None:
        """点徽标换一段文字，演示 set_text。"""
        self._badge_index = (self._badge_index + 1) % len(_BADGE_TEXT)
        text = _BADGE_TEXT[self._badge_index]
        self.badge_demo.set_text(text)
        self.feedback.configure(text=f"徽标文字换成「{text}」")

    def _jump_five(self) -> None:
        """代码改页，不触发 command。"""
        self.pager.set_page(5)
        self._sync_page_hint()
        self.feedback.configure(text="set_page(5)：已跳到第 5 页，没有触发 command")

    def _clear(self) -> None:
        """清空数据，只剩第 1 页。"""
        self.pager.set_total(0)
        self._sync_page_hint()
        self.feedback.configure(text="set_total(0)：只剩第 1 页")

    def _restore(self) -> None:
        """恢复 238 条。"""
        self.pager.set_total(238)
        self._sync_page_hint()
        self.feedback.configure(text="set_total(238)：12 页回来了")

    def _set_size(self, size: int) -> None:
        """改每页条数，页数跟着变。"""
        self.pager.set_page_size(size)
        self._sync_page_hint()
        self.feedback.configure(
            text=f"set_page_size({size})：238 条变成 {self.pager.pages} 页"
        )

    def _sync_page_hint(self) -> None:
        """把页码回显同步到分页条。"""
        self.page_hint.configure(
            text=f"当前第 {self.pager.page} / {self.pager.pages} 页"
        )

    def _on_tab(self, name: str) -> None:
        """切换页签。"""
        self.feedback.configure(text=f"切到「{name}」页签")

    def _on_range(self, low: float, high: float) -> None:
        """区间滑块松手。"""
        self.range_hint.configure(text=f"{low:g} – {high:g}")
        self.feedback.configure(text=f"区间 {low:g} – {high:g}，松手才回调")

    def _on_search(self, text: str) -> None:
        """搜索框防抖结束 / 回车 / 清空。"""
        if text:
            self.feedback.configure(text=f"搜索「{text}」")
        else:
            self.feedback.configure(text="搜索框清空了")

    def _on_step(self, step: int) -> None:
        """点步骤条上的某一步。"""
        self.feedback.configure(text=f"步骤条点到第 {step} 步")

    def _on_finish(self, _wizard: Wizard) -> None:
        """向导最后一页点了完成。"""
        self.feedback.configure(text="向导完成，可以开始备份了")

    def _on_crumb(self, value: str) -> None:
        """点了面包屑的中间层级。"""
        self.feedback.configure(text=f"面包屑点到 {value}")

    def _on_color(self, color: str) -> None:
        """色板里选了一个颜色。"""
        self.color_hint.configure(text=color)
        self.feedback.configure(text=f"选中颜色 {color}")

    def _on_color_dialog(self) -> None:
        """打开完整取色面板，选完回显。"""
        color = ColorDialog(
            self,
            value=self.color_picker.get(),
            title="选择颜色",
        ).show()
        if color:
            self.color_dialog_hint.configure(text=color)
            self.feedback.configure(text=f"取色面板选中 {color}")

    def _on_split(self, ratio: float) -> None:
        """拖动分栏手柄松开。"""
        self.feedback.configure(text=f"分栏比例 {ratio:.0%}")

    def _toggle_skeleton(self) -> None:
        """暂停 / 继续骨架屏动画。"""
        if self._skeleton_on:
            self.skeleton1.stop()
            self.skeleton2.stop()
            self.skeleton_btn.configure(text="继续呼吸")
            self._skeleton_on = False
            self.feedback.configure(text="骨架屏动画停住")
        else:
            self.skeleton1.start()
            self.skeleton2.start()
            self.skeleton_btn.configure(text="暂停呼吸")
            self._skeleton_on = True
            self.feedback.configure(text="骨架屏继续呼吸")

    def _set_tone(self, tone: str, label: str) -> None:
        """切状态栏的文字和圆点颜色。"""
        self.status.set_text(label, tone=tone)
        self.feedback.configure(text=f"状态栏：{label}")

    def _menu(self, label: str) -> None:
        """点菜单项。"""
        self.feedback.configure(text=f"菜单项：{label}")

    def _build_filter_popover(self, parent: tk.Misc) -> None:
        """Popover 的内容：一个输入框 + 应用按钮。"""
        CTkLabel(parent, text="关键词").pack(anchor="w")
        self.filter_entry = FormEntry(parent, placeholder="输入后点应用")
        self.filter_entry.pack(fill="x", pady=(6, 10))
        PrimaryButton(parent, "应用", command=self._apply_filter).pack(anchor="e")

    def _apply_filter(self) -> None:
        """点弹层里的应用：回显并收起。"""
        text = self.filter_entry.get().strip()
        self.feedback.configure(text=f"筛选：{text or '（空）'}")
        self.popover.hide()

    def _build_acrylic_popover(self, parent: tk.Misc) -> None:
        """系统玻璃弹层的内容。"""
        CTkLabel(parent, text="系统玻璃").pack(anchor="w")
        HintLabel(
            parent,
            "整块直接透出背后内容；窗口拿到焦点才模糊。",
        ).pack(fill="x", pady=(6, 10))
        PrimaryButton(parent, "知道了", command=self._close_acrylic).pack(anchor="e")

    def _close_acrylic(self) -> None:
        self.acrylic_popover.hide()
        self.feedback.configure(text="系统玻璃弹层：已收起")
