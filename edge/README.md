# Vigilance Edge Agent

Proceso que corre en el dispositivo edge (PC con GPU, Jetson, etc.)
capturando streams RTSP, corriendo inferencia local y reportando al backend.

## Flujo

```
Cámara RTSP
    ↓ (thread por cámara)
CameraStream  ──push──→  ClipRecorder (buffer circular)
    ↓ (queue async)
EdgePipeline._loop()
    ↓ (batch de N cámaras)
InferenceEngine.predict_batch()
    ↓ detecciones
_handle_result()
    ├── upload_frame() ──PUT──→ MinIO (pre-signed URL)
    ├── build_clip()   ──PUT──→ MinIO (pre-signed URL)
    └── ingest_event() ──POST──→ FastAPI backend
                                    ↓
                                 Redis pub/sub → Dashboard SSE
```

## Setup rápido

```bash
# 1. Copiar configuración
cp .env.example .env
# Editar .env con tu API_BASE_URL, credenciales y S3

# 2. Configurar cámaras
cp config/cameras.json config/cameras.json
# Editar con los IDs reales del backend y URLs RTSP

# 3. Agregar tu modelo
cp /ruta/a/tu/modelo.pt models/best.pt

# 4. Ajustar mapeo de clases si es necesario
# Editar agent/inference.py → CLASS_TO_EVENT

# 5. Correr
docker compose up -d

# O directamente
pip install -r requirements.txt
python main.py
```

## Configuración de cámaras (config/cameras.json)

Los `id` de cada cámara deben coincidir exactamente con los UUIDs
registrados en el backend via `POST /api/v1/cameras`.

```json
[
  {
    "id": "uuid-del-backend",
    "name": "Nombre descriptivo",
    "rtsp_url": "rtsp://user:pass@ip:554/stream",
    "fps_capture": 15,
    "enabled": true,
    "detection_config": {
      "confidence_threshold": 0.65,
      "event_types": ["intrusion", "fire"],
      "zones": []
    }
  }
]
```

## Mapeo de clases del modelo

Editar `agent/inference.py` → `CLASS_TO_EVENT` para mapear
las clases de tu modelo a los event_types del sistema:

```python
CLASS_TO_EVENT = {
    "person":   "intrusion",
    "fire":     "fire",
    "crowd":    "crowd",
    # agrega las clases de tu modelo aquí
}
```

## Variables de entorno clave

| Variable | Descripción |
|---|---|
| `API_BASE_URL` | URL del backend FastAPI |
| `TENANT_SLUG` | Slug del tenant (ej: `acme`) |
| `API_EMAIL` | Email del usuario agente |
| `API_PASSWORD` | Password del usuario agente |
| `MODEL_PATH` | Ruta al archivo `.pt` |
| `MODEL_DEVICE` | `cpu`, `cuda`, o `mps` |
| `FRAME_SKIP` | Analizar 1 de cada N frames |
| `CLIP_ENABLED` | Grabar clips de video del evento |
| `CLIP_PRE_SECONDS` | Segundos de video antes del evento |
| `CLIP_POST_SECONDS` | Segundos de video después del evento |

## Hardware recomendado

| Dispositivo | Cámaras | Notas |
|---|---|---|
| Raspberry Pi 5 | 1-2 | CPU only, modelo ligero (YOLOv8n) |
| PC con GTX 1660 | 4-8 | `MODEL_DEVICE=cuda` |
| NVIDIA Jetson Orin | 8-16 | Usar Dockerfile stage `jetson` |
| Intel NUC + Coral TPU | 2-4 | Requiere modelo TFLite |
