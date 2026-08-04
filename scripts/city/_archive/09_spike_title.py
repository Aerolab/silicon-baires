"""Spike — how is the title actually sitting in the reference?

Two readings of the reference are possible and they look very different once
built: the letters are flat plates lying in the ground plane (extruded down,
so the type shears exactly like the roofs), or they are a wall of type
standing up and facing the camera.

The flat reading has a wrinkle worth checking: a flat title rotated 45 deg to
the city grid projects with NO shear at all under this camera, only a vertical
squash to about 0.62. That is what makes the reference letters read upright
and squat at the same time. So the rotation about Z is the whole experiment.

Renders one variant per angle plus the standing-wall control. Nothing is saved.

WHAT THIS SPIKE CONCLUDED, AND WHY IT IS WRONG. It picked the flat reading and
the off-grid rotation, and both were wrong. The letters are buildings, not
plates, and their baseline goes on the street grid: beside SILICON the city's
edges run at -27 deg and SILICON runs at -25.6. The no-shear property of 135
deg is real and it is a trap — it is a fact about this one camera, and the
title is a fact about the city. Kept because the renders are the evidence for
how the wrong answer looked, and it looked convincing.

    ./bl scripts/city/09_spike_title.py
"""
import sys, pathlib, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Vector
from _common import pbrmat

R = ROOT / "renders"
FONT = "/Users/bilune/Library/Fonts/PPMonumentNarrow-Black.otf"
CAM_WIDTH = 210.0


def make_text(body, size, extrude):
    cu = bpy.data.curves.new("t", type="FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(FONT)
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    ob = bpy.data.objects.new(body, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(bpy.data.materials["Title Red"])
    return ob


def clear():
    for ob in list(bpy.context.scene.collection.objects):
        if ob.type == "FONT":
            bpy.data.objects.remove(ob, do_unlink=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    sc = bpy.context.scene
    paint("Title Red")

    cam = bpy.data.objects["HeroCam"]
    cam.data.ortho_scale = CAM_WIDTH
    exposure = sc.view_settings.exposure

    # flat on the ground plane, rotated about Z. 135 deg is the angle at which
    # the projection is pure squash with no shear.
    for phi in (90, 112, 135, 157, 180):
        clear()
        for k, (body, cy) in enumerate((("BUENOS", 14.0), ("AIRES", -14.0))):
            ob = make_text(body, 22.0, 3.0)
            ob.rotation_euler = (0, 0, math.radians(phi))
            v = Vector((-math.sin(math.radians(phi)), math.cos(math.radians(phi)), 0))
            ob.location = Vector((0, 0, 42.0)) + v * cy
        blib.render(str(R / f"spike_title_flat{phi}.png"), "EEVEE", samples=32,
                    resolution=(1280, 720), exposure=exposure)

    # standing wall, facing the camera
    clear()
    for body, dz in (("BUENOS", 12.0), ("AIRES", -12.0)):
        ob = make_text(body, 18.0, 3.0)
        ob.rotation_euler = (math.radians(90), 0, math.radians(45 + 180))
        ob.location = (30, 30, 45.0 + dz)
    blib.render(str(R / "spike_title_wall.png"), "EEVEE", samples=32,
                resolution=(1280, 720), exposure=exposure)


main()
