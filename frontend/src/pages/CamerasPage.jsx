import React from 'react'
import { Badge, Btn } from '../components/UI.jsx'

export default function CamerasPage({ cameras }) {
  const online  = cameras.filter(c => c.status === 'online').length
  const offline = cameras.length - online

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <span style={{ color: 'var(--text2)', fontSize: 13 }}>{cameras.length} cámaras registradas</span>
        <Badge variant="green"><i className="ti ti-wifi" style={{ fontSize: 11 }} aria-hidden="true" /> {online} online</Badge>
        <Badge variant="red"  style={{ marginRight: 'auto' }}>
          <i className="ti ti-wifi-off" style={{ fontSize: 11 }} aria-hidden="true" /> {offline} offline
        </Badge>
        <Btn variant="teal" onClick={() => window.open('', '_blank')}>
          <i className="ti ti-plus" style={{ fontSize: 12 }} aria-hidden="true" /> Agregar cámara
        </Btn>
      </div>

      {/* Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
        {cameras.map(cam => <CameraCard key={cam.id} cam={cam} />)}
      </div>
    </div>
  )
}

function CameraCard({ cam }) {
  const online = cam.status === 'online'

  return (
    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r2)', overflow: 'hidden' }}>
      {/* Thumbnail */}
      <div style={{ height: 120, background: 'var(--bg3)', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 6 }}>
        <i
          className={`ti ${online ? 'ti-camera' : 'ti-camera-off'}`}
          style={{ fontSize: 28, color: 'var(--text3)', opacity: .4 }}
          aria-hidden="true"
        />
        <span style={{ fontSize: 10, color: 'var(--text3)' }}>
          {online ? `${cam.fps} fps` : 'sin señal'}
        </span>

        {/* Alert overlay */}
        {cam.alert && (
          <div style={{
            position: 'absolute', inset: 0,
            background: 'rgba(248,81,73,.08)',
            border: '1px solid rgba(248,81,73,.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span style={{ fontSize: 10, color: 'var(--red)', background: 'var(--red2)', padding: '3px 8px', borderRadius: 20 }}>
              <i className="ti ti-alert-triangle" style={{ fontSize: 11 }} aria-hidden="true" /> Evento activo
            </span>
          </div>
        )}

        {/* LIVE pill */}
        <div style={{
          position: 'absolute', top: 8, left: 8,
          display: 'flex', alignItems: 'center', gap: 5,
          background: 'rgba(13,17,23,.75)', padding: '3px 7px', borderRadius: 20,
          fontSize: 10, fontWeight: 500,
        }}>
          <span style={{
            width: 6, height: 6, borderRadius: '50%',
            background: online ? 'var(--green)' : 'var(--red)',
            display: 'inline-block',
            animation: online ? 'pulse 1.5s infinite' : 'none',
          }} />
          {online ? 'LIVE' : 'OFFLINE'}
        </div>

        {/* Zone pill */}
        <div style={{
          position: 'absolute', bottom: 8, right: 8,
          fontSize: 10, background: 'rgba(13,17,23,.75)',
          padding: '3px 7px', borderRadius: 20, color: 'var(--text2)',
        }}>
          {cam.zone}
        </div>
      </div>

      {/* Info */}
      <div style={{ padding: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>{cam.name}</div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--text3)', fontFamily: 'monospace' }}>{cam.ip}</span>
          <Badge variant={online ? 'green' : 'red'} style={{ fontSize: 10 }}>
            {online ? 'Online' : 'Offline'}
          </Badge>
        </div>
        <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
          <Btn variant="teal" style={{ fontSize: 11 }}>
            <i className="ti ti-player-play" style={{ fontSize: 11 }} aria-hidden="true" /> Ver live
          </Btn>
          <Btn style={{ fontSize: 11 }}>
            <i className="ti ti-settings" style={{ fontSize: 11 }} aria-hidden="true" />
          </Btn>
          {online && (
            <Btn variant="danger" style={{ fontSize: 11 }}>
              <i className="ti ti-wifi-off" style={{ fontSize: 11 }} aria-hidden="true" />
            </Btn>
          )}
        </div>
      </div>
    </div>
  )
}
