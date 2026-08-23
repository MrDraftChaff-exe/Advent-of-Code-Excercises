import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/wiki-media": {
        target: "https://upload.wikimedia.org",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/wiki-media/, ""),
      },
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 4173,
    proxy: {
      "/wiki-media": {
        target: "https://upload.wikimedia.org",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/wiki-media/, ""),
      },
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
