"""Step 12 — the camera move.

A descent with a drift. Over ten seconds the camera falls from elevation 38 to
24 while sliding sideways and closing in a little.

WHY DOWN. The title is built as buildings on the street grid, so how wide the
word reads is decided by the elevation and nothing else. At 38 degrees the red
roof box has a true aspect of 1.62 against the reference's 2.61, and solving
the projection puts the match at 22.5 degrees. So descending is a move toward
the reference rather than away from it, and it is the one axis where the
reference tells us which way to go. 24, not 22.5: the last degree and a half
costs more of the roofscape than it buys in the word, and the roofscape is
60 per cent of what this camera sees of a building.

WHY THE DRIFT IS SMALL. 37 m over the whole shot. The move has to end on the
composition that was already settled - the title sitting right of centre with
the campus around it - so the drift is measured backwards from that: enough
that the word travels a third of the frame and settles, not enough that
anything whips.

The drift runs along the screen horizontal, which for an azimuth of 45 is the
world direction (-1, 1). Moving the camera along (1, -1) slides the frame left
and carries the title in from the right edge.

WHAT IS NOT IN FRAME. At 190 m of width the Obelisco is 203 m from centre on
screen and the Floralis 293, so neither is in the shot. Seeing them both would
need to open to about 620 m, which is the whole city and a different film.

The camera is animated with real keyframes at intervals rather than two ends,
because elevation is an ANGLE: interpolating the camera's position linearly
between two points on an arc cuts the corner, and the horizon slides. Each key
is computed on the arc and the interpolation between them is linear, so the
easing comes from the smoothstep rather than from Bezier handles nobody can
inspect.

    ./bl scripts/city/12_camera.py
    ./bl scripts/city/12_camera.py video     # and render the preview
"""
import sys, pathlib, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Vector

R = ROOT / "renders"
FPS, FRAMES = 24, 240
AZIMUTH = 45.0                 # fixed: it is what gives every building two faces
DIST = 1450.0                  # only sets where the camera sits on the arc
KEYS = 13

# start -> end.
#
# TARGET1 is where the hero camera was already pointing, and it is NOT the
# origin: blib.camera() aims at the centre of the scene's bounds. Assuming
# (0, 0) put the title hard against the right edge - a composition nobody
# approved and one that does not match the approved still. With this target the
# title lands 2.5 m off centre on screen, which is where the still has it.
#
# It is written down rather than read off the camera. Reading it looked
# cleverer and was a trap: the first run of this step animates the camera, so
# the second run reads back the target IT wrote and the framing is whatever the
# last run happened to leave. A composition is a decision and belongs in the
# file.
TARGET1 = Vector((-51.84, 22.83, 0.0))
EL0, EL1 = 38.0, 24.0
SCALE0, SCALE1 = 210.0, 170.0
# how far the target starts off the final one, along (1, -1), which is the
# screen horizontal at azimuth 45. 20 m of world is 28 m of screen slide, and
# the frame opens 40 m wider than it closes, so the title has room to sit
# fully inside the frame at the start instead of being cut by the edge.
DRIFT = 20.0


def smoothstep(t):
    return t * t * (3.0 - 2.0 * t)


def place(cam, elevation, scale, target):
    a, e = math.radians(AZIMUTH), math.radians(elevation)
    eye = target + Vector((math.cos(a) * math.cos(e),
                           math.sin(a) * math.cos(e),
                           math.sin(e))) * DIST
    cam.location = eye
    cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = scale


def linear(ob):
    for fc in blib.fcurves(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, FRAMES

    cam = bpy.data.objects["HeroCam"]
    cam.animation_data_clear()
    if cam.data.animation_data:
        cam.data.animation_data_clear()
    target1 = TARGET1
    target0 = target1 + Vector((DRIFT, -DRIFT, 0.0))
    print(f"  aiming at ({target1.x:.0f}, {target1.y:.0f}), "
          f"starting {DRIFT * math.sqrt(2):.0f} m along the screen horizontal")

    for i in range(KEYS):
        t = i / (KEYS - 1)
        s = smoothstep(t)
        frame = 1 + round(t * (FRAMES - 1))
        place(cam, EL0 + (EL1 - EL0) * s, SCALE0 + (SCALE1 - SCALE0) * s,
              target0.lerp(target1, s))
        cam.keyframe_insert("location", frame=frame)
        cam.keyframe_insert("rotation_euler", frame=frame)
        cam.data.keyframe_insert("ortho_scale", frame=frame)
    linear(cam)
    linear(cam.data)

    print(f"\n  camera: elevation {EL0:.0f} -> {EL1:.0f}, "
          f"width {SCALE0:.0f} -> {SCALE1:.0f} m, "
          f"drift {(target1 - target0).length:.0f} m, {KEYS} keys")

    # leave the scene on the last frame: that is the composition the still is
    # rendered from, so step 07 and the end of the video agree
    scene.frame_set(FRAMES)
    exposure = scene.view_settings.exposure
    for f in (1, FRAMES // 2, FRAMES):
        scene.frame_set(f)
        blib.render(str(R / f"city_12_cam_{f:03d}.png"), "EEVEE", samples=48,
                    resolution=(1280, 720), exposure=exposure)
    scene.frame_set(FRAMES)
    blib.save(str(R / "city.blend"))

    if "video" in sys.argv:
        blib.render_video(str(R / "city_move.mp4"), fps=FPS, engine="EEVEE",
                          samples=48, resolution=(1280, 720),
                          exposure=exposure)
        print("  video: renders/city_move.mp4")


main()
