import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const backendProxy = process.env.VITE_BACKEND_PROXY || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: backendProxy,
        changeOrigin: true
      }
    }
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts'
  }
});
