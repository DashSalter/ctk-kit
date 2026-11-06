"""页面基类：统一初始化，UI 类和事件类都从这里开始。"""

from __future__ import annotations

import time
import tkinter as tk
from typing import Callable, Iterable, List, Optional

from . import tokens as T
from .frames import Frame

#: 分帧构建每个时间片的预算（秒）。单张卡片超过它时这一帧会被撑长，
#: 但至少保证队列会推进一张，不会卡死。
_BUILD_SLICE = 0.012

#: 预建模式：相邻页在后台建时不占用当前帧，全部卡片排队，
#: 否则预建会把正在看的页面卡住半秒。
_PREWARM = False


def set_prewarm(enabled: bool) -> None:
    """打开/关闭预建模式（只影响 ``build_cards`` 的同步建卡数量）。"""
    global _PREWARM
    _PREWARM = bool(enabled)


class PageBase(Frame):
    """所有页面的公共基类。

    统一在这里拿到根窗口（``App``）；主题、日志、用户信息等全局初始化
    也可以放在这里。子类只负责建界面，事件类再实现 :meth:`bind_events`。

    组件多的页面用 :meth:`build_cards` 并声明 ``cards_first = 3``：
    启动时这页整页跳过，第一次切过去才建；页内前 3 张同步出现，其余按
    12ms 时间片补建，不会为了最后几张卡片把切页拖住。
    """

    #: 页内分帧：0 = 整页同步建；N > 0 = 前 N 张同步、其余分帧。
    #: 默认 1：首次切过去先出页头和第一张卡片，剩下的按时间片补建，
    #: 不会为了一张大页面把整个窗口冻住。启动遮罩会跳过这样的页面，
    #: 第一次切过去时再建。
    cards_first: int = 1

    def __init__(self, master: tk.Misc) -> None:
        """建页面容器，并把根窗口存到 ``self.app``。"""
        # 页面用不透明底色：切页时新页 place 上来先盖住旧页，旧页再撤，
        # 中间不会露出父容器的黑色底。
        super().__init__(master, fg_color=T.COLOR_BG)
        self.app = master.winfo_toplevel()
        self._build_queue: List[Callable[[], None]] = []
        self._build_job: Optional[str] = None
        self._built_callbacks: List[Callable[[], None]] = []

    # ------------------------------------------------------------ 分帧构建

    def build_cards(self, area, builders: Iterable[Callable[..., None]], *, first: Optional[int] = None) -> None:
        """按顺序建一组卡片：前 ``first`` 张同步，其余分帧。

        页面只给出顺序，不用逐条写 :meth:`build_later`::

            self.build_cards(area, [
                self._build_badges,
                self._build_tooltip,
                self._build_pagination,
                ...
            ])

        参数:
            area: 卡片挂载的容器（通常是 ``Scrollable``）。
            builders: 依次调用的构建函数，每个收到 ``area``。
            first: 同步构建的张数；不传就用类上的 ``cards_first``
                （0 表示整页同步建）。
        """
        builders = list(builders)
        if first is None:
            first = self.cards_first
        if _PREWARM:
            # 预建：一张都不同步建，全部交给时间片，别卡住当前页
            first = 0
        elif first <= 0:
            first = len(builders)
        for builder in builders[:first]:
            builder(area)
        for builder in builders[first:]:
            self.build_later(builder, area)

    def build_later(self, builder: Callable[..., None], *args, **kwargs) -> None:
        """把一段构建任务排到后续事件循环里执行。

        每个时间片最多占用约 12 ms，建完一段还有剩余时间就继续建下一段，
        所以一帧里可能补好几张卡片。页面销毁后队列自动停止。

        参数:
            builder: 建控件的函数，通常是 ``self._build_xxx``。
            *args / **kwargs: 原样传给 ``builder``。
        """
        if not self.winfo_exists():
            return
        self._build_queue.append(lambda: builder(*args, **kwargs))
        if self._build_job is None:
            self._suspend_scrollbars()
            self._build_job = self.after(1, self._run_build_step)

    def when_built(self, callback: Callable[[], None]) -> None:
        """所有排队任务都完成后调用一次 ``callback``。

        队列已经空了就立刻调用；构建被销毁打断时回调不会执行。
        可以登记多个回调，按登记顺序依次调用（比如事件绑定之外还要
        在建完后刷新一次页面状态）。
        """
        if not self._build_queue and self._build_job is None:
            callback()
            return
        self._built_callbacks.append(callback)

    def _alive(self) -> bool:
        """页面窗口还在不在；根窗口已经销毁时 ``winfo_exists`` 自己会抛。"""
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def _run_build_step(self) -> None:
        """在一个时间片里尽量多建几张卡，然后让出一帧。

        预算（``_BUILD_SLICE``）用完就让出，避免一帧占住事件循环太久；
        至少建一张，所以单张卡片超预算时队列仍会推进。
        """
        self._build_job = None
        if not self._alive() or not self._build_queue:
            self._finish_build()
            return
        deadline = time.perf_counter() + _BUILD_SLICE
        try:
            while self._build_queue:
                self._build_queue.pop(0)()
                if time.perf_counter() >= deadline:
                    break
        except tk.TclError:
            # 页面在构建中途被销毁：剩下的任务没有意义了
            self._build_queue.clear()
            self._resume_scrollbars()
            return
        # 这里不调 update_idletasks：after 回调返回后 Tk 自己会跑一次 idle，
        # 布局和重绘就在那一轮完成。手动更新会让每张卡片都排一次布局，
        # 分帧反而比同步建更慢（实测输入页 660ms → 1037ms）。
        if not self._alive():
            self._build_queue.clear()
            return
        if self._build_queue:
            self._build_job = self.after(1, self._run_build_step)
        else:
            self._finish_build()

    def _finish_build(self) -> None:
        """分帧队列清空：恢复滚动条并回调 ``when_built``。"""
        if not self._alive():
            self._build_queue.clear()
            return
        self._resume_scrollbars()
        callbacks, self._built_callbacks = self._built_callbacks, []
        for callback in callbacks:
            callback()

    def _walk_scrollables(self):
        """递归找出页面里的滚动容器（按 duck typing，不依赖 layout）。"""
        def walk(widget):
            for child in widget.winfo_children():
                if hasattr(child, "suspend_scrollbar"):
                    yield child
                else:
                    yield from walk(child)

        yield from walk(self)

    def _suspend_scrollbars(self) -> None:
        """分帧构建期间冻结页面内滚动条的重绘。"""
        for scrollable in self._walk_scrollables():
            try:
                scrollable.suspend_scrollbar()
            except tk.TclError:
                pass

    def _resume_scrollbars(self) -> None:
        """构建结束，恢复滚动条并补画一次。"""
        for scrollable in self._walk_scrollables():
            try:
                scrollable.resume_scrollbar()
            except tk.TclError:
                pass

    def destroy(self) -> None:
        """销毁页面时取消还没跑完的构建任务。"""
        if self._build_job is not None:
            try:
                self.after_cancel(self._build_job)
            except tk.TclError:
                pass
            self._build_job = None
        self._build_queue.clear()
        self._built_callbacks.clear()
        try:
            self._resume_scrollbars()
        except tk.TclError:
            # 父窗口先一步销毁时遍历控件树会抛，退出路径上忽略
            pass
        super().destroy()

    def bind_events(self) -> None:
        """建议实现：在这里注册按钮和事件绑定。

        只是约定，不是强制；不需要绑定的页面保持空实现即可。
        """

    def on_show(self) -> None:
        """页面被切到前台时调用（默认什么都不做，按需覆写）。

        适合刷新数据、恢复滚动位置这类「每次露面都要做」的事。此时页面已经
        摆放好、尺寸也更新过了。
        """

    def on_hide(self) -> None:
        """页面被切走、或按当前外观要被重建销毁之前调用（默认什么都不做）。

        适合停掉定时器、收起很长的列表这类「离开时省点资源」的事。
        """
