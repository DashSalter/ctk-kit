"""颜色选择器：点色块从预设颜色里挑一个。

用法::

    from ctk_kit import ColorPicker

    picker = ColorPicker(card, value="#2563eb", command=lambda c: print(c))
    picker.pack(side="left")

    picker.get()          # 当前颜色
    picker.set("#dc2626") # 直接改

``colors`` 可以换成自己的色板；``command`` 在用户选色时触发，``set()``
默认不触发。

色板点不到想要的颜色时，用 :class:`ColorDialog` 弹一个完整取色面板
（HSV 色域 + 色相条 + hex / RGB / HSV / HSL 输入）::

    color = ColorDialog(app, value="#2563eb").show()  # 取消返回 None
"""

from __future__ import annotations

import colorsys
import tkinter as tk
from typing import Any, Callable, List, Optional, Sequence

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

from . import tokens as T
from .branding import dim_image, set_window_icon
from .buttons import PrimaryButton, SecondaryButton
from .context_menu import attach_menu
from .core.win32 import enable_acrylic
from .fonts import get_font
from .inputs import FormEntry, Segmented
from .theme import is_win11, set_titlebar_dark

__all__ = ["ColorPicker", "ColorDialog"]

ColorCommand = Optional[Callable[[str], None]]

#: 默认色板：常用主色 + 深浅灰，够覆盖大多数场景。
_SWATCHES = [
    "#2563eb",
    "#0891b2",
    "#059669",
    "#ca8a04",
    "#ea580c",
    "#dc2626",
    "#db2777",
    "#7c3aed",
    "#475569",
    "#0f172a",
    "#ffffff",
    "#94a3b8",
]


