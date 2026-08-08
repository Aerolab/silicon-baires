// The city in the browser. Everything it knows comes from web/public/, and
// everything in web/public/ comes from `./bl scripts/city/20_export_web.py`.
// There are no numbers in this file that also live in the .blend.
import * as THREE from "three";
import { EXRLoader } from "three/examples/jsm/loaders/EXRLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { loadCity } from "./city.js";
import { makePost, ENV_INTENSITY } from "./post.js";
import { makeCamera, placeHero, shotAt, fitToAspect } from "./shot.js";
import { measureFramebuffer, compare } from "./measure.js";
import { makeSpots } from "./spots.js";
import { TIER, TIER_WHY } from "./tier.js";
import { createElement, Play, Pause, Orbit, Clapperboard } from "lucide";

// no-store, and everything else keyed on cfg.stamp: the assets have stable
// names, so without this a re-export is invisible until a hard reload.
const cfg = await fetch("./city_shot.json", { cache: "no-store" })
  .then((r) => r.json());
const { grade, sun, sky } = cfg;      // shot is fitted to the window, below
const v = cfg.stamp ? `?v=${cfg.stamp}` : "";

// Diagnostic switches, because "it runs at 10 fps" is not a finding and the
// three candidates cost very different amounts:
//   ?noshadow=1  drop the shadow pass      ?nopost=1  drop the post chain
//   ?taps=8      cheaper depth-of-field    ?shadow=2048  shadow map size
//
// And the three look knobs, for trying a grade before committing to it:
//   ?ev=0.9      exposure, in stops on top of the .blend's
//   ?env=1.2     how much the baked sky fills the shadows
//   ?contrast=1.3
const flags = new URLSearchParams(location.search);
const flag = (k, d) => (flags.has(k) ? Number(flags.get(k)) || 1 : d);
const num = (k, d) => (flags.has(k) ? Number(flags.get(k)) : d);

// --- offline capture -------------------------------------------------------
// ?capture=1 turns the page into a frame server for scripts/record.mjs: the
// clock stops being wall time, the frame size stops being the window, and the
// loop below never starts. See capture.js — nothing else in this file behaves
// differently, which is the point: the video is this page, not a port of it.
const capturing = flags.has("capture");
// THE FRAME IS NOT THE WINDOW. Every place that used innerWidth/innerHeight
// reads these instead, so a capture can ask for 1920x1080 out of whatever
// window a headless browser happens to open.
let viewW = capturing ? num("w", 1920) : innerWidth;
let viewH = capturing ? num("h", 1080) : innerHeight;
// Supersampling: the canvas is rendered ss times larger and ffmpeg scales it
// back down. This page has antialias:false — the scene goes through a
// half-float render target and MSAA does not survive that — so downsampling
// is the only antialiasing there is, and at 1x every parapet edge crawls.
//
// Off capture it comes from tier.js, which is where the phone budget lives.
// ?ss= still wins over both, so a device can be tested at a ratio its tier
// would never pick.
const ss = capturing ? num("ss", 2) : num("ss", TIER.pixelRatio);

// --- the shot, fitted to this window ---------------------------------------
// The rectangle every solid thing in the city occupies, measured by the export
// off the 533 published footprints. The fence below reads it too, and so does
// fitToAspect, which is why it is up here rather than down there.
const bounds = cfg.bounds ?? { x: [-400, 400], y: [-450, 400], top: 80 };
// A window narrower than 16:9 gets a frame longer than the city unless the
// shot is refitted; see fitToAspect. ?pelev= and ?pcap= override the two
// numbers it derives, which is how the values it uses were chosen.
const fitOpts = {
  elevation: flags.has("pelev") ? num("pelev", 0) : undefined,
  cap: flags.has("pcap") ? num("pcap", 0) : undefined,
  hero: flags.has("phero") ? num("phero", 0) : undefined,
  off: flags.has("nofit"),
};
// Never under capture. 1920x1080 IS the shot's own aspect, so the fit would
// return it unchanged anyway — but that is an equality between two divisions,
// and the video is the deliverable. It does not get to depend on a rounding.
let shot = capturing
  ? cfg.shot : fitToAspect(cfg.shot, viewW / viewH, bounds, fitOpts);

