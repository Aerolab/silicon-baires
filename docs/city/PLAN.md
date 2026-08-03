# Build plan — "toy valley" city

Goal: build a city in the visual language of the *Silicon Valley* title sequence and
render a hero frame from a helicopter-style tilt-shift camera. The title was out of
scope at first and is now built, as buildings: see the fourth pass. Company signs are
built and carry **invented** companies, not real branding: see the fifth pass. The
city is Buenos Aires, and says so.

Read `STYLE-BIBLE.md` first. This document is about *how the work is organised*.

## The order the steps actually run in

The numbers no longer match the order, and following the numbers breaks the build.
The dependencies are real: step 05 has to know where the buildings are before it
plants anything, and step 08 deletes what step 05 puts inside the letters.

```
03_ground  →  04_buildings  →  10_signs  →  06_landmarks  →  06b_porteno
           →  05_life  →  08_title  →  11_animate  →  07_look final
```

with `02_kit` and `02b_porteno_kit` before all of it, once.

- **04 before 05**, and **06, 06b before 05**: they publish the footprints in
  `city_solids.json` that step 05 queries before placing a tree.
- **04 before 10**: step 04 chooses where the signs go and reserves the space;
  step 10 only builds them.
- **06b after 04 and 10**: a cupola takes a roof corner and needs to know what
  is already standing there.
- **05 before 08**: step 08 deletes what is inside the letters and only step 05
  puts it back.
- **11 after 08**: otherwise it animates cars step 08 is about to delete.

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
| **M2** ✅ | 81 blocks on a straight grid, street hierarchy, varied block sizes | `03_ground.py`. The curved arterial of the first two passes was removed: see the third pass below. |
| **M3** ✅ | Trees, street furniture, traffic, crowds | `05_life.py` — 1522 trees, 456 lights and signals, ~1000 vehicles, ~660 people, all instanced |
| **M4** ✅ | Stadium, curved building, parking structure, construction site with lattice cranes | `06_landmarks.py` |
| **M5** ✅ | Depth of field, grain, final render | `07_look.py`. The Defocus node does nothing on an orthographic camera, so the blur is driven off the Z pass into a variable Blur. |
| **M6** ✅ | Second pass against the reference | A side-by-side critique found six faults; all six fixed. See below. |
| **M7** ✅ | The title, as buildings | `08_title.py`. Out of the original scope, and the thing this build got wrong most often: three times, and every wrong version measured well against the reference. See the fourth pass. |
| **M8** ✅ | Nothing intersects a building, and it is checked | `_solids.py`, `99_check_overlap.py`, and the clearance queries in `05_life.py`. See the fifth pass. |
| **M9** ✅ | Buenos Aires reads | `02b_porteno_kit.py`, `06b_porteno.py` |
| **M10** ✅ | Sign placeholders with fake logos | `04_buildings.py` plans them, `10_signs.py` builds them, `renders/city_signs.json` is the manifest |
| **M11** ✅ | The city moves | `11_animate.py`, and `renders/city_move.mp4` |

## Second pass: what the comparison against the reference changed

Everything above was built, rendered and then compared frame to frame with the
reference. The critique found six faults, in order of impact:

1. **The shot was four times too wide.** Measured with a car as a ruler: the
   reference runs ~14 px per metre, so its frame spans ~140 m. Ours spanned
   590 m. Now 170 m. This alone explains most of the "not enough detail"
   complaints: the detail existed, it was just sub-pixel.
2. **The road was twice as bright as it should be, and the wrong hue.** 0.38
   luminance and cool grey against 0.18 and warm. The frame had 0.3 % of pixels
   below 0.25 where the reference has 15.7 %, so it had no dark values at all.
3. **Blocks were too big and setbacks far too generous.** 90 m blocks with
   6–12 m setbacks left every building floating in a lawn. Now 64 m blocks with
   1.5–4 m setbacks, and the sidewalk cut from 4.0 to 2.5 m so it stops framing
   every block in a thick white line.
