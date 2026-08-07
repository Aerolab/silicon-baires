// The server half of the offline capture: three endpoints that turn a stream
// of PNGs from the page into one video file, with no frames on disk.
//
// The page posts each frame and waits for the response, so backpressure is the
// protocol: the reply is sent once ffmpeg has taken the bytes. That is what
// keeps a 4K capture from buffering gigabytes of PNG in node while ffmpeg
// encodes at its own pace.
//
// It only exists in the dev server. `vite build` does not carry it, and with
// no capture running it never touches a request.
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

// Two outputs, always both, because they are for different things and the
// expensive part (drawing 624 frames) is shared:
//
//   mp4   H.264, yuv420p, CRF 14. Plays anywhere, small enough to send.
//   mov   ProRes 422 HQ. What goes into an edit — no long-GOP, no 4:2:0
//         chroma, so a cut or a title over it does not soften the frame.
//
// The scale is lanczos and it is doing the antialiasing: the page renders with
// antialias:false (the post chain's half-float target cannot carry MSAA), so
// every edge in the city is hard until this filter averages it down.
const ENCODERS = {
  mp4: (w, h) => [
    "-vf", `scale=${w}:${h}:flags=lanczos`,
    "-c:v", "libx264", "-preset", "slow", "-crf", "14",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
  ],
  mov: (w, h) => [
    "-vf", `scale=${w}:${h}:flags=lanczos`,
    "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le",
  ],
};

const readBody = (req) => new Promise((resolve, reject) => {
  const chunks = [];
  req.on("data", (c) => chunks.push(c));
  req.on("end", () => resolve(Buffer.concat(chunks)));
  req.on("error", reject);
});

export function capture({ outDir = "capture", name = "city" } = {}) {
  let job = null;

  const startFfmpeg = (cfg) => {
    fs.mkdirSync(outDir, { recursive: true });
    const outputs = Object.entries(ENCODERS).flatMap(([ext, args]) => [
      ...args(cfg.width, cfg.height), path.join(outDir, `${name}.${ext}`),
    ]);
    // One ffmpeg, one input, two outputs: the PNG stream is decoded once and
    // the scale runs twice. Two processes would mean sending every frame
    // twice, which at 4K is the whole cost of the capture.
    const args = [
      "-hide_banner", "-loglevel", "warning", "-y",
      "-f", "image2pipe", "-vcodec", "png",
      "-framerate", String(cfg.fps), "-i", "pipe:0",
      ...outputs,
    ];
    const proc = spawn("ffmpeg", args, { stdio: ["pipe", "inherit", "inherit"] });
    proc.on("error", (e) => console.error("[capture] ffmpeg:", e.message));
    return proc;
  };

  return {
    name: "city-capture",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use("/__capture/start", async (req, res) => {
        const cfg = JSON.parse((await readBody(req)).toString() || "{}");
        job = { cfg, seen: 0, started: Date.now(), proc: startFfmpeg(cfg) };
        console.log(`[capture] ${cfg.frames} frames · ` +
          `${cfg.srcWidth}x${cfg.srcHeight} -> ${cfg.width}x${cfg.height} ` +
          `(${cfg.ss}x) · ${cfg.fps} fps`);
        // The recorder waits on this file rather than on a socket: it is the
        // one signal that survives the browser, the server and ffmpeg all
        // being separate processes.
        fs.rmSync(path.join(outDir, `${name}.done`), { force: true });
        res.end("ok");
      });

      server.middlewares.use("/__capture/frame", async (req, res) => {
        if (!job) { res.statusCode = 409; return res.end("no capture running"); }
        const png = await readBody(req);
        // Reply only once ffmpeg has taken it. write() returning false means
        // its buffer is full — waiting for "drain" is what stops the page from
        // running ahead of the encoder.
        const ok = job.proc.stdin.write(png);
        if (!ok) await new Promise((r) => job.proc.stdin.once("drain", r));
        job.seen++;
        if (job.seen % 24 === 0 || job.seen === job.cfg.frames) {
          const s = (Date.now() - job.started) / 1000;
          console.log(`[capture] ${job.seen}/${job.cfg.frames} · ` +
            `${(s / job.seen).toFixed(2)} s/frame · ` +
            `${Math.round((job.cfg.frames - job.seen) * s / job.seen)} s left`);
        }
        res.end("ok");
      });

      server.middlewares.use("/__capture/done", async (req, res) => {
        if (!job) { res.statusCode = 409; return res.end("no capture running"); }
        const { proc, cfg, seen, started } = job;
        job = null;
        proc.stdin.end();
        const code = await new Promise((r) => proc.on("close", r));
        const took = Math.round((Date.now() - started) / 1000);
        const files = Object.keys(ENCODERS).map((ext) =>
          path.join(outDir, `${name}.${ext}`));
        // The frames the page SENT, not the frames it meant to: a capture that
        // stopped halfway still produces a playable file, and this is the only
        // place the difference is visible.
        fs.writeFileSync(path.join(outDir, `${name}.done`), JSON.stringify({
          ok: code === 0 && seen === cfg.frames,
          frames: seen, expected: cfg.frames, code, seconds: took, files, cfg,
        }, null, 2));
        console.log(`[capture] ffmpeg exited ${code} · ${seen} frames · ${took} s`);
        res.end("ok");
      });
    },
  };
}
