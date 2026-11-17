import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/wallet': 'http://127.0.0.1:8000',
      '/prices': 'http://127.0.0.1:8000',
      '/portfolio': 'http://127.0.0.1:8000',
      '/advice': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  }
})
