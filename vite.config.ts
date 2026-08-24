import { defineConfig } from "vitest/config";
import type { Plugin } from "vite";
import react from "@vitejs/plugin-react";
import type { IncomingMessage, ServerResponse } from "node:http";

function zipAttachment(): Plugin {
  const middleware = (
    req: IncomingMessage,
    res: ServerResponse,
    next: () => void,
  ) => {
    const url = req.url ?? "";
    if (!/\.zip(\?|$)/.test(url)) {
      next();
      return;
    }
    const name = decodeURIComponent(
      url.split("/").pop()?.split("?")[0] ?? "download.zip",
    );
    res.setHeader("Content-Disposition", `attachment; filename="${name}"`);
    next();
  };
  return {
    name: "zip-attachment",
    configureServer(server) {
      server.middlewares.use(middleware);
    },
    configurePreviewServer(server) {
      server.middlewares.use(middleware);
    },
  };
}

export default defineConfig({
  plugins: [react(), zipAttachment()],
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
