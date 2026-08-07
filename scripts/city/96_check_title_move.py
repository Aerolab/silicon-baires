"""Does the title still work when the camera moves?

The title is a real object lying in the city, not a compositing layer, so a
camera move will see it turn, foreshorten and eventually go edge-on. That is
the reference's behaviour too. This renders the same frame from a few azimuths
and elevations around the hero so the failure is visible now rather than after
the move is animated.

The findings recorded here previously — that the lean unwinds to nothing at
azimuth 20 — belonged to a version whose words were rotated off the street
grid, and they no longer hold. The title now sits on the grid, so what the
camera does to it is fixed by the city, not tunable.

What IS tunable is how wide the word reads, and it comes out of the elevation
alone. The red roof box has a true aspect of 1.62 at elevation 38 and the
reference's is 2.61; solving the projection gives **elevation 22.5°** for a
match, and the "low" shot below at 26° is most of the way there. A move that
descends is therefore a move toward the reference, not away from it.

Note the trap in the numbers step 08 prints: 0.554 x 0.615 against the
reference's 0.642 x 0.437 are fractions of a 16:9 frame, so dividing them is
meaningless. In metres a height fraction is worth 0.5625 of a width fraction.

Re-run this and read the frames before designing the move.

    ./bl scripts/city/96_check_title_move.py
"""
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from _common import open_city, R
from mathutils import Vector

SHOTS = [("wide", 45, 38, 420), ("hero", 45, 38, 210),
         ("early", 20, 45, 300), ("late", 70, 33, 260),
         ("low", 45, 26, 240)]


def main():
    open_city(needs_collections=('TITLE',),
              hint="run the chain in CLAUDE.md first")
    scene = bpy.context.scene
    title = bpy.data.collections["TITLE"]
    # TitleRoot is an Empty and has no mesh: ob.data is None and this died on
    # it. The same Empty caught 99_check_overlap.py the first time it ran.
    pts = [ob.matrix_world @ v.co
           for ob in title.objects if ob.type == "MESH"
           for v in ob.data.vertices]
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
