"""页面骨架：页头、分区卡片、分隔线、滚动容器、空状态。

一套页面按这个顺序搭出来，视觉就不会散：

    PageHeader  →  section(title)  →  card 里的若干行  →  divider  →  footer

除滚动容器外，这里的工厂都会顺手 ``pack``（``fill="x"``），因为它们的位置
在页面骨架里是固定的；按钮、输入框这类需要自己摆位。
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

from . import tokens as T
from .fonts import get_font


class PageHeader(ctk.CTkFrame):
    """页面顶部：左边标题，右边信息标签。

    直接当控件用；右侧标签通过 ``header.info`` 访问。为了兼容旧写法，
    也支持 ``head, info = PageHeader(...)`` 解包。
    """

    def __init__(self, master: tk.Misc, title: str) -> None:
        """建页头：左边标题、右边信息标签，整行铺满。"""
        super().__init__(master, fg_color="transparent")
        self.pack(fill="x")
        self.title_label = ctk.CTkLabel(
            self, text=title, font=get_font(T.FONT_TITLE), text_color=T.COLOR_TEXT
        )
        self.title_label.pack(side="left")
        self.info = ctk.CTkLabel(
            self, text="", font=get_font(T.FONT_TINY), text_color=T.COLOR_MUTED, anchor="e"
        )
        self.info.pack(side="right", pady=(9, 0))

    def __iter__(self) -> Any:
        """兼容旧写法 ``head, info = PageHeader(...)`` 的解包。"""
        # 兼容 `head, info = PageHeader(...)` 的旧写法
        return iter((self, self.info))


class SectionTitle(ctk.CTkLabel):
    """分区标题（设置页的「外观」「备份」这一层），构造时即 ``pack``。"""

    def __init__(self, master: tk.Misc, text: str) -> None:
        """建分区标题；构造时自动 ``pack`` 成一行。"""
        super().__init__(
            master,
            text=text,
            font=get_font(T.FONT_SECTION),
            text_color=T.COLOR_TEXT,
            anchor="w",
        )
        self.pack(fill="x", pady=(T.SPACE_LG, T.SPACE_SM - 2))


class Card(ctk.CTkFrame):
    """圆角卡片容器，可选在上方带标题。

    卡片样式（填充、1px 边框、圆角）与 :class:`Card` 相同；传 ``title``
    时在卡片**外面**的上方放一行标题，卡片内容仍放在卡片内部::

        box = Card(page, title="复杂页面")
        form = Frame(box)
        form.pack(fill="x", padx=16, pady=12)

    参数:
        title: 卡片标题；不传就没有标题，行为与普通卡片相同。
        **kwargs: 其余参数与 ``CTkFrame`` 相同，显式传同名参数可覆盖卡片样式。

    注意:
        标题是 ``master`` 的子控件、用 ``pack`` 放在卡片上方，所以：

        - 带 ``title`` 的卡片要用 ``pack`` 放进 ``master``（不能用 ``grid``）；
        - 卡片 ``pack`` 时传的 ``padx`` 会自动同步给标题，标题和卡片左右对齐；
        - 卡片 ``pack`` 时传的 ``pady`` 顶部值会转给标题，在标题上方留白，
          卡片本身不再重复留这段顶部间距；底部值仍留给卡片；
        - 卡片内容不受影响，内部仍可任意用 ``pack`` 或 ``grid``。
    """

    def __init__(
        self, master: tk.Misc, *, title: str = "", **kwargs: Any
    ) -> None:
        """建卡片；传 ``title`` 时在卡片上方再放一行标题。"""
        kwargs.setdefault("fg_color", T.COLOR_CARD)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", T.COLOR_BORDER)
        kwargs.setdefault("corner_radius", T.RADIUS_MEDIUM)
        super().__init__(master, **kwargs)
        self.title_label = None
        if title:
            self.title_label = ctk.CTkLabel(
                master,
                text=title,
                font=get_font(T.FONT_SECTION),
                text_color=T.COLOR_TEXT,
                anchor="w",
            )
            self.title_label.pack(fill="x", pady=(0, T.SPACE_SM))

    @property
    def body(self) -> "Card":
        """卡片的内容容器。

        目前就是卡片自身；加这个属性是为了让调用方不用关心「Card 既是
        边框又是内容容器」这个细节，以后内部结构变了也不用改调用代码::

            box = Card(page, title="详情")
            Frame(box.body).pack(fill="x", padx=16, pady=12)
        """
        return self

    def pack(self, cnf: Any = None, **kwargs: Any) -> None:
        """``pack`` 卡片时把 ``padx`` / 顶部 ``pady`` 同步给标题。

        标题是 ``master`` 的子控件，不会自动跟着卡片的外边距走；这里在摆放
        卡片时顺手把同样的水平边距设给标题，并把顶部间距挪到标题上方——否则
        卡片自己的顶部 ``pady`` 会把标题和卡片之间的空隙撑大、把标题挤上去。
        """
        if self.title_label is not None:
            padx = kwargs.get("padx")
            if padx is None and cnf:
                padx = cnf.get("padx")
            pady = kwargs.get("pady")
            if pady is None and cnf:
                pady = cnf.get("pady")

            scale = getattr(self.title_label, "_apply_widget_scaling", None)
            if not callable(scale):
                scale = None

            label_cnf: dict[str, Any] = {}
            if padx is not None:
                # 卡片走 CTkBaseClass.pack，会把 padx 按窗口缩放；标题用原生
                # pack_configure，不缩放，这里补上同样的缩放才能对齐。
                if scale is not None:
                    if isinstance(padx, (tuple, list)):
                        padx = tuple(scale(value) for value in padx)
                    else:
                        padx = scale(padx)
                label_cnf["padx"] = padx
            if pady is not None:
                top, bottom = self._split_pady(pady)
                if scale is not None:
                    top = scale(top)
                label_cnf["pady"] = (top, T.SPACE_SM)
                # 顶部间距已经交给标题，卡片只保留底部间距
                kwargs = {**kwargs, "pady": (0, bottom)}
            if label_cnf:
                self.title_label.pack_configure(**label_cnf)
        if cnf:
            kwargs = {**cnf, **kwargs}
        super().pack(**kwargs)

    @staticmethod
    def _split_pady(pady: Any) -> tuple[Any, Any]:
        """把 ``pady`` 拆成 ``(top, bottom)``；单值表示上下相同。"""
        if isinstance(pady, (tuple, list)):
            values = list(pady)
            if len(values) == 1:
                return values[0], values[0]
            return values[0], values[1]
        return pady, pady


def _resolve(color: Any) -> Any:
    """令牌里的颜色是 (浅色, 深色) 元组，纯 tk 控件只认解析后的字符串。"""
    if isinstance(color, (tuple, list)) and len(color) == 2:
        from .theme import color_of

        return color_of(color)
    return color


def _canvas_bg(master: tk.Misc) -> str:
    """给 canvas 找一个实际的背景色：tk 的 canvas 不认 ``transparent``。"""
    try:
        value = master.cget("fg_color")
    except Exception:  # noqa: BLE001
        value = None
    if isinstance(value, (tuple, list)):
        return _resolve(value)
    if isinstance(value, str) and value and value != "transparent":
        return value
    return _resolve(T.COLOR_CARD)


def divider(
    master: tk.Misc,
    *,
    pady: tuple = (T.SPACE_MD, 0),
    text: str = "",
    dashed: bool = False,
    color: Any = None,
) -> tk.Misc:
    """分隔线；用 Frame 而不是 ttk.Separator，颜色好控制。

    参数:
        master: 父容器。
        pady: ``(上, 下)`` 外边距，默认 ``(12, 0)``。
        text: 给了就在线中间挖个口、放这行字（从左边起排）。
        dashed: ``True`` 时画成虚线（canvas 画的短线段）。
        color: 线的颜色，默认 ``COLOR_BORDER``。

    返回:
        已 ``pack(fill="x")`` 的一行容器。
    """
    line_color = color or T.COLOR_BORDER
    if not text and not dashed:
        # 纯 tk.Frame：CTkFrame 的 1px 高度会被它自己的圆角/描边吃掉，画不出来
        line = tk.Frame(master, height=1, bg=_resolve(line_color))
        line.pack(fill="x", pady=pady)
        return line

    row = ctk.CTkFrame(master, fg_color="transparent")
    row.pack(fill="x", pady=pady)

    if text:
        label = ctk.CTkLabel(
            row,
            text=text,
            font=get_font(T.FONT_SMALL),
            text_color=T.COLOR_MUTED,
            fg_color="transparent",
        )
        label.pack(side="left", padx=(0, 10))
    _line(row, line_color, dashed, side="left", fill="x", expand=True)
    return row


def _line(master: tk.Misc, color: Any, dashed: bool, **pack_options: Any) -> tk.Misc:
    """画一根实线或虚线；虚线用 canvas 的短线段拼。"""
    if not dashed:
        line = tk.Frame(master, height=1, bg=_resolve(color))
        line.pack(**pack_options)
        return line

    canvas = tk.Canvas(
        master, height=1, bg=_canvas_bg(master), highlightthickness=0, bd=0
    )
    canvas.pack(**pack_options)
    fill = _resolve(color)

    def redraw(_event: tk.Event = None) -> None:
        """宽度变了就重画一遍：短线段在 canvas 里不会自己拉伸。"""
        canvas.delete("all")
        width = max(1, canvas.winfo_width())
        step, gap = 4, 4
        x = 0
        while x < width:
            canvas.create_line(x, 0, min(width, x + step), 0, fill=fill)
            x += step + gap

    canvas.bind("<Configure>", redraw)
    redraw()
    return canvas


def vertical_divider(
    master: tk.Misc, *, height: int = 20, padx: tuple = (0, 0), color: Any = None
) -> tk.Frame:
    """1px 宽的竖向分隔线，用来隔开同一行里的几块内容。"""
    line = tk.Frame(master, width=1, height=height, bg=_resolve(color or T.COLOR_BORDER))
    line.pack(side="left", fill="y", padx=padx)
    return line


def style_scrollbar(bar: ctk.CTkScrollbar) -> ctk.CTkScrollbar:
    """把任意 ``CTkScrollbar`` 调成窄条淡色。

    ``CTkScrollbar`` 的滑块宽度是「控件宽度减去两侧 ``border_spacing``」，
    默认间距是 0，所以同样 ``width=12`` 的滚动条在文本区里会画成 12 宽的粗条；
    滚动容器走的是 CTk 主题里的 4，滑块才 4 宽。两处必须统一用同一个间距，
    否则并排放着就是「一根粗、一根细」。

    参数:
        bar: ``CTkScrollbar`` 实例。

    返回:
        同一个 ``bar``，方便链式调用。
    """
    bar.configure(
        width=T.SCROLLBAR_WIDTH,
        border_spacing=T.SCROLLBAR_SPACING,
        fg_color="transparent",
        button_color=T.COLOR_SCROLLBAR,
        button_hover_color=T.COLOR_SCROLLBAR_HOVER,
    )
    return bar


def style_scrollable(frame: ctk.CTkScrollableFrame) -> ctk.CTkScrollableFrame:
    """把 CTkScrollableFrame 的滚动条调成窄条淡色。

    CTkScrollableFrame 的滚动条藏在 ``_scrollbar`` 私有属性里，只能这样拿；
    CTk 升级时如果改名，这里会静默失效（不报错，只是回到默认样式）。

    参数:
        frame: ``CTkScrollableFrame`` 实例；传入其它控件时原样返回。

    返回:
        同一个 ``frame``，方便链式调用。
    """
    bar = getattr(frame, "_scrollbar", None)
    if bar is not None:
        style_scrollbar(bar)
    canvas = getattr(frame, "_parent_canvas", None)
    if canvas is not None:
        # CTk 默认 yscrollincrement=1，一格滚轮只挪 20px；调到 3 倍（60px）
        canvas.configure(yscrollincrement=3)
    return frame


class Scrollable(ctk.CTkScrollableFrame):
    """已配好滚动条样式的透明滚动容器。

    构造参数与 ``CTkScrollableFrame`` 一致（``fg_color`` 默认透明）；
    摆位由调用方决定，``pack`` / ``grid`` 都行。
    """

    def __init__(self, master: tk.Misc, **kwargs: Any) -> None:
        """建透明滚动容器，并套用库的滚动条样式。"""
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        style_scrollable(self)


def empty_hint(master: tk.Misc, title: str, detail: str = "") -> ctk.CTkFrame:
    """居中的空状态：一行主提示 + 一行补充说明。

    参数:
        master: 父容器。
        title: 主提示（如「这里还没有内容」）。
        detail: 补充说明；为空时只显示一行。

    返回:
        透明容器，已经装好 1~2 行灰色文字；摆放由调用方决定。
    """
    box = ctk.CTkFrame(master, fg_color="transparent")
    ctk.CTkLabel(box, text=title, font=get_font(T.FONT_BODY), text_color=T.COLOR_MUTED).pack()
    if detail:
        ctk.CTkLabel(
            box,
            text=detail,
            font=get_font(T.FONT_SMALL),
            text_color=T.COLOR_MUTED,
            justify="center",
        ).pack(pady=(6, 0))
    return box


class FieldLabel(ctk.CTkLabel):
    """卡片内左对齐的字段名，宽度固定让右边控件能对齐成一列。"""

    def __init__(self, master: tk.Misc, text: str, *, width: int = 112) -> None:
        """建固定宽度的字段名标签，让右边控件能对齐成一列。"""
        super().__init__(
            master,
            text=text,
            font=get_font(T.FONT_SMALL),
            text_color=T.COLOR_MUTED,
            width=width,
            anchor="w",
        )


class HintLabel(ctk.CTkLabel):
    """字段下方的说明文字（左对齐、多行左对齐），构造时尚未摆位。"""

    def __init__(self, master: tk.Misc, text: str) -> None:
        """建字段说明标签（左对齐、多行左对齐），构造时尚未摆位。"""
        super().__init__(
            master,
            text=text,
            font=get_font(T.FONT_SMALL),
            text_color=T.COLOR_MUTED,
            anchor="w",
            justify="left",
        )
