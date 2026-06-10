"""
Clip recorder con buffer circular.
Mantiene los últimos N segundos en RAM y guarda pre+post evento.
"""
import os
import time
import tempfile
import threading
from collections import deque

import cv2
import numpy as np

from agent.config import settings
from utils.logger import get_logger

log = get_logger("clip_recorder")


class ClipRecorder:
    """
    Buffer circular de frames indexados por timestamp.
    - Pre-buffer: mantiene `pre_seconds` de video siempre en memoria.
    - Post-buffer: graba `post_seconds` después de un trigger.
    """

    def __init__(self, camera_id: str, fps: float):
        self.camera_id = camera_id
        self.fps = fps
        self.pre_seconds = settings.CLIP_PRE_SECONDS
        self.post_seconds = settings.CLIP_POST_SECONDS
        self.enabled = settings.CLIP_ENABLED

        # Buffer circular: (timestamp, frame)
        max_frames = int((self.pre_seconds + self.post_seconds + 2) * fps)
        self._buffer: deque[tuple[float, np.ndarray]] = deque(maxlen=max_frames)
        self._lock = threading.Lock()

        # Estado de grabación post-evento
        self._recording = False
        self._trigger_time: float | None = None
        self._post_frames: list[tuple[float, np.ndarray]] = []

    def push(self, frame: np.ndarray) -> None:
        """Agrega frame al buffer. Llamar por cada frame capturado."""
        if not self.enabled:
            return
        ts = time.time()
        with self._lock:
            self._buffer.append((ts, frame.copy()))
            if self._recording:
                self._post_frames.append((ts, frame.copy()))

    def trigger(self) -> None:
        """Marca el inicio de un evento — comienza a acumular post-frames."""
        if not self.enabled:
            return
        with self._lock:
            self._recording = True
            self._trigger_time = time.time()
            self._post_frames = []
        log.debug("clip.trigger", camera=self.camera_id)

    def is_ready(self) -> bool:
        """Retorna True si ya acumulamos suficientes post-frames."""
        if not self._recording or self._trigger_time is None:
            return False
        return time.time() - self._trigger_time >= self.post_seconds

    def build_clip(self, output_path: str | None = None) -> str | None:
        """
        Ensambla pre-buffer + post-frames en un archivo MP4.
        Retorna la ruta del archivo temporal.
        """
        if not self.enabled:
            return None

        with self._lock:
            trigger_time = self._trigger_time
            pre_frames = [
                (ts, f) for ts, f in self._buffer
                if ts < trigger_time
            ][-int(self.pre_seconds * self.fps):]
            post_frames = list(self._post_frames)
            self._recording = False
            self._trigger_time = None
            self._post_frames = []

        all_frames = pre_frames + post_frames
        if not all_frames:
            log.warning("clip.build.empty", camera=self.camera_id)
            return None

        path = output_path or tempfile.mktemp(suffix=".mp4")
        h, w = all_frames[0][1].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(path, fourcc, self.fps, (w, h))

        for _, frame in all_frames:
            writer.write(frame)
        writer.release()

        log.info(
            "clip.built",
            camera=self.camera_id,
            frames=len(all_frames),
            duration=round(len(all_frames) / self.fps, 1),
            path=path,
        )
        return path

    def reset(self) -> None:
        with self._lock:
            self._recording = False
            self._trigger_time = None
            self._post_frames = []
