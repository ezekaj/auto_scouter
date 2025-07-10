import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    host: true,
  },
  build: {
    outDir: 'dist',
    // Production optimizations (less aggressive for mobile debugging)
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: false, // Keep console logs for mobile debugging
        drop_debugger: true,
      },
    },
    // Code splitting for better caching
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-tabs'],
          query: ['@tanstack/react-query'],
          icons: ['lucide-react'],
        },
      },
    },
    // Asset optimization
    assetsInlineLimit: 4096,
    chunkSizeWarningLimit: 1000,
    // Enable source maps for mobile debugging
    sourcemap: true,
  },
  // Preview server configuration
  preview: {
    port: 3000,
    host: true,
  },
})