4. **The symmetric circus was the single biggest giveaway.** It read as a formal
   corporate park rather than improvised tech sprawl. Replaced by a curved
   arterial — which then had to be dropped too, see the third pass below.
5. **Every roof used the same recipe.** Now roughly a fifth stay sparse, a tenth
   carry a single large feature, and the rest are dense.
6. **Facades had 0.2–0.5 m of relief where the reference has 0.5–3 m.** Added
   entrance canopies, deeper spandrel bands and projecting shade frames.

## Third pass: the grid goes straight

The curved arterial did not survive contact with the grid. A curve meeting an
orthogonal layout leaves ragged leftovers: a block that merely touches the
corridor loses its whole 64 m footprint to clear a 12 m verge, so the arterial
ended up flanked by two enormous empty roads. Removed.

The city is now strictly rectangular, 9 x 9 blocks, 714 m. Variety comes from
the grid itself rather than from curves:

- **Street hierarchy.** Local streets 12 m (two 3.5 m lanes), two avenues per
  axis at 22 m (four lanes).
- **Block sizes vary per row and column**, 52 to 76 m, so nothing reads as one
  repeated module.

Three placement bugs surfaced along the way, all the same mistake: **placing
things by cell index without checking the terrain actually there**. Towers and
landmarks stood on cells the arterial had eaten; the construction site shared a
lot with finished buildings. All three now look the lot up and skip loudly if
it is missing.

And one modelling bug that a dozen renders failed to catch: the crane mast was
rotated +90 deg about Y instead of -90, which sends +X to -Z. The mast ran
underground and only the jib was visible, floating. In an orthographic view a
horizontal jib looks like a diagonal boom, which is why it read as plausible.

## Fourth pass: the title

`scripts/city/08_title.py`, spiked first in `09_spike_title.py`.

**The letters are buildings.** The red in the reference is the roof of a
building whose plan is the letterform, standing on the ground: under the S of
SILICON there is a curved glass facade following the curve of the S. Each
letter here carries the city's own banded facade — a concrete spandrel at the
letter outline, a glass band inset 0.75 m above it, per floor, with a red roof
and a near-black parapet. Blender's font curves take an outline offset in
metres, which is what makes a facade band on a letter possible; scaling shrinks
toward a centre and cannot do it.

The first three attempts at this step got it wrong in the same way, and the
error survived two rounds of review because it measured well: flat red plates
lying on the roofs of a campus. It matched the reference's bounding box to
within 0.005 and looked like a caption.

**The baseline goes on the street grid.** The measurement that settles it:
in the window of frame beside SILICON the city's edges run at −27° and SILICON
runs at −25.6°; at the bottom of frame the city runs at −13° and VALLEY at
−13.5°. Both words are parallel to the streets. Their angles differ from each
other only because that render is perspective and parallel lines converge.

The letters themselves are ordinary letters: baseline along +Y, letter vertical
along −X, both city axes, and `plan()` is a plain rotation.

Two things were tried here and both were wrong, in opposite directions. The
first rotated the words 105° off the grid, on the strength of a real piece of
geometry — at 135° a shape in the ground plane projects with no shear at all —
and produced type dropped onto a city. The second kept the baseline on the grid
but pre-sheared the glyphs 45° in plan so their stems would come out vertical
on screen. That one is seductive because it looks right in the hero frame: it
buys upright type by making the buildings parallelograms, to flatter a single
camera. Both grid axes project to ±atan(sin e) = ±31.6°, so a letter really
does read as a 63° lozenge from here, and that is what a letter-shaped building
looks like from a fixed oblique view.

**Making room for it** is a superblock. The footprint is the word itself, H
across by W along, so it wants one block wide by two long.
`03_ground.py` merges cells (4,4) and (4,5) into one 58 × 140 m block and the
streets run around it, which is how the reference does it and how a real campus
does it. Merging four, which is where this started, left half the site as empty
paving. The internal streets take their
markings, lights, signals and traffic with them — `in_super()` in steps 03 and
05 is what keeps a bus from driving through a letter. Step 04 builds nothing on
those cells at all.

