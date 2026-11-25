"""图片毛玻璃背景：选择本地图片当窗口背景，可调模糊和蒙层。"""

import os

from PIL import Image, ImageDraw

import ctk_kit as ctk


def gradient() -> Image.Image:
    """默认背景：不依赖本地图片也能直接看到效果。"""
    width, height = 1400, 900
    image = Image.new("RGB", (width, height))
    pen = ImageDraw.Draw(image)
    for y in range(height):
        t = y / height
        pen.line(
            (0, y, width, y),
            fill=(int(8 + 40 * t), int(36 + 60 * (1 - t)), int(88 + 70 * (1 - t))),
        )
    pen.ellipse((120, 90, 640, 610), fill="#f6bd16")
    pen.ellipse((820, 280, 1340, 800), fill="#e8557b")
    return image


app = ctk.App(title="图片毛玻璃背景", size=(980, 660), min_size=(760, 520))
app.set_theme("frosted")

state = {"image": gradient(), "blur": 16, "alpha": 0x40}


def apply() -> None:
    """把当前图片 / 模糊 / 蒙层一次性写给底层窗口。"""
    app.set_frost_backdrop(
        image=state["image"],
        color="#0A1420",
        alpha=state["alpha"],
        blur=state["blur"],
    )


card = ctk.Card(app, inside_title="图片毛玻璃背景", width=400, height=336)
card.place(x=28, y=28)
body = card.row(1, fill="both", expand=True, padx=16, pady=(14, 16))

status = ctk.Label(body, text="当前：内置渐变背景", anchor="w")
status.pack(fill="x", pady=(0, 8))


def on_path(path: str) -> None:
    """路径变了：文件存在就换背景，不存在只提示不报错。"""
    path = path.strip()
    if not path:
        status.set_text("未选择图片")
        return
    if not os.path.isfile(path):
        status.set_text("路径不存在，继续输入或点「浏览」")

        return
    state["image"] = path
    try:
        apply()
    except Exception as exc:  # noqa: BLE001 - 用户可能选了坏文件
        status.set_text(f"读取失败：{exc}")

        return
    status.set_text(f"当前：{os.path.basename(path)}")



ctk.PathField(
    body,
    mode="file",
    title="选择背景图片",
    placeholder="选择一张图片，或把文件拖进来",
    on_change=on_path,
).pack(fill="x")


def on_blur(widget) -> None:
    """模糊档位。"""
    state["blur"] = int(widget.get())
    apply()


blur = ctk.Segmented(
    body, {"无": 0, "轻": 8, "强": 18}, command=on_blur
)
blur.pack(fill="x", pady=(10, 0))
blur.set(18)


def on_tint(widget) -> None:
    """图片上的蒙层浓度。"""
    state["alpha"] = int(widget.get())
    apply()


tint = ctk.Segmented(
    body, {"浅": 0x14, "中": 0x40, "深": 0x80}, command=on_tint
)
tint.pack(fill="x", pady=(8, 0))
tint.set(0x40)


def reset() -> None:
    """回到内置渐变背景。"""
    state["image"] = gradient()
    apply()
    status.configure(text="当前：内置渐变背景")


ctk.SecondaryButton(body, "恢复默认背景", command=reset).pack(
    fill="x", pady=(12, 0)
)

app.mainloop()
