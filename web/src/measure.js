// Measure the frame the way the .blend measured its references.
//
// `_common.GRADE` was fitted by comparing five numbers between the render and
// the reference clip: mean luma, its standard deviation, the fraction of dark
// pixels, the fraction of bright ones, and saturation. The browser is a third
// renderer of the same city, so it gets held to the same five numbers, read
// off the actual framebuffer rather than judged by eye.
//
//   await window.measure()   ->  { mean, std, dark, bright, sat, rb }
//
// The reference to beat, from renders/city_07_look.png:
//   mean 0.470  std 0.247  dark 24.0%  bright 15.5%  sat 0.388  R/B 1.329
export const REFERENCE = {
  mean: 0.470, std: 0.247, dark: 0.240, bright: 0.155, sat: 0.388, rb: 1.329,
};

export function measureFramebuffer(renderer) {
  const gl = renderer.getContext();
  const w = gl.drawingBufferWidth, h = gl.drawingBufferHeight;
  const px = new Uint8Array(w * h * 4);
  // Straight off the default framebuffer, so what is measured is what is on
  // screen: after tone mapping, after the grade, in display space, exactly
  // like reading a PNG.
  gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);

  let sum = 0, sum2 = 0, dark = 0, bright = 0, sat = 0, r = 0, b = 0;
  const n = w * h;
  for (let i = 0; i < n; i++) {
    const R = px[i * 4] / 255, G = px[i * 4 + 1] / 255, B = px[i * 4 + 2] / 255;
    const l = R * 0.2126 + G * 0.7152 + B * 0.0722;
    sum += l; sum2 += l * l;
    if (l < 0.25) dark++;
    if (l > 0.75) bright++;
    const mx = Math.max(R, G, B), mn = Math.min(R, G, B);
    if (mx > 0) sat += (mx - mn) / mx;
    r += R; b += B;
  }
  const mean = sum / n;
  return {
    mean: +mean.toFixed(3),
    std: +Math.sqrt(Math.max(0, sum2 / n - mean * mean)).toFixed(3),
    dark: +(dark / n).toFixed(3),
    bright: +(bright / n).toFixed(3),
    sat: +(sat / n).toFixed(3),
    rb: +(r / Math.max(b, 1e-6)).toFixed(3),
  };
}

// Side by side with the reference, so the answer is a direction to move in and
// not a table to interpret.
export function compare(got, ref = REFERENCE) {
  const rows = Object.keys(ref).map((k) => {
    const d = got[k] - ref[k];
    const arrow = Math.abs(d) < (k === "rb" ? 0.05 : 0.02) ? "ok"
      : (d > 0 ? "too high" : "too low");
    return `${k.padEnd(7)} ${String(got[k]).padStart(6)}  vs ${String(ref[k]).padStart(6)}  ${arrow}`;
  });
  return rows.join("\n");
}
