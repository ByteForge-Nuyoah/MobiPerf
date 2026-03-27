import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/screenshots': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
      '/records': 'http://localhost:8000',
      '/logs': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
