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

// (width, target) on this frame, straight out of the table. Frames are 1-based
// because Blender's are.
export function shotAt(shot, frame) {
  const i = Math.min(shot.track.length - 1, Math.max(0, Math.round(frame) - 1));
  return shot.track[i];
}
