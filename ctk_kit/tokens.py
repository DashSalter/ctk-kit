"""设计令牌：颜色、字体、圆角与间距。

界面只有一套「毛玻璃」配色：每个颜色令牌就是一个 ``#RRGGBB`` 字符串，
CustomTkinter 控件、原生 tk 控件、canvas 拿到的都是同一个值，不存在
「浅色一套、深色一套」的切换。

想按外观个别区分时仍然可以传 ``(浅色, 深色)`` 二元组（CTk 支持），但库内
的令牌本身都是单值；需要自己取值的场合（原生 tk 控件、canvas、滚动条）直接
用令牌即可，不必再调用 ``theme.color_of()``。

本模块只有常量，没有运行时依赖；导入它是零成本的。
"""

from __future__ import annotations

from typing import Dict, Tuple, Union

# 颜色令牌：单个 ``#RRGGBB``。允许传二元组是为了兼容调用方自己的配色，
# 库内定义的令牌一律是字符串。
ColorToken = str
ColorPair = Union[str, Tuple[str, str]]

# 字体规格：``(字族, 字号)`` 或 ``(字族, 字号, "bold")``，可直接传给 tk 控件。
FontSpec = Union[Tuple[str, int], Tuple[str, int, str]]

# ---------------------------------------------------------------- 字体
# 微软雅黑在 Windows 上最稳；换平台时只改这一行。
FONT_NAME = "微软雅黑"

FONT_TITLE: FontSpec = (FONT_NAME, 20, "bold")  # 页面标题
FONT_CARD_TITLE: FontSpec = (FONT_NAME, 15, "bold")  # 卡片标题
FONT_SECTION: FontSpec = (FONT_NAME, 14, "bold")  # 设置页分区标题
FONT_BODY: FontSpec = (FONT_NAME, 13)  # 正文、输入框
FONT_TABLE: FontSpec = (FONT_NAME, 13)  # 表格正文与表头
FONT_TABLE_HEAD: FontSpec = (FONT_NAME, 13, "bold")  # 表格表头
FONT_SMALL: FontSpec = (FONT_NAME, 12)  # 次要说明、按钮
FONT_TINY: FontSpec = (FONT_NAME, 11)  # 时间戳、徽标旁边的信息
FONT_BADGE: FontSpec = (FONT_NAME, 9)  # 分类徽标

# ---------------------------------------------------------------- 颜色
# 取值都是「毛玻璃底上实际显示的那一个」：原来三元组的第三项优先，
# 没有第三项的沿用深色值。改这一组就等于改整套外观。
COLOR_BG: ColorToken = "#0e0f12"  # 窗口底色
COLOR_SIDE: ColorToken = "#131418"  # 侧边栏 / 状态栏
# 标题栏：刻意比内容区和侧边栏都亮一档，看出「顶栏」这一层
COLOR_TITLEBAR: ColorToken = "#1c1e25"
COLOR_CARD: ColorToken = "#181920"  # 卡片
# 输入类控件（输入框、下拉框、文本区）的底色。描边只有 1px，边界主要靠这层底色
# 和卡片拉开层次。
COLOR_INPUT: ColorToken = "#22242c"
COLOR_BORDER: ColorToken = "#262831"  # 细边框：卡片、分割线
COLOR_BORDER_STRONG: ColorToken = "#3b3e4a"  # 轨道、未选中描边
# 输入类控件的 1px 描边：比 COLOR_BORDER 深一档，卡片上才看得出边界。
COLOR_BORDER_INPUT: ColorToken = "#343a47"

COLOR_TEXT: ColorToken = "#f1f3f6"
# 比 COLOR_TEXT 柔和一档：表格正文、密集列表用
COLOR_TEXT_SOFT: ColorToken = "#B1B6BD"
COLOR_MUTED: ColorToken = "#98a0ab"
COLOR_FAINT: ColorToken = "#6b7280"

COLOR_ACCENT: ColorToken = "#4c4b98"  # 主色：主按钮、链接
COLOR_ACCENT_HOVER: ColorToken = "#4B4D6B"
COLOR_ACCENT_TEXT: ColorToken = "#ffffff"

