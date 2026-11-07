"""多页面窗口的页面管理与按页重建。

带侧边栏的桌面程序通常是「一堆页面叠在同一个容器里，切页只换层级」。切外观时
如果把所有页面就地重绘，customtkinter 会在滚动容器、卡片这类嵌套很深的结构里
漏色；一次性全部重建又要好几秒。这个模块把「只重建正在看的那一页、其余页等
切过去再建」的套路封装好，配合 :func:`ctk_kit.theme.apply_appearance_fast` 使用。

页面必须放在同一个容器里、用 ``place`` 叠放（本模块自己会调 ``place``）。
"""

from __future__ import annotations

import time
import tkinter as tk
from typing import Callable, Dict, Optional, Sequence, Set

import customtkinter as ctk

from . import theming
from .page import set_prewarm
from .theme import apply_appearance_fast

# 建页函数：给页面名，返回一个已建好的页面容器。
PageFactory = Callable[[str], ctk.CTkFrame]

# 离开页面时的回调（比如把很长的列表缩回首屏）。
PageHook = Callable[[ctk.CTkFrame], None]

# ``switch(defer=True)`` 时延迟多久重建：一帧 16 ms 左右，
# 留够一次窗口合成的时间，好让「外壳已经换色」这一帧真的显示出来。
_DEFER_MS = 24

# 丢过页面之后，多少秒内不许后台预建把它们建回来。拖动往往是连着拖几下，
# 刚建完就再丢一遍纯属白费。
_PREWARM_PAUSE = 6.0


