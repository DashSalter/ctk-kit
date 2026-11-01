"""图片页：显示图片、滚轮缩放、按住左键拖动看局部、双击复位。

和 ``table_page.py`` 一样拆成「UI 类 + 事件类」：``ImagePageUI`` 只建控件，
``ImagePage`` 在构造时自动 ``bind_events()``，缩放回调也统一在事件类里接上。
示例图片是现场用 Pillow 画的，仓库里不放素材文件。
"""

from __future__ import annotations

import tkinter as tk

from ctk_kit import (
    Card,
    FieldLabel,
    Frame,
    HintLabel,
    ImageViewer,
    PageBase,
    PageHeader,
    Scrollable,
    SecondaryButton,
    TextArea,
    tokens as T,
    CodePanel,
)

#: 代码块字体：等宽，比正文大一点，展开后不用凑近看。
CODE_FONT = ("Consolas", 15)

CODE_VIEWER = '''from ctk_kit import ImageViewer

viewer = ImageViewer(
    frame,
    height=320,
    min_zoom=1.0,      # 最小就是「适配窗口」，不会缩成一团
    max_zoom=8.0,      # 放大上限
    empty_text="还没有图片",
    on_zoom=lambda z: print(f"{z:.0%}"),   # 倍率变化回调
)
viewer.pack(fill="both", expand=True)

viewer.set_image(r"D:\\photos\\shot.png")   # 路径 / Path / PIL.Image 都行
viewer.set_image(None)                      # 回到空态
viewer.fit()                                # 缩放到适配窗口
viewer.set_zoom(2.5)                        # 指定倍数
viewer.zoom()                               # 读当前倍数

# 滚轮以光标为中心缩放；按住左键拖动看局部；双击回到适配窗口
# 只重采样「画布上看得见的那一块」，8 倍也不会越放越卡
# 需要 Pillow：pip install "ctk-kit[image]"'''

CODE_SOURCE = '''def _demo_image(variant: int = 1):
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (1200, 800), (16, 22, 38))
    draw = ImageDraw.Draw(image)
    # ... 画渐变、网格、圆环和文字 ...
    return image

viewer.set_image(_demo_image(1))   # 直接传 PIL.Image，不落盘
viewer.set_image(None)             # 清空；on_zoom 会收到 1.0

# 换图时自动重新 fit；想让用户自己缩放就先 set_image 再 set_zoom
# 空态只显示 empty_text，拖拽和滚轮都不响应'''

#: 演示图的尺寸：放大后要看得出细节，缩小后又能完整放进窗口。
DEMO_SIZE = (1200, 800)


