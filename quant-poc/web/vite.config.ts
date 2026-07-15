import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy REST + WebSocket to the FastAPI backend so the frontend can use
// same-origin relative paths (/api, /ws) in dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
