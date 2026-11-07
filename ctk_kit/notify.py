"""窗口内的浮层提示（toast）。

信息可以不再挤在窗口里的某一行文字上：提示条直接浮在窗口顶部或底部的
边缘，几秒后自己消失，不占布局、不挤动内容，窗口缩放时跟着边缘走。

两种形态:

- ``pill``：一行窄条，圆角与卡片一致，适合「已复制」「已保存」这类过程提示，
  会自动消失。
- ``card``：带状态图标、标题、正文和关闭按钮的卡片，适合错误、警告这类
  需要看清再处理的信息；默认停留时间更长。

两个位置: 窗口顶部（``position="top"``）与窗口底部（``position="bottom"``）。

每条提示都是一个无边框的小窗口（和下拉面板同一套做法）：窗口本身被系统
裁成圆角，圆角以外根本不绘制，所以压在页面卡片上也不会露出一圈深色底。

用法::

    from ctk_kit import Notifier

    tips = Notifier(app)
    tips.show("已复制到剪贴板")
    tips.show("保存成功", level="success")
    tips.show("云备份失败", title="网络错误", level="error",
              style="card", position="bottom")

不想自己持有实例时，用便捷函数：它会按窗口缓存一个默认的 ``Notifier``，
连续调用时多条提示会正常堆叠::

    from ctk_kit import notify

    notify(app, "已复制到剪贴板")
    notify(app, "保存成功", level="success", position="bottom")

提示条只在 ``show`` 时创建，关掉就把小窗口一并销毁，不会常驻。
"""

from __future__ import annotations

import contextlib
import sys
import time
import tkinter as tk
import weakref
from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image, ImageDraw

from . import tokens as T
from .core.win32 import clear_window_alpha
from .paint import cached
from .popup import round_window_corners
from .fonts import get_font

#: 允许的提示级别。
LEVELS = ("info", "success", "warn", "error")

#: 允许的位置。
POSITIONS = ("top", "bottom")

#: 允许的形态。
STYLES = ("pill", "card")

#: 每个级别在卡片圆标里用的符号。
LEVEL_ICONS = {
    "info": "i",
    "success": "✓",
    "warn": "!",
    "error": "✕",
}

#: 每种形态的默认停留秒数。卡片信息多，多留一会儿。
DEFAULT_SECONDS = {"pill": 2.6, "card": 4.5}

#: 图标超采样倍数：先按 4 倍画，再交给 ``CTkImage`` 缩回去，圆边才没有锯齿。
_ICON_SCALE = 4


