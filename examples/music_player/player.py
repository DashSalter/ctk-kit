"""基于 miniaudio 的本地播放内核。

只依赖 ``miniaudio``：解码统一成 44.1kHz / 双声道 / 16bit，
播放、暂停、seek、音量都通过同一个 ``PlaybackDevice`` 完成。
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import miniaudio

SAMPLE_RATE = 44100
CHANNELS = 2


class Player:
    """单曲播放器：同一时间只播一首。"""

    def __init__(self, volume: float = 0.7) -> None:
        self._device: Optional[miniaudio.PlaybackDevice] = None
        self._stream = None
        self._path: Optional[Path] = None
        self._duration = 0.0
        # 位置用「起点 + 已过时间」算，避免把设备预读的缓冲区算进播放位置
        self._base = 0.0
        self._started_at: Optional[float] = None
        self._paused_pos = 0.0
        self._paused = False
        self._finished = False
        self._volume = max(0.0, min(1.0, volume))

    # ---- 只读状态 ------------------------------------------------------

    @property
    def path(self) -> Optional[Path]:
        """当前加载的文件；没加载时为 ``None``。"""
        return self._path

    @property
    def duration(self) -> float:
        """当前文件时长（秒）；读不到时为 0。"""
        return self._duration

    @property
    def position(self) -> float:
        """已播放位置（秒）。"""
        if self._paused or self._started_at is None:
            return min(self._paused_pos, self._duration or self._paused_pos)
        elapsed = time.monotonic() - self._started_at
        return min(self._base + elapsed, self._duration or self._base + elapsed)

    @property
    def paused(self) -> bool:
        """是否处于暂停状态。"""
        return self._paused

    @property
    def finished(self) -> bool:
        """当前曲目是否已经自然播放完。"""
        return self._finished

    @property
    def volume(self) -> float:
        """0.0 ~ 1.0 的主音量。"""
        return self._volume

    # ---- 播放控制 ------------------------------------------------------

    def play(self, path: str | Path) -> None:
        """从头播放 ``path``；格式不支持时抛 ``miniaudio.DecodeError``。"""
        self.stop()
        path = Path(path)
        self._duration = _read_duration(path)
        self._ensure_device()
        self._path = path
        self._base = 0
        self._started_at = time.monotonic()
        self._paused_pos = 0.0
        self._paused = False
        self._finished = False
        try:
            self._stream = self._make_stream(0)
            self._device.start(self._stream)
        except Exception:
            self.stop()
            raise

    def toggle(self) -> None:
        """播放 / 暂停切换。"""
        if self._path is None or self._device is None or self._finished:
            return
        if self._paused:
            self._base = self._paused_pos
            self._started_at = time.monotonic()
            self._device.start(self._stream)
            self._paused = False
        else:
            self._paused_pos = self.position
            self._device.stop()
            self._paused = True

    def seek(self, seconds: float) -> None:
        """跳到 ``seconds`` 秒；暂停中 seek 后仍保持暂停。"""
        if self._path is None or self._device is None or self._duration <= 0:
            return
        target = max(0.0, min(float(seconds), self._duration))
        was_playing = not self._paused
        self._device.stop()
        self._close_stream()
        self._base = target
        self._paused_pos = target
        self._finished = False
        try:
            self._stream = self._make_stream(int(target * SAMPLE_RATE))
        except Exception:
            self._started_at = None
            self._paused = True
            raise
        if was_playing:
            self._started_at = time.monotonic()
            self._device.start(self._stream)
        else:
            self._started_at = None
            self._paused = True

    def stop(self) -> None:
        """停止播放并清空当前曲目。"""
        if self._device is not None and self._device.running:
            self._device.stop()
        self._close_stream()
        self._path = None
        self._base = 0.0
        self._paused_pos = 0.0
        self._started_at = None
        self._paused = False
        self._finished = False

    def set_volume(self, volume: float) -> None:
        """设置主音量，范围外的值会被夹到 0.0 ~ 1.0。"""
        self._volume = max(0.0, min(1.0, float(volume)))
        if self._device is not None:
            self._device.set_master_volume(self._volume)

    def close(self) -> None:
        """停止并释放音频设备；窗口关闭时调用。"""
        if self._device is not None:
            self._device.close()
            self._device = None
        self._close_stream()

    # ---- 内部 ----------------------------------------------------------

    def _ensure_device(self) -> None:
        """首次播放时才申请音频设备。"""
        if self._device is not None:
            return
        self._device = miniaudio.PlaybackDevice(
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=CHANNELS,
            sample_rate=SAMPLE_RATE,
            buffersize_msec=100,
        )
        self._device.set_master_volume(self._volume)

    def _make_stream(self, start_frame: int):
        """按固定格式流式解码，``start_frame`` 之后的帧才输出。

        miniaudio 的设备回调会 ``send(帧数)``，所以这里也要转发帧数，
        并把生成器预热到第一个 ``yield``。
        """
        raw = miniaudio.stream_file(
            str(self._path),
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=CHANNELS,
            sample_rate=SAMPLE_RATE,
            seek_frame=start_frame,
        )

        def stream():
            try:
                frames = yield
                while True:
                    chunk = raw.send(frames)
                    frames = yield chunk
            except StopIteration:
                self._finished = True
            finally:
                raw.close()

        generator = stream()
        next(generator)
        return generator

    def _close_stream(self) -> None:
        """关掉当前解码器，释放文件句柄。"""
        if self._stream is None:
            return
        try:
            self._stream.close()
        except Exception:
            pass
        self._stream = None


def _read_duration(path: Path) -> float:
    """读时长；文件损坏或格式不支持时返回 0，让界面自己降级。"""
    try:
        return float(miniaudio.get_file_info(str(path)).duration)
    except Exception:
        return 0.0