// --- the renderer ----------------------------------------------------------
// The one call on this page that can fail before anything else exists: no
// WebGL2, a blocked context, a driver the browser has blacklisted. Uncaught it
// is a white page, which is the failure this whole guard is here to replace.
let renderer;
try {
  renderer = new THREE.WebGLRenderer({
    antialias: false, alpha: false,
    // Only under capture: toBlob() reads the drawing buffer one task after the
    // draw, and without this it is already cleared — every PNG comes out blank.
    preserveDrawingBuffer: capturing,
  });
} catch (err) {
  window.__cityFail?.("Este navegador no pudo abrir WebGL, que es lo que dibuja la ciudad.");
  throw err;
}
renderer.setPixelRatio(ss);
renderer.setSize(viewW, viewH);
// NoToneMapping on purpose: the scene renders into a linear buffer and post.js
// applies AgX at the very end, which is the order Blender uses. See post.js.
renderer.toneMapping = THREE.NoToneMapping;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

// --- when the context goes -------------------------------------------------
// THE ONE FAILURE THAT REPORTS ITSELF. A driver reset, a background tab the
// system reclaimed, or a GPU allocation that did not fit all end here, and
// without preventDefault the browser never even tries to give it back.
//
// What this cannot catch is the failure tier.js exists for: when Chromium
// kills the renderer process for memory, no JavaScript on this page runs
// again, so there is nothing left to draw a message with. Cheap frames are the
// only defence against that one; this is the defence against everything else.
let alive = true;
renderer.domElement.addEventListener("webglcontextlost", (e) => {
  e.preventDefault();
  alive = false;                       // stop the loop: drawing now floods errors
  // force: this one covers the screen even with the city already up, because
  // a lost context IS the whole page. Everything else after startup is not.
  window.__cityFail?.(
    "El navegador cortó la escena 3D, casi siempre por falta de memoria de video.",
    true);
}, false);
renderer.domElement.addEventListener("webglcontextrestored", () => {
  // Rebuilding 28.215 instances, the PMREM and the post chain by hand is a
  // second copy of the whole startup. A reload is the same thing, correct by
  // construction, and by now the visitor is looking at a button anyway.
  location.reload();
}, false);

const scene = new THREE.Scene();

// --- the light -------------------------------------------------------------
// SUN_ENERGY is Blender's irradiance in W/m^2 and three's DirectionalLight
// intensity is the same quantity, so the number crosses over unchanged.
const sunLight = new THREE.DirectionalLight(
  new THREE.Color(...sun.color), sun.energy);
sunLight.position.set(...sun.position);
sunLight.target.position.set(0, 0, 0);
sunLight.castShadow = !flag("noshadow", 0);
sunLight.shadow.mapSize.setScalar(flag("shadow", TIER.shadowMapSize));
sunLight.shadow.bias = -0.0006;
sunLight.shadow.normalBias = 0.35;
scene.add(sunLight, sunLight.target);

// The sky, baked out of the .blend's Nishita world with its strength and its
// desaturation already in it. It is the background AND the fill light: this is
// as close as a rasteriser gets to what Cycles does with the same world.
//
// The load is a promise as well as a callback, because a capture must not
// start before it resolves: the sky is the fill light, and the frames drawn
// without it are a darker, contrastier city that no measurement would catch —
// they simply are the first few seconds of the video.
const skyReady = new Promise((resolve) => {
new EXRLoader().load(`./${sky.file}${v}`, (tex) => {
  tex.mapping = THREE.EquirectangularReflectionMapping;
  const pmrem = new THREE.PMREMGenerator(renderer);
  const env = pmrem.fromEquirectangular(tex).texture;
  scene.environment = env;
  scene.background = env;
  // scene.environmentIntensity, NOT material.envMapIntensity: when the light
  // comes from scene.environment the per-material knob does nothing at all,
  // and turning it from 1 to 40 with no effect reads as "the sky is not
  // lighting anything" rather than "wrong dial".
  scene.environmentIntensity = num("env", ENV_INTENSITY);
  pmrem.dispose();
  tex.dispose();
  resolve();
});
});

