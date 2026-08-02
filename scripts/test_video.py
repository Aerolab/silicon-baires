import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bpy, blib
R = str(pathlib.Path(__file__).resolve().parents[1] / "renders")
blib.reset()
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.35)
blib.assign(bpy.context.object, blib.pbr("Azul", (0.15,0.4,0.9), roughness=0.3, metallic=0.6))
blib.three_point(); blib.camera(azimuth=45, elevation=20)
blib.turntable(frames=24)
print("VIDEO:", blib.render_video(f"{R}/turntable.mp4", fps=24, resolution=(480,360), samples=16))