@cached
def _level_icon(level: str, color: str, size: int, scaling: float) -> Image.Image:
    """画一枚抗锯齿的级别图标：圆底 + 白色符号。

    尺寸按物理像素算：``size * scaling`` 取整后再乘 ``_ICON_SCALE``，
    缩回去正好是整数倍，不会卡在半个像素上发糊。
    """
    pixel = max(16, int(round(size * scaling))) * _ICON_SCALE
    image = Image.new("RGBA", (pixel, pixel), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pen.ellipse((0, 0, pixel - 1, pixel - 1), fill=color)

    u = pixel / 22.0            # 以 22 逻辑像素为基准换算符号坐标
    width = max(2, int(round(2.1 * u)))
    cx = cy = pixel / 2.0
    white = "#ffffff"

    if level == "error":
        arm = 4.3 * u
        pen.line([(cx - arm, cy - arm), (cx + arm, cy + arm)], fill=white, width=width)
        pen.line([(cx - arm, cy + arm), (cx + arm, cy - arm)], fill=white, width=width)
    elif level == "warn":
        pen.line([(cx, cy - 4.8 * u), (cx, cy + 1.2 * u)], fill=white, width=width)
        dot = 1.2 * u
        pen.ellipse(
            (cx - dot, cy + 3.6 * u - dot, cx + dot, cy + 3.6 * u + dot), fill=white
        )
    elif level == "success":
        pen.line(
            [
                (cx - 4.2 * u, cy + 0.3 * u),
                (cx - 1.2 * u, cy + 3.3 * u),
                (cx + 4.4 * u, cy - 3.4 * u),
            ],
            fill=white,
            width=width,
            joint="curve",
        )
    else:  # info
        dot = 1.1 * u
        pen.ellipse(
            (cx - dot, cy - 4.3 * u - dot, cx + dot, cy - 4.3 * u + dot), fill=white
        )
        pen.line([(cx, cy - 1.4 * u), (cx, cy + 4.6 * u)], fill=white, width=width)
    return image


def _level_image(level: str, color: str, size: int, scaling: float) -> ctk.CTkImage:
    """把 ``_level_icon`` 包成 ``CTkImage``（交给 CTk 按 DPI 缩放）。"""
    image = _level_icon(level, color, size, scaling)
    return ctk.CTkImage(
        light_image=image,
        dark_image=image.copy(),
        size=(size, size),
    )

_MARGIN = 16  # 浮层离窗口边缘的距离
_GAP = 8      # 同一位置多条提示之间的间隙
_FADE_STEPS = 5   # 淡入淡出分几步
_FADE_MS = 16     # 每步间隔，整体约 80ms


class _Notice:
    """一条提示的内部状态：窗口、控件、计时器与剩余时长。"""

    __slots__ = (
        "window",
        "view",
        "position",
        "style",
        "duration",
        "remaining",
        "timer",
        "started",
        "on_close",
    )

    def __init__(self, window, view, position, style, duration, on_close):
        """保存一条提示的状态字段；控件和计时器由 ``Notifier`` 管。"""
        self.window = window
        self.view = view
        self.position = position
        self.style = style
        self.duration = duration
        self.remaining = duration
        self.timer = None
        self.started = time.monotonic()
        self.on_close = on_close





# 卡片底色 / 关闭按钮悬停色，和右键菜单、下拉面板保持一致。
_CARD_BG = "#2B2B2B"
_CARD_HOVER = "#575A63"


class Notifier:
    """管理贴在窗口顶部或底部的提示条。

    一个窗口建一个实例即可，``show`` 可以反复调用，同一位置的提示会纵向
    堆叠。每条提示是一个独立的无边框小窗口，圆角由系统裁剪，四角不会露出
    底色；窗口位置跟着 ``master`` 的边缘走。

    参数:
        master: 提示条所属的窗口或容器，浮层相对它的边缘定位。
        duration: 默认停留秒数；``None`` 时按形态取 ``DEFAULT_SECONDS``，
            取 ``0`` 表示不自动消失，需要手动关闭。
        max_visible: 同一位置最多同时显示几条，超出时先关掉最旧的。
    """

    def __init__(
        self, master, *, duration: Optional[float] = None, max_visible: int = 3
    ):
        """保存参数；提示条本身在第一次 :meth:`show` 时才创建。"""
        self.master = master
        self.duration = duration
        self.max_visible = max(1, int(max_visible))
        self._notes = {position: [] for position in POSITIONS}
        self._follow_id = None
        self._focus_id = None

    # ---------------------------------------------------------------- 公开接口

    def show(
        self,
        message: str,
        *,
        title: str = "",
        level: str = "info",
        position: str = "top",
        style: str = "pill",
        duration: Optional[float] = None,
        on_close: Optional[Callable] = None,
    ) -> ctk.CTkFrame:
        """弹出一条提示。

        参数:
            message: 正文文字。
            title: 卡片形态的标题；为空时只显示正文。
            level: 级别，取 ``"info"`` / ``"success"`` / ``"warn"`` / ``"error"``。
            position: ``"top"`` 贴窗口顶部，``"bottom"`` 贴窗口底部。
            style: ``"pill"`` 单行窄条，``"card"`` 带图标和关闭按钮的卡片。
            duration: 这条提示停留多少秒；``None`` 用实例默认值，``0`` 表示常驻。
            on_close: 提示消失时调用，参数是这条提示的控件。

        返回:
            这条提示的 ``CTkFrame``，可以交给 :meth:`dismiss` 提前关闭。

        异常:
            ValueError: ``level`` / ``position`` / ``style`` 不在允许范围。
        """
        self._check(level, position, style)
        seconds = self._seconds(style, duration)
        window, view = self._build(message, title, level, style)
        notice = _Notice(window, view, position, style, seconds, on_close)
        self._mount(notice)
        if seconds > 0:
            self._arm(notice)
        self._bind_hover(view, notice)
        return view

    def dismiss(self, view) -> bool:
        """立刻关闭一条提示。

        参数:
            view: :meth:`show` 返回的控件。

        返回:
            找到并关掉了返回 ``True``，这条提示已经不在了返回 ``False``。
        """
        for position in POSITIONS:
            for notice in list(self._notes[position]):
                if notice.view is view:
                    self._remove(notice)
                    return True
        return False

    def clear(self) -> None:
        """关掉当前所有提示。"""
        for position in POSITIONS:
            for notice in list(self._notes[position]):
                self._remove(notice, notify=False)

    def count(self, position: Optional[str] = None) -> int:
        """数一数当前显示着几条提示。

        参数:
            position: 只数某一个位置；``None`` 数两边总数。

        返回:
            提示条数。
        """
        if position is None:
            return sum(len(notes) for notes in self._notes.values())
        return len(self._notes[position])

    def destroy(self) -> None:
        """关掉所有提示并解除对窗口的跟随（窗口关闭前调用可选）。"""
        self.clear()

    # ---------------------------------------------------------------- 内部实现

    @staticmethod
    def _check(level, position, style) -> None:
        """校验级别、位置、形态三个枚举值，非法时抛 ``ValueError``。"""
        if level not in LEVELS:
            raise ValueError(
                "level 只能是 " + " / ".join(LEVELS) + "，收到 " + repr(level)
            )
        if position not in POSITIONS:
            raise ValueError(
                "position 只能是 " + " / ".join(POSITIONS) + "，收到 " + repr(position)
            )
        if style not in STYLES:
            raise ValueError(
                "style 只能是 " + " / ".join(STYLES) + "，收到 " + repr(style)
            )

    def _seconds(self, style, duration) -> float:
        """算这条提示实际停留多少秒：调用参数 > 实例默认 > 形态默认。"""
        if duration is not None:
            return max(0.0, float(duration))
        if self.duration is not None:
            return max(0.0, float(self.duration))
        return DEFAULT_SECONDS[style]

    def _build(self, message, title, level, style) -> tuple[Any, Any]:
        """建出小窗口和里面那张卡片，返回 ``(window, card)``。"""
        color = T.STATUS_COLORS[level]
        # 两种形态都用 RADIUS_SMALL 的小圆角：圆角半径要和 Windows 的
        # 系统窗口圆角（约 8）一致，描边环才不会在四角被裁出豁口。
        radius = T.RADIUS_SMALL

        window = ctk.CTkToplevel(self.master)
        window.withdraw()
        window.overrideredirect(True)
        # 不做全局置顶：设了 -topmost 之后，切到别的应用提示还浮在最上面。
        # transient 把窗口挂成主窗口的「附属窗口」——只在主窗口之上，
        # 主窗口被别的应用盖住或最小化时，提示也跟着一起下去。
        with contextlib.suppress(Exception):
            window.transient(self.master)
        # 描边用「一圈底色」而不是控件自带的 border：窗口整面铺描边色，
        # 卡片四边各内缩 1px，四边宽度就是绝对均匀的，圆角处也跟着一起弯。
        window.configure(fg_color=T.COLOR_BORDER)

        # 卡片底色和右键菜单、下拉面板保持一致（#2B2B2B）。
        card = ctk.CTkFrame(
            window,
            fg_color=_CARD_BG,
            corner_radius=max(1, radius - 1),
            border_width=0,
        )
        card.pack(fill="both", expand=True, padx=1, pady=1)

        if style == "pill":
            dot = ctk.CTkFrame(
                card, width=7, height=7, corner_radius=4, fg_color=color
            )
            dot.pack(side="left", padx=(14, 8))
            ctk.CTkLabel(
                card,
                text=message,
                font=get_font(T.FONT_SMALL),
                text_color=color,
                anchor="w",
                justify="left",
            ).pack(side="left", padx=(0, 16), pady=7)
            return window, card

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(
            body,
            text="",
            image=_level_image(level, color, 22, self._scaling()),
            width=22,
            height=22,
        ).pack(side="left", anchor="n", pady=(2, 0))
        text = ctk.CTkFrame(body, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True, padx=(10, 6))
        if title:
            ctk.CTkLabel(
                text,
                text=title,
                font=get_font((T.FONT_NAME, 13, "bold")),
                text_color=T.COLOR_TEXT,
                anchor="w",
                justify="left",
            ).pack(fill="x")
        ctk.CTkLabel(
            text,
            text=message,
            font=get_font(T.FONT_SMALL),
            text_color=T.COLOR_MUTED,
            anchor="w",
            justify="left",
            wraplength=300,
        ).pack(fill="x", pady=(2, 0) if title else 0)
        ctk.CTkButton(
            body,
            text="✕",
            width=18,
            height=18,
            border_spacing=0,
            corner_radius=6,
            fg_color="transparent",
            hover_color=_CARD_HOVER,
            text_color=T.COLOR_FAINT,
            font=get_font((T.FONT_NAME, 10)),
            command=lambda v=card: self.dismiss(v),
        ).pack(side="right", anchor="n", padx=(6, 0), pady=(2, 0))
        # 内容建完先量一次尺寸；窗口这时还藏着，等 _relayout 定位后再显出来。
        window.update_idletasks()
        return window, card

    def _mount(self, notice) -> None:
        """把一条新提示挂进对应位置，超上限时先关掉最旧的，再统一重排。"""
        notes = self._notes[notice.position]
        notes.append(notice)
        self._ensure_follow()
        # 先关掉超出上限的旧提示，再统一排一次位置。反过来的话新提示会先
        # 按「多一条」的位置显示出来、紧接着整列上移，看起来就是闪一下。
        while len(notes) > self.max_visible:
            self._remove(notes[0], notify=False, relayout=False)
        self._relayout(notice.position)

    def _ensure_follow(self) -> None:
        """挂上窗口移动/缩放/获焦的跟随绑定；已经挂过就什么都不做。"""
        if self._follow_id is not None:
            return
        try:
            self._follow_id = self.master.bind(
                "<Configure>", lambda _event: self._relayout_all(), add="+"
            )
            # 主窗口重新激活时把提示再抬一次：transient 在部分平台上对
            # overrideredirect 窗口不生效，靠这一下兜底。
            self._focus_id = self.master.bind(
                "<FocusIn>", lambda _event: self._raise_notes(), add="+"
            )
        except Exception:
            self._follow_id = None
            self._focus_id = None

    def _raise_notes(self) -> None:
        """主窗口重新获得焦点时，把所有提示条重新抬到最上面。"""
        for position in POSITIONS:
            for notice in self._notes[position]:
                with contextlib.suppress(Exception):
                    notice.window.lift()

    def _drop_follow(self) -> None:
        """解除窗口跟随绑定，清空事件句柄。"""
        with contextlib.suppress(Exception):
            if self._follow_id is not None:
                self.master.unbind("<Configure>", self._follow_id)
            if self._focus_id is not None:
                self.master.unbind("<FocusIn>", self._focus_id)
        self._follow_id = None
        self._focus_id = None

    def _relayout_all(self) -> None:
        """两个位置上只要有提示，就各自重排一遍。"""
        for position in POSITIONS:
            if self._notes[position]:
                self._relayout(position)

    def _relayout(self, position) -> None:
        """把同一位置的提示从边缘开始纵向排开，条与条之间只留空隙。

        每条提示是一个小窗口，尺寸按卡片需求算；窗口贴边后由系统裁圆角，
        所以浮层面积就只有卡片本身。
        """
        notes = self._notes[position]
        # 最新的那条离窗口边缘最近：顶部从新到旧往下排，底部从新到旧往上排。
        ordered = list(reversed(notes))
        scaling = self._scaling()
        root_x = self.master.winfo_rootx()
        root_y = self.master.winfo_rooty()
        root_w = self.master.winfo_width()
        root_h = self.master.winfo_height()
        offset = self._margin_physical()
        for notice in ordered:
            window = notice.window
            try:
                window.update_idletasks()
                # 窗口藏着时用内容请求尺寸；已经显示出来的用实际尺寸。
                if window.winfo_ismapped():
                    width = window.winfo_width()
                    height = window.winfo_height()
                else:
                    width = window.winfo_reqwidth()
                    height = window.winfo_reqheight()
            except Exception:
                continue
            if width <= 2 or height <= 2:
                continue
            x = root_x + max(0, (root_w - width) // 2)
            if position == "top":
                y = root_y + offset
            else:
                y = root_y + root_h - offset - height
            # 尺寸按逻辑像素给、位置直接是屏幕像素（与下拉面板同一套换算）。
            # 注意：只给 "+x+y" 的位置形式在 CTkToplevel 上会被忽略，必须带尺寸。
            # 尺寸**向下**取整：round/ceil 让窗口比内容大一点点时，多出来的那条
            # 像素会露出窗口底色，在圆角外形成一圈没被抠掉的亮边。
            size = "{:d}x{:d}".format(
                max(1, int(width / scaling)), max(1, int(height / scaling))
            )
            if not window.winfo_ismapped():
                # 新窗口先在屏幕外完成第一次绘制，再挪到目标位置：直接在目标
                # 位置 deiconify 的话，系统会先显示一个空框、再补上内容。
                window.geometry(size + "+-10000+-10000")
                with contextlib.suppress(Exception):
                    window.attributes("-alpha", 0.0)
                window.deiconify()
                window.update_idletasks()
                fresh = True
            else:
                fresh = False
            window.geometry(size + "+{:d}+{:d}".format(int(x), int(y)))
            # 先让 Tk 处理这次几何变更再抬窗口：顺序反过来时 lift 之前
            # 排队的 geometry 会被丢掉，多条提示会全部叠在同一个位置。
            window.update_idletasks()
            window.lift()
            self._round_window_corners(window)
            if fresh:
                self._fade(window, 0.0, 1.0)
            offset += height + int(round(_GAP * scaling))
        # 统一刷新一次，确保这一轮所有窗口都真的移到了算好的位置。
        with contextlib.suppress(Exception):
            self.master.update_idletasks()

    def _scaling(self) -> float:
        """当前窗口缩放比；拿不到时按 1.0 处理。"""
        try:
            return self.master.winfo_toplevel()._get_window_scaling() or 1.0
        except Exception:
            return 1.0

    def _margin_physical(self) -> int:
        """提示离窗口边缘的间距，换算成物理像素。"""
        return int(round(_MARGIN * self._scaling()))

    def _round_window_corners(self, window) -> None:
        """把窗口裁成圆角，公共逻辑在 :mod:`ctk_kit.popup`。"""
        # 半径跟内部卡片同值：窗口比卡片更圆时，四角会露出一圈粗描边。
        round_window_corners(window, T.RADIUS_SMALL, self._scaling())

    def _remove(self, notice, notify=True, relayout=True) -> None:
        """从位置列表摘掉一条提示，淡出后销毁；可选触发关闭回调。

        参数:
            notice: 要移除的提示状态。
            notify: 是否调用它的 ``on_close`` 回调。
            relayout: 是否立刻重排同位置的其余提示（补位）。
        """
        notes = self._notes.get(notice.position)
        if not notes or notice not in notes:
            return
        notes.remove(notice)
        if notice.timer is not None:
            with contextlib.suppress(Exception):
                notice.window.after_cancel(notice.timer)
            notice.timer = None
        window = notice.window
        view = notice.view
        # 先从列表里摘掉并重排，让下面的提示立刻补位；窗口本身在原位
        # 淡出后再销毁。直接 destroy 会出现「那一格突然空掉」的跳变。
        if relayout:
            self._relayout(notice.position)
        if not self._notes["top"] and not self._notes["bottom"]:
            self._drop_follow()
        if notify and notice.on_close is not None:
            notice.on_close(view)
        # 淡出期间可能有别的提示补到同一格，抬到最上层再淡出，不然会被盖住。
        with contextlib.suppress(Exception):
            window.lift()
        self._fade(window, 1.0, 0.0, on_done=lambda: self._destroy_window(window))

    @staticmethod
    def _destroy_window(window) -> None:
        """销毁提示窗口；已经销毁或窗口已失效时静默忽略。"""
        with contextlib.suppress(Exception):
            window.destroy()

    def _fade(self, window, start, end, on_done=None) -> None:
        """让窗口透明度从 ``start`` 渐变到 ``end``，结束后回调。"""
        steps = _FADE_STEPS

        def step(index) -> None:
            """执行第 ``index`` 步透明度；走完调用 ``on_done``。"""
            if index > steps:
                if end >= 1.0:
                    # 淡入结束就把 WS_EX_LAYERED 摘掉：layered 窗口的内容是
                    # 位图合成，125% 缩放下文字会被重采样，看着发虚。
                    with contextlib.suppress(Exception):
                        clear_window_alpha(window)
                if on_done is not None:
                    on_done()
                return
            value = start + (end - start) * index / steps
            try:
                window.attributes("-alpha", max(0.0, min(1.0, value)))
            except Exception:
                if on_done is not None:
                    on_done()
                return
            with contextlib.suppress(Exception):
                window.after(_FADE_MS, lambda: step(index + 1))

        step(1)

    def _arm(self, notice) -> None:
        """启动或重启这条提示的自动关闭计时器。"""
        if notice.timer is not None:
            with contextlib.suppress(Exception):
                notice.window.after_cancel(notice.timer)
        notice.started = time.monotonic()
        notice.timer = notice.window.after(
            int(notice.remaining * 1000), lambda: self._expire(notice)
        )

    def _expire(self, notice) -> None:
        """计时到点：关掉这条提示。"""
        notice.timer = None
        self._remove(notice)

    def _pause(self, notice) -> None:
        """指针悬停：取消计时器，并记下已经停留了多久、还剩多少。"""
        if notice.timer is None:
            return
        with contextlib.suppress(Exception):
            notice.window.after_cancel(notice.timer)
        notice.timer = None
        notice.remaining = max(
            0.15, notice.remaining - (time.monotonic() - notice.started)
        )

    def _resume(self, notice) -> None:
        """指针移开：按剩余时间继续计时；提示已经关掉就不管。"""
        if notice.timer is not None or notice.remaining <= 0:
            return
        if notice.position not in self._notes:
            return
        if notice not in self._notes[notice.position]:
            return
        self._arm(notice)

    def _bind_hover(self, widget, notice) -> None:
        """指针停在提示上时暂停自动消失，移开继续计时。"""
        try:
            widget.bind("<Enter>", lambda _event: self._pause(notice), add="+")
            widget.bind("<Leave>", lambda _event: self._resume(notice), add="+")
        except Exception:
            pass
        for child in widget.winfo_children():
            self._bind_hover(child, notice)


_NOTIFIERS = weakref.WeakKeyDictionary()


def notify(master, message: str, **kwargs) -> ctk.CTkFrame:
    """用默认参数的 :class:`Notifier` 弹出一条提示。

    同一个 ``master`` 会复用同一个 ``Notifier``，所以连续调用时多条提示
    会正常堆叠。``App`` 自带 ``self.notifier``，这里会优先复用它，避免同一
    个窗口出现两个提示层（那样同一位置的提示会互相叠）。

    参数:
        master: 提示条所属的窗口或容器。
        message: 正文文字。
        **kwargs: 其余参数原样传给 :meth:`Notifier.show`。

    返回:
        这条提示的 ``CTkFrame``。
    """
    notifier = getattr(master, "notifier", None)
    if notifier is None:
        notifier = _NOTIFIERS.get(master)
        if notifier is None:
            notifier = Notifier(master)
            _NOTIFIERS[master] = notifier
    return notifier.show(message, **kwargs)
