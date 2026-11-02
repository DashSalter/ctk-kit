"""图片查看器：显示图片，滚轮以光标为中心缩放，按住左键拖动看局部。

只依赖 Pillow（``pip install ctk-kit[image]``）。图片按 1:1 像素绘制在 canvas 上，
所以显示是否清晰跟系统缩放无关。

示例::

    viewer = ImageViewer(page, height=320)
    viewer.pack(fill="x")
    viewer.set_image(r"D:\\photos\\shot.png")

交互：
    * 滚轮：以鼠标位置为中心放大/缩小。
    * 左键按住拖动：平移。
    * 双击：回到「适配窗口」。
"""

from __future__ import annotations

import math
import tkinter as tk
from pathlib import Path
from typing import Callable, Optional, Union

import customtkinter as ctk

try:  # Pillow 是可选依赖
    from PIL import Image, ImageTk
except ImportError as exc:  # pragma: no cover - 只在没装 Pillow 时走到
    raise ImportError(
        "ImageViewer 需要 Pillow，先执行 pip install \"ctk-kit[image]\""
    ) from exc

from . import tokens as T
from .branding import empty_state
from .fonts import get_font
from .images import open_image
from .theme import color_of

Source = Union[str, Path, "Image.Image"]

#: 渲染块在可见范围之外多留的余量（相对画布尺寸）。留得多，拖动时不必每帧重采样。
_RENDER_MARGIN = 0.28


