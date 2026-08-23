import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins: [react()],
  base: '/web/dist/',
  server: {
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/ws': 'ws://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    manifest: true,
  },
});
