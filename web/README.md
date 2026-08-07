# The city, in a browser

The same city as `renders/city.blend`, running at 60 fps in WebGL: the same
geometry, the same traffic, the same camera move, and a look measured against
the same reference as the render.

```bash
./bl scripts/city/20_export_web.py     # from the repo root: publish the city
cd web && npm install && npm run dev   # http://localhost:5173
```

Re-run the export after any change to the `.blend`. Nothing else needs to
change: the browser has no copy of the palette, the grade, the camera path or
the traffic, it is handed all four.

## What it costs

| | |
|---|---|
| `city.glb` | 3,3 MB (Draco) — 172 meshes, 180 materials |
| `city_motion.json` | 0,26 MB — 1784 objects, 4190 keys |
| `city_sky.exr` | 0,08 MB — the baked world |
| On screen | 427 draw calls, 28.215 instances, 60 fps on an M4 Pro |

## How it is put together

    20_export_web.py  ->  public/            ->  src/
    ────────────────      ──────────────         ─────────────────────────────
    the .blend            city.glb               city.js    geometry, instances
                          city_motion.json       shot.js    the camera move
                          city_shot.json         post.js    the look
                          city_sky.exr           measure.js the five numbers
                                                 main.js    the loop

**`city.js`** collapses 8131 nodes into ~200 `InstancedMesh` grouped by
geometry and material. Added as they come, the glb is 8131 draw calls and about
12 fps.

**`shot.js`** does not re-derive the camera move. `_common.shot_at()` is eased
time over an exponential zoom tied to the pan; the export samples it once per
frame and this reads the row. Two implementations of that easing is exactly the
kind of shared number `docs/city/MAP.md` exists to prevent.

**`post.js`** is `07_look.py`'s compositor in one fullscreen pass, in the order
Blender uses: blur from the depth buffer, grain, vignette, white balance,
exposure, then AgX last. `BLUR_MAX`, `FOCUS_SPREAD`, `GRAIN` and `VIGNETTE` are
read out of `07_look.py` by the export, not copied.

## The look does not match the render, and that is the decision

`post.js` ships `TONEMAP = "none"`: linear light straight to the display,
clipped. The `.blend` goes through AgX, which rolls the highlights off and
desaturates as it does it — right for a frame in a film, dark and muted for a
toy city you can spin. The web trades the rolloff for a lit, open picture, and
`?nopost=1` is the reference for it.

Setting `TONEMAP = "agx"` in `post.js` gets the render's grade back, measured
and within tolerance on all five numbers. Everything else in the chain is the
same either way: the miniature blur, the grain, the vignette and the white
balance do not touch chroma.

```js
window.measure().table       // from the console, any time
```

|                | mean  | std   | dark  | bright | sat   | R/B   |
|----------------|-------|-------|-------|--------|-------|-------|
| the render     | 0.470 | 0.247 | 24.0% | 15.5%  | 0.388 | 1.329 |
| `TONEMAP` agx  | 0.471 | 0.255 | 23.0% | 15.0%  | 0.400 | 1.320 |
| `TONEMAP` none | 0.609 | 0.252 | 4.9%  | 33.0%  | 0.263 | 1.134 |

The same five numbers `_common.GRADE` was fitted with. The shipped row misses
the reference on purpose and the table says by how much, so it stays a decision
rather than becoming a drift. Cycles also bounces light where a rasteriser does
not, so `EXPOSURE_OFFSET` and `ENV_INTENSITY` put back what that costs.

One thing that is not a preference: the pass converts linear light to sRGB
itself, because three.js does that for its own materials and cannot do it for a
raw `ShaderMaterial`. Without it the page renders 0.18 darker in the mean with
its shadows crushed — and, misleadingly, *more* saturated, since the missing
gamma pulls the channels apart. It looks like a grade. It is a bug.

Try a grade before committing to it: `?ev=0.4&env=1.3&contrast=1.2`.

## The video

```bash
npm run record                        # capture/city.mp4 + capture/city.mov
npm run record -- --w 3840 --h 2160   # 4K
npm run record -- --ss 1 --to 24      # a one-second test, in seconds
```

624 frames, 26 s, 24 fps, in about two and a half minutes on an M4 Pro. It
starts its own Vite on port 5199 and its own headless Chrome with a throwaway
profile, so it touches neither a dev server you have open nor your browser.

**A screen recording is a different picture and that is why this exists.** The
page draws at whatever rate the machine manages and a recorder samples at
whatever rate IT manages, so a missed browser frame becomes a repeated video
frame and a missed recorder frame becomes a dropped one. The pan judders and
the traffic stutters in the file even though nothing on screen ever did. This
has no clock at all: the recorder asks for frame *n*, waits however long it
takes, and asks for *n+1*. 624 frames go in and 624 frames come out.

