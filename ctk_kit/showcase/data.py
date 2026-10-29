"""示例数据：页面清单、组件索引，以及各页共用的假数据。

这些内容不依赖任何控件，只被 ``pages`` 下的页面模块读取。
"""

from __future__ import annotations

from ctk_kit import tokens as T

APP_TITLE = "ctk-kit 全组件展示"

PAGES = ("总览", "基件", "按钮", "输入", "布局", "提示", "列表", "主题", "表单", "设置")

SAMPLE_ITEMS = [
    {
        "id": f"item-{index}",
        "title": f"示例条目 {index:02d}",
        "subtitle": "一行摘要，放网址、账号或关键词",
        "tag": ["账号", "恢复码", "密钥"][index % 3],
    }
    for index in range(120)
]

COLOR_TOKENS = sorted(name for name in vars(T) if name.startswith("COLOR_"))

# 按字号从大到小排，演示时一眼能看出层级
FONT_TOKENS = [
    ("FONT_TITLE", T.FONT_TITLE),
    ("FONT_CARD_TITLE", T.FONT_CARD_TITLE),
    ("FONT_SECTION", T.FONT_SECTION),
    ("FONT_BODY", T.FONT_BODY),
    ("FONT_SMALL", T.FONT_SMALL),
    ("FONT_TINY", T.FONT_TINY),
    ("FONT_BADGE", T.FONT_BADGE),
]

RADIUS_TOKENS = [
    ("RADIUS_SMALL", T.RADIUS_SMALL),
    ("RADIUS_MEDIUM", T.RADIUS_MEDIUM),
    ("RADIUS_LARGE", T.RADIUS_LARGE),
    ("RADIUS_PILL", T.RADIUS_PILL),
]

SPACE_TOKENS = [
    ("SPACE_XS", T.SPACE_XS),
    ("SPACE_SM", T.SPACE_SM),
    ("SPACE_MD", T.SPACE_MD),
    ("SPACE_LG", T.SPACE_LG),
    ("SPACE_XL", T.SPACE_XL),
]

# 组件索引：(页面名, 一句话说明)
INDEX = [
    ("基件", "字体、状态色、色板、圆角、间距、滚动条宽度"),
    ("按钮", "主按钮 / 次要按钮 / 危险按钮 / 描边 / 微型按钮 / 禁用态"),
    ("输入", "工具栏框、表单框、密码、分段选择、开关、下拉框、大文本区"),
    ("布局", "页头、分区标题、卡片、分隔线、滚动容器、空态、字段标签"),
    ("提示", "窗口顶部/底部的浮层提示：四种级别、两种形态、堆叠与常驻"),
    ("列表", "LazyList 懒加载、关键词与分类筛选、刷新、清空、空态"),
    ("主题", "深浅色切换、color_of 取色、repaint_native 重绘原生控件"),
    ("表单", "把输入、下拉、分段、开关与底部动作拼成一张表单"),
    ("设置", "外观模式切换（浅色 / 深色）、版本与运行环境"),
]
