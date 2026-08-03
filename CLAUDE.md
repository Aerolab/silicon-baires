# blender-mcp

Generative 3D with Blender, driven by code, headless.

## Start here

```bash
./bl scripts/verify_setup.py     # 9 checks, ~3s. If it says 9/9, the environment is ready.
./bl scripts/my_script.py        # run any script inside Blender
./bl                             # open the GUI with the newest .blend
```

The `bl` wrapper finds the Blender binary on its own (or honours `BLENDER_BIN`).

## The rule that is not negotiable

**A render is not validated until it has been looked at.** After rendering, open the
PNG with the Read tool. Framing, exposure and material mistakes raise no exception:
they come out ugly and the script exits 0.

`verify_setup.py` applies the same idea automatically: it measures render luminance to
catch the black or blown-out frame, which is the most common failure mode when working
without a viewport.

## How to build

Never position cameras or compute light power by hand. `blib` derives them from the
real geometry of the scene, so the same code works on a 2cm object and a 100m one.

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bpy, blib

blib.reset()
bpy.ops.mesh.primitive_monkey_add()
blib.assign(bpy.context.object, blib.pbr("Mat", (0.9, 0.3, 0.2), roughness=0.3))
blib.three_point()
blib.camera(azimuth=45, elevation=20)
blib.report()                                   # what is actually in the scene
blib.render("renders/out.png", "EEVEE")         # and then: look at the PNG
```

Iterate in EEVEE (0.65s), move to Cycles only for the final image.

## The city

The main piece of work in this repo is a city in the style of the *Silicon Valley*
title sequence: `renders/city.blend`, built by the numbered scripts in
`scripts/city/`, in order.

**The numbers are not the order.** Following them breaks the build, because the
dependencies are real. Each script opens `city.blend`, adds its layer and saves:

```bash
./bl scripts/city/03_ground.py       # the site
./bl scripts/city/04_buildings.py    # publishes footprints AND plans the signs
./bl scripts/city/10_signs.py        # builds what 04 planned
./bl scripts/city/06_landmarks.py
./bl scripts/city/06b_porteno.py     # Obelisco, Floralis
./bl scripts/city/05_life.py         # needs everything above: it queries footprints
./bl scripts/city/08_title.py        # BUENOS AIRES, built as buildings. After 05, always
./bl scripts/city/11_animate.py      # after 08, or it animates cars 08 deletes
./bl scripts/city/12_camera.py       # the camera move. After 11: it leaves the
                                     # scene on the last frame, and 11 resets it to 1
./bl scripts/city/07_look.py final   # the final Cycles frame, shot on frame 240
```

`02_kit.py` and `02b_porteno_kit.py` run once, before all of it. Do not re-run
`02_kit.py` casually: it makes new mesh datablocks and every instance in the
city goes on pointing at the old ones.

Five standing checks, because none of these failures raise an exception:

```bash
./bl scripts/city/99_check_overlap.py           # nothing is standing inside a building
./bl scripts/city/98_check_floating.py          # nothing buried, nothing hovering
./bl scripts/city/95_check_traffic.py           # right-hand traffic, and on the road
./bl scripts/city/96_check_title_move.py        # the title from other angles
python3 scripts/city/97_check_title.py renders/city_08_title_only.png
```

`99_check_overlap.py` is the one to run after touching anything that places
objects. A tree inside an office wall is invisible from the hero camera — it
hides behind the very wall it is inside — and 917 of them survived the whole
build until there was something that could count.

`95_check_traffic.py` exists for the same reason one axis of this city drove on
the left for weeks: every street looked completely plausible on its own, and the
only way to see it was to follow one car or to count.

Read `docs/city/STYLE-BIBLE.md` before touching the look, and `docs/city/PLAN.md`
for how the build is organised and which decisions were already settled (roads as
negative space, orthographic camera, depth of field from the Z pass, the title
built as buildings on the street grid). Both documents record the attempts that
were wrong as well as the one that stuck — the title was got wrong three times,
and every wrong version measured well.

Three files travel with the `.blend` and are read by later steps, so do not
delete them: `renders/city_solids.json`, the rectangle every solid thing
occupies; `renders/city_signs.json`, the manifest of company signs (name,
position, orientation, face size) for dropping real artwork on later; and
`renders/city_lots.json`, the street and block tables, which also carry the
section of the Avenida 9 de Julio under `avenue9j` — steps 05 and 06b build
from that key rather than from a second copy of the numbers.

**The street tables are per axis and they are not interchangeable.** A street
running along X sits at a Y coordinate, so it comes out of the Y table. Reading
the wrong one is off by 5–6 m, which is less than a lane width, so every street
still reads as a street while the cars quietly drive along the pavement.

The `.blend` is the deliverable, not the scripts. There is no city generator and
there should not be one: when a building looks wrong, fix that building.

## Layout

```
bl                        wrapper: ./bl <script.py>
blib/                     project library (framing, lights, materials, render, GN, export)
scripts/                  Blender scripts, one per task
scripts/verify_setup.py   environment self-check
scripts/_introspect/      probes that interrogate the API; the probe*.json are the evidence
renders/                  outputs (gitignored: regenerated by running the scripts)
                          including city.blend, city_solids.json, city_signs.json
.claude/skills/blender/   project skill: verified 5.2 API, look dev, recipes
.agents/skills/           installed three.js skills (symlinked from .claude/skills)
skills-lock.json          which third-party skills are installed, and at which version
addon.py                  Blender MCP addon, optional
```

## Available skills

- **`blender`** (ours) — read it before writing any Blender code. Documents `blib` and
  the 5.x API changes that break code written from memory: `BLENDER_EEVEE_NEXT` does not
  exist, `action.fcurves` is gone, geometry nodes modifier inputs are set through
  `mod.properties.inputs[id]["value"]`, and video needs `media_type="VIDEO"` before
  `FFMPEG`. All verified against the installed binary, not taken from documentation.
- **`threejs-fundamentals` / `threejs-loaders` / `threejs-lighting` / `threejs-materials`**
  (from `CloudAI-X/threejs-skills`) — for when the output goes to the browser.
  `threejs-loaders` covers `GLTFLoader` and Draco, which is what `blib.export_glb()`
  produces by default.

## Environment

- Blender 5.2.0 LTS, Python 3.13, macOS
- Cycles on GPU via Metal (Apple M4 Pro), configured automatically by `blib.use_gpu()`
- Measured timings (960×540): EEVEE 64spp = 0.65s, Cycles GPU 512spp = 3.2s,
  Cycles CPU 128spp = 5.3s. The first Cycles render of each process pays ~10s of Metal
  kernel compilation, so batch final renders into a single script.

## The MCP, optional

The `blender` server (`uvx blender-mcp`) is registered for live sessions, editing a
scene while a human watches it in the GUI. It requires installing `addon.py` into
Blender (`Edit > Preferences > Add-ons > Install from Disk`) and clicking
"Connect to Claude" in the side panel (N key).

Not needed for normal work: the CLI gives the full API and everything stays versioned.