class ImageViewer(ctk.CTkFrame):
    """可缩放、可拖动的图片显示区。

    参数:
        master: 父容器。
        height: 控件高度（逻辑像素），默认 320。
        min_zoom / max_zoom: 相对「适配窗口」的缩放范围，默认 0.2 到 8 倍。
        empty_text: 还没设置图片时的提示。

    返回:
        尚未摆位的 ``ImageViewer``；用 :meth:`set_image` 放图。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        height: int = 320,
        min_zoom: float = 1.0,
        max_zoom: float = 8.0,
        empty_text: str = "还没有图片",
        empty_image: bool = True,
        on_zoom: Optional[Callable[[float], None]] = None,
    ) -> None:
        """建图片查看器；内部再建 canvas，图片等 ``set_image`` 时再放。"""
        super().__init__(
            master,
            fg_color=T.COLOR_SOFT,
            border_width=1,
            border_color=T.COLOR_BORDER,
            corner_radius=0,
            height=height,
        )
        self._min_zoom = min_zoom
        self._max_zoom = max_zoom
        self._empty_text = empty_text
        self._empty_image = bool(empty_image)
        self._on_zoom = on_zoom

        self._canvas = tk.Canvas(
            self,
            bg=color_of(T.COLOR_SOFT),
            highlightthickness=0,
            cursor="fleur",
        )
        self._canvas.pack(fill="both", expand=True, padx=1, pady=1)

        self._original: Optional["Image.Image"] = None
        self._photo: Optional["ImageTk.PhotoImage"] = None
        self._item: Optional[int] = None
        self._fit_scale = 1.0
        self._zoom = 1.0
        self._offset = [0.0, 0.0]
        # 整图在画布上的显示尺寸（浮点），以及渲染块左上角与它对应的偏移量
        self._disp_size = (1.0, 1.0)
        self._render_offset = [0.0, 0.0]
        self._auto_fit = True
        self._drag: Optional[tuple[float, float, float, float]] = None

        self._canvas.bind("<Configure>", self._on_configure)
        self._canvas.bind("<MouseWheel>", self._on_wheel)
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<Double-Button-1>", lambda _e: self.fit())

    # ------------------------------------------------------------------ #
    def set_image(self, source: Optional[Source]) -> None:
        """设置要显示的图片；传 ``None`` 清空。

        参数:
            source: 文件路径、``pathlib.Path`` 或已经打开的 PIL 图片。
        """
        if source is None:
            self._original = None
        elif isinstance(source, Image.Image):
            self._original = source.copy()
        else:
            # 路径走缓存：同一文件重复预览不用再读盘、解码
            self._original = open_image(source)
        self._auto_fit = True
        self._zoom = 1.0
        self._render()

    def fit(self) -> None:
        """回到「适配窗口」的缩放和居中位置。"""
        self._auto_fit = True
        self._zoom = 1.0
        self._render()

    def set_zoom(self, value: float) -> None:
        """直接设定缩放倍数（相对适配尺寸），以画布中心为锚点。

        参数:
            value: 目标倍数，会被夹到 ``min_zoom`` / ``max_zoom`` 之间。
        """
        if self._original is None:
            return
        target = max(self._min_zoom, min(self._max_zoom, value))
        if abs(target - self._zoom) < 1e-6:
            return
        canvas_w = max(1, self._canvas.winfo_width())
        canvas_h = max(1, self._canvas.winfo_height())
        anchor_x = (canvas_w / 2 - self._offset[0]) / max(1e-6, self._zoom)
        anchor_y = (canvas_h / 2 - self._offset[1]) / max(1e-6, self._zoom)
        self._zoom = target
        self._offset[0] = canvas_w / 2 - anchor_x * self._zoom
        self._offset[1] = canvas_h / 2 - anchor_y * self._zoom
        self._auto_fit = False
        self._render(keep_view=True)

    def zoom(self) -> float:
        """当前相对适配尺寸的缩放倍数。"""
        return self._zoom

    # ------------------------------------------------------------------ #
    def _on_configure(self, _event: tk.Event) -> None:
        """控件尺寸变化：按新尺寸重画，保留当前视口。"""
        self._render(keep_view=True)

    def _on_wheel(self, event: tk.Event) -> str:
        """滚轮缩放：以光标下的图片点为锚，缩完重画。"""
        if self._original is None:
            return "break"
        step = 1.12 if event.delta > 0 else 1 / 1.12
        target = max(self._min_zoom, min(self._max_zoom, self._zoom * step))
        if abs(target - self._zoom) < 1e-6:
            return "break"

        # 光标下的图片坐标，缩放后仍让这一点停在光标下
        anchor_x = (event.x - self._offset[0]) / max(1e-6, self._zoom)
        anchor_y = (event.y - self._offset[1]) / max(1e-6, self._zoom)
        self._zoom = target
        self._offset[0] = event.x - anchor_x * self._zoom
        self._offset[1] = event.y - anchor_y * self._zoom
        self._auto_fit = False
        self._render(keep_view=True)
        return "break"

    def _on_press(self, event: tk.Event) -> str:
        """按下开始拖拽：记下起点和当时的偏移。"""
        if self._item is None:
            return "break"
        self._drag = (event.x, event.y, self._offset[0], self._offset[1])
        return "break"

    def _on_drag(self, event: tk.Event) -> str:
        """拖拽中：只平移位图，超出预渲染范围才重新采样。"""
        if self._drag is None or self._item is None:
            return "break"
        start_x, start_y, offset_x, offset_y = self._drag
        self._offset[0] = offset_x + (event.x - start_x)
        self._offset[1] = offset_y + (event.y - start_y)
        self._auto_fit = False
        # 渲染块比画布大一圈，平移时只挪这张位图，不重新采样；挪到头了才重画
        self._canvas.move(
            self._item,
            self._offset[0] - self._render_offset[0],
            self._offset[1] - self._render_offset[1],
        )
        if not self._region_covers():
            self._render(keep_view=True)
        return "break"

    def _on_release(self, _event: tk.Event) -> str:
        """松开：结束拖拽，把偏移夹回边界并重画。"""
        self._drag = None
        self._clamp_offset()
        self._render(keep_view=True)
        return "break"

    # ------------------------------------------------------------------ #
    def _render(self, *, keep_view: bool = False) -> None:
        """按当前缩放和偏移重画一张位图；``keep_view`` 时保留已有视图状态。"""
        canvas_w = max(1, self._canvas.winfo_width())
        canvas_h = max(1, self._canvas.winfo_height())
        self._canvas.delete("all")
        self._item = None
        self._photo = None

        if self._original is None:
            if self._empty_image:
                empty_state(self, self._canvas, canvas_w, canvas_h, self._empty_text)
            else:
                self._canvas.create_text(
                    canvas_w / 2,
                    canvas_h / 2,
                    text=self._empty_text,
                    font=get_font(T.FONT_SMALL),
                    fill=color_of(T.COLOR_FAINT),
                )
            if self._on_zoom is not None:
                self._on_zoom(1.0)
            return

        image = self._original
        if self._auto_fit:
            self._fit_scale = min(
                canvas_w / image.width,
                canvas_h / image.height,
                1.0,
            )
            self._zoom = 1.0

        scale = self._fit_scale * self._zoom
        disp_w = max(1.0, image.width * scale)
        disp_h = max(1.0, image.height * scale)
        self._disp_size = (disp_w, disp_h)

        if self._auto_fit or not keep_view:
            self._offset[0] = (canvas_w - disp_w) / 2
            self._offset[1] = (canvas_h - disp_h) / 2
        self._clamp_offset()

        # 只渲染画布上看得见的那一块，四周再外扩一圈：放大到 8 倍时若整图重采样，
        # 会去生成一张上亿像素的位图，越放越卡；按可见块画，代价与倍率无关。
        margin = max(canvas_w, canvas_h) * _RENDER_MARGIN
        ox, oy = self._offset
        left = max(0.0, ox - margin)
        top = max(0.0, oy - margin)
        right = min(float(canvas_w), ox + disp_w + margin)
        bottom = min(float(canvas_h), oy + disp_h + margin)
        if right - left < 1 or bottom - top < 1:
            if self._on_zoom is not None:
                self._on_zoom(self._zoom)
            return

        sx0 = max(0, int((left - ox) / scale))
        sy0 = max(0, int((top - oy) / scale))
        sx1 = min(image.width, int(math.ceil((right - ox) / scale)))
        sy1 = min(image.height, int(math.ceil((bottom - oy) / scale)))
        sx1 = max(sx1, sx0 + 1)
        sy1 = max(sy1, sy0 + 1)
        # 目标尺寸必须由「取整后的源矩形」反算，不能直接用可见区的宽度：
        # 两边各自取整会让宽高比对不上，图片看着被压扁成方块。
        crop_w = sx1 - sx0
        crop_h = sy1 - sy0
        target_w = max(1, int(round(crop_w * scale)))
        target_h = max(1, int(round(crop_h * scale)))
        pos_x = ox + sx0 * scale
        pos_y = oy + sy0 * scale

        crop = image.crop((sx0, sy0, sx1, sy1))
        # 放大时 BICUBIC 和 LANCZOS 肉眼几乎没差，但快三成；缩小时才用 LANCZOS 保细节
        enlarging = target_w >= crop_w
        resample = Image.BICUBIC if enlarging else Image.LANCZOS
        resized = crop.resize((target_w, target_h), resample)
        self._photo = ImageTk.PhotoImage(resized)
        self._render_offset = [self._offset[0], self._offset[1]]
        self._item = self._canvas.create_image(
            pos_x, pos_y, anchor="nw", image=self._photo
        )
        if self._on_zoom is not None:
            self._on_zoom(self._zoom)

    def _region_covers(self) -> bool:
        """当前渲染块是否够大，挪动它也不会露出空白。"""
        if self._item is None:
            return False
        x0, y0, x1, y1 = self._canvas.bbox(self._item)
        # 留 1px 容差：渲染块的尺寸是取整算出来的，可能比画布差一像素
        return (
            x0 <= 1
            and y0 <= 1
            and x1 >= self._canvas.winfo_width() - 1
            and y1 >= self._canvas.winfo_height() - 1
        )

    def _clamp_offset(self) -> None:
        """图片比窗口小时居中；比窗口大时别拖出太多空白。"""
        canvas_w = max(1, self._canvas.winfo_width())
        canvas_h = max(1, self._canvas.winfo_height())
        disp_w, disp_h = self._disp_size

        if disp_w <= canvas_w:
            self._offset[0] = (canvas_w - disp_w) / 2
        else:
            self._offset[0] = min(0.0, max(canvas_w - disp_w, self._offset[0]))
        if disp_h <= canvas_h:
            self._offset[1] = (canvas_h - disp_h) / 2
        else:
            self._offset[1] = min(0.0, max(canvas_h - disp_h, self._offset[1]))
