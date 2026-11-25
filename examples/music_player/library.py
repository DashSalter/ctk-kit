"""媒体库：扫描文件夹、读取标题/歌手/时长，按需取内嵌封面。"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from mutagen import File as MutagenFile
from PIL import Image

AUDIO_EXTS = {".mp3", ".flac", ".wav", ".ogg"}


@dataclass(frozen=True)
class Track:
    """一首歌的基本信息。"""

    path: Path
    title: str
    artist: str
    duration: float


def scan_folder(folder: str | Path) -> list[Track]:
    """递归扫描文件夹，返回按文件名排序的曲目列表。"""
    root = Path(folder)
    if not root.is_dir():
        raise ValueError(f"文件夹不存在：{root}")
    paths = sorted(
        (p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTS),
        key=lambda p: str(p).lower(),
    )
    return [_read_track(p) for p in paths]


def read_cover(path: str | Path) -> Image.Image | None:
    """读内嵌封面；没有封面或读取失败时返回 ``None``。"""
    try:
        audio = MutagenFile(str(path))
        if audio is None:
            return None
        data = _cover_bytes(audio)
        if not data:
            return None
        return Image.open(BytesIO(data)).convert("RGB")
    except Exception:
        return None


def format_time(seconds: float) -> str:
    """秒数格式化成 ``m:ss``；非法值显示 ``0:00``。"""
    seconds = max(0, int(seconds or 0))
    return f"{seconds // 60}:{seconds % 60:02d}"


def _read_track(path: Path) -> Track:
    """读一首歌的标签；失败就用文件名兜底。"""
    title = path.stem
    artist = "未知艺术家"
    duration = 0.0
    try:
        audio = MutagenFile(str(path), easy=True)
        if audio is not None:
            title = _first(audio.tags, "title") or title
            artist = _first(audio.tags, "artist") or artist
            if audio.info is not None:
                duration = float(audio.info.length)
    except Exception:
        pass
    return Track(path=path, title=title, artist=artist, duration=duration)


def _first(tags, key: str) -> str:
    """取标签里的第一个值（不同格式可能是列表或字符串）。"""
    if not tags:
        return ""
    value = tags.get(key)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    return str(value).strip()


def _cover_bytes(audio) -> bytes | None:
    """按 FLAC / ID3 / MP4 三种常见存放方式取封面字节。"""
    pictures = getattr(audio, "pictures", None)
    if pictures:
        return pictures[0].data
    tags = audio.tags
    if tags is None:
        return None
    getall = getattr(tags, "getall", None)
    if getall is not None:
        frames = getall("APIC")
        if frames:
            return frames[0].data
    covers = tags.get("covr")
    if covers:
        return bytes(covers[0])
    return None
