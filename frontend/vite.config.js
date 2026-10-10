import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy: browser calls /analyze on this origin, so no CORS needed.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/analyze": "http://127.0.0.1:8001",
      "/complaints": "http://127.0.0.1:8001",
      "/contradictions": "http://127.0.0.1:8001",
      "/suspicion": "http://127.0.0.1:8001",
      "/insights": "http://127.0.0.1:8001",
      "/app": "http://127.0.0.1:8001",
    },
  },
});
