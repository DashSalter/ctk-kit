"""设计令牌：颜色、字体、圆角与间距。

颜色一般写成 ``(浅色, 深色)`` 二元组：CustomTkinter 收到二元组会按当前外观
自动取用，切换深浅色时不需要重建控件。需要单独指定「毛玻璃」那一档时写成
``(浅色, 深色, 毛玻璃)`` 三元组——第三项只在开启毛玻璃底色时生效，没写就
沿用深色值。

需要自己取值的场合——原生 tk 控件、canvas、滚动条——用 ``theme.color_of()``。

本模块只有常量，没有运行时依赖；导入它是零成本的。
"""

from __future__ import annotations

from typing import Dict, Tuple, Union

# 颜色令牌：``(浅色, 深色)`` 或 ``(浅色, 深色, 毛玻璃)``。
# 第三项只在毛玻璃底色下使用，缺省时毛玻璃沿用深色值。
ColorPair = Union[Tuple[str, str], Tuple[str, str, str]]

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
COLOR_BG: ColorPair = ("#f4f5f7", "#0e0f12")  # 窗口底色
COLOR_SIDE: ColorPair = ("#ffffff", "#131418")  # 侧边栏 / 状态栏
# 标题栏：刻意比内容区和侧边栏都亮一档，深浅两套都能看出「顶栏」这一层
COLOR_TITLEBAR: ColorPair = ("#e8ebf1", "#1c1e25")
COLOR_CARD: ColorPair = ("#ffffff", "#181920")  # 卡片
# 输入类控件（输入框、下拉框、文本区）的底色。描边只有 1px，边界主要靠这层底色
# 和卡片拉开层次，所以浅色值取「比卡片暗一档的灰」而不是纯白。
COLOR_INPUT: ColorPair = ("#eef1f6", "#22242c")
COLOR_BORDER: ColorPair = ("#e3e6eb", "#262831")  # 细边框：卡片、分割线
COLOR_BORDER_STRONG: ColorPair = ("#c9cfd8", "#3b3e4a")  # 轨道、未选中描边
# 输入类控件的 1px 描边：比 COLOR_BORDER 深一档，白卡片上才看得出边界。
# 深色下它常常只在水平边上可见（竖直边被 150% 缩放的半格吃掉），这是 Tk 不抗锯齿的
# 已知代价，不是颜色选错。
COLOR_BORDER_INPUT: ColorPair = ("#b0b9c6", "#343a47")

COLOR_TEXT: ColorPair = ("#111827", "#f1f3f6")
# 比 COLOR_TEXT 柔和一档：表格正文、密集列表用，深色下不会白得晃眼
COLOR_TEXT_SOFT: ColorPair = ("#374151", "#B1B6BD")
COLOR_MUTED: ColorPair = ("#6b7280", "#98a0ab")
COLOR_FAINT: ColorPair = ("#9aa1ac", "#6b7280")

COLOR_ACCENT: ColorPair = ("#2563eb", "#2f6fed", "#3E4059")  # 主色：主按钮、链接
COLOR_ACCENT_HOVER: ColorPair = ("#1d4ed8", "#4B4D6B")
COLOR_ACCENT_TEXT: ColorPair = ("#ffffff", "#ffffff")

# 控件「激活态」专用色：勾选、单选、开关拨到右边、滑块已填充、进度条、分段选中段。
# 比主色偏青，色相统一；两套取值都要在卡片底色上足够亮，选中一眼能看出来。
# 第三项是毛玻璃底下的取值：透明底上的青色发灰，换成更沉的蓝才压得住。
COLOR_ACTIVE: ColorPair = ("#17a6bd", "#4fb6cc", "#606269")
COLOR_ACTIVE_HOVER: ColorPair = ("#13899d", "#6acbdd", "#494A4F")
# 开关的圆球：要和青色轨道拉开明度差，拨到右边时圆球才看得清
COLOR_BUTTON_KNOB: ColorPair = ("#559FE8", "#47F6FF")
# 鼠标移到开关上时的圆球色（悬停）。浅色主题的轨道是浅灰 / 中青，球要往深里走；
# 深色主题轨道偏暗，球要往亮里走。不能用同色系的中调（会糊在轨道里）。
COLOR_BUTTON_KNOB_HOVER: ColorPair = ("#1d4ed8", "#eaffff")

COLOR_SOFT: ColorPair = ("#f0f2f5", "#22242c")  # 次要按钮底色
COLOR_SOFT_HOVER: ColorPair = ("#e4e8ee", "#2c2f38")
# 比 COLOR_SOFT_HOVER 更淡一档：输入框里的图标按钮悬停时用，别抢输入框本身的注意力
COLOR_HOVER_FAINT: ColorPair = ("#eef1f6", "#262932")

# 危险配色
COLOR_DANGER: ColorPair = ("#dc2626", "#ef4444",'#FF4949')  # 红色本体：文字 / 实心底
COLOR_DANGER_SOFT: ColorPair = ("#fdeaea", "#3a1c1e",'#2E1618')  # 淡红底
COLOR_DANGER_SOFT_HOVER: ColorPair = ("#fbcfcf", "#4a2327")  # 淡红底悬停

COLOR_ERROR: ColorPair = ("#dc2626", "#f87171")
COLOR_SUCCESS: ColorPair = ("#15803d", "#4ade80")
COLOR_WARNING: ColorPair = ("#b45309", "#fbbf24")

# 滚动条比边框还淡一档：它常驻在右侧，太显眼会抢内容
COLOR_SCROLLBAR: ColorPair = ("#c8cdd8", "#3d4350")
COLOR_SCROLLBAR_HOVER: ColorPair = ("#aab1c0", "#535a6b")

# ---------------------------------------------------------------- 玻璃外观
# 开启「毛玻璃」时窗口底和侧边栏都画纯黑：DWM 的 acrylic 把黑色像素当成透明，
# 于是整窗透出桌面的模糊。卡片、输入框这些仍是实色，浮在玻璃上。
# 深浅两套都取纯黑——透出来偏亮还是偏暗由 tint 决定，不由这两个值决定。
COLOR_BG_GLASS: ColorPair = ("#000000", "#000000")
COLOR_SIDE_GLASS: ColorPair = ("#000000", "#000000")

# 顶部提示条按级别取色（"info" / "success" / "warn" / "error"）
STATUS_COLORS: Dict[str, ColorPair] = {
    "info": COLOR_MUTED,
    "success": COLOR_SUCCESS,
    "warn": COLOR_WARNING,
    "error": COLOR_ERROR,
}


def _flatten_glass_colors() -> None:
    """把源码里的三元组压平成二元组。

    CustomTkinter 的 ``_check_color_type`` 只接受长度正好是 2 的元组，三元组
    传进去会直接抛 ``ValueError``。所以模块加载完就把常量换回二元组，第三项
    （毛玻璃取值）收进 :data:`GLASS_COLORS`，由 ``theme.apply_backdrop`` 使用。
    这样常量声明处仍能一眼看出玻璃模式用哪个色，下游拿到的又始终是合法二元组。
    """
    for name, value in list(globals().items()):
        if not name.startswith("COLOR_") or not isinstance(value, tuple):
            continue
        if len(value) == 3:
            GLASS_COLORS[name] = (value[2], value[2])
            globals()[name] = (value[0], value[1])


#: 毛玻璃模式下要替换的颜色：``{令牌名: (玻璃色, 玻璃色)}``。
#: 键是 ``tokens`` 里的常量名，值是已经压成二元组的玻璃取值。
GLASS_COLORS: Dict[str, ColorPair] = {}

_flatten_glass_colors()

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
