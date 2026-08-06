# The city, as a dependency graph

Read this before changing anything, and before adding a step.

The numbered scripts are not a pipeline you can run in order. Each one opens
`renders/city.blend`, adds its own layer and saves, and the dependencies between
them are real: a step can silently produce a wrong city if what it reads is not
there yet. **None of these failures raise an exception.** That is the whole
reason this file exists.

Everything below is declared in the code, not just described here. Each step
opens with `open_city(needs_collections=..., needs_files=...)`, so a missing
prerequisite now stops the run with the command that fixes it instead of
surfacing thirty lines later as a `KeyError`, or not surfacing at all.

## The order

```
_stage.py                  # ONCE, and it DESTROYS the city. Not a step.
  02_kit.py                # the assets everything else instances
  02b_porteno_kit.py       # taxis, colectivos, jacarandas. Same collection
    03_ground.py           # the site.  publishes city_lots.json
      04_buildings.py      # publishes footprints AND plans the signs
        10_signs.py        # builds what 04 planned
      06_landmarks.py      # stadium, campus
      06b_porteno.py       # Obelisco, Floralis
        05_life.py         # needs all of the above: it queries the footprints
          08_title.py      # BUENOS AIRES, built as buildings
            11_animate.py  # traffic and walkers
              12_camera.py # the move. Owns the camera in the .blend
                07_look.py # the final frame
                  20_export_web.py  # the same city, published to web/
```

Indentation is dependency, not preference. Siblings at the same level are
independent of each other and can run in any order.

## What each step reads, owns and publishes

A step **owns** a collection when it calls `purge()` on it: the collection is
emptied and rebuilt on every run, so anything else that writes into it is lost.