# 控件「激活态」专用色：勾选、单选、开关拨到右边、滑块已填充、进度条、分段选中段。
# 透明底上的青色发灰，这里用更沉的蓝才压得住。
COLOR_ACTIVE: ColorToken = "#606269"
COLOR_ACTIVE_HOVER: ColorToken = "#494A4F"
# 「进度条前景色」：从二级颜色复制出来的一份，单独调不影响别处
COLOR_PROGRESS: ColorToken = "#606269"
# 「进度条背景色」：进度条的轨道、滑块未填充段
COLOR_PROGRESS_TRACK: ColorToken = "#3b3e4a"
# 开关的圆球：要和轨道拉开明度差，拨到右边时圆球才看得清
COLOR_BUTTON_KNOB: ColorToken = "#47F6FF"
# 鼠标移到开关上时的圆球色（悬停）
COLOR_BUTTON_KNOB_HOVER: ColorToken = "#eaffff"
# 「三级颜色」：开关的圆球、勾选框的勾、单选框的中心点共用一个亮色
COLOR_KNOB: ColorToken = "#80b8ae"
# 上面的悬停版：鼠标移到开关 / 勾选框 / 单选框上时的高亮
COLOR_KNOB_HOVER: ColorToken = "#eaffff"

COLOR_SOFT: ColorToken = "#22242c"  # 次要按钮底色
COLOR_SOFT_HOVER: ColorToken = "#2c2f38"
# 比 COLOR_SOFT_HOVER 更淡一档：输入框里的图标按钮悬停时用
COLOR_HOVER_FAINT: ColorToken = "#262932"

# 危险配色
COLOR_DANGER: ColorToken = "#FF4949"  # 红色本体：文字 / 实心底
COLOR_DANGER_SOFT: ColorToken = "#2E1618"  # 淡红底
COLOR_DANGER_SOFT_HOVER: ColorToken = "#4a2327"  # 淡红底悬停

COLOR_ERROR: ColorToken = "#f87171"
COLOR_SUCCESS: ColorToken = "#4ade80"
COLOR_WARNING: ColorToken = "#fbbf24"

# 滚动条比边框还淡一档：它常驻在右侧，太显眼会抢内容
COLOR_SCROLLBAR: ColorToken = "#3d4350"
COLOR_SCROLLBAR_HOVER: ColorToken = "#535a6b"

# ---------------------------------------------------------------- 玻璃外观
# 开启「毛玻璃」时窗口底和侧边栏都画纯黑：DWM 的 acrylic 把黑色像素当成透明，
# 于是整窗透出桌面的模糊。卡片、输入框这些仍是实色，浮在玻璃上。
COLOR_BG_GLASS: ColorToken = "#000000"
COLOR_SIDE_GLASS: ColorToken = "#000000"

# 顶部提示条按级别取色（"info" / "success" / "warn" / "error"）
STATUS_COLORS: Dict[str, ColorToken] = {
    "info": COLOR_MUTED,
    "success": COLOR_SUCCESS,
    "warn": COLOR_WARNING,
    "error": COLOR_ERROR,
}

# ---------------------------------------------------------------- 尺寸
SCROLLBAR_WIDTH: int = 12
# 滚动条滑块两侧留白：滑块的可见宽度 = SCROLLBAR_WIDTH - 2 * SCROLLBAR_SPACING
SCROLLBAR_SPACING: int = 4
# `bind_focus_border()` 用的描边宽度：需要「聚焦亮一圈」时把它传给 CTk 控件。
# 库里的输入类控件自己用 1px 的 COLOR_BORDER_INPUT（见上），聚焦也不变色，
# 这个更粗的宽度纯粹是留给调用方的可选项。
# 值必须是 2：Tk 的 canvas 不做抗锯齿，1px 在 150% 缩放下落在半格上，
# 圆角弧线和长边都会成段丢像素——那正是「边框断开」的成因。
BORDER_FOCUS_WIDTH: int = 2
RADIUS_SMALL: int = 8
RADIUS_MEDIUM: int = 10
RADIUS_LARGE: int = 12
RADIUS_PILL: int = 999  # 提示条这类胶囊形

SPACE_XS: int = 4
SPACE_SM: int = 8
SPACE_MD: int = 12
SPACE_LG: int = 16
SPACE_XL: int = 24