**As built**, so the numbers are checkable: BUENOS 103.3 m long, AIRES 76.1 m,
both at a 20 m cap and 0.93 letterspacing, 8 m of leading, roofs at 24.5 m.
Footprint x −26.0 to 22.0 and y −12.7 to 90.7, inside a block of x −31 to 27
and y −31 to 109. Roof box 0.554 × 0.615 of frame against the reference's
0.642 × 0.437, in a 170 m frame.

**Those four numbers are fractions of frame and must not be divided.** The
frame is 16:9, so a height fraction is worth 0.5625 of a width fraction in
metres. Read as ratios they say 0.90 against 1.47 and the title looks too tall;
converted to true aspect they say **1.60 against 2.61** and it is too narrow.
Both readings happen to point the camera the same way, which is why the error
survived, but the size of the gap was wrong by 60 %.

Solved from the geometry rather than by trying elevations: at azimuth 45 the
roof box aspect is 1.62 at elevation 38 — which agrees with the 1.60 measured
off the render, so the model of the projection is right — and it reaches the
reference's 2.61 at **elevation 22.5°**. That is the number for the camera
move. Lower the camera and the word spreads; there is no other lever, since
the footprint is fixed by the block.

`clear_ground()` in step 08 removes whatever the earlier steps left standing
inside the letters, since they run first and know nothing about where the words
land. It must never touch the KIT masters: they live near the origin, the title
lands on top of them, and deleting one takes every instance of that asset in
the city with it. That is why step 08 has to run after step 05, never twice in
a row over a title that has moved.

**For the camera move**, `96_check_title_move.py` renders the same frame from
several azimuths and elevations. Its earlier finding — that the lean unwinds to
nothing at azimuth 20 — belonged to the off-grid version and no longer holds:
the shear in `plan()` is tuned to one elevation and one azimuth, so moving the
camera puts the lean back. Re-run it before designing the move.

## Fifth pass: things that stand inside other things, and things that move

Four pieces of work, in the order they had to happen.

### Nothing may stand inside a building

The complaint was trees intersecting buildings. The count, once there was
something that could count, was **917 street trees inside an office** — 44 % of
the row — plus canopies through entrance canopies, solar arrays hanging over
parapets, roof units inside company signs, and buses through walls.

The reason it had gone unnoticed for the whole build is worth stating: by the
time step 05 runs, every building has been merged into one mesh, so there is no
per-building object left to ask. Steps 04, 06, 06b, 08 and 10 now publish the
rectangle each solid occupies into `renders/city_solids.json`, and step 05
queries it before placing anything.

- The clearance is **measured off the asset's own mesh**, not assumed. The trees
  range from 1.84 m to 4.38 m of plan radius, so one blanket number either lets
  Tree2 into the wall or refuses Tree3 for nothing. It is the largest
  `hypot(x, y)`, not the largest x or y, because everything is dropped in at a
  random rotation about Z.
- A tree that does not fit is **not refused, it is downgraded**: same species
  smaller, then a narrower species, then a shrub. Refusing outright left a bare
  pavement in front of every building, which is the opposite of the reference.
- The street tree row moved **onto the pavement**. It used to run 1.2 m inside
  the lot interior and buildings come within 0.75 m of that same line, so the
  row was inside the building by construction. The pedestrians moved with it,
  for the same reason.

