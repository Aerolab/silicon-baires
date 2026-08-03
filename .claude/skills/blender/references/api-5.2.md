# Blender 5.2 API — verified facts

Everything here came from interrogating the installed Blender (`scripts/_introspect/`),
not from documentation or memory. Blender 5.2.0 LTS, Python 3.13.13.

## Enums that matter

```python
render.engine          : BLENDER_EEVEE | CYCLES | BLENDER_WORKBENCH
                         (BLENDER_EEVEE_NEXT does NOT exist, it was 4.2-4.5 only)
view_settings.view_transform : Standard | Filmic | AgX | Khronos PBR Neutral | Raw | False Color
view_settings.look     : None | AgX - Punchy | AgX - Base Contrast |
                         AgX - Medium High Contrast | AgX - High Contrast | AgX - Greyscale
                         (looks only exist when view_transform = AgX)
image_settings.media_type : IMAGE | MULTI_LAYER_IMAGE | VIDEO
image_settings.file_format : PNG WEBP AVIF JPEG OPEN_EXR HDR TIFF ... (+ FFMPEG if media_type=VIDEO)
ffmpeg.format          : MPEG4 MKV WEBM AVI DV FLASH MPEG1 MPEG2 OGG QUICKTIME
ffmpeg.codec           : H264 H265 AV1 WEBM PRORES DNXHD FFV1 THEORA ...
```

**Dynamic enums lie under introspection.** `bl_rna.properties["engine"].enum_items`
returns an incomplete list in background mode. To learn which values are really valid,
try assigning them inside a `try`.

## The compositor moved into a node group

`scene.node_tree` **no longer exists**. Compositing is a node group hung off the
scene, and several classic nodes are gone:

```python
scene.view_layers[0].use_pass_z = True          # do this first: it adds the socket
ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
scene.compositing_node_group = ng

rl = ng.nodes.new("CompositorNodeRLayers"); rl.scene = scene
out = ng.nodes.new("NodeGroupOutput")           # NOT CompositorNodeComposite
```

| Gone in 5.2 | Use instead |
|---|---|
| `CompositorNodeComposite` | `NodeGroupOutput` |
| `CompositorNodeMixRGB` | `ShaderNodeMix` (`data_type="RGBA"`; sockets `[0]` fac, `[6]`/`[7]` A/B, output `[2]`) |
| `CompositorNodeMath` | `ShaderNodeMath` |
| `CompositorNodeTexture` | `CompositorNodeImageCoordinates` + `ShaderNodeTexWhiteNoise` |

Shader nodes work inside a compositor tree now. `CompositorNodeBlur` lost
`filter_type` and `size_x/size_y`: both are input sockets (`Type`, `Size`), and
because `Size` is a socket you can link an image into it for a **variable
blur** — which is how you fake depth of field on an orthographic camera, where
`CompositorNodeDefocus` produces nothing at all.

## Sky Texture — Nishita was renamed

```python
sky.sky_type = "NISHITA"        # TypeError on 5.2
sky.sky_type = "MULTIPLE_SCATTERING"   # this is the Nishita model now
```

Valid values: `SINGLE_SCATTERING`, `MULTIPLE_SCATTERING`, `PREETHAM`,
`HOSEK_WILKIE`. `dust_density` also became `aerosol_density`. The rest of the
properties kept their names: `sun_elevation`, `sun_rotation`, `sun_disc`,
`sun_intensity`, `altitude`, `air_density`, `ozone_density`.

## Principled BSDF — exact socket names

```
Base Color, Metallic, Roughness, IOR, Alpha, Thin Wall, Normal, Weight,
Diffuse Roughness,
Subsurface Weight, Subsurface Radius, Subsurface Scale, Subsurface IOR, Subsurface Anisotropy,
Specular IOR Level, Specular Tint, Anisotropic, Anisotropic Rotation, Tangent,
Transmission Weight,
Coat Weight, Coat Roughness, Coat IOR, Coat Tint, Coat Normal,
Sheen Weight, Sheen Roughness, Sheen Tint,
Emission Color, Emission Strength,
Thin Film Thickness, Thin Film IOR
```

Translation from the old 3.x code still circulating online:

| Before (3.x) | Now |
|---|---|
| `Specular` | `Specular IOR Level` |
| `Subsurface` | `Subsurface Weight` |
| `Transmission` | `Transmission Weight` |
| `Sheen` | `Sheen Weight` |
| `Clearcoat` | `Coat Weight` |
| `Clearcoat Roughness` | `Coat Roughness` |
| `Emission` | `Emission Color` |

`blib._set()` raises `KeyError` listing the available sockets when a name does not
exist, which beats failing silently.

Transparency in EEVEE: besides lowering `Alpha` you must set
`mat.surface_render_method = "BLENDED"` (`blib.pbr` does it automatically when
`alpha < 1` or `transmission > 0`).

## Slotted Actions (4.4+) — `action.fcurves` is dead

```python
# BROKEN in 5.x:
for fc in obj.animation_data.action.fcurves: ...

# Correct:
ad = obj.animation_data
for layer in ad.action.layers:
    for strip in layer.strips:
        if strip.type == "KEYFRAME":
            cb = strip.channelbag(ad.action_slot)
            for fc in cb.fcurves: ...
```