def _demo_image(variant: int = 1):
    """现场画一张细节够多的示意图，放大后能看出清晰度的变化。

    不往仓库里塞图片文件，示例页也能独立跑。
    """
    from PIL import Image, ImageDraw, ImageFont

    width, height = DEMO_SIZE
    image = Image.new("RGB", (width, height), (16, 22, 38))
    draw = ImageDraw.Draw(image)

    warm = variant == 2
    for x in range(0, width, 6):
        ratio = x / width
        if warm:
            color = (int(46 + 150 * ratio), int(28 + 60 * ratio), int(50 + 40 * ratio))
        else:
            color = (int(18 + 30 * ratio), int(28 + 88 * ratio), int(58 + 120 * ratio))
        draw.rectangle([x, 0, x + 6, height], fill=color)

    for x in range(0, width + 1, 50):
        draw.line([(x, 0), (x, height)], fill=(30, 40, 60), width=1)
    for y in range(0, height + 1, 50):
        draw.line([(0, y), (width, y)], fill=(30, 40, 60), width=1)
    for x in range(0, width + 1, 200):
        draw.line([(x, 0), (x, height)], fill=(90, 110, 150), width=2)
    for y in range(0, height + 1, 200):
        draw.line([(0, y), (width, y)], fill=(90, 110, 150), width=2)

    center = (width // 2, height // 2)
    for index, radius in enumerate(range(70, 330, 44)):
        shade = max(70, 220 - index * 14)
        tint = (shade, min(255, shade + 40), 230) if warm else (90, shade, 235)
        draw.ellipse(
            [
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ],
            outline=tint,
            width=4,
        )

    for index, (corner_x, corner_y) in enumerate(
        [(60, 60), (width - 260, 60), (60, height - 200), (width - 260, height - 200)]
    ):
        draw.rounded_rectangle(
            [corner_x, corner_y, corner_x + 200, corner_y + 140],
            radius=18,
            fill=(40 + index * 30, 60, 90 + index * 20),
            outline=(200, 210, 235),
            width=2,
        )

    try:
        big = ImageFont.load_default(size=84)
        small = ImageFont.load_default(size=26)
        tiny = ImageFont.load_default(size=18)
    except TypeError:  # Pillow < 10
        big = small = tiny = ImageFont.load_default()

    draw.text((center[0], center[1] - 30), "CTK-KIT", font=big, fill=(245, 248, 255), anchor="mm")
    draw.text(
        (center[0], center[1] + 60),
        f"IMAGE VIEWER DEMO · {width} x {height}",
        font=small,
        fill=(214, 226, 245),
        anchor="mm",
    )
    for step in range(0, width + 1, 200):
        draw.text((step + 6, 8), str(step), font=tiny, fill=(200, 214, 235))
    for step in range(0, height + 1, 200):
        draw.text((8, step + 6), str(step), font=tiny, fill=(200, 214, 235))
    return image


class ImagePageUI(PageBase):
    """图片页 UI：只建控件，事件留给 ImagePage。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "图片")
        self.header.info.configure(text="滚轮缩放 · 拖动平移 · 双击复位")

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "滚轮、拖动或点按钮，回显会出现在这里")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_preview(area)
        self._build_source(area)

    def _build_preview(self, area: tk.Misc) -> None:
        """主预览区：缩放 / 平移 / 双击复位，右上角实时显示倍率。"""
        box = Card(area, title="交互预览")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        self.fit_button = SecondaryButton(row, "适配窗口")
        self.fit_button.pack(side="left")
        self.zoom_in_button = SecondaryButton(row, "放大")
        self.zoom_in_button.pack(side="left", padx=(8, 0))
        self.zoom_out_button = SecondaryButton(row, "缩小")
        self.zoom_out_button.pack(side="left", padx=(8, 0))
        self.swap_button = SecondaryButton(row, "换一张")
        self.swap_button.pack(side="left", padx=(8, 0))

        self.zoom_label = HintLabel(row, "100%")
        self.zoom_label.pack(side="right")
        FieldLabel(row, "倍率", width=44).pack(side="right", padx=(8, 0))

        # 固定高度的容器：ImageViewer 放在 Scrollable 里时，光靠 height 参数
        # 撑不开（内部 canvas 的默认高度会顶掉它），这里由容器锁定预览区高度。
        viewer_row = Frame(box, height=430)
        viewer_row.pack(fill="x", padx=16, pady=(0, 8))
        viewer_row.pack_propagate(False)

        self.viewer = ImageViewer(
            viewer_row,
            min_zoom=1.0,
            max_zoom=8.0,
            empty_text="还没有图片",
        )
        self.viewer.pack(fill="both", expand=True)
        self.viewer.set_image(_demo_image(1))

        HintLabel(
            box,
            "滚轮以光标为中心缩放；按住左键拖动看局部；双击回到适配窗口。",
        ).pack(fill="x", padx=16, pady=(0, 8))

        CodePanel(
            box,
            CODE_VIEWER,
            "set_image 之后会自动 fit；min_zoom 可以传更小的值来允许缩小。",
        )

    def _build_source(self, area: tk.Misc) -> None:
        """图片来源：路径 / Path / PIL.Image，以及空态。"""
        box = Card(area, title="图片来源与空态")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "图片来源", width=68).pack(side="left")
        HintLabel(
            row,
            "路径 / pathlib.Path / PIL.Image 都可以传；传 None 回到空态。",
        ).pack(side="left", padx=(8, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))

        self.fill_button = SecondaryButton(row, "放入示意图")
        self.fill_button.pack(side="left")
        self.clear_button = SecondaryButton(row, "清空")
        self.clear_button.pack(side="left", padx=(8, 0))

        HintLabel(row, "空态只显示 empty_text，拖拽和滚轮都不响应。").pack(side="right")

        viewer_row = Frame(box, height=200)
        viewer_row.pack(fill="x", padx=16, pady=(0, 8))
        viewer_row.pack_propagate(False)

        self.empty_viewer = ImageViewer(
            viewer_row,
            empty_text="点上面的「放入示意图」试试",
        )
        self.empty_viewer.pack(fill="both", expand=True)

        CodePanel(
            box,
            CODE_SOURCE,
            "示例图是现场画的 PIL.Image，不依赖任何图片文件；空态传 None 即可。",
        )


class ImagePage(ImagePageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.variant = 1
        self.bind_events()

    def bind_events(self) -> None:
        """必须实现：注册按钮、换图与缩放回调。"""
        self.fit_button.configure(command=self._fit)
        self.zoom_in_button.configure(command=self._zoom_in)
        self.zoom_out_button.configure(command=self._zoom_out)
        self.swap_button.configure(command=self._swap)
        self.fill_button.configure(command=self._fill_empty)
        self.clear_button.configure(command=self._clear_empty)

        # ImageViewer 的 on_zoom 只能在构造时传入，没有公开的 setter；
        # 这里统一在事件类里接上，倍率变化就能写回底部回显条。
        self.viewer._on_zoom = self._on_zoom
        self.empty_viewer._on_zoom = self._on_empty_zoom

    def _fit(self) -> None:
        """回到适配窗口。"""
        self.viewer.fit()
        self._show("回到适配窗口（倍率 100%）")

    def _zoom_in(self) -> None:
        """以画布中心放大 1.3 倍，到上限就停在 800%。"""
        before = self.viewer.zoom()
        self.viewer.set_zoom(before * 1.3)
        if abs(self.viewer.zoom() - before) < 1e-6:
            self._show("已经是最大倍率 800%")

    def _zoom_out(self) -> None:
        """以画布中心缩小 1.3 倍，min_zoom=1.0 时最小就是适配窗口。"""
        before = self.viewer.zoom()
        self.viewer.set_zoom(before / 1.3)
        if abs(self.viewer.zoom() - before) < 1e-6:
            self._show("已经是最小倍率 100%（适配窗口）")

    def _swap(self) -> None:
        """在第 1 / 2 张示意图之间切换。"""
        self.variant = 2 if self.variant == 1 else 1
        self.viewer.set_image(_demo_image(self.variant))
        self._show(f"换成了第 {self.variant} 张示意图")

    def _fill_empty(self) -> None:
        """给空态区域也放一张图。"""
        self.empty_viewer.set_image(_demo_image(2))
        self._show("空态区域放进了一张图；set_image 之后自动 fit")

    def _clear_empty(self) -> None:
        """清空空态区域，回到 empty_text。"""
        self.empty_viewer.set_image(None)
        self._show("已清空：空态区域重新显示 empty_text")

    def _on_zoom(self, value: float) -> None:
        """主预览的倍率回调：更新角标并回显。"""
        text = f"{value * 100:.0f}%"
        self.zoom_label.configure(text=text)
        self._show(f"当前倍率 {text}")

    def _on_empty_zoom(self, value: float) -> None:
        """空态区域的倍率回调：只写回显条，不抢主预览的角标。"""
        if self.empty_viewer._original is None:
            return
        self._show(f"空态区域的当前倍率 {value * 100:.0f}%")

    def _show(self, text: str) -> None:
        """把交互结果写回底部回显条。"""
        self.feedback.configure(text=text)
