"""Does the title still work when the camera moves?

The title is a real object lying in the city, not a compositing layer, so a
camera move will see it turn, foreshorten and eventually go edge-on. That is
the reference's behaviour too. This renders the same frame from a few azimuths
and elevations around the hero so the failure is visible now rather than after
the move is animated.

The findings recorded here previously — that the lean unwinds to nothing at
azimuth 20 — belonged to a version whose words were rotated off the street
grid, and they no longer hold. The title now sits on the grid, so what the
camera does to it is fixed by the city, not tunable. Re-run this and read the
frames before designing the move.

    ./bl scripts/city/96_check_title_move.py
"""
import sys, pathlib, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Vector

R = ROOT / "renders"
SHOTS = [("wide", 45, 38, 420), ("hero", 45, 38, 210),
         ("early", 20, 45, 300), ("late", 70, 33, 260),
         ("low", 45, 26, 240)]


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    scene = bpy.context.scene
    title = bpy.data.collections["TITLE"]
    pts = [ob.matrix_world @ v.co
           for ob in title.objects for v in ob.data.vertices]
    centre = sum(pts, Vector((0, 0, 0))) / len(pts)
    print(f"  title centre {tuple(round(v, 1) for v in centre)}")

    cam = bpy.data.objects["HeroCam"]
    keep = (cam.location.copy(), cam.rotation_euler.copy(),
            cam.data.ortho_scale)
    for name, az, el, width in SHOTS:
        c = blib.camera(azimuth=az, elevation=el, distance=1450)
        cam.location = c.location
        cam.rotation_euler = c.rotation_euler
        bpy.data.objects.remove(c, do_unlink=True)
        scene.camera = cam          # blib.camera() made itself the active one
        blib.look_at(cam, centre)
        cam.data.ortho_scale = width
        blib.render(str(R / f"city_96_move_{name}.png"), "EEVEE", samples=32,
                    resolution=(1280, 720),
                    exposure=scene.view_settings.exposure)
    cam.location, cam.rotation_euler, cam.data.ortho_scale = keep
    print("\n  nothing saved: the hero camera is put back where it was")


main()
