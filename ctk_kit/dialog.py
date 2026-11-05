"""对话框：信息 / 成功 / 警告 / 错误 / 确认 / 输入。

和提示浮层（:mod:`ctk_kit.notify`）不同，这里是**模态窗口**：弹出期间
主窗口客户区点不了、滚轮也滚不动，必须点按钮、按 Esc 或 Alt+F4 才能
继续；但主窗口仍然可以拖动，对话框会跟着走。实现方式是 ``CTkToplevel``
+ ``overrideredirect``（无边框圆角卡片）+ ``grab_set`` + ``wait_window``，
再在父窗口上临时拦 ``<MouseWheel>``——CTk 的滚动走 ``bind_all``，
光靠 grab 拦不住。

内容全部画在一张 ``tk.Canvas`` 上（标题、正文、按钮都是 canvas 图元），
而不是用 ``CTkFrame`` / ``CTkLabel`` 拼。这样模糊背景图能直接当 canvas
的底层图元，文字和按钮没有「不透明底色」，毛玻璃才是整块磨砂；用控件
拼的话每行文字都会带一条实色横带，看起来像条纹玻璃。输入框是个例外，
它必须是真控件，所以用 ``create_window`` 嵌进 canvas。

常用的三种直接调函数：:

    from ctk_kit import alert, confirm, prompt

    alert(app, "已保存到 D:/backup", title="完成", level="success")

    if confirm(app, "删除这份备份？", level="warn", danger=True, ok="删除"):
        ...

    name = prompt(app, "给备份起个名字", value="backup-01")

需要更自由的排版时直接用 :class:`Dialog`：``buttons`` 自己给，
按下的按钮的 ``value`` 由 :meth:`Dialog.show` 返回。
"""

from __future__ import annotations

import contextlib
import sys
import time
import tkinter as tk
from typing import Any, Callable, Optional, Sequence

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

from . import tokens as T
from .fonts import get_font
from .core.glass import backdrop_image, excluding_from_capture, gradient_image
from .inputs import FormEntry
from .paint import cached
from .popup import round_window_corners, scaled_geometry
from .core.win32 import acrylic_window, client_frame_inset, set_client_rect
from .theme import color_of

__all__ = ["Dialog", "alert", "confirm", "prompt"]

#: 各层级用的主色。
_LEVEL_COLORS = {
    "info": T.COLOR_ACCENT,
    "success": T.COLOR_SUCCESS,
    "warn": T.COLOR_WARNING,
    "error": T.COLOR_ERROR,
}

#: 没给 title 时按层级挑一个默认标题。
_LEVEL_TITLES = {
    "info": "提示",
    "success": "完成",
    "warn": "注意",
    "error": "错误",
}

# 布局常量（逻辑像素，最后统一乘缩放）。
_PAD = 18
_GAP_ICON = 12
_ICON = 34
_BUTTON_H = 34
_BUTTON_MIN_W = 88

# 展开：淡入 + 从下往上浮；对话框是模态，收起不做动画，点完就走
_OPEN_ANIM_MS = 150
_GLASS_SETTLE_MS = 220
_ANIM_STEP = 16
_OPEN_SLIDE = 6


