# Look dev — making the render good, not just making it run

Working blind (no viewport), most ugly renders come from four causes. In order of
how often they bite.

## 1. Exposure

Blender works in linear light and the view transform decides how that maps to screen.

| view_transform | When |
|---|---|
| **AgX** | the default. Cinematic, scenes with strong lights. It desaturates highlights on purpose: a saturated red under bright light comes out pastel pink, **that is not a bug** |
| **Khronos PBR Neutral** | product, e-commerce, anything where color must be faithful. Preserves saturation and does not wash out the brights |
| **Standard** | no tone mapping. Only to compare against an exact color, or for UI/compositing |
| **Filmic** | the old 2.8x default. No reason to pick it today |

If the object comes out pure white with no detail, it is blown out: lower `strength`
in `three_point()` or pass `exposure=-1.0` to `render()`. If it comes out dead grey,
raise it. The `blib` rig is calibrated so an albedo 0.8 material sits just below
clipping at `strength=1.0`.

**Light power scales with the square of the distance.** That is why `three_point()`
computes watts from the scene size: copying "500W" from a tutorial written for a 1m
object leaves a 5cm object completely black.

## 2. Framing

`blib.camera()` projects the evaluated geometry onto the camera axes, so it frames
correctly with no intervention. The parameters worth touching:

- `margin` — 1.0 pins the subject to the edges, 1.25 (default) gives air, 1.6 leaves
  it small in frame.
- `lens` — 35mm exaggerates perspective (dynamic, dramatic), 50mm is neutral,
  85-135mm compresses and is what product photography uses because it does not distort.
- `elevation` — 0 is level with the subject, 15-25 is the normal three-quarter view,
  >60 is top-down.
- `azimuth` — 0 is head-on; 35-50 shows two faces and reads volume better.

When unsure, run `contact_sheet()` and look at all four views before deciding.

## 3. Lighting

`three_point()` gives a correct but neutral result. To give it character:

- **Key** defines the shape. More lateral (higher azimuth relative to the camera) =
  more dramatic.
- **Fill** controls contrast. Drop it to `0.1` for a hard look, raise it for advertising.
- **Rim** separates subject from background. It is what makes a dark object read
  against a dark backdrop.
- **`softness`** scales the emitter sizes. Big light = soft shadows and wide
  reflections; small light = crisp shadows and point highlights. For product, almost
  always big.

An HDRI does more for realism than any rig, especially with metallic or reflective
materials, because it gives them something to reflect. `blib.hdri(path)` takes an
`.hdr`/`.exr`; with no file it sets a studio grey. `visible=False` keeps the background
transparent while still lighting the scene (ideal for compositing later).

Transparent background: `render(..., transparent=True)` keeps alpha, and `blib`
switches the PNG to RGBA only in that case.

## 4. Materials

- `roughness` changes how a material reads more than anything else. 0.0-0.15 mirror or
  lacquer, 0.2-0.4 polished plastic, 0.5-0.7 matte, >0.8 chalk.
- `metallic` is effectively binary: 0 or 1. Intermediate values do not exist physically
  except in map transitions.
- A metal with low roughness and nothing to reflect renders black. Always give it an
  HDRI or large emitters around it.
- `coat` (clear varnish) over a colored material gives the car paint / lacquer /
  expensive plastic look.
- Glass: `transmission=1.0`, `roughness=0.0`, `ior=1.45`. In EEVEE it needs
  `surface_render_method="BLENDED"`; in Cycles it just works, and much better.

## Failures that raise no exception

- Black object → no lights, or a metallic material with no environment, or flipped normals.
- Flat white object → blown out, or materials never assigned (Blender's default is a
  light grey 0.8: if everything is the same grey, the materials did not apply).
- Noise/grain in Cycles → too few samples. Raise to 256-512 or enable denoising.
- Hard aliased shadows in EEVEE → raise `taa_render_samples`, or move to Cycles.
- Empty scene rendering grey → the camera ended up inside an object, or `scene.camera`
  was never set. `blib.report()` prints the distance to the center.
