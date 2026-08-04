# Style bible — the "toy valley" look

Derived by zooming into the reference frames (`refs/frames`, `refs/crops`), not from
memory. The original sequence was made by yU+co for HBO. We are reproducing the
**look and the city**, not the branding. The company signs are built and the
mountings are copied exactly; the companies on them are invented — section 10b.
The title itself is built, as buildings — section 10.

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
anything: it is 0.284 now. Chroma in this frame comes from what is in it, not
from the view transform.

## 2. Camera

Read off the frames:

- **Verticals are perfectly parallel.** No convergence anywhere in frame, left or
  right edge included. The first pass tried perspective with a camera shift and
  measured 6.5° of lean at 150 mm from 1450 m, so the camera is **orthographic**.
  The reference itself is not: its two title lines sit at different leans, which
  only perspective explains. We take the parallel verticals and give up that cue.
- **Long lens, far away.** Near and far buildings are nearly the same apparent scale.
- **Azimuth 45°** throughout, so every building shows exactly two faces. It never
  moves: it is what the whole grid is composed against.
- **Elevation 30.6°, fixed.** It never moves either. This replaces an earlier
  descent from 38° to 24°, which was a move the reference does not make: tracking
  the clip frame by frame shows the angle constant start to finish.
  The number is measured, and by a better measurement than the one it replaces.
  A ground line along +x projects to a screen line with tan θ = sin e · cot(az),
  and along +y with tan θ = sin e · tan(az); a gradient-orientation histogram over
  the whole frame puts the two ground axes at +28° and −26°, and the product of
  the tangents gives sin e while the ratio gives the azimuth (46.2°, near enough
  to our 45). That is a statistic over every edge in the image. The 22.5° that
  used to justify 24° came from the aspect of one red roof box read off by eye,
  and it was wrong.
  Every straight street runs diagonally across frame; nothing is axis-aligned to
  the image.
- **The move is a straight line at a constant apparent speed, then a hold.**
  Nothing rotates: with the azimuth and the elevation both fixed, the camera is a
  pure orthographic dolly, so its path in world space is a straight segment and
  the only other animated value is the frame width. Twenty-two seconds of
  movement, two seconds frozen on the title.
- **The shot is lateral first and a zoom second.** 320 m of travel, which is
  1.84 frame widths against the reference's 0.65 — nearly three times as much
  ground — while zooming only ×1.48, the reference's own ratio. An earlier version had
  almost exactly the reference's travel and ×2.35 of zoom, and read as a zoom
  with a bit of slide, which is what it was. Travel and zoom are two numbers and
  only their ratio carries the character.
- **Its length is set by the size of the title, not by taste.** The word is 98 m
  wide on screen against a 170 m final frame, so starting with it outside the
  frame and passing the Obelisco costs 1.84 frame widths of travel, and the
  reference pans at 0.05 to 0.10 frame widths per second. Those multiply out. There is no ten-second
  arrangement that both starts with the title off frame and moves at
  the reference's apparent speed; speeding the result up afterwards is a decision
  that can still be made, and a move that whips is not one that can be undone.
- **The pan is tied to the zoom: the camera advances in proportion to the current
  frame width.** This is the one thing that separates a move that glides from a
  move that creeps and then rushes, and it was got wrong first. A pan that is
  linear in metres cannot look linear in a shot that is closing, because the same
  metres cover more of a narrower frame; measured on our own render, the apparent
  speed accelerated from 0.005 to 0.083 frame-widths per second while the
  reference held 0.07 flat. Fitting dx/dq ∝ Wⁿ over the body of the reference
  puts **n at 1.10**, and n = 1 fits ten times better than the n = 0 we had.
- **It crosses the Obelisco, and that is what costs the diagonal.** The
  reference's travel climbs 36.3° across the screen; ours is flat, a pure lateral
  slide, because the Obelisco and the title lie along the screen horizontal.
  Scanning every heading that ends on the title and puts the monument in frame
  gives a range of 0° to 13° and nothing above it, and at 13° the monument is cut
  by the top edge. How far back the shot can start is a ceiling and not a
  preference: the Obelisco is 177 m from the south edge of the city, and past
  360 m of travel the bare site shows in the top left corner of the opening frame.
  320 m was the longest run that rendered full of city.
- **A landmark that is not in the corridor is not in the film.** The shot crosses
  13 of the 81 blocks, so where a monument sits has to be checked against the
  *path*, not against the hero still. The Floralis was placed at the far corner of
  the city by a rule written for a single frame and spent the whole move 2.83
  frame half-widths outside it. It is at (5, 3) now, on the axis and centred at
  54 % of the move. Four of the six built landmarks are still outside.
