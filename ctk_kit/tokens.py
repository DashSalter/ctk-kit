"""设计令牌：颜色、字体、圆角与间距。

颜色一律写成 ``(浅色, 深色)`` 二元组：CustomTkinter 收到二元组会按当前外观
自动取用，切换深浅色时不需要重建控件。

需要自己取值的场合——原生 tk 控件、canvas、滚动条——用 ``theme.color_of()``。

本模块只有常量，没有运行时依赖；导入它是零成本的。
"""

from __future__ import annotations

from typing import Dict, Tuple, Union

# ``(浅色, 深色)`` 颜色二元组，例如 ``("#ffffff", "#181920")``。
ColorPair = Tuple[str, str]

# 字体规格：``(字族, 字号)`` 或 ``(字族, 字号, "bold")``，可直接传给 tk 控件。
FontSpec = Union[Tuple[str, int], Tuple[str, int, str]]

# ---------------------------------------------------------------- 字体
# 微软雅黑在 Windows 上最稳；换平台时只改这一行。
FONT_NAME = "微软雅黑"

FONT_TITLE: FontSpec = (FONT_NAME, 20, "bold")      # 页面标题
FONT_CARD_TITLE: FontSpec = (FONT_NAME, 15, "bold")  # 卡片标题
FONT_SECTION: FontSpec = (FONT_NAME, 14, "bold")     # 设置页分区标题
FONT_BODY: FontSpec = (FONT_NAME, 13)                # 正文、输入框
FONT_SMALL: FontSpec = (FONT_NAME, 12)               # 次要说明、按钮
FONT_TINY: FontSpec = (FONT_NAME, 11)                # 时间戳、徽标旁边的信息
FONT_BADGE: FontSpec = (FONT_NAME, 9)                # 分类徽标

# ---------------------------------------------------------------- 颜色
COLOR_BG: ColorPair = ("#f4f5f7", "#0e0f12")             # 窗口底色
COLOR_SIDE: ColorPair = ("#ffffff", "#131418")           # 侧边栏 / 状态栏
# 标题栏：刻意比内容区和侧边栏都亮一档，深浅两套都能看出「顶栏」这一层
COLOR_TITLEBAR: ColorPair = ("#e8ebf1", "#1c1e25")
COLOR_CARD: ColorPair = ("#ffffff", "#181920")           # 卡片
COLOR_INPUT: ColorPair = ("#ffffff", "#1d1f26")          # 输入框、下拉框、分段控件底色
COLOR_BORDER: ColorPair = ("#e3e6eb", "#262831")         # 细边框
COLOR_BORDER_STRONG: ColorPair = ("#c9cfd8", "#3b3e4a")  # 悬停边框

COLOR_TEXT: ColorPair = ("#111827", "#f1f3f6")
COLOR_MUTED: ColorPair = ("#6b7280", "#98a0ab")
COLOR_FAINT: ColorPair = ("#9aa1ac", "#6b7280")

COLOR_ACCENT: ColorPair = ("#2563eb", "#2f6fed")        # 主色：主按钮、链接
COLOR_ACCENT_HOVER: ColorPair = ("#1d4ed8", "#3b82f6")
COLOR_ACCENT_TEXT: ColorPair = ("#ffffff", "#ffffff")

# 控件「激活态」专用色：勾选、单选、开关拨到右边、滑块已填充、进度条、分段选中段。
# 比主色偏青、饱和度低一档，压在卡片上不刺眼；深色值比 COLOR_INPUT（#1d1f26）明显亮。
COLOR_ACTIVE: ColorPair = ("#1b94a7", "#3891a3")
COLOR_ACTIVE_HOVER: ColorPair = ("#157a8a", "#46a3b5")

COLOR_SOFT: ColorPair = ("#f0f2f5", "#22242c")          # 次要按钮底色
COLOR_SOFT_HOVER: ColorPair = ("#e4e8ee", "#2c2f38")
# 比 COLOR_SOFT_HOVER 更淡一档：输入框里的图标按钮悬停时用，别抢输入框本身的注意力
COLOR_HOVER_FAINT: ColorPair = ("#eef1f6", "#262932")

COLOR_DANGER: ColorPair = ("#dc2626", "#ef4444")
COLOR_DANGER_SOFT: ColorPair = ("#fdeaea", "#3a1c1e")
COLOR_DANGER_SOFT_HOVER: ColorPair = ("#fbcfcf", "#4a2327")

COLOR_ERROR: ColorPair = ("#dc2626", "#f87171")
COLOR_SUCCESS: ColorPair = ("#15803d", "#4ade80")
COLOR_WARNING: ColorPair = ("#b45309", "#fbbf24")

# 滚动条比边框还淡一档：它常驻在右侧，太显眼会抢内容
COLOR_SCROLLBAR: ColorPair = ("#d9dde5", "#23262e")
COLOR_SCROLLBAR_HOVER: ColorPair = ("#bcc3d0", "#39404f")

# 顶部提示条按级别取色（"info" / "success" / "warn" / "error"）
STATUS_COLORS: Dict[str, ColorPair] = {
    "info": COLOR_MUTED,
    "success": COLOR_SUCCESS,
    "warn": COLOR_WARNING,
    "error": COLOR_ERROR,
}

# ---------------------------------------------------------------- 尺寸
SCROLLBAR_WIDTH: int = 12
# 滚动条滑块两侧留白：滑块的可见宽度 = SCROLLBAR_WIDTH - 2 * SCROLLBAR_SPACING
SCROLLBAR_SPACING: int = 4
RADIUS_SMALL: int = 8
RADIUS_MEDIUM: int = 10
RADIUS_LARGE: int = 12
RADIUS_PILL: int = 999  # 提示条这类胶囊形

SPACE_XS: int = 4
SPACE_SM: int = 8
SPACE_MD: int = 12
SPACE_LG: int = 16
SPACE_XL: int = 24
