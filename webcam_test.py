from ultralytics import YOLO
import cv2
import os
# Cargar modelo entrenado
model = YOLO(os.path.join('runs', 'detect', 'train-6', 'weights', 'best.pt'))

# Abrir webcam
cap = cv2.VideoCapture(0)

# Opcional: resolución
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Inferencia
    results = model(frame)

    # Dibujar resultados
    annotated_frame = results[0].plot()

    # Mostrar
    cv2.imshow("YOLO Webcam", annotated_frame)

    # Salir con Q
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()