// --- the city --------------------------------------------------------------
const loadEl = document.getElementById("load");
const barEl = document.querySelector("#bar i");
const pctEl = document.getElementById("pct");
const city = await loadCity(v, (p) => {
  const n = Math.round(p * 100);
  if (barEl) barEl.style.width = `${n}%`;
  if (pctEl) pctEl.textContent = `${n}%`;
});
if (barEl) barEl.style.width = "100%";
if (pctEl) pctEl.textContent = "100%";
scene.add(city.root);
Object.assign(window, { city, scene, THREE, renderer, sunLight });
// camera and controls are attached further down, once they exist.

// The knobs the look was calibrated with, in one place for the next time:
//   window.look.env(0.9); window.look.exposure(0.5); window.measure().table
// See LOOK CALIBRATION in post.js.
window.look = {
  env: (x) => (scene.environmentIntensity = x),
  exposure: (x) => (post.uniforms.uExposure.value = x),
  contrast: (x) => (post.uniforms.uContrast.value = x),
};

// The shadow camera follows the shot instead of covering the whole city: at
// 700 m across, a 4096 map is 17 cm per texel and every shadow edge crawls.
// Fitted to the frame it is under 5 cm, which is what makes the buildings sit
// on the ground rather than hover over it.
const shadowCam = sunLight.shadow.camera;
shadowCam.near = 1;
shadowCam.far = shot.distance * 3;

const camera = makeCamera(shot);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.enabled = false;            // the move owns the camera until "libre"

// --- the fence -------------------------------------------------------------
// Free navigation is fenced to the BUILT city, not to the scene. Step 03 lays
// a sheet of ground well past the last block, so an unfenced orbit spends most
// of its travel over bare site — and, worse, goes under it, where the city is
// a silhouette floating on nothing.
//
// The rectangle comes from the export, which measures it off the 533 published
// footprints rather than off a bounding box. MARGIN is deliberate slack: the
// edge of the map should be reachable, just not somewhere you can fall off.
const MARGIN = 60;                     // metres of overshoot allowed
const fenceMin = new THREE.Vector3(bounds.x[0] - MARGIN, bounds.y[0] - MARGIN, 0);
const fenceMax = new THREE.Vector3(bounds.x[1] + MARGIN, bounds.y[1] + MARGIN,
                                   bounds.top);
// HOW LOW THE CAMERA MAY GO, and 90 degrees is not the answer even though it
// is where the ground is. The site is a finite sheet: from 8 degrees above the
// horizon the frame is half sky, with the cut edge of the map running across
// it and the city sitting on a slab in the air. The limit is what keeps the
// frame full of city, not what keeps the camera above the road.
//
// 24 degrees is a little flatter than the film's own 30.6, so the free camera
// can find angles the shot never uses without finding the edge of the world.
controls.maxPolarAngle = THREE.MathUtils.degToRad(90 - 24);
controls.minPolarAngle = THREE.MathUtils.degToRad(8);   // near top-down
controls.screenSpacePanning = false;   // pan along the ground, not the screen
// The built city is 785 m across. Framing 700 shows nearly all of it and still
// lands the far edge outside the frame; the near end is about one block.
const FREE_WIDTH = shot.hero_width;    // the frustum free mode is fixed at
controls.minZoom = FREE_WIDTH / 700;
controls.maxZoom = FREE_WIDTH / 25;

const _eye = new THREE.Vector3();
// Degrees above the horizon. The depth of field needs it, and so does every
// limit below: how wide the frame may get and how far the target may wander
// both depend on how much ground a tilted frame covers.
const elevationOf = (cam, target) => THREE.MathUtils.radToDeg(Math.asin(
  THREE.MathUtils.clamp(_dir.copy(cam.position).sub(target).normalize().z, -1, 1)));
const _dir = new THREE.Vector3();
const CITY_SPAN = Math.max(bounds.x[1] - bounds.x[0], bounds.y[1] - bounds.y[0]);