def _noop(*_args: object, **_kwargs: object) -> None:
    """占位回调：控件销毁前把定时轮询换成它。"""


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
        first_of: Optional[Callable[[str], int]] = None,
    ) -> None:
        """保存建页函数和页面名；页面容器在第一次显示时才建。

        参数:
            first_of: 可选回调 ``first_of(name) -> int``：返回页面的
                ``cards_first``。启动时 ``build_all`` 会跳过返回值 > 0 的页面，
                等用户第一次切过去再建。不传就建全部页面。
        """
        self._host = host
        self._factory = factory
        self._pages: list[str] = list(pages)
        self._on_hide = on_hide
        self._first_of = first_of
        self._frames: Dict[str, ctk.CTkFrame] = {}
        self._stale: Set[str] = set()
        self._current: Optional[str] = None
        self._prewarm_pending: list = []
        self._prewarm_job: Optional[str] = None
        self._prewarm_resume_at = 0.0

    # ------------------------------------------------------------------ 查询

    @property
    def pages(self) -> tuple:
        """页面名，按当前顺序（动态加页后会变）。"""
        return tuple(self._pages)

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

    def prewarm(self, names: Sequence[str]) -> None:
        """把还没建的页面先建好（不显示），下次切过去直接 ``lift``。

        只建不 ``place``：未显示的页面一旦 ``place`` 就会参与窗口布局，
        窗口一改尺寸十几页一起重排，启动后第一次拖动会卡好几秒。这里只
        想免掉「切过去时要等构造」的那一段。

        一页建完再建下一页：两页的分帧队列同时跑会互相抢时间片，
        正在看的页面就会一顿一顿的。
        """
        pending = [n for n in names if n not in self._frames and n in self._pages]
        if not pending:
            return
        # 刚丢过页面就别急着建回来：拖动结束后后台立刻重建，下一段拖动
        # 又得再销毁一遍，看起来就是「拖一下就卡一下」。
        if time.monotonic() < self._prewarm_resume_at:
            return
        self._prewarm_pending = pending
        self._prewarm_next()

    def cancel_prewarm(self) -> None:
        """放弃还在排队的相邻页预建（用户已经切页，别再抢主线程）。"""
        self._prewarm_pending = []
        job = self._prewarm_job
        self._prewarm_job = None
        if job is not None:
            try:
                self._host.after_cancel(job)
            except tk.TclError:
                pass

    def _prewarm_next(self) -> None:
        """建 ``_prewarm_pending`` 里的第一页，建完再约下一页。"""
        self._prewarm_job = None
        pending = self._prewarm_pending
        if not pending:
            return
        try:
            if not self._host.winfo_exists():
                return
        except tk.TclError:
            return
        name = pending.pop(0)
        set_prewarm(True)
        try:
            page = self._build(name)
        except Exception:  # noqa: BLE001 - 预建失败不该影响当前页
            page = None
        finally:
            set_prewarm(False)
        if not pending:
            return

        def later() -> None:
            """一页建完，留一帧给当前页上屏，再建下一页。"""
            self._prewarm_job = None
            try:
                self._prewarm_job = self._host.after(80, self._prewarm_next)
            except tk.TclError:
                self._prewarm_job = None

        if page is not None and hasattr(page, "when_built"):
            page.when_built(later)
        else:
            later()

    # ------------------------------------------------------------------ 建页

    def _build(self, name: str) -> ctk.CTkFrame:
        """建一页（不摆放），同时清掉它的过期标记。

        启动时 ``build_all`` 会把所有页都建出来，但只应该显示当前页；
        如果这里顺手 ``place``，其余十几页虽然在底层看不见，窗口一改尺寸
        仍会跟着重排——启动后第一次拖动因此要好几秒。摆放留给
        :meth:`show` / :meth:`rebuild`。
        """
        page = self._factory(name)
        self._frames[name] = page
        self._stale.discard(name)
        # 新页用的是当前令牌，记下版本号，切回来时不用再补刷
        page._painted_version = theming.color_version()
        return page

    def hidden_roots(self) -> list:
        """已经建好、但当前没在显示的页面容器。

        换色时把它们交给 :func:`ctk_kit.theming.apply_palette` 的 ``skip``，
        省掉看不见那部分的遍历；切过去时按版本号补刷。
        """
        roots = []
        current = self._current
        for name, page in self._frames.items():
            if name == current:
                continue
            try:
                # 切页只改 z 序，隐藏页也保持 place，不能再用 winfo_manager
                # 判断可见性。
                if page.winfo_exists():
                    roots.append(page)
            except Exception:  # noqa: BLE001 - 页面正在销毁
                continue
        return roots

    def drop_hidden(self) -> int:
        """把除了当前页以外的页面全部销毁，返回销毁的页数。

        拖动窗口边框改尺寸时，已经建好的每一页都要跟着重排一次，打开过的
        页面越多越卡。这里干脆把看不见的页扔掉——切回去时按需重建，用一次
        构建换整段拖动的流畅。

        只销毁控件，不碰 ``self._pages`` 的页面定义，所以重建随时可以发生。
        """
        dropped = 0
        for name, page in list(self._frames.items()):
            if name == self._current:
                continue
            # 页面工厂理论上返回新容器，但真有工厂返回传进去的 host 时，
            # 这一刀会把整个页面区连根拔掉，切回去就报 bad window path name。
            if page is self._host:
                continue
            self._call_hook(page, "on_hide")
            self._stop_page_polling(page)
            # 走 Tcl 一次性销毁整棵子树：逐控件调 Python 的 destroy 时，
            # 一页 500 个控件要上百毫秒，十几页就是好几秒。
            try:
                self._host.tk.call("destroy", page._w)
            except Exception:  # noqa: BLE001 - 回退到逐个销毁
                try:
                    page.destroy()
                except Exception:  # noqa: BLE001 - 已经在别处销毁了
                    pass
            self._frames.pop(name, None)
            dropped += 1
        if dropped:
            # 后台预建会把刚丢掉的页面又建回来，这里连它也按住几秒。
            self.cancel_prewarm()
            self._prewarm_resume_at = time.monotonic() + _PREWARM_PAUSE
        return dropped

    def build_all(
        self,
        progress: Optional[Callable[[int, int, str], None]] = None,
        *,
        names: Optional[Sequence[str]] = None,
    ) -> None:
        """预建页面（启动时用），可逐页汇报进度。

        默认把所有页面都建出来。``first_of(name) > 0`` 的页面会被跳过：这类
        页面自己把卡片分成「前几张同步、其余分帧」，启动时建它反而会把遮罩
        拖住，等第一次 :meth:`show` 时再建。

        只想要启动时先建当前页、其余页等用户切过去再建，就传
        ``names=[当前页]``——遮罩因此不用等十几页。

        参数:
            progress: 可选回调 ``progress(done, total, name)``；每建完一页
                调用一次，用来驱动启动遮罩的进度条。
            names: 只预建这些页面；不传则按上面的默认规则建全部。
        """
        def deferred(name: str) -> bool:
            """这页是否留到第一次显示时再建。"""
            if self._first_of is None:
                return False
            try:
                return self._first_of(name) > 0
            except Exception:  # noqa: BLE001 - 读不到就当成普通页面
                return False

        if names is None:
            candidates = [name for name in self._pages if not deferred(name)]
            if not candidates:
                # 页面全都改成「第一次显示再建」了（``cards_first > 0``）：
                # 至少把当前页建出来，否则启动后是一片空白。
                seed = self._current or (self._pages[0] if self._pages else None)
                candidates = [seed] if seed else []
        else:
            # 显式点名时不做 deferred 过滤：调用方要建就建
            candidates = [name for name in names if name in self._pages]

        total = len(candidates)
        for index, name in enumerate(candidates, start=1):
            if name not in self._frames:
                self._build(name)
            if progress is not None:
                # 先把这一页和进度条画出来，再建下一页；否则构建期间
                # 事件循环被连续占用，遮罩会一直停在旧进度上。
                self._host.update_idletasks()
                progress(index, total, name)

    def add_page(self, name: str) -> None:
        """追加一个页面名；页面本身等第一次 :meth:`show` / :meth:`frame` 时再建。

        参数:
            name: 页面名，必须还没注册过。
        """
        if name in self._pages:
            raise ValueError(f"页面已存在：{name!r}")
        self._pages.append(name)

    def remove_page(self, name: str) -> None:
        """移除一个页面并销毁它的容器。

        参数:
            name: 页面名。不能是当前正在显示的页面——先切到别的页再删。

        异常:
            ValueError: 页面不存在，或者它当前正被显示。
        """
        if name not in self._pages:
            raise ValueError(f"未知页面：{name!r}；可选 {list(self._pages)}")
        if name == self._current:
            raise ValueError(f"不能删除正在显示的页面：{name!r}；先切到别的页")
        page = self._frames.pop(name, None)
        if page is not None:
            try:
                page.destroy()
            except Exception:  # noqa: BLE001 - 已经在别处销毁了
                pass
        self._pages.remove(name)
        self._stale.discard(name)

    @staticmethod
    def _stop_page_polling(page: tk.Misc) -> None:
        """停掉页内控件自己排的定时轮询。

        customtkinter 的 ``CTkTextbox`` 用 ``after(50)`` 反复检查滚动条，
        销毁时不取消；整棵子树被 Tcl 一次拔掉后，下一拍就会撞上
        ``invalid command name``。先把入口换成空函数，回调再触发也只是
        什么都不做。
        """
        try:
            widgets = list(theming._walk(page))
        except Exception:  # noqa: BLE001 - 页面已经不可遍历
            return
        for widget in widgets:
            if callable(getattr(widget, "_check_if_scrollbars_needed", None)):
                try:
                    widget._check_if_scrollbars_needed = _noop
                except Exception:  # noqa: BLE001 - 只读属性之类的
                    pass

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
        page._painted_version = theming.color_version()
        page.place(relx=0, rely=0, relwidth=1, relheight=1)
        if visible:
            page.lift()
        else:
            page.lower()
        if old is not None:
            self._call_hook(old, "on_hide")
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
        # 用户已经在切页了，后台排队建的邻居页先让开主线程。
        self.cancel_prewarm()
        if name in self._stale:
            self.rebuild(name)
        elif name not in self._frames:
            self._build(name)

        page = self._frames[name]
        # 换色时只刷了当时可见的页，这一页可能还停在旧色上；按版本号补一次。
        if getattr(page, "_painted_version", -1) != theming.color_version():
            theming.repaint_page(page)
            page._painted_version = theming.color_version()
        self._swap(page, name)
        return page

    def _swap(self, page: ctk.CTkFrame, name: str) -> None:
        """把 ``page`` 摆到最上层，其它页压到下面。"""
        if page.winfo_manager() != "place":
            # 首次显示（或外部把页面拿掉了）：摆满父容器并等布局完成
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            try:
                page.update_idletasks()
            except Exception:  # noqa: BLE001 - 控件可能在回调里被销毁
                pass
        else:
            # 它上一轮可能被当成后台页钉成了固定像素尺寸，切回来要恢复跟随窗口。
            page.place_configure(
                relx=0, rely=0, relwidth=1, relheight=1, width=0, height=0
            )
        # 已经 place 过的页面直接抬到最上层即可：重复 place 会触发页面内
        # 重新布局，切页就多花几十毫秒。
        page.lift()
        self._current = name

        try:
            width = max(1, self._host.winfo_width())
            height = max(1, self._host.winfo_height())
        except tk.TclError:
            width = height = 1

        for other in list(self._frames.values()):
            if other is page:
                continue
            try:
                if other.winfo_manager() != "place":
                    continue
                # 切页只改 z 序，不把旧页从布局里摘掉：place_forget 会让
                # 旧页的窗口立刻消失，父容器收到重绘请求时新页可能还没画
                # 完，中间那一帧就会露出横条。留在栈里压下去，整块画面由
                # 系统一次性合成。
                #
                # 但留在栈里的页要钉成固定像素尺寸：``relwidth=1`` 会让
                # 十几页都跟着窗口 resize 重排，拖拽窗口时肉眼可见地卡。
                other.place_configure(
                    relwidth=0, relheight=0, width=width, height=height
                )
                other.lower()
            except tk.TclError:
                continue
            if self._on_hide is not None:
                try:
                    self._on_hide(other)
                except Exception:  # noqa: BLE001 - 钩子不该打断切页
                    pass
            self._call_hook(other, "on_hide")
        # 先让旧页收尾，再通知新页「已经上场」，顺序符合直觉。
        self._call_hook(page, "on_show")

    @staticmethod
    def _call_hook(page: tk.Misc, name: str) -> None:
        """调用页面自己的 ``on_show`` / ``on_hide`` 钩子；没定义就跳过。

        钩子抛异常不打断切页，异常只影响这个钩子本身。
        """
        hook = getattr(page, name, None)
        if callable(hook):
            try:
                hook()
            except Exception:  # noqa: BLE001 - 钩子不该打断切页
                pass

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
            """执行 ``after_rebuild`` 回调；延迟重建时也用它收尾。"""
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
            """延迟到下一帧再重建当前页；期间若已重建就跳过。"""
            if name in self._stale:
                self.rebuild(name)
            finish()

        # 一帧 16 ms 左右：留够一次合成的时间，让「底色已换」真的被人看见
        schedule(_DEFER_MS, rebuild_later)
