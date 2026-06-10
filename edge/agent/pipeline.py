"""
Pipeline principal del edge agent.
Orquesta: captura → batch → inferencia → upload → ingest API.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import time
from datetime import datetime, timezone

from agent.api_client import APIClient
from agent.clip_recorder import ClipRecorder
from agent.config import CameraConfig, settings
from agent.inference import InferenceEngine, InferenceResult
from agent.stream import CameraStream
from agent.uploader import upload_frame, upload_clip
from utils.logger import get_logger

log = get_logger("pipeline")

# Cooldown por cámara+tipo para no inundar el backend con alertas repetidas
_cooldowns: dict[str, float] = {}
COOLDOWN_SECONDS = 30


def _is_on_cooldown(camera_id: str, event_type: str) -> bool:
    key = f"{camera_id}:{event_type}"
    last = _cooldowns.get(key, 0)
    return time.time() - last < COOLDOWN_SECONDS


def _set_cooldown(camera_id: str, event_type: str) -> None:
    _cooldowns[f"{camera_id}:{event_type}"] = time.time()


class EdgePipeline:
    def __init__(self):
        self.engine = InferenceEngine()
        self.cameras: list[CameraConfig] = []
        self.streams: list[CameraStream] = []
        self._running = False

    # ── Setup ─────────────────────────────────────────────────────────────────
    def setup(self) -> None:
        self.cameras = settings.load_cameras()
        if not self.cameras:
            raise RuntimeError("No cameras configured. Check config/cameras.json")

        log.info("pipeline.setup", cameras=len(self.cameras))
        self.engine.load()

        for cam in self.cameras:
            stream = CameraStream(cam)
            self.streams.append(stream)

    # ── Run ───────────────────────────────────────────────────────────────────
    async def run(self) -> None:
        self._running = True

        # Inicia captura de todas las cámaras
        for stream in self.streams:
            stream.start()

        log.info("pipeline.running", cameras=len(self.streams))

        async with APIClient() as api:
            try:
                await self._loop(api)
            finally:
                for stream in self.streams:
                    stream.stop()

    async def _loop(self, api: APIClient) -> None:
        """
        Bucle principal:
        Cada iteración recolecta un batch de frames (uno por cámara) y
        corre inferencia en batch para maximizar throughput de GPU.
        """
        while self._running:
            # Recolectar frames disponibles de todas las cámaras
            batch_frames = []
            batch_camera_ids = []
            batch_configs = []
            batch_streams = []

            for stream in self.streams:
                frame = await stream.get_frame(timeout=0.1)
                if frame is not None:
                    batch_frames.append(frame)
                    batch_camera_ids.append(stream.camera_id)
                    batch_configs.append(stream.camera.detection_config)
                    batch_streams.append(stream)

            if not batch_frames:
                await asyncio.sleep(0.05)
                continue

            # Inferencia en batch
            try:
                results = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.engine.predict_batch,
                    batch_frames,
                    batch_camera_ids,
                    batch_configs,
                )
            except Exception as e:
                log.error("pipeline.inference.error", error=str(e))
                continue

            # Procesar cada resultado en paralelo
            tasks = [
                self._handle_result(api, result, frame, stream)
                for result, frame, stream in zip(results, batch_frames, batch_streams)
                if result.has_detections
            ]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    # ── Manejo de detección ───────────────────────────────────────────────────
    async def _handle_result(
        self,
        api: APIClient,
        result: InferenceResult,
        frame,
        stream: CameraStream,
    ) -> None:
        camera = next(c for c in self.cameras if c.id == result.camera_id)

        for det in result.detections:
            # Cooldown para no spamear
            if _is_on_cooldown(result.camera_id, det.event_type):
                log.debug(
                    "pipeline.cooldown",
                    camera=camera.name,
                    event_type=det.event_type,
                )
                continue

            _set_cooldown(result.camera_id, det.event_type)
            log.info(
                "pipeline.detection",
                camera=camera.name,
                event_type=det.event_type,
                confidence=round(det.confidence, 3),
            )

            # 1. Subir frame a MinIO
            frame_s3_key = await self._upload_frame(api, result.camera_id, frame)

            # 2. Grabar clip (trigger → esperar post_seconds → subir)
            clip_s3_key = None
            if settings.CLIP_ENABLED:
                stream.clip_recorder.trigger()
                clip_s3_key = await self._wait_and_upload_clip(
                    api, result.camera_id, stream.clip_recorder
                )

            # 3. Notificar al backend
            await self._ingest_event(
                api=api,
                camera_id=result.camera_id,
                event_type=det.event_type,
                confidence=det.confidence,
                bounding_boxes=result.to_bounding_boxes(),
                frame_s3_key=frame_s3_key,
                clip_s3_key=clip_s3_key,
            )

    async def _upload_frame(
        self, api: APIClient, camera_id: str, frame
    ) -> str | None:
        try:
            ts = int(time.time())
            filename = f"frame_{ts}.jpg"
            upload_url, s3_key = await api.get_presign_upload_url(camera_id, filename)
            await asyncio.get_event_loop().run_in_executor(
                None, upload_frame, upload_url, frame
            )
            log.debug("pipeline.frame.uploaded", key=s3_key)
            return s3_key
        except Exception as e:
            log.warning("pipeline.frame.upload.error", error=str(e))
            return None

    async def _wait_and_upload_clip(
        self, api: APIClient, camera_id: str, recorder: ClipRecorder
    ) -> str | None:
        try:
            # Esperar a que se acumulen los post-frames
            deadline = time.time() + settings.CLIP_POST_SECONDS + 2
            while not recorder.is_ready() and time.time() < deadline:
                await asyncio.sleep(0.2)

            clip_path = await asyncio.get_event_loop().run_in_executor(
                None, recorder.build_clip, None
            )
            if not clip_path:
                return None

            ts = int(time.time())
            filename = f"clip_{ts}.mp4"
            upload_url, s3_key = await api.get_presign_upload_url(camera_id, filename)
            await asyncio.get_event_loop().run_in_executor(
                None, upload_clip, upload_url, clip_path
            )
            os.unlink(clip_path)
            log.info("pipeline.clip.uploaded", key=s3_key)
            return s3_key
        except Exception as e:
            log.warning("pipeline.clip.upload.error", error=str(e))
            return None

    async def _ingest_event(
        self,
        api: APIClient,
        camera_id: str,
        event_type: str,
        confidence: float,
        bounding_boxes: list[dict],
        frame_s3_key: str | None,
        clip_s3_key: str | None,
    ) -> None:
        payload = {
            "camera_id": camera_id,
            "event_type": event_type,
            "confidence": confidence,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "frame_s3_key": frame_s3_key,
            "clip_s3_key": clip_s3_key,
            "bounding_boxes": bounding_boxes,
            "raw_inference": {},
        }
        try:
            resp = await api.ingest_event(payload)
            log.info(
                "pipeline.event.ingested",
                event_id=resp.get("id"),
                event_type=event_type,
                camera_id=camera_id[:8],
            )
        except Exception as e:
            log.error("pipeline.event.ingest.error", error=str(e))

    def stop(self) -> None:
        self._running = False
