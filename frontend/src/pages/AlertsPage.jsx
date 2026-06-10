import React, { useState, useMemo } from 'react'

const SEVERITY_ICON = {
  critical: 'ti-alert-triangle',
  warning:  'ti-alert-circle',
  info:     'ti-info-circle',
}

const STATUS_LABEL = { new: 'Nuevo', review: 'Revisando', resolved: 'Resuelto' }

export default function AlertsPage({ alerts }) {
  const [filter, setFilter]   = useState('all')
  const [query,  setQuery]    = useState('')

  const filtered = useMemo(() => {
    return alerts.filter(a => {
      if (filter === 'critical' && a.severity !== 'critical') return false
      if (filter === 'warning'  && a.severity !== 'warning')  return false
      if (filter === 'new'      && a.status   !== 'new')      return false
      const q = query.toLowerCase()
      if (q && !a.title.toLowerCase().includes(q) && !a.cam.toLowerCase().includes(q)) return false
      return true
    })
  }, [alerts, filter, query])

  return (
    <div>
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        <div style={{ position: 'relative' }}>
          <i className="ti ti-search" style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text3)', fontSize: 14, pointerEvents: 'none' }} aria-hidden="true" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Buscar alertas..."
            style={{
              background: 'var(--bg3)', border: '1px solid var(--border)',
              borderRadius: 'var(--r)', padding: '6px 12px 6px 32px',
              color: 'var(--text)', fontSize: 13, width: 200, outline: 'none',
            }}
          />
        </div>
        {['all','critical','warning','new'].map(f => (
          <FilterBtn key={f} active={filter === f} onClick={() => setFilter(f)}>
            {{ all: 'Todas', critical: 'Críticas', warning: 'Avisos', new: 'Sin revisar' }[f]}
          </FilterBtn>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text3)' }}>
          {filtered.length} alerta{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text3)' }}>
            <i className="ti ti-bell-off" style={{ fontSize: 32, display: 'block', marginBottom: 8 }} aria-hidden="true" />
            Sin alertas que mostrar
          </div>
        ) : (
          filtered.slice(0, 50).map(a => <AlertRow key={a.id} alert={a} />)
        )}
      </div>
    </div>
  )
}

function AlertRow({ alert: a }) {
  const icon = SEVERITY_ICON[a.severity] || 'ti-bell'
  const iconStyle = {
    critical: { background: 'var(--red2)',   color: 'var(--red)'   },
    warning:  { background: 'var(--amber2)', color: 'var(--amber)' },
    info:     { background: 'var(--blue2)',  color: 'var(--blue)'  },
  }[a.severity] || {}

  const statusStyle = {
    new:      { background: 'var(--red2)',   color: 'var(--red)'   },
    review:   { background: 'var(--amber2)', color: 'var(--amber)' },
    resolved: { background: 'var(--green2)', color: 'var(--green)' },
  }[a.status] || {}

  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: 'var(--r2)', padding: '14px 16px',
      display: 'flex', gap: 14, alignItems: 'flex-start',
      animation: 'slideIn .25s ease',
    }}>
      <div style={{
        width: 34, height: 34, borderRadius: 8,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0, fontSize: 16, ...iconStyle,
      }}>
        <i className={`ti ${icon}`} aria-hidden="true" />
      </div>

      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 3 }}>{a.title}</div>
        <div style={{ fontSize: 11, color: 'var(--text3)', display: 'flex', gap: 10, alignItems: 'center' }}>
          <span><i className="ti ti-camera" style={{ fontSize: 11 }} aria-hidden="true" /> {a.cam}</span>
          <span><i className="ti ti-map-pin" style={{ fontSize: 11 }} aria-hidden="true" /> {a.zone}</span>
          <span style={{ padding: '2px 7px', borderRadius: 20, fontSize: 10, fontWeight: 500, ...statusStyle }}>
            {STATUS_LABEL[a.status] || a.status}
          </span>
        </div>
      </div>

      <span style={{ fontSize: 11, color: 'var(--text3)', whiteSpace: 'nowrap' }}>{a.time}</span>
    </div>
  )
}

function FilterBtn({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '5px 12px', borderRadius: 20, fontSize: 12, cursor: 'pointer',
        border: '1px solid', transition: 'background .15s, color .15s',
        background: active ? 'var(--teal4)' : 'transparent',
        borderColor: active ? 'var(--teal3)' : 'var(--border)',
        color: active ? 'var(--teal2)' : 'var(--text2)',
      }}
    >
      {children}
    </button>
  )
}
