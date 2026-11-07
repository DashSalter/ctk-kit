"""勾选框与单选圆点：用 Pillow 画抗锯齿的指示符。

ttkbootstrap 的 ``Checkbutton`` / ``Radiobutton`` 指示符是**图片**：它把资源里的
PNG 重新着色后交给 ttk 的 image element。Tk 自己用 canvas 画圆环时不做抗锯齿，
圆形边缘就会有一格一格的阶梯，这里照同样的思路，用 Pillow 在 4 倍尺寸上画好再缩回来。
"""

from __future__ import annotations

import contextlib
import time
import tkinter as tk
from typing import Any, Callable, Dict, List, Optional, Tuple

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font
from .paint import blend_hex, cached
from .sugar import Enablable, Textual
from .theme import color_of

try:  # Pillow 是可选依赖
    from PIL import Image, ImageDraw, ImageTk

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

#: 超采样倍数。
_SCALE = 4
#: 勾选/取消的「亮起」时长（毫秒）。
_MARK_ANIM_MS = 200
#: 动画帧间隔（毫秒）；按经过时间插值，Tk 定时器抖动不影响速度。
_MARK_ANIM_STEP = 16


def _bg_of(master: tk.Misc) -> str:
    """给 canvas 找一个实际背景色。"""
    try:
        value = master.cget("fg_color")
    except Exception:  # noqa: BLE001
        value = None
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return color_of(value)
    if isinstance(value, str) and value and value != "transparent":
        return value
    return color_of(T.COLOR_CARD)


@cached
def _round_image(size: int, checked: bool, color: str, track: str, foreground: str):
    """圆点：未选中是描边圆环，选中是实心圆加一个浅色内点。"""
    scale = _SCALE
    total = size * scale
    image = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pad = 1 * scale
    box = (pad, pad, total - pad - 1, total - pad - 1)
    if checked:
        pen.ellipse(box, fill=color)
        inner = total * 0.2
        center = total / 2
        pen.ellipse(
            (center - inner, center - inner, center + inner, center + inner),
            fill=foreground,
        )
    else:
        pen.ellipse(box, outline=track, width=2 * scale)
    return image.resize((size, size), Image.LANCZOS)


@cached
def _square_image(
    size: int, checked: bool, color: str, track: str, foreground: str
):
    """勾选框：未选中是圆角方框，选中是实心方块加一个白色对勾。"""
    scale = _SCALE
    total = size * scale
    image = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pad = 1 * scale
    box = (pad, pad, total - pad - 1, total - pad - 1)
    radius = max(2, int(total * 0.22))
    if checked:
        pen.rounded_rectangle(box, radius=radius, fill=color)
        width = max(2, int(total * 0.09))
        pen.line(
            [
                (total * 0.27, total * 0.52),
                (total * 0.44, total * 0.69),
                (total * 0.75, total * 0.33),
            ],
            fill=foreground,
            width=width,
            joint="curve",
        )
    else:
        pen.rounded_rectangle(box, radius=radius, outline=track, width=2 * scale)
    return image.resize((size, size), Image.LANCZOS)


def _square_image_at(
    size: int, progress: float, color: str, track: str, foreground: str
):
    """勾选框的中间帧：描边色向填充色过渡，填充和对勾按 ``progress`` 淡入。"""
    scale = _SCALE
    total = size * scale
    image = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pad = 1 * scale
    box = (pad, pad, total - pad - 1, total - pad - 1)
    radius = max(2, int(total * 0.22))
    pen.rounded_rectangle(
        box,
        radius=radius,
        outline=blend_hex(track, color, min(1.0, progress * 1.35)),
        width=2 * scale,
    )
    if progress <= 0:
        return image.resize((size, size), Image.LANCZOS)
    layer = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    inner = ImageDraw.Draw(layer)
    inner.rounded_rectangle(box, radius=radius, fill=color)
    inner.line(
        [
            (total * 0.27, total * 0.52),
            (total * 0.44, total * 0.69),
            (total * 0.75, total * 0.33),
        ],
        fill=foreground,
        width=max(2, int(total * 0.09)),
        joint="curve",
    )
    # 描边先亮、填充和对勾晚一点出来，比整块一起淡入更有层次
    fade = min(1.0, max(0.0, (progress - 0.12) / 0.88))
    alpha = layer.split()[3].point(lambda value: int(value * fade))
    layer.putalpha(alpha)
    return Image.alpha_composite(image, layer).resize((size, size), Image.LANCZOS)


