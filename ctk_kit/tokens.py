"""设计令牌：颜色、字体、圆角与间距。

颜色一律写成 ``(浅色, 深色)`` 二元组：CustomTkinter 收到二元组会按当前外观
自动取用，切换深浅色时不需要重建控件。

需要自己取值的场合——原生 tk 控件、canvas、滚动条——用 ``theme.color_of()``。
"""

from __future__ import annotations

# ---------------------------------------------------------------- 字体
# 微软雅黑在 Windows 上最稳；换平台时只改这一行。
FONT_NAME = "微软雅黑"

FONT_TITLE = (FONT_NAME, 20, "bold")      # 页面标题
FONT_CARD_TITLE = (FONT_NAME, 15, "bold")  # 卡片标题
FONT_SECTION = (FONT_NAME, 14, "bold")     # 设置页分区标题
FONT_BODY = (FONT_NAME, 13)                # 正文、输入框
FONT_SMALL = (FONT_NAME, 12)               # 次要说明、按钮
FONT_TINY = (FONT_NAME, 11)                # 时间戳、徽标旁边的信息
FONT_BADGE = (FONT_NAME, 9)                # 分类徽标

# ---------------------------------------------------------------- 颜色
COLOR_BG = ("#f4f5f7", "#0e0f12")             # 窗口底色
COLOR_SIDE = ("#ffffff", "#131418")           # 侧边栏 / 状态栏
COLOR_CARD = ("#ffffff", "#181920")           # 卡片
COLOR_INPUT = ("#ffffff", "#1d1f26")          # 输入框、下拉框、分段控件底色
COLOR_BORDER = ("#e3e6eb", "#262831")         # 细边框
COLOR_BORDER_STRONG = ("#c9cfd8", "#3b3e4a")  # 悬停边框

COLOR_TEXT = ("#111827", "#f1f3f6")
COLOR_MUTED = ("#6b7280", "#98a0ab")
COLOR_FAINT = ("#9aa1ac", "#6b7280")

COLOR_ACCENT = ("#2563eb", "#2f6fed")        # 主色：主按钮、选中态
COLOR_ACCENT_HOVER = ("#1d4ed8", "#3b82f6")
COLOR_ACCENT_TEXT = ("#ffffff", "#ffffff")

COLOR_SOFT = ("#f0f2f5", "#22242c")          # 次要按钮底色
COLOR_SOFT_HOVER = ("#e4e8ee", "#2c2f38")
# 比 COLOR_SOFT_HOVER 更淡一档：输入框里的图标按钮悬停时用，别抢输入框本身的注意力
COLOR_HOVER_FAINT = ("#eef1f6", "#262932")
COLOR_SEG_SELECTED = ("#e2ebff", "#1b2a44")  # 分段控件选中段

COLOR_DANGER = ("#dc2626", "#ef4444")
COLOR_DANGER_SOFT = ("#fdeaea", "#3a1c1e")
COLOR_DANGER_SOFT_HOVER = ("#fbcfcf", "#4a2327")

COLOR_ERROR = ("#dc2626", "#f87171")
COLOR_SUCCESS = ("#15803d", "#4ade80")
COLOR_WARNING = ("#b45309", "#fbbf24")

# 滚动条比边框还淡一档：它常驻在右侧，太显眼会抢内容
COLOR_SCROLLBAR = ("#d9dde5", "#23262e")
COLOR_SCROLLBAR_HOVER = ("#bcc3d0", "#39404f")

# 顶部提示条按级别取色
STATUS_COLORS = {
    "info": COLOR_MUTED,
    "success": COLOR_SUCCESS,
    "warn": COLOR_WARNING,
    "error": COLOR_ERROR,
}

# ---------------------------------------------------------------- 尺寸
SCROLLBAR_WIDTH = 12
RADIUS_SMALL = 8
RADIUS_MEDIUM = 10
RADIUS_LARGE = 12
RADIUS_PILL = 999  # 提示条这类胶囊形

SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24