- **The title starts outside the frame and the camera brings it in.** It first
  touches the frame at about 45 % of the move and is fully inside by 84 %. The
  reference looks like this too and gets there a different way: its letters pop in
  one at a time and out of order, so they are animated, not revealed. Ours cannot
  pop in — they are twenty-four buildings — so the camera has to do the work, and
  that is what forces the long travel.
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

**The stadium is El Monumental**, and four things carry that at 80 px, in the
order they survive being small:

1. **White seats with big red chevrons.** Every photograph of the place, 1978 or
   last week, is white and red zig-zags. It is the only cue the size of the
   whole building, so it reads first. The pattern is painted per (segment, tier)
   rather than with a texture, because at this scale the tiers *are* the pixels:
   nine up the rake, forty-eight round.
2. **A dark facade, and it has to be most of the height.** From outside, the
   ground is a dark banded drum with a white crown, and the white and red is
   what you see over the crown and down inside the bowl. This is the cue that
   took three passes, and none of them was about hue. A pale wall under a pale
   rake reads as one smooth drum; four advertising bands on that wall turn the
   drum into a hoarding; splitting it into a low dark facade and a tall light
   shell puts the light half straight back on top. Proportion, then trim.
3. **A ring that is not uniform**, lower at one end — what is left of the
   horseshoe the ground was until the Centenario stand closed it in 1978. The
   dip faces +x so this camera looks down into the bowl through it.
4. **An oval rather than a circle**, roofed the whole way round, with the
   scoreboard slung on two red columns over the far end.

The pitch is a rectangle inside the oval — a round pitch in a round surround is
a bullseye. The roof cantilevers 3.8 m and no more: an earlier one reached 7.6 m
and turned the stadium into a covered dish, because a camera at 30° sees the
rake, and the rake is the only reason to model a stadium instead of a drum.

This is the ground **as it is now**: the 2023–24 remodelling lowered the pitch
and took the athletics track out. `TRACK` in `06_landmarks.py` puts the track
back for the configuration the place had for most of its life; everything else
is shared, since the remodelling rebuilt the inside of the bowl and left the
drum around it alone.

One trap worth carrying beyond the stadium: `pbrmat` returns an existing
material **untouched**, and the city's materials live in `city.blend` with a
fake user. Editing a colour in a script therefore changes nothing on a rebuild —
the render simply keeps the old look, and nothing raises. `06_landmarks.py`
wraps it in `repaint()`, which forces the base colour so the file wins over the
`.blend`.

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

Two more formats — the rooftop **billboard** and the **medianera** mural —
exist only along the Avenida 9 de Julio, and are in §10b-1 below, because what
governs them is a law rather than a reference frame.

Every one of these mountings has to stand clear of what the facade already
carries. **These facades have a shade frame 0.45 m proud and are published
0.45 m out**, so anything mounted closer is inside the building it is mounted
on. That is why the letters needed 1.05 m and why a mural cannot use the 0.2 m
that is honest for real paint on real bricks.

The mark is a silhouette and nothing else — a disc, a ring, a square, a
triangle, a chevron, three bars. At this distance there is no such thing as a
detailed logo. Saturated face, flat ink, matte: nothing here is emissive.

Roof units and signs compete for the same roof, and the sign wins. Whatever
places the units has to know where the sign is going first.

### 10b-1. The avenue advertising

9 de Julio is not lit by the same trade as the office park, and what it may
carry is not a matter of taste. **GCBA Ley 2936 de Publicidad Exterior** is
what gives the real avenue its face, and three of its articles decide the look:

- **Art. 12.16.2 prohibits structures on roofs and terraces** along the
  stretches that take in 9 de Julio. So the format that reads as this avenue
  is the painted **medianera**, not the rooftop hoarding. The mural is the
  common thing here and the board the exception - about three to one. Built
  the other way round, at fourteen boards to twelve murals, it was a
  convincing picture of a different avenue.
- **Art. 5.4.b: a mural may cover half the visible party wall.** No cap in
  square metres at all - it scales with the wall, which is why these are
  enormous and why an invented 34 m ceiling was holding the big ones back. A
  20 x 30 m wall is entitled to 300 m² of mural.
- **Art. 5.5 caps a rooftop sign** at 100 m² over 15 m of building, 80 m²
  over 10 m, 60 m² below that, with no more than 10 m of structure above the
  roof. A 20 x 8 board is 160 m² and was over the largest allowance by sixty
  per cent.
- **Art. 5.8 fixes the panel module at 1.09 x 1.48 m** and multiples of it.
  The murals are snapped down to whole modules. It costs nothing - rounding
  down can never break a fit that was already checked - and it is the
  difference between Argentine proportions and arbitrary ones.

