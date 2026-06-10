// ---------------------------------------------------------------------------
// Cámaras mock — reemplazar con GET /api/cameras
// ---------------------------------------------------------------------------
export const INITIAL_CAMERAS = [
  { id: 'cam-01', name: 'Entrada principal',    ip: '192.168.1.101', zone: 'Zona A', fps: 25, status: 'online'  },
  { id: 'cam-02', name: 'Estacionamiento Norte', ip: '192.168.1.102', zone: 'Zona B', fps: 20, status: 'online'  },
  { id: 'cam-03', name: 'Pasillo Central',       ip: '192.168.1.103', zone: 'Zona A', fps: 25, status: 'online'  },
  { id: 'cam-04', name: 'Sala de Servidores',    ip: '192.168.1.104', zone: 'Zona C', fps: 15, status: 'online'  },
  { id: 'cam-05', name: 'Perímetro Sur',         ip: '192.168.1.105', zone: 'Zona B', fps: 20, status: 'offline' },
  { id: 'cam-06', name: 'Recepción',             ip: '192.168.1.106', zone: 'Zona A', fps: 25, status: 'online'  },
]

// ---------------------------------------------------------------------------
// Tipos de evento
// ---------------------------------------------------------------------------
export const EVENT_TYPES = [
  'person_detected',
  'vehicle_detected',
  'intrusion',
  'loitering',
  'object_left',
]

export const EVENT_LABELS = {
  person_detected:  'Persona detectada',
  vehicle_detected: 'Vehículo detectado',
  intrusion:        'Intrusión detectada',
  loitering:        'Merodeo detectado',
  object_left:      'Objeto abandonado',
}

export const EVENT_SEVERITY = {
  person_detected:  'info',
  vehicle_detected: 'info',
  intrusion:        'critical',
  loitering:        'warning',
  object_left:      'warning',
}

export const CHART_COLORS = ['#2ea89c', '#58a6ff', '#f85149', '#d29922', '#bc8cff']

// ---------------------------------------------------------------------------
// Tenant (reemplazar con JWT decode o /api/me)
// ---------------------------------------------------------------------------
export const TENANT_NAME = 'Acme Corp'
