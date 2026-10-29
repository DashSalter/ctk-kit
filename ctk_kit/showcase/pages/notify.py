"""提示页：窗口顶部/底部的浮层提示，四种级别、两种形态、堆叠与常驻。

单独启动：``python -m ctk_kit.showcase.pages.notify``
"""

from __future__ import annotations

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.buttons import primary_button, soft_button
from ctk_kit.layout import hint_label, page_header, scrollable, section_title
from ctk_kit.notify import LEVELS, Notifier
from ctk_kit.text import TextArea
from ctk_kit.theme import color_of

from ..shell import _card_body, _card_shell, _feedback, _row, run_page

TITLE = "提示"

NOTIFY_USAGE = '''\
from ctk_kit import Notifier

tips = Notifier(app)                      # 一个窗口一个实例

# 窄条：一行话，2.6 秒后自动消失
tips.show("已复制到剪贴板")
tips.show("保存成功", level="success", position="bottom")

# 卡片：图标 + 标题 + 正文 + 关闭按钮，4.5 秒
tips.show("连接超时，请检查网络后重试",
          title="云备份失败", level="error",
          style="card", position="bottom")

# 常驻，直到点关闭按钮或 dismiss()
view = tips.show("正在导出…", style="card", duration=0)
tips.dismiss(view)

# 便捷函数：按窗口缓存 Notifier，连续调用会堆叠
from ctk_kit import notify

notify(app, "已复制到剪贴板", level="success")
'''


def build(master, *, notifier: Notifier) -> ctk.CTkFrame:
    """Notifier 的四种级别、两个位置、两种形态，连同堆叠与代码示例。"""
    page = ctk.CTkFrame(master, fg_color="transparent")

    _, info = page_header(page, TITLE)
    info.configure(text="浮层贴边，不占布局")

    feedback = _feedback(page, "点按钮，提示会浮在窗口边缘")

    area = scrollable(page)
    area.pack(fill="both", expand=True, pady=(14, 0))
    bg = color_of(T.COLOR_CARD)

    labels = {"info": "信息", "success": "成功", "warn": "警告", "error": "错误"}

    def show(message, **kwargs):
        notifier.show(message, **kwargs)
        where = "顶部" if kwargs.get("position", "top") == "top" else "底部"
        shape = kwargs.get("style", "pill")
        feedback(f"{where} · {shape} · 已弹出：{message}")

    # --- 级别 ---
    section_title(area, "级别 level")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    for level in LEVELS:
        soft_button(
            row,
            f"{labels[level]} {level}",
            lambda lv=level: show(f"这是一条{labels[lv]}提示", level=lv),
            width=100,
        ).pack(side="left", padx=(0, 8))
    hint_label(
        body, "颜色取 tokens.STATUS_COLORS；窄条形态默认 2.6 秒后自动消失。"
    ).pack(fill="x")

    # --- 位置 ---
    section_title(area, "位置 position")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    primary_button(
        row, "顶部 top", lambda: show("贴在窗口顶部", position="top"), width=110
    ).pack(side="left")
    primary_button(
        row, "底部 bottom", lambda: show("贴在窗口底部", position="bottom"), width=110
    ).pack(side="left", padx=(8, 0))
    hint_label(
        body, "顶部靠上边缘、底部靠下边缘，距边 16px；窗口缩放时自动跟随。"
    ).pack(fill="x")

    # --- 形态 ---
    section_title(area, "形态 style")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    soft_button(
        row, "窄条 pill", lambda: show("已复制到剪贴板", style="pill"), width=110
    ).pack(side="left")
    soft_button(
        row,
        "卡片 card",
        lambda: show(
            "连接超时，请检查网络后重试",
            title="云备份失败",
            level="error",
            style="card",
        ),
        width=110,
    ).pack(side="left", padx=(8, 0))
    hint_label(
        body, "窄条适合过程提示；卡片带图标、标题与关闭按钮，适合错误与警告。"
    ).pack(fill="x")

    # --- 组合 ---
    section_title(area, "组合：位置 × 形态 × 级别")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)
    row = _row(body, bg)
    soft_button(
        row,
        "顶部 · 窄条 · 成功",
        lambda: show("已保存到本机", style="pill", level="success", position="top"),
        width=150,
    ).pack(side="left")
    soft_button(
        row,
        "顶部 · 卡片 · 警告",
        lambda: show(
            "密码已用 180 天，建议更换",
            title="该换密码了",
            style="card",
            level="warn",
            position="top",
        ),
        width=150,
    ).pack(side="left", padx=(8, 0))
    row = _row(body, bg)
    soft_button(
        row,
        "底部 · 窄条 · 信息",
        lambda: show("已切换外观模式", style="pill", level="info", position="bottom"),
        width=150,
    ).pack(side="left")
    soft_button(
        row,
        "底部 · 卡片 · 错误",
        lambda: show(
            "云端返回 401，登录状态可能已过期",
            title="同步失败",
            style="card",
            level="error",
            position="bottom",
        ),
        width=150,
    ).pack(side="left", padx=(8, 0))

    # --- 堆叠与常驻 ---
    section_title(area, "堆叠与常驻")
    box = _card_shell(area)
    box.pack(fill="x")
    body = _card_body(box)

    def fire_three():
        for delay, text in ((0, "第一条"), (160, "第二条"), (320, "第三条")):
            page.after(delay, lambda t=text: show(f"{t}：同一位置向下堆叠"))
        feedback("连发三条；超出 max_visible（默认 3）时最旧的先关掉")

    row = _row(body, bg)
    soft_button(row, "连发三条", fire_three, width=100).pack(side="left")
    soft_button(
        row,
        "常驻卡片（点 ✕ 关闭）",
        lambda: show(
            "这条不会自动消失，点右上角 ✕ 或下面的「全部关掉」",
            title="需要手动确认",
            style="card",
            level="warn",
            duration=0,
        ),
        width=170,
    ).pack(side="left", padx=(8, 0))
    soft_button(
        row,
        "全部关掉",
        lambda: (notifier.clear(), feedback("已清空所有提示")),
        width=100,
    ).pack(side="left", padx=(8, 0))
    hint_label(
        body, "指针停在提示上会暂停计时，移开继续倒数。"
    ).pack(fill="x")

    # --- 代码示例 ---
    section_title(area, "用法")
    example = TextArea(
        area, readonly=True, height=250, bg_color=T.COLOR_CARD, show_counter=False
    )
    example.pack(fill="x")
    example.set(NOTIFY_USAGE)
    hint_label(area, "只读展示；完整参数见 Notifier.show 的文档字符串。").pack(
        fill="x", pady=(4, 0)
    )
    return page


def main() -> int:
    return run_page(
        lambda app: build(app, notifier=Notifier(app)),
        TITLE,
        height=900,
    )


if __name__ == "__main__":
    raise SystemExit(main())
