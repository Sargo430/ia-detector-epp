from ultralytics import YOLO
import os
from pathlib import Path

# Cargar modelo entrenado
carpeta_entrenamiento = "./runs/detect/train-18"  # Cambiar si el modelo está en otra carpeta
ruta_modelo = os.path.join(carpeta_entrenamiento, "weights", "best.pt")
model = YOLO(ruta_modelo)

# Exportar a TensorRT
model.export(
    format="engine",
    half=True,
    imgsz=640,
)