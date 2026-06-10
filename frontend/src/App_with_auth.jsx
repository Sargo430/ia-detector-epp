/**
 * App.jsx — snippet de integración con autenticación JWT
 * --------------------------------------------------------
 * Muestra cómo conectar el hook al WebSocket real cuando se tiene un JWT.
 *
 * Asume que el token se obtiene del backend tras el login
 * (POST /api/v1/auth/login → { access_token, refresh_token }).
 *
 * Por simplicidad, el token se guarda en memoria (useState).
 * NO usar localStorage/sessionStorage — no funcionan en artifacts de Claude.ai
 * y son vulnerables a XSS. En producción, usar httpOnly cookies o memory store.
 */

import React, { useState, useCallback } from 'react'
import { useAlertWebSocket } from './hooks/useAlertWebSocket'

// ── Ejemplo mínimo de auth store en memoria ───────────────────────────────────
function useAuthToken() {
  const [token, setToken] = useState(null)

  const login = useCallback(async (username, password) => {
    const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
    })
    if (!res.ok) throw new Error('Login failed')
    const { access_token } = await res.json()
    setToken(access_token)
    return access_token
  }, [])

  const logout = useCallback(() => setToken(null), [])

  return { token, login, logout }
}

// ── Cómo usar el hook con el token real ──────────────────────────────────────

export default function App() {
  const { token, login, logout } = useAuthToken()

  const handleMessage = useCallback((payload) => {
    // Mismo handler que ya existe en App.jsx
    console.log('Alert received:', payload)
  }, [])

  const { status, reconnectCount } = useAlertWebSocket({
    onMessage: handleMessage,
    token,                       // ← pasar el JWT aquí
    useMock: !token,             // ← mock mientras no hay sesión, real cuando hay token
  })

  // Si no hay token todavía, mostrar pantalla de login
  if (!token) {
    return <LoginScreen onLogin={login} />
  }

  // ... resto del dashboard igual
  return (
    <div>
      {/* WS status: {status}, reconexiones: {reconnectCount} */}
      {/* <Sidebar wsStatus={status} ... /> */}
    </div>
  )
}

function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState(null)
  const [loading,  setLoading]  = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)
    try {
      await onLogin(username, password)
    } catch (err) {
      setError('Credenciales inválidas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)' }}>
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 12, padding: 32, width: 360 }}>
        <h2 style={{ marginBottom: 24, color: 'var(--teal2)' }}>Vigilance</h2>
        <input
          type="text"
          placeholder="Usuario"
          value={username}
          onChange={e => setUsername(e.target.value)}
          style={{ width: '100%', marginBottom: 12, padding: '8px 12px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)' }}
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={e => setPassword(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          style={{ width: '100%', marginBottom: 16, padding: '8px 12px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)' }}
        />
        {error && <div style={{ color: 'var(--red)', fontSize: 12, marginBottom: 12 }}>{error}</div>}
        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{ width: '100%', padding: '9px', background: 'var(--teal)', border: 'none', borderRadius: 8, color: '#fff', fontWeight: 500, cursor: 'pointer' }}
        >
          {loading ? 'Ingresando...' : 'Ingresar'}
        </button>
      </div>
    </div>
  )
}
