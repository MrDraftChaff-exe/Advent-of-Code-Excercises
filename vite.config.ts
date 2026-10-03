import { defineConfig } from "vitest/config";
import type { Plugin } from "vite";
import react from "@vitejs/plugin-react";
import fs from "node:fs";
import path from "node:path";
import type { IncomingMessage, ServerResponse } from "node:http";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));

function zipAttachment(): Plugin {
  const middleware = (
    req: IncomingMessage,
    res: ServerResponse,
    next: () => void,
  ) => {
    const urlPath = decodeURIComponent((req.url ?? "").split("?")[0] ?? "");
    if (!urlPath.endsWith(".zip")) {
      next();
      return;
    }
    const name = path.basename(urlPath);
    const file = path.join(ROOT, "public", urlPath.replace(/^\//, ""));
    if (!fs.existsSync(file) || !fs.statSync(file).isFile()) {
      res.statusCode = 404;
      res.setHeader("Content-Type", "text/plain; charset=utf-8");
      res.end("zip not found");
      return;
    }
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
