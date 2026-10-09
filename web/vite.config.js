import { defineConfig } from 'vite';

// Relative base so the build works at https://<user>.github.io/tideborn/ and anywhere else.
export default defineConfig({
  base: './',
  build: {
    target: 'es2020',
    chunkSizeWarningLimit: 900,
  },
  server: { host: true },
});
