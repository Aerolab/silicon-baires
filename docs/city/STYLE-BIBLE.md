# Style bible — the "toy valley" look

Derived by zooming into the reference frames (`refs/frames`, `refs/crops`), not from
memory. The original sequence was made by yU+co for HBO. We are reproducing the
**look and the city**, not the branding: no company logos. The title itself is
built, as buildings — section 10.

Everything below is a rule to build against. When a render disagrees with this
document, the render is wrong until proven otherwise.

---

## 1. The one-sentence read

A **scale model of a corporate office park**, photographed from a helicopter with a
long lens and a miniature-faking depth of field. Clean, sunny, plastic-toy, mid-day,
no dirt, no grit, no drama.

It is *not* a low-poly art piece and *not* archviz. It is a deliberate mix:

| Layer | Fidelity |
|---|---|
| Buildings, roads, roofs | **clean and semi-realistic**: correct proportions, real facade logic, crisp edges |
| Nature, props, vehicles, people | **openly low-poly and toy-like**: faceted, flat-shaded, abstracted |

That contrast is the signature. Buildings that look low-poly kill it; trees that look
realistic kill it too.

---

## 1b. The numbers, measured off the reference

Not estimated. A car is 4.4 m long, so it works as a ruler, and the rest came
from sampling pixels.

**The reference does not agree with itself, and one frame is not the target.**
Measured the same way across all four frames, Rec.709 luma on sRGB:

| | frame 1 | frame 2 | frame 3 | frame 4 | ours |
|---|---|---|---|---|---|
| Mean luminance | 0.414 | 0.406 | 0.498 | 0.476 | **0.439** |
| Pixels below 0.25 | 35.2 % | 35.1 % | 16.0 % | 11.1 % | **13.1 %** |
| Mean saturation | 0.336 | 0.316 | 0.335 | 0.220 | **0.284** |
| Green coverage | 22.4 % | 23.6 % | 21.9 % | 26.2 % | **27.7 %** |

The dark-pixel fraction runs from 11 % to 35 % across four frames of the same
sequence. An earlier pass took 15.7 % off one frame and wrote it down as *the*
number; a critique later took 35.2 % off a different one and called us 22 points
too bright. Both are one frame. We sit inside the range on every row except
green, which is 1.5 points high. Paving the ordinary block interiors is the
obvious lever and it does not work: it overshoots to 17.3 % and takes
saturation down with it, because the hero frame samples six blocks out of
eighty and the number is noise at that size. See `PLAN.md` for the three
measurements. Do not chase it from the lot surface.

| | Reference | Where we landed |
|---|---|---|
| Scale | ~14 px per metre → **the frame spans ~140 m** | 170 m |
| Road luminance | **0.18**, and warm (0.20, 0.18, 0.14) | 0.19 warm |

Two of these were badly wrong on the first pass and are worth remembering:

- **The shot is tight.** The first attempt framed 590 m, four times too wide.
  Every piece of detail was then sub-pixel, which reads as "not enough detail"
  when the real fault is the lens.
- **The road carries the whole value structure.** At 0.38 luminance and cool
  grey, the frame had 0.3 % dark pixels where every reference frame has between
  11 % and 35 %, and nothing else could compensate.

Saturation was the long-standing gap, at 0.20 against 0.22–0.34. The jacarandás,
the taxis and the company signs closed most of it without anyone grading
anything: it is 0.283 now. Chroma in this frame comes from what is in it, not
from the view transform.

## 2. Camera

Read off the frames:

- **Verticals are perfectly parallel.** No convergence anywhere in frame, left or
  right edge included. The first pass tried perspective with a camera shift and
  measured 6.5° of lean at 150 mm from 1450 m, so the camera is **orthographic**.
  The reference itself is not: its two title lines sit at different leans, which
  only perspective explains. We take the parallel verticals and give up that cue.
