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
| `05_life` | `KIT`, `SITE`, `BUILDINGS`, lots, **solids** | `NATURE`, `FURNITURE`, `TRAFFIC`, `PEOPLE`, `ROOFPEOPLE` | — |
| `08_title` | `BUILDINGS`, `NATURE`, lots | `TITLE` | — (it DELETES from other collections) |
| `11_animate` | `TRAFFIC`, `TITLE`, lots, solids | `AIR` | — (animates `TRAFFIC`, `PEOPLE`) |
| `12_camera` | `TITLE`, `TRAFFIC` | — | the camera animation |
| `07_look` | `BUILDINGS`, `TITLE` | — | the compositor |

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
python3 scripts/city/97_check_title.py renders/city_08_title_only.png
```

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
