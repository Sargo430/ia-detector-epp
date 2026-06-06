import time
import numpy as np
from ultralytics import YOLO
import os
carpeta_entrenamiento = "./runs/detect/train-17"
ruta_modelo = os.path.join(carpeta_entrenamiento, "weights", "best.engine")

ruta_modelo_pt = os.path.join(carpeta_entrenamiento, "weights", "best.pt")
# Cargar modelos
pt_model = YOLO(ruta_modelo_pt)
trt_model = YOLO(ruta_modelo)

# Imagen de prueba
image_path = "image.jpg"

# Warmup
for _ in range(20):
    pt_model.predict(image_path, verbose=False)
    trt_model.predict(image_path, verbose=False)

def benchmark(model, image, runs=100):
    times = []

    for _ in range(runs):
        start = time.perf_counter()

        model.predict(
            image,
            verbose=False,
            device=0
        )

        end = time.perf_counter()
        times.append((end - start) * 1000)  # ms

    avg_ms = np.mean(times)
    fps = 1000 / avg_ms

    return {
        "avg_ms": avg_ms,
        "min_ms": np.min(times),
        "max_ms": np.max(times),
        "fps": fps
    }

print("Benchmarking PyTorch...")
pt_results = benchmark(pt_model, image_path)

print("Benchmarking TensorRT...")
trt_results = benchmark(trt_model, image_path)

print("\n=== RESULTADOS ===")
print(f"PyTorch (.pt)")
print(f"Latencia promedio: {pt_results['avg_ms']:.2f} ms")
print(f"FPS: {pt_results['fps']:.2f}")

print("\nTensorRT (.engine)")
print(f"Latencia promedio: {trt_results['avg_ms']:.2f} ms")
print(f"FPS: {trt_results['fps']:.2f}")

speedup = pt_results['avg_ms'] / trt_results['avg_ms']

print(f"\nAceleración TensorRT: {speedup:.2f}x")