// HOW WIDE THE FRAME MAY GET, AND IT DEPENDS ON THE ANGLE. An orthographic
// frame of width w and height w/aspect, tilted `elevation` above the ground,
// covers w/aspect/sin(elevation) metres of DEPTH — at 24 degrees that is two
// and a half times its own height. So a 700 m frame is 980 m deep, and over a
// 785 m city the difference is sky and bare site. Capping the width alone does
// not catch it; the cap has to fall as the camera drops.
function widestFrame(elevationDeg, aspect) {
  const s = Math.sin(THREE.MathUtils.degToRad(Math.max(elevationDeg, 4)));
  return Math.min(700, CITY_SPAN * s * aspect);
}

// And where the frame may be centred, which shrinks as the frame grows: a view
// that covers the whole city has nowhere to go but the middle of it. When the
// window is wider than the city the range inverts, and the target collapses to
// the centre rather than flipping — which is the correct answer, not a guard.
function clampToFence(v, radius) {
  const axis = (value, lo, hi) => {
    const a = lo + radius - MARGIN, b = hi - radius + MARGIN;
    return a > b ? (lo + hi) / 2 : THREE.MathUtils.clamp(value, a, b);
  };
  const x = axis(v.x, bounds.x[0], bounds.x[1]);
  const y = axis(v.y, bounds.y[0], bounds.y[1]);
  const z = THREE.MathUtils.clamp(v.z, fenceMin.z, fenceMax.z);
  const moved = x !== v.x || y !== v.y || z !== v.z;
  v.set(x, y, z);
  return moved;
}

// shot last, so the post chain anchors its depth of field on the FITTED
// elevation rather than on the .blend's. They are the same number on 16:9.
const post = makePost(renderer, {
  ...cfg, taps: flag("taps", 24), samples: TIER.samples, shot });
// ?spots=1 — numbered roofs, for pointing at one. Off by default and not part
// of the piece; see spots.js.
const spots = flag("spots", 0) ? await makeSpots(camera) : null;
Object.assign(window, { post, camera, controls });
if (flags.has("ev")) post.uniforms.uExposure.value = num("ev", 0);
if (flags.has("contrast")) post.uniforms.uContrast.value = num("contrast", 1);
post.setSize(renderer.domElement.width, renderer.domElement.height);

// --- the transport ---------------------------------------------------------
const ui = {
  play: document.getElementById("play"),
  scrub: document.getElementById("scrub"),
  frame: document.getElementById("frame"),
  free: document.getElementById("free"),
  stats: document.getElementById("stats"),
};
ui.scrub.max = String(shot.frames);

// The counters are off by default. ?stats=1 brings them back, and window.stats
// reads them once without turning anything on.
const showStats = flags.has("stats");
if (showStats) {
  ui.stats.classList.add("on");
  ui.frame.classList.add("on");
}
window.stats = () => ({
  fps: Math.round(fps), ...city.stats,
  // What profile this device got and what decided it, because the only thing
  // that ever comes back from a phone is a screenshot.
  tier: TIER.name, ss, samples: TIER.samples,
  shadow: sunLight.shadow.mapSize.x, why: TIER_WHY,
  // The fitted shot, which on anything 16:9 or wider is the .blend's own.
  aspect: +(viewW / viewH).toFixed(3),
  elevation: +shot.elevation.toFixed(1),
  wOpen: +shot.track[0][0].toFixed(1),
  wHero: +shot.track[shot.track.length - 1][0].toFixed(1),
});

let frame = 1;
let playing = true;
let free = false;
let last = performance.now();

// Each button shows the action it performs, not the state it is in: playing
// shows a pause, and the shot shows an orbit.
const setIcon = (el, icon, label) => {
  el.replaceChildren(createElement(icon));
  el.title = label;
  el.setAttribute("aria-label", label);
};
const paint = () => {
  setIcon(ui.play, playing ? Pause : Play,
          playing ? "Pausar (espacio)" : "Reproducir (espacio)");
  setIcon(ui.free, free ? Clapperboard : Orbit,
          free ? "Volver al plano (F)" : "Cámara libre (F)");
};

