# Vigilance Dashboard

Panel de control para la plataforma de videovigilancia Vigilance. Construido con React + Vite, conectado al backend mediante WebSocket para alertas en tiempo real.

## Stack

- **React 18** + Vite
- **Chart.js** via react-chartjs-2 (métricas y gráficos)
- **WebSocket** con reconexión automática (back-off exponencial)
- **Tabler Icons** (webfont, sin dependencia npm)

## Estructura

```
src/
├── components/
│   ├── Sidebar.jsx        # Navegación lateral con indicador WS
│   └── UI.jsx             # Badge, Btn, MetricCard, WsStatusPill
├── hooks/
│   └── useAlertWebSocket.js  # Hook WS con mock y auto-reconnect
├── lib/
│   └── constants.js       # Cámaras, tipos de evento, colores
├── pages/
│   ├── MetricsPage.jsx    # Métricas + gráficos
│   ├── CamerasPage.jsx    # Grid de cámaras con estado live
│   └── AlertsPage.jsx     # Feed de alertas con filtros
├── App.jsx                # Root: estado global + wiring WS
└── index.css              # Design tokens (CSS vars)
```

## Inicio rápido

```bash
npm install
cp .env.example .env
npm run dev
```

Abre http://localhost:5173

## Conectar al backend real

### 1. Desactivar el mock en `App.jsx`

```jsx
// src/App.jsx
const { status: wsStatus } = useAlertWebSocket({
  onMessage: handleMessage,
  useMock: false,        // ← cambiar esto
  token: authToken,      // ← JWT del store de auth
})
```

### 2. Variables de entorno

```env
VITE_WS_URL=wss://api.vigilance.yourdomain.com/ws/alerts
VITE_API_URL=https://api.vigilance.yourdomain.com
```

### 3. Endpoint WebSocket esperado en FastAPI

```
GET /ws/alerts?token=<jwt>
```

Payload que el hook espera por cada mensaje:

```json
{
  "event_type":  "intrusion",
  "camera_id":   "cam-03",
  "camera_name": "Pasillo Central",
  "zone":        "Zona A",
  "severity":    "critical",
  "confidence":  94,
  "ts":          "2025-03-12T14:32:00Z"
}
```

### 4. Poblar cámaras desde la API

Reemplazar `INITIAL_CAMERAS` en `src/lib/constants.js` con un `useEffect` que llame a `GET /api/cameras`.

## Build para producción

```bash
npm run build
# Salida en dist/ — servir con Nginx o similar
```

## Próximos pasos sugeridos

- [ ] Login screen con JWT (almacenar en memory, pasar al WS)
- [ ] Fetch dinámico de cámaras desde `GET /api/cameras`
- [ ] Reproductor de clips en modal (MinIO presigned GET URL)
- [ ] Filtro por tenant (multi-tenant admin view)
- [ ] Notificaciones de escritorio (`Notification API`) para alertas críticas
