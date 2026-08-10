// The easter egg: click the Vercel disc and the city turns Vercel black.
//
// Click the floating disc over the HQ and every building fades to the near
// black of that brand, then back again on a second click. Nothing else in the
// page changes: the sun, the sky, the grade and the move are all as they were,
// so it reads as the city changing colour rather than as a different render.
//
// WHAT TURNS AND WHAT DOES NOT. The facades, the glass and the pavement —
// listed by name from the palette that built them (_palette.py). Cars, foliage,
// water, the asphalt and the logos themselves keep their colour, which is what
// makes the frame still look like a city at night rather than a silhouette.
// BUENOS AIRES stays scarlet: it is the one warm thing left in the shot. The
// list is matched by prefix against the material names in the glb, so a new
// concrete needs no edit here.
//
// WHY MATERIALS AND NOT A POST EFFECT. A filter over the whole frame would
// darken the cars and the trees too, and it would fight the AgX pass that
// post.js applies last. Tinting the materials happens before all of that and
// survives the grade untouched.
//
// THE MATERIALS ARE SHARED, so a single assignment covers every instance of
// every building at once, and the fade is one lerp per material per frame
// rather than one per object.
import * as THREE from "three";

// Vercel black, and it is the same value the .blend uses for the HQ walls:
// _palette.py "Concrete Ink" is #232528. Written here as a number rather than
// imported because nothing else crosses from Python to JS in this project.
const INK = 0x232528;
// The glass goes darker still, or the windows read as pale holes punched in a
// black wall. Same relationship the palette already has between Concrete Ink
// and Glass Dark (#15181b).
const INK_GLASS = 0x15181b;
// The pavement turns too. It is the second biggest surface in the frame after
// the roofs, and left alone it was a pale grid holding the shape of a daylit
// city under a skyline that had already gone dark — the one thing that gave
// away that this is a tint and not a night.
//
// Two values, because the palette has two and the difference is what makes a
// street read as a street: "Sidewalk" (#98938a) and "Paving Pale" (#a8a294)
// are the light ones and stay the lighter of the pair here, "Paving" (#6e6a5e)
// stays under them. Both land above the asphalt, which is already near-black
// at #211e19 and is deliberately NOT in this list: if the kerbs sink to the
// road the block edges disappear and the city loses its grid.
const INK_PAVING = 0x35373b;
const INK_PAVING_DARK = 0x2a2c2f;

// The title is NOT here, and that is deliberate: BUENOS AIRES stays scarlet
// while everything under it goes dark. It is the one warm thing left in the
// frame and the whole point of the shot.
const FACADE = ["Concrete", "Brick", "Facade", "Roof", "Stadium", "Wall"];
const GLASS = ["Glass"];
// "Paving Pale" before "Paving": prefix matching would otherwise send the pale
// one to the dark value, since it starts with the shorter name.
const PAVING_PALE = ["Sidewalk", "Paving Pale"];
const PAVING = ["Paving"];

const SECONDS = 1.1;          // the fade, each way

const isOneOf = (name, list) => list.some((p) => name.startsWith(p));

export function makeDarkMode(city, { camera, renderer, sign = "Sign.001" }) {
  // The materials to turn, found once, with their original colour kept so the
  // way back is exact rather than a second guess at what they used to be.
  const targets = [];
  const seen = new Set();
  city.root.traverse((o) => {
    const m = o.material;
    if (!m || seen.has(m.uuid)) return;
    const name = m.name || "";
    // Ordered, and the order carries meaning: the pale pavings are tested
    // before the plain one so "Paving Pale" is not caught by the "Paving"
    // prefix and dragged to the darker value.
    let ink = null;
    if (isOneOf(name, PAVING_PALE)) ink = INK_PAVING;
    else if (isOneOf(name, PAVING)) ink = INK_PAVING_DARK;
    else if (isOneOf(name, GLASS)) ink = INK_GLASS;
    else if (isOneOf(name, FACADE)) ink = INK;
    if (ink === null) return;
    seen.add(m.uuid);
    targets.push({
      material: m,
      from: m.color.clone(),
      to: new THREE.Color(ink),
    });
  });

  // WHAT IS CLICKABLE. The disc is a handful of instances inside the big
  // InstancedMesh that city.js collapsed everything into, so there is no
  // object to hit-test: `byName` is the only way back from a Blender object
  // name to (mesh, instance index). Raycasting the whole city and then asking
  // whether the hit belongs to the sign is both simpler and cheaper than
  // rebuilding a separate mesh for it.
  const slots = city.byName?.get(sign) ?? [];
  if (!slots.length) {
    console.warn(`darkmode: ${sign} is not in the glb — the egg is off.`);
    return { update() {}, get on() { return false; } };
  }
  const wanted = new Map();     // mesh -> Set(instanceId)
  for (const s of slots) {
    let set = wanted.get(s.mesh);
    if (!set) wanted.set(s.mesh, (set = new Set()));
    set.add(s.index);
  }

  const ray = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  let on = false;
  let t = 0;                    // 0 is the day city, 1 is fully dark

  // A pointer that moved is a drag of OrbitControls, not a click on a sign.
  // Without this the egg fires at the end of every orbit that happens to
  // finish over the disc.
  let downAt = null;
  const el = renderer.domElement;
  el.addEventListener("pointerdown", (e) => { downAt = [e.clientX, e.clientY]; });
  el.addEventListener("pointerup", (e) => {
    if (!downAt) return;
    const moved = Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]);
    downAt = null;
    if (moved > 5) return;
    ndc.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    for (const hit of ray.intersectObjects([...wanted.keys()], false)) {
      if (wanted.get(hit.object)?.has(hit.instanceId)) { on = !on; break; }
    }
  });

  // The cursor is the only affordance there is: no label, no hint, nothing in
  // the UI. It is an easter egg, and a pointer over one disc in the skyline is
  // exactly as much of a clue as it should get.
  el.addEventListener("pointermove", (e) => {
    ndc.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    let over = false;
    for (const hit of ray.intersectObjects([...wanted.keys()], false)) {
      if (wanted.get(hit.object)?.has(hit.instanceId)) { over = true; break; }
    }
    el.style.cursor = over ? "pointer" : "";
  });

  return {
    get on() { return on; },
    // dt in seconds, from the same clock the loop already keeps. Driven by
    // time and not by frame count so the fade lasts as long on a slow machine
    // as on a fast one.
    update(dt) {
      const want = on ? 1 : 0;
      if (t === want) return;
      const step = dt / SECONDS;
      t = want > t ? Math.min(want, t + step) : Math.max(want, t - step);
      // smoothstep, so it eases out of the day city and settles into the dark
      // one instead of arriving at full speed
      const k = t * t * (3 - 2 * t);
      for (const g of targets) g.material.color.lerpColors(g.from, g.to, k);
    },
  };
}
