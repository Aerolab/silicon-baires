# Build plan — "toy valley" city

Goal: build a city in the visual language of the *Silicon Valley* title sequence and
render a hero frame from a helicopter-style tilt-shift camera. **No company logos and
no title typography** — the subject is the city itself.

Read `STYLE-BIBLE.md` first. This document is about *how the work is organised*.

---

## 0. What we are making, and what we are not

**We are building a city.** The deliverable is `renders/city.blend`: an actual model
with actual buildings in it, and the frames rendered from it.

**We are not building a city generator.** No spec format, no layout engine, no
parameterised system that could produce a thousand different cities. That would make
the software the deliverable and the city a by-product, and it is far more work for a
scene this size.

The practical difference: when a building looks wrong, we fix that building. We do not
go tune a generator and regenerate everything.

The one thing that stays "systematic" is **instancing**. A tree is modelled once and
repeated four hundred times; same for cars, people, streetlights and roof units. That
is not architecture, it is the only way 24 GB of shared memory survives the scene, and
it is what anyone modelling this by hand would do too.

### How the work physically happens

Headless Blender has no interface to operate. Every action goes through Python, so the
work looks like a series of short scripts, each one a construction step:

```
scripts/city/00_ground.py       build the plate and the block slabs   -> save city.blend
scripts/city/01_roads.py        open city.blend, lay the roads        -> save city.blend
scripts/city/02_block_a.py      open city.blend, put up 3 buildings   -> save city.blend
...
```

Each script opens the saved file, adds its part, renders a preview, and saves. The
`.blend` grows and is the source of truth. The scripts are the record of how it got
built, not a program to be maintained.

**Every step ends by looking at the render.** Framing, exposure and material mistakes
raise no exception. This is the existing project rule and it matters more here than
anywhere else, because the scene is too big to hold in your head.

Checkpoints: keep `city_M1.blend`, `city_M3.blend` etc. so a bad turn can be backed out
without re-running everything.

## 1. Scale contract

Fixed before anything is modelled, because framing, lighting and every proportion
depend on it. 1 Blender unit = 1 metre.

| Quantity | Value |
|---|---|
| Floor height | 3.8 m |
| Low-rise campus | 2–5 floors (7.6–19 m) — the bulk of the city |
| Mid-rise slab | 8–12 floors (30–46 m) — a handful |
| Tower | 20–26 floors (76–99 m) — one or two |
| Block module | 90 × 90 m, with 45 × 90 and 180 × 90 variants |
| Street corridor | 22 m: 2 × 7 m carriageway + 2 × 4 m sidewalk |
| Kerb height | 0.15 m |
| Block slab lift | 0.3–1.2 m above road level, varies per block |
| Arterial curve radius | 60–150 m |
| Tree | 6–11 m tall, canopy radius 2.5–4 m |
| Car | 4.4 × 1.8 × 1.5 m; bus 11 m; truck 8 m |
| Person | 1.75 m |
| City extent | 6 × 6 blocks ≈ 660 × 660 m (5 × 5 is enough if we want to trim) |
| Hero frame coverage | ~350 × 200 m of that |

The camera ends up ~700 m out with a ~110 mm lens. Note that the city is lit by a
**sun + sky**, not by `blib.three_point()`: that rig is for objects on a table. A
sun/sky helper is the one addition `blib` needs.

## 2. The asset kit

Modelled once, reused everywhere. This is the only part built "in advance"; everything
else is built in place.

| Asset | Variants | Notes |
|---|---|---|
| Broadleaf tree | 3–4 | faceted lobes on a thin trunk, flat shaded |
| Conifer | 2 | simple cones |
| Hedge / shrub | 2 | |
| Car | 5–6 | sedan, van, pickup, SUV, plus a bus and a box truck |
| Person | 4–5 poses | boxy, ~1.75 m, flat colours, no faces |
| Streetlight, traffic light, sign | 1 each | pole + arm |
| Roof units | 6–8 | HVAC box, salmon pipe frame, solar array, stair bulkhead, dish, water tank |
| Bench, planter, bollard | 1 each | |

Colour variation comes from a handful of material variants per asset, not from
modelling each one separately.

## 3. Build order

Each layer says what goes in and how we know it is right. The check always ends in a
render we open and look at.

### L0 — Ground and terraces
Base plate, per-block raised slabs with visible edges, plaza and parking surfaces.
*Check:* top-down orthographic render — the block and street pattern must read as a
city plan.

### L1 — Roads — **SOLVED, see `scripts/city/01_spike_intersections.py`**

The spike built one crossroads three ways and rendered them side by side.

| | Result |
|---|---|
| **A** corridors + intersection patch | Works. 306 tris. But every crossing needs its own patch and its own corner pieces, and a curved arterial would need a bespoke patch per junction. |
| **B** boolean union of the ribbons | Failed on first contact. Coplanar flat slabs make the EXACT solver produce a solid with the road carved away entirely. Salvageable with effort; not worth it. |
| **E** negative space | Works, 210 tris, and no intersection is built at all. |

**Decision: E, negative space.** One asphalt sheet under the whole city; every block is
a slab raised on top of it. The road is simply where no slab covers, so crossings,
T-junctions and roundabouts cost nothing and can never gap or z-fight. Markings are
flat quads floating 2 cm over the sheet.

This also happens to be what the reference actually shows: the style bible notes that
every block sits on a raised slab with a visible vertical edge. We were going to build
those slabs regardless — this way they do the road's job too.

