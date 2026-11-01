"""图片页：显示图片、滚轮缩放、按住左键拖动看局部。

单独启动：``python -m ctk_kit.showcase.pages.image``
"""

from __future__ import annotations

import customtkinter as ctk

from ctk_kit.buttons import SecondaryButton
from ctk_kit.image_view import ImageViewer
from ctk_kit.layout import Card, HintLabel, PageHeader

from ..shell import _card_body, _code_panel, run_page

TITLE = "图片"

CODE = '''from ctk_kit import ImageViewer

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


def _demo_image(variant: int = 1):
    """现场画一张细节够多的示意图，放大后能看出清晰度的变化。

    不往仓库里塞图片文件，示例页也能独立跑。
    """
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1200, 800
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


def build(master) -> ctk.CTkFrame:
    """一页演示：滚轮缩放 + 拖动平移，缩放比例实时显示。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = PageHeader(page, TITLE)
    info.configure(text="滚轮缩放 · 按住左键拖动 · 双击复位")

    box = Card(page)
    bar = ctk.CTkFrame(page, fg_color="transparent")

    zoom_label = HintLabel(bar, "100%")
    zoom_label.pack(side="right")

    def report(value: float) -> None:
        zoom_label.configure(text=f"{value * 100:.0f}%")

    viewer = ImageViewer(box, height=430, on_zoom=report)
    viewer.pack(fill="both", expand=True, padx=16, pady=16)

    current = {"variant": 1}

    def swap() -> None:
        current["variant"] = 2 if current["variant"] == 1 else 1
        viewer.set_image(_demo_image(current["variant"]))
        feedback.configure(text=f"换成了第 {current['variant']} 张示意图")

    SecondaryButton(bar, "适配窗口", viewer.fit).pack(side="left")
    SecondaryButton(bar, "放大", lambda: viewer.set_zoom(viewer.zoom() * 1.3)).pack(
        side="left", padx=(8, 0)
    )
    SecondaryButton(bar, "缩小", lambda: viewer.set_zoom(viewer.zoom() / 1.3)).pack(
        side="left", padx=(8, 0)
    )
    SecondaryButton(bar, "换一张", swap).pack(side="left", padx=(8, 0))

    feedback = HintLabel(bar, "图片是现场用 Pillow 画的，没有额外素材文件。")
    feedback.pack(side="left", padx=(12, 0))
    page.viewer = viewer

    box.pack(fill="both", expand=True, pady=(14, 0))
    bar.pack(fill="x", pady=(12, 0))

    code_box = Card(page)
    code_box.pack(fill="x", pady=(12, 0))
    _code_panel(
        _card_body(code_box),
        CODE,
        "set_image 之后会自动 fit；min_zoom 可以传更小的值来允许缩小。",
    )

    viewer.set_image(_demo_image(1))
    return page


def main() -> int:
    return run_page(build, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
