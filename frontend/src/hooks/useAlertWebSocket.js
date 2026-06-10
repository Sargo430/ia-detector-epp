/**
 * useAlertWebSocket
 * -----------------
 * Hook que conecta al endpoint WebSocket del backend Vigilance y llama a
 * `onMessage` con cada alerta recibida.
 *
 * Soporta dos modos:
 *   - Producción: WebSocket real con autenticación JWT y reconexión automática
 *   - Desarrollo: MockWebSocket que genera eventos aleatorios localmente
 *
 * Autenticación contra el backend:
 *   ws://host/ws/alerts?token=<jwt>          ← método primario (query param)
 *   Sec-WebSocket-Protocol: <jwt>            ← fallback (algunos entornos)
 *
 * Configuración via .env:
 *   VITE_WS_URL=ws://localhost:8000/ws/alerts
 *   VITE_USE_MOCK_WS=false
 */

import { useEffect, useRef, useCallback, useState } from 'react'

// ── Configuración ─────────────────────────────────────────────────────────────
const WS_BASE_URL  = import.meta.env.VITE_WS_URL      || 'ws://localhost:8000/ws/alerts'
const USE_MOCK     = import.meta.env.VITE_USE_MOCK_WS  === 'true'
const BASE_DELAY   = 1_000    // ms — delay inicial de reconexión
const MAX_DELAY    = 30_000   // ms — tope del back-off exponencial
const PING_INTERVAL = 30_000  // ms — keepalive al servidor

// ── Tipos de status del WebSocket ────────────────────────────────────────────
// 'connecting' | 'connected' | 'disconnected' | 'auth_error'

// ─────────────────────────────────────────────────────────────────────────────
// Mock WebSocket (solo desarrollo — eliminar en producción si se prefiere)
// ─────────────────────────────────────────────────────────────────────────────
const MOCK_CAMERAS = [
  { id: 'cam-01', name: 'Entrada principal',     zone: 'Zona A' },
  { id: 'cam-02', name: 'Estacionamiento Norte', zone: 'Zona B' },
  { id: 'cam-03', name: 'Pasillo Central',       zone: 'Zona A' },
  { id: 'cam-04', name: 'Sala de Servidores',    zone: 'Zona C' },
  { id: 'cam-06', name: 'Recepción',             zone: 'Zona A' },
]
const MOCK_TYPES = ['person_detected', 'vehicle_detected', 'intrusion', 'loitering', 'object_left']
const MOCK_SEV   = { person_detected: 'info', vehicle_detected: 'info', intrusion: 'critical', loitering: 'warning', object_left: 'warning' }

function createMockWS() {
  const listeners = {}
  const emit = (ev, data) => (listeners[ev] || []).forEach(fn => fn(data))
  let alive = true

  const schedule = () => {
    if (!alive) return
    setTimeout(() => {
      if (!alive) return
      const type = MOCK_TYPES[Math.floor(Math.random() * MOCK_TYPES.length)]
      const cam  = MOCK_CAMERAS[Math.floor(Math.random() * MOCK_CAMERAS.length)]
      emit('message', {
        data: JSON.stringify({
          type:        'alert',
          event_type:  type,
          camera_id:   cam.id,
          camera_name: cam.name,
          zone:        cam.zone,
          severity:    MOCK_SEV[type],
          confidence:  Math.round(75 + Math.random() * 24),
          ts:          new Date().toISOString(),
        }),
      })
      schedule()
    }, 3500 + Math.random() * 4000)
  }

  setTimeout(() => { emit('open', {}); schedule() }, 600)

  return {
    readyState: 1,
    addEventListener: (ev, fn) => { listeners[ev] = listeners[ev] || []; listeners[ev].push(fn) },
    removeEventListener: () => {},
    close: () => { alive = false },
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook principal
// ─────────────────────────────────────────────────────────────────────────────

/**
 * @param {object}   opts
 * @param {function} opts.onMessage   - Callback con el payload del evento
 * @param {string}   [opts.token]     - JWT para autenticación (producción)
 * @param {boolean}  [opts.useMock]   - Forzar mock independientemente del .env
 *
 * @returns {{ status: string, reconnectCount: number }}
 */
export function useAlertWebSocket({ onMessage, token = null, useMock = USE_MOCK }) {
  const wsRef          = useRef(null)
  const retryCount     = useRef(0)
  const retryTimer     = useRef(null)
  const pingTimer      = useRef(null)
  const onMessageRef   = useRef(onMessage)
  const [status,         setStatus]         = useState('connecting')
  const [reconnectCount, setReconnectCount] = useState(0)

  // Mantener la referencia al callback actualizada sin re-conectar
  useEffect(() => { onMessageRef.current = onMessage }, [onMessage])

  const clearTimers = useCallback(() => {
    clearTimeout(retryTimer.current)
    clearInterval(pingTimer.current)
  }, [])

  const connect = useCallback(() => {
    clearTimers()
    setStatus('connecting')

    let ws

    if (useMock) {
      ws = createMockWS()
    } else {
      if (!token) {
        setStatus('auth_error')
        console.error('[WS] No JWT token provided — cannot connect to real WS endpoint')
        return
      }
      const url = `${WS_BASE_URL}?token=${encodeURIComponent(token)}`
      ws = new WebSocket(url)
    }

    wsRef.current = ws

    ws.addEventListener('open', () => {
      setStatus('connected')
      retryCount.current = 0
      setReconnectCount(0)

      // Keepalive: enviar ping cada 30s para mantener la conexión viva
      // (algunos load balancers/proxies cierran conexiones inactivas)
      if (!useMock) {
        pingTimer.current = setInterval(() => {
          try {
            ws.send(JSON.stringify({ type: 'ping' }))
          } catch (_) {}
        }, PING_INTERVAL)
      }
    })

    ws.addEventListener('message', (ev) => {
      let payload
      try {
        payload = typeof ev.data === 'string' ? JSON.parse(ev.data) : ev.data
      } catch (err) {
        console.warn('[WS] Failed to parse message:', err)
        return
      }

      // Ignorar mensajes de control (connected, pong)
      if (payload?.type === 'connected') {
        console.info('[WS] Server confirmed connection for tenant:', payload.tenant_id)
        return
      }
      if (payload?.type === 'pong') return

      // Normalizar: el backend envuelve alertas con type: 'alert'
      const alert = payload?.type === 'alert' ? payload : payload
      onMessageRef.current(alert)
    })

    ws.addEventListener('close', (ev) => {
      clearInterval(pingTimer.current)

      // Códigos de error de aplicación definidos en el backend
      if (ev.code === 4001 || ev.code === 4002) {
        setStatus('auth_error')
        console.error('[WS] Auth error:', ev.reason)
        return  // No reconectar — el token es inválido
      }

      setStatus('disconnected')
      if (!useMock) scheduleReconnect()
    })

    ws.addEventListener('error', (err) => {
      console.error('[WS] Error:', err)
    })
  }, [token, useMock, clearTimers])

  const scheduleReconnect = useCallback(() => {
    const delay = Math.min(BASE_DELAY * 2 ** retryCount.current, MAX_DELAY)
    retryCount.current += 1
    setReconnectCount(retryCount.current)
    console.info(`[WS] Reconnecting in ${delay}ms (attempt ${retryCount.current})`)
    retryTimer.current = setTimeout(connect, delay)
  }, [connect])

  // Iniciar conexión al montar; reconectar si cambia el token
  useEffect(() => {
    connect()
    return () => {
      clearTimers()
      wsRef.current?.close?.()
    }
  }, [connect, clearTimers])

  return { status, reconnectCount }
}