- **Long lens, far away.** Near and far buildings are nearly the same apparent scale.
- **Elevation 38°**, **azimuth 45°** so every building shows exactly two faces.
  Measured off the reference at 35°, from the ±30° screen angle of its grid edges.
  Every straight street runs diagonally across frame; nothing is axis-aligned to the
  image.
- **Depth of field is shallow and it is the whole trick.** A band across the middle is
  sharp; the top of frame and the bottom corners go soft. That single effect is what
  makes a 600 m city read as a 60 cm model.
- Frame is **densely packed edge to edge**. There is no empty foreground, no sky, no
  horizon. The city bleeds off all four sides.

## 3. Light

- One sun, **high, slightly behind and to the right** of camera. Shadows are short and
  fall toward the lower-left.
- **Shadows are soft** (large sun angle, ~3–5°) and **not black**: they read as a
  darker, slightly cooler version of the surface, never as a hole.
- Strong, even ambient fill from a bright sky. Nothing in frame is underexposed; the
  darkest asphalt still reads as grey, not black.
- Time of day: late morning. Warm-neutral, no golden hour, no long shadows.

## 4. Palette

Measured off the frames.

| Role | Colour | Notes |
|---|---|---|
| Warm concrete | cream / beige `#e6ded0` → `#cfc4b2` | the dominant building tone |
| Cool concrete | grey `#b9bcbd` → `#8e9295` | second family, for the greyer campuses |
| Glass, light | desaturated teal `#7fa3ad` | office banding, always slightly reflective |
| Glass, dark | near-black slate `#2c3134` | curtain-wall towers; **visibly reflects the city** |
| Asphalt | warm dark grey `#3a3a3c` | never pure black |
| Sidewalk / kerb | light warm grey `#c9c6bd` | raised ~15 cm above the road |
| Road markings | off-white `#eef0ee` | crisp, no wear |
| Grass | saturated mid green `#4aa32a` | flat, no texture, hard edges against concrete |
| Foliage | 4–6 greens, `#2f6b25` → `#79b93a` | varied per instance |
| Trunks | red-brown `#7a3b2a` | short, thin, visible |
| Roof plant | salmon / terracotta `#d0714a` | the ductwork and pipe frames |
| Accents | pure saturated red, yellow, magenta, orange | props only, one or two per block |

Rule: **surfaces are matte**. Roughness 0.6–0.9 for concrete, 0.4 for painted metal.
Only glass and water are smooth. No metals except small props.

## 5. The architecture kit

Every building in frame decomposes into the same few moves.

**Massing.** Footprints are rectangles and L / U / Z / T combinations of rectangles,
axis-aligned to the block. Heights are quantised to floors. Most of the city is
**2–5 floors**; a handful of 8–12 floor slabs; exactly one or two real towers; one
stadium; one organic "blob" building.

**Facade.** The dominant pattern is **horizontal banding**, repeated per floor:

```
  ─── solid spandrel band (concrete, protrudes ~15 cm, casts a shadow line)
  ─── recessed glass band (with thin vertical mullions at a regular pitch)
  ─── solid spandrel band
```

Variants seen: continuous horizontal louvres (thin slats, no glass), punched square
windows in a grid (the older/darker buildings), full curtain wall (the dark towers),
and glazed roofs made of a **grid of dark mullions over light glass**.

**Roof.** The camera is high, so the roof is 60% of what you see of a building. It is
never a bare plane. Always:
- a **parapet ring** around the edge, 60–90 cm, lighter than the walls,
- then some combination of: HVAC boxes, a salmon **pipe frame** (a rectangular loop of
  extruded pipe with 1–2 boxes on it), solar panel arrays (blue-grey grids), skylights,
  a rooftop garden, a pool, a helipad, a ping-pong table, a stair bulkhead, satellite
  dishes, and 2–5 people.

**Ground.** Each block sits on a **raised slab** with a visible vertical edge, so the
city is a set of terraces, not a flat plane. Kerbs, planters and plazas are all just
slabs at different heights.

