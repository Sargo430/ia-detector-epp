import React, { useState, useCallback, useEffect, useRef } from 'react'
import Sidebar      from './components/Sidebar.jsx'
import MetricsPage  from './pages/MetricsPage.jsx'
import CamerasPage  from './pages/CamerasPage.jsx'
import AlertsPage   from './pages/AlertsPage.jsx'
import { Badge }    from './components/UI.jsx'
import { useAlertWebSocket } from './hooks/useAlertWebSocket.js'
import {
  INITIAL_CAMERAS,
  EVENT_LABELS,
  EVENT_SEVERITY,
  TENANT_NAME,
} from './lib/constants.js'

const TAB_TITLES = {
  metrics: 'Métricas y estadísticas',
  cameras: 'Gestión de cámaras',
  alerts:  'Alertas y eventos',
}

// ── Seed alerts ──────────────────────────────────────────────────────────────
function seedAlerts() {
  const typeKeys   = Object.keys(EVENT_LABELS)
  const timeLabels = ['hace 2m','hace 5m','hace 11m','hace 18m','hace 24m','hace 31m','hace 45m','hace 1h']
  return Array.from({ length: 8 }, (_, i) => {
    const t   = typeKeys[Math.floor(Math.random() * typeKeys.length)]
    const cam = INITIAL_CAMERAS[Math.floor(Math.random() * INITIAL_CAMERAS.length)]
    return {
      id:       Date.now() + i,
      title:    EVENT_LABELS[t],
      cam:      cam.name,
      zone:     cam.zone,
      severity: EVENT_SEVERITY[t],
      status:   i < 2 ? 'new' : i < 5 ? 'review' : 'resolved',
      time:     timeLabels[i] || `hace ${Math.floor(Math.random() * 60)}m`,
    }
  })
}

export default function App() {
  const [tab,          setTab]         = useState('metrics')
  const [cameras,      setCameras]     = useState(INITIAL_CAMERAS)
  const [alerts,       setAlerts]      = useState(seedAlerts)
  const [newAlerts,    setNewAlerts]   = useState(0)
  const [stats,        setStats]       = useState({ totalEvents: 47, criticalCount: 3, latency: 142 })
  const [clock,        setClock]       = useState('')
  const alertTimers                    = useRef({})

  // Clock
  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  // WebSocket message handler
  const handleMessage = useCallback((payload) => {
    const { event_type, camera_id, camera_name, zone, severity, confidence } = payload
    const timeStr = new Date().toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' })

    // Append new alert at top
    setAlerts(prev => [{
      id:       Date.now(),
      title:    `${EVENT_LABELS[event_type] || event_type} — ${confidence}%`,
      cam:      camera_name,
      zone,
      severity: severity || EVENT_SEVERITY[event_type] || 'info',
      status:   'new',
      time:     timeStr,
    }, ...prev.slice(0, 199)])  // cap at 200

    // Update stats
    setStats(prev => ({
      ...prev,
      totalEvents:   prev.totalEvents + 1,
      criticalCount: severity === 'critical' ? prev.criticalCount + 1 : prev.criticalCount,
      latency:       Math.round(110 + Math.random() * 80),
    }))

    // Bump new-alert counter only if not on alerts tab
    setTab(current => {
      if (current !== 'alerts') setNewAlerts(n => n + 1)
      return current
    })

    // Flash alert overlay on camera card
    if (severity === 'critical' || severity === 'warning') {
      setCameras(prev => prev.map(c => c.id === camera_id ? { ...c, alert: true } : c))
      clearTimeout(alertTimers.current[camera_id])
      alertTimers.current[camera_id] = setTimeout(() => {
        setCameras(prev => prev.map(c => c.id === camera_id ? { ...c, alert: false } : c))
      }, 6000)
    }
  }, [])

  const { status: wsStatus } = useAlertWebSocket({
    onMessage: handleMessage,
    useMock: true,           // ← cambiar a false y pasar token= cuando el backend esté listo
    // token: authToken,
  })

  const handleTabChange = (id) => {
    setTab(id)
    if (id === 'alerts') setNewAlerts(0)
  }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar
        activeTab={tab}
        onTab={handleTabChange}
        wsStatus={wsStatus}
        newAlerts={newAlerts}
        cameraCount={cameras.length}
      />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Top bar */}
        <div style={{
          height: 52, background: 'var(--bg2)', borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', padding: '0 20px', gap: 12,
        }}>
          <span style={{ fontSize: 15, fontWeight: 500, flex: 1 }}>{TAB_TITLES[tab]}</span>
          <Badge variant="teal">
            <i className="ti ti-building" style={{ fontSize: 11 }} aria-hidden="true" /> {TENANT_NAME}
          </Badge>
          <Badge variant="default" style={{ fontSize: 11 }}>
            <i className="ti ti-clock" style={{ fontSize: 11 }} aria-hidden="true" /> {clock}
          </Badge>
        </div>

        {/* Page content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
          {tab === 'metrics' && <MetricsPage stats={stats} />}
          {tab === 'cameras' && <CamerasPage cameras={cameras} />}
          {tab === 'alerts'  && <AlertsPage  alerts={alerts}  />}
        </div>
      </div>
    </div>
  )
}
