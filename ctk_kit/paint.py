"""PIL 绘制缓存：固定样式的图只画一次，多个组件共用。

缓存的是 ``PIL.Image``，它不绑定 Tk root；组件拿到图后自己包
``CTkImage`` / ``ImageTk.PhotoImage``（这两类对象和窗口、DPI 绑定，不能
跨窗口复用）。返回的图是共享的，调用方不要原地修改。

进度值、滑块位置这类每帧都变的图不要走这里：缓存键会随数值无限增长。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, List

#: 最多缓存多少张图；键由绘制参数组成，一般页面远用不到。
_CACHE_SIZE = 256

#: 所有被装饰过的绘制函数，``clear()`` 时统一清空。
_WRAPPERS: List[Any] = []


def cached(fn: Callable[..., Any]) -> Callable[..., Any]:
    """给绘制函数加全局 LRU 缓存；参数必须可哈希。

    用法::

        @cached
        def _icon(color: str):
            ...
    """
    wrapper = lru_cache(maxsize=_CACHE_SIZE)(fn)
    _WRAPPERS.append(wrapper)
    return wrapper


def clear() -> None:
    """清空绘制缓存（测试结束或要释放内存时调用）。"""
    for wrapper in _WRAPPERS:
        wrapper.cache_clear()


class ColorAnimation:
    """一次颜色渐变的句柄；调用 :meth:`cancel` 可以停在当前帧。"""

    def __init__(self, widget: Any, option: str) -> None:
        self.widget = widget
        self.option = option
        self._job: Any = None
        self._cancelled = False

    def cancel(self) -> None:
        """停止后续帧；已经画上去的颜色不会回滚。"""
        self._cancelled = True
        if self._job is not None:
            try:
                self.widget.after_cancel(self._job)
            except Exception:  # noqa: BLE001 - 控件可能已经销毁
                pass
            self._job = None


def _hex_to_rgb(value: str):
    """``#rrggbb`` 转三元组；不是 6 位十六进制就抛 ``ValueError``。"""
    text = value.lstrip("#")
    if len(text) != 6:
        raise ValueError(f"不是 #rrggbb 颜色：{value!r}")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def _blend(start, end, ratio: float) -> str:
    """两个 RGB 三元组按比例混合，返回 ``#rrggbb``。"""
    red, green, blue = (
        round(start[i] + (end[i] - start[i]) * ratio) for i in range(3)
    )
    return f"#{red:02x}{green:02x}{blue:02x}"


def _set_color(widget: Any, option: str, color: str) -> None:
    try:
        widget.configure(**{option: color})
    except Exception:  # noqa: BLE001 - 控件可能已经销毁
        pass


def animate_color(
    widget: Any,
    option: str,
    start: str,
    end: str,
    duration: int = 150,
    fps: int = 30,
) -> ColorAnimation:
    """把控件的某个颜色选项从 ``start`` 渐变到 ``end``（``#rrggbb``）。

    参数:
        widget: 任意 tk / CTk 控件。
        option: 要改的选项名，例如 ``"fg_color"``、``"text_color"``、
            ``"bg"``。
        start / end: 起止颜色，``#rrggbb``；不是 6 位十六进制时直接跳到
            ``end``，不做动画。
        duration: 总时长（毫秒），默认 150。
        fps: 帧率，默认 30（150ms 约 5 帧，足够看出过渡）。

    返回:
        :class:`ColorAnimation`；同一控件同一选项再调一次会先取消上一次，
        不会叠加两套定时器。

    注意:
        渐变期间每帧都会 ``configure``，颜色选项会短暂变成动画值；不要在
        动画中途读 ``cget`` 推断「主题色」。
    """
    animation = ColorAnimation(widget, option)

    # 同一控件、同一选项只保留一个动画
    jobs = getattr(widget, "_ctk_kit_color_jobs", None)
    if jobs is None:
        jobs = {}
        setattr(widget, "_ctk_kit_color_jobs", jobs)
    previous = jobs.get(option)
    if previous is not None:
        previous.cancel()

    try:
        start_rgb = _hex_to_rgb(start)
        end_rgb = _hex_to_rgb(end)
    except ValueError:
        _set_color(widget, option, end)
        return animation

    if start.lower() == end.lower():
        _set_color(widget, option, end)
        return animation

    frames = max(1, int(round(duration / 1000 * fps)))
    delay = max(10, int(round(1000 / fps)))
    jobs[option] = animation

    def step(index: int) -> None:
        if animation._cancelled:
            return
        _set_color(widget, option, _blend(start_rgb, end_rgb, index / frames))
        if index < frames:
            animation._job = widget.after(delay, lambda: step(index + 1))
        else:
            animation._job = None
            jobs.pop(option, None)

    step(0)
    return animation
