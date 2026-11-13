"""最小示例：把输入框、开关绑定到 conf_base 配置项。

运行后在卡片里输入昵称、拨动开关，内容会立刻写进当前目录的
``ui_prefs.json``；关掉窗口再运行，会读回上次的值。
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
    """界面偏好配置：一个字符串 + 一个布尔值。"""

    _path = "ui_prefs.json"
    form = Section("form")
    nickname = form.field(default="")
    remember = form.field(default=True)


app = ctk.App(title="配置绑定示例", size=(560, 300), backdrop="none")

card = ctk.Card(app, inside_title="偏好设置")
card.pack(fill="both", expand=True, padx=16, pady=16)

row = card.row(1, fill="x", padx=16, pady=(16, 10))
ctk.Label(row, "昵称").pack(side="left", padx=(0, 10))

entry = ctk.CTkEntry(row, placeholder_text="输入昵称")
entry.pack(side="left", fill="x", expand=True)
entry.bind_config(UiPrefs.nickname)

row = card.row(2, fill="x", padx=16, pady=(0, 10))
switch = ctk.Switch(row, text="记住我")
switch.pack(side="left")
switch.bind_config(UiPrefs.remember)

ctk.HintLabel(
    card,
    "修改后立刻写入 ui_prefs.json；重启窗口会读回。",
).pack(fill="x", padx=16, pady=(0, 16))

app.mainloop()