The two formats:

- **Billboard.** A panel 12-20 m wide and 5-8 m tall, at most 100 m² of face,
  standing on legs about 4 m clear of the roof deck on a visible steel frame
  with a catwalk under it. Turned to face the camera, not the avenue: the real
  ones are aimed at the traffic, and from azimuth 45 the traffic is the lens.
  Rotation 135 degrees, the same number the mast disc needed. Rare here.
- **Medianera.** A mural filling a blind party wall, up to half of it, hung
  from just under the parapet rather than stood on the ground: once the area
  is capped the panel no longer reaches both ends of the wall, and the half
  worth keeping is the top one, which is the half that clears whatever stands
  in front of it. One flat panel, one mark, no letters: the artwork is a
  texture that goes on later. The common format on this avenue.

A mural does not start at the same height on the two banks. The entrance
canopy reaches 2.8 m off the wall at z 3.1-3.5, and `wing()` only ever builds
canopies on the ±y walls - so the east-bank mural, which is on +y, starts at
6.1 m, and the west-bank one, which is on +x, runs down to 2.2 m the way a
real medianera does. One number for both threw away four metres of every west
wall and, with the area cap in, refused every two-floor building on that side.

The two banks of the avenue are not symmetrical and cannot be made so. West of
it a building's avenue wall is its **+x** wall, which this camera sees. East of
it the avenue wall is a **-x** wall, which is the back of the building however
well it is built, so the mural there goes on the **+y** wall facing the cross
street. A real medianera on that side is exposed to the cross street too, so
this is a constraint the geometry hands over rather than a compromise.

A mural is painted flat on its wall in life, and cannot be here: the facades
carry a shade frame 0.45 m proud and are published 0.45 m out, so the panel
stands off at the same 1.05 m the parapet letters use.

The brands on these are invented too, and drawn from a different list -
drink, bank, phone, football - so the office park does not start selling soda.
Unlike the company signs, each avenue sign gets its **own** material rather
than one shared per brand: these are the ones real artwork is going onto, and
repainting one wall must not repaint four others.

## 10c. What makes it Buenos Aires

The test is whether it survives being twelve pixels tall from a high oblique
view. Almost nothing that makes the city recognisable at eye level does: the
tiled pavements, the cafés on the footpath, the kiosks, the painted party walls
are all invisible from here. Silhouette and colour are what is left.

| Cue | Why it survives |
|---|---|
| **Ochavas** — every block corner cut at 45° | the best of the lot, and it is not a prop: Buenos Aires cuts every street corner by code, so no block downtown has a 90° corner and every crossing opens into an octagon. Four bevels per block. With square corners the grid reads Manhattan |
| **The Avenida 9 de Julio**, 52 m, with planted medians and a Metrobús corridor | the second best, and for the same reason as the ochava: it is structure, not a prop. Nothing else in the city is 52 m of anything |
| **Jacarandás in flower** | violet against green reads at any size. One street tree in five; at one in two the city turns into a fantasy |
| **Taxis**, black body, `#f2c300` roof | this camera sees mostly roof, and the roof is the livery |
| **Colectivos**, flat two-tone per line | a small bright rectangle among the cars |
| **The Obelisco**, 67.5 m on a 6.8 m base | taller than every building here, so it is the only vertical in frame |
| **Floralis Genérica**, six 20 m petals and four stamens, 32 m across, over a 44 m pool | the only polished thing in the city, and the pool is what makes its plaza read |

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

**The Floralis is a BOWL, and every wrong version got there a different way.**
It took four attempts and a photograph. The petal is a *scoop*, not a leaf:

- **The section is a circular arc**, half-angle ~52°, curling towards the axis.
  Flat is a six-pointed star, whatever the file calls it. A shallow parabolic
  dish is a flat blade with a crease. A *deep* parabolic dish is worse than
  both — a parabola keeps steepening, so the edges shoot up into two spikes and
  the petal comes out a folded paper dart. An arc has constant curvature and
  reads as sheet metal bent on a roller, which is what it is.
- **It widens towards the tip**, which is broad and rounded. Narrow at the
  root, widest at the very top. Widest-at-40 %-with-a-point is a leaf.
- **The tangent at the tip decides bowl versus umbrella.** Radius easing off
  (t^0.8) against height accelerating (t^1.5) leaves the tip at ~60° above
  horizontal: a wide shallow floor turning up into near-vertical walls. Reach
  the tip with dz/dt = 0 and every petal finishes by flattening outward — a
  blown-out umbrella.