class ColorPicker(ctk.CTkFrame):
    """带色块预览的下拉选色控件。

    参数:
        master: 父容器。
        value: 初始颜色，默认主色蓝。
        colors: 自定义色板（hex 字符串列表）；不传用内置 12 色。
        command: 选色回调，参数是 hex 字符串。
        width: 控件宽度，默认 130。
        **kwargs: 透传给外层 ``CTkFrame``。

    方法:
        get(): 当前颜色。
        set(color, notify=False): 改颜色；``notify=True`` 时也回调。
        open() / close() / toggle(): 手动控制色板。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        value: str = "#2563eb",
        colors: Optional[Sequence[str]] = None,
        command: ColorCommand = None,
        width: int = 130,
        **kwargs: Any,
    ) -> None:
        """建颜色选择器；色板默认 4 列 3 行。"""
        super().__init__(
            master,
            fg_color=T.COLOR_INPUT,
            border_width=1,
            border_color=T.COLOR_BORDER_INPUT,
            corner_radius=T.RADIUS_SMALL,
            width=width,
            height=38,
            **kwargs,
        )
        self.pack_propagate(False)

        self._value = value
        self._command = command
        self._colors: List[str] = list(colors) if colors else list(_SWATCHES)

        self._swatch = ctk.CTkButton(
            self,
            text="",
            width=22,
            height=22,
            corner_radius=4,
            fg_color=value,
            hover_color=value,
            border_width=1,
            border_color=T.COLOR_BORDER,
            command=self.toggle,
        )
        self._swatch.pack(side="left", padx=(8, 6))

        self._label = ctk.CTkLabel(
            self,
            text=value,
            font=get_font(T.FONT_TINY),
            text_color=T.COLOR_TEXT,
            anchor="w",
        )
        self._label.pack(side="left", fill="x", expand=True)

        self._arrow = ctk.CTkButton(
            self,
            text="▾",
            width=26,
            height=26,
            corner_radius=6,
            fg_color="transparent",
            hover_color=T.COLOR_SOFT,
            text_color=T.COLOR_MUTED,
            font=get_font((T.FONT_NAME, 16)),
            command=self.toggle,
        )
        self._arrow.pack(side="right", padx=(0, 6))

        menu = attach_menu(self, [("复制颜色", self._copy_color)], deep=True)
        menu.add_command(
            "粘贴颜色", self._paste_color, enabled=self._clipboard_is_color
        )

    def _copy_color(self) -> None:
        """复制当前颜色的 hex 字符串。"""
        value = self.get()
        self.clipboard_clear()
        self.clipboard_append(value)
        self.update_idletasks()

    def _paste_color(self) -> None:
        """把剪贴板里的颜色贴进来（等同于用户选了这个颜色）。"""
        color = self._clipboard_color()
        if color:
            self.set(color, notify=True)

    def _clipboard_color(self) -> str:
        """剪贴板里的颜色，规范成 ``#rrggbb``；不是颜色时返回空字符串。"""
        try:
            text = str(self.clipboard_get()).strip()
        except Exception:  # noqa: BLE001 - 剪贴板为空或放的不是文本
            return ""
        rgb = _parse_hex(text)
        return _hex_of(rgb) if rgb is not None else ""

    def _clipboard_is_color(self, _source: Any = None) -> bool:
        """剪贴板里有没有能认出来的颜色（菜单据此灰掉「粘贴颜色」）。"""
        return self._clipboard_color() != ""

    # --- 对外 ---
    def get(self) -> str:
        """当前颜色。"""
        return self._value

    def set(self, color: str, notify: bool = False) -> None:
        """改颜色；``notify=True`` 时也触发 ``command``。"""
        self._value = color
        self._swatch.configure(fg_color=color, hover_color=color)
        self._label.configure(text=color)
        if notify and self._command is not None:
            self._command(color)

    def configure(self, require_redraw: bool = False, **kwargs: Any) -> Any:
        """支持 ``configure(command=...)`` / ``configure(value=...)``。"""
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "value" in kwargs:
            self.set(str(kwargs.pop("value")))
        if kwargs:
            return super().configure(require_redraw=require_redraw, **kwargs)
        return self

    def open(self) -> None:
        """打开取色面板。面板是模态的，关掉之后才返回。"""
        self._open_dialog()

    def close(self) -> None:
        """接口占位：取色面板是模态窗口，由它自己关。"""

    def toggle(self) -> None:
        """点色块或箭头都直接打开面板。"""
        self._open_dialog()

    def _open_dialog(self) -> None:
        """打开完整取色面板，选完直接应用到控件上。"""
        color = ColorDialog(self, value=self._value, colors=self._colors).show()
        if color:
            self.set(color, notify=True)

    # --- 内部 ---


# ---------------------------------------------------------------- 完整取色面板


