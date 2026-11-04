"""主窗口底下那一层「颜色窗口」。

它就是一块和主窗口等大、同位置的窗口，挂在主窗口下面，自己开着系统
毛玻璃（``AccentState = 3``）。上层主窗口把客户区抠成透明，于是视觉上
看到的是：

    桌面 → 被这一层模糊 → 叠上这里选的颜色 → 上层控件浮在上面

颜色（tint）由调用方给，暖黑、深灰、纯白都可以；模糊本身由 DWM 做，
所以换颜色只改一个整数，不用重画任何图。
"""

from __future__ import annotations

import contextlib
import tkinter as tk
from typing import Optional

from .popup import set_glass_geometry
from .win32 import enable_acrylic, set_round_region

__all__ = ["FrostLayer"]

#: 兜底同步的间隔（毫秒）。拖动窗口时 ``<Configure>`` 不一定实时，靠它补。
POLL_MS = 300

#: 毛玻璃模式下窗口自身的底色：纯黑才会被 DWM 当成透明键。
_KEY_COLOR = "#000000"


def _tint(color: str, alpha: int) -> int:
    """把 ``#RRGGBB`` + alpha 拼成 DWM 要的 ``0xAABBGGRR``。"""
    rgb = str(color).lstrip("#")
    red, green, blue = int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16)
    return (int(alpha) & 0xFF) << 24 | blue << 16 | green << 8 | red