- **Width is two thirds of the available arc.** Six petals at a 16 m radius
  have 16.7 m of arc each. Half of that leaves sky between them: a star. All
  of it closes the gaps into one continuous vessel: a cup. The **V-shaped
  notches between petals have to be visible** — they are what says six petals.

**And there are four stamens.** They were missing entirely, and they are what
makes it *that* flower rather than a generic metal one. They have to clear the
petals by real height — at 2 m of overhang they are a smudge in the middle of
the bowl from the hero angle.

The stem height is not free. A 20 m petal reaching 16 m out and 23 m up has to
start around 9.5 m or the arithmetic does not close: the straight line from a
5 m root to the tip is already 23 m. That is why the real flower sits up in the
air on a stalk, and getting it wrong makes a desk ornament.

**The real proportions, for reference, since ours are deliberately not them.**
Jacarandá is only 3.6 % of the city's 432,000 street trees; fresno americano is
36 % and dominant, then plátano, ficus, tilo, paraíso. We run jacarandá at 20 %
because one tree in twenty-eight would not read at all from here, and the point
of the cue is to be seen. That is a knowing exaggeration, not an error.

**Cúpulas were built and then removed, and the reason is the useful part.** A
dome is a real cue and it does survive this camera — a dome is a silhouette,
not a texture. It was built as domes scattered across roofs at a fixed rate,
which looked wrong. The first fix was to put each one on an actual street
corner rather than a random corner of a published box — correct, and still not
enough. **What was missing is that a cupola belongs to a kind of building.** It
crowns an academic pile with a mansard and a corner rotunda; stuck on a flat
modern office block it reads as a hat on the wrong head however carefully it is
placed. Adding a dome is cheap, adding the building it belongs to is a
different job, and until that job is done there are none — a cue that reads as
a mistake is worse than an absent cue.

Rejected for this camera, and worth recording so they are not tried again:
veredas, café tables, kioscos, laundry on terraces, fileteado on the colectivos
(the lines are 2–4 cm). All real, all invisible from 1450 m. (Medianeras were
on this list and have come off it — see §10b. What was rejected was the blank
painted party wall as texture; what works is the advertising mural, which is
20 m of flat colour and reads perfectly well.)

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
- **Avenida 9 de Julio at 140 m.** It is 82 % of a 170 m frame. The 52 m
  version is now built, and the section is the whole trick — see below.

**The Avenida 9 de Julio: the width is set by one relationship, not by taste.**
70 m against a real 110 (140 counting the lateral streets). The number that
matters is not the absolute one — it is that **the real avenue is wider than a
city block**, 110 m against a porteño block of about 100. Being *narrower* than
a block is precisely what stops a wide road from reading as the widest avenue
in the world. Our blocks average 64 m, so 70 is the smallest width that keeps
the relationship, and the relationship is the whole cue. The first attempt was
52 m and it is a wide avenue and nothing else.

The section, all of it inside the street gap because the pavements belong to the
blocks:

| from the west building line | |
|---|---|
| 0 – 19 m | lateral carriageway, five lanes, one way |
| 19 – 28 m | planted median |
| 28 – 42 m | Metrobús corridor: bus lane, 7 m platform, bus lane |
| 42 – 51 m | planted median |
| 51 – 70 m | lateral carriageway, five lanes, the other way |

**The bus corridor stays at 14 m however wide the avenue gets.** Four exclusive
lanes are 13–14 m and that is sourced; it is not a proportion of anything. An
early attempt gave it 16 m against 10 m carriageways and from above that reads
as a dark canal with two service roads beside it. It is the wrong way round —
what makes the avenue enormous is the asphalt, and the busway is a thin thing
laid down the middle of it.

**The Metrobús, all sourced (GCBA):** it runs *with* traffic, not counterflow;
four exclusive lanes, two per direction; down the centre of the avenue, on the
central medians that were cleared for it. The platform is a central island
between the two directions, roofed, and raised **40 cm** — the height is the
reason the platform exists, because the buses board level. The corridor is 3 km
with 17 stations, which is **175–185 m apart**, or one station every three
blocks at our size. (The central-island layout won over lateral platforms
because it cost 249 trees against 893.)

The medians are not decoration either. A 52 m sheet of asphalt is a runway; the
same width striped along its length — carriageway, trees, buses, trees,
carriageway — is legible as structure instead of as absence. The jacarandá is
over-represented in the median rows on purpose, because the real avenue is one
of the places people go to see them.

