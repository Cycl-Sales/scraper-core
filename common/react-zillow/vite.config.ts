import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8018',  // Updated to correct backend port
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
