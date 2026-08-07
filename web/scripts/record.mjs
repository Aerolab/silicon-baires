// Record the shot to a video file, from the browser, without a screen
// recorder anywhere in it.
//
//   npm run record                      1920x1080, 2x supersampled, all 624
//   npm run record -- --w 3840 --h 2160 4K
//   npm run record -- --ss 1 --to 24    a one-second test, fast
//   npm run record -- --headed          watch it happen in a throwaway window
//
// Out: web/capture/city.mp4 (H.264) and web/capture/city.mov (ProRes 422 HQ).
//
// It starts its own Vite server on a free port and its own Chrome with its own
// profile directory, so it does not touch a dev server you have running, and
// it does not touch your browser. Both are killed on the way out, including on
// Ctrl-C — a headless Chrome nobody can see is not a thing to leave behind.
import { spawn } from "node:child_process";
import { createServer } from "vite";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

const argv = process.argv.slice(2);
const arg = (k, d) => {
  const i = argv.indexOf(`--${k}`);
  return i === -1 ? d : argv[i + 1];
};
const has = (k) => argv.includes(`--${k}`);

const opt = {
  w: Number(arg("w", 1920)),
  h: Number(arg("h", 1080)),
  // 2x is 4 times the pixels and the difference between crawling parapet edges
  // and clean ones. It is the single biggest quality knob here, ahead of the
  // output resolution: 1080p supersampled from 2x reads better than a raw 4K.
  ss: Number(arg("ss", 2)),
  from: Number(arg("from", 1)),
  to: arg("to", null),
  name: arg("name", "city"),
  port: Number(arg("port", 5199)),
};

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
if (!fs.existsSync(CHROME)) {
  console.error(`No Chrome at ${CHROME}. Set one, or run the URL by hand:`);
  console.error(`  http://localhost:${opt.port}/?capture=1&w=${opt.w}&h=${opt.h}&ss=${opt.ss}`);
}

const outDir = path.join(root, "capture");
const doneFile = path.join(outDir, `${opt.name}.done`);
fs.mkdirSync(outDir, { recursive: true });
fs.rmSync(doneFile, { force: true });

process.env.CAPTURE_NAME = opt.name;
const server = await createServer({
  root, configFile: path.join(root, "vite.config.js"),
  server: { port: opt.port, strictPort: true },
});
await server.listen();

const params = new URLSearchParams({
  capture: "1", w: String(opt.w), h: String(opt.h), ss: String(opt.ss),
  from: String(opt.from),
});
if (opt.to) params.set("to", String(opt.to));
const url = `http://localhost:${opt.port}/?${params}`;
console.log(`[record] ${url}`);

// The canvas is drawn at w*ss, and Chrome caps a WebGL drawing buffer at the
// GPU's max texture size — so the WINDOW is the video size and the pixel ratio
// does the supersampling, which is how the page is written.
const profile = fs.mkdtempSync(path.join(process.env.TMPDIR || "/tmp", "city-rec-"));
const chrome = spawn(CHROME, [
  ...(has("headed") ? [] : ["--headless=new"]),
  // Headless Chrome falls back to SwiftShader, which renders this city
  // correctly and about thirty times slower. On macOS ANGLE-over-Metal keeps
  // the real GPU; if the frame times below look like seconds rather than tens
  // of milliseconds, that fallback is what happened.
  "--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist",
  "--enable-unsafe-swiftshader",        // rather than failing outright
  `--window-size=${opt.w},${opt.h}`,
  `--user-data-dir=${profile}`,
  "--no-first-run", "--no-default-browser-check", "--disable-extensions",
  "--autoplay-policy=no-user-gesture-required",
  url,
], { stdio: ["ignore", "inherit", "inherit"] });

let closing = false;
const cleanup = async (code) => {
  if (closing) return;
  closing = true;
  chrome.kill("SIGKILL");
  fs.rmSync(profile, { recursive: true, force: true });
  await server.close();
  process.exit(code);
};
process.on("SIGINT", () => cleanup(130));
chrome.on("close", () => { if (!closing) console.log("[record] chrome closed"); });

// Wait for the plugin's receipt. Polling a file rather than sharing state with
// the plugin: Vite loads the config in its own module graph, so the plugin
// instance here would not be the one that ran.
const t0 = Date.now();
while (!fs.existsSync(doneFile)) {
  if (chrome.exitCode !== null && !fs.existsSync(doneFile)) {
    console.error("[record] chrome exited before the capture finished");
    await cleanup(1);
  }
  await new Promise((r) => setTimeout(r, 500));
}
const receipt = JSON.parse(fs.readFileSync(doneFile, "utf8"));
console.log(`[record] ${receipt.frames}/${receipt.expected} frames in ` +
  `${Math.round((Date.now() - t0) / 1000)} s`);
for (const f of receipt.files) {
  const mb = (fs.statSync(f).size / 1e6).toFixed(1);
  console.log(`[record]   ${path.relative(root, f)}  ${mb} MB`);
}
if (!receipt.ok) console.error("[record] INCOMPLETE — see above");
await cleanup(receipt.ok ? 0 : 1);
