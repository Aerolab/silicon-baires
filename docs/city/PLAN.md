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
inside the range on every measure except green coverage, which is 28.5 % against
21.9–26.2 % — a little heavy, and the trees are why.

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
