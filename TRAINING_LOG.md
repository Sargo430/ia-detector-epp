# Registro de Entrenamientos - PPE Detection (YOLO)

## Descripción General
Este documento registra la configuración y parámetros utilizados en cada sesión de entrenamiento del detector de Equipos de Protección Personal (PPE) basado en YOLO.

**Dataset**: css-data
- **Clases**: Hardhat, Mask, NO-Hardhat, NO-Mask, NO-Safety Vest, Person, Safety Cone, Safety Vest, machinery, vehicle
- **Total de clases**: 10

---

## Configuraciones de Entrenamiento

### Train 1-7: Configuración Inicial (Seba)
**Estado**: Entrenamientos básicos sin filtros ni data augmentation

```bash
!yolo task=detect mode=train epochs=180 data='ppe_data.yaml' model=yolo11n.pt imgsz=640 patience=10
```

| Parámetro | Valor |
|-----------|-------|
| Modelo Base | yolo11n.pt |
| Épocas | 180 |
| Resolución | 640x640 |
| Paciencia | 10 |
| Data Augmentation | Ninguna |
| Workers | Default |
| Cache | Enabled |

**Notas**: Configuración inicial sin aplicar técnicas avanzadas de aumento de datos.

---

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

---

### Train 9: Segunda Modificación
**Descripción**: Ajuste de parámetros de Data Augmentation

```bash
!yolo task=detect mode=train epochs=200 data='ppe_data.yaml' model=yolo11n.pt imgsz=640 patience=15 cache=False workers=4 degrees=10 fliplr=0.5 mosaic=0.5 mixup=0.0 copy_paste=0.1
```

| Parámetro | Valor |
|-----------|-------|
| Modelo Base | yolo11n.pt |
| Épocas | 200 |
| Resolución | 640x640 |
| Paciencia | 15 |
| Workers | 4 |
| Cache | False |
| **Data Augmentation** | |
| Rotación (degrees) | 10° |
| Flip Horizontal (fliplr) | 0.5 |
| Mosaic | 0.5 |
| Mixup | 0.0 |
| Copy-Paste | 0.1 |

**Notas**: Reducción de algunos parámetros de augmentation para encontrar un equilibrio óptimo. Aumento de épocas a 200 y paciencia a 15.

---

### Train 10
**Descripción**: Entrenamiento estándar sin augmentation extrema

```bash
!yolo task=detect mode=train epochs=200 data='ppe_data.yaml' model=yolo11n.pt imgsz=640 patience=15 cache=False workers=4
```

| Parámetro | Valor |
|-----------|-------|
| Modelo Base | yolo11n.pt |
| Épocas | 200 |
| Resolución | 640x640 |
| Paciencia | 15 |
| Workers | 4 |
| Cache | False |
| Data Augmentation | Default |

**Notas**: Configuración simplificada utilizando parámetros por defecto de YOLO.

---

### Train 11
**Descripción**: Aumento de épocas y paciencia

```bash
!yolo task=detect mode=train epochs=300 data='ppe_data.yaml' model=yolo11n.pt imgsz=640 patience=25 cache=False workers=4
```

| Parámetro | Valor |
|-----------|-------|
| Modelo Base | yolo11n.pt |
| Épocas | 300 |
| Resolución | 640x640 |
| Paciencia | 25 |
| Workers | 4 |
| Cache | False |
| Data Augmentation | Default |

**Notas**: Se aumentaron significativamente las épocas y paciencia para permitir una mejor convergencia del modelo.

---

### Train 12: Transfer Learning desde Train 11
**Descripción**: Continuación del entrenamiento usando los pesos del Train 11 + nuevas imágenes

```bash
!yolo task=detect mode=train model='runs/detect/train-11/weights/last.pt' data='ppe_data.yaml' epochs=500 patience=40 imgsz=640 cache=False workers=4
```

| Parámetro | Valor |
|-----------|-------|
| Modelo Base | runs/detect/train-11/weights/last.pt |
| Épocas | 500 |
| Resolución | 640x640 |
| Paciencia | 40 |
| Workers | 4 |
| Cache | False |
| Dataset | Expandido con 360 nuevas imágenes |

**Resultado**: ❌ Resultados deficientes en implementación con cámara. Los pesos del Train 11 no generalizaban bien con nuevas imágenes.

**Notas**: Transfer learning desde Train 11. Se añadieron aproximadamente 1000 nuevas imágenes al dataset.

---

### Train 13: Regresión al Modelo Base
**Descripción**: Vuelta a modelo predeterminado de YOLO con dataset expandido

```bash
!yolo task=detect mode=train model=yolo11n.pt data='ppe_data.yaml' epochs=300 patience=30 imgsz=640 cache=False workers=4
```

