// The city: load the glb, collapse it into instanced meshes, and move the
// 1784 things that move.
//
// WHY THE COLLAPSE. The glb has 8131 nodes over 172 meshes, because that is
// what the .blend has: every car in the city is a separate object sharing one
// mesh datablock, which is the cheapest instancing Blender offers. Added to a
// three.js scene as-is that is 8131 draw calls and the page runs at about 12
// fps on an M4. Grouped by (geometry, material) it is a couple of hundred
// InstancedMesh, and the same frame costs nothing.
//
// NOTHING HERE KNOWS WHAT A CITY IS. It groups by geometry and moves whatever
// city_motion.json names. Rebuild the .blend differently and this file does
// not change.
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";

const _m = new THREE.Matrix4();
const _p = new THREE.Vector3();
const _q = new THREE.Quaternion();
const _s = new THREE.Vector3();
const ONE = new THREE.Vector3(1, 1, 1);

export async function loadCity(v = "", onProgress = null) {
  const draco = new DRACOLoader().setDecoderPath("./draco/");
  const loader = new GLTFLoader().setDRACOLoader(draco);

  const [gltf, motion] = await Promise.all([
    // El glb son 5.8 de los 8.5 MB, así que su progreso ES el progreso. Con
    // gzip por el medio `total` llega en 0 a veces: entonces se informa lo
    // descargado y la barra se mueve igual, contra un tamaño estimado.
    loader.loadAsync(`./city.glb${v}`, (e) => {
      if (!onProgress) return;
      const total = e.total || 6.2e6;
      onProgress(Math.min(0.98, e.loaded / total));
    }),
    fetch(`./city_motion.json${v}`).then((r) => r.json()),
  ]);
  draco.dispose();

  const root = new THREE.Group();
  // Blender is Z-up and the export keeps it that way, so the whole app is
  // Z-up: every number in city_shot.json is then the same number the .blend
  // has, and there is no axis conversion to get backwards.
  const groups = new Map();      // "geomId|matId" -> { geometry, material, nodes }
  const byName = new Map();      // object name -> [{ mesh, index, scale }]

  // THE NAME OF THE OBJECT, NOT OF THE PRIMITIVE, AND NOT GUESSED.
  //
  // A Blender object with four material slots arrives as a Group for the node
  // and four Mesh children for the primitives, and the children are named
  // after the MESH, not the node: object "CarBlue.i.003" becomes a Group
  // "CarBluei003" (three strips the dots) holding "CarBlue_1".."CarBlue_4".
  // So neither the child's name nor a prefix test recovers the address, and
  // both fail silently — the first version of this matched zero of 1784 cars
  // and the city just sat there looking correct.
  //
  // GLTFLoader keeps the mapping it used, so ask it: climb to the nearest
  // ancestor that came from a glTF node, and read that node's name straight
  // out of the file. No sanitising, no prefix rules, nothing to drift.
  const assoc = gltf.parser.associations;
  const nodeDefs = gltf.parser.json.nodes || [];
  const objectName = (o) => {
    for (let n = o; n; n = n.parent) {
      const a = assoc.get(n);
      if (a && a.nodes !== undefined) return nodeDefs[a.nodes]?.name ?? null;
    }
    return null;
  };

  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse((o) => {
    if (!o.isMesh) return;
    const key = `${o.geometry.uuid}|${o.material.uuid}`;
    let g = groups.get(key);
    if (!g) groups.set(key, (g = { geometry: o.geometry, material: o.material, nodes: [] }));
    g.nodes.push({ name: objectName(o), matrix: o.matrixWorld.clone() });
  });

  let instances = 0;
  for (const { geometry, material, nodes } of groups.values()) {
    // Whether a material is single- or double-sided is decided in the export
    // step, per material, by looking at whether its meshes are actually closed
    // (see 20_export_web.py). Nothing to override here: doing it in the
    // browser meant either paying for back faces nobody sees — 12 fps against
    // 36 — or culling the Floralis, whose petals are open shells and lose
    // their inside surface.
    const mesh = new THREE.InstancedMesh(geometry, material, nodes.length);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.frustumCulled = false;    // one instanced mesh spans the whole city
    nodes.forEach((n, i) => {
      mesh.setMatrixAt(i, n.matrix);
      if (!n.name) return;
      const slot = { mesh, index: i };
      const seen = byName.get(n.name);
      if (seen) seen.push(slot); else byName.set(n.name, [slot]);
    });
    mesh.instanceMatrix.needsUpdate = true;
    root.add(mesh);
    instances += nodes.length;
  }

  // Resolve the motion against what actually came out of the glb. The export
  // step already checked the names, so anything missing here means the two
  // files were generated from different runs - say so instead of quietly
  // parking a third of the traffic.
  const movers = [];
  const orphans = [];
  for (const e of motion) {
    const slots = byName.get(e.n);
    if (!slots) { orphans.push(e.n); continue; }
    movers.push({
      slots,
      scale: e.s ? new THREE.Vector3().fromArray(e.s) : ONE,
      frames: e.k.map((k) => k[0]),
      pos: e.k.map((k) => new THREE.Vector3().fromArray(k[1])),
      rot: e.k.map((k) => new THREE.Quaternion().fromArray(k[2])),
      seg: 0,                      // where we were last frame; see setFrame
    });
  }
  if (orphans.length) {
    // Both sides of the mismatch, because "not found" on its own sent a
    // debugging session looking in the wrong file: the names are there, they
    // are spelled differently.
    console.warn(`${orphans.length} moving objects are not in city.glb.\n` +
      `  motion says: ${orphans.slice(0, 3).join(", ")}\n` +
      `  the glb has: ${[...byName.keys()].slice(0, 3).join(", ")}\n` +
      `  Re-run ./bl scripts/city/20_export_web.py — the two files disagree.`);
  }

  const bbox = new THREE.Box3().setFromObject(gltf.scene);

  return {
    root, movers, bbox, gltfScene: gltf.scene,
    stats: { nodes: instances, drawCalls: groups.size, movers: movers.length },

    // Step 11 gives almost everything exactly two linear keyframes, so for
    // almost everything this lerp is not an approximation of the animation: it
    // IS the animation. The export checks that claim against Blender at three
    // frames it did not sample.
    setFrame(frame) {
      const touched = new Set();
      for (const m of movers) {
        const f = m.frames;
        // Walk from wherever we were rather than searching: playback moves one
        // frame at a time, and everything except the rotor has two keys.
        let i = m.seg;
        while (i > 0 && frame < f[i]) i--;
        while (i < f.length - 2 && frame >= f[i + 1]) i++;
        m.seg = i;

        const t = THREE.MathUtils.clamp((frame - f[i]) / (f[i + 1] - f[i]), 0, 1);
        _p.lerpVectors(m.pos[i], m.pos[i + 1], t);
        _q.slerpQuaternions(m.rot[i], m.rot[i + 1], t);
        for (const s of m.slots) {
          s.mesh.setMatrixAt(s.index, _m.compose(_p, _q, m.scale));
          touched.add(s.mesh);
        }
      }
      for (const mesh of touched) mesh.instanceMatrix.needsUpdate = true;
    },
  };
}
