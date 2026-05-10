import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "^/auth/(register|login|me)$": "http://127.0.0.1:8000",
      "^/dashboard(/.*)?$": "http://127.0.0.1:8000",
      "^/favorites(/.*)?$": "http://127.0.0.1:8000",
      "^/plans(/.*)?$": "http://127.0.0.1:8000",
      "/api": "http://127.0.0.1:8000",
      "^/qa/ask$": "http://127.0.0.1:8000",
      "^/schools/(search|\\d+(/score-lines)?)$": "http://127.0.0.1:8000",
      "^/recommendations/generate$": "http://127.0.0.1:8000",
      "^/reports/(submit|[^/]+)$": "http://127.0.0.1:8000"
    }
  }
});