## 6. Roads

- Wide, **dark asphalt** with an off-white solid edge line on both sides and lane
  separators. Crosswalks are full zebra bars on all four arms of an intersection.
- The network is a **strictly rectangular grid** with a hierarchy: 12 m local
  streets, 22 m avenues every third or fourth line, and block sizes that vary
  52–76 m per row and column. That variation is what stops it reading as a
  spreadsheet. Curved arterials were tried and dropped: a curve meeting an
  orthogonal grid leaves a block that merely touches the corridor losing its
  whole 64 m footprint to clear a 12 m verge, and the result was two enormous
  empty roads with one building stranded between them.
- Sidewalk is a raised slab that follows the road, with the kerb face visible.
- Street furniture: streetlights (pole + curved arm + flat head), traffic lights (pole
  + long cantilever arm + 2 signal boxes), signposts, occasional bus shelters.

## 7. Nature

- Two archetypes cover 90% of it: a **rounded broadleaf** (2–4 faceted lobes on a thin
  trunk, flat shaded) and a **conifer cone**. Plus low hedges and shrub blobs.
- Heights 6–11 m. Colour, scale and rotation randomised per instance.
- Trees line the streets in regular rows and clump irregularly in parks. Both patterns
  are needed; only one of them looks wrong.
- Grass is a **flat plane with a flat green material**. No grass geometry, no texture.

## 8. Population

- **Cars:** one extruded rounded body + a lighter glass greenhouse + dark wheels.
  Perhaps 200 triangles. One flat saturated body colour each. Vans, pickups, a bus, a
  box truck, a helicopter.
- **People:** ~1.75 m, boxy, Lego-adjacent — torso, head, hair block, arms, legs, each a
  flat colour. No faces. They read at 10–20 px. They are what makes the model feel
  inhabited and they are cheap; use hundreds.
- Groups matter more than individuals: clusters at crossings, queues, people on roofs,
  people around the pool.

## 9. Render finish

- Slight **film grain** over the whole frame (visible in the reference).
- Very slight vignette / falloff at the edges.
- Colour is punchy but not crushed: saturated greens and accents, everything else
  desaturated. `AgX` will fight the saturated greens; test `Khronos PBR Neutral` and
  `AgX - Punchy` before committing.

## 10. The title

Ours says BUENOS AIRES. The construction is the reference's; the words are not.

- **The letters are the buildings.** Not an overlay, not a billboard, and not
  plates resting on roofs either — that was a wrong reading that survived two
  rounds of review because it measured well. Zoom into the S of SILICON: there
  is a curved glass facade directly under it, following the curve of the S. The
  red is the roof of a building whose plan is the letterform, standing on the
  ground and taking up real space.
- They carry **the same banded facade as the rest of the city**, which is what
  makes them read as architecture and not as type dropped in. Blender's font
  curves take an outline offset in metres, so a letter can be shrunk
  perpendicular to its own contour: that is a facade band, and scaling cannot
  do it.
- **The baseline runs along a street.** Measured, not assumed: in the window of
  frame beside SILICON the city's own edges run at −27° and SILICON runs at
  −25.6°; at the bottom of frame the city runs at −13° and VALLEY at −13.5°.
  The two words are parallel to the grid and differ from each other only
  because that render is perspective and its lines converge.
- **The letters are ordinary letters.** Baseline along one city axis, the
  letter's own vertical along the other. Both grid axes project to ±atan(sin
  *e*) = ±31.6°, so from this camera a letter reads as a 63° lozenge rather
  than as upright type. That is what a letter-shaped building looks like from
  a fixed oblique view and it is not a defect to correct.
- **Do not pre-shear the plan to flatter the camera.** It was tried: shearing
  the glyph 45° in plan puts its stem exactly vertical on screen, and it works,
  and it is wrong. It makes the buildings parallelograms in order to please one
  viewpoint, and every other viewpoint pays for it.