Three things it does that a recorder cannot:

- **The frame is not the window.** `viewW/viewH` replaced `innerWidth/
  innerHeight` throughout `main.js`, so 1920×1080 comes out of whatever window
  a headless browser opened.
- **It supersamples.** `--ss 2` draws at 3840×2160 and ffmpeg scales down with
  lanczos. That downscale is the only antialiasing there is — the page runs
  `antialias: false` because the post chain's half-float target cannot carry
  MSAA — and it is a bigger quality difference than the output resolution:
  1080p at `--ss 2` reads better than raw 4K at `--ss 1`.
- **Time comes from the frame number.** `(n / fps) * 1000`, so the grain is the
  same on a re-run and a slow frame does not become a long one.

No frames are written to disk: `vite-plugin-capture.js` pipes the PNGs into one
ffmpeg with two outputs, and the page's fetch does not resolve until ffmpeg has
taken the bytes, which is the backpressure. `city.mp4` is H.264 CRF 14 for
sending; `city.mov` is ProRes 422 HQ for an edit, where a title over 4:2:0
long-GOP would soften.

**It waits for the sky.** The EXR loads on a callback and it is the fill light,
so a capture that starts before it resolves opens on a darker, contrastier city
— frames that measure fine because nothing measures them.

The video ships the page's look, not the render's: `TONEMAP = "none"`. For the
film grade, set `TONEMAP = "agx"` in `post.js` and record again.

## Diagnostics

```
?stats=1      fps, draw calls and instance counts, bottom right
?nopost=1     draw without the post chain
?noshadow=1   drop the shadow pass
?taps=8       cheaper depth of field
?shadow=2048  smaller shadow map
```

From the console: `window.city`, `scene`, `camera`, `controls`, `post`,
`renderer`, `look.env(x)`, `look.exposure(x)`, `look.contrast(x)`,
`measure(frame)`.

## Controls

Space plays and pauses, `F` swaps between the shot and a free orbit, the slider
scrubs. The two buttons are Lucide icons and each one shows the action it
performs rather than the state it is in — playing shows a pause, the shot shows
an orbit. The frame counter is diagnostic and hidden; `?stats=1` brings it back
along with the rest.

**When the move lands, the camera is handed over.** The shot ends on the
approved hero framing after four seconds held on the title, which is the right
place to start exploring from, so free orbit turns itself on there rather than
looping the move. The city keeps running underneath — step 11's traffic is 26
seconds long and it loops — because orbiting a frozen city is orbiting a
photograph.

### The fence around free orbit

The site is a finite sheet with a city in the middle of it, so an unfenced
orbit spends most of its travel over bare ground, and below the horizon it
finds the city floating on a slab. Three limits, and they are coupled because
the failure is:

| | |
|---|---|
| **angle** | 24° to 82° above the ground. At 8° the frame is half sky with the cut edge of the map across it |
| **width** | at most `min(700 m, city × sin(elevation) × aspect)` — a tilted frame covers `height/sin(elevation)` of ground, so a 700 m frame at 24° is 980 m deep and the cap has to fall with the camera |
| **position** | inside the built rectangle, shrunk by how far the view reaches. A frame that covers the whole city collapses to its centre, because there is nowhere else for it to be |

The rectangle is not a scene bounding box: `20_export_web.py` measures it off
the 533 published footprints, so it is where the city *is*, not where the
ground sheet ends. It travels in `city_shot.json` as `bounds`.

The depth of field follows the angle too. `FOCUS_SPREAD` is the depth that
stays sharp at the hero angle; free orbit needs four times that at 24° and less
than that overhead, where what varies in depth is the buildings rather than the
ground. `frameDepth()` in `post.js` covers both, and evaluates to exactly
`FOCUS_SPREAD` at the hero frame, so the shot is untouched by any of it.

## If something looks wrong here and right in the render

Suspect the winding first. A rasteriser with backface culling draws the near
face and drops the far one; a path tracer shades both and never complains. Until
`_common.box()` and `.sphere()` were fixed, 100 of the 118 closed meshes in the
.blend were wound inside out, and the roof signs flickered here for it — the
plate's underside was the face being drawn, and it lies exactly on the roof.

`./bl scripts/city/92_check_zfight.py` finds faces sharing a plane across the
whole city. And to see what this page sees without opening it, set
`use_backface_culling = True` on every material in Blender and render: same
question, one second, no browser.

## What the browser does not do

The traffic runs for 26 seconds and loops, because that is the length of the
shot in the `.blend` — the cars are not simulated here, they are Blender's
keyframes interpolated. Making it run forever means porting `11_animate.py`,
not extending this.
