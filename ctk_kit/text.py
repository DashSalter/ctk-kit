"""大文本组件：带占位符、字数统计与只读模式的多行输入区。

``CTkTextbox`` 自身没有占位符，只读状态也要调用方自己管 ``state``；
``TextArea`` 把这两件事连同字数统计包成一个可直接摆位的整体：

- 占位符：没有内容且失焦时显示灰色占位文字，聚焦或输入后自动让位
- 字数：底部一行 ``N 字 · M 行``，``show_counter=False`` 可关掉
- 只读：``readonly=True`` 时禁止编辑，``set_readonly()`` 可随时切换
- ``on_change``：键盘输入或 ``set()`` 之后回调最新全文

所有颜色、字体、圆角都取自 ``tokens``，切换深浅色不需要额外处理。

工厂只返回控件，不负责摆位::

    area = TextArea(frame, placeholder="写点什么…", on_change=print)
    area.pack(fill="both", expand=True)
    area.set("第一行\\n第二行")
"""

from __future__ import annotations

import sys
import tkinter as tk
from typing import Any, Callable, Optional

import customtkinter as ctk

from . import tokens as T
from .context_menu import attach_edit_menu
from .fonts import get_font
from .layout import style_scrollbar
from .scrolling import find_scrollable, wheel_step
from .sugar import Enablable

# 内容变化回调：收到最新的全文（空文本时是空字符串）。
ChangeHandler = Optional[Callable[[str], None]]


