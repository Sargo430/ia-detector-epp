"""
Stream processor por cámara.
- Captura frames de RTSP en un thread dedicado
- Alimenta una queue async para el pipeline de inferencia
- Reconexión automática ante cortes de red
"""
from __future__ import annotations

import asyncio
import threading
import time
from queue import Queue, Full, Empty

import cv2
import numpy as np

from agent.config import CameraConfig, settings
from agent.clip_recorder import ClipRecorder
from utils.logger import get_logger

log = get_logger("stream")


class CameraStream:
    """
    Captura frames de una cámara RTSP en un thread separado.
    Los frames se ponen en una Queue para consumo async.
    """

    def __init__(self, camera: CameraConfig):
        self.camera = camera
        self.camera_id = camera.id
        self.rtsp_url = camera.rtsp_url
        self.fps = camera.fps_capture

        self._queue: Queue[np.ndarray | None] = Queue(
            maxsize=settings.FRAME_QUEUE_MAX
        )
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._frame_count = 0

        self.clip_recorder = ClipRecorder(camera.id, fps=float(self.fps))

    # ── Control ───────────────────────────────────────────────────────────────
    def start(self) -> None:
        log.info("stream.start", camera=self.camera.name, url=self.rtsp_url)
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._capture_loop, daemon=True, name=f"stream-{self.camera_id[:8]}"
        )
        self._thread.start()

    def stop(self) -> None:
        log.info("stream.stop", camera=self.camera.name)
        self._stop_event.set()
        self._queue.put(None)  # desbloquea get() si está esperando
        if self._thread:
            self._thread.join(timeout=5)

    # ── Captura en thread ─────────────────────────────────────────────────────
    def _capture_loop(self) -> None:
        reconnect_delay = settings.RTSP_RECONNECT_DELAY

        while not self._stop_event.is_set():
            cap = self._open_capture()
            if cap is None:
                log.warning(
                    "stream.connect.failed",
                    camera=self.camera.name,
                    retry_in=reconnect_delay,
                )
                time.sleep(reconnect_delay)
                continue

            log.info("stream.connected", camera=self.camera.name)
            frame_interval = max(1, int(30 / self.fps))  # asume source ~30fps

            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    log.warning("stream.read.failed", camera=self.camera.name)
                    break

                self._frame_count += 1

                # Frame skip — solo procesa 1 de cada N
                if self._frame_count % settings.FRAME_SKIP != 0:
                    self.clip_recorder.push(frame)
                    continue

                self.clip_recorder.push(frame)

                try:
                    self._queue.put_nowait(frame)
                except Full:
                    # Si la cola está llena descarta el frame más viejo
                    try:
                        self._queue.get_nowait()
                    except Empty:
                        pass
                    self._queue.put_nowait(frame)

            cap.release()
            if not self._stop_event.is_set():
                log.info(
                    "stream.reconnect",
                    camera=self.camera.name,
                    delay=reconnect_delay,
                )
                time.sleep(reconnect_delay)

    def _open_capture(self) -> cv2.VideoCapture | None:
    # Detecta si es webcam (número) o RTSP (URL)
        source = int(self.rtsp_url) if self.rtsp_url.isdigit() else self.rtsp_url
        cap = cv2.VideoCapture(source, cv2.CAP_ANY)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            return None
        return cap

    # ── Consumo async ─────────────────────────────────────────────────────────
    async def get_frame(self, timeout: float = 1.0) -> np.ndarray | None:
        """Retorna el siguiente frame disponible (non-blocking desde async)."""
        loop = asyncio.get_event_loop()
        try:
            frame = await loop.run_in_executor(
                None, lambda: self._queue.get(timeout=timeout)
            )
            return frame
        except Empty:
            return None

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    @property
    def total_frames(self) -> int:
        return self._frame_count
