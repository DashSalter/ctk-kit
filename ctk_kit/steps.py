"""步骤条与向导：把长流程拆成几步，显示当前走到哪。

``Steps`` 是纯展示（可选点击跳转），``Wizard`` 在它下面接一个内容区
和「上一步 / 下一步」按钮，每步的内容由调用方给的构建函数现建。

用法::

    from ctk_kit import Steps, Wizard

    Steps(card, steps=["选择文件", "设置参数", "开始备份"], current=2)

    wizard = Wizard(
        card,
        steps=[
            ("选择文件", build_pick_page),
            ("确认", build_confirm_page),
        ],
        command=lambda w: print("完成"),
    )

构建函数签名是 ``(parent, wizard)``：往 ``parent`` 里放控件，需要跳步时
调 ``wizard.go_to(n)``。步骤圆点用 Pillow 画，数字和对勾不会糊。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional, Sequence, Tuple

import customtkinter as ctk

from . import tokens as T
from .buttons import PrimaryButton, SoftButton
from .fonts import get_font
from .sugar import Valuable
from .paint import cached
from .theme import color_of

try:  # Pillow 是可选依赖
    from PIL import Image, ImageDraw, ImageFont

    _HAS_PIL = True
except Exception:  # noqa: BLE001
    _HAS_PIL = False

__all__ = ["Steps", "Wizard"]

#: 圆点直径（逻辑像素）。
_DOT = 24
#: 超采样倍数。
_SCALE = 4
#: 连接线高度。
_LINE = 2

StepCommand = Optional[Callable[[int], None]]
PageBuilder = Callable[[ctk.CTkFrame, "Wizard"], None]


def _font(size: int):
    """尽量用 Arial 画数字；系统没有时退回 Pillow 的默认字体。"""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:  # noqa: BLE001
        return ImageFont.load_default()


@cached
def _dot_image(
    index: int, state: str, color: str, border: str, muted: str
):
    """画一个步骤圆点：完成是对勾、当前是数字、未开始是描边数字。"""
    scale = _SCALE
    size = _DOT
    image = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    box = (2 * scale, 2 * scale, (size - 2) * scale, (size - 2) * scale)
    center = size * scale / 2

    if state == "done":
        pen.ellipse(box, fill=color)
        pen.line(
            [
                (7 * scale, 12 * scale),
                (11 * scale, 16 * scale),
                (17 * scale, 8 * scale),
            ],
            fill="#ffffff",
            width=2 * scale,
            joint="curve",
        )
    elif state == "current":
        pen.ellipse(box, fill=color)
        pen.text(
            (center, center),
            str(index + 1),
            font=_font(11 * scale),
            fill="#ffffff",
            anchor="mm",
        )
    else:
        pen.ellipse(box, outline=border, width=2 * scale)
        pen.text(
            (center, center),
            str(index + 1),
            font=_font(11 * scale),
            fill=muted,
            anchor="mm",
        )
    return image.resize((size, size), Image.LANCZOS)


class Steps(Valuable, ctk.CTkFrame):
    """横向步骤条。

    参数:
        master: 父容器。
        steps: 每一步的标题，按顺序排列。
        current: 当前第几步，从 1 开始，默认 1。
        command: 点击某一步时的回调（``clickable=True`` 时才绑）。
        clickable: 步骤圆点是否可点，默认 ``False``。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        get(): 当前步数（1 开始）。
        set_current(step, notify=False): 跳到某一步。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        steps: Sequence[str] = (),
        current: int = 1,
        command: StepCommand = None,
        clickable: bool = False,
        **kwargs: Any,
    ) -> None:
        """建步骤条；``current`` 超出范围会夹到首尾。"""
        super().__init__(master, fg_color="transparent", **kwargs)

        self._titles = list(steps)
        self._current = self._clamp(current)
        self._command = command
        self._clickable = clickable
        self._dots: list[ctk.CTkLabel] = []
        self._labels: list[ctk.CTkLabel] = []
        self._lines: list[ctk.CTkFrame] = []
        self._photos: list[Any] = []

        for index, title in enumerate(self._titles):
            dot = ctk.CTkLabel(self, text="", width=_DOT, height=_DOT)
            dot.grid(row=0, column=index * 2, padx=0)
            label = ctk.CTkLabel(
                self,
                text=title,
                font=get_font(T.FONT_SMALL),
                text_color=T.COLOR_MUTED,
                fg_color="transparent",
            )
            label.grid(row=1, column=index * 2, pady=(4, 0))
            self._dots.append(dot)
            self._labels.append(label)

            if index < len(self._titles) - 1:
                line = ctk.CTkFrame(
                    self,
                    height=_LINE,
                    fg_color=T.COLOR_BORDER,
                    corner_radius=1,
                )
                line.grid(row=0, column=index * 2 + 1, sticky="ew", padx=(8, 8))
                self._lines.append(line)
                self.grid_columnconfigure(index * 2 + 1, weight=1)

            if clickable:
                for widget in (dot, label):
                    widget.bind(
                        "<Button-1>", lambda _e, i=index: self._go(i + 1)
                    )

        self._paint()

    # --- 对外 ---
    def configure(self, **kwargs: Any) -> None:
        """改属性；``command=`` 换点击回调，其余透传给 ``CTkFrame``。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        super().configure(**kwargs)

    def get(self) -> int:
        """当前第几步（1 开始）。"""
        return self._current

    def set_current(self, step: int, notify: bool = False) -> None:
        """跳到 ``step``；``notify=True`` 时也回调。"""
        step = self._clamp(step)
        if step == self._current:
            return
        self._current = step
        self._paint()
        if notify and self._command is not None:
            self._command(step)

    def set_value(self, step: int) -> None:
        """跳到第 ``step`` 步，等价于 ``set_current(step)``。"""
        self.set_current(step)

    # --- 内部 ---
    def _clamp(self, step: int) -> int:
        """夹到 ``1..len(steps)``；没有步骤时返回 1。"""
        if not self._titles:
            return 1
        return max(1, min(int(step), len(self._titles)))

    def _paint(self) -> None:
        """按当前步数刷新圆点、标题和连接线。"""
        if not self.winfo_exists():
            return
        color = color_of(T.COLOR_ACTIVE)
        border = color_of(T.COLOR_BORDER_STRONG)
        muted = color_of(T.COLOR_FAINT)
        self._photos = []
        for index, dot in enumerate(self._dots):
            if index < self._current - 1:
                state = "done"
            elif index == self._current - 1:
                state = "current"
            else:
                state = "todo"
            if _HAS_PIL:
                image = _dot_image(index, state, color, border, muted)
                photo = ctk.CTkImage(
                    light_image=image, dark_image=image, size=(_DOT, _DOT)
                )
                self._photos.append(photo)
                dot.configure(image=photo, text="")
            else:
                dot.configure(
                    text="✓" if state == "done" else str(index + 1),
                    font=get_font((T.FONT_NAME, 11, "bold")),
                    text_color=T.COLOR_ACCENT_TEXT if state != "todo" else muted,
                    fg_color=T.COLOR_ACTIVE if state != "todo" else "transparent",
                    corner_radius=999,
                )
            label = self._labels[index]
            label.configure(
                text_color=T.COLOR_TEXT if index <= self._current - 1 else T.COLOR_MUTED
            )
        for index, line in enumerate(self._lines):
            line.configure(
                fg_color=T.COLOR_ACTIVE
                if index < self._current - 1
                else T.COLOR_BORDER
            )

    def _go(self, step: int) -> None:
        """点击某一步。"""
        if step == self._current:
            return
        self.set_current(step, notify=True)


class Wizard(Valuable, ctk.CTkFrame):
    """分步向导：步骤条 + 内容区 + 上一步/下一步。

    参数:
        master: 父容器。
        steps: ``(标题, 构建函数)`` 的序列；构建函数签名是
            ``(parent, wizard)``，往 ``parent`` 里放这一页的控件。
        command: 最后一页点「完成」时的回调，参数是 ``Wizard``。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        get(): 当前第几步。
        go_to(step): 跳到某一步并重建内容。
        next(): 下一步；已经在最后一页时触发完成回调。
        back(): 上一步。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        steps: Sequence[Tuple[str, PageBuilder]] = (),
        command: Optional[Callable[["Wizard"], None]] = None,
        **kwargs: Any,
    ) -> None:
        """建向导；第一页内容在构造结束时立即构建。"""
        super().__init__(master, fg_color="transparent", **kwargs)

        self._titles = [title for title, _builder in steps]
        self._builders = [builder for _title, builder in steps]
        self._command = command
        self._current = 1

        self._bar = Steps(self, steps=self._titles, current=1, clickable=False)
        self._bar.pack(fill="x", pady=(0, 10))

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True)

        self._footer = ctk.CTkFrame(self, fg_color="transparent")
        self._footer.pack(fill="x", pady=(10, 0))
        self._back = SoftButton(self._footer, "上一步", command=self.back)
        self._back.pack(side="left")
        self._next = PrimaryButton(self._footer, "下一步", command=self.next)
        self._next.pack(side="right")

        self._render()

    # --- 对外 ---
    def configure(self, **kwargs: Any) -> None:
        """改属性；``command=`` 换完成回调，其余透传给 ``CTkFrame``。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        super().configure(**kwargs)

    def get(self) -> int:
        """当前第几步（1 开始）。"""
        return self._current

    def go_to(self, step: int) -> None:
        """跳到 ``step`` 并重建这一页的内容。"""
        if not self._builders:
            return
        step = max(1, min(int(step), len(self._builders)))
        self._current = step
        self._bar.set_current(step)
        self._render()

    def set_value(self, step: int) -> None:
        """跳到第 ``step`` 步，等价于 ``go_to(step)``。"""
        self.go_to(step)

    def next(self) -> None:
        """下一步；已经在最后一页时触发完成回调。"""
        if self._current >= len(self._builders):
            if self._command is not None:
                self._command(self)
            return
        self.go_to(self._current + 1)

    def back(self) -> None:
        """上一步。"""
        if self._current > 1:
            self.go_to(self._current - 1)

    # --- 内部 ---
    def _render(self) -> None:
        """清空内容区，构建当前页；刷新按钮状态和文字。"""
        for child in self._body.winfo_children():
            child.destroy()
        if not self._builders:
            return
        builder = self._builders[self._current - 1]
        builder(self._body, self)

        last = self._current == len(self._builders)
        self._next.configure(text="完成" if last else "下一步")
        self._back.configure(state="normal" if self._current > 1 else "disabled")