class FrostLayer:
    """贴在主窗口下面、负责「模糊 + 颜色」的那一层。

    参数:
        master: 主窗口（``App``）。
        color: 叠在模糊桌面上的颜色，``#RRGGBB``。
        alpha: 颜色浓度，``0``–``255``；越小越透。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        color: str = "#FFFFFF",
        alpha: int = 0x38,
        glass: bool = False,
        spread: int = 0,
    ) -> None:
        self.master = master
        self.color = color
        self.alpha = int(alpha)
        self.glass = bool(glass)
        self.spread = max(0, int(spread))
        self._window: Optional[tk.Toplevel] = None
        self._poll: Optional[str] = None
        self._visible = False
        self._syncing = False
        self._region_size: Optional[tuple[int, int]] = None
        self._bindings: list[tuple[str, str]] = []

    # ------------------------------------------------------------------ 生命周期
    def start(self) -> None:
        """建窗口、挂玻璃、开始跟随主窗口。"""
        self._ensure()
        self.show()
        self._schedule()

    def stop(self) -> None:
        """拆掉底层窗口，停止跟随。"""
        if self._poll is not None:
            with contextlib.suppress(tk.TclError):
                self.master.after_cancel(self._poll)
            self._poll = None
        for sequence, funcid in self._bindings:
            with contextlib.suppress(tk.TclError):
                self.master.unbind(sequence, funcid)
        self._bindings.clear()
        window, self._window = self._window, None
        self._visible = False
        # 窗口换了，圆角裁剪的缓存也跟着失效，下次 sync 要重裁。
        self._region_size = None
        if window is not None:
            with contextlib.suppress(tk.TclError):
                window.destroy()

    def show(self) -> None:
        """显示底层窗口并立即对齐。"""
        window = self._window
        if window is None or not window.winfo_exists():
            return
        with contextlib.suppress(tk.TclError):
            window.deiconify()
        # -alpha 要在窗口显示之后设才生效，所以这里再刷一次底色。
        self.apply_glass()
        self._visible = True
        self.sync()
        self._keep_behind()
        # 新开的窗口会把焦点抢走，显示完把焦点还给主窗口。
        with contextlib.suppress(tk.TclError):
            self.master.after(30, self._restore_focus)

    def hide(self) -> None:
        """藏起来（主窗口最小化时用）。"""
        self._visible = False
        window = self._window
        if window is None or not window.winfo_exists():
            return
        with contextlib.suppress(tk.TclError):
            window.withdraw()

    # ------------------------------------------------------------------ 颜色
    def configure(
        self,
        *,
        color: Optional[str] = None,
        alpha: Optional[int] = None,
        glass: Optional[bool] = None,
        spread: Optional[int] = None,
    ) -> None:
        """换颜色 / 浓度 / 是否用毛玻璃 / 外扩尺寸，立刻重画一次。"""
        mode_changed = glass is not None and bool(glass) != self.glass
        if color is not None:
            self.color = color
        if alpha is not None:
            self.alpha = int(alpha)
        if glass is not None:
            self.glass = bool(glass)
        if spread is not None:
            self.spread = max(0, int(spread))
        if mode_changed:
            # 纯色 ↔ 毛玻璃 换的是窗口的「种类」（一个带 WS_THICKFRAME +
            # extend，一个不带）。就地改底色拆不干净，直接重建一个最省事。
            self.stop()
            self.start()
            # 新窗口的 <Configure> 可能晚一帧才到，补一次对齐。
            with contextlib.suppress(tk.TclError):
                self.master.after(80, self.sync)
            return
        self.apply_glass()
        # 重画有时会把这一层顶到前面，换完再压回去。
        self._keep_behind()

    def apply_glass(self) -> None:
        """把当前底色画到这一层上。

        ``glass=False``：一块普通纯色窗口，颜色选什么就是什么。
        ``glass=True``：改成系统毛玻璃——底色刷纯黑让 DWM 当透明键，
        模糊和 tint 交给 DWM。
        """
        window = self._window
        if window is None or not window.winfo_exists():
            return
        if self.glass:
            with contextlib.suppress(tk.TclError):
                window.configure(bg=_KEY_COLOR)
                enable_acrylic(
                    window,
                    tint=_tint(self.color, self.alpha),
                    accent=3,
                    extend=True,
                    frame=True,
                )
            self._round(window)
            return
        with contextlib.suppress(tk.TclError):
            window.configure(bg=self.color)
            # 纯色窗口的「背景透明度」走 Tk 的 -alpha：0 全透、255 最实。
            window.attributes(
                "-alpha", max(0.0, min(1.0, int(self.alpha) / 255.0))
            )
            # 主窗口是圆角，这一层要是直角，四个角就会露出它自己的底色。
            # DWM 的 33 对无边框窗口不生效，只能自己裁区域。
            self._round(window)

    def _round(self, window: tk.Toplevel) -> None:
        """把这一层裁成跟主窗口一样的圆角。"""
        with contextlib.suppress(tk.TclError):
            set_round_region(
                window,
                self._radius(),
                window.winfo_width(),
                window.winfo_height(),
            )

    # ------------------------------------------------------------------ 跟随
    def sync(self) -> None:
        """把底层窗口对齐到主窗口：位置和尺寸。

        这里**不要**调 ``update_idletasks()``：它会就地处理待办事件，把
        ``<Configure>`` 又派发回来，于是 ``sync -> Configure -> sync`` 无限
        递归，表现就是界面卡死、屏幕狂闪。
        """
        if self._syncing:
            return
        window = self._window
        if window is None or not window.winfo_exists():
            return
        self._syncing = True
        try:
            with contextlib.suppress(tk.TclError):
                # 优先用 DWM 的「外框」矩形：它含标题栏和边框，正好是主窗口
                # 在屏幕上占的那一块。只拿客户区的话，标题栏那 38px 会露出来。
                bounds = self._frame_bounds()
                if bounds is not None:
                    left, top, right, bottom = bounds
                else:
                    width = self.master.winfo_width()
                    height = self.master.winfo_height()
                    left = self.master.winfo_rootx()
                    top = self.master.winfo_rooty()
                    right = left + width
                    bottom = top + height
                width = right - left
                height = bottom - top
                if width <= 1 or height <= 1:
                    return
                # 四周再往里收 1 个逻辑像素：DWM 的外框含阴影边，主窗口的
                # 抗锯齿边缘也可能差半个像素，收紧一点就不会在边上露出来。
                # 毛玻璃模式的窗口自带 WS_THICKFRAME，set_glass_geometry
                # 已经按边框差校正过，再收一次会整体偏移，所以跳过。
                inset = 0 if self.glass else self._inset()
                if width > inset * 2 + 1 and height > inset * 2 + 1:
                    left += inset
                    top += inset
                    width -= inset * 2
                    height -= inset * 2
                # 往外扩：底层窗口比主窗口大一圈，露出来的就是这圈底色。
                if self.spread:
                    extra = int(round(self.spread * self._scaling()))
                    left -= extra
                    top -= extra
                    width += extra * 2
                    height += extra * 2
                # frame=True 补了 WS_THICKFRAME，客户区会被非客户区吃掉，
                # 必须按边框差校正一次，否则窗口只有一条边。
                set_glass_geometry(window, width, height, left, top)
                if (width, height) != self._region_size:
                    self._region_size = (width, height)
                    set_round_region(
                        window,
                        self._radius(),
                        window.winfo_width(),
                        window.winfo_height(),
                    )
        finally:
            self._syncing = False

    def _scaling(self) -> float:
        """主窗口当前的 DPI 缩放（取不到就按 1.0）。"""
        with contextlib.suppress(Exception):
            return float(self.master._get_window_scaling() or 1.0)
        return 1.0

    def _radius(self) -> int:
        """主窗口的圆角半径（物理像素）。默认按 Win11 的 8 逻辑像素算。"""
        return int(round(8 * self._scaling()))

    def _inset(self) -> int:
        """四周内缩的像素数（物理像素），按 1 逻辑像素算。"""
        return max(1, int(round(1 * self._scaling())))

    def _frame_bounds(self) -> Optional[tuple[int, int, int, int]]:
        """主窗口在屏幕上的外框矩形 ``(左, 上, 右, 下)``，拿不到返回 ``None``。"""
        probe = getattr(self.master, "frame_bounds", None)
        if callable(probe):
            with contextlib.suppress(Exception):
                bounds = probe()
                if bounds is not None:
                    return bounds  # type: ignore[no-any-return]
        return None

    # ------------------------------------------------------------------ 内部
    def _ensure(self) -> None:
        window = self._window
        if window is not None and window.winfo_exists():
            return
        window = tk.Toplevel(self.master)
        window.overrideredirect(True)
        window.configure(bg=self.color)
        self._window = window
        self.apply_glass()
        for sequence, handler in (
            ("<Configure>", self._on_master_configure),
            ("<Map>", self._on_master_map),
            ("<Unmap>", self._on_master_unmap),
        ):
            funcid = self.master.bind(sequence, handler, add="+")
            if funcid:
                self._bindings.append((sequence, funcid))
        self._keep_behind()

    def _keep_behind(self) -> None:
        """把主窗口提到前面，这一层自然就压在下面。

        只在显示 / 重建时调一次：每次同步都 ``lift`` 会让窗口反复重排，
        看起来就是闪。
        """
        window = self._window
        if window is None:
            return
        # ``lower(belowThis)`` 不接受参数（那是 Canvas/place 的签名），
        # 传了主窗口会抛 TclError 被吞掉，于是这层一直盖在主窗口上面。
        with contextlib.suppress(tk.TclError):
            window.lower()
        with contextlib.suppress(tk.TclError):
            self.master.lift()

    def _restore_focus(self) -> None:
        """把焦点还给主窗口（建底层窗口会顺手把激活窗口切过去）。"""
        with contextlib.suppress(tk.TclError):
            self.master.focus_force()

    def _schedule(self) -> None:
        if self._poll is not None:
            return
        self._poll = self.master.after(POLL_MS, self._tick)

    def _tick(self) -> None:
        self._poll = None
        if self._window is None:
            return
        if self._visible:
            with contextlib.suppress(tk.TclError):
                self.sync()
        with contextlib.suppress(tk.TclError):
            self._poll = self.master.after(POLL_MS, self._tick)

    def _on_master_configure(self, event: tk.Event) -> None:
        if event.widget is self.master and self._visible:
            self.sync()

    def _on_master_map(self, event: tk.Event) -> None:
        if event.widget is self.master:
            self.show()

    def _on_master_unmap(self, event: tk.Event) -> None:
        if event.widget is self.master:
            self.hide()
