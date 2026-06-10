import React from 'react'


// ── Badge ──────────────────────────────────────────────────────────────────
export function Badge({ variant = 'default', children, style }) {
  const vars = {
    teal:    { background: 'var(--teal4)',   color: 'var(--teal2)',  border: '1px solid var(--teal3)' },
    green:   { background: 'var(--green2)',  color: 'var(--green)'                                    },
    red:     { background: 'var(--red2)',    color: 'var(--red)'                                      },
    amber:   { background: 'var(--amber2)',  color: 'var(--amber)'                                    },
    blue:    { background: 'var(--blue2)',   color: 'var(--blue)'                                     },
    default: { background: 'var(--bg3)',     color: 'var(--text2)',  border: '1px solid var(--border)' },
  }
  const base = {
    display: 'inline-flex', alignItems: 'center', gap: 4,
    padding: '3px 8px', borderRadius: 20, fontSize: 11, fontWeight: 500,
    ...vars[variant],
    ...style,
  }
  return <span style={base}>{children}</span>
}

// ── Button ─────────────────────────────────────────────────────────────────
export function Btn({ variant = 'default', onClick, children, style }) {
  const vars = {
    teal:    { borderColor: 'var(--teal3)', color: 'var(--teal2)', background: 'var(--teal4)' },
    danger:  { borderColor: 'rgba(248,81,73,.4)', color: 'var(--red)', background: 'var(--red2)' },
    default: { borderColor: 'var(--border)', color: 'var(--text2)', background: 'var(--bg3)' },
  }
  const base = {
    display: 'inline-flex', alignItems: 'center', gap: 5,
    padding: '4px 10px', borderRadius: 6, fontSize: 11,
    border: '1px solid', cursor: 'pointer',
    transition: 'opacity .15s',
    ...vars[variant],
    ...style,
  }
  return (
    <button style={base} onClick={onClick}
      onMouseEnter={e => e.currentTarget.style.opacity = '.75'}
      onMouseLeave={e => e.currentTarget.style.opacity = '1'}
    >
      {children}
    </button>
  )
}

// ── Metric Card ────────────────────────────────────────────────────────────
export function MetricCard({ label, value, sub, subVariant, icon }) {
  const subColor = subVariant === 'up' ? 'var(--green)' : subVariant === 'down' ? 'var(--red)' : 'var(--text2)'
  return (
    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r2)', padding: 16 }}>
      <div style={{ fontSize: 11, color: 'var(--text3)', marginBottom: 8, letterSpacing: '.04em', textTransform: 'uppercase' }}>
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 500, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: subColor, marginTop: 6 }}>{sub}</div>}
    </div>
  )
}

// ── WS Status pill ─────────────────────────────────────────────────────────
export function WsStatusPill({ status }) {
  const map = {
    connected:    { dot: 'var(--green)',  label: 'Conectado',    labelColor: 'var(--green)'  },
    connecting:   { dot: 'var(--amber)',  label: 'Conectando…',  labelColor: 'var(--amber)'  },
    disconnected: { dot: 'var(--red)',    label: 'Desconectado', labelColor: 'var(--red)'    },
  }
  const s = map[status] || map.connecting
  return (
    <div style={{ margin: 8, padding: '10px 12px', background: 'var(--bg3)', borderRadius: 'var(--r)', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <span style={{
          width: 7, height: 7, borderRadius: '50%', background: s.dot,
          display: 'inline-block', marginRight: 6,
          animation: status === 'connected' ? 'pulse 2s infinite' : 'none',
        }} />
        <span style={{ fontSize: 11, color: 'var(--text2)' }}>
          <b style={{ color: s.labelColor, fontWeight: 500 }}>{s.label}</b>
        </span>
      </div>
      <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 4 }}>vigilance-ws:8765</div>
    </div>
  )
}
