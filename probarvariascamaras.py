import cv2
import os
import time
import numpy as np
from ultralytics import YOLO
from threading import Thread
from collections import deque

# =====================================
# 1. Configuración de las Cámaras IP
# =====================================
CAMARAS = [
    {
        "nombre": "Camara 1",
        "url": "http://192.168.18.100:8080/video",
        "color": (0, 255, 0)  # Verde
    },
    {
        "nombre": "Camara 2",
        "url": "http://192.168.18.95:8080/video",  # Cambia por tu segunda IP
        "color": (255, 0, 0)  # Azul
    }
]

# =====================================
# 2. Cargar modelo
# =====================================
carpeta_entrenamiento = "./runs/detect/train-18"
ruta_modelo = os.path.join(carpeta_entrenamiento, "weights", "best.engine")
model = YOLO(ruta_modelo)

print(f"✅ Modelo cargado desde: {ruta_modelo}")

# =====================================
# 3. Configuración
# =====================================
frame_width, frame_height = 640, 480

def capturar_y_detectar(config, frame_cache):
    """Captura frames de una cámara y realiza detección"""
    cap = cv2.VideoCapture(config["url"])
    
    if not cap.isOpened():
        print(f"❌ Error: No se pudo conectar a {config['nombre']}")
        return
    
    print(f"✅ {config['nombre']} conectada")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"❌ Se perdió el stream de {config['nombre']}")
            break
        
        # Redimensionar para consistencia
        frame = cv2.resize(frame, (frame_width, frame_height))
        
        # Realizar detección
        results = model.predict(
            source=frame,
            conf=0.4,
            verbose=False,
            stream=True
        )
        
        for result in results:
            annotated_frame = result.plot(
                line_width=1,
                font_size=0.6,
            )
        
        # Guardar frame procesado
        frame_cache[config["nombre"]] = annotated_frame
        
        time.sleep(0.001)  # Pequeña pausa
    
    cap.release()

# =====================================
# 4. Main
# =====================================
print("\n🎥 Iniciando transmisión de múltiples cámaras\n")

# Diccionario para compartir frames entre hilos
frame_cache = {}
threads = []

# Iniciar hilos para cada cámara
for camara in CAMARAS:
    frame_cache[camara["nombre"]] = None
    thread = Thread(target=capturar_y_detectar, args=(camara, frame_cache))
    thread.daemon = True
    thread.start()
    threads.append(thread)

# Variables para cálculo de FPS
fps_history = deque(maxlen=30)
ultimo_tiempo = time.time()
frame_count = 0

# Loop principal
try:
    while True:
        # Crear canvas combinado (una sola ventana)
        canvas_height = frame_height
        canvas_width = frame_width * len(CAMARAS)
        canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
        
        # Dibujar cada cámara en el canvas
        for i, camara in enumerate(CAMARAS):
            x_offset = i * frame_width
            
            # Obtener frame de la cámara
            frame = frame_cache.get(camara["nombre"])
            
            if frame is not None:
                # Asegurar tamaño correcto
                frame = cv2.resize(frame, (frame_width, frame_height))
                canvas[:, x_offset:x_offset+frame_width] = frame
                
                # Añadir nombre de la cámara
                cv2.putText(
                    canvas,
                    camara["nombre"],
                    (x_offset + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    camara["color"],
                    2
                )
            else:
                # Mostrar mensaje de espera
                cv2.putText(
                    canvas,
                    f"Esperando {camara['nombre']}...",
                    (x_offset + 20, canvas_height//2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )
        
        # Calcular FPS (corregido - sin división por cero)
        frame_count += 1
        tiempo_actual = time.time()
        tiempo_transcurrido = tiempo_actual - ultimo_tiempo
        
        if tiempo_transcurrido >= 1.0:
            fps = frame_count / tiempo_transcurrido
            fps_history.append(fps)
            frame_count = 0
            ultimo_tiempo = tiempo_actual
        
        # Mostrar FPS en la ventana
        if fps_history:
            fps_promedio = sum(fps_history) / len(fps_history)
            cv2.putText(
                canvas,
                f"FPS: {fps_promedio:.1f}",
                (10, canvas_height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )
        
        # Mostrar TODO en UNA sola ventana
        cv2.imshow("Detección Múltiple Cámaras - EPP", canvas)
        
        # Salir con 'q' o ESC
        if cv2.waitKey(1) & 0xFF in [27, ord('q')]:
            break

except KeyboardInterrupt:
    print("\n🛑 Deteniendo...")

finally:
    cv2.destroyAllWindows()
    print("\n" + "="*50)
    print("🏁 Prueba finalizada correctamente")
    print("="*50)