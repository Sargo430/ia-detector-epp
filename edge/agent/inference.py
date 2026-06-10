"""
Motor de inferencia — envuelve tu modelo YOLO/custom.
Soporta: batch inference, filtrado por zona, mapeo a event_type.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from pathlib import Path

from agent.config import settings, DetectionConfig
from utils.logger import get_logger

log = get_logger("inference")


@dataclass
class Detection:
    event_type: str
    confidence: float
    box: dict          # {x, y, w, h} normalizado 0-1
    label: str
    class_id: int


@dataclass
class InferenceResult:
    camera_id: str
    detections: list[Detection] = field(default_factory=list)

    @property
    def has_detections(self) -> bool:
        return len(self.detections) > 0

    def to_bounding_boxes(self) -> list[dict]:
        return [
            {
                "x": d.box["x"],
                "y": d.box["y"],
                "w": d.box["w"],
                "h": d.box["h"],
                "label": d.label,
                "confidence": round(d.confidence, 4),
            }
            for d in self.detections
        ]


# Mapeo de clases YOLO → event_type del sistema
# Ajusta según las clases de tu modelo entrenado
CLASS_TO_EVENT: dict[str, str] = { 
    "Hardhat":        "Casco",
    "Mask":      "mascara",
    "NO-Hardhat":         "no casco",
    "NO-Mask":            "no mascara",
    "NO-Safety Vest":     "no chaleco",
    "Person":          "Persona",
    "Safety Cone":         "Cono de seguridad",
    "Safety Vest":         "Chaleco de seguridad",
    "machinery":   "Maquinaria",
    "vehicle": "vehiculo",
    

}


class InferenceEngine:
    def __init__(self):
        self._model = None
        self._loaded = False

    def load(self) -> None:
        """Carga el modelo. Llamar una sola vez al inicio."""
        model_path = Path(settings.MODEL_PATH)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {model_path}\n"
                "Coloca tu archivo .pt en models/best.pt"
            )

        log.info("inference.load", path=str(model_path), device=settings.MODEL_DEVICE)
        from ultralytics import YOLO
        self._model = YOLO(str(model_path))
        self._model.to(settings.MODEL_DEVICE)
        self._loaded = True
        log.info("inference.load.ok")

    def predict_batch(
        self,
        frames: list[np.ndarray],
        camera_ids: list[str],
        detection_configs: list[DetectionConfig],
    ) -> list[InferenceResult]:
        """
        Inferencia en batch — más eficiente que frame a frame.
        Retorna una lista de InferenceResult, uno por frame.
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        results_raw = self._model.predict(
            source=frames,
            imgsz=settings.MODEL_IMG_SIZE,
            conf=settings.MODEL_CONFIDENCE,
            iou=settings.MODEL_IOU,
            verbose=False,
            stream=False,
        )

        output = []
        for i, (raw, cam_id, det_cfg) in enumerate(
            zip(results_raw, camera_ids, detection_configs)
        ):
            detections = self._parse_result(raw, det_cfg, frames[i].shape)
            output.append(InferenceResult(camera_id=cam_id, detections=detections))

        return output

    def _parse_result(
        self,
        raw,
        det_cfg: DetectionConfig,
        frame_shape: tuple,
    ) -> list[Detection]:
        """Convierte salida YOLO a lista de Detection filtrada por config."""
        h, w = frame_shape[:2]
        detections = []

        if raw.boxes is None:
            return detections

        for box in raw.boxes:
            conf = float(box.conf[0])
            class_id = int(box.cls[0])
            label = raw.names[class_id]
            event_type = CLASS_TO_EVENT.get(label, "intrusion")

            # Filtrar por confidence del tenant
            if conf < det_cfg.confidence_threshold:
                continue

            # Filtrar por event_types configurados
            if det_cfg.event_types and event_type not in det_cfg.event_types:
                continue

            # Coordenadas normalizadas
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            bx = (x1 + x2) / 2 / w
            by = (y1 + y2) / 2 / h
            bw = (x2 - x1) / w
            bh = (y2 - y1) / h

            # Filtrar por zona si está configurado
            if det_cfg.zones and not self._in_any_zone(bx, by, det_cfg.zones, w, h):
                continue

            detections.append(Detection(
                event_type=event_type,
                confidence=conf,
                box={"x": round(bx, 4), "y": round(by, 4),
                     "w": round(bw, 4), "h": round(bh, 4)},
                label=label,
                class_id=class_id,
            ))

        return detections

    @staticmethod
    def _in_any_zone(cx: float, cy: float, zones: list[dict], w: int, h: int) -> bool:
        """Point-in-polygon para filtrar detecciones fuera de zonas de interés."""
        import cv2
        point = (cx * w, cy * h)
        for zone in zones:
            polygon = np.array(zone.get("polygon", []), dtype=np.float32)
            if len(polygon) < 3:
                continue
            if cv2.pointPolygonTest(polygon, point, False) >= 0:
                return True
        return False
