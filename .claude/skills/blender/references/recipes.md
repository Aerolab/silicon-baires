# Recipes

All of these were tested in this project. Reference scripts live in `scripts/`.

## Standard preamble

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bpy, blib

R = str(pathlib.Path(__file__).resolve().parents[1] / "renders")
blib.reset()
```

## Product shot

```python
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05)
obj = bpy.context.object
bpy.ops.object.shade_smooth()
blib.assign(obj, blib.pbr("Lacquer", (0.9, 0.2, 0.15), roughness=0.15, coat=0.6))

blib.hdri(strength=0.6, visible=False)      # lights the scene, keeps bg transparent
blib.three_point(strength=1.0, softness=1.4)
blib.camera(azimuth=45, elevation=15, lens=85, margin=1.3)

blib.render(f"{R}/product.png", "CYCLES", samples=256, resolution=(1600, 1600),
            transparent=True, view_transform="Khronos PBR Neutral")
```

Key points: long lens (85mm) so nothing distorts, `Khronos PBR Neutral` so the product
color is the real one, transparent background for compositing afterwards.

## Checking a shape from several angles

```python
blib.contact_sheet(f"{R}/check.png", engine="EEVEE", resolution=(600, 600))
# -> check_front.png, check_three_quarter.png, check_side.png, check_top.png
```

Read all four. It is the only way to catch something that looks right head-on and is
broken from the side.

## Turntable video

```python
blib.turntable(frames=90)                    # creates a parent empty, animates 0->360
blib.render_video(f"{R}/turntable.mp4", fps=30, codec="H264", container="MPEG4",
                  engine="EEVEE", samples=32, resolution=(1080, 1080))
```

`turntable()` with no arguments parents every root object to an empty and rotates the
empty, so camera and lights stay put. 90 frames in EEVEE takes about a minute. In
Cycles, multiply by the cost of one frame: work that out before launching it.

## Procedural scatter (geometry nodes)

```python
ng, gin, gout = blib.gn_tree("Scatter", inputs=[("Density", "NodeSocketFloat", 300.0),
                                                ("Size", "NodeSocketFloat", 0.05)])
n = ng.nodes
dist = n.new("GeometryNodeDistributePointsOnFaces"); dist.distribute_method = "POISSON"
inst = n.new("GeometryNodeInstanceOnPoints")
ico  = n.new("GeometryNodeMeshIcoSphere")
setm = n.new("GeometryNodeSetMaterial")      # instances do NOT inherit the material
join = n.new("GeometryNodeJoinGeometry")
setm.inputs["Material"].default_value = blib.pbr("Dots", (0.95, 0.45, 0.1))

L = ng.links.new
L(gin.outputs["Geometry"], dist.inputs["Mesh"])
L(gin.outputs["Density"],  dist.inputs["Density Max"])   # POISSON: no "Density" socket
L(gin.outputs["Size"],     ico.inputs["Radius"])
L(dist.outputs["Points"],  inst.inputs["Points"])
L(dist.outputs["Rotation"], inst.inputs["Rotation"])
L(ico.outputs["Mesh"],     inst.inputs["Instance"])
L(inst.outputs["Instances"], setm.inputs["Geometry"])
L(setm.outputs["Geometry"],  join.inputs["Geometry"])
L(gin.outputs["Geometry"],   join.inputs["Geometry"])
L(join.outputs["Geometry"],  gout.inputs["Geometry"])

blib.gn_apply(host, ng, Density=800.0, Size=0.04)
```

Before wiring a node you have not used before: `print(blib.sockets(node))`.

## Parametric variations

What makes scripting worth it over modelling by hand:

```python
for i, (color, rough) in enumerate([((0.9,0.2,0.1), 0.1), ((0.1,0.5,0.9), 0.4),
                                    ((0.2,0.8,0.3), 0.7)]):
    blib.reset()
    ...build the scene with color/rough...
    blib.render(f"{R}/var_{i:02d}.png", "EEVEE")
```

One Blender process, N renders: saves the startup (~1s) and the Cycles kernel
compilation (~10s) per variation.

## Web export (three.js)

```python
blib.export_glb(f"{R}/model.glb", draco=True)
```

`export_apply=True` (the `blib` default) applies modifiers: without it, a model
generated with geometry nodes exports empty. Draco compresses ~5x (measured:
6888 -> 1211 bytes on a test mesh). On the three.js side you need `DRACOLoader`;
if that is a nuisance, pass `draco=False`.

`export_yup=True` converts from Blender's Z-up to the Y-up three.js expects.

## Importing an existing model

```python
bpy.ops.import_scene.gltf(filepath="...")    # glTF/GLB
bpy.ops.import_scene.fbx(filepath="...")     # FBX
# the rest moved to wm.* in 5.x (import_scene.obj NO LONGER EXISTS):
bpy.ops.wm.obj_import(filepath="...")        # OBJ
bpy.ops.wm.stl_import(filepath="...")        # STL
bpy.ops.wm.ply_import(filepath="...")        # PLY
bpy.ops.wm.usd_import(filepath="...")        # USD
bpy.ops.wm.alembic_import(filepath="...")    # ABC
blib.report()                                 # what came in: polys, materials, scale
```

The first thing after importing is `report()`: third-party models arrive at absurd
scales (millimetres, inches) and that wrecks the light rig. Normalize before lighting.

## Saving state

```python
blib.save(f"{R}/scene.blend")
```

Useful so a human can open the result in the GUI to review it or carry on by hand.
