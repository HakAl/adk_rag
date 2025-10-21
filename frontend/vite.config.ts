import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Auth endpoints
      '/register': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/login': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/logout': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/me': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/verify-email': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/resend-verification': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Chat endpoints - use specific paths to avoid conflicting with React Router
      '/chat/coordinator': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/chat/direct': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Session endpoints
      '/sessions': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Other API endpoints
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/stats': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})