`blib.fcurves(obj)` handles both versions.

## Geometry nodes from Python

Group interface (this changed in 4.0, it is no longer `ng.inputs`):

```python
ng = bpy.data.node_groups.new("Name", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT",  socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
s = ng.interface.new_socket("Density", in_out="INPUT", socket_type="NodeSocketFloat")
s.default_value = 10.0
```

Modifier values (this changed in 5.x):

```python
mod = obj.modifiers.new("GN", "NODES"); mod.node_group = ng
# 4.x:  mod["Socket_2"] = 800.0                       <- TypeError on 5.2
# 5.x:  mod.properties.inputs["Socket_2"]["value"] = 800.0
```

The identifier (`Socket_2`) is not the name: map it with
`{s.name: s.identifier for s in ng.interface.items_tree if s.in_out == "INPUT"}`,
or just call `blib.gn_set(mod, "Density", 800.0)`.

Two rules that raise nothing and simply give wrong results:

- **GN instances do not inherit the host object's materials.** You need a
  `GeometryNodeSetMaterial` in the tree before the output.
- **`obj.bound_box` is the base mesh box**, ignoring modifiers and geometry nodes.
  To measure the real geometry you must evaluate the depsgraph
  (`obj.evaluated_get(depsgraph).to_mesh()`) and add `depsgraph.object_instances`.
  `blib.bounds()` already does this.

Conditional sockets: `distribute_method="POISSON"` disables `Density` and enables
`Distance Min` / `Density Max` / `Density Factor`. Disabled sockets **still appear when
iterating `node.inputs` but vanish from the `node.inputs["name"]` lookup**.
Use `blib.sockets(node)` to see which ones are usable.

## Cycles on Apple Silicon

```python
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for d in prefs.devices: d.use = (d.type == "METAL")
scene.cycles.device = "GPU"
```

On this machine it detects `Apple M4 Pro (GPU - 16 cores)`. Note that
`compute_device_type` introspected through `bl_rna` returns an empty list, yet the
assignment works. `blib.use_gpu()` tries METAL/OPTIX/CUDA/HIP/ONEAPI in order and
returns whichever one took.

Cycles defaults in 5.2: `samples=4096`, `use_denoising=True`,
`denoiser="OPENIMAGEDENOISE"`, `use_adaptive_sampling=True`, `max_bounces=12`.
4096 samples is wildly expensive: always lower it by hand (128-512 is plenty with
the denoiser).

## Export

`bpy.ops.export_scene.gltf` takes 110 parameters. The ones that matter:

```python
bpy.ops.export_scene.gltf(
    filepath=..., export_format="GLB",
    export_draco_mesh_compression_enable=True,   # Draco is available in this build
    export_apply=True,      # applies modifiers (without it, geometry nodes export empty)
    export_yup=True,        # Y-up: what three.js expects
    use_selection=False,
)
```

Available formats: `export_scene.gltf`, `export_scene.fbx`. Build has
`codec_ffmpeg=True` and `openvdb=True`.

## Text objects

Measured against the installed binary, building a title out of letter-shaped
buildings.

`curve.offset` **shrinks or grows the outline perpendicular to its own contour,
in metres, independent of `size`.** Measured on a "B": at size 10 an offset of
-0.5 takes the glyph from 4.666 x 5.590 to 3.666 x 4.590, and at size 25 from
11.665 x 13.975 to 10.665 x 12.975. Exactly 0.5 m off each side both times.

That is the only way to inset a glyph *perpendicular to its own edge*. Scaling
shrinks toward a centre, which is a different shape. It is what makes a facade
band possible on a letter: spandrel at offset 0, glass at offset -0.75, per
floor.

Push it too far and the outline self-intersects — at size 10 an offset of -1.0
already produces garbage (the height stops shrinking and the vertex count
jumps). Keep the offset small against the cap height.

`curve.space_character` is the tracking multiplier, and advance width is affine
in it, so two samples solve for any target width. Below about 0.88 a Black
weight closes up and adjacent letters weld into one another.

`curve.extrude` extrudes symmetrically about the object origin and caps both
ends, so a slice from z0 to z1 is built with `extrude=(z1-z0)/2` and then moved
to `(z0+z1)/2`.

Text objects have no usable bounding box until they are evaluated. Go through
`bpy.data.meshes.new_from_object(ob.evaluated_get(depsgraph))`, and note that
`ob.bound_box` is **cached**: after editing `mesh.vertices` in place it still
reports the pre-edit extents, silently, and anything framing against it lands
in the wrong place.

## bpy_prop_collection

`mesh.vertices[::step]` raises `TypeError: bpy_prop_collection[slice]: slice
steps not supported`. Use `range(0, len(vs), step)`.

Worth knowing because **a Python exception in a background script does not
change Blender's exit code**: `./bl script.py` prints the traceback and exits 0.
A step that died half way looks exactly like a step that worked, and the file
it was supposed to save is simply the previous one. Check the printed output,
not `$?`.
