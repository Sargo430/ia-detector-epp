import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy al backend FastAPI en desarrollo
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Proxy WebSocket al backend
      '/ws': {
        target: 'ws://localhost:8765',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