Verified on a curved arterial as well (`E2_curve`): a curve only bends the *block
outline*, which is a flat polygon, while the road underneath stays the same flat sheet.
That was the whole reason to prefer E over A, and it holds.

Open: markings on curves are annulus sectors, and short dashes currently carry the same
48 segments as long bands. Cheap to fix, wasteful if left.

*Check:* top-down render — no gaps, no z-fighting, markings continuous through curves.

### L2 — Building massing
Footprints (rectangles and L / U / Z / T combinations) extruded to whole floor counts,
placed lot by lot. Grey-box only, no detail yet.
*Check:* hero-camera render in grey — the skyline and the block rhythm have to work
before any detail goes on.

### L3 — Facades
Horizontal banding (concrete spandrel + recessed glass with mullions), louvres, punched
windows, curtain wall. Built once per pattern with an array, then applied per building
with the right floor count.
*Check:* close-up of four buildings against `refs/crops/i_oracle_facade.png`.

### L4 — Roofscape
Parapet ring plus roof units on every single building. From this camera the roof is
most of what you see, and an empty roof is the fastest way to look unfinished.
*Check:* close-up of four roofs at 1:1 pixel scale.

### L5 — Nature
Street tree rows following the road curves, irregular clumps in the parks, hedges,
grass, a pond, park paths. Both patterns are needed; only one of them looks wrong.
*Check:* a park block render — the trees must read as toys and must not visibly repeat.

### L6 — Street furniture
Streetlights, traffic lights, signs, bus stops, bollards, benches, fences.
*Check:* intersection close-up against `refs/crops/l_topleft_block.png`.

### L7 — Population
Cars along the road curves with irregular gaps, parked cars in lots, people on
sidewalks, at crossings, on roofs. Clustered, never evenly spaced.
*Check:* close-up — the groups have to look intentional.

### L8 — Landmarks
The pieces that break the grid and anchor the frame: the curved "blob" building, a
stadium, a glazed building with a letterform footprint, a construction site with
lattice cranes and excavators, a glass tower, an open-deck parking structure.
*Check:* each one alone, then in context.

### L9 — Light and world
Sun and sky, soft shadows, bright ambient. Nothing in frame clips to black.
*Check:* sample the darkest pixel of a render — the asphalt must stay above zero.

### L10 — Camera and look
Shifted long lens for parallel verticals, depth of field tuned for the miniature read,
view transform chosen by comparison, film grain, subtle vignette.
*Check:* side by side with `refs/frames/3.png` at the same crop.

### L11 — Output
Final Cycles GPU render at 2560 × 1440. A slow camera move is possible later without
rebuilding anything.

## 4. Milestones

| # | Deliverable | Definition of done |
|---|---|---|
| **M0** ✅ | Palette, asset kit (39 assets), sun/sky and hero camera | `00_setup.py`, `02_kit.py`. Camera had to become orthographic: a 150 mm lens at 1450 m still leaned verticals 6.5°, measured. |
| **M1** ✅ | Site, buildings, facades, roofs | `03_ground.py`, `04_buildings.py` |
| **M2** ✅ | 40 grid blocks + a circus of 8 sector blocks and 4 curved islands | `03_ground.py` |
| **M3** ✅ | Trees, street furniture, traffic, crowds | `05_life.py` — 1522 trees, 456 lights and signals, ~1000 vehicles, ~660 people, all instanced |
| **M4** ✅ | Stadium, curved building, parking structure, construction site with lattice cranes | `06_landmarks.py` |
| **M5** ✅ | Depth of field, grain, final render | `07_look.py`. The Defocus node does nothing on an orthographic camera, so the blur is driven off the Z pass into a variable Blur. |
| **M6** | *(optional)* camera move, or `.glb` export for the browser | — |

M1 carries the whole risk. If the block does not look right, nothing after it will, and
scaling a wrong look just makes it wrong thirty-six times over.

## 5. What can be built in parallel

A `.blend` is a single binary file, so two things cannot edit the city at once. What
*can* run in parallel is the **asset kit**: trees, vehicles, people and roof units are
each built in their own small `.blend` and appended into the city when ready. Landmarks
work the same way — each is modelled standalone and brought in.

The city file itself is edited one step at a time, in order.

## 6. Risks, ranked

1. **Road intersections.** Highest chance of eating days. Spike it at M0 on a single
   crossroads, three approaches, before committing to one.
2. **Memory and render time.** 24 GB shared with the GPU. Instancing from the first
   asset, a triangle-count report (unique vs instanced) on every save, and a
   resolution/sample ladder. If Cycles will not hold the full city, EEVEE can carry the
   wide frame — the look is flat-lit enough to survive it.
3. **Repetition.** A city assembled from a kit reads as assembled from a kit. Counter
   it deliberately: vary heights, colour families and footprint types per block, rotate
   a few buildings off-axis, and hand-place the exceptions.
4. **Depth of field.** Easy to overdo into a blurry mess. Tune it last, on the final
   camera, against the reference crop.
5. **Losing work in a big file.** Checkpoint `.blend`s at each milestone.

## 7. Assumptions (say if any is wrong)

- **Deliverable: one hero still frame**, 2560 × 1440, Cycles. Built so an animated
  camera move is a later addition, not a rebuild.
- **No logos, no title text.** Where the original has a logo, we put an abstract
  signage volume so the silhouette still works.
- **A fictional city in that style**, not a shot-for-shot copy of a specific frame.
- **6 × 6 blocks**, camera covering roughly a third — enough to fill the frame edge to
  edge with depth behind.
