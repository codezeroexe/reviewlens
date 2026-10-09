import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy: browser calls /analyze on this origin, so no CORS needed.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/analyze": "http://127.0.0.1:8001" },
  },
});