| step | reads | owns (purged and rebuilt) | publishes |
|---|---|---|---|
| `02_kit` | — | `KIT` (purged by hand, see below) | — |
| `02b_porteno_kit` | `KIT` | adds to `KIT` | — |
| `03_ground` | `KIT` | `SITE` | `city_lots.json` |
| `04_buildings` | `KIT`, `SITE`, lots | `BUILDINGS`, `ROOFPROPS`, `CAMPUSROOF` | solids `buildings`, `city_signs.json` |
| `06_landmarks` | `KIT`, `SITE`, lots | `LANDMARKS`, `LANDMARK_PROPS` | solids `landmarks` |
| `06b_porteno` | `KIT`, `SITE`, lots | `PORTENO` | solids `porteno` |
| `10_signs` | `BUILDINGS`, signs manifest | `SIGNS` | solids `signs` |
| `05_life` | `KIT`, `SITE`, `BUILDINGS`, lots, **solids**, **the site mesh itself** | `NATURE`, `FURNITURE`, `TRAFFIC`, `PEOPLE`, `ROOFPEOPLE` | — |
| `08_title` | `BUILDINGS`, `NATURE`, lots | `TITLE` | — (it DELETES from other collections) |
| `11_animate` | `TRAFFIC`, `TITLE`, lots, solids | `AIR` | — (animates `TRAFFIC`, `PEOPLE`) |
| `12_camera` | `TITLE`, `TRAFFIC` | — | the camera animation |
| `07_look` | `BUILDINGS`, `TITLE` | — | the compositor (the grade is `_common`'s) |
| `20_export_web` | everything, plus `07_look`'s numbers | — (writes outside the .blend) | `web/public/`: the glb, the motion, the shot, the sky |

## The south rim

`03_ground.build_rim` bolts one extra row of blocks onto the south edge,
outside the grid, because the opening frame of the move runs off the end of the
map: the camera starts at (163, -214) and its top-left corner reaches y = -440,
where the built area stops at -357. 83 m of bare sheet, 7 per cent of the
opening cut.

**It is not a tenth row and it must not become one.** `axis_layout` centres the
grid on the origin, so `EXTENT = 10` shifts every coordinate in the city by half
a block — the Obelisco, the title, the landmarks, the approved hero framing —
and reshuffles the stream that decides what kind every lot is on top of that.

The rim lots are keyed **j = -1** and appended to `city_lots.json` after the
superblock. Every step that walks the lots with a shared RNG skips them in its
main pass and builds them at the end from `rng(RIM_SEED)`, which is the device
`avenue_rng` and `sign_rng` already use:

| step | where the rim is built |
|---|---|
| `03_ground` | `build_rim()`, after `build_blocks`. Also carries the 9 de Julio's section — busway and medians — south over the rim, since the avenue is inside the exposed wedge |
| `04_buildings` | skipped in the main loop, built after `build_towers`. `r` is what `build_campus` and `build_towers` draw from next |
| `05_life` | `lots` is filtered before the four shared passes and the rim is planted afterwards |

Verified by diffing, not assumed: the first 80 lots of `city_lots.json` and the
first 381 `buildings` footprints of `city_solids.json` are byte-identical to
what they were before the rim existed.

The rim medians get no trees. `_common.median_runs` is what step 05 plants from,
so extending it would have handed 05 a longer list and moved every tree in the
city. At that distance, out of focus and behind the last row of roofs, it is not
a difference anyone can see.

## The six couplings that have actually broken

Each of these cost a rebuild at least once, and each is now enforced in one
place instead of being remembered in two.

**1. How long the shot is.** `_common.FPS / FRAMES / MOVE`. Step 12 lengthened
the shot and step 11 went on animating the old length, so every car in the city
stopped dead halfway through and stood there. The standing checks read frame 1,
where it has not happened yet. Change it there, then re-run **11 and then 12**.

**2. How wide the hero frame is.** `_common.HERO_WIDTH`. It was written as
`170.0` in three files: `07_look.CAM_WIDTH`, `12_camera.SCALE1` and a literal in
`11_animate`. The move has to LAND on the framing the still is rendered at, so
they are the same number by definition.

**2b. Where the camera goes.** `_common.SHOT_*` and `shot_at / shot_cover`. The
move used to be private to step 12, which was right while 12 was the only step
that cared. Step 04 cares now: it plans a company sign for every roof the shot
passes over, so it has to trace the same path 12 flies. Two copies of a camera
move fails more quietly than any of the others here — the signs would simply be
planned along a route the camera does not take, and every frame still renders.

Change the path or `SHOT_ZOOM` and re-run **04, 10, then 12**: 04 decides which
roofs are in the shot, 10 builds what it decided, 12 flies it.

**3. Where the medians run.** `_common.median_runs`. Step 03 builds the medians
and step 05 plants them, and they disagreed: 03 dropped both stubs of the plaza
block for being 9 m long, 05 planted from its own arithmetic anyway, and four
trees ended up on the bare asphalt of the 9 de Julio. `94_check_road.py` catches
this class of bug by dropping a ray and reading the material underneath, which
is deliberately a different mechanism from the one that places the trees.

**4. Which colour wins.** `_palette.py`. The palette used to live in four places
and the last one to run won. `pbrmat()` only ever CREATED, so editing a hex in a
script did nothing at all to a material already saved in the `.blend`, and
raised nothing at all. Two local helpers (`retint`, `repaint`) existed to work
around it. Now: one table, applied by `open_city()` on the way in, and
`pbrmat()` reports it when a step asks for a colour the palette overrules.

**5. Where the camera is.** `_common.preview()`. Twelve steps set `ortho_scale`
before their control render and then saved the file; one restored it. So the
camera stored in the `.blend` was a side effect of which step ran last. Worse,
once step 12 has keyframed the camera the fcurve wins, so setting `ortho_scale`
in an earlier step silently did nothing. `preview()` mutes the animation, frames
the shot, and puts everything back.

**The camera in the .blend belongs to `12_camera.py`.** Everything else that
needs a different framing asks for it through `preview()` and gives it back.

**6. Which grade wins.** `_common.GRADE`, applied by `open_city()`. This one
failed more quietly than any of the others, because the two parties were a step
and a library. `07_look` set `view_settings.look = "AgX - Punchy"` seven lines
above its render call, and `blib.render`'s signature carried `look="None"` as a
default and assigned it unconditionally — so the look was set, then reset, then
rendered. The approved still and all 624 frames of the move went out with no
look at all: 0.185 mean saturation against a reference that runs 0.20–0.32, and
5.5 % dark pixels against 10–35 %. Nothing about that raises an exception, and
the number it moved most is the one nobody re-measured after the palette work.

`blib.render` now treats `view_transform`, `look` and `exposure` as
"leave the scene's alone" when they are not passed. **A step must not set
`view_settings`**; steps 11 and 12 used to read the exposure back out of the
scene and hand it to every render call, which was a workaround for exactly this
bug, and those lines are gone.

**7. Where a pedestrian may cross.** `city_lots.json → crossings`, written by 03
where it actually paints a zebra and read by 05 to stand people on one. Two
crossings in five are skipped out of a private `rng(5150)`, so the paint is the
only record: recomputing it in 05 would have been a second copy of that seed and
of the whole nest of offsets around it. Change how the zebras are laid out and
re-run **03, then 05, 08, 11, 12** — 05 places the crossers, 11 times them.

While publishing it, the layout itself turned out to be wrong: see below.

## The zebras were painted inside the junction

`WALK` is the pavement inside the block. `build_markings` treated it as a
shoulder inside the carriageway and subtracted it twice, so every crossing sat
`(w - 2*WALK)/2 + 1.2` = 4.7 m from the street centre on a street whose asphalt
reaches 6 — inside the junction box — and was drawn 5 m shorter than the street
it crossed. You could walk one end to end without reaching a pavement.

It is paint, from 250 m up, at 45°. Nothing could see it, and it only surfaced
because somebody was asked to walk one. The lane dividers on the avenues are
laid out on the same `carriage = w - 2*WALK` convention and are 0.75 m off the
lanes the traffic actually uses; that is under a paint width and has been left
alone.

## A hold is a placement, and it has to pass what a placement passes

`11_animate` resolves a junction by moving one car up to 45 m back along its
lane before frame 1. That gives it a different ten seconds of driving, so it is
a new placement — but it was vetted with less than one: a single point against
the buildings and the superblock, where `path_blocked` vets the whole path
against those **and** the Obelisco's island, and where step 05's placement also
knew about the other vehicles.

Two failures came out of the gap, both invisible because frame 1 always looked
right:

- **A car held onto the car behind it.** One speed per lane makes rear-ending
  impossible *for the positions step 05 placed*; a hold moves one of them, and
  once two share a spot they travel together for all 624 frames. Seven pairs
  shipped, one at a separation of exactly zero. Found by `92_check_zfight`,
  which was looking for coplanar faces and found two whole cars.
- **A bus held into the plaza** clipped two people on the Obelisco's island.
  Found by `91_check_crowd`.

A hold now checks `tailgated` against the live lane index, then applies itself
and re-runs `path_blocked`, rolling back if it fails. It costs 62 more vehicles
taken off the road out of 1513, and step 11 prints the overlap count so a
regression cannot be silent again.

## The crowd and the traffic were two layers, not one city

685 of 2883 people stood on a carriageway and 545 were driven through during the
shot, with every standing check passing. Two mechanisms fixed it and they are
different on purpose:

- **Placement asks the ground.** `_common.surfacer` — the ray 94 has always
  dropped for the trees — is now asked by 05 before it stands anybody, and by 11
  before it walks them.
- **The check asks something dynamic.** That makes "is anyone on the asphalt"
  circular, so `91_check_crowd` samples the shot and counts people a vehicle
  passes through. No placement pass can answer that one.

The crossers are the exception: they are meant to be on the road, and
`11_animate.crossers` times each against the real vehicles in the lanes it
crosses, reusing `Car.window` with a person's clearance. Exposure is computed
**per lane** — as one carriageway it needs a 9-second gap that never exists, and
138 of 173 stood still.

## The street tables are per axis and they are not interchangeable

A street running along X sits at a Y coordinate, so it comes out of the Y table.
Reading the wrong one is off by 5–6 m, which is less than a lane width, so every
street still reads as a street while the cars quietly drive along the pavement.
One axis of this city drove on the left for weeks.

## Files that travel with the .blend

Do not delete these. They are regenerated by the steps that own them, but the
steps that read them will produce a wrong city rather than an error if they are
missing — which is why `open_city(needs_files=...)` checks first.

| file | written by | read by |
|---|---|---|
| `city_lots.json` | 03 | 04, 05, 06, 06b, 08, 11, 95 |
| ⤷ its `crossings` key | 03 (only where a zebra was actually painted) | 05 |
| `city_solids.json` | 04, 06, 06b, 10 (per tag) | 05, 11, 99 |
| `city_signs.json` | 04 | 10 |

`city_solids.json` is merged per tag, never rewritten whole: the steps run one
at a time and each rebuilds only its own layer, so a whole-file rewrite would
silently drop the layers still standing in the `.blend`.

**The sign manifest is positional.** `10_signs` gives billboards and medianeras
a private material per sign, named off the planned object (`Logo Sign.045 BOCA`)
so that dropping real artwork on one wall does not repaint four others. Those
names come from creation order in step 04, so re-running 04 with different
massing re-shuffles them and any artwork applied by hand comes unstuck.

## The two traps that are not dependencies

**`02_kit.py` purges the KIT.** It used to build `Heli.001` alongside the old
`Heli` while every instance went on pointing at the old one, so an edit to an
asset silently did nothing. Purging fixes that and makes the consequence honest
instead of invisible: a re-run leaves every existing instance orphaned, so it
**must** be followed by the whole chain from `03_ground.py`, and
`02b_porteno_kit.py` has to run again too because its assets live in the same
collection.

**`_stage.py` destroys the city.** It was called `00_setup.py`, which put it at
the head of a list of numbered steps that are otherwise all safe to re-run —
and it opens with `blib.reset()`.

## Where the shared code lives

| file | what is in it |
|---|---|
| `_common.py` | the numbers, `Mesh` and instancing, and the step scaffold (`open_city`, `purge`, `preview`, `save_city`, `require`) |
| `_palette.py` | every art-directed colour in the city, once |
| `_solids.py` | the footprint table and the spatial query behind it |
| `_archive/` | spikes that settled a decision and are kept as evidence. They carry the layout from before step 03 went to per-row block sizes, so their numbers are not current |

## The web build

`20_export_web.py` is the only step that writes outside the `.blend`, and it is
the last one: it reads the finished city and publishes `web/public/`. See
`web/README.md`.

It is a step and not a script off to one side because it has the same failure
mode as every other step here — **none of what can go wrong raises an
exception.** Three things already have, and each is now checked in the export
rather than noticed in a browser:

- **The names are the joint.** The motion file addresses objects by name and
  the browser looks them up in the glb. A name the glTF exporter rewrites is an
  object that silently stops moving.
- **The transform is world, not local.** Read locally, a car's heading is not
  animated at all (step 11 keyframes location only), so half the traffic drove
  sideways at a perfectly plausible speed, and `Heli.rotor` — which has a
  parent — was placed by its offset from a helicopter it no longer knew about.
- **Two keys are not always enough.** The rotor turns exactly 26 times over the
  shot, so its two ends agree and every "did it move?" test says no.
  `check_motion` compares the browser's interpolation against Blender at three
  frames nobody sampled, and fails the run if they disagree.

And one that is not in the export at all, because it was in the geometry: until
`_common.box()` and `.sphere()` were fixed, **100 of the 118 closed meshes in
this .blend had their faces wound inside out**. Cycles shades both sides and
never mentioned it; the browser draws the far face and the roof signs tore
against the decks they lie on. If anything looks wrong in the browser and right
in a render, suspect this first — `bmesh.calc_volume(signed=True)` is positive
when a closed mesh points outward, and CLAUDE.md has the whole story.

The look is measured, not eyeballed: `window.measure()` in the browser reports
the same five numbers `_common.GRADE` was fitted with, against the same
reference frame.

It also publishes `bounds` — the rectangle the built city occupies, measured
off the 533 footprints in `city_solids.json` rather than off a bounding box,
because step 03 lays ground well past the last block. Free navigation in the
browser is fenced to it, so the orbit cannot end up over bare site or under the
sheet.

## The standing checks

None of what they catch raises an exception, and none of it is reliably visible
from the hero camera.

```bash
./bl scripts/city/99_check_overlap.py    # nothing is standing inside a building
./bl scripts/city/98_check_floating.py   # nothing buried, nothing hovering
./bl scripts/city/95_check_traffic.py    # right-hand traffic, and on the road
./bl scripts/city/94_check_road.py       # nothing green ON the road
./bl scripts/city/96_check_title_move.py # the title from other angles
./bl scripts/city/93_check_signs.py      # how many brands the shot delivers
./bl scripts/city/92_check_zfight.py     # nothing fights for the same plane
python3 scripts/city/97_check_title.py renders/city_08_title_only.png
```

`92_check_zfight.py` also turned up something no check owns yet: **about twenty
pairs of vehicles are parked inside each other**, 17 to 23 m2 of overlap each
(`CarTeal.i.150` and `CarTeal.i.151`, say). That is not a z-fighting fault, it
is step 05 placing two cars in one space, and `99_check_overlap.py` does not
see it because it tests things against buildings and not against each other.

`93_check_signs.py` answers the question the build could not answer at all
before it existed: **how many distinct company brands actually go past the
camera.** Signs were planned evenly over a 700 m city that the shot crosses on
one 320 m diagonal, so 77 were built and 18 reached the frame, of which twelve
were distinct — the rest were beautiful and off camera. It also enforces the
two rules that are about what the frame reads as rather than about the roof:
one sign per building, and no two of them closer than `MIN_GAP` of the frame
width while both are on screen.

`99_check_overlap.py` is the one to run after touching anything that places
objects. A tree inside an office wall is invisible from the hero camera — it
hides behind the very wall it is inside — and 917 of them survived the whole
build until there was something that could count.