def _parse_hex(text: str) -> Optional[tuple]:
    """``#rgb`` / ``#rrggbb`` → ``(r, g, b)``；解析失败返回 ``None``。"""
    text = str(text or "").strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6:
        return None
    try:
        return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def _hex_of(rgb: Sequence[int]) -> str:
    """``(r, g, b)`` → ``#rrggbb``。"""
    r, g, b = (max(0, min(255, int(c))) for c in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def _rgb255(rgb: Sequence[float]) -> tuple:
    """``colorsys`` 的 0–1 浮点 RGB → 0–255 整数元组。"""
    return tuple(max(0, min(255, round(c * 255))) for c in rgb)


def _hue_row(size: int) -> Image.Image:
    """横向彩虹：从左到右 0→360°，每列同一色相。"""
    data = bytearray()
    for x in range(size):
        data += bytes(_rgb255(colorsys.hsv_to_rgb(x / max(1, size - 1), 1.0, 1.0)))
    return Image.frombytes("RGB", (size, 1), bytes(data)).resize((size, size))


def _hs_image(size: int) -> Image.Image:
    """色相（横向 0→1）× 饱和度（纵向 1→0）平面，明度固定 1。"""
    hue = _hue_row(size)
    white = Image.new("RGB", (size, size), "#ffffff")
    # 纵向遮罩：顶部 255（保留彩色），底部 0（变成白）。
    column = bytes(round(255 * (size - 1 - i) / (size - 1)) for i in range(size))
    mask = Image.frombytes("L", (1, size), column).resize((size, size))
    return Image.composite(hue, white, mask)


def _marker_image(radius: int) -> Image.Image:
    """取色光标的圆环：白圈 + 1px 黑边，浅色区和深色区都看得清。

    4 倍画完再 LANCZOS 缩回，边缘平滑，不会像 canvas 的 oval 那样锯齿。
    """
    scale = 4
    side = (radius + 1) * 2
    big = side * scale
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    center = big / 2
    outer = radius * scale
    pen.ellipse(
        (center - outer, center - outer, center + outer, center + outer),
        outline="#000000",
        width=scale,
    )
    inner = outer - scale
    pen.ellipse(
        (center - inner, center - inner, center + inner, center + inner),
        outline="#ffffff",
        width=2 * scale,
    )
    return image.resize((side, side), Image.LANCZOS)


def _value_image(hue: float, sat: float, width: int, height: int) -> Image.Image:
    """明度条：顶部是当前色相 / 饱和度下的最亮色，底部是黑。"""
    bright = Image.new(
        "RGB", (width, height), _rgb255(colorsys.hsv_to_rgb(hue, sat, 1.0))
    )
    black = Image.new("RGB", (width, height), "#000000")
    column = bytes(round(255 * (height - 1 - i) / (height - 1)) for i in range(height))
    mask = Image.frombytes("L", (1, height), column).resize((width, height))
    return Image.composite(bright, black, mask)


#: 毛玻璃的透明键色：DWM 只把纯黑当全透明，窗口底铺它就透出模糊的桌面。
_GLASS_VEIL = "#000000"

#: 玻璃 tint（0xAABBGGRR）：和 App 默认一致，alpha 0xE6 + 底色 #181A20。
_GLASS_TINT = 0xE6201A18

#: 玻璃窗口会给内容叠约 25% 的白，画板先减掉同样的量，显示出来才是原色。
_BOARD_DIM = 0.25
# 色板描边：预压一档灰，叠上玻璃那层白之后正好是浅灰，不会发白。
_BOARD_BORDER = "#1D1D1F"


class ColorDialog(ctk.CTkToplevel):
    """完整取色面板：色相/饱和度方块 + 明度条 + hex / RGB / HSV / HSL 输入。

    窗口是系统毛玻璃：底色纯黑当透明键，DWM 自己模糊背后的内容；标题栏
    交还 DWM，不涂纯色。左上角图标默认用库自带的 logo。

    参数:
        master: 父容器；对话框相对它的窗口居中。
        value: 初始颜色 ``#rrggbb``（也接受 ``#rgb``）。
        title: 窗口标题，默认「选择颜色」。
        command: 点「确定」后的回调，参数是 ``#rrggbb``。
        icon: 标题栏 / 任务栏图标路径；``None`` 用库自带的 logo。

    用法::

        color = ColorDialog(app, value="#2563eb").show()
        if color:
            print(color)

    :meth:`show` 会一直阻塞到对话框关闭（``wait_window``），返回选中的
    颜色；点「取消」、按 Esc 或直接关掉窗口返回 ``None``。

    面板里能做的事：
    - 左边方块上拖动选色相（横）和饱和度（纵），右边竖条上拖动选明度；
    - 直接输入 hex；
    - 用下拉框把右侧三个数值框切成 RGB / HSV / HSL，改完回车生效。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        value: str = "#2563eb",
        title: str = "选择颜色",
        command: Optional[Callable[[str], None]] = None,
        icon: Optional[str] = None,
        colors: Optional[Sequence[str]] = None,
    ) -> None:
        # 屏蔽 CTk 自带的标题栏染色：它会先 withdraw 再 deiconify，而且把
        # 标题栏涂成实色，玻璃就断了；改用本库的 set_titlebar_dark(glass=True)。
        self._deactivate_windows_window_header_manipulation = True
        super().__init__(master)
        self.withdraw()
        self.title(title)
        self.configure(fg_color=_GLASS_VEIL)
        self.resizable(False, False)
        # Win11 上 owned window 会被 DWM 当成「非激活」，玻璃直接变灰；所以
        # 不设 transient，改用置顶让对话框浮在父窗口上面（关掉就没了）。
        try:
            self.attributes("-topmost", True)
        except tk.TclError:
            pass

        self._icon = icon
        self._command = command
        self._result: Optional[str] = None
        self._updating = False
        self._scale = max(1.0, float(self.winfo_fpixels("1i")) / 96.0)
        self._size = max(120, int(200 * self._scale))
        self._bar_w = max(12, int(16 * self._scale))
        self._area_photo: Optional[ImageTk.PhotoImage] = None
        self._bar_photo: Optional[ImageTk.PhotoImage] = None
        self._area_image_id: Optional[int] = None
        self._bar_image_id: Optional[int] = None
        self._area_marker: Optional[int] = None
        self._bar_marker: Optional[int] = None
        self._area_marker_photo: Optional[ImageTk.PhotoImage] = None
        self._bar_marker_photo: Optional[ImageTk.PhotoImage] = None

        rgb = _parse_hex(value) or (37, 99, 235)
        self._rgb = tuple(rgb)
        self._hsv = list(colorsys.rgb_to_hsv(*(c / 255.0 for c in self._rgb)))
        self._colors: List[str] = list(colors) if colors else list(_SWATCHES)

        self._build()
        self._bind_events()
        self._refresh()
        self.update_idletasks()
        self._place()
        self._apply_icon()
        self._apply_glass()
        self.protocol("WM_DELETE_WINDOW", lambda: self._finish(None))

    # ------------------------------------------------------------ 界面
    def _build(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(padx=10, pady=10)

        canvas_col = ctk.CTkFrame(body, fg_color="transparent")
        canvas_col.grid(row=0, column=0, rowspan=2, sticky="nw")

        self._area = tk.Canvas(
            canvas_col,
            width=self._size,
            height=self._size,
            bd=0,
            highlightthickness=0,
        )
        self._area.pack(side="left")
        self._bar = tk.Canvas(
            canvas_col,
            width=self._bar_w,
            height=self._size,
            bd=0,
            highlightthickness=0,
        )
        self._bar.pack(side="left", padx=(10, 0))

        side = ctk.CTkFrame(body, fg_color="transparent")
        side.grid(row=0, column=1, rowspan=2, padx=(12, 0), sticky="nsew")

        preview_row = ctk.CTkFrame(side, fg_color="transparent")
        preview_row.pack(fill="x")
        self._preview = ctk.CTkFrame(
            preview_row,
            width=40,
            height=32,
            corner_radius=6,
            fg_color=_hex_of(self._rgb),
        )
        self._preview.pack(side="left")
        self._preview.pack_propagate(False)
        self._hex = FormEntry(preview_row, height=32)
        self._hex.configure(width=118, font=get_font(T.FONT_TINY))
        self._hex.pack(side="left", padx=(8, 0), fill="x", expand=True)

        mode_row = ctk.CTkFrame(side, fg_color="transparent")
        mode_row.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(
            mode_row,
            text="模式",
            width=40,
            anchor="w",
            font=get_font(T.FONT_TINY),
            text_color=T.COLOR_MUTED,
        ).pack(side="left", padx=(0, 8))
        self._mode = Segmented(
            mode_row,
            ["RGB", "HSV", "HSL"],
            lambda _value: self._sync_fields(),
            width=150,
            height=30,
            font=T.FONT_TINY,
        )
        self._mode.pack(side="left", fill="x", expand=True)

        self._num_entries: List[ctk.CTkEntry] = []
        self._num_labels: List[ctk.CTkLabel] = []
        for index in range(3):
            row = ctk.CTkFrame(side, fg_color="transparent")
            row.pack(fill="x", pady=(10 if index == 0 else 7, 0))
            label = ctk.CTkLabel(
                row,
                text="",
                width=40,
                anchor="w",
                font=get_font(T.FONT_TINY),
                text_color=T.COLOR_MUTED,
            )
            label.pack(side="left", padx=(0, 8))
            entry = FormEntry(row, height=30)
            entry.configure(width=100, font=get_font(T.FONT_TINY))
            entry.pack(side="left", fill="x", expand=True)
            self._num_entries.append(entry)
            self._num_labels.append(label)

        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self._body = body

        # 参考色放在「取消 / 确定」左边的空白里：点一下跳到那个颜色，
        # 不直接关面板，还能接着微调。
        if self._colors:
            swatches = ctk.CTkFrame(buttons, fg_color="transparent")
            swatches.pack(side="left")
            for color in self._colors:
                ctk.CTkButton(
                    swatches,
                    text="",
                    width=20,
                    height=20,
                    corner_radius=5,
                    fg_color=color,
                    hover_color=color,
                    border_width=1,
                    border_color=T.COLOR_BORDER,
                    command=lambda c=color: self._use_swatch(c),
                ).pack(side="left", padx=(0, 5))

        actions = ctk.CTkFrame(buttons, fg_color="transparent")
        actions.pack(side="right")
        SecondaryButton(
            actions,
            "取消",
            lambda: self._finish(None),
            width=84,
            height=32,
            border=True,
        ).pack(side="left", padx=(0, 8))
        PrimaryButton(
            actions,
            "确定",
            lambda: self._finish(self._hex_text()),
            width=84,
            height=32,
        ).pack(side="left")

    def _bind_events(self) -> None:
        self._area.bind("<Button-1>", self._on_area)
        self._area.bind("<B1-Motion>", self._on_area)
        self._bar.bind("<Button-1>", self._on_bar)
        self._bar.bind("<B1-Motion>", self._on_bar)
        self._hex.bind("<Return>", self._apply_hex)
        self._hex.bind("<FocusOut>", self._apply_hex)
        for entry in self._num_entries:
            entry.bind("<Return>", self._apply_numbers)
            entry.bind("<FocusOut>", self._apply_numbers)
        self.bind("<Escape>", lambda _event: self._finish(None))

    # ------------------------------------------------------------ 对外
    def show(self) -> Optional[str]:
        """显示并等待关闭，返回选中的 ``#rrggbb``；取消返回 ``None``。"""
        self.update_idletasks()
        self._place()
        self.deiconify()
        self.lift()
        # 窗口刚映射时 DWM 合成还没稳定，先挂一次、稍后再补一次玻璃。
        self.after(60, self._apply_glass)
        try:
            self.wait_visibility()
            self.grab_set()
        except Exception:  # noqa: BLE001 - 无窗口管理器时跳过模态
            pass
        self.focus_set()
        self.wait_window(self)
        return self._result

    # ------------------------------------------------------------ 绘制
    def _refresh(self) -> None:
        """按当前 HSV 重算 RGB，刷新色相/饱和度平面、明度条和输入框。"""
        hue, sat, val = self._hsv
        self._rgb = _rgb255(colorsys.hsv_to_rgb(hue, sat, val))
        if self._area_image_id is None:
            self._draw_area()
        self._draw_bar()
        self._draw_markers()
        self._sync_fields()

    def _draw_area(self) -> None:
        """画 H×S 平面：横轴色相、纵轴饱和度，明度固定为 1。"""
        image = dim_image(_hs_image(self._size), _BOARD_DIM)
        self._area_photo = ImageTk.PhotoImage(image)
        if self._area_image_id is None:
            self._area_image_id = self._area.create_image(
                0, 0, anchor="nw", image=self._area_photo
            )
        else:
            self._area.itemconfigure(self._area_image_id, image=self._area_photo)
        # 浅色分割线：色板边缘包一圈，和输入框的描边同色。
        self._area.delete("frame")
        self._area.create_rectangle(
            0,
            0,
            self._size - 1,
            self._size - 1,
            outline=_BOARD_BORDER,
            width=1,
            tags="frame",
        )

    def _draw_bar(self) -> None:
        """画明度条：顶部是当前色相/饱和度下的最亮色，底部到黑。"""
        image = dim_image(
            _value_image(self._hsv[0], self._hsv[1], self._bar_w, self._size),
            _BOARD_DIM,
        )
        self._bar_photo = ImageTk.PhotoImage(image)
        if self._bar_image_id is None:
            self._bar_image_id = self._bar.create_image(
                0, 0, anchor="nw", image=self._bar_photo
            )
        else:
            self._bar.itemconfigure(self._bar_image_id, image=self._bar_photo)
        self._bar.delete("frame")
        self._bar.create_rectangle(
            0,
            0,
            self._bar_w - 1,
            self._size - 1,
            outline=_BOARD_BORDER,
            width=1,
            tags="frame",
        )

    def _draw_markers(self) -> None:
        """取色光标用图片画（4 倍超采样），边缘比 canvas 的 oval 干净。"""
        size = self._size - 1
        radius = max(5, int(6 * self._scale))
        x = self._hsv[0] * size
        y = (1.0 - self._hsv[1]) * size
        if self._area_marker is None:
            self._area_marker_photo = ImageTk.PhotoImage(_marker_image(radius))
            self._area_marker = self._area.create_image(
                x, y, image=self._area_marker_photo
            )
        else:
            self._area.coords(self._area_marker, x, y)

        bar_y = (1.0 - self._hsv[2]) * size
        center_x = self._bar_w / 2
        if self._bar_marker is None:
            self._bar_marker_photo = ImageTk.PhotoImage(_marker_image(radius))
            self._bar_marker = self._bar.create_image(
                center_x, bar_y, image=self._bar_marker_photo
            )
        else:
            self._bar.coords(self._bar_marker, center_x, bar_y)

    def _sync_fields(self) -> None:
        """把当前颜色写回 hex 框、预览块和三个数值框。"""
        if self._updating:
            return
        self._updating = True
        try:
            color = self._hex_text()
            self._hex.delete(0, "end")
            self._hex.insert(0, color)
            self._preview.configure(fg_color=color)

            mode = self._mode.get()
            if mode == "RGB":
                numbers = list(self._rgb)
                labels = ["红", "绿", "蓝"]
            elif mode == "HSV":
                numbers = [
                    round(self._hsv[0] * 360),
                    round(self._hsv[1] * 100),
                    round(self._hsv[2] * 100),
                ]
                labels = ["色相", "饱和", "明度"]
            else:
                hue, light, sat = colorsys.rgb_to_hls(
                    *(c / 255.0 for c in self._rgb)
                )
                numbers = [round(hue * 360), round(sat * 100), round(light * 100)]
                labels = ["色相", "饱和", "亮度"]

            for entry, number, label, name in zip(
                self._num_entries, numbers, self._num_labels, labels
            ):
                entry.delete(0, "end")
                entry.insert(0, str(int(number)))
                label.configure(text=name)
        finally:
            self._updating = False

    # ------------------------------------------------------------ 交互
    def _on_area(self, event: tk.Event) -> None:
        size = max(1, self._size - 1)
        self._hsv[0] = max(0.0, min(1.0, event.x / size))
        self._hsv[1] = max(0.0, min(1.0, 1.0 - event.y / size))
        self._refresh()

    def _on_bar(self, event: tk.Event) -> None:
        size = max(1, self._size - 1)
        self._hsv[2] = max(0.0, min(1.0, 1.0 - event.y / size))
        self._refresh()

    def _apply_hex(self, _event: Optional[tk.Event] = None) -> None:
        if self._updating:
            return
        rgb = _parse_hex(self._hex.get())
        if rgb is None:
            self._sync_fields()
            return
        self._set_rgb(rgb)

    def _apply_numbers(self, _event: Optional[tk.Event] = None) -> None:
        if self._updating:
            return
        try:
            values = [float(entry.get()) for entry in self._num_entries]
        except ValueError:
            self._sync_fields()
            return

        mode = self._mode.get()
        try:
            if mode == "RGB":
                self._set_rgb(tuple(max(0, min(255, round(v))) for v in values))
            elif mode == "HSV":
                self._hsv = [
                    (values[0] % 360) / 360.0,
                    max(0.0, min(1.0, values[1] / 100.0)),
                    max(0.0, min(1.0, values[2] / 100.0)),
                ]
                self._refresh()
            else:
                rgb = colorsys.hls_to_rgb(
                    (values[0] % 360) / 360.0,
                    max(0.0, min(1.0, values[2] / 100.0)),
                    max(0.0, min(1.0, values[1] / 100.0)),
                )
                self._set_rgb(_rgb255(rgb))
        except Exception:  # noqa: BLE001 - 输入不合法时还原
            self._sync_fields()

    def _set_rgb(self, rgb: Sequence[int]) -> None:
        self._rgb = tuple(max(0, min(255, int(c))) for c in rgb)
        self._hsv = list(colorsys.rgb_to_hsv(*(c / 255.0 for c in self._rgb)))
        self._refresh()

    def _use_swatch(self, color: str) -> None:
        """点参考色块：跳到那个颜色（不直接关面板，还能再微调）。"""
        rgb = _parse_hex(color)
        if rgb:
            self._set_rgb(rgb)

    def _hex_text(self) -> str:
        return _hex_of(self._rgb)

    # ------------------------------------------------------------ 收尾
    def _finish(self, color: Optional[str]) -> None:
        self._result = color
        try:
            self.grab_release()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.destroy()
        except Exception:  # noqa: BLE001
            pass
        if color and self._command is not None:
            self._command(color)

    def _place(self) -> None:
        """把对话框放到父窗口中间，贴着屏幕边就往里收。"""
        try:
            top = self.master.winfo_toplevel()
            top.update_idletasks()
            width = self._body.winfo_reqwidth() - 20
            height = self._body.winfo_reqheight() - 20
            x = top.winfo_rootx() + (top.winfo_width() - width) // 2
            y = top.winfo_rooty() + (top.winfo_height() - height) // 2
            x = max(0, min(x, self.winfo_screenwidth() - width))
            y = max(0, min(y, self.winfo_screenheight() - height))
            self.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:  # noqa: BLE001
            pass

    def _apply_icon(self) -> None:
        """标题栏 / 任务栏图标：默认用库自带的 logo。"""
        try:
            set_window_icon(self, path=self._icon)
        except Exception:  # noqa: BLE001 - 图标缺失时保持系统默认
            pass

    def _apply_glass(self) -> None:
        """挂系统毛玻璃：黑底当透明键，标题栏交还 DWM。"""
        try:
            self.configure(fg_color=_GLASS_VEIL)
        except Exception:  # noqa: BLE001 - 老窗口没有 fg_color
            pass
        dark = ctk.get_appearance_mode() == "Dark"
        try:
            if is_win11():
                # 选色面板固定 Mica：系统背板 38=2，不跟主题里的 accent 走。
                enable_acrylic(
                    self,
                    tint=None,
                    dark=dark,
                    system_backdrop=2,
                    frame=False,
                    extend=True,
                )
            else:
                enable_acrylic(
                    self,
                    tint=_GLASS_TINT,
                    dark=dark,
                    frame=False,
                    extend=True,
                )
        except Exception:  # noqa: BLE001 - 非 Windows 或 API 不可用
            pass
        try:
            set_titlebar_dark(self, dark, glass=True)
        except Exception:  # noqa: BLE001 - 非 Windows 或老系统
            pass