ui.play.onclick = () => {
  playing = !playing;
  paint();
};
ui.scrub.oninput = () => {
  frame = Number(ui.scrub.value);
  playing = false;
  paint();
};
function setFree(on) {
  free = on;
  controls.enabled = free;
  paint();
  if (!free) return;
  // Hand OrbitControls the camera exactly where the move left it, so switching
  // does not jump. The frustum is then FIXED at FREE_WIDTH and the wheel works
  // through camera.zoom, which is the only thing minZoom and maxZoom can fence
  // — they cannot fence a frustum that keeps changing.
  const [w, tx, ty] = shotAt(shot, frame);
  placeHero(camera, shot, FREE_WIDTH, tx, ty, viewW / viewH);
  camera.zoom = FREE_WIDTH / w;        // after placeHero, which resets it to 1
  camera.updateProjectionMatrix();
  controls.target.set(tx, ty, 0);
  controls.update();
}

ui.free.onclick = () => setFree(!free);
addEventListener("keydown", (e) => {
  if (e.code === "Space") { e.preventDefault(); ui.play.click(); }
  if (e.code === "KeyF") ui.free.click();
});

addEventListener("resize", () => {
  if (capturing) return;             // the frame is the capture's, not the window's
  viewW = innerWidth; viewH = innerHeight;
  renderer.setSize(viewW, viewH);
  post.setSize(renderer.domElement.width, renderer.domElement.height);
  // Rotating a phone changes the aspect by a factor of four, so the fit is
  // re-derived rather than kept. The post chain's SPREAD_K is not: it anchors
  // the depth of field on the hero frame, which is a look constant, not a
  // framing one, and re-anchoring it mid-shot would visibly re-focus.
  if (!capturing) shot = fitToAspect(cfg.shot, viewW / viewH, bounds, fitOpts);
});

// --- the loop --------------------------------------------------------------
// Frame time over a fixed window rather than a smoothed instantaneous rate:
// the smoothed one takes eight seconds to converge at 7 fps, which is long
// enough to read the wrong number and act on it.
// DRAWING IS SEPARATE FROM THE LOOP, so that measuring does not depend on the
// tab being in front. requestAnimationFrame does not fire in a background tab,
// which turned a look calibration into twenty minutes of debugging a promise
// that was never going to resolve.
let fps = 0, windowFrames = 0, windowStart = performance.now();

function drawFrame(now) {
  city.setFrame(frame);

  const [width, tx, ty] = shotAt(shot, frame);
  const aspect = viewW / viewH;
  let framing;
  if (free) {
    controls.update();
    // The zoom-out limit is re-derived every frame, because it depends on how
    // low the camera currently is. minZoom alone would be a constant, and the
    // constant that is safe at 24 degrees is a needlessly tight one at 80.
    const el = elevationOf(camera, controls.target);
    controls.minZoom = (camera.right - camera.left) /
      widestFrame(el, viewW / viewH);
    if (camera.zoom < controls.minZoom) {
      camera.zoom = controls.minZoom;
      camera.updateProjectionMatrix();
    }
    // Keep the target inside the fence and carry the camera with it, rather
    // than clamping the target alone: clamping only the target swings the
    // camera around a point that stopped moving, which reads as the city
    // spinning away from you.
    //
    // The offset is READ THIS FRAME, after controls.update(), never cached. A
    // cached one is a stale one the moment the target is against the fence —
    // the camera would keep being restored to an old orientation, so rotating
    // while panned to the edge did nothing, and the polar limit that
    // OrbitControls had just enforced was overwritten a line later.
    // Keep the ortho box in step with the wheel: OrbitControls zooms an
    // orthographic camera through camera.zoom, and the post chain needs the
    // width in metres, not the zoom factor.
    framing = { width: (camera.right - camera.left) / camera.zoom };

    _eye.copy(camera.position).sub(controls.target);
    // The reach of the view over the ground: its width, or its depth when the
    // camera is low enough that depth is the larger of the two.
    const reach = Math.max(
      framing.width,
      framing.width / (viewW / viewH) /
        Math.sin(THREE.MathUtils.degToRad(Math.max(el, 4)))) / 2;
    if (clampToFence(controls.target, reach)) {
      camera.position.copy(controls.target).add(_eye);
    }
  } else {
    framing = placeHero(camera, shot, width, tx, ty, aspect);
  }

  // The shadow camera, fitted to what the frame actually shows.
  const cover = framing.width * 1.15;
  shadowCam.left = -cover; shadowCam.right = cover;
  shadowCam.top = cover; shadowCam.bottom = -cover;
  shadowCam.updateProjectionMatrix();
  const focus = free ? controls.target : new THREE.Vector3(tx, ty, 0);
  sunLight.target.position.copy(focus);
  sunLight.position.copy(focus).add(new THREE.Vector3(...sun.position));
  sunLight.target.updateMatrixWorld();

  post.setFraming(framing.width, shot.hero_width, camera.near, camera.far,
                  free ? elevationOf(camera, controls.target) : shot.elevation,
                  free ? viewW / viewH : undefined);
  if (flag("nopost", 0)) {
    renderer.setRenderTarget(null);
    renderer.render(scene, camera);
  } else {
    post.render(scene, camera, now / 1000);
  }

  if (spots) spots.update();

  if (showStats) {
    ui.frame.textContent =
      `${String(Math.round(frame)).padStart(3, "0")} / ${shot.frames}`;
    ui.stats.textContent =
      `${fps.toFixed(0)} fps (${(1000 / fps).toFixed(1)} ms) · ${city.stats.drawCalls} draw calls · ` +
      `${city.stats.nodes.toLocaleString("es-AR")} instancias · ` +
      `${city.stats.movers.toLocaleString("es-AR")} en movimiento`;
  }
}

