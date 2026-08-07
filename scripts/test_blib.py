import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bpy, blib

R = str(pathlib.Path(__file__).resolve().parents[1] / "renders")

blib.reset()
# deliberately tiny object (2cm) to prove the rig scales by itself
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.01, location=(0,0,0.01))
ball = bpy.context.object
bpy.ops.object.shade_smooth()
blib.assign(ball, blib.pbr("Coral", (0.95,0.35,0.25), roughness=0.25, coat=0.5))

bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=0.004, location=(0,0,0.002))
base = bpy.context.object
blib.assign(base, blib.pbr("Metal", (0.7,0.7,0.72), roughness=0.15, metallic=1.0))

blib.hdri(strength=0.4)
blib.three_point(strength=1.0)
blib.camera(azimuth=50, elevation=22, margin=1.35)
blib.report()

print("EEVEE:", blib.render(f"{R}/test_eevee.png", "EEVEE", resolution=(800,600),
                            view_transform="Khronos PBR Neutral"))
print("CYCLES:", blib.render(f"{R}/test_cycles.png", "CYCLES", samples=200,
                             resolution=(800,600), view_transform="AgX", look="AgX - Punchy"))
print("GLB:", blib.export_glb(f"{R}/test.glb"))
print("BLEND:", blib.save(f"{R}/test.blend"))