- **The title occupies its own block and the streets run around it.** With the
  baseline on the grid the footprint is *a·H* across by *W + a·H* along, which
  is one block wide by two long — not four. Four leaves half the site as empty
  paving.
- **One letterspacing value, both words, and the same cap height.** Solving the
  spacing per word so that both span the same width opens the shorter word to
  nearly double the gaps, to cover for having a letter fewer. The short word is
  simply shorter and centred under the long one. Below about 0.88 of the
  default advance, a Black weight closes up and the letters weld together.
- They are *not* staggered along the baseline: shifting the second word back
  also lifts it on screen by sin *e* times the shift, which eats the clearance
  between the lines and they collide.
- **The roof is red, the parapet is a dark cut edge.** Carrying the face red
  down the side reads as inflated plastic.
- **Signal red**, `#ED1B16` measured off the reference frame. AgX Punchy will not
  give you both that brightness and that purity: pick the base colour against the
  render, not against the swatch.
- The letter buildings are **squat**: about 25 m tall against a 22 m cap height.
  Taller and each letter becomes a tower and the word stops reading from above.

## 10b. The company signs

We are not reproducing the branding, so the companies are invented. What is
reproduced is how a logo is physically mounted, because that is what shows.

- **Facade letters.** Individual extruded letters mounted **on the wall**,
  hanging just under the roof edge, cap height ~4.2 m, extruded ~0.9 m. Zoom
  into the Google building: the roof-edge band runs *above* the letters and
  they cast their shadow down the facade. They were first built standing on top
  of the parapet, which is wrong and costs them everything — on the parapet
  they read against the sky and the roof; on the wall they read against pale
  concrete, and that contrast is the whole point.
  Put them on a wall the camera can see: from azimuth 45 that means +x or +y.
  And they have to stand clear of whatever else the facade already carries —
  ours has a shade frame 0.45 m proud, so 0.45 m of projection put every letter
  inside it.
- **Roofmark.** A flat panel lying on the deck, about 0.42 of the smaller roof
  dimension, with a single flat mark on it. Costs no height at all and is the
  commonest type in the reference.
- **Mast disc.** A large disc on a pole, standing clear of the roof, turned to
  face the camera. One or two in frame at most: it is a hero.

The mark is a silhouette and nothing else — a disc, a ring, a square, a
triangle, a chevron, three bars. At this distance there is no such thing as a
detailed logo. Saturated face, flat ink, matte: nothing here is emissive.

Roof units and signs compete for the same roof, and the sign wins. Whatever
places the units has to know where the sign is going first.

## 10c. What makes it Buenos Aires

The test is whether it survives being twelve pixels tall from a high oblique
view. Almost nothing that makes the city recognisable at eye level does: the
tiled pavements, the cafés on the footpath, the kiosks, the painted party walls
are all invisible from here. Silhouette and colour are what is left.

| Cue | Why it survives |
|---|---|
| **Ochavas** — every block corner cut at 45° | the best of the lot, and it is not a prop: Buenos Aires cuts every street corner by code, so no block downtown has a 90° corner and every crossing opens into an octagon. Four bevels per block. With square corners the grid reads Manhattan |
| **Jacarandás in flower** | violet against green reads at any size. One street tree in five; at one in two the city turns into a fantasy |
| **Taxis**, black body, `#f2c300` roof | this camera sees mostly roof, and the roof is the livery |
| **Colectivos**, flat two-tone per line | a small bright rectangle among the cars |
| **The Obelisco**, 67.5 m on a 6.8 m base | taller than every building here, so it is the only vertical in frame |
| **Cúpulas** on corner buildings, oxidised `#4a6b63` | a dome is a silhouette, not a texture |
| **Floralis Genérica**, 23 m, 32 m across, over a 44 m pool | the only polished thing in the city, and the pool is what makes its plaza read |

