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

## The other rule: count it before you fix it

Three kinds of request come in, and they get three different answers. **Only the
third one is a judgement call**; the first two are decided by what was asked.

**1. A request about one thing. Do that one thing.** "Paint building A red"
means building A. Do not go looking for a rule, do not repaint the city, do not
propose a palette system. This is the case `the .blend is the deliverable`
below is about, and it is the most common one.

**2. A request about everything. Do it once, where the number lives.** "The
buildings are 12 storeys, make them 13" is not eighty edits: it is one, in the
step that decides storeys, followed by re-running the chain. Editing eighty
objects by hand produces a `.blend` that is right and a script that is wrong,
and the next run of that step silently puts all eighty back. **The scope came
from the request — the only thing to get right is not doing it by hand.**

**3. A request about one thing that is a symptom of everything. Do what was
asked, then count, then say the number.** This is the one worth being alert
for, and it is where the rest of this section applies. "There are four people
standing in the middle of the street by the sign" was a true report about four
people, and underneath it were 685 standing on a carriageway and 545 being
driven through during the shot. Four is a nudge. 685 is a rule that does not
exist.

**Do not assume case 3 — measure whether you are in it.** The cost of checking
is one script that counts; the cost of guessing wrong in either direction is
either shipping 681 more of the same, or rebuilding a city nobody asked you to
touch. And when the count comes back large, **the scope is still the user's
call**: report the number and what fixing it costs, rather than quietly widening
the job.

**What gets reported is a sample, not the bug.** Every defect in this project's
history arrived as one instance somebody happened to see, and every one of them
turned out to be a rule that was wrong everywhere it applied:

| what was reported | what it actually was |
|---|---|
| four people standing in one street | 685 of 2883 on a carriageway, 545 driven through |
| a tree in a wall | 917 of them |
| the roof signs flicker in the browser | 100 of 118 closed meshes wound inside out |
| two cars in the same spot | 7 pairs, one at a separation of exactly zero |
| one zebra crossing that led nowhere | all 216, from subtracting `WALK` twice |
| the masts are floating over the roof | all 13, from standing on the parapet line |
| the traffic looks odd on that street | one whole axis of the city driving on the left |

So the first move on any defect is **not** to fix it. It is to write the thing
that counts how many there are — and that number decides what kind of problem
it is. Four people in a street is a placement to nudge. 685 is a missing rule,
and nudging four of them ships the other 681.

The loop, in order:

1. **Measure.** Count every instance before touching anything. The count is the
   scope, and it is usually one to three orders of magnitude larger than the
   report.
2. **Find the rule that is wrong**, not the instances. 685 people on the asphalt
   was one fact nobody had written down: the placement had no idea what a road
   was. It could not be fixed 685 times.
3. **Fix it where the rule lives**, once, and make every caller read it. Look
   for the second copy while you are there — most of these were two places
   disagreeing about one number.
4. **Leave the counter behind as a check**, and make it ask a question the fix
   cannot answer by construction. See `91_check_crowd` on why it counts people
   a vehicle drives through rather than people standing on asphalt: once the
   placement reads the geometry, asking the geometry is circular.
5. **Re-measure.** The number is 0, or the fix is not done.

**The test that tells case 3 from case 1** is not "could this be generalised" —
almost anything can. It is **"is this instance a violation of a rule that should
hold everywhere?"** A building that reads badly from the hero camera breaks no
rule: it is taste, taste does not generalise, and there is nothing to count.
A building standing inside another one breaks an invariant, and there were
never one of those. **Ugly is a case. Wrong is a rule.**

**A repair has to pass everything the original placement passed.** This is the
corollary that keeps catching people. `11_animate` resolves a junction by moving
a car 45 m back along its lane — that is a new placement, not an adjustment, and
it was vetted with a fraction of what the placement was vetted with. Two bugs
came out of that one gap. When you move something that was validated, re-run the
validation; do not write a lighter version of it inline.

