"""本地音乐播放器示例（Windows，miniaudio）。

运行：
    .venv\\Scripts\\python.exe examples\\music_player\\main.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from conf_base import ConfigBase, Section
from PIL import Image, ImageDraw, ImageOps

import ctk_kit as ctk
from ctk_kit import tokens as T
from ctk_kit.fonts import get_font

from library import Track, format_time, read_cover, scan_folder
from player import Player

COVER_SIZE = 280
VOLUME = 70


class MusicPrefs(ConfigBase):
    """播放器的用户配置：记住上次打开的文件夹和音量。"""

    _path = str(Path.home() / ".ctk-kit" / "music_player.json")

    player = Section("player")
    folder = player.field(default="")
    volume = player.field(default=VOLUME)


def saved_volume() -> int:
    """读取上次的音量；读不到或超出范围时回到默认值。"""
    try:
        value = int(MusicPrefs.volume.value)
    except Exception:
        return VOLUME
    return max(0, min(100, value))


volume_level = saved_volume()

app = ctk.App(title="音乐播放器", size=(1000, 660), min_size=(900, 600))
app.set_theme("frosted")

app.grid_columnconfigure(0, weight=0, minsize=400)
app.grid_columnconfigure(1, weight=1)
app.grid_rowconfigure(0, weight=1)

player = Player(volume=volume_level / 100)
tracks: list[Track] = []
index_by_path: dict[str, int] = {}
current = -1
seeking = False


# ---------------------------------------------------------------- 封面工具
def _rounded(image: Image.Image, size: int = COVER_SIZE, radius: int = 18) -> Image.Image:
    """裁成正方形、贴圆角蒙版，透明角交给 CTkImage 合成。"""
    image = ImageOps.fit(image.convert("RGBA"), (size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    image.putalpha(mask)
    return image


def _placeholder() -> Image.Image:
    """没有封面时画一张简单的唱片占位图。"""
    image = Image.new("RGBA", (COVER_SIZE, COVER_SIZE), (30, 33, 43, 255))
    draw = ImageDraw.Draw(image)
    center = COVER_SIZE // 2
    draw.ellipse(
        (center - 72, center - 72, center + 72, center + 72), fill=(52, 57, 72, 255)
    )
    draw.ellipse(
        (center - 24, center - 24, center + 24, center + 24), fill=(30, 33, 43, 255)
    )
    return _rounded(image)


placeholder_ctk = ctk.CTkImage(
    light_image=_placeholder(), dark_image=_placeholder(), size=(COVER_SIZE, COVER_SIZE)
)
cover_ctk: Optional[ctk.CTkImage] = None

# ---------------------------------------------------------------- 正在播放
now_card = ctk.Card(app, inside_title="正在播放", width=400)
now_card.grid(row=0, column=0, sticky="nsew", padx=(24, 12), pady=24)
body = now_card.row(1, fill="both", expand=True, padx=18, pady=(14, 18))

cover_label = ctk.CTkLabel(body, text="", image=placeholder_ctk, width=COVER_SIZE, height=COVER_SIZE)
cover_label.pack(pady=(2, 12))

title_label = ctk.Label(
    body, text="未选择曲目", font=get_font(T.FONT_SECTION), text_color=T.COLOR_TEXT
)
title_label.pack(fill="x")
artist_label = ctk.Label(
    body,
    text="在右侧选择音乐文件夹",
    anchor="w",
    font=get_font(T.FONT_SMALL),
    text_color=T.COLOR_MUTED,
)
artist_label.pack(fill="x", pady=(2, 10))

progress = ctk.Slider(body, from_=0.0, to=1.0, width=320)
progress.pack(fill="x")

time_row = ctk.CTkFrame(body, fg_color="transparent")
time_row.pack(fill="x")
time_now = ctk.Label(
    time_row, text="0:00", anchor="w", font=get_font(T.FONT_SMALL), text_color=T.COLOR_MUTED
)
time_now.pack(side="left")
time_total = ctk.Label(
    time_row, text="0:00", anchor="e", font=get_font(T.FONT_SMALL), text_color=T.COLOR_MUTED
)
time_total.pack(side="right")

controls = ctk.CTkFrame(body, fg_color="transparent")
controls.pack(fill="x", pady=(12, 10))
controls.grid_columnconfigure((0, 1, 2), weight=1)
prev_btn = ctk.SecondaryButton(controls, "上一首", command=lambda: step(-1), width=92, height=36)
prev_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")
play_btn = ctk.PrimaryButton(controls, "播放", command=lambda: toggle(), width=110, height=40)
play_btn.grid(row=0, column=1, padx=6, sticky="ew")
next_btn = ctk.SecondaryButton(controls, "下一首", command=lambda: step(1), width=92, height=36)
next_btn.grid(row=0, column=2, padx=(6, 0), sticky="ew")

volume_row = ctk.CTkFrame(body, fg_color="transparent")
volume_row.pack(fill="x")
volume_label = ctk.Label(
    volume_row,
    text=f"音量 {volume_level}%",
    width=72,
    anchor="w",
    font=get_font(T.FONT_SMALL),
    text_color=T.COLOR_MUTED,
)
volume_label.pack(side="left")
volume = ctk.Slider(volume_row, from_=0, to=100, width=200)
volume.pack(side="left", fill="x", expand=True, padx=(8, 0))
volume.set(volume_level)

# ---------------------------------------------------------------- 播放列表
list_card = ctk.Card(app, inside_title="播放列表")
list_card.grid(row=0, column=1, sticky="nsew", padx=(12, 24), pady=24)
list_body = list_card.row(1, fill="both", expand=True, padx=16, pady=(14, 16))

picker = ctk.CTkFrame(list_body, fg_color="transparent")
picker.pack(fill="x")
path_field = ctk.PathField(
    picker,
    mode="folder",
    placeholder="选择音乐文件夹",
    on_pick=lambda _path: load_folder(),
)
path_field.pack(side="left", fill="x", expand=True)
saved_folder = ""
try:
    saved_folder = str(MusicPrefs.folder.value or "")
except Exception:
    pass
if saved_folder:
    path_field.set(saved_folder)
refresh_btn = ctk.SecondaryButton(picker, "刷新", command=lambda: load_folder(), width=76)
refresh_btn.pack(side="left", padx=(8, 0))

hint = ctk.Label(
    list_body,
    text="支持 mp3 / flac / wav / ogg",
    anchor="w",
    font=get_font(T.FONT_SMALL),
    text_color=T.COLOR_MUTED,
)
hint.pack(fill="x", pady=(8, 8))

playlist = ctk.TreeView(list_body, columns=("时长",), height=12, command=lambda _v: play_selected())
playlist.pack(fill="both", expand=True)


# ---------------------------------------------------------------- 播放逻辑
def load_folder() -> None:
    """扫描文件夹并重建列表；扫描期间先提示一下。"""
    global current
    folder = path_field.get().strip()
    if not folder:
        hint.set_text("请先选择音乐文件夹")
        return
    hint.set_text("扫描中…")
    app.update_idletasks()
    try:
        found = scan_folder(folder)
    except Exception as exc:
        hint.set_text(f"读取失败：{exc}")
        return
    player.stop()
    current = -1
    play_btn.configure(text="播放")
    progress.set(0.0)
    time_now.set_text("0:00")
    time_total.set_text("0:00")
    try:
        MusicPrefs.folder.value = folder
    except Exception:
        pass
    tracks[:] = found
    index_by_path.clear()
    playlist.clear()
    for index, track in enumerate(tracks):
        index_by_path[str(track.path)] = index
        playlist.insert(
            parent="", text=track.title, values=(format_time(track.duration),), iid=str(track.path)
        )
    hint.set_text(f"共 {len(tracks)} 首" if tracks else "没有找到音频文件")


def play_selected() -> None:
    """点击列表行：找到对应曲目并播放。"""
    iid = playlist.get_selected()
    if iid is not None and iid in index_by_path:
        play_index(index_by_path[iid])


def play_index(index: int) -> None:
    """播放第 ``index`` 首，并同步封面、标题、时长。"""
    global current, cover_ctk
    if not 0 <= index < len(tracks):
        return
    track = tracks[index]
    try:
        player.play(track.path)
    except Exception as exc:
        current = -1
        play_btn.configure(text="播放")
        hint.set_text(f"无法播放：{exc}")
        return
    current = index
    duration = player.duration or track.duration
    time_total.set_text(format_time(duration))
    time_now.set_text("0:00")
    progress.set(0.0)
    title_label.set_text(track.title)
    artist_label.set_text(track.artist)
    play_btn.configure(text="暂停")
    hint.set_text(f"正在播放：{track.title}")

    cover = read_cover(track.path)
    image = _rounded(cover) if cover is not None else _placeholder()
    cover_ctk = ctk.CTkImage(light_image=image, dark_image=image, size=(COVER_SIZE, COVER_SIZE))
    cover_label.configure(image=cover_ctk)


def toggle() -> None:
    """播放 / 暂停；还没选歌时从第一首开始。"""
    if player.path is None:
        if tracks:
            play_index(0)
        return
    if player.finished:
        step(1)
        return
    player.toggle()
    play_btn.configure(text="播放" if player.paused else "暂停")


def step(delta: int) -> None:
    """上一首 / 下一首，首尾循环。"""
    if not tracks:
        return
    base = current if current >= 0 else (0 if delta > 0 else len(tracks) - 1)
    play_index((base + delta) % len(tracks))


def on_seek(value: float) -> None:
    """拖动中只更新时间文字，松手才真正 seek。"""
    global seeking
    seeking = True
    if player.duration > 0:
        time_now.set_text(format_time(value * player.duration))


def on_seek_release(value: float) -> None:
    """松手：跳到目标位置。"""
    global seeking
    seeking = False
    if player.duration > 0:
        try:
            player.seek(value * player.duration)
        except Exception as exc:
            hint.set_text(f"跳转失败：{exc}")


def on_volume(value: float) -> None:
    """音量 0 ~ 100 映射到设备主音量。"""
    volume_label.set_text(f"音量 {int(value)}%")
    player.set_volume(value / 100)


def save_volume(value: float) -> None:
    """松手才写配置，拖动过程中不反复落盘。"""
    try:
        MusicPrefs.volume.value = int(round(value))
    except Exception:
        pass


progress.configure(command=on_seek, release_command=on_seek_release)
volume.configure(command=on_volume, release_command=save_volume)


def tick() -> None:
    """每 250ms 同步一次进度；播完自动下一首。"""
    if player.path is not None:
        duration = player.duration
        if duration > 0 and not seeking:
            position = min(player.position, duration)
            progress.set(position / duration)
            time_now.set_text(format_time(position))
        if player.finished:
            if current + 1 < len(tracks):
                play_index(current + 1)
            else:
                player.stop()
                play_btn.configure(text="播放")
                hint.set_text("播放完毕")
    app.after(250, tick)


def on_close() -> None:
    player.close()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", on_close)
app.after(250, tick)
if saved_folder:
    app.after(0, load_folder)  # 启动时自动读取上次的文件夹
app.mainloop()