| Parámetro | Valor |
|-----------|-------|
| Modelo Base | yolo11n.pt |
| Épocas | 300 |
| Resolución | 640x640 |
| Paciencia | 30 |
| Workers | 4 |
| Cache | False |
| Dataset | +360 imágenes |

**Resultado**: ✅ Mejor desempeño en implementación con cámara

---

### Train 14
**Estado**: No documentado - Posiblemente interrumpido a 300 épocas por corte de luz.

**Notas**: Archivo de modelo `train14llegoa300epocasporcorte deluz.pt` indica que alcanzó 300 épocas antes de ser interrumpido.

---

### Train 15: Escalado de Dataset
**Descripción**: Dataset ampliado a ~2600 imágenes + 1000 nuevas

```bash
!yolo task=detect mode=train model=yolo11n.pt data='ppe_data.yaml' epochs=400 patience=50 imgsz=640 cache=False workers=4
```

| Parámetro | Valor |
|-----------|-------|
| Modelo Base | yolo11n.pt |
| Épocas | 400 |
| Resolución | 640x640 |
| Paciencia | 50 |
| Workers | 4 |
| Cache | False |
| Dataset | ~3500 - 3600aprox imágenes |

**Resultado**: ✅ Muy buenos resultados

**Notas**: Entrenamiento largo con dataset significativamente expandido. Alcanzó máximo 300 épocas debido a early stopping.

---

### Train 16: Cambio de Arquitectura a YOLOv11s
**Descripción**: Migración a modelo más robusto (Small en lugar de Nano)

```bash
!yolo task=detect mode=train model=yolo11s.pt data='ppe_data.yaml' epochs=250 patience=25 imgsz=640 workers=6
```

| Parámetro | Valor |
|-----------|-------|
| Modelo Base | **yolo11s.pt** (Small - más parámetros que Nano) |
| Épocas | 250 |
| Resolución | 640x640 |
| Paciencia | 25 |
| Workers | 6 |
| Cache | Default (True) |
| Dataset | ~3500 - 3600 imágenes |

**Resultado**: ✅ Muy buenos resultados, métricas excelentes

**Notas**: 
- Cambio de modelo yolo11n.pt → yolo11s.pt
- Resultados comparables y un poco parecido al Train 15, a pesar de menos épocas
- Mejor generalización de la arquitectura más robusta
- **Recomendación**: Aumentar épocas a 300-400 y paciencia a 40-50 para mejor convergencia

---

## Comparativa de Modelos

| Entrenamiento | Modelo | Épocas | Paciencia | Workers | Datos | Resultado |
|---|---|---|---|---|---|---|
| 1-7 | yolo11n | 180 | 10 | Default | Base | ⚠️ Básico |
| 8 | yolo11n | 180 | 10 | 2 | Base | ⚠️ Augmentation alto |
| 9 | yolo11n | 200 | 15 | 4 | Base | ✓ Balanceado |
| 10 | yolo11n | 200 | 15 | 4 | Base | ✓ Estándar |
| 11 | yolo11n | 300 | 25 | 4 | Base | ✓ Largo |
| 12 | yolo11n | 500 | 40 | 4 | +360 imgs | ❌ Malo en cámara |
| 13 | yolo11n | 300 | 30 | 4 | +360 | ✅ Bueno en cámara |
| 14 | yolo11n | 400 | 50 | 4 | ~3600 | ⏸️ Interrumpido |
| 15 | yolo11n | 400 | 50 | 4 | ~3600 | ✅✅ Excelente |
| **16** | **yolo11s** | **250** | **25** | **6** | **~4500** | **✅✅ Excelente** |

---

## Recomendaciones Futuras

### Para Train 17 o siguiente:
```bash
!yolo task=detect mode=train model=yolo11s.pt data='ppe_data.yaml' epochs=350 patience=40 imgsz=640 workers=6
```

**Razones**:
1. Modelo yolo11s.pt demostró mejor desempeño que yolo11n.pt
2. Aumentar épocas a 350 permitiría mejor convergencia
3. Paciencia de 40 proporciona oportunidad de mejora sin sobreentrenamiento
4. 6 workers optimizado para hardware disponible

---

## Dataset Split
- **Train**: css-data/train
- **Valid**: css-data/valid  
- **Test**: css-data/test

## Clases Detectadas (10 clases)
1. Hardhat (Casco de seguridad)
2. Mask (Mascarilla)
3. NO-Hardhat (Sin casco)
4. NO-Mask (Sin mascarilla)
5. NO-Safety Vest (Sin chaleco)
6. Person (Persona)
7. Safety Cone (Cono de seguridad)
8. Safety Vest (Chaleco de seguridad)
9. machinery (Maquinaria)
10. vehicle (Vehículo)

---

**Última actualización**: 3 de junio de 2026
**Mejor modelo actual**: Train 16 (yolo11s.pt)
