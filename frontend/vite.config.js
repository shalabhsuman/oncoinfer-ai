import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/classify': 'http://localhost:8080',
      '/health': 'http://localhost:8080'
    }
  }
})
