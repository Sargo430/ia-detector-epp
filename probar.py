from ultralytics import YOLO
import cv2
import os
from pathlib import Path

# =========================
# Cargar modelo
# =========================
# Especifica aquí la carpeta del entrenamiento (relativa o absoluta)
carpeta_entrenamiento = "./runs/detect/train-16"  # Cambiar si el modelo está en otra carpeta
ruta_modelo = os.path.join(carpeta_entrenamiento, "weights", "best.pt")
model = YOLO(ruta_modelo)
print(f"✅ Modelo cargado desde: {ruta_modelo}")

# =========================
# Carpetas de entrada y salida
# =========================
carpeta_imagenes = "imagenes"
carpeta_detecciones = "detecciones"

# Crear carpeta de salida si no existe
os.makedirs(carpeta_detecciones, exist_ok=True)

# Extensiones permitidas
extensiones = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".avif"]

# =========================
# Resolución máxima de pantalla
# =========================
max_w, max_h = 1280, 720  # ajusta si tu pantalla es diferente

# =========================
# Contadores para estadísticas
# =========================
total_imagenes = 0
total_detecciones = 0
imagenes_con_detecciones = 0

# =========================
# Recorrer archivos
# =========================
for archivo in os.listdir(carpeta_imagenes):

    ruta_completa = os.path.join(carpeta_imagenes, archivo)

    # Verificar que sea archivo y tenga extensión válida
    if Path(archivo).suffix.lower() in extensiones:

        total_imagenes += 1
        print(f"Procesando: {archivo}")

        # Predicción
        results = model.predict(
            source=ruta_completa,
            conf=0.4,
            verbose=False
        )

        # Obtener el resultado de la primera imagen
        result = results[0]

        # Contar detecciones en esta imagen
        num_detecciones = len(result.boxes) if result.boxes is not None else 0
        total_detecciones += num_detecciones

        if num_detecciones > 0:
            imagenes_con_detecciones += 1

        # Obtener imagen anotada en full resolución
        annotated_frame = result.plot(
            line_width=1,
            font_size=0.6,
        )

        # =====================================
        # GUARDAR IMAGEN EN FULL RESOLUCIÓN
        # =====================================
        nombre_salida = f"detectado_{archivo}"
        ruta_salida = os.path.join(carpeta_detecciones, nombre_salida)
        cv2.imwrite(ruta_salida, annotated_frame)
        print(f"  ✅ Guardado: {ruta_salida} ({num_detecciones} detecciones)")

        # =====================================
        # REDIMENSIONAR SOLO PARA MOSTRAR
        # =====================================
        h, w = annotated_frame.shape[:2]
        if w > max_w or h > max_h:
            escala = min(max_w / w, max_h / h)
            nuevo_w = int(w * escala)
            nuevo_h = int(h * escala)
            frame_mostrar = cv2.resize(annotated_frame, (nuevo_w, nuevo_h))
        else:
            frame_mostrar = annotated_frame

        # Mostrar imagen
        cv2.imshow("Detección EPP", frame_mostrar)

        # Esperar tecla (ESC para salir, cualquier otra tecla continúa)
        tecla = cv2.waitKey(0)
        if tecla == 27:  # ESC
            break

# =========================
# Cerrar ventanas
# =========================
cv2.destroyAllWindows()

# =========================
# Mostrar estadísticas finales
# =========================
print("\n" + "="*50)
print("📊 ESTADÍSTICAS FINALES")
print("="*50)
print(f"📁 Imágenes procesadas: {total_imagenes}")
print(f"🔍 Imágenes con detecciones: {imagenes_con_detecciones}")
print(f"🎯 Total de objetos detectados: {total_detecciones}")
print(f"💾 Imágenes guardadas en: {carpeta_detecciones}/")
print("="*50)