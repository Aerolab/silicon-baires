import { defineConfig } from "vite";
import { capture } from "./vite-plugin-capture.js";

export default defineConfig({
  // Relative, so a build can be dropped in any subfolder of any host.
  base: "./",
  // Dev only (apply: "serve"), and inert unless a capture is running.
  // See scripts/record.mjs.
  plugins: [capture({ outDir: "capture", name: process.env.CAPTURE_NAME || "city" })],
  server: { port: 5173, open: false },
  build: { assetsInlineLimit: 0, chunkSizeWarningLimit: 2000 },
});
