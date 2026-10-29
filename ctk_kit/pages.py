"""多页面窗口的页面管理与按页重建。

带侧边栏的桌面程序通常是「一堆页面叠在同一个容器里，切页只换层级」。切外观时
如果把所有页面就地重绘，customtkinter 会在滚动容器、卡片这类嵌套很深的结构里
漏色；一次性全部重建又要好几秒。这个模块把「只重建正在看的那一页、其余页等
切过去再建」的套路封装好，配合 :func:`ctk_kit.theme.apply_appearance_fast` 使用。

页面必须放在同一个容器里、用 ``place`` 叠放（本模块自己会调 ``place``）。
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, Optional, Sequence, Set

import customtkinter as ctk

from .theme import apply_appearance_fast

# 建页函数：给页面名，返回一个已建好的页面容器。
PageFactory = Callable[[str], ctk.CTkFrame]

# 离开页面时的回调（比如把很长的列表缩回首屏）。
PageHook = Callable[[ctk.CTkFrame], None]

# ``switch(defer=True)`` 时延迟多久重建：一帧 16 ms 左右，
# 留够一次窗口合成的时间，好让「外壳已经换色」这一帧真的显示出来。
_DEFER_MS = 24


class PageRebuilder:
    """管理一组页面，并按需重建某一页。

    典型用法::

        self.pages = PageRebuilder(self.body, self._build_page, PAGES)

        def _build_page(self, name):
            return PAGES[name].build(self.body)

        def switch_theme(self, mode):
            apply_appearance_fast(mode, window=self)   # 先切全局外观
            self.pages.switch()                        # 再重建当前页

    参数:
        host: 所有页面共用的父容器。
        factory: 建页函数 ``factory(name) -> CTkFrame``，由调用方决定这一页长什么样。
        pages: 页面名序列，顺序只用于遍历，不影响显示。
        on_hide: 可选回调，页面被切走时调用一次，参数是那个页面容器。
    """

    def __init__(
        self,
        host: tk.Misc,
        factory: PageFactory,
        pages: Sequence[str],
        *,
        on_hide: Optional[PageHook] = None,
    ) -> None:
        self._host = host
        self._factory = factory
        self._pages = tuple(pages)
        self._on_hide = on_hide
        self._frames: Dict[str, ctk.CTkFrame] = {}
        self._stale: Set[str] = set()
        self._current: Optional[str] = None

    # ------------------------------------------------------------------ 查询

    @property
    def pages(self) -> tuple:
        """页面名，按构造时给的顺序。"""
        return self._pages

    @property
    def current(self) -> Optional[str]:
        """当前显示的页面名；还没 ``show`` 过时是 ``None``。"""
        return self._current

    @property
    def frames(self) -> Dict[str, ctk.CTkFrame]:
        """页面名到容器的映射（只含已经建出来的页面）。"""
        return self._frames

    @property
    def stale(self) -> Set[str]:
        """外观变过、配色还是旧的那批页面名。"""
        return set(self._stale)

    def frame(self, name: str) -> ctk.CTkFrame:
        """取某一页的容器，没建就建一个（但不显示）。"""
        if name not in self._frames:
            self._build(name)
        return self._frames[name]

    # ------------------------------------------------------------------ 建页

    def _stack(self, page: ctk.CTkFrame) -> None:
        """把页面铺满父容器并压到最底层。"""
        page.place(relx=0, rely=0, relwidth=1, relheight=1)
        page.lower()

    def _build(self, name: str) -> ctk.CTkFrame:
        page = self._factory(name)
        self._frames[name] = page
        self._stack(page)
        self._stale.discard(name)
        return page

    def build_all(self) -> None:
        """把所有页面都建出来（启动时用；页面多的话会有点慢）。"""
        for name in self._pages:
            if name not in self._frames:
                self._build(name)

    def rebuild(self, name: str) -> ctk.CTkFrame:
        """按当前外观重建一页：先建新页挂好，再销毁旧页。

        必须「先建后销」而不是当场 ``destroy`` 再建：customtkinter 的
        ``CTkScrollableFrame`` 在 ``__init__`` 里挂了 ``bind_all`` 全局绑定，
        在回调里销毁控件会让事件继续派发给已销毁的控件
        （``bad window path name``）。

        参数:
            name: 页面名。

        返回:
            新建好的页面容器。
        """
        if name not in self._pages:
            raise ValueError(f"未知页面：{name!r}；可选 {list(self._pages)}")

        old = self._frames.get(name)
        visible = old is not None and old.winfo_manager() == "place" and (
            self._current == name
        )
        page = self._factory(name)
        self._frames[name] = page
        page.place(relx=0, rely=0, relwidth=1, relheight=1)
        if visible:
            page.lift()
        else:
            page.lower()
        if old is not None:
            try:
                old.destroy()
            except Exception:  # noqa: BLE001 - 已经在别处销毁了
                pass
        self._stale.discard(name)
        # 立刻排版一次，省得新页先以 0 尺寸显示、再跳一下
        try:
            page.update_idletasks()
        except Exception:  # noqa: BLE001 - 控件可能在回调里被销毁
            pass
        return page

    # ------------------------------------------------------------------ 切页

    def show(self, name: str) -> ctk.CTkFrame:
        """显示某一页；如果这页的配色过期了，先重建它。

        参数:
            name: 页面名。

        返回:
            被显示的页面容器。
        """
        if name not in self._pages:
            raise ValueError(f"未知页面：{name!r}；可选 {list(self._pages)}")
        if name in self._stale:
            self.rebuild(name)
        elif name not in self._frames:
            self._build(name)

        page = self._frames[name]
        page.place(relx=0, rely=0, relwidth=1, relheight=1)
        page.lift()
        self._current = name

        for key, other in self._frames.items():
            if other is page or other.winfo_manager() != "place":
                continue
            other.place_forget()
            if self._on_hide is not None:
                try:
                    self._on_hide(other)
                except Exception:  # noqa: BLE001 - 钩子不该打断切页
                    pass
        return page

    # -------------------------------------------------------------- 切外观

    def mark_stale(self) -> None:
        """把所有页标成「配色过期」，下次切过去时重建。"""
        self._stale = set(self._pages)

    def switch(
        self,
        mode: str,
        *,
        window: Optional[tk.Misc] = None,
        before_rebuild: Optional[Callable[[], None]] = None,
        after_rebuild: Optional[Callable[[], None]] = None,
        defer: bool = False,
    ) -> None:
        """切外观：更新全局配色，然后重建当前页。

        其余页面只打「过期」标记，等用户切过去时由 :meth:`show` 补建——Tk 是
        单线程的，连着重建十页会让窗口僵住一秒多，比原来的全量重绘还难受。

        参数:
            mode: ``"light"`` / ``"dark"`` / ``"system"``。
            window: 传了就把这个窗口的底色和标题栏一起刷（通常就是主窗口）。
            before_rebuild: 重建当前页之前调一次。适合处理「比页面还该先变」的
                东西，比如窗口边框、大面积底纹。
            after_rebuild: 重建之后再调一次。侧边栏、状态栏这类「不属于任何页面」
                的容器放这里：页面占了整块视觉重心，先让它整体换掉，外壳随后
                跟上，比反过来自然。
            defer: 把当前页的重建推迟到下一个事件循环。整个 ``switch`` 是同步的，
                换完底色到重建完成之间窗口根本没有机会重绘；置 ``True`` 可以让
                「底色已换」这一帧真正上屏之后再重建页面（多花一帧，约二十毫秒）。
        """
        apply_appearance_fast(mode, window=window)
        if before_rebuild is not None:
            before_rebuild()
        self.mark_stale()
        name = self._current

        def finish() -> None:
            if after_rebuild is not None:
                after_rebuild()

        if name is None:
            finish()
            return
        if not defer:
            self.rebuild(name)
            finish()
            return
        host = self._host
        schedule = getattr(host, "after", None)
        if not callable(schedule):
            self.rebuild(name)
            finish()
            return

        def rebuild_later() -> None:
            if name in self._stale:
                self.rebuild(name)
            finish()

        # 一帧 16 ms 左右：留够一次合成的时间，让「底色已换」真的被人看见
        schedule(_DEFER_MS, rebuild_later)