`99_check_overlap.py` is the check, and it is deliberately three tests: the
footprint query (the same one step 05 makes, so it goes quiet if the mechanism
breaks), real triangle-against-triangle BVH overlap (the ground truth, which
does not care what anybody published), and the big merged meshes against each
other (a crane jib through a neighbour's facade belongs to nobody).

Two things it taught, both about the difference between contact and
intersection. Every tested object is **lifted 5 cm** first, because a roof unit
sits with its bottom face exactly on the roof plate and coplanar triangles
report as overlapping — without the lift the first run reported all 300-odd roof
units as errors. And modelling a loose object as a **disc of some radius** is
wrong in both directions: a traffic light is a 6 m cantilever arm over the road,
and a 6 m disc swallows the building behind it. It samples the vertices instead.

The count went 159 → 49 → 24 → 13 → 0 as each class was fixed. The one that
took longest was the title: sampling points and asking whether each is inside a
letter kept missing, at 8 directions and then at 32, because a canopy can
straddle the bar of an A with every sample falling in the daylight either side.
Step 08 now asks the triangles, the same way the check does.

One real bug in the query itself, and it is the classic one: the spatial hash
looked only in the cell containing the query point, forgetting the query has a
radius. A tree with an 8 m canopy standing 2 m outside a footprint one 24 m cell
over passed cheerfully.

### Buenos Aires

Chosen by what survives being twelve pixels tall from a high oblique view, which
rules out most of what makes the city recognisable at eye level — the tiled
pavements, the cafés, the kiosks, the painted party walls are all invisible from
here. What is left is silhouette and colour.

- **Jacarandás.** The strongest and the cheapest. One street tree in five is in
  flower. Six in twelve was tried first and half the city came out violet, which
  reads as a fantasy rather than as November.
- **Taxis**, black with a yellow roof, one car in five. From this camera a car is
  almost entirely its roof, so a livery whose distinguishing feature is the roof
  colour is a piece of luck.
- **Colectivos**, flat saturated two-tone, painted per line.
- **The Obelisco**, 67.5 m on a 6.8 m base — taller than every building here
  including the eighteen-floor tower, which is the whole reason it works from a
  camera that flattens everything else into roofs. It is the only vertical in
  frame.
- **Cúpulas** on the corners of corner buildings: the one eye-level detail that
  survives, because a dome is a silhouette rather than a texture.
- **Floralis Genérica**, 23 m, in the plaza on the other side.

Two things about placement. A 170 m frame holds the title's own block and very
little else, so at the hero framing the Obelisco reads as a shaft at the top of
frame and the Floralis at the left edge; both are composed for the camera *move*
rather than for the still. And "plaza" is not an empty lot — step 04 builds
offices on plazas — so the Obelisco went up inside somebody's fourth floor until
its cell was reserved.

### Signs, ready for logos

Three mountings, taken off the reference frames: **parapet letters** standing on
the roof edge and projecting past the facade (the Google one, and the type that
reads from furthest away because it breaks the roofline), a flat **roofmark**
panel lying on the deck, and a **mast disc** standing clear of everything.

Step 04 chooses and reserves, step 10 builds, `renders/city_signs.json` is the
manifest. Each sign is its own object with its own material slots, so real
artwork later is a material swap on a named object.

The letters went on the **+y wall**, which is the one this camera can see: the
hero camera is at azimuth 45 and looks at the +x and +y faces of everything, and
the first version put them on −y, where they were geometrically perfect and
permanently behind the building. Turned through π the word also runs along world
−x, which is screen-right from here, so it reads forwards.

### Movement

Two linear keyframes per object, no rig and no physics: at this scale what sells
movement is the whole frame drifting in several directions at once.

Every vehicle in a lane gets the **same speed**, which makes rear-end collisions
impossible by construction rather than by checking; speed varies between lanes
instead, and one lane in six is congested. Crossings are the part that has to be
solved, and it can be solved exactly, because two constant-velocity cars either
meet or they do not and it is decided before the first frame. Each conflict
holds one car back along its own lane; holding creates new conflicts, so it
iterates, and what six passes cannot settle is taken off the road rather than
left to drive through something. **773 conflicts, 809 cars held, 169 hidden, 0
left.** A car may not be held into a building or onto the title's block.

Nine hundred people walk, along the pavement axis step 05 recorded when it
placed them — a figure that picks its own heading walks into a wall half the
time. And the helicopter that has been sitting unused in the kit since step 02
finally crosses the frame.

## Sixth pass: the research that arrived late

The Buenos Aires work in the fifth pass was built from what I already knew,
because the research I had commissioned did not come back in time. It came back
afterwards, sourced, and it changed four things and confirmed the rest.

**The ochava, which should have been first.** Buenos Aires cuts every street
corner at 45° by code, so no block downtown has a 90° corner and every crossing
opens into an octagon. Four bevels per block. It costs almost nothing, it is
structural rather than decorative, and it does more for the read than any
monument: with square corners the grid is Manhattan. It is now in
`03_ground.py`, 4 m of chord.

Knock-on: the last tree of each pavement row used to sit out over the cut
corner with nothing under it, so the row is 12 m shorter than the block instead
of 8. `98_check_floating.py` is what would have caught that; it was cheaper to
predict it.

**The taxi livery is a law.** Ley 2.148: black below, yellow from the lower line
of the window *upward* — the whole greenhouse, not a yellow lid on a black
cabin. Rebuilt. This is the highest-value correction in the batch, because from
this camera a car is mostly its roof and the yellow is now most of the vehicle.
Taxis also came out of the parked-car pool: a third of every office car park was
yellow, which reads as a rank.

**Two monument numbers were wrong and are fixed** — see the note above on the
Obelisco's 63 m shaft and the Floralis's 32 m spread over a 44 m pool.

**The provincial shields.** Plaza de la República has the 24 provincial coats of
arms set into the paving in a ring around the Obelisco. They are 2 m discs,
14 px each, and a ring of them is more legible from above than any paving
texture, because a ring is a shape.

**The parapet letters are facade letters.** Zooming into the Google building
settles it: the roof-edge band runs above the word and the letters cast their
shadow down the wall. They were built standing on top of the parapet, which
reads against the sky instead of against pale concrete and throws away the
contrast that makes them legible. Now mounted on the wall, tops 0.7 m under the
roof edge.

That change is also what got the signs tested at all. They were a whole class of
object built in the fifth pass and never added to `99_check_overlap.py`, and the
moment they were, **22 of them were inside their own buildings**: 0.45 m of
projection is the real projection of a letter, but this city's facades carry a
shade frame that already stands 0.45 m proud. Then a further round, because a
lot carries up to four separate buildings and a long word runs off the end of
the wing it is mounted on and into the next one — which needs a second pass,
since when a sign is planned the buildings after it in the loop do not exist
yet. One word had to be dropped for want of room. **Anything built and not
added to the check is untested, and it will be wrong.**

**Confirmed, no change needed:** the jacarandá colour (blue-violet tending to
indigo — the common error is pinkish lilac, and ours was already right), the
colectivo two-tone-plus-stripe scheme and its dominant combinations, the
Floralis's mirror-polished steel, the four windows and single west door on the
Obelisco.

### What was declined, and why

Recording these so nobody re-derives them. Each one is real and would read.

- **Water tanks on every roof**, 30–60 per porteño block, 8 × 20 px each. This
  loses to the reference: the style bible has said since the second pass that
  its roofs are quiet with one memorable thing on them, and a mechanical carpet
  is the *Silicon Valley* look gone. Where Buenos Aires and the reference
  disagree, the reference wins — it is the language the whole piece is in.
- **86.6 m blocks.** The porteño block-to-street ratio is 6.3:1 against our
  5.3:1. But the title's superblock is sized to the word, so the block size is
  load-bearing for the thing the frame is built around.
- **Avenida 9 de Julio at 140 m** — 82 % of a 170 m frame. The buildable
  version is a ~52 m avenue with a raised Metrobús platform down the middle,
  which is what would make it read as *that* avenue rather than a wide one.
- **Medianeras** — the blank painted party walls — would be excellent and need
  neighbouring buildings of wildly different heights, which is a change to how
  step 04 picks floor counts rather than a thing to add.
- **Casa Rosada, Congreso, Puente de la Mujer.** All specced now if wanted. The
  Congreso's copper dome at 80 m against pale stone is the strongest of the
  three from this camera.

## Seventh pass: the avenue, the empty blocks, and which side of the road

Three corrections from the first proper look at the finished frame.

### Everything drove on the left

The lane table in step 05 is written once and used for both axes, and **the two
axes have opposite handedness about the offset sign**. Heading +x the driver's
right hand points at −y, so the +x traffic belongs on the negative side of the
street; heading +y it points at +x, so the +y traffic belongs on the positive
side. One table cannot be right for both. The Y streets came out correct by
luck and the X streets came out British.

What makes this worth recording is that it is invisible. Every individual
street is internally consistent — two lanes, opposite directions, cars evenly
spaced — and looks completely plausible. You can only see it by picking one car
and following it across an intersection, or by counting.

### The street tables were being read on the wrong axis

Found while fixing the above, and the same shape of bug. `streets_x` holds the
positions of the streets that run along **Y** — its entries are X coordinates —
and step 03's markings and step 05's traffic were both reading it for the
streets that run along X. Since both axes have the same total length and two
avenues each, everything landed inside a street gap and nothing looked wrong.
It is off by 5–6 m, and the avenues have their wide streets at different
indices per axis, so **the four-lane markings of an avenue were being painted
down a 12 m local street** while the real avenue was painted as a local. 46
vehicles were driving 1.75 m up on the pavement, which is under a lane width
and therefore under the threshold of looking wrong.

Both are now covered by `95_check_traffic.py`, which is the fifth standing
check: which side of the road, on the road at all, and buses only in the busway.

### The Avenida 9 de Julio

Built at 52 m, at street index 6 on the X axis, which is two blocks off centre
— the periphery, not the middle. The section is in §10c of the style bible and
the reasoning that matters is there too: the bus corridor got 16 m in the first
attempt and had to come down to 14, because what makes the avenue enormous is
the asphalt and not the thing running down the middle of it.

**The Obelisco has moved into it**, onto an island at the crossing with a wide
cross street, which is where the real one stands. This is the change that makes
it work: a monument in a plaza is a monument, and a monument in the middle of
eight lanes is Buenos Aires. It also solves a composition problem nobody had
named — the Obelisco, the Floralis and the title were inside three adjacent
blocks, so the middle of the frame had three things competing and the rest of
the city had none. The Floralis is now at (2, 7), the far corner. From the hero
azimuth the Obelisco falls on the left of the frame and the Floralis on the
right, at about the same height, which is the band a camera move sweeps.

Plaza de la República is 34 × 23 m against a real ~100. The first version was
60 × 23 and read as a platform rather than a place.

The avenue also carries two sign formats that exist nowhere else in the city —
the rooftop **billboard** and the **medianera** mural — because the real 9 de
Julio is an advertising corridor and that is most of what tells a viewer which
kind of street they are looking at. Medianeras had been declined in the sixth
pass on the grounds that they need neighbouring buildings of wildly different
heights; that was the *blank painted party wall as texture*, which is invisible
from here. The advertising mural is 20 m of flat colour and reads fine.

Which of the two dominates is decided by GCBA Ley 2936 and not by taste — see
§10b-1 of the style bible. The first version had fourteen boards to twelve
murals, which is a convincing picture of a different avenue: art. 12.16.2
prohibits rooftop structures on these stretches, so the mural is the format and
the board the exception, about three to one.

**And the rate was tuned four times before anyone checked whether the rate was
the limit.** `AV_BILLBOARD` went 0.85 → 0.22 → 0.60 → 0.18 with the count stuck
at one or two throughout. A rate that moves by a factor of five and changes
nothing is not what is limiting the count. What was limiting it: on the avenue
the sign goes on the wing that *looks at* the avenue, which on an L is often a
12 m arm — right for a mural, which needs a wall, and hopeless for a board,
which needs roof. A hoarding turned 45° in plan reaches 0.354 of its length in
both axes at once, so it wants about 15 m of roof in the short direction and
was refused on nearly every candidate. The board now goes on the widest wing
and the mural on the wall that faces the avenue; on a plain rectangle these are
the same wing and nothing changes.

The two banks of the avenue are not treated the same, and the reason is the
camera rather than the city. West of the avenue, the wall that looks at it is a
+x wall, which azimuth 45 can see. East of it, the wall that looks at the
avenue is a −x wall and is permanently the back of the building, so the mural
goes on the +y wall facing the cross street instead. This is the third time
this project has had to learn that a sign on a face the camera cannot see is
geometrically perfect and completely worthless.

### The empty block, which had a cause

`CAMPUS` in step 04 — the set of blocks left clear for the title — held four
cells, but step 03 only merges **two** of them into the superblock the title
stands on. Column 5 was being kept empty for a word that never reaches it. That
is the bare green block sitting immediately to the right of the title in every
frame since the title was built, and nothing was wrong with it except that the
set was a guess where the superblock is a fact.

The rest of the bare green was a quarter of the city being a lot with no
building on it at all — `parking` or `park` — which is a bigger lever than any
setback. Those weights are now 11 % and 8 % against 14 % and 12 %; the skipped
cell inside a block went from one in ten to one in twenty-five; and the `bar`
footprint went from 55 % of its lot's depth to 72 %, because at 55 % two bars
on a split block left a strip of lawn wider than the street beside it.

Only the thresholds moved, never the number of draws — the kinds of every lot
come out of one stream and adding or removing a draw reshuffles all of them.

### The mast had never been checked

Found by the overlap check on the last rebuild: one mast disc standing inside
the building next door. Masts had **no fit test at all**, on either pass, while
parapet words had two — and the mast is the format that reaches furthest, since
a 16 m disc stood on edge at 45° in plan swings 5.7 m out in x and y at once,
well past the parapet it stands behind.

This is the third time this project has found a whole class of object that was
built and never tested: the trees inside letters, then all 22 company signs the
moment SIGNS was added to the check, now the masts. The check finds them
because it tests *every loose object*, not the ones somebody remembered to
validate. That property is the reason it works and it is worth protecting.

### The plaza, and a check that could not have caught it

Two faults spotted by eye in the GUI, after all five checks had passed.

**A colectivo standing on a planting bed of the plaza.** Step 05 already
refuses to *place* a bus on the plaza, and that is not the same question: a bus
in the corridor covers 110–145 m in a ten-second shot and the island is 60 m
long, so one that starts a hundred metres south of it finishes on top of it.
The overlap check looks at frame 1, and at frame 1 the bus is on the road. So
this is a class of fault the checks are structurally blind to — **anything that
is only wrong once the animation has run**. Step 11 now hides the buses whose
ten seconds take them onto the island, the same policy it already uses for
crossing conflicts.

Worth noting what I got wrong just before this: when the beds first made the
overlap check fail, I moved them into the ground mesh. That was right for the
people standing on them and it *also* silenced the bus, which was a real fault.
Moving a thing out of the check because the check complains is only correct
when the complaint is the false one.

**The cross street ran straight through the island**, so traffic drove over the
plaza and through the monument. The plaza is now mid-block. The real Corrientes
is at that junction, but it was diverted in 1971 and bends around the Obelisco;
ours has no such bend, so mid-block is the closer reproduction of the effect.

That move broke the median trimming, which cut one end off a run — correct when
the plaza was at a crossing, wrong when it lands in the middle of a run with
planting owed on both sides. It cuts into two runs now.

**And the plaza came out deserted**, because it used to get its crowd for free
from the knot of people scattered at every crossing. An empty plaza around a
monument reads as a model rather than as a city, and it is the one place in
frame the eye is sent to. 34 people on the island, sampled inside the oval
rather than in its bounding box, and a few waiting on each Metrobús platform.

### Where the numbers landed

| | |
|---|---|
| City | 762 × 714 m, 80 lots |
| Avenue | 70 m at x = 120, 3 Metrobús stations, 141 median trees |
| Signs | 82 — 24 parapet, 32 roofmark, 10 mast, 12 medianera, 4 billboard |
| Trees / cars / people | 1599 / 1807 / 2324 |
| Crossing conflicts | 1160 found, 1113 held, 282 taken off the road, 0 left |

## Verification

`scripts/city/99_check_overlap.py` — three tests: published footprints, real
triangle overlap, and the merged meshes against each other. See the fifth pass
for what each is for and why contact is not intersection.

`scripts/city/98_check_floating.py` — two tests, because the two failure modes
differ. **A**: no geometry below ground (every asset is modelled on z = 0, so
anything below it is an orientation error). **B**: every instanced asset has a
surface under it, ray-cast against the site, buildings and landmarks.

Its first version tested every connected piece and reported 65,000 of 101,769
as floating. That premise was wrong: a facade band has nothing directly under
it by design. Merged building meshes are deliberately out of scope.

`scratchpad/plan_check.py` renders a top-down plan plus two context views. Run
it after any structural change — the close-ups and the colour metrics both
looked fine while the layout was destroyed, because neither measures geometry.

`scripts/city/97_check_title.py` compares the title in a render against the
same measurements taken off the reference frame: coverage, bounding box,
centre, face colour, ink inside its own box. It runs on the isolation pass
that step 08 renders, because the city contains other red things (a
construction frame, cars, a rooftop sign) and a colour threshold counts all of
them without saying so.

**Closed, and worth recording how.** Saturation sat at 0.20 against a stated
0.334 for a long time. It is 0.283 now and nobody graded anything: the
jacarandás, the taxis and the company signs put the chroma into the frame.
Colour here comes from what is in the shot.

**And the target was never one number.** Measured the same way across all four
reference frames, the fraction of pixels below 0.25 luminance runs 11.1, 16.0,
35.1, 35.2 %, and mean saturation runs 0.220 to 0.336. An earlier pass took
15.7 % off one frame and wrote it down as *the* reference; a later critique took
35.2 % off a different one and concluded we were 22 points too bright. Ours sits
inside the range on every measure except green coverage, which is 27.7 % against
21.9–26.2 %.

**That last one was chased and should not be chased again.** The ground is the
larger source: with the ordinary blocks in lawn it contributes 14.9 points of
green against 9.7 from every tree canopy in frame put together, so paving them
is the obvious lever. Measured, in both directions:

| | green | saturation |
|---|---|---|
| all lawn | 27.7 % | 0.284 |
| half paved | 19.5 % | 0.245 |
| all paved | 17.3 % | 0.237 |

Half paved lands closer to all paved than to all lawn, and that gives the game
away: the hero frame shows about six blocks out of eighty, so the number is
decided by which handful the camera happens to see rather than by the
proportion in the city. It is sampling noise at n = 6. Both changes also took
saturation down with them, because paving is grey — so the fix made two of the
three measures worse. Reverted. The 1.5-point overshoot is smaller than the
4.3-point spread the reference frames have between themselves, and the next
lever, if anyone wants one, is the tree count or the palette, not the lot
surface.

Also open, and probably not fixable here: the title face renders at
(0.809, 0.198, 0.102) against the reference's (0.928, 0.107, 0.085) — the
right hue, a little dark and twice as green. The sweep in the scratchpad shows
this is AgX Punchy, not a bad base colour: brightness and purity trade off
against each other, and every candidate lands on the same curve. The clean fix
is grading the title after the view transform, which the compositor cannot do
because it runs before it. Worth noting that the reference is not consistent
with itself either — its own wide shot is a much more orange red than the
close-up we measured, and ours sits between the two.

Still open, and not attempted: `98_check_floating.py` does not look inside the
merged building meshes, so a loose piece of one building is out of scope by
design. The company logos themselves are deliberately not drawn — the mountings
and the manifest exist, the artwork does not.

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

- **Deliverable: one hero still frame**, 2560 × 1440, Cycles, plus a ten-second
  moving preview at 24 fps. The camera itself does not move yet; the city does.
- **No real branding.** The sign mountings are built and carry invented companies
  (ZONDA, OMBÚ, PAMPA, CEIBO…), so the silhouette works and real artwork can be
  dropped onto a named object later. The **title is built**, though it was not in
  the original scope: BUENOS AIRES, as buildings shaped like the letters.
- **A fictional Buenos Aires in that style**, not a shot-for-shot copy of a
  specific frame and not a map of the real city: the Obelisco stands on a block
  of an invented grid, not on 9 de Julio.
- **6 × 6 blocks**, camera covering roughly a third — enough to fill the frame edge to
  edge with depth behind.
