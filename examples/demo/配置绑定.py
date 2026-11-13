"""最小示例：每种可绑定控件各放一个，绑定到 conf_base 配置项。

运行后改任意控件，内容会立刻写进当前目录的 ``ui_prefs.json``；关掉窗口再
运行，会读回上次的值。
"""

from __future__ import annotations

import sys

import ctk_kit as ctk

try:
    from conf_base import ConfigBase, Section
except ImportError:  # 本地开发时 conf_base 还没 pip install
    sys.path.insert(0, r"F:\PyCharmMiscProject")
    from conf_base import ConfigBase, Section


class UiPrefs(ConfigBase):
    """界面偏好配置：每种控件对应一个字段。"""

    _path = "ui_prefs.json"
    form = Section("form")
    nickname = form.field(default="")
    remember = form.field(default=True)
    autologin = form.field(default=False)
    theme = form.field(default="深色")
    font_size = form.field(default=14)
    notify = form.field(default="邮件")
    language = form.field(default="中文")
    volume = form.field(default=50.0)
    note = form.field(default="")


app = ctk.App(title="配置绑定示例", size=(640, 820), backdrop="none")

card = ctk.Card(app, inside_title="偏好设置")
card.pack(fill="both", expand=True, padx=16, pady=16)

row = card.row(1, fill="x", padx=16, pady=(16, 10))
ctk.Label(row, "昵称", width=64).pack(side="left", padx=(0, 10))
nickname_entry = ctk.CTkEntry(row, placeholder_text="输入昵称")
nickname_entry.pack(side="left", fill="x", expand=True)
nickname_entry.bind_config(UiPrefs.nickname)

row = card.row(2, fill="x", padx=16, pady=(0, 10))
remember_switch = ctk.Switch(row, text="记住我")
remember_switch.pack(side="left", padx=(0, 24))
autologin_check = ctk.Check(row, text="自动登录")
autologin_check.pack(side="left")
remember_switch.bind_config(UiPrefs.remember)
autologin_check.bind_config(UiPrefs.autologin)

row = card.row(3, fill="x", padx=16, pady=(0, 10))
ctk.Label(row, "主题", width=64).pack(side="left", padx=(0, 10))
theme_segmented = ctk.Segmented(row, values=("深色", "浅色", "跟随系统"))
theme_segmented.pack(side="left")
theme_segmented.bind_config(UiPrefs.theme)

row = card.row(4, fill="x", padx=16, pady=(0, 10))
ctk.Label(row, "字号", width=64).pack(side="left", padx=(0, 10))
font_spinner = ctk.Spinner(row, from_=12, to=32, value=14)
font_spinner.pack(side="left")
font_spinner.bind_config(UiPrefs.font_size)

row = card.row(5, fill="x", padx=16, pady=(0, 10))
ctk.Label(row, "通知", width=64).pack(side="left", padx=(0, 10))
for notify_value in ("邮件", "短信", "不通知"):
    radio = ctk.Radio(row, notify_value, value=notify_value, group="notify")
    radio.pack(side="left", padx=(0, 18))
    radio.bind_config(UiPrefs.notify)

row = card.row(6, fill="x", padx=16, pady=(0, 10))
ctk.Label(row, "语言", width=64).pack(side="left", padx=(0, 10))
language_drop = ctk.DropField(
    row, values_provider=lambda: ["中文", "English", "日本語"]
)
language_drop.pack(side="left", fill="x", expand=True)
language_drop.bind_config(UiPrefs.language)

row = card.row(7, fill="x", padx=16, pady=(0, 10))
ctk.Label(row, "音量", width=64).pack(side="left", padx=(0, 10))
volume_slider = ctk.Slider(row, from_=0, to=100, width=200)
volume_slider.pack(side="left")
volume_slider.bind_config(UiPrefs.volume)

row = card.row(8, fill="x", padx=16, pady=(0, 10))
ctk.Label(row, "备注", width=64).pack(side="left", padx=(0, 10))
note_area = ctk.TextArea(row, height=90)
note_area.pack(side="left", fill="x", expand=True)
note_area.bind_config(UiPrefs.note)


def refresh(section: str = "", option: str = "", value: object = None) -> None:
    """任何配置变化后刷新底部提示。"""
    if option:
        hint.configure(text=f"已保存：{option} = {value!r}")
    else:
        hint.configure(text="改动任意控件，都会立刻写进 ui_prefs.json")


hint = ctk.HintLabel(card, "")
hint.pack(fill="x", padx=16, pady=(0, 16))
for prop in (
    UiPrefs.nickname,
    UiPrefs.remember,
    UiPrefs.autologin,
    UiPrefs.theme,
    UiPrefs.font_size,
    UiPrefs.notify,
    UiPrefs.language,
    UiPrefs.volume,
    UiPrefs.note,
):
    prop.on_change(refresh)
refresh()

app.mainloop()
