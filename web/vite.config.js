import { defineConfig } from "vite";
import { capture } from "./vite-plugin-capture.js";

// THE ONE THING IN THE PAGE THAT CANNOT BE RELATIVE. Every asset here loads off
// `./`, which is why a build drops into any host. Open Graph is the exception:
// og:image and og:url are read by a crawler that has no page context, so they
// have to be absolute or the card comes up blank.
//
// Taken from Vercel's own build env rather than typed in, so pointing a custom
// domain at the project is all it takes — nothing here needs editing. The
// fallback is the project's default domain, which is also what a local build
// gets, and `%SITE_URL%` is what index.html interpolates.
const SITE_URL = "https://" + (process.env.VERCEL_PROJECT_PRODUCTION_URL ||
                               "silicon-baires.vercel.app");

const siteUrl = () => ({
  name: "site-url",
  transformIndexHtml: (html) => html.replaceAll("%SITE_URL%", SITE_URL),
});

export default defineConfig({
  // Relative, so a build can be dropped in any subfolder of any host.
  base: "./",
  // Dev only (apply: "serve"), and inert unless a capture is running.
  // See scripts/record.mjs.
  plugins: [siteUrl(),
            capture({ outDir: "capture", name: process.env.CAPTURE_NAME || "city" })],
  server: { port: 5173, open: false },
  build: { assetsInlineLimit: 0, chunkSizeWarningLimit: 2000 },
});
