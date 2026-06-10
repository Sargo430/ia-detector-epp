# ── Stage base ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV deps
    libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libgomp1 libgstreamer1.0-0 \
    # RTSP / FFmpeg
    ffmpeg \
    # Networking
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Stage CPU (desarrollo / edge x86) ─────────────────────────────────────────
FROM base AS cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Modelo se monta en runtime (no se incluye en imagen)
VOLUME ["/app/models", "/app/config"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "main.py"]


# ── Stage Jetson / CUDA ────────────────────────────────────────────────────────
# Para Jetson Orin/Xavier: usa imagen base de NVIDIA
# FROM nvcr.io/nvidia/l4t-pytorch:r35.4.1-pth2.1-py3 AS jetson
#
# WORKDIR /app
# RUN apt-get update && apt-get install -y ffmpeg libglib2.0-0 && rm -rf /var/lib/apt/lists/*
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# VOLUME ["/app/models", "/app/config"]
# CMD ["python", "main.py"]
