import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Listen on all network interfaces for network access
    port: 80, // Port 80 - requires Administrator rights
    strictPort: false, // Try next port if 80 is busy
  },
  preview: {
    host: '0.0.0.0', // Listen on all network interfaces for production preview
    port: 80,
    strictPort: false,
  },
  build: {
    outDir: 'dist', // Output directory for production build
    sourcemap: false, // Disable source maps for production
    minify: 'esbuild', // Use esbuild for fast minification
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'chart-vendor': ['recharts'],
        },
      },
    },
  },
})
