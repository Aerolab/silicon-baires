// Offline capture: draw the shot one frame at a time and hand each PNG to the
// dev server, which pipes it straight into ffmpeg.
//
// WHY NOT A SCREEN RECORDING. The page runs at whatever rate the machine
// manages, and a recorder samples it at whatever rate IT manages, so every
// frame the browser misses is a frame the video repeats, and every frame the
// recorder misses is one it drops. Neither is visible while it happens and
// both are obvious in the file: the pan judders and the traffic stutters even
// though nothing on screen ever did. It also samples the window, so the video
// is as big as the window was, compressed by whatever the recorder chose.
//
// So: no clock. `draw(n)` is synchronous, the frame is only sent once it is
// drawn, and the next one is only asked for once the server took the last.
// 624 frames come out at exactly 624 frames, however long each one took.
//
// WHY NOT MediaRecorder / CCapture. MediaRecorder is the same sampling problem
// with a VP8 bitrate on top. CCapture builds a video in the tab, which means
// holding it in memory and re-encoding what ffmpeg would do better anyway.

// PNG rather than JPEG: it is the last generation-loss-free point in the
// chain, and ffmpeg is doing a downscale after it. A 4K PNG is ~6 MB and it is
// never written to disk — the plugin pipes it to ffmpeg and it is gone.
const toPNG = (canvas) =>
  new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("toBlob() gave nothing"))),
                  "image/png"));

const post = async (url, body, type) => {
  const res = await fetch(url, {
    method: "POST", body,
    headers: type ? { "content-type": type } : undefined,
  });
  if (!res.ok) throw new Error(`${url}: ${res.status} ${await res.text()}`);
  return res;
};

export async function runCapture({ canvas, draw, frames, fps, width, height,
                                   ss, from, to }) {
  const first = Math.max(1, Math.round(from));
  const last = Math.min(frames, Math.round(to));
  const total = last - first + 1;

  // The canvas is the SUPERSAMPLED size; `width`x`height` is what the video is.
  // ffmpeg does the scale, so the recorder has to be told both.
  await post("/__capture/start", JSON.stringify({
    fps, width, height, srcWidth: canvas.width, srcHeight: canvas.height,
    frames: total, ss,
  }), "application/json");

  const started = performance.now();
  for (let n = first; n <= last; n++) {
    draw(n);
    const png = await toPNG(canvas);
    await post(`/__capture/frame?n=${n}`, png, "image/png");

    const done = n - first + 1;
    const per = (performance.now() - started) / done / 1000;
    // On the page, because a headless browser's console is not where anyone is
    // looking; record.mjs prints the same numbers from the server side.
    status(`frame ${n} / ${last} · ${per.toFixed(2)} s each · ` +
           `${Math.round((total - done) * per)} s left`);
  }

  await post("/__capture/done", "{}", "application/json");
  status(`done — ${total} frames`);
}

function status(text) {
  let el = document.getElementById("capture-status");
  if (!el) {
    el = document.createElement("div");
    el.id = "capture-status";
    el.style.cssText = "position:fixed;left:16px;top:16px;z-index:99;" +
      "background:#000a;padding:6px 10px;border-radius:6px";
    document.body.appendChild(el);
  }
  el.textContent = text;
}
