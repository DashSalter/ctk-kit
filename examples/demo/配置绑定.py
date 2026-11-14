"""最小示例：每种可绑定控件各放一个，绑定到 conf_base 配置项。

运行后改任意控件，内容会立刻写进当前目录的 ``ui_prefs.json``；关掉窗口再
运行，会读回上次的值。
"""

from __future__ import annotations

import ctk_kit as ctk

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

row = card.row(1, fill="x", padx=16, pady=(14, 8))
nickname_entry = ctk.CTkEntry(row.label("昵称"), placeholder_text="输入昵称")
nickname_entry.pack(fill="x")
nickname_entry.bind_config(UiPrefs.nickname)

# 同一行放两个开关：标签右侧的容器里各摆一个
row = card.row(2, fill="x", padx=16)
switch_holder = row.label("账号")
remember_switch = ctk.Switch(switch_holder, text="记住我")
remember_switch.pack(side="left")
autologin_check = ctk.Check(switch_holder, text="自动登录")
autologin_check.pack(side="left", padx=(24, 0))
remember_switch.bind_config(UiPrefs.remember)
autologin_check.bind_config(UiPrefs.autologin)

row = card.row(3, fill="x", padx=16)
theme_segmented = ctk.Segmented(
    row.label("主题"), values=("深色", "浅色", "跟随系统")
)
theme_segmented.pack(anchor="w")
theme_segmented.bind_config(UiPrefs.theme)

row = card.row(4, fill="x", padx=16)
font_spinner = ctk.Spinner(row.label("字号"), from_=12, to=32, value=14)
font_spinner.pack(anchor="w")
font_spinner.bind_config(UiPrefs.font_size)

row = card.row(5, fill="x", padx=16)
notify_group = ctk.RadioGroup(
    row.label("通知"), ("邮件", "短信", "不通知"), value=UiPrefs.notify.value, group="notify"
)
notify_group.pack(anchor="w")
notify_group.bind_config(UiPrefs.notify)

row = card.row(6, fill="x", padx=16)
language_drop = ctk.DropField(
    row.label("语言"), values_provider=lambda: ["中文", "English", "日本語"]
)
language_drop.pack(fill="x")
language_drop.bind_config(UiPrefs.language)

row = card.row(7, fill="x", padx=16)
volume_slider = ctk.Slider(row.label("音量"), from_=0, to=100, width=200)
volume_slider.pack(anchor="w")
volume_slider.bind_config(UiPrefs.volume)

row = card.row(8, fill="x", padx=16)
note_area = ctk.TextArea(row.label("备注"), height=90)
note_area.pack(fill="x")
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
