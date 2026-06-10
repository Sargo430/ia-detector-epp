import React from 'react'
import { WsStatusPill } from './UI.jsx'

const NAV = [
  { id: 'metrics',  label: 'Métricas',   icon: 'ti-chart-bar' },
  { id: 'cameras',  label: 'Cámaras',    icon: 'ti-camera'    },
  { id: 'alerts',   label: 'Alertas',    icon: 'ti-bell'      },
]

const NAV2 = [
  { id: 'operators', label: 'Operadores',    icon: 'ti-users'    },
  { id: 'settings',  label: 'Configuración', icon: 'ti-settings' },
]

export default function Sidebar({ activeTab, onTab, wsStatus, newAlerts, cameraCount }) {
  return (
    <aside style={{
      width: 200, minWidth: 200,
      background: 'var(--bg2)',
      borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Logo */}
      <div style={{ padding: '20px 16px 16px', display: 'flex', alignItems: 'center', gap: 8, borderBottom: '1px solid var(--border)' }}>
        <div style={{ width: 28, height: 28, background: 'var(--teal)', borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <i className="ti ti-shield-lock" style={{ color: '#fff', fontSize: 15 }} aria-hidden="true" />
        </div>
        <span style={{ fontSize: 15, fontWeight: 500 }}>
          <span style={{ color: 'var(--teal2)' }}>Vigi</span>lance
        </span>
      </div>

      {/* Nav */}
      <nav style={{ padding: '12px 8px', flex: 1 }}>
        <SectionLabel>Panel</SectionLabel>
        {NAV.map(item => (
          <NavItem
            key={item.id}
            item={item}
            active={activeTab === item.id}
            onClick={() => onTab(item.id)}
            badge={
              item.id === 'cameras' ? (
                <Pill color="teal">{cameraCount}</Pill>
              ) : item.id === 'alerts' && newAlerts > 0 ? (
                <Pill color="red" pulse>{newAlerts > 9 ? '9+' : newAlerts}</Pill>
              ) : null
            }
          />
        ))}

        <SectionLabel style={{ marginTop: 8 }}>Sistema</SectionLabel>
        {NAV2.map(item => (
          <NavItem key={item.id} item={item} active={false} onClick={() => {}} />
        ))}
      </nav>

      <WsStatusPill status={wsStatus} />
    </aside>
  )
}

function SectionLabel({ children, style }) {
  return (
    <div style={{ fontSize: 10, color: 'var(--text3)', padding: '8px 10px 4px', letterSpacing: '.06em', textTransform: 'uppercase', ...style }}>
      {children}
    </div>
  )
}

function NavItem({ item, active, onClick, badge }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '8px 10px', borderRadius: 'var(--r)',
        cursor: 'pointer', fontSize: 13, marginBottom: 2,
        border: 'none', width: '100%', textAlign: 'left',
        background: active ? 'var(--teal4)' : 'transparent',
        color: active ? 'var(--teal2)' : 'var(--text2)',
        fontWeight: active ? 500 : 400,
        transition: 'background .15s, color .15s',
      }}
      onMouseEnter={e => { if (!active) { e.currentTarget.style.background = 'var(--bg3)'; e.currentTarget.style.color = 'var(--text)' } }}
      onMouseLeave={e => { if (!active) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text2)' } }}
    >
      <i className={`ti ${item.icon}`} style={{ fontSize: 16 }} aria-hidden="true" />
      {item.label}
      {badge && <span style={{ marginLeft: 'auto' }}>{badge}</span>}
    </button>
  )
}

function Pill({ children, color, pulse }) {
  const colors = {
    teal: { background: 'var(--teal4)', color: 'var(--teal2)', border: '1px solid var(--teal3)' },
    red:  { background: 'var(--red2)',  color: 'var(--red)',   border: '1px solid rgba(248,81,73,.3)' },
  }
  return (
    <span style={{
      padding: '2px 7px', borderRadius: 20, fontSize: 10, fontWeight: 500,
      animation: pulse ? 'pulse 2s infinite' : 'none',
      ...colors[color],
    }}>
      {children}
    </span>
  )
}