The monument numbers are sourced, not remembered, and two were wrong the first
time. The Obelisco is 67.5 m of which **63 m is shaft**, from the base to a
3.50 m square where the apex begins — so the apex is 4.5 m, not 3.5 — and it
ends **blunt at 40 cm**, not in a point. (The sources disagree about the base:
7 × 7 m in one place, 6.80 m per side in another.) The Floralis is **32 m
across** open over a **44 m pool**, not the 20 m and 14 m first built, which
made it a sculpture on a lawn instead of the thing that fills its own plaza.

**The taxi livery is a law, not a style choice.** Ley 2.148 art. 12.3.3.1: black
below, yellow from the lower line of the window upward — so the whole
greenhouse is yellow with a glass band cut into it, not a black cabin with a
yellow lid. It matters more here than at eye level, because this camera sees a
car almost entirely from above and the yellow area is most of what the vehicle
is. The yellow is `#f2c300`, egg yolk, not lemon. Taxis go on the road, never
in an office car park: a third of the parked cars came out yellow once and read
as a taxi rank that was not there.

**Jacarandá is blue-violet, tending to indigo.** The common mistake is pinkish
lilac. If it comes out pink it is wrong.

**The real proportions, for reference, since ours are deliberately not them.**
Jacarandá is only 3.6 % of the city's 432,000 street trees; fresno americano is
36 % and dominant, then plátano, ficus, tilo, paraíso. We run jacarandá at 20 %
because one tree in twenty-eight would not read at all from here, and the point
of the cue is to be seen. That is a knowing exaggeration, not an error.

Rejected for this camera, and worth recording so they are not tried again:
veredas, medianeras, café tables, kioscos, laundry on terraces, fileteado on
the colectivos (the lines are 2–4 cm). All real, all invisible from 1450 m.

Rejected for a different reason — they would read, and they lose to the
reference or to the frame:

- **Water tanks on every roof.** A porteño block carries 30–60 of them and
  they would read at 8 × 20 px. But §5 and §10b of this document say the
  reference's roofs are quiet with one memorable thing on them, and carpeting
  them is the *Silicon Valley* look gone. This is a Buenos Aires built in that
  language, and where the two disagree the language wins.
- **86.6 m blocks.** The porteño block is ~100 varas, and the block-to-street
  ratio is 6.3:1 against our 5.3:1. Ours is 64 m and the title's superblock is
  sized to the word, so changing it moves the thing the whole frame is built
  around.
- **Avenida 9 de Julio at 140 m.** It is 82 % of a 170 m frame. A widened
  avenue at ~52 m with a raised Metrobús platform down the middle would read,
  and is the version to build if it is ever wanted.

## 10d. Movement

Two linear keyframes per object. No rig, no path constraint, no physics: what
sells movement at this scale is the whole frame drifting in several directions
at once, not any single vehicle being convincing.

- Everything in a **lane** shares a speed, so nothing can run into the car in
  front. Variety comes from lane to lane: 7–10 m/s local, 11–14.5 on an avenue,
  3–4.5 for one lane in six.
- **Crossings** are decided before the first frame and can be computed. Hold one
  car back along its own lane until the other has cleared; take off the road
  whatever that cannot settle.
- **People walk along the pavement axis**, and have to be told which axis it is.
- One helicopter, high, in a straight line: the only thing in frame that is not
  on the grid.

## 11. The failure modes to watch for

1. **Grid syndrome** — everything on the same axis at the same height. Fix: street
   hierarchy, varied block sizes, height variety, rotated hero buildings.
2. **Empty roofs** — the single fastest way to look unfinished from this camera angle.
3. **Realistic trees** — breaks the toy contract instantly.
4. **Black shadows** — kills the "brightly lit model" read.
5. **Uniform colour** — every building the same beige. Needs the cool-grey family and
   1–2 saturated buildings per district.
6. **No depth of field** — without it the whole thing reads as a game level, not a
   model.
