// The glb is Draco-compressed (3.3 MB instead of 15), so the page needs the
// decoder. It ships inside the three package; copying it into public/ keeps the
// page self-contained and off any CDN, and re-runs on every dev/build so a
// three upgrade cannot leave a stale decoder behind.
import { cp, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const from = resolve(here, "../node_modules/three/examples/jsm/libs/draco/gltf");
const to = resolve(here, "../public/draco");

await rm(to, { recursive: true, force: true });
await cp(from, to, { recursive: true });
console.log("draco decoder -> public/draco");