class TextArea(Enablable, ctk.CTkFrame):
    """多行文本输入区，附带占位符、字数统计与只读模式。"""

    def __init__(
        self,
        master: tk.Misc,
        *,
        placeholder: str = "",
        height: int = 200,
        readonly: bool = False,
        show_counter: bool = True,
        on_change: ChangeHandler = None,
        bg_color: Any = None,
        text_color: Any = None,
        menu: Any = True,
        **kwargs: Any,
    ) -> None:
        """创建文本区。

        参数:
            master: 父容器。
            placeholder: 没有内容时显示的灰色占位文字，空字符串表示不要占位符。
            height: 文本区高度（像素），默认 200；状态栏另算。
            readonly: 是否只读（禁止编辑，仍可选中与复制）。
            show_counter: 是否在底部显示字数统计，默认 True。
            on_change: 内容变化时的回调，参数是当前全文。
            bg_color: 文本区底色（颜色元组或 ``"transparent"``），默认用输入框底色
                ``COLOR_INPUT``。放在卡片里当日志显示时，传 ``COLOR_CARD`` 或
                ``"transparent"`` 就不会比周围亮一截。
            text_color: 正文颜色，默认 ``COLOR_TEXT``。
            menu: 右键菜单。``True`` 挂默认的复制/粘贴/剪切/清空，``False``
                或 ``None`` 不挂，传 ``(文字, 函数)`` 的序列则只用这些自定义项。
            **kwargs: 透传给外层 ``CTkFrame`` 的参数。
        """
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._placeholder = placeholder
        self._placeholder_active = False
        self._readonly = bool(readonly)
        self._on_change = on_change
        self._text_color: Any = text_color if text_color is not None else T.COLOR_TEXT
        # 文本区的底色默认比卡片暗一档的 COLOR_INPUT，配一圈 1px 的 COLOR_BORDER_INPUT。
        # 外面传 "transparent" 时换成父容器实色——CTk 的 fg_color 虽然认透明，
        # 但透明要一层层往上取色，嵌套一多容易露出缝隙。
        self._bg_color: Any = bg_color if bg_color is not None else T.COLOR_INPUT
        self._transparent_bg = isinstance(self._bg_color, str) and (
            self._bg_color.lower() == "transparent"
        )
        fill = self._solid_bg()

        self.textbox = ctk.CTkTextbox(
            self,
            height=height,
            corner_radius=T.RADIUS_MEDIUM,
            border_width=1,
            border_color=T.COLOR_BORDER_INPUT,
            fg_color=fill,
            text_color=self._text_color,
            font=get_font(T.FONT_BODY),
            wrap="word",
            # 滚动条和其它滚动容器用同一套令牌，免得文本区这里灰一截、列表那里又不一样
            scrollbar_button_color=T.COLOR_SCROLLBAR,
            scrollbar_button_hover_color=T.COLOR_SCROLLBAR_HOVER,
        )
        self.textbox.pack(fill="both", expand=True)
        for name in ("_y_scrollbar", "_x_scrollbar"):
            bar = getattr(self.textbox, name, None)
            if bar is not None:
                # CTkTextbox 没有暴露滚动条宽度的构造参数，只能构造后补一下；
                # 间距必须和 Scrollable() 用同一个，否则滑块会比页面滚动条粗一圈
                style_scrollbar(bar)
        self.textbox.bind("<FocusIn>", self._handle_focus_in)
        self.textbox.bind("<FocusOut>", self._handle_focus_out)
        self.textbox.bind("<KeyRelease>", lambda _event: self._refresh())

        # 滚轮链：文本区还有内容可滚时先滚文本区；到底（或本来就没内容）时
        # 把滚轮交给外层 Scrollable，否则鼠标停在输入框上整页就卡住滚不动。
        self._bind_wheel()

        self.counter = ctk.CTkLabel(
            self,
            text="0 字",
            anchor="e",
            font=get_font(T.FONT_TINY),
            text_color=T.COLOR_FAINT,
        )
        if show_counter:
            self.counter.pack(fill="x", pady=(T.SPACE_XS, 0))

        if self._placeholder:
            self._show_placeholder()
        self._apply_readonly_state()
        self._refresh(notify=False)
        if menu:
            if menu is True:
                attach_edit_menu(self)
            else:
                attach_edit_menu(self, menu, preset=False)

    # ------------------------------------------------------------ 读写
    def get(self) -> str:
        """返回当前全文；占位符显示中时返回空字符串。"""
        if self._placeholder_active:
            return ""
        return self.textbox.get("1.0", "end-1c")

    def set(self, text: str) -> None:
        """整体替换内容；传空字符串会恢复占位符。"""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        if text:
            self.textbox.insert("1.0", text)
            self._placeholder_active = False
            self.textbox.configure(text_color=self._text_color)
        elif self._placeholder:
            self._show_placeholder()
        else:
            self._placeholder_active = False
            self.textbox.configure(text_color=self._text_color)
        self._apply_readonly_state()
        self._refresh()

    def clear(self) -> None:
        """清空内容，等价于 ``set("")``。"""
        self.set("")

    def append(self, text: str) -> None:
        """追加到末尾；自动刷新字数统计并触发 ``on_change``。"""
        self.insert(text)

    def insert(self, text: str, at: str = "end") -> None:
        """在 ``at`` 位置插入文本；``at`` 接受 Tk 索引（如 ``"1.0"``、``"end"``）。

        占位符显示中时会先清掉占位符；只读控件临时放开、写入后再锁回去。
        """
        if not text:
            return
        self.textbox.configure(state="normal")
        if self._placeholder_active:
            self._clear_placeholder()
            at = "1.0"
        self.textbox.insert(at, text)
        self._apply_readonly_state()
        self._refresh()

    # ------------------------------------------------------------ 只读
    @property
    def readonly(self) -> bool:
        """当前是否处于只读状态。"""
        return self._readonly

    def set_readonly(self, value: bool) -> None:
        """切换只读状态。"""
        self._readonly = bool(value)
        self._apply_readonly_state()

    def _apply_enabled(self, enabled: bool) -> None:
        """禁用等价于只读：内容还能选中复制，但改不了。"""
        self.set_readonly(not enabled)

    def is_enabled(self) -> bool:
        """文本区当前是否可编辑。"""
        return not self._readonly

    # ------------------------------------------------------------ 内部
    def _bind_wheel(self) -> None:
        """给内部 tk.Text 挂滚轮：能滚就滚自己，滚到底再交给外层滚动容器。"""
        text = self.textbox._textbox
        if sys.platform.startswith("linux"):
            text.bind("<Button-4>", self._on_wheel_linux, add="+")
            text.bind("<Button-5>", self._on_wheel_linux, add="+")
        else:
            text.bind("<MouseWheel>", self._on_wheel, add="+")

    def _on_wheel(self, event: Any) -> str:
        """Windows / macOS：delta 为正表示向上滚。"""
        if not event.delta:
            return "break"
        return self._wheel_step(-1 if event.delta > 0 else 1)

    def _on_wheel_linux(self, event: Any) -> str:
        """Linux：Button-4 向上，Button-5 向下。"""
        return self._wheel_step(-1 if event.num == 4 else 1)

    def _wheel_step(self, units: int) -> str:
        """先滚文本区；文本区已经到顶/到底时把滚轮转给外层 Scrollable。"""
        return wheel_step(
            self.textbox._textbox,
            units,
            self_units=3,
            master=self,
        )

    def _find_scrollable(self) -> Optional[ctk.CTkScrollableFrame]:
        """向上找最近的 CTkScrollableFrame（Scrollable 是它的子类）。"""
        return find_scrollable(self)

    def _solid_bg(self) -> Any:
        """文本区实际用的底色。

        传入 ``"transparent"`` 时沿父链找第一个实色：文本区在卡片里当日志面板用
        时，要的就是「和卡片同色」。返回的可能是 ``(浅色, 深色)`` 二元组，
        交给 CTk 按当前外观自己取，切主题时会跟着变。
        """
        if not self._transparent_bg:
            return self._bg_color
        node: Any = getattr(self, "master", None)
        for _ in range(8):
            if node is None:
                break
            try:
                value = node.cget("fg_color")
            except Exception:  # noqa: BLE001 - 原生 tk 控件没有这个属性
                break
            if not (isinstance(value, str) and value.lower() == "transparent"):
                return value
            node = getattr(node, "master", None)
        return T.COLOR_CARD

    def _apply_readonly_state(self) -> None:
        """按 ``readonly`` 切换内部 Text 的可编辑状态。"""
        self.textbox.configure(state="disabled" if self._readonly else "normal")

    def _show_placeholder(self) -> None:
        """显示占位文字：临时放开只读，写完再锁回去。"""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", self._placeholder)
        self.textbox.configure(text_color=T.COLOR_FAINT)
        self._placeholder_active = True
        self._apply_readonly_state()

    def _clear_placeholder(self) -> None:
        """清掉占位文字并恢复正文颜色。"""
        self.textbox.delete("1.0", "end")
        self.textbox.configure(text_color=self._text_color)
        self._placeholder_active = False

    def _handle_focus_in(self, _event: Any) -> None:
        """聚焦：非只读时把占位文字撤掉（只读时保留占位符）。"""
        # 只读时保留占位符：它不是可编辑内容，不该因为聚焦就消失
        if self._placeholder_active and not self._readonly:
            self._clear_placeholder()

    def _handle_focus_out(self, _event: Any) -> None:
        """失焦且内容为空时重新显示占位文字。"""
        if self._placeholder_active:
            return
        if not self.textbox.get("1.0", "end-1c") and self._placeholder:
            self._show_placeholder()
            self._refresh()

    def _refresh(self, notify: bool = True) -> None:
        """更新字数统计；``notify`` 为真时把全文交给 ``on_change``。"""
        text = self.get()
        if text:
            lines = text.count("\n") + 1
            self.counter.configure(text=f"{len(text)} 字 · {lines} 行")
        else:
            self.counter.configure(text="0 字")
        if notify and self._on_change is not None:
            self._on_change(text)
