// The camera move, flown from the table the export wrote.
//
// It does NOT re-derive the easing. `_common.shot_at()` is eased time over an
// exponential zoom tied to the pan, and a second implementation of that in
// JavaScript is exactly the kind of shared number this project has a whole
// documentation section about. 20_export_web.py samples it once per frame and
// the browser reads the row.
import * as THREE from "three";

export function makeCamera(shot) {
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, shot.distance * 4);
  cam.up.set(0, 0, 1);           // Z-up, like the .blend
  return cam;
}

// Where the hero camera sits for a given (width, target): the canonical orbit
// out of _common.place_hero, in the same two lines of trigonometry.
export function placeHero(cam, shot, width, tx, ty, aspect) {
  const a = THREE.MathUtils.degToRad(shot.azimuth);
  const e = THREE.MathUtils.degToRad(shot.elevation);
  const target = new THREE.Vector3(tx, ty, 0);
  const eye = new THREE.Vector3(
    Math.cos(a) * Math.cos(e), Math.sin(a) * Math.cos(e), Math.sin(e),
  ).multiplyScalar(shot.distance).add(target);

  cam.position.copy(eye);
  cam.lookAt(target);

  // The .blend renders 1920x1080 and the deliverable is that frame. A browser
  // window is any shape at all, so the frame is fitted rather than assumed:
  // the shot's width is honoured on the narrow axis, which means a wide window
  // shows MORE city than the render and never less. Cropping the approved
  // framing to fit a window would be a different shot.
  const shotAspect = 1 / shot.aspect;                 // 1920/1080
  let w = width, h = width * shot.aspect;
  if (aspect > shotAspect) w = h * aspect; else h = w / aspect;

  cam.left = -w / 2; cam.right = w / 2;
  cam.top = h / 2; cam.bottom = -h / 2;
  // zoom too, because free orbit drives an orthographic camera through it and
  // leaves it wherever the wheel stopped. Without this the shot comes back
  // framed at whatever the last free look was, which still renders a perfectly
  // plausible city — at the wrong scale.
  cam.zoom = 1;
  cam.updateProjectionMatrix();
  return { target, width: w, height: h };
}

// HOW MUCH FRAME THE CITY CAN ACTUALLY FILL, asked of the shot rather than
// only of free orbit. It is main.js's widestFrame() applied one level up.
//
// placeHero honours the shot's WIDTH on the narrow axis, so a narrower window
// gets the extra as HEIGHT — and height on a tilted orthographic frame is
// DEPTH over the ground. A phone at 0,46 turns a 306 m frame into a 662 m one,
// which is 1300 m of ground on a city 786 m across: the city comes out as a
// diagonal band with sky in one corner and bare site in the other.
//
// THE TEST IS NOT "narrower than 16:9", AND GETTING THAT WRONG BROKE DESKTOP.
// It was, for one revision, and 16:10 is 1,6 — so every MacBook, every window
// that is not maximised, and the 1280x800 the checks themselves run in all
// took the phone's framing: the move flattened to one width with no zoom in
// it, on machines that had no problem to fix. The question is not the aspect,
// it is whether the frame the move opens on still lands on city, and below
// 0,765 it does not.
export function fitToAspect(shot, aspect, bounds, opts = {}) {
  const span = Math.max(bounds.x[1] - bounds.x[0], bounds.y[1] - bounds.y[0]);
  const widest = (deg) =>
    span * Math.sin(THREE.MathUtils.degToRad(deg)) * aspect;

  const track = shot.track;
  const wMax = track.reduce((m, r) => Math.max(m, r[0]), 0);
  const heroOld = shot.hero_width;

  // What the city can fill at the shot's own angle, against what the move
  // opens on. 16:9 gives 711 against 306, 16:10 gives 640, 4:3 gives 533, 1:1
  // gives 400 — all of them clear, all of them untouched. A phone gives 185.
  const fill = widest(shot.elevation);
  const forced = opts.cap !== undefined || opts.hero !== undefined ||
                 opts.elevation !== undefined;
  if (opts.off || (!forced && fill >= wMax)) return shot;

  // ONE WIDTH FOR THE WHOLE PAN. The move does not open where it cannot open:
  // every wider opening was put on a phone and looked at, and they all spend
  // the one thing a 0,46 frame is short of — the city being close enough to
  // read — on a zoom that has nowhere to go anyway. It scales with how far
  // short the frame falls, so it is 167 m on a 3:4 window and 118 on a phone.
  //
  // The floor is the title, and the .blend measures it: `title_reach` is
  // published by 20_export_web.py — screen space, from the centre of the frame
  // the move lands on — because the browser has no copy of where BUENOS AIRES
  // is and should not grow one. It is a REACH and not a width: the title is
  // 94,2 m across but sits 50,6 m off centre, so a frame needs 101,3 m to hold
  // it, not 94,2. TITLE_FILL is the share it may take; 1.0 puts the letters on
  // the edges.
  const TITLE_FILL = 0.86;
  const titleMin = shot.title_reach
    ? (2 * shot.title_reach.u) / TITLE_FILL : heroOld;
  const hero = opts.hero ?? THREE.MathUtils.clamp(
    heroOld * (fill / wMax), Math.min(titleMin, heroOld), heroOld);

  // Anything at or below the hero collapses the exponent below to 0, which is
  // what "does not open" means. ?pcap= reaches the widths measured on the way,
  // because they are what a cap MEANS on this shot:
  //
  //   233   widest() at 40°. Still shows a wedge of bare site in the corner:
  //         widest() assumes a frame CENTRED on the city, and the opening one
  //         sits out by the south-east corner where the ground runs out sooner.
  //   205   the same wedge, smaller.
  //   185   widest() at the shot's own 30,6°. Clean, and the widest that is.
  const cap = opts.cap ?? hero;

  // THE ANGLE IS DERIVED FROM THE WIDTH ACTUALLY FLOWN, not from the table's
  // opening. Reading wMax — 306 m — needed 57° and pinned to the 40° ceiling;
  // at 118 the same question answers 19°, under the shot's own 30,6, so the
  // camera stays where the .blend put it and the frame keeps the film's
  // perspective instead of going flat. The ceiling is still here for a window
  // that lands between the two, and 40 is where it sits because past that the
  // buildings read as a map. asin over 1 is NaN, and a NaN elevation is a
  // camera pointing nowhere.
  const need = THREE.MathUtils.clamp(cap / (span * aspect), 0, 1);
  const elevation = opts.elevation ?? Math.min(
    opts.maxElevation ?? 40,
    Math.max(shot.elevation, THREE.MathUtils.radToDeg(Math.asin(need))));

  // A POWER CURVE AND NOT A SCALE. w' = hero·(w/heroOld)^p maps the table's
  // last frame — which is heroOld — onto the new hero exactly, and its widest
  // onto the cap; everything between rides the same curve, so a move that does
  // open keeps its shape.
  const p = cap > hero && wMax > heroOld
    ? Math.log(cap / hero) / Math.log(wMax / heroOld) : 0;
  return {
    ...shot, elevation, hero_width: hero,
    track: track.map(([w, tx, ty]) =>
      [hero * Math.pow(Math.max(w, heroOld) / heroOld, p), tx, ty]),
  };
}

// (width, target) on this frame, straight out of the table. Frames are 1-based
// because Blender's are.
export function shotAt(shot, frame) {
  const i = Math.min(shot.track.length - 1, Math.max(0, Math.round(frame) - 1));
  return shot.track[i];
}
