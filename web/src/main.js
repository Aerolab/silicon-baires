// The city in the browser. Everything it knows comes from web/public/, and
// everything in web/public/ comes from `./bl scripts/city/20_export_web.py`.
// There are no numbers in this file that also live in the .blend.
import * as THREE from "three";
import { EXRLoader } from "three/examples/jsm/loaders/EXRLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { loadCity } from "./city.js";
import { makePost, ENV_INTENSITY } from "./post.js";
import { makeCamera, placeHero, shotAt } from "./shot.js";
import { measureFramebuffer, compare } from "./measure.js";
import { createElement, Play, Pause, Orbit, Clapperboard } from "lucide";

// no-store, and everything else keyed on cfg.stamp: the assets have stable
// names, so without this a re-export is invisible until a hard reload.
const cfg = await fetch("./city_shot.json", { cache: "no-store" })
  .then((r) => r.json());
const { shot, grade, sun, sky } = cfg;
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

// --- the renderer ----------------------------------------------------------
const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: false });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
// NoToneMapping on purpose: the scene renders into a linear buffer and post.js
// applies AgX at the very end, which is the order Blender uses. See post.js.
renderer.toneMapping = THREE.NoToneMapping;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();

// --- the light -------------------------------------------------------------
// SUN_ENERGY is Blender's irradiance in W/m^2 and three's DirectionalLight
// intensity is the same quantity, so the number crosses over unchanged.
const sunLight = new THREE.DirectionalLight(
  new THREE.Color(...sun.color), sun.energy);
sunLight.position.set(...sun.position);
sunLight.target.position.set(0, 0, 0);
sunLight.castShadow = !flag("noshadow", 0);
sunLight.shadow.mapSize.setScalar(flag("shadow", 4096));
sunLight.shadow.bias = -0.0006;
sunLight.shadow.normalBias = 0.35;
scene.add(sunLight, sunLight.target);

// The sky, baked out of the .blend's Nishita world with its strength and its
// desaturation already in it. It is the background AND the fill light: this is
// as close as a rasteriser gets to what Cycles does with the same world.
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
});

// --- the city --------------------------------------------------------------
const loadEl = document.getElementById("load");
const city = await loadCity(v);
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
const bounds = cfg.bounds ?? { x: [-400, 400], y: [-450, 400], top: 80 };
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

const post = makePost(renderer, { ...cfg, taps: flag("taps", 24) });
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
if (showStats) ui.stats.classList.add("on");
window.stats = () => ({ fps: Math.round(fps), ...city.stats });

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
ui.free.onclick = () => {
  free = !free;
  controls.enabled = free;
  paint();
  if (free) {
    // Hand OrbitControls the camera exactly where the move left it, so
    // switching does not jump. The frustum is then FIXED at FREE_WIDTH and the
    // wheel works through camera.zoom, which is the only thing minZoom and
    // maxZoom can fence — they cannot fence a frustum that keeps changing.
    const [w, tx, ty] = shotAt(shot, frame);
    placeHero(camera, shot, FREE_WIDTH, tx, ty, innerWidth / innerHeight);
    camera.zoom = FREE_WIDTH / w;      // after placeHero, which resets it to 1
    camera.updateProjectionMatrix();
    controls.target.set(tx, ty, 0);
    controls.update();
  }
};
addEventListener("keydown", (e) => {
  if (e.code === "Space") { e.preventDefault(); ui.play.click(); }
  if (e.code === "KeyF") ui.free.click();
});

addEventListener("resize", () => {
  renderer.setSize(innerWidth, innerHeight);
  post.setSize(renderer.domElement.width, renderer.domElement.height);
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
  const aspect = innerWidth / innerHeight;
  let framing;
  if (free) {
    controls.update();
    // The zoom-out limit is re-derived every frame, because it depends on how
    // low the camera currently is. minZoom alone would be a constant, and the
    // constant that is safe at 24 degrees is a needlessly tight one at 80.
    const el = elevationOf(camera, controls.target);
    controls.minZoom = (camera.right - camera.left) /
      widestFrame(el, innerWidth / innerHeight);
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
      framing.width / (innerWidth / innerHeight) /
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
                  free ? innerWidth / innerHeight : undefined);
  if (flag("nopost", 0)) {
    renderer.setRenderTarget(null);
    renderer.render(scene, camera);
  } else {
    post.render(scene, camera, now / 1000);
  }

  ui.frame.textContent = `${String(Math.round(frame)).padStart(3, "0")} / ${shot.frames}`;
  if (showStats) {
    ui.stats.textContent =
      `${fps.toFixed(0)} fps (${(1000 / fps).toFixed(1)} ms) · ${city.stats.drawCalls} draw calls · ` +
      `${city.stats.nodes.toLocaleString("es-AR")} instancias · ` +
      `${city.stats.movers.toLocaleString("es-AR")} en movimiento`;
  }
}

function tick(now) {
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
    if (frame > shot.frames) frame = 1;
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
requestAnimationFrame(tick);
