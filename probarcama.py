from ultralytics import YOLO
import cv2
import os

# =========================
# Cargar modelo
# =========================
# Especifica aquí la carpeta del entrenamiento (relativa o absoluta)
carpeta_entrenamiento = "./runs/detect/train-16"  # Cambiar si el modelo está en otra carpeta
ruta_modelo = os.path.join(carpeta_entrenamiento, "weights", "best.pt")
model = YOLO(ruta_modelo)
print(f"✅ Modelo cargado desde: {ruta_modelo}")

# =========================
# Iniciar cámara
# =========================
cap = cv2.VideoCapture(0)  # 0 = cámara por defecto, cambiar a 1 si tienes varias

if not cap.isOpened():
    print("❌ No se pudo abrir la cámara")
    exit()

print("✅ Cámara iniciada — presiona ESC para salir")

# =========================
# Loop de detección en tiempo real
# =========================
while True:
    ret, frame = cap.read()

    if not ret:
        print("❌ Error leyendo frame")
        break

    # Predicción sobre el frame actual
    results = model.predict(
        source=frame,
        conf=0.4,
        verbose=False
    )

    # Anotar frame con detecciones
    annotated_frame = results[0].plot()

    # Mostrar conteo en pantalla
    num_detecciones = len(results[0].boxes) if results[0].boxes is not None else 0
    cv2.putText(
        annotated_frame,
        f"Detecciones: {num_detecciones}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1, (0, 255, 0), 2
    )

    # Mostrar ventana
    cv2.imshow("Detección EPP - Tiempo Real", annotated_frame)

    # ESC para salir
    if cv2.waitKey(1) & 0xFF == 27:
        break

# =========================
# Liberar recursos
# =========================
cap.release()
cv2.destroyAllWindows()
print("✅ Cámara cerrada")