**When the request really is one instance, say so and do it.** The judgement
belongs to whoever is asked, not to a rule — but state the count either way, so
the person asking can decide whether they want the other 681.

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
./bl scripts/city/07_look.py final   # the final Cycles frame, shot on the last one
./bl scripts/city/20_export_web.py   # and the same city, published to web/
```

**`docs/city/MAP.md` is the dependency graph**: what each step reads, which
collections it owns and rebuilds, what it publishes, and the five couplings that
have actually broken a build. Read it before changing anything, and before
adding a step. The graph is declared in the code as well — every step opens with
`open_city(needs_collections=..., needs_files=...)`, so a missing prerequisite
stops the run with the command that fixes it, instead of surfacing thirty lines
later as a `KeyError` or not surfacing at all.

Five numbers are shared and each one is shared because two steps disagreed
about it once, silently:

- **How long the shot is** — `_common.FPS / FRAMES / MOVE`. Change it there,
  then re-run **11 and then 12**, in that order.
- **Where the camera goes** — `_common.SHOT_*`, with `shot_at()` and
  `shot_cover()`. Step 12 flies the move and step 04 plans a company sign for
  every roof the move passes over, so they read one path. Change it, then
  re-run **04, 10, then 12**.
- **How wide the hero frame is** — `_common.HERO_WIDTH`. The move has to land on
  the framing the still is rendered at.
- **Every colour** — `scripts/city/_palette.py`, one table, applied on the way
  in by `open_city()`. Editing a hex anywhere else does nothing and says nothing.
- **The grade** — `_common.GRADE`: the view transform, the look, the exposure,
  the white balance, and the sun-to-sky ratio the whole frame's contrast comes
  from. Also applied by `open_city()`. It is a shared number because it was a
  private one: 07_look set `view_settings.look` on the line above a
  `blib.render` whose own default reset it, so the still and all 624 frames of
  the move shipped with no look at all — flat, grey and cool against every
  reference frame. `blib.render` now leaves the scene's view settings alone
  unless a caller passes its own. **Do not set `view_settings` inside a step.**

**The city has a south rim**, one row of blocks bolted on outside the grid at
`j = -1`, because the opening frame of the move ran 83 m off the end of the map.
Do not turn it into a tenth row: `EXTENT = 10` recentres the whole grid and moves
the Obelisco, the title and the approved hero framing. Steps 03, 04 and 05 each
skip it in their shared pass and build it last from `rng(RIM_SEED)`. See
`docs/city/MAP.md`.

**The camera in the `.blend` belongs to `12_camera.py`.** Any step that needs a
different framing for a control render asks through `_common.preview()`, which
mutes the animation, frames the shot and puts everything back.

`02_kit.py` and `02b_porteno_kit.py` run once, before all of it, in that order.
`_stage.py` builds the empty stage and **destroys the city**: it runs once, at
the very beginning, and never again. It was called `00_setup.py`.

`02_kit.py` now **purges the KIT collection** before rebuilding. It used to
build `Heli.001` alongside the old `Heli` while every instance went on pointing
at the old one, so an edit to an asset silently did nothing. Purging fixes that
and makes the consequence honest instead of invisible: a re-run leaves every
existing instance orphaned, so it **must** be followed by the whole chain from
`03_ground.py`, and `02b_porteno_kit.py` has to run again too because its assets
live in the same collection.

Nine standing checks, because none of these failures raise an exception:

```bash
./bl scripts/city/99_check_overlap.py           # nothing is standing inside a building
./bl scripts/city/98_check_floating.py          # nothing buried, nothing hovering
./bl scripts/city/95_check_traffic.py           # right-hand traffic, and on the road
./bl scripts/city/94_check_road.py              # and nothing green ON the road
./bl scripts/city/96_check_title_move.py        # the title from other angles
./bl scripts/city/93_check_signs.py             # how many brands the shot delivers
./bl scripts/city/92_check_zfight.py            # nothing fights for the same plane
./bl scripts/city/91_check_crowd.py             # and nobody is driven through
python3 scripts/city/97_check_title.py renders/city_08_title_only.png
```

`93_check_signs.py` counts the thing the video is actually for. The signs are
planned for a camera that crosses the city on one diagonal, so "77 signs built"
and "how many a viewer sees" are different numbers by a factor of four, and only
the second one matters. It measures `built` — the mesh step 10 made — because
the plan and the result stopped being the same thing once brands started hanging
off facades. See **How a brand gets added** below.

There is one more script in that family and it is not a check: `90_brand_sites.py`
answers where the next client can go, before anything is edited.

**A hold in `11_animate` is a placement, and it has to pass what a placement
passes.** Resolving a junction moves one car up to 45 m back along its lane, so
it gets a different ten seconds of driving — but the hold was vetted with one
point against the buildings and the superblock, where `path_blocked` vets the
whole path against those *and* the Obelisco's island. Two failures came out of
that gap and both were invisible, because frame 1 always looked right: a bus
held into the plaza clipped two people standing on the island, and a car held
back 36 m landed on the car behind it — where it then stayed for all 624
frames, because everything in a lane shares one speed. Seven pairs shipped like
that, one at a separation of exactly zero. **The "no rear-ending by
construction" invariant is about the positions step 05 placed; a hold moves
one.** Step 11 now prints the overlap count, and it is 0.

`92_check_zfight.py` finds two faces on one plane, overlapping, pointing the
same way — a question with no answer. **Cycles answers it arbitrarily but
consistently, so it has never shown up in a render**; a rasteriser answers it
per pixel and the surface tears into patches that swap as the camera moves.
It works in world space across objects, ignores anything no viewpoint can
reach, and ranks by area, because the worst fault in the city was two
triangles. Two things cause it, and see **the winding** below for the first.
The second is a detail resting exactly on its backing: sink it by
`_common.SINK`, and `10_signs.mark()` is the worked example.

`99_check_overlap.py` is the one to run after touching anything that places
objects. A tree inside an office wall is invisible from the hero camera — it
hides behind the very wall it is inside — and 917 of them survived the whole
build until there was something that could count.

**A roof `top` is the top of the parapet, not the deck.** `wing()` finishes
every wing with a plate at 0.02 and a 0.85 m parapet ring around the edge, and
returns the top of the ring, because that is what a sign hangs off and what the
published solid has to reach. Anything that *stands* on the roof stands
`04_buildings.DECK` below it. That subtraction was written out by hand in four
places and forgotten in a fifth, so all 13 masts in the city floated 0.83 m over
their own roof — the ring is at the edge and thin air everywhere the pole
actually is. It is one number now and every caller reads it.

`98_check_floating.py` missed all 13 for as long as its TEST B meant "is this
an instance of a KIT asset", and a sign is not one. It tests the sign formats
that rest on a deck as well now. **Membership in a check is part of the check**:
this one had been passing for months on a question it was never asked.

`95_check_traffic.py` exists for the same reason one axis of this city drove on
the left for weeks: every street looked completely plausible on its own, and the
only way to see it was to follow one car or to count.

`94_check_road.py` drops a ray under every tree and reads the material of the
ground it lands on, so it answers the question against the site mesh rather than
against the street tables the placement already read. That is the point of it:
four trees stood in the middle of the 9 de Julio beside the Obelisco and both
tables were correct — step 03 dropped the median across the plaza block for
being two 9 m stubs, and step 05 planted one anyway from its own arithmetic.
The rule now lives once, in `_common.median_runs`, and both steps read it.

`91_check_crowd.py` asks the one question about the crowd that no placement
pass can answer. **The crowd and the traffic were two layers, not one city**:
685 of 2883 people — 23.8 % — were standing on a carriageway, and over the 26 s
of the shot a vehicle drove clean through 545 of them. Every standing check
passed the whole time, because none of them had ever been pointed at the people.

So the ray that 94 drops for the trees is in `_common` now and step 05 asks it
before it stands anybody anywhere. That makes "is anyone on the asphalt" a
circular question — the placement reads the same geometry the check would — so
this check asks a **dynamic** one instead: sampled across the shot, does a
vehicle ever share a body-width with a person? It is 0 now, and it is the number
to watch, because it is the only one that cannot be satisfied by arithmetic.

The people at the zebras are the exception that proves it: they are *meant* to
be on the road. `11_animate.crossers` times each one against the real vehicles
in the lanes it has to cross — the same `Car.window` that stops two cars meeting
in a junction, asked with a person's clearance — so they wait at the kerb and go
when there is room. 114 of 173 find a gap; the other 59 stand and wait, which is
what a person does. **The failure mode is somebody waiting, never somebody under
a bus.**

Two things this cost, and both are the usual shape:

- **Exposure is per lane, not per carriageway.** Treating the road as one
  hazard means a 12 m crossing needs a 9-second gap, and on a street with a car
  every 13–44 m there is never one: 138 of 173 stood still. A car in the far
  lane cannot hit somebody still in the near one.
- **Shorten the walk, don't cancel it.** Refusing every walker whose fifteen
  metres left the pavement rooted 587 of 1000 people to the spot. Someone who
  walks eight metres and stops at the corner is a person waiting to cross;
  someone who never moves is a bollard.

**The traffic lights are props and they stay props.** They show all three lenses
at once and never change, and the green wave that would fix it cannot be built
on this traffic: nothing in this city brakes — step 11 gives every vehicle one
constant speed, which is what makes rear-end collisions impossible by
construction — and **98 of the 100 junctions have traffic crossing on both axes
during the shot**, so any colour a signal shows is a lie for one of the two
streets. Scale settles the rest: at 170 m across 1920 px a 16 cm lens is 1.8 px.
The rule a light would have encoded lives in the crossers instead, applied to
the thing big enough to see it. Making the signals honest means braking the
vehicles, which is a rewrite of `11_animate`, not a tweak.

## The zebras were painted inside the junction

`WALK` is the 2.5 m of pavement **inside the block**. It is not a shoulder
inside the carriageway: a street is asphalt for its whole declared width. Step
03 subtracted it twice when it laid out the crossings — set back
`(w - 2*WALK)/2 + 1.2` from the street centre, which is 4.7 m on a street whose
asphalt reaches 6 — so every zebra was painted **across the middle of the
junction box** rather than beside it, and drawn 5 m shorter than the street it
crossed.

**Nothing could see it.** It is paint, from 250 m up, at 45°: it reads as a
crossing wherever it is. It surfaced only when somebody was asked to *walk* one
and the far end turned out to be more asphalt — you could follow one for twenty
metres without ever reaching a pavement.

Where the zebras are is now published, in `city_lots.json` under `crossings`,
because two crossings in five are skipped out of a private `rng(5150)` and the
paint is the only record of which. Step 05 stands people on the published ones;
the kerb they wait at is **found by walking out with the ray**, not computed
from the half-width, because every corner is chamfered by the ochava and the
point 1.1 m past the kerb line is over the cut.

## The winding was inside out, everywhere, until it wasn't

`Mesh.box()` and `Mesh.sphere()` in `_common.py` built their faces wound the
wrong way, so their normals pointed INTO the solid. Measured by signed volume,
**100 of the 118 closed meshes in the .blend were inside out**: every tree,
every car, the helicopter, the jacarandas, every sign plate.

**Nothing could see it.** Cycles shades both sides of a face, so every render
this project ever shipped was correct. A rasteriser is not so forgiving: with
backface culling on, the face it draws is the far one, and the far one is
usually lying on top of something. That is what made the roof signs flicker in
the browser — the plate's UNDERSIDE was being drawn, and it sits exactly on the
roof deck.

Two things follow, and both are the point of writing this down:

- **Check the winding before blaming anything else.** `bmesh.calc_volume(
  signed=True)` on a closed mesh is positive when the faces point outward.
- **A render is not the only judge.** To see what a rasteriser sees without
  leaving Blender, set `use_backface_culling = True` on every material and
  render: before the fix the roof logo was translucent and the towers had open
  floors; after it, everything is solid. That is the cheapest reproduction of
  the browser there is.

Changing a primitive in `_common` means **rebuilding the whole chain** from
`02_kit.py`, because the geometry is already baked into the .blend. That is
what fixing this cost, and it is the reason to check `92_check_zfight.py`
before adding anything that lies flat on a surface.

Read `docs/city/MAP.md` before touching the build,
`docs/city/STYLE-BIBLE.md` before touching the look, and `docs/city/PLAN.md`
for how the build is organised and which decisions were already settled (roads as
negative space, orthographic camera, depth of field from the Z pass, the title
built as buildings on the street grid). Both documents record the attempts that
were wrong as well as the one that stuck — the title was got wrong three times,
and every wrong version measured well.

Four files travel with the `.blend` and are read by later steps, so do not
delete them — **and they are committed alongside it**, which for three of them
they were not: a fresh clone got a 19 MB city and no way to run a single check
against it, because the .gitignore shipped the deliverable and not the four
things that describe it. `renders/city_solids.json`, the rectangle every solid
thing occupies; `renders/city_signs.json`, the manifest of company signs (name,
position, orientation, face size, `owner` — the building it belongs to,
recorded by the step that places it because an L is several overlapping wings
and recovering the address afterwards is a guess — and `built`, what step 10
actually made, which is not the same thing: see below); `renders/city_lots.json`,
the street and block tables, which also carry the
section of the Avenida 9 de Julio under `avenue9j` — steps 05 and 06b build
from that key rather than from a second copy of the numbers; and
`renders/city_buildings.json`, **which wings make up each building**.

That last one is new and it exists because a whole batch of client logos went
wrong without it. `city_solids.json` publishes one rectangle per WING, and an L
is several wings that touch, so nothing could tell two buildings apart from two
arms of one. The browser overlay called 149 roofs free when 68 were, a client
landed on a building another brand already had, and grouping by overlap does not
work either: every footprint is published 0.9 m padded, so two neighbours with a
small setback "touch" as well. Step 04 knows without ambiguity — a lot cell is a
building — so it writes it down. Same decision as `own()`: the only step that
knows is the one that records it.

## How a brand gets added

The judgement is almost always the same, and it is not a matter of taste: a
client goes on a building nobody else has, on a wall the camera can see that
faces a street, at the biggest size that wall allows. All four of those have
numeric answers, and answering them by eye is what turned six logos into an
afternoon of renders.

```bash
./bl scripts/city/90_brand_sites.py       # which buildings are free, and which wall
```

It reports, per free building: the wall to use, how much of it the camera
actually sees, how far the kerb is, how big a wordmark and a symbol fit, and
what that would deliver in the frame. Copy the coordinate into that brand's
`HERO` entry as `facade_at`, the wall as `facade_side`, then rebuild
`04 → 10` and **look at it**.

**The coordinate goes in `HERO`, and only sometimes in `EXTRA` as well.** An
`EXTRA` anchor is placed by `plan_extra`, which runs only on a cell the
allocation left with **no sign at all** — so on a building that already has a
record, an anchor is never placed and the step says `NO ENTRARON: X` and nothing
more. It is also not needed there: the allocation already gives every brand in
the `_brands` tables a record, and `facade_at` decides where the art goes, not
the record. Pin the brand in `PIN` so the next sign added does not move it.
Cocos is the worked example, on a building whose record is the Mercado Libre
anchor — a `facade_only` brand whose own art `HERO` had moved three blocks away.

Five things this project has already got wrong, so do not re-derive them:

- **A logo goes on the FRONT, not on the roof.** That is how every brand here is
  mounted: a `HERO` entry with `facade_only`, artwork stuck to a wall, nothing
  built on the deck. The anchor in `EXTRA` exists only so the manifest has a
  record to pin a brand to; its `kind` is never seen. Roofmarks and billboards
  read as a pale rectangle from 250 m.
- **"The longest wall" is the wrong wall.** On these blocks the long face is the
  one inside the complex. Three brands ended up hanging over a courtyard 17–32 m
  from the street. The wall that faces the street has its kerb under 4 m away,
  and `90_brand_sites` measures it.
- **A wall can be perfectly street-facing and still invisible**, because the
  building's own other arm, or the neighbour a metre away, stands in front of
  it. That is a sightline question, not a distance one: a block 12 m away and
  20 m tall hides a wall with 6 m of clear air in front. `_common.wall_seen`
  casts toward the camera and answers it.
- **What binds the size is the aspect.** A wordmark is bound by the width of the
  wall, a square symbol by its height — and the ground floor is set back, so the
  logo lives between about 5 m and the parapet. Paisanos gets 9,6 m as a symbol
  on its street face and 25 m as a word on its long one; both walls, one brand,
  is what `facade_arts: ["iso", "word"]` is for.
- **One brand per address, and the check now counts what HERO moved.** A sign
  record points at the roof it was planned on while its artwork can hang off a
  neighbour's wall, so a building carrying two logos used to read as empty.
  Deliberate exceptions go in `_brands.SHARED` with their reason, which is not
  the same as the rule not running.

**`93_check_signs` measures what was built, not what was planned.** Step 10
writes `built` back into the manifest — the bounding box of the mesh it actually
made. For most signs the two agree. For a `facade_only` brand they do not: the
plan is an anchor that is never raised, so the check was reporting "roofmark,
7.1 m" for a 27.6 m wordmark on a wall, and calling this project's best-placed
clients too small to count.

**The street tables are per axis and they are not interchangeable.** A street
running along X sits at a Y coordinate, so it comes out of the Y table. Reading
the wrong one is off by 5–6 m, which is less than a lane width, so every street
still reads as a street while the cars quietly drive along the pavement.

The `.blend` is the deliverable, not the scripts. There is no city generator and
there should not be one: when a building looks wrong, fix that building.

**This is about taste, not about correctness, and the two get confused.** Looking
wrong is a case: it does not generalise, and trying to generalise it is how you
end up with a generator nobody can steer. Being wrong is a rule: a building
inside another one, a car on the pavement, somebody standing in the road. Those
are never one instance — see **count it before you fix it** at the top. Ugly is a
case. Wrong is a rule.

## The city, in a browser

The same city runs in WebGL at 60 fps: `web/`, and `web/README.md` explains it.
One command regenerates everything it draws.

```bash
./bl scripts/city/20_export_web.py     # the glb, the motion, the shot, the sky
cd web && npm install && npm run dev
```

**The browser holds no second copy of anything.** It does not know the palette,
the grade, the camera move or the traffic — the export hands it all four, so a
change to the `.blend` reaches the page by re-running one step and nothing else.
The move in particular is sampled per frame by the export rather than
re-implemented in JavaScript, which is the same reason `_common` owns
`SHOT_*` in the first place.

**The video comes out of the page, not out of a screen recorder.**
`cd web && npm run record` draws all 624 frames offline — no clock, no
sampling, 1920×1080 supersampled 2× — and pipes them into ffmpeg: `mp4` for
sending, `mov` (ProRes 422 HQ) for an edit. A screen recording samples a page
that is itself dropping frames, so the pan judders in the file even though it
never did on screen. `web/README.md` has the flags.

**The look is measured, not eyeballed.** `window.measure()` in the console
reports the five numbers `_common.GRADE` was fitted with — mean luma, contrast,
dark, bright, saturation — read off the framebuffer and compared to
`renders/city_07_look.png`.

**And the web deliberately does not ship the render's grade.** It runs
`TONEMAP = "none"`: linear light, clipped, a stop brighter with the shadows
open — 4.9 % dark pixels against the render's 24 %. AgX is right for a frame in
a film and reads dark and muted for a city you can spin, so the page trades the
highlight rolloff for a lit picture and pays for it in the bright column.
`TONEMAP = "agx"` in `web/src/post.js` restores the render's look exactly, and
the table beside it records what each one measures. Two further constants there
cancel what a rasteriser cannot do (Cycles bounces light; the same scene
arrives 1.2 stops darker).

**A pass that writes its own pixels owns the colour space.** three.js converts
linear light to sRGB for its own materials and cannot do it for a raw
`ShaderMaterial`, so the post chain does it. Skipping it costs 0.18 of mean
luma, crushes the shadows, and — because the missing gamma pulls the channels
apart — makes the frame look MORE saturated. It reads as a grade decision, so
it survives being looked at.

Three failures the export now checks, because none of them raise anything and
all three shipped a city that looked fine and was wrong: the object names the
glTF exporter rewrites, the difference between a local and a world transform
(half the traffic drove sideways), and the helicopter rotor, which turns
exactly 26 times and therefore ends the shot where it started.

## Layout

```
bl                        wrapper: ./bl <script.py>
blib/                     project library (framing, lights, materials, render, GN, export)
scripts/                  Blender scripts, one per task
scripts/city/_common.py   the shared numbers, the mesh plumbing, the step scaffold
scripts/city/_palette.py  every colour in the city, once
scripts/city/_solids.py   the footprint table and the spatial query behind it
scripts/city/_brands.py   the real brands, where each one hangs, and why
scripts/city/_stage.py    the empty stage. Runs once. DESTROYS the city
scripts/city/_archive/    spikes kept as evidence; their numbers are not current
scripts/city/90_brand_sites.py  where the next client fits. Run before editing _brands
docs/city/MAP.md          the dependency graph: read before changing anything
assets/logos/SOURCES.md   where every logo came from, and what each file lacks
scripts/verify_setup.py   environment self-check
scripts/_introspect/      probes that interrogate the API; the probe*.json are the evidence
renders/                  outputs (gitignored: regenerated by running the scripts)
                          including city.blend, city_solids.json, city_signs.json,
                          city_buildings.json
web/                      the city in the browser (three.js + Vite). See its README
web/public/               written by 20_export_web.py; gitignored, regenerate it
.claude/skills/blender/   project skill: verified 5.2 API, look dev, recipes
.agents/skills/           installed three.js skills (symlinked from .claude/skills)
skills-lock.json          which third-party skills are installed, and at which version
README.md                 the public face of the repo. CLAUDE.md is the working one
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
scene while a human watches it in the GUI. It needs that project's Blender add-on
installed (`Edit > Preferences > Add-ons > Install from Disk`) and "Connect to
Claude" clicked in the side panel (N key).

**The add-on is not vendored here.** Get `addon.py` from the upstream project,
[ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) — it used to sit
at the root of this repo as 122 KB of somebody else's code with a one-line
credit, which is not how a dependency is carried.

Not needed for normal work: the CLI gives the full API and everything stays versioned.
