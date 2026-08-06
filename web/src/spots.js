// Numbered roofs, so a person can point at one.
//
// `?spots=1` draws a numbered pin over every roof big enough to carry a sign,
// green where there is one already and white where there is not. It is a
// working tool and not part of the piece: nothing here runs unless the flag is
// on, and the numbers come from the export (city_spots.json), not from
// anything the page invents.
//
// THE NUMBERS ARE STABLE ACROSS REBUILDS. 20_export_web assigns them by sorted
// position, so "put the logo on 47" still means the same roof tomorrow.
//
// Drawn as DOM, not as sprites: a few hundred divs cost nothing next to the
// city, they stay crisp at any zoom, and text in WebGL would mean a font atlas
// for a debug overlay.
import * as THREE from "three";

const MAX_ON_SCREEN = 90;     // the nearest N, so a wide shot is not a wall of
                              // numbers with nothing readable in it

export async function makeSpots(camera) {
  let data;
  try {
    data = await fetch("./city_spots.json", { cache: "no-store" })
      .then((r) => r.json());
  } catch {
    return { update() {}, count: 0 };
  }

  const host = document.createElement("div");
  host.style.cssText =
    "position:fixed;inset:0;pointer-events:none;z-index:5;" +
    "font:600 12px/1 ui-sans-serif,system-ui,sans-serif";
  document.body.appendChild(host);

  const spots = data.spots.map(([id, x, y, z, w, d, rot, taken]) => {
    const el = document.createElement("div");
    el.textContent = taken ? `${id} · ${taken}` : String(id);
    el.style.cssText =
      "position:absolute;transform:translate(-50%,-50%);white-space:nowrap;" +
      "padding:2px 6px;border-radius:9px;letter-spacing:.02em;" +
      (taken
        ? "background:rgba(24,110,60,.92);color:#eafff2;"
        : "background:rgba(255,255,255,.94);color:#101010;") +
      "box-shadow:0 1px 3px rgba(0,0,0,.45)";
    host.appendChild(el);
    // z is the DECK, not the parapet: see roof_spots() in the export. The pin
    // sits a little over it so it clears whatever is standing on the roof.
    return { el, pos: new THREE.Vector3(x, y, z + 4), taken };
  });

  const v = new THREE.Vector3();
  return {
    count: spots.length,
    update() {
      const near = [];
      for (const s of spots) {
        v.copy(s.pos).project(camera);
        // behind the camera, or off the frame: not drawn at all
        if (v.z > 1 || v.x < -1.05 || v.x > 1.05 || v.y < -1.05 || v.y > 1.05) {
          s.el.style.display = "none";
          continue;
        }
        near.push([v.z, s, (v.x + 1) / 2 * innerWidth,
                   (1 - v.y) / 2 * innerHeight]);
      }
      near.sort((a, b) => a[0] - b[0]);
      near.forEach(([, s, px, py], i) => {
        if (i >= MAX_ON_SCREEN) { s.el.style.display = "none"; return; }
        s.el.style.display = "block";
        s.el.style.left = `${px.toFixed(0)}px`;
        s.el.style.top = `${py.toFixed(0)}px`;
      });
    },
  };
}
