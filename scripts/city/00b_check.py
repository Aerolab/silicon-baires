"""Step 00b — verify the stage, without touching it.

Opens city.blend, drops throwaway boxes at the scale of real buildings, renders,
and exits WITHOUT SAVING. Nothing here ends up in the city file.

Answers the four questions step 00 cannot answer on an empty plane:
  1. does the hero camera cover the intended slice of the city?
  2. do shadows fall towards screen lower-left, and are they soft but not black?
  3. are vertical edges parallel at the frame edges, or do we need an ortho camera?
  4. AgX or Khronos PBR Neutral for this palette?

    ./bl scripts/city/00b_check.py
"""
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import bpy, blib

R = ROOT / "renders"
BLOCK, STREET, EXTENT = 90.0, 22.0, 6
PITCH = BLOCK + STREET

bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))

# A stand-in building on each block centre. Heights walk through the range in
# the scale contract so the skyline reads at a glance.
HEIGHTS = [7.6, 11.4, 19.0, 15.2, 30.4, 45.6, 76.0, 99.0]
mats = [bpy.data.materials[n] for n in
        ("Concrete Warm", "Concrete Cool", "Concrete Warm2", "Glass Dark")]

half = (EXTENT - 1) / 2.0
for i in range(EXTENT):
    for j in range(EXTENT):
        h = HEIGHTS[(i * 3 + j * 5) % len(HEIGHTS)]
        bpy.ops.mesh.primitive_cube_add(size=1)
        b = bpy.context.object
        b.scale = (BLOCK * 0.42, BLOCK * 0.42, h / 2.0)
        b.location = ((i - half) * PITCH, (j - half) * PITCH, h / 2.0)
        blib.assign(b, mats[(i + j) % len(mats)])

# Human scale: a 1.75 m sliver at the foot of the centre block. If this is not
# visible as a speck, the camera is too far out.
bpy.ops.mesh.primitive_cube_add(size=1)
p = bpy.context.object
p.scale = (0.5, 0.5, 0.875)
p.location = (BLOCK * 0.5, BLOCK * 0.5, 0.875)
blib.assign(p, bpy.data.materials["Accent Red"])

blib.report()
for vt in ("AgX", "Khronos PBR Neutral"):
    tag = vt.split()[0].lower()
    blib.render(str(R / f"city_00b_{tag}.png"), "EEVEE", samples=64,
                resolution=(1600, 900), view_transform=vt,
                exposure=bpy.context.scene.view_settings.exposure)

print("\n  nothing saved: city.blend is untouched")