def _round_image_at(
    size: int, progress: float, color: str, track: str, foreground: str
):
    """单选的中间帧：圆环色向填充色过渡，实心圆和浅色内点按进度淡入。"""
    scale = _SCALE
    total = size * scale
    image = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pad = 1 * scale
    box = (pad, pad, total - pad - 1, total - pad - 1)
    pen.ellipse(
        box,
        outline=blend_hex(track, color, min(1.0, progress * 1.35)),
        width=2 * scale,
    )
    if progress <= 0:
        return image.resize((size, size), Image.LANCZOS)
    layer = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    inner = ImageDraw.Draw(layer)
    inner.ellipse(box, fill=color)
    dot = total * 0.2
    center = total / 2
    inner.ellipse(
        (center - dot, center - dot, center + dot, center + dot), fill=foreground
    )
    # 圆环先变色，内点稍后再亮
    fade = min(1.0, max(0.0, (progress - 0.12) / 0.88))
    alpha = layer.split()[3].point(lambda value: int(value * fade))
    layer.putalpha(alpha)
    return Image.alpha_composite(image, layer).resize((size, size), Image.LANCZOS)


class _Mark(Enablable, Textual, ctk.CTkFrame):
    """勾选/单选共用的底座：左边一个指示符，右边一行字。"""

    _shape = "round"

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        *,
        width: int,
        height: int,
        command: Optional[Callable[[], None]],
        font: Any,
    ) -> None:
        """建底座：canvas 放指示符，label 放文字。"""
        super().__init__(master, fg_color="transparent")
        self._size = max(12, int(height))
        self._command = command
        self._bg = _bg_of(self)
        self._photo = None
        # 视觉进度（0=未选中、1=选中），动画期间与变量里的值不同步
        self._progress = 0.0
        self._anim_job: Optional[str] = None
        self._anim_from = 0.0
        self._anim_to = 0.0
        self._anim_started = 0.0
        # 程序性写变量时临时静音 trace，避免先把终态画出来再补间
        self._silent = False
        # 鼠标是否悬停在指示符/文字上：悬停时勾和圆点换成「悬停色」
        self._hover = False
        # 是否可用；禁用时文字变灰、点击无反应
        self._enabled = True

        self._canvas = tk.Canvas(
            self,
            width=self._size,
            height=self._size,
            bg=self._bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._canvas.pack(side="left")
        self._label = ctk.CTkLabel(
            self,
            text=text,
            font=font,
            text_color=T.COLOR_TEXT,
            fg_color="transparent",
            cursor="hand2",
        )
        self._label.pack(side="left", padx=(8, 0))
        for widget in (self._canvas, self._label):
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    # ------------------------------------------------------------ 悬停
    def _on_enter(self, _event: Any = None) -> None:
        """鼠标进来：勾 / 圆点换「悬停色」。"""
        if not getattr(self, "_enabled", True):
            return
        if not self._hover:
            self._hover = True
            self._refresh()

    def _on_leave(self, _event: Any = None) -> None:
        """鼠标离开：换回三级颜色。"""
        if self._hover:
            self._hover = False
            self._refresh()

    # ------------------------------------------------------------ 子类实现
    def _is_checked(self) -> bool:
        """子类给：当前是否选中。"""
        raise NotImplementedError

    def _set_checked(self, value: bool) -> None:
        """子类给：写入选中状态。"""
        raise NotImplementedError

    # ------------------------------------------------------------ 公共
    def _next_state(self) -> bool:
        """点击后的目标状态；单选框已选中时再点不会取消，子类覆盖。"""
        return not self._is_checked()

    def _variable_changed(self) -> None:
        """变量被外部改写时跟随；单选框切换时旧项也会淡出。"""
        if self._silent:
            return
        checked = 1.0 if self._is_checked() else 0.0
        if self._anim_job is not None or abs(checked - self._progress) > 0.001:
            self._animate_to(checked)
        else:
            self._refresh()

    def _on_click(self, _event: Optional[tk.Event] = None) -> None:
        """点击：切换选中状态并回调。"""
        if not getattr(self, "_enabled", True):
            return
        target = self._next_state()
        if target != self._is_checked():
            self._set_checked(target)
            self._animate_to(1.0 if target else 0.0)
        if self._command is not None:
            self._command()

    def _apply_enabled(self, enabled: bool) -> None:
        """禁用时文字变灰、指示符不再响应悬停与点击。"""
        self._enabled = bool(enabled)
        self._hover = False
        try:
            self._label.configure(
                text_color=T.COLOR_TEXT if enabled else T.COLOR_FAINT
            )
            cursor = "hand2" if enabled else ""
            self._canvas.configure(cursor=cursor)
            self._label.configure(cursor=cursor)
        except tk.TclError:
            return
        self._refresh()

    def set_text(self, text: Any) -> None:
        """改右侧文字（``CTkFrame`` 本身没有 ``text`` 选项，只能改 label）。"""
        self._label.configure(text=str(text))

    def get_text(self) -> str:
        """读回右侧文字。"""
        try:
            return str(self._label.cget("text"))
        except tk.TclError:
            return ""

    def apply_theme(self) -> None:
        """按当前令牌重画指示符（``theming`` 运行时换色后调用）。"""
        self._bg = _bg_of(self)
        try:
            self._canvas.configure(bg=self._bg)
        except tk.TclError:
            return
        self._refresh()

    def _refresh(self) -> None:
        """重画指示符；没有动画时直接画终态。"""
        self._canvas.delete("all")
        if self._anim_job is not None:
            self._paint(self._progress)
            return
        checked = self._is_checked()
        self._progress = 1.0 if checked else 0.0
        enabled = getattr(self, "_enabled", True)
        color = color_of(T.COLOR_ACTIVE) if enabled else color_of(T.COLOR_BORDER_STRONG)
        track = color_of(T.COLOR_BORDER_STRONG)
        foreground = color_of(T.COLOR_KNOB_HOVER if self._hover else T.COLOR_KNOB)
        if not _HAS_PIL:
            self._draw_plain(checked, color, track, foreground)
            return
        make = _round_image if self._shape == "round" else _square_image
        self._photo = ImageTk.PhotoImage(
            make(self._size, checked, color, track, foreground)
        )
        self._canvas.create_image(self._size / 2, self._size / 2, image=self._photo)

    def _paint(self, progress: float) -> None:
        """画一帧中间态；不走缓存，进度值会让缓存键无限增长。"""
        self._canvas.delete("all")
        enabled = getattr(self, "_enabled", True)
        color = color_of(T.COLOR_ACTIVE) if enabled else color_of(T.COLOR_BORDER_STRONG)
        track = color_of(T.COLOR_BORDER_STRONG)
        foreground = color_of(T.COLOR_KNOB_HOVER if self._hover else T.COLOR_KNOB)
        if not _HAS_PIL:
            self._draw_plain(progress >= 0.5, color, track, foreground)
            return
        make = _round_image_at if self._shape == "round" else _square_image_at
        self._photo = ImageTk.PhotoImage(
            make(self._size, progress, color, track, foreground)
        )
        self._canvas.create_image(self._size / 2, self._size / 2, image=self._photo)

    # ------------------------------------------------------------ 动画
    def _animate_to(self, target: float) -> None:
        """从当前进度补间到 ``target``；正在动的动画直接改目标。"""
        if not _HAS_PIL:
            self._refresh()
            return
        self._anim_from = self._progress
        self._anim_to = target
        if abs(self._anim_from - target) < 0.001:
            self._progress = target
            if self._anim_job is not None:
                with contextlib.suppress(tk.TclError):
                    self.after_cancel(self._anim_job)
                self._anim_job = None
            self._refresh()
            return
        self._anim_started = time.perf_counter()
        if self._anim_job is None:
            self._anim_job = self.after(_MARK_ANIM_STEP, self._anim_step)

    def _anim_step(self) -> None:
        """按真实经过时间插值，缓动用 ease_out_cubic。"""
        self._anim_job = None
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        elapsed = (time.perf_counter() - self._anim_started) * 1000
        ratio = min(1.0, elapsed / _MARK_ANIM_MS)
        eased = 1.0 - (1.0 - ratio) ** 3
        if ratio >= 1.0:
            self._progress = self._anim_to
            self._refresh()
            return
        self._progress = self._anim_from + (self._anim_to - self._anim_from) * eased
        self._paint(self._progress)
        self._anim_job = self.after(_MARK_ANIM_STEP, self._anim_step)

    def destroy(self) -> None:
        """销毁前取消动画帧，页面重建时不留 ``after`` 残留。"""
        if self._anim_job is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._anim_job)
            self._anim_job = None
        super().destroy()

    def _draw_plain(self, checked: bool, color: str, track: str, fg: str) -> None:
        """没装 Pillow 时的退路：canvas 画圆/方框（边缘会有阶梯）。"""
        canvas = self._canvas
        size = self._size
        pad = 2
        box = (pad, pad, size - pad, size - pad)
        if self._shape == "round":
            if checked:
                canvas.create_oval(*box, fill=color, outline="")
                inner = size * 0.2
                canvas.create_oval(
                    size / 2 - inner,
                    size / 2 - inner,
                    size / 2 + inner,
                    size / 2 + inner,
                    fill=fg,
                    outline="",
                )
            else:
                canvas.create_oval(*box, outline=track, width=2)
        else:
            if checked:
                canvas.create_rectangle(*box, fill=color, outline="")
            else:
                canvas.create_rectangle(*box, outline=track, width=2)

    def configure(self, **kwargs: Any) -> None:
        """支持 ``configure(command=...)``，和 CTk 控件的用法一致。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if kwargs:
            super().configure(**kwargs)
            self._bg = _bg_of(self)
            self._canvas.configure(bg=self._bg)
            self._refresh()


class Check(_Mark):
    """勾选框：实心圆角方块 + 白色对勾。"""

    _shape = "square"

    def __init__(
        self,
        master: tk.Misc,
        text: str = "",
        command: Optional[Callable[[], None]] = None,
        *,
        width: int = 22,
        height: int = 22,
        variable: Optional[tk.IntVar] = None,
        font: Any = None,
    ) -> None:
        """建勾选框；``get()`` 返回 0/1，和 ``CTkCheckBox`` 一致。"""
        self._variable = variable or tk.IntVar(value=0)
        super().__init__(
            master,
            text,
            width=width,
            height=height,
            command=command,
            font=font or get_font(T.FONT_BODY),
        )
        self._variable.trace_add("write", lambda *_: self._variable_changed())
        self._refresh()

    def _is_checked(self) -> bool:
        return bool(self._variable.get())

    def _set_checked(self, value: bool) -> None:
        self._silent = True
        try:
            self._variable.set(1 if value else 0)
        finally:
            self._silent = False

    def get(self) -> int:
        """0 / 1；等价于 ``int(get_value())``，保留给 ``CTkCheckBox`` 老代码。"""
        return 1 if self._is_checked() else 0

    def get_value(self) -> bool:
        """当前是否勾上。"""
        return self._is_checked()

    def set_value(self, value: bool) -> None:
        """勾上 / 取消勾选（不触发 ``command``）。"""
        self._set_checked(bool(value))
        self._animate_to(1.0 if value else 0.0)

    def select(self) -> None:
        """勾上（``set_value(True)`` 的旧名字）。"""
        self.set_value(True)

    def deselect(self) -> None:
        """取消勾选（``set_value(False)`` 的旧名字）。"""
        self.set_value(False)


class Radio(_Mark):
    """单选项：圆形指示符，同一个 ``group`` 里只用点一个。

    一组单选项共用内部的一个变量，所以不需要自己 new 一个 ``StringVar``：

    ```python
    Radio(box, "小", value="s", group="size")
    Radio(box, "中", value="m", group="size")
    Radio(box, "大", value="l", group="size")
    ```

    三个都传 ``group="size"`` 就自动互斥，选中值用任意一个的 ``get_value()``
    读即可。想自己管变量时仍然可以传 ``variable=``。
    """

    _shape = "round"

    #: ``group`` 名 → (组内共用的变量, 成员列表)
    _groups: Dict[str, Tuple[tk.StringVar, List["Radio"]]] = {}

    def __init__(
        self,
        master: tk.Misc,
        text: str = "",
        value: str = "",
        *,
        group: Optional[str] = None,
        variable: Optional[tk.StringVar] = None,
        command: Optional[Callable[[], None]] = None,
        width: int = 22,
        height: int = 22,
        font: Any = None,
    ) -> None:
        """建单选项；``value`` 是选中时写进变量的值，同 ``group`` 自动互斥。"""
        self._value = value if value else text
        self._group = group
        self._variable = self._variable_for(group, variable)
        if group is not None:
            Radio._groups.setdefault(group, (self._variable, []))[1].append(self)
        super().__init__(
            master,
            text,
            width=width,
            height=height,
            command=command,
            font=font or get_font(T.FONT_BODY),
        )
        self._variable.trace_add("write", lambda *_: self._variable_changed())
        if group is not None:
            self.bind("<Destroy>", self._on_group_destroy, add="+")
        self._refresh()

    @staticmethod
    def _variable_for(
        group: Optional[str], variable: Optional[tk.StringVar]
    ) -> tk.StringVar:
        """同组复用第一个成员建的变量；没分组或第一次建就自己 new 一个。"""
        if group is None:
            return variable or tk.StringVar()
        entry = Radio._groups.get(group)
        if entry is not None:
            return entry[0]
        return variable or tk.StringVar()

    def _on_group_destroy(self, event: Any = None) -> None:
        """控件销毁时从组里摘掉，页面重建不会留下死引用。"""
        if event is not None and event.widget is not self:
            return
        if self._group is None:
            return
        entry = Radio._groups.get(self._group)
        if entry is None:
            return
        members = entry[1]
        if self in members:
            members.remove(self)
        if not members:
            Radio._groups.pop(self._group, None)

    def _is_checked(self) -> bool:
        return self._variable.get() == self._value

    def _next_state(self) -> bool:
        """单选：点已选中的项不会再取消。"""
        return True

    def _set_checked(self, value: bool) -> None:
        if value:
            self._silent = True
            try:
                self._variable.set(self._value)
            finally:
                self._silent = False

    def select(self) -> None:
        """选中这一项。"""
        self._set_checked(True)
        self._animate_to(1.0)

    def get_value(self) -> str:
        """当前选中的值（同组共用的那个变量）。"""
        return self._variable.get()

    def set_value(self, value: str) -> None:
        """选中值为 ``value`` 的那一项；同组里值匹配的会自动亮起。"""
        self._variable.set(str(value))