function tick(now) {
  if (!alive) return;                  // the context is gone; see webglcontextlost
  requestAnimationFrame(tick);
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  if (++windowFrames >= 30) {
    fps = (windowFrames * 1000) / (now - windowStart);
    windowFrames = 0;
    windowStart = now;
  }
  if (playing) {
    frame += dt * shot.fps;
    if (frame > shot.frames) {
      // THE SHOT LANDS AND THE CAMERA IS HANDED OVER. The move ends on the
      // approved hero framing after four seconds held on the title, so that is
      // the frame to start exploring from — setFree reads it before the clock
      // wraps, which is why this order matters.
      if (!free) setFree(true);
      // The city keeps running underneath. Step 11's traffic is 26 seconds
      // long and it loops; freezing it would leave you orbiting a photograph.
      frame = 1;
    }
    ui.scrub.value = String(Math.round(frame));
  }
  drawFrame(now);
}

// window.measure(frame) draws that frame and reads the pixels straight back —
// synchronous, so it works with the tab in the background. Defaults to the last
// frame, which is the one renders/city_07_look.png is.
window.measure = (at = shot.frames) => {
  frame = at;
  playing = false;
  paint();
  drawFrame(performance.now());
  const got = measureFramebuffer(renderer);
  return { got, table: compare(got) };
};

paint();
loadEl.classList.add("gone");
// From here on the city is up, so a later error is a bug in one corner rather
// than a page that never started: the guard in index.html stops covering the
// screen for it. A lost context still does, because that one IS the whole page.
window.__cityRunning = true;

if (capturing) {
  // No requestAnimationFrame at all under capture. The loop above advances the
  // clock by how long the last frame TOOK, which is exactly what makes a screen
  // recording of a heavy frame stutter; the recorder asks for frame n, waits
  // for it however long it takes, and asks for n+1.
  const { runCapture } = await import("./capture.js");
  await skyReady;
  await runCapture({
    canvas: renderer.domElement,
    frames: shot.frames, fps: shot.fps, width: viewW, height: viewH, ss,
    from: num("from", 1), to: num("to", shot.frames),
    // The one thing the recorder is allowed to drive. Time is derived from the
    // frame number rather than read off the clock, so the grain is the same on
    // a re-run and a slow frame does not become a long one.
    draw: (n) => {
      frame = n;
      playing = false;
      drawFrame((n / shot.fps) * 1000);
    },
  });
} else {
  requestAnimationFrame(tick);
}
