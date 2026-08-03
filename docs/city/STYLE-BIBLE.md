# Style bible — the "toy valley" look

Derived by zooming into the reference frames (`refs/frames`, `refs/crops`), not from
memory. The original sequence was made by yU+co for HBO. We are reproducing the
**look and the city**, not the branding: no company logos, no title type.

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

| | Reference | Where we landed |
|---|---|---|
| Scale | ~14 px per metre → **the frame spans ~140 m** | 210 m |
| Mean luminance | 0.498 | 0.47 |
| Pixels below 0.25 | **15.7 %** | 15.5 % |
| Green coverage | **17.3 %** | 15.1 % |
| Mean saturation | **0.334** | 0.20 |
| Road luminance | **0.18**, and warm (0.20, 0.18, 0.14) | 0.19 warm |

Two of these were badly wrong on the first pass and are worth remembering:

- **The shot is tight.** The first attempt framed 590 m, four times too wide.
  Every piece of detail was then sub-pixel, which reads as "not enough detail"
  when the real fault is the lens.
- **The road carries the whole value structure.** At 0.38 luminance and cool
  grey, the frame had 0.3 % dark pixels against the reference's 15.7 %, and
  nothing else could compensate.

Saturation is still the open gap. The reference fills its frame with foliage,
coloured buildings and props; ours still shows a lot of pale roof and asphalt.

## 2. Camera

Read off the frames:

- **Verticals are perfectly parallel.** No convergence anywhere in frame, left or
  right edge included. That means orthographic, or perspective with camera shift.
  Perspective + shift is the right pick: it keeps a little depth cue that pure ortho
  loses.
- **Long lens, far away.** Near and far buildings are nearly the same apparent scale.
  Estimate: 100–135 mm equivalent, camera several hundred metres out.
- **Elevation ~35–40°**, **azimuth ~45°** so every building shows exactly two faces.
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
- The network is a **rotated orthogonal grid cut by big sweeping curved arterials**
  (radii of 60–150 m) and one or two roundabouts. Those curves are what stop the city
  reading as a spreadsheet, and they are the hardest part to build.
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

## 10. The failure modes to watch for

1. **Grid syndrome** — everything on the same axis at the same height. Fix: curved
   arterials, varied block sizes, height variety, rotated hero buildings.
2. **Empty roofs** — the single fastest way to look unfinished from this camera angle.
3. **Realistic trees** — breaks the toy contract instantly.
4. **Black shadows** — kills the "brightly lit model" read.
5. **Uniform colour** — every building the same beige. Needs the cool-grey family and
   1–2 saturated buildings per district.
6. **No depth of field** — without it the whole thing reads as a game level, not a
   model.
