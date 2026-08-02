import bpy, math, sys

# escena limpia
bpy.ops.wm.read_factory_settings(use_empty=True)

# objeto
bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 1))
suzanne = bpy.context.object
bpy.ops.object.shade_smooth()

mat = bpy.data.materials.new("Naranja")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.9, 0.35, 0.1, 1)
bsdf.inputs["Roughness"].default_value = 0.35
suzanne.data.materials.append(mat)

# piso
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))

# luz
bpy.ops.object.light_add(type='AREA', location=(4, -4, 6))
bpy.context.object.data.energy = 800

# camara
bpy.ops.object.camera_add(location=(6, -6, 4), rotation=(math.radians(63), 0, math.radians(45)))
bpy.context.scene.camera = bpy.context.object

# render
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 800, 600
scene.render.filepath = "/Users/bilune/develop/blender-mcp/renders/smoke_test.png"
bpy.ops.render.render(write_still=True)
print("OK ->", scene.render.filepath)
