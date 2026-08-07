"""The smallest thing that proves Blender renders at all, without blib.

Everything else in this repo goes through `blib`, which derives framing and
light power from the geometry. This one places a camera and a light by hand on
purpose: when a render comes out black, it answers whether the problem is the
environment or the library.

    ./bl scripts/smoke_test.py
"""
import bpy, math, pathlib

OUT = pathlib.Path(__file__).resolve().parents[1] / "renders" / "smoke_test.png"

# a clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# the object
bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 1))
suzanne = bpy.context.object
bpy.ops.object.shade_smooth()

mat = bpy.data.materials.new("Orange")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.9, 0.35, 0.1, 1)
bsdf.inputs["Roughness"].default_value = 0.35
suzanne.data.materials.append(mat)

# the floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))

# the light
bpy.ops.object.light_add(type='AREA', location=(4, -4, 6))
bpy.context.object.data.energy = 800

# the camera
bpy.ops.object.camera_add(location=(6, -6, 4),
                          rotation=(math.radians(63), 0, math.radians(45)))
bpy.context.scene.camera = bpy.context.object

# and the render
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 800, 600
OUT.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(OUT)
bpy.ops.render.render(write_still=True)
print("OK ->", scene.render.filepath)