def _badge(level: str, size: int = 34) -> Image.Image:
    """画一枚圆形图标：底是层级色，上面一个白色符号。

    ``size`` 是**物理像素**；4 倍尺寸画完再缩放，圆边和符号才不会有
    canvas 那种阶梯。
    """
    scale = 4
    side = max(8, int(size)) * scale
    color = color_of(_LEVEL_COLORS.get(level, T.COLOR_ACCENT))
    image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pen.ellipse((0, 0, side - 1, side - 1), fill=color)

    white = "#ffffff"
    stroke = max(2, side // 12)
    cx = cy = side / 2

    if level == "success":
        # 对勾
        pen.line(
            (cx - side * 0.20, cy + side * 0.01, cx - side * 0.05, cy + side * 0.16),
            fill=white,
            width=stroke,
        )
        pen.line(
            (cx - side * 0.05, cy + side * 0.16, cx + side * 0.22, cy - side * 0.16),
            fill=white,
            width=stroke,
        )
    elif level == "error":
        # 叉
        arm = side * 0.18
        pen.line((cx - arm, cy - arm, cx + arm, cy + arm), fill=white, width=stroke)
        pen.line((cx - arm, cy + arm, cx + arm, cy - arm), fill=white, width=stroke)
    elif level == "warn":
        # 竖线 + 圆点
        pen.line((cx, cy - side * 0.20, cx, cy + side * 0.05), fill=white, width=stroke)
        pen.ellipse(
            (cx - stroke / 2, cy + side * 0.13, cx + stroke / 2, cy + side * 0.13 + stroke),
            fill=white,
        )
    else:
        # 信息：一个 i
        pen.ellipse(
            (cx - stroke / 2, cy - side * 0.21, cx + stroke / 2, cy - side * 0.21 + stroke),
            fill=white,
        )
        pen.line((cx, cy - side * 0.02, cx, cy + side * 0.19), fill=white, width=stroke)

    return image.resize((int(size), int(size)), Image.LANCZOS)


def _round_corners(window: tk.Misc, radius: int = 12) -> None:
    """把无边框窗口裁成圆角，公共逻辑在 :mod:`ctk_kit.popup`。

    对话框是 ``overrideredirect`` 窗口，DWM 圆角对它无效，必须用 region
    硬裁剪，四角才不会留下四个直角。
    """
    round_window_corners(window, radius)


@cached
def _pill_image(width: int, height: int, radius: int, fill: str) -> Image.Image:
    """画按钮的圆角底图；超采样后缩回，边缘才有抗锯齿。"""
    scale = 4
    image = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pen.rounded_rectangle(
        (0, 0, width * scale - 1, height * scale - 1),
        radius=max(0, radius) * scale,
        fill=fill,
    )
    return image.resize((width, height), Image.LANCZOS)


class _CanvasButton:
    """canvas 上自绘的一枚按钮：圆角底图 + 居中文字，带 hover。"""

    def __init__(
        self,
        canvas: tk.Canvas,
        *,
        x: float,
        y: float,
        width: int,
        height: int,
        radius: int,
        label: str,
        fill: str,
        hover: str,
        text_color: str,
        font: Any,
        command: Callable[[], None],
    ) -> None:
        self._canvas = canvas
        self._command = command
        self._tag = f"dialog-button-{id(self)}"
        self._normal = ImageTk.PhotoImage(_pill_image(width, height, radius, fill))
        self._active = ImageTk.PhotoImage(_pill_image(width, height, radius, hover))
        self._image_item = canvas.create_image(
            x, y, anchor="nw", image=self._normal, tags=(self._tag,)
        )
        self._text_item = canvas.create_text(
            x + width / 2,
            y + height / 2,
            text=label,
            fill=text_color,
            font=font,
            tags=(self._tag,),
        )
        canvas.tag_bind(self._tag, "<Enter>", self._on_enter)
        canvas.tag_bind(self._tag, "<Leave>", self._on_leave)
        canvas.tag_bind(self._tag, "<Button-1>", self._on_press)
        canvas.tag_bind(self._tag, "<ButtonRelease-1>", self._on_release)

    def _paint(self, image: ImageTk.PhotoImage) -> None:
        self._canvas.itemconfigure(self._image_item, image=image)

    def _on_enter(self, _event: tk.Event) -> None:
        self._paint(self._active)
        with contextlib.suppress(tk.TclError):
            self._canvas.configure(cursor="hand2")

    def _on_leave(self, _event: tk.Event) -> None:
        self._paint(self._normal)
        with contextlib.suppress(tk.TclError):
            self._canvas.configure(cursor="")

    def _on_press(self, _event: tk.Event) -> None:
        self._paint(self._active)

    def _on_release(self, _event: tk.Event) -> None:
        self._command()


class Dialog(ctk.CTkToplevel):
    """一个等待用户操作的卡片窗口。

    参数:
        master: 父容器；对话框会相对它的窗口居中。
        title: 标题；为空时只显示正文。
        message: 正文，会自动换行。
        detail: 正文下面的小字补充，可以放路径、影响范围这类信息。
        level: ``"info"`` / ``"success"`` / ``"warn"`` / ``"error"``，决定图标颜色。
        buttons: ``[(文字, 返回值), ...]``；默认只有一个「确定」。
            最后一个按钮是主按钮（强调色）。
        prompt: 给初始值就多显示一个输入框，:meth:`show` 返回输入的字符串。
        danger: 主按钮是否用危险色（删除、清空这类操作）。
        width: 对话框宽度（逻辑像素），默认 392。
        glass: 旧参数，``False`` 时不要背景（等于 ``backdrop="none"``）。
        glass_refresh_ms: 背景重截间隔（毫秒）；0 表示每帧连轴刷新（最快）。
        glass_blur / glass_upscale / glass_blur_scale:
            模糊半径（逻辑像素）、升采样倍数、模糊范围系数。
        backdrop: ``"glass"``（截屏模糊，默认）/ ``"gradient"``（固定竖向渐变）/
            ``"none"``（纯卡片色）。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str = "",
        message: str = "",
        detail: str = "",
        level: str = "info",
        buttons: Optional[Sequence[tuple]] = None,
        prompt: Optional[str] = None,
        danger: bool = False,
        width: int = 392,
        glass: bool = True,
        glass_refresh_ms: int = 300,
        glass_blur: int = 20,
        glass_upscale: float = 2.0,
        glass_blur_scale: float = 0.5,
        backdrop: str = "glass",
        gradient_top: Optional[str] = None,
        gradient_bottom: Optional[str] = None,
    ) -> None:
        super().__init__(master)
        self.withdraw()
        # 无边框卡片：没有系统标题栏，弹出来就是一块圆角面板。
        self.overrideredirect(True)
        # 窗口底色就是描边色：canvas 内缩 1px，露出的这一圈负责直边的描边，
        # 圆角处由卡片图四角填的同色补上。
        self.configure(fg_color=T.COLOR_BORDER)
        self._parent_window = master.winfo_toplevel()

        self._result: Any = None
        self._buttons: list = list(buttons) if buttons else [("确定", True)]
        self._prompt = prompt
        self._entry: Optional[FormEntry] = None
        self._entry_item: Optional[int] = None
        self._canvas_buttons: list[_CanvasButton] = []
        self._images: list[ImageTk.PhotoImage] = []
        self._width = max(300, int(width))
        self._glass = glass
        # 0 表示每帧连轴刷新（尽可能快），>0 是固定间隔毫秒
        self._glass_refresh_ms = max(0, int(glass_refresh_ms))
        self._glass_blur = max(1, int(glass_blur))
        self._glass_upscale = max(1.0, float(glass_upscale))
        self._glass_blur_scale = max(0.05, min(2.0, float(glass_blur_scale)))
        self._acrylic_tint = 0xCC201A18
        style = str(backdrop or "none").lower()
        if style not in {"glass", "gradient", "acrylic", "none"}:
            style = "glass"
        # glass=False 是旧参数，等效于关掉背景
        self._backdrop_style = style if glass else "none"
        self._gradient_top = gradient_top
        self._gradient_bottom = gradient_bottom
        self._master = master
        self._backdrop_item: Optional[int] = None
        self._backdrop_photo: Optional[ImageTk.PhotoImage] = None
        # 展开动画：淡入 + 从下方轻轻浮上来
        self._anim_job: Optional[str] = None
        self._anim_started: float = 0.0
        self._refresh_job: Optional[str] = None
        self._frame_pos: tuple[int, int] = (0, 0)
        self._frame_size: tuple[int, int] = (0, 0)

        self._title_text = title
        self._message_text = message
        self._detail_text = detail
        self._level = level
        self._danger = danger

        self._canvas = tk.Canvas(
            self,
            highlightthickness=0,
            borderwidth=0,
            bg=color_of(T.COLOR_CARD),
        )
        if self._backdrop_style == "acrylic":
            # acrylic 模式不用 canvas：canvas 不参与 DWM 合成，压在玻璃上就是实心块
            self._canvas.destroy()
            self._canvas = None
            self._veil: Optional[ctk.CTkFrame] = None
        else:
            self._canvas.pack(fill="both", expand=True, padx=1, pady=1)
            self._veil = None

        self._build()
        self._place_over(master)

        self.bind("<Escape>", lambda _e: self._finish(None))
        self.protocol("WM_DELETE_WINDOW", lambda: self._finish(None))

        self._wheel_bind = None
        self._wheel_bind_linux = None
        self._wheel_bind_linux5 = None
        self._move_bind = None

    # ------------------------------------------------------------ 绘制
    def _build(self) -> None:
        """把所有内容画到 canvas 上，并把宽高定下来。

        先用 ``bbox`` 量出每段文字的真实高度，再依次往下排；宽度固定成
        ``width``，高度跟着内容走。
        """
        if self._backdrop_style == "acrylic":
            self._build_acrylic()
            return
        canvas = self._canvas
        scaling = self._get_window_scaling() or 1.0
        self._scaling = scaling
        s = scaling
        pad = int(round(_PAD * s))
        width_px = max(1, int(round(self._width * s)))
        wrap = width_px - 2 * pad

        title_font = get_font(T.FONT_CARD_TITLE)
        body_font = get_font(T.FONT_BODY)
        small_font = get_font(T.FONT_SMALL)

        cursor = float(pad)

        icon_size = int(round(_ICON * s))
        badge = ImageTk.PhotoImage(_badge(self._level, icon_size))
        self._images.append(badge)
        canvas.create_image(pad, cursor, anchor="nw", image=badge)

        title_h = 0
        if self._title_text:
            item = canvas.create_text(
                pad + icon_size + int(round(_GAP_ICON * s)),
                cursor + icon_size / 2,
                anchor="w",
                text=self._title_text,
                font=title_font,
                fill=color_of(T.COLOR_TEXT),
            )
            title_h = self._text_height(item) or int(round(22 * s))

        cursor += max(icon_size, title_h)

        if self._message_text:
            cursor += (12 * s) if self._title_text else 0
            item = canvas.create_text(
                pad,
                cursor,
                anchor="nw",
                width=wrap,
                text=self._message_text,
                font=body_font,
                fill=color_of(T.COLOR_TEXT_SOFT if self._title_text else T.COLOR_TEXT),
                justify="left",
            )
            cursor += self._text_height(item)

        if self._detail_text:
            cursor += int(round(8 * s))
            item = canvas.create_text(
                pad,
                cursor,
                anchor="nw",
                width=wrap,
                text=self._detail_text,
                font=small_font,
                fill=color_of(T.COLOR_MUTED),
                justify="left",
            )
            cursor += self._text_height(item)

        if self._prompt is not None:
            entry_h = int(round(36 * s))
            self._entry = FormEntry(canvas, placeholder="", height=36)
            self._entry.configure(width=max(40, int(round(wrap / s))))
            self._entry_item = canvas.create_window(
                pad, cursor, anchor="nw", window=self._entry, width=wrap, height=entry_h
            )
            self._entry.insert(0, self._prompt)
            self._entry._entry.bind("<Return>", lambda _e: self._submit_prompt())
            cursor += entry_h + int(round(14 * s))

        cursor += int(round(18 * s))
        button_h = int(round(_BUTTON_H * s))
        radius = int(round(T.RADIUS_SMALL * s))
        gap = int(round(8 * s))

        last = len(self._buttons) - 1
        x_right = float(width_px - pad)
        for index in range(last, -1, -1):
            label, value = self._buttons[index]
            if index == last:
                background = T.COLOR_DANGER if self._danger else T.COLOR_ACCENT
                hover = T.COLOR_DANGER if self._danger else T.COLOR_ACCENT_HOVER
                foreground = T.COLOR_ACCENT_TEXT
            else:
                background = T.COLOR_SOFT
                hover = T.COLOR_SOFT_HOVER
                foreground = T.COLOR_TEXT
            text_w = small_font.measure(str(label))
            button_w = max(int(round(_BUTTON_MIN_W * s)), text_w + int(round(32 * s)))
            x_right -= button_w
            self._canvas_buttons.append(
                _CanvasButton(
                    canvas,
                    x=x_right,
                    y=cursor,
                    width=button_w,
                    height=button_h,
                    radius=radius,
                    label=str(label),
                    fill=color_of(background),
                    hover=color_of(hover),
                    text_color=color_of(foreground),
                    font=small_font,
                    command=lambda v=value: self._finish(v),
                )
            )
            x_right -= gap

        height_px = int(round(cursor + button_h + 16 * s))
        self._frame_size = (width_px, height_px)
        self._wrap = wrap

    def _text_height(self, item: int) -> int:
        """量一段 canvas 文字的实际高度（换行后的高度）。"""
        self._canvas.update_idletasks()
        bbox = self._canvas.bbox(item)
        if not bbox:
            return 0
        return int(bbox[3] - bbox[1])

    # ------------------------------------------------------- acrylic 版
    def _build_acrylic(self) -> None:
        """acrylic 模式：黑底 + 一层 veil，内容用真控件排。

        和 canvas 版的区别只在渲染层：窗口本身是系统玻璃，veil 用纯黑，
        DWM 会把黑色当空白继续透；文字用 ``fg_color="transparent"`` 的
        label，只画字、不带底色块。
        """
        self.configure(fg_color="#000000")
        veil = ctk.CTkFrame(self, fg_color="#000000", corner_radius=0)
        veil.pack(fill="both", expand=True)
        self._veil = veil

        inner = ctk.CTkFrame(veil, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=_PAD, pady=_PAD)

        head = ctk.CTkFrame(inner, fg_color="transparent")
        head.pack(fill="x")
        icon_size = int(round(34 * (self._get_window_scaling() or 1.0)))
        self._acrylic_icon = ImageTk.PhotoImage(_badge(self._level, icon_size))
        # 用 tk.Label：CTkLabel 会抱怨 PhotoImage 不能随 DPI 缩放；图片已经是
        # 物理像素，黑底又正好等于“透明”，不会挡玻璃。
        tk.Label(
            head,
            image=self._acrylic_icon,
            bg="#000000",
            bd=0,
            highlightthickness=0,
        ).pack(side="left")
        ctk.CTkLabel(
            head,
            text=self._title_text or _LEVEL_TITLES.get(self._level, "提示"),
            font=get_font((T.FONT_NAME, 15, "bold")),
            text_color=T.COLOR_TEXT,
        ).pack(side="left", padx=(12, 0))

        if self._message_text:
            ctk.CTkLabel(
                inner,
                text=self._message_text,
                wraplength=max(80, self._width - 2 * _PAD),
                justify="left",
                anchor="w",
                text_color=T.COLOR_TEXT_SOFT,
            ).pack(fill="x", pady=(14, 0))
        if self._detail_text:
            ctk.CTkLabel(
                inner,
                text=self._detail_text,
                wraplength=max(80, self._width - 2 * _PAD),
                justify="left",
                anchor="w",
                text_color=T.COLOR_MUTED,
            ).pack(fill="x", pady=(6, 0))
        if self._prompt is not None:
            self._entry = FormEntry(inner, placeholder=self._prompt)
            self._entry.pack(fill="x", pady=(12, 0))
            self._entry._entry.bind("<Return>", lambda _e: self._submit_prompt())

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(18, 0))
        last = len(self._buttons) - 1
        for index in range(last, -1, -1):
            label, value = self._buttons[index]
            if index == last:
                background = T.COLOR_DANGER if self._danger else T.COLOR_ACCENT
                hover = T.COLOR_DANGER if self._danger else T.COLOR_ACCENT_HOVER
                foreground = T.COLOR_ACCENT_TEXT
            else:
                background = T.COLOR_SOFT
                hover = T.COLOR_SOFT_HOVER
                foreground = T.COLOR_TEXT
            ctk.CTkButton(
                row,
                text=str(label),
                width=_BUTTON_MIN_W,
                height=_BUTTON_H,
                corner_radius=T.RADIUS_SMALL,
                fg_color=background,
                hover_color=hover,
                text_color=foreground,
                font=get_font((T.FONT_NAME, 13)),
                command=lambda v=value: self._finish(v),
            ).pack(side="right", padx=(8, 0))

        self.update_idletasks()
        scaling = self._get_window_scaling() or 1.0
        self._scaling = scaling
        self._frame_size = (
            max(1, int(round(self._width * scaling))),
            max(1, self.winfo_reqheight()),
        )

    # ------------------------------------------------------------ 定位
    def _apply_geometry(
        self, width: int, height: int, left: int, top: int, *, settle: bool = True
    ) -> None:
        """设窗口位置和尺寸；acrylic 窗口把边框算进去，再按客户区校正一次。

        :func:`acrylic_window` 给无边框窗口补了 ``WS_THICKFRAME``，系统多出
        一圈缩放边框。Tk 的 ``geometry()`` 在宽度方向不补这一圈（125% 下客户
        区少 16px），纵向却正好——所以这里只给宽度加上差值，让 Tk 自己算出来
        的客户区就是目标尺寸；之后 :func:`set_client_rect` 再把可能的 1px 取整
        误差校正掉。两步尺寸一致，窗口在可见状态下不会被缩小再撑大，也就不会
        闪出一条玻璃边。

        ``settle=True`` 时先把 ``geometry`` 处理完（等 ``WM_SIZE`` 回来、Tk 的
        几何记录同步）再校正；拖动跟手时传 ``False``，省掉每帧的空闲等待。
        """
        inset_w = 0
        if self._backdrop_style == "acrylic":
            inset_w, _ = client_frame_inset(self)
        with contextlib.suppress(tk.TclError):
            self.geometry(scaled_geometry(self, width + inset_w, height, left, top))
        if self._backdrop_style != "acrylic":
            return
        if settle:
            with contextlib.suppress(tk.TclError):
                self.update_idletasks()
        set_client_rect(self, width, height, left, top)

    def _place_over(self, master: tk.Misc) -> None:
        """在父窗口中间摆好；父窗口不可用时退回屏幕中间。

        宽度固定成 ``width``，只让高度跟着内容走——几种对话框放在一起宽度一致，
        看起来才像同一个组件。

        最后把坐标夹进屏幕：父窗口被拖到屏幕外时，对话框仍然停在看得见的地方，
        不会跟着一起消失。
        """
        self.update_idletasks()
        width, height = self._frame_size
        if width <= 2 or height <= 2:
            width = max(1, int(round(self._width * (self._get_window_scaling() or 1.0))))
            height = max(1, self.winfo_reqheight())
            self._frame_size = (width, height)
        try:
            parent = master.winfo_toplevel()
            left = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
            top = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        except tk.TclError:
            left = (self.winfo_screenwidth() - width) // 2
            top = (self.winfo_screenheight() - height) // 2
        # 夹进屏幕：窗口被拖到屏幕外时，对话框至少还能看见、能点
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        left = min(max(0, left), max(0, screen_w - width))
        top = min(max(0, top), max(0, screen_h - height))
        self._frame_pos = (left, top)
        self._apply_geometry(width, height, left, top)

    def _apply_backdrop(self) -> None:
        """把背景垫在 canvas 最底层：截屏模糊图或固定渐变；失败保持纯色。"""
        if self._backdrop_style in {"none", "acrylic"}:
            return
        width, height = self._frame_size
        if width <= 2 or height <= 2:
            return
        left, top = self._frame_pos
        with contextlib.suppress(Exception):
            scaling = self._get_window_scaling() or 1.0
            if self._backdrop_style == "gradient":
                image = gradient_image(
                    width - 2,
                    height - 2,
                    top=self._gradient_top,
                    bottom=self._gradient_bottom,
                )
            else:
                with excluding_from_capture(self):
                    image = backdrop_image(
                        left + 1,
                        top + 1,
                        width - 2,
                        height - 2,
                        scaling=scaling,
                        radius=T.RADIUS_SMALL,
                        blur=self._glass_blur,
                        upscale=self._glass_upscale,
                        blur_scale=self._glass_blur_scale,
                    )
            if image is None:
                return
            photo = ImageTk.PhotoImage(image)
            self._backdrop_photo = photo
            if self._backdrop_item is None:
                self._backdrop_item = self._canvas.create_image(
                    0, 0, anchor="nw", image=photo
                )
                self._canvas.tag_lower(self._backdrop_item)
            else:
                self._canvas.itemconfigure(self._backdrop_item, image=photo)

    def _refresh_acrylic(self) -> None:
        """重挂一次系统玻璃，并按实际边框校正尺寸。

        ``enable_acrylic()`` 里的 ``SetWindowPos(FRAMECHANGED)`` 会让系统重算
        非客户区，客户区可能又缩回一圈。窗口这时已经显示出来了，重设
        ``geometry`` 会让 Tk 把内容整体重排一帧、闪一下，所以这里只把客户区
        尺寸按原值校正回去，不动 Tk 的几何记录。
        """
        if self._backdrop_style != "acrylic":
            return
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        acrylic_window(self, tint=self._acrylic_tint)
        width, height = self._frame_size
        if width > 2 and height > 2:
            set_client_rect(self, width, height, *self._frame_pos)

    def _start_refresh(self) -> None:
        """持续重截背景：背后内容滚动或变化时，毛玻璃能跟上。"""
        self._cancel_refresh()
        if self._backdrop_style == "acrylic":
            return
        if self._backdrop_style != "glass":
            return
        self._refresh_job = self.after(self._refresh_delay(), self._refresh_backdrop)

    def _refresh_delay(self) -> int:
        """下一帧的等待时间：0 表示连轴跑，实测每帧只受截图+滤波耗时限制。"""
        return 1 if self._glass_refresh_ms <= 0 else self._glass_refresh_ms

    def _refresh_backdrop(self) -> None:
        """定时重截一帧；窗口没了就停。"""
        self._refresh_job = None
        if not self.winfo_exists():
            return
        self._apply_backdrop()
        self._refresh_job = self.after(self._refresh_delay(), self._refresh_backdrop)

    def _cancel_refresh(self) -> None:
        if self._refresh_job is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._refresh_job)
            self._refresh_job = None

    # ------------------------------------------------------------ 结果
    def _submit_prompt(self) -> None:
        """输入框里按回车：等同点主按钮。"""
        self._finish(self._buttons[-1][1])

    def _finish(self, value: Any) -> None:
        """记下返回值并关窗。"""
        self._cancel_refresh()
        if self._prompt is not None and self._entry is not None:
            if value == self._buttons[-1][1]:
                value = self._entry.get()
            else:
                value = None
        self._result = value
        with contextlib.suppress(tk.TclError):
            self.grab_release()
        self.destroy()

    def show(self) -> Any:
        """显示并等待用户操作，返回按下的按钮对应的值。

        关掉窗口或按 Esc 返回 ``None``；有输入框时返回输入的文字。

        模态靠三件事，而不是把父窗口整个禁用：

        - ``grab_set``：客户区的点击、键盘都进不来
        - 父窗口上临时绑 ``<MouseWheel>`` 并 ``return "break"``：滚轮被截住。
          单靠 grab 不行，CTk 的滚动区走的是 ``bind_all``，那条链不受 grab 管
        - 父窗口移动时重新居中：标题栏可以拖，对话框跟着走

        位置会被夹在屏幕内，父窗口拖到屏幕外时对话框仍然可见。
        """
        parent = self._parent_window
        # 父窗口可能已经被拖走：先按当前位置重新居中，再截背后的图
        self._place_over(self._master)
        self._apply_backdrop()
        # transient 让对话框在同一个应用里始终浮在父窗口上面；但它管不住
        # 「切到后台再切回前台」——Windows 重新激活时会按 z-order 重排，
        # 无边框窗口会被主窗口盖住。补一个 -topmost 保证一直在最上层。
        with contextlib.suppress(tk.TclError):
            # acrylic 模式不能设 transient：owned window 在 Win11 上不算
            # “激活窗口”，DWM 会直接给个灰底、不上模糊。
            if self._backdrop_style != "acrylic":
                self.transient(self._master)
                self.attributes("-topmost", True)
        # 先透明再显示：不然第一帧会整块不透明地闪一下。
        # acrylic 模式不能碰 -alpha：设过它的窗口会一直是 layered 的，
        # DWM 的系统玻璃会被摘掉，弹出来就是一片灰。
        if self._backdrop_style != "acrylic":
            with contextlib.suppress(tk.TclError):
                self.attributes("-alpha", 0.0)
        if self._backdrop_style == "acrylic":
            # 先在「还没显示」的状态把玻璃挂好，再 deiconify：窗口第一次
            # 出现在屏幕上就是玻璃，不会先闪一帧亮色底。
            self.update()
            self.update_idletasks()
            width_px, _ = self._frame_size
            self._frame_size = (width_px, max(1, self.winfo_reqheight()))
            # 顺序不能反：挂玻璃会给窗口补上 WS_THICKFRAME，客户区因此比外框
            # 少一圈边框；先挂再定位，_apply_geometry() 才能按实际边框校正。
            acrylic_window(self, tint=self._acrylic_tint)
            self.update()
            self._place_over(self._master)
            self.update()
            self.deiconify()
            self.update()
        else:
            self.update_idletasks()
            self.deiconify()
        if self._backdrop_style == "acrylic":
            # 系统玻璃：DWM 自己切圆角、自己模糊，不用 region 裁。
            # 挂完再 update 一轮，首帧才会直接是玻璃而不是亮灰。
            self._refresh_acrylic()
            self.update()
            # 窗口刚映射时 DWM 的合成还没稳定，先挂一次、稍后再补一次。
            self.after(60, self._refresh_acrylic)
        else:
            _round_corners(self, T.RADIUS_SMALL)
        self.grab_set()

        # 滚轮：拦在 toplevel 这一层，比 bind_all 早一步
        self._wheel_bind = parent.bind("<MouseWheel>", self._block_wheel, add="+")
        self._wheel_bind_linux = parent.bind("<Button-4>", self._block_wheel, add="+")
        self._wheel_bind_linux5 = parent.bind("<Button-5>", self._block_wheel, add="+")
        # 拖动 / 缩放窗口时跟着走
        self._move_bind = parent.bind("<Configure>", self._on_parent_configure, add="+")
        # 父窗口从最小化恢复 / 重新映射时，弹窗可能被压到它下面，补一次置顶
        self._map_bind = parent.bind("<Map>", self._on_parent_map, add="+")

        if self._entry is not None:
            self._entry.focus_set()
            self._entry._entry.icursor("end")
        else:
            self.focus_force()
        if self._backdrop_style != "acrylic":
            self._start_open_anim()
        self._start_refresh()
        try:
            self.wait_window(self)
        finally:
            for event, bind_id in (
                ("<MouseWheel>", self._wheel_bind),
                ("<Button-4>", self._wheel_bind_linux),
                ("<Button-5>", self._wheel_bind_linux5),
                ("<Configure>", self._move_bind),
                ("<Map>", self._map_bind),
            ):
                with contextlib.suppress(tk.TclError):
                    parent.unbind(event, bind_id)
            with contextlib.suppress(tk.TclError):
                self.grab_release()
        return self._result

    def _on_parent_map(self, _event: Optional[tk.Event] = None) -> None:
        """父窗口重新映射（最小化恢复、切前台）时把弹窗再提上来。"""
        if not self.winfo_exists():
            return
        with contextlib.suppress(tk.TclError):
            self.attributes("-topmost", True)
            self.lift()

    def _block_wheel(self, _event: tk.Event) -> str:
        """截住滚轮：对话框打开时背景不该跟着滚。"""
        return "break"

    def _on_parent_configure(self, event: Optional[tk.Event] = None) -> None:
        """父窗口动了就立刻重新居中，拖窗口时对话框跟手走。

        ``<Configure>`` 绑在顶层窗口上会收到所有子控件冒泡上来的事件（滚动页面
        时每帧几十个），所以先按 ``event.widget`` 过滤掉。

        这里直接重排、不隔帧：Windows 上 Tk 处理 ``WM_MOVE`` 时是同步分发
        ``<Configure>`` 的，隔帧会退回主循环，拖动过程中就完全不跟手——
        DropField 的下拉面板能跟手，用的也是这个路子。
        """
        if event is not None:
            with contextlib.suppress(tk.TclError):
                if event.widget is not self._parent_window.winfo_toplevel():
                    return
        self._reposition()

    def _reposition(self) -> None:
        """重新居中；拖动时每帧都会走这里，所以不碰 ``update_idletasks``。

        尺寸已经定下来了（``_build`` 里算过），这里只用现成的宽高和父窗口
        位置重算坐标，再夹进屏幕。
        """
        if not self.winfo_exists():
            return
        # 展开动画期间位置由动画控制，跟手逻辑等它跑完再说
        if self._anim_job is not None:
            return
        parent = self._parent_window.winfo_toplevel()
        width, height = self._frame_size
        if width <= 2 or height <= 2:
            return
        left = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        top = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        left = min(max(0, left), max(0, screen_w - width))
        top = min(max(0, top), max(0, screen_h - height))
        # 位置变了，毛玻璃的截图区域也要跟着变，否则刷出来的是旧位置的画面
        self._frame_pos = (left, top)
        self._apply_geometry(width, height, left, top, settle=False)
        # 拖动中先别重截：每帧截一次既慢又会闪，停下来再刷
        self._reschedule_refresh()

    def _reschedule_refresh(self) -> None:
        """把下一次重截往后推；拖动时会被每帧的 ``<Configure>`` 不断推迟。"""
        if self._backdrop_style != "glass":
            return
        if self._refresh_job is not None:
            with contextlib.suppress(tk.TclError):
                self.after_cancel(self._refresh_job)
        self._refresh_job = self.after(_GLASS_SETTLE_MS, self._refresh_backdrop)

    # ------------------------------------------------------------ 展开动画
    def _start_open_anim(self) -> None:
        """淡入 + 从下方浮上来；跑动画时 ``_reposition`` 让位。"""
        self._anim_started = time.perf_counter()
        self._anim_job = self.after(1, self._open_step)

    def _open_step(self) -> None:
        self._anim_job = None
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        width, height = self._frame_size
        left, top = self._frame_pos
        slide = int(round(_OPEN_SLIDE * (self._get_window_scaling() or 1.0)))
        ratio = (time.perf_counter() - self._anim_started) / (_OPEN_ANIM_MS / 1000.0)
        done = ratio >= 1.0
        eased = 1.0 if done else 1.0 - (1.0 - ratio) ** 3
        offset = 0 if done else int(round((1.0 - eased) * slide))
        with contextlib.suppress(tk.TclError):
            self.geometry(scaled_geometry(self, width, height, left, top + offset))
            self.attributes("-alpha", 1.0 if done else round(eased, 3))
        if not done:
            self._anim_job = self.after(_ANIM_STEP, self._open_step)
        elif self._backdrop_style == "acrylic":
            # alpha 动画期间窗口是 layered 的，系统玻璃会被摘掉；等 alpha
            # 稳定在 1.0 之后再挂一次。
            acrylic_window(self, tint=self._acrylic_tint)
        else:
            _round_corners(self, T.RADIUS_SMALL)

    def destroy(self) -> None:
        """销毁前取消动画和背景刷新，避免窗口没了 after 还在跑。"""
        if self._anim_job is not None:
            with contextlib.suppress(Exception):
                self.after_cancel(self._anim_job)
            self._anim_job = None
        self._cancel_refresh()
        super().destroy()


def alert(
    master: tk.Misc,
    message: str,
    *,
    title: str = "",
    level: str = "info",
    ok: str = "知道了",
    detail: str = "",
    **kwargs: Any,
) -> None:
    """信息框：只有一个「知道了」。

    多出来的关键字（``backdrop="acrylic"`` 之类）直接转给 :class:`Dialog`。
    """
    Dialog(
        master,
        title=title,
        message=message,
        detail=detail,
        **kwargs,
        level=level,
        buttons=[(ok, True)],
    ).show()


def confirm(
    master: tk.Misc,
    message: str,
    *,
    title: str = "",
    level: str = "warn",
    ok: str = "确定",
    cancel: str = "取消",
    detail: str = "",
    danger: bool = False,
    **kwargs: Any,
) -> bool:
    """确认框：返回 ``True`` 表示点了 ``ok``。"""
    result = Dialog(
        master,
        title=title,
        message=message,
        **kwargs,
        detail=detail,
        level=level,
        buttons=[(cancel, False), (ok, True)],
        danger=danger,
    ).show()
    return bool(result)


def prompt(
    master: tk.Misc,
    message: str,
    *,
    title: str = "",
    value: str = "",
    ok: str = "确定",
    cancel: str = "取消",
    detail: str = "",
    **kwargs: Any,
) -> Optional[str]:
    """输入框：返回输入的文字；点取消返回 ``None``。"""
    result = Dialog(
        master,
        title=title,
        message=message,
        **kwargs,
        detail=detail,
        level="info",
        buttons=[(cancel, False), (ok, True)],
        prompt=value,
    ).show()
    return result if isinstance(result, str) else None
