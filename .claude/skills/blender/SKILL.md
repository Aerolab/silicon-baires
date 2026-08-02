---
name: blender
description: Create, modify and render 3D scenes in Blender 5.2 from headless Python. Use whenever the task touches modelling, materials, lighting, geometry nodes, animation, renders, or glTF/web/video export in this project. Covers the `blib` library and the Blender 5.x API changes that break code written from memory.
---

# Headless Blender 5.2

Blender is driven **by script, never by eye**. The loop is always the same:

```bash
./bl scripts/something.py
```

and then **look at the PNG with the Read tool**. There is no way to validate a render
without seeing it: framing, exposure and material mistakes raise no exception, they
just come out ugly and exit 0.

## The loop, in order

1. Write the script in `scripts/`, always starting with `blib.reset()`.
2. Run it. If the script calls `blib.report()`, you see what is actually in the scene.
3. **Read the resulting PNG.** Use `blib.contact_sheet()` when the shape matters from
   more than one angle.
4. Iterate in EEVEE (~0.7s), switch to Cycles only for the final image.

Never hardcode camera positions or light power: `blib.camera()` and `blib.three_point()`
derive them from the real geometry and work the same on a 2cm object and a 100m one.

## blib — the project library

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bpy, blib
```

| Function | Purpose |
|---|---|
| `reset(world_color, world_strength)` | empty reproducible scene. Always first |
| `camera(target, azimuth, elevation, distance, lens, margin, ortho)` | frames itself by projecting the evaluated geometry |
| `three_point(target, strength, key_azimuth, softness)` | key/fill/rim rig scaled to scene size |
| `light(kind, location, energy, size, target)` | single light aimed at a point |
| `hdri(path, strength, rotation, visible)` | world from an HDRI or studio grey |
| `pbr(name, base_color, roughness, metallic, coat, transmission, emission…)` | Principled material with 5.2 socket names |
| `emissive(name, color, strength)` | emissive material |
| `assign(obj, mat)` | assign a material |
| `render(path, engine, samples, resolution, transparent, view_transform, look)` | render a PNG, returns the path |
| `contact_sheet(path, views)` | several views of the same subject |
| `gn_tree(name, inputs)` / `gn_apply(obj, ng, **vals)` / `gn_set(mod, name, val)` | geometry nodes |
| `sockets(node)` | the **usable** sockets of a node (see gotcha below) |
| `turntable(obj, frames)` / `render_video(path, fps, codec)` | animation |
| `export_glb(path, draco)` / `save(path)` | export and .blend |
| `report()` | what is in the scene: objects, polys, materials, lights, bounds |

Prefer **the data API** (`bpy.data.*`) over operators (`bpy.ops.*`): in background mode
operators depend on context and fail in confusing ways. Reasonable exceptions:
`primitive_*_add`, `shade_smooth`, `render.render`, the exporters.

## The five Blender 5.2 gotchas

All verified against the installed Blender, all of them break code written from memory.

1. **`BLENDER_EEVEE_NEXT` does not exist.** The engines are `BLENDER_EEVEE`, `CYCLES`,
   `BLENDER_WORKBENCH`.
2. **`action.fcurves` is gone** (slotted Actions). Curves live in
   `action.layers[].strips[].channelbag(slot).fcurves`. Use `blib.fcurves(obj)`.
3. **Geometry nodes modifier inputs changed**: it used to be `mod["Socket_2"] = v`,
   now it is `mod.properties.inputs["Socket_2"]["value"] = v`. Use
   `blib.gn_set(mod, "Density", v)`.
4. **For video you must set `image_settings.media_type = "VIDEO"` BEFORE**
   `file_format = "FFMPEG"`, otherwise the enum does not even list it.
5. **Sockets with `enabled=False` disappear from name lookup** while still showing up
   when iterating. Example: with `distribute_method="POISSON"` there is no
   `inputs["Density"]`, it is `inputs["Density Max"]`. When in doubt, `blib.sockets(node)`.

Principled BSDF socket names also changed in 4.x: there is no bare `Specular`,
`Subsurface`, `Sheen`, `Clearcoat` or `Transmission`. See `references/api-5.2.md`.

## Which engine to use

Measured on this machine (M4 Pro), 960×540, simple scene:

| Config | Time |
|---|---|
| EEVEE 64 spp | **0.65 s** |
| Cycles GPU 512 spp | 3.2 s |
| Cycles CPU 128 spp | 5.3 s |
| Cycles GPU, first render of the process | +10 s (compiles Metal kernels) |

EEVEE to iterate, Cycles GPU (Metal, already handled by `blib.use_gpu()`) for the final.
That +10s on the first Cycles render is per process: batch the final renders into a
single script instead of invoking Blender many times.

## References

- `references/api-5.2.md` — verified enums, Principled sockets, API changes
- `references/look-dev.md` — color management, lighting, camera, why something looks wrong
- `references/recipes.md` — complete recipes: product, turntable, procedural, web export
