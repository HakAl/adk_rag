import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH || '/',
  server: {
    port: 3000,
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks: {
          // React core
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],

          // UI libraries
          'ui-vendor': [
            'lucide-react',
            'date-fns',
            'clsx',
            'tailwind-merge',
            'class-variance-authority',
          ],

          // React Query
          'query-vendor': ['@tanstack/react-query'],

          // Markdown and syntax highlighting
          'markdown-vendor': [
            'react-markdown',
            'react-syntax-highlighter',
          ],
        },
      },
    },
    chunkSizeWarningLimit: 800,
  },
})