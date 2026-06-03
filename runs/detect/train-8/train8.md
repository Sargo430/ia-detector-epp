### Train 8: Primera Modificación
**Descripción**: Introducción de Data Augmentation

```bash
!yolo task=detect mode=train epochs=180 data='ppe_data.yaml' model=yolo11n.pt imgsz=640 patience=10 cache=False workers=2 degrees=15 fliplr=0.5 mosaic=1.0 mixup=0.1 copy_paste=0.3
```

| Parámetro | Valor |
|-----------|-------|
| Modelo Base | yolo11n.pt |
| Épocas | 180 |
| Resolución | 640x640 |
| Paciencia | 10 |
| Workers | 2 |
| Cache | False |
| **Data Augmentation** | |
| Rotación (degrees) | 15° |
| Flip Horizontal (fliplr) | 0.5 |
| Mosaic | 1.0 |
| Mixup | 0.1 |
| Copy-Paste | 0.3 |

**Notas**: Se introdujeron técnicas de aumento de datos para mejorar la generalización del modelo.
