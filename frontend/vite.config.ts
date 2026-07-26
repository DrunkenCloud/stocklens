import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// server.port fixed to 3000 to match the backend's CORS allow_origins (backend/main.py)
export default defineConfig({
  plugins: [react()],
  server: { port: 3000 },
});
