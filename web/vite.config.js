import { defineConfig } from "vite";

export default defineConfig({
  // Relative, so a build can be dropped in any subfolder of any host.
  base: "./",
  server: { port: 5173, open: false },
  build: { assetsInlineLimit: 0, chunkSizeWarningLimit: 2000 },
});