**The shelters run the length of the boulevard** — up to two per block, 22 m
each, always clear of the intersections by 5 m. This is a deliberate departure
from the sourced number: the real corridor is 3 km with 17 stations, 175–185 m
apart, or one every three blocks at our size. One every three blocks is what
the timetable says and it leaves the median empty; a shorter shelter repeated
along it is what the avenue *looks* like. Recorded here as a departure so
nobody re-derives the spacing from the source and "fixes" it.

They are **dark grey with one white line down the roof**. Pale, they were the
brightest thing on the avenue and pulled the eye off the monument. Dark, they
sit into the asphalt — and then a dark rectangle on dark asphalt is a hole, so
the white line is not decoration: it is the entire reason the shelter reads.

Each gets a 4.4 m totem at one end and a zebra reaching it from both medians.
Without the totem a station is a paving slab seen from directly above, and this
camera is looking for silhouettes; without the crossing it is an object dropped
in the road, because nobody could walk to it. One totem, not two: two on a 22 m
shelter, twice per block, is a picket fence down the middle of the avenue. The
canopy oversails the platform by **1.2 m and no more** — at 3 m it is 13 m of
roof over a 7 m platform with none of it visible from above, which reads as a
lid rather than as a station.

**Plaza de la República is an oval, 60 × 31 m**, and it is not a plaza beside
the avenue: the two directions of the 9 de Julio **separate and pass around
it**, which is what the real one does since the 1971 layout.

**It sits mid-block, not on a crossing**, and that is a correction. The real
one is at a junction — Corrientes and Diagonal Norte, both 33 m against the
avenue's 140 — so it went on a crossing first. It does not work, because our
crossings are crossings: the cross street runs straight through the island, so
traffic drives over the plaza and through the monument. The real Corrientes
does not do that; it was diverted in 1971 and bends around the Obelisco, which
makes the plaza a hole in the traffic rather than a junction. Mid-block gives
the same read and none of the geometry.

**The oval is the point, and it took a photograph to see it.** Built as a
rectangle of the same dimensions it reads as a widening of the road; built as
an oval it reads as a place in it. It is also **the only curve anywhere in this
city** — the grid is strictly rectangular and even the ochavas are straight
cuts — so the eye finds it before anything else in frame, and it costs one
polygon function.

Four things dress it, off the photograph, and none of them is a paving pattern:

| | |
|---|---|
| **Red tile border**, ~3 m all round | after the monument itself this is the strongest element in the photograph: a saturated ring against grey asphalt and green median, and the only red on the ground anywhere in the city |
| **Two curved planting beds**, one in each end | what stops the island from being a car park with a spire on it. Ours are ovals rather than the real crescents — two pixels of difference and a crescent costs a boolean |
| **The flagpole**, 18 m, at the south end | 18 m of vertical in a frame whose only other vertical is the monument, and the cue that says which country this is without any text. Turned to +135° like the mast discs: a flag hung along a world axis is edge-on to a camera at azimuth 45 and vanishes into a line |
| **The 24 provincial shields**, on a 9 m ring | on the monument's own apron, between the two beds. At 12 m a third of them ended up in the grass |

The beds go into the **ground** mesh, not the monument mesh. A 26 cm kerb is a
floor, and built as a solid it made the overlap check report a bus and two
people standing inside a planting bed — true, and useless. Same call as was
already made for the plaza paving. The flagpole is a solid and is published.

**The trees.** The real medians are dominated by palo borracho, jacarandá and
tipa — the transplant census for the Metrobús works moved 154 palos borrachos,
93 jacarandás, 33 lapachos and 6 tipas. We have no palo borracho in the kit, so
the median rows run jacarandá-heavy, which is a knowing exaggeration in the same
direction as the street trees and for the same reason: it is the one of the
three that reads at this size.

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

**Argentina drives on the right, and one lane table cannot serve both axes.**
Heading +x the driver's right hand points at −y, so the +x traffic belongs on
the negative side of the street; heading +y it points at +x, so the +y traffic
belongs on the positive side. The two axes have opposite handedness about the
offset sign. Written once and used for both, the Y streets came out correct by
luck and the X streets came out British.

This is worth its own paragraph because of how invisible it is. Every single
street is internally consistent — two lanes, opposite directions, evenly spaced
cars — and looks completely plausible on its own. The only ways to see it are
to pick one car and follow it through an intersection, or to count. There is
now a check that counts: `95_check_traffic.py`.

On the 9 de Julio the unit is not the street but the **carriageway**. Each
lateral is one way, like Cerrito and Carlos Pellegrini, so what has to agree
with the direction is which side of the avenue the carriageway is on — the
+y carriageway is the one on the +x side. And the bus corridor is for buses:
a bus lane with cars in it is not a bus lane, and the corridor is the one part
of the avenue a viewer can actually name.

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
