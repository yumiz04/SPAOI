import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// El proxy evita problemas de CORS durante el desarrollo: el navegador cree que
// llama a /agent (mismo origen) y Vite reenvía a la API FastAPI del agente.
// Para cambiar el destino del agente, edita AGENT_TARGET.
const AGENT_TARGET = 'http://localhost:8090';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/agent': {
        target: AGENT_TARGET,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/agent/, ''),
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});