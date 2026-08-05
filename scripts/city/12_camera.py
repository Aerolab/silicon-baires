"""Step 12 — the camera move, measured off the reference rather than invented.

The first version of this step descended: elevation 38 to 24 with a small drift.
Then the reference clip was tracked frame by frame, and the descent turned out to
be a move the reference does not make. What it actually does:

    elevation   FIXED at 30.6 degrees, start to finish
    azimuth     FIXED at 46.2
    translation a straight line at constant speed
    zoom        continuous, x1.48 over the move, about 5 per cent per second
    structure   7.4 s of movement, then 1.2 s frozen on the title

HOW IT WAS MEASURED. The reference is orthographic - the ground axes are parallel
across the frame - and under an orthographic camera at a fixed azimuth and
elevation ANY camera motion projects to a similarity on screen: one uniform scale
plus a 2D translation. So fitting (s, tx, ty) between frame pairs recovers the
whole move with no 3D reconstruction. A grid of windows, phase correlation per
window, trimmed least squares to throw out the cars and cranes and the title
itself, then compose the pair maps into one trajectory. The composition lands
everything in FINAL-frame pixels, which is what makes the numbers below directly
convertible to metres once the final frame width is chosen.

The elevation came out of a different measurement, and a more reliable one than
the aspect-of-the-red-box arithmetic that used to justify 24 degrees. A ground
line along +x projects to a screen line with tan(theta) = sin(e) * cot(azimuth),
and along +y with tan(theta) = sin(e) * tan(azimuth). A gradient-orientation
histogram over the whole frame puts the two ground axes at 28 and -26 degrees;
the product of the tangents gives sin(e) and the ratio gives the azimuth. That is
a statistic over every edge in the image rather than one box read off by eye.

AZIMUTH STAYS 45. The measured 46.2 is inside the error of the histogram and,
more to the point, 45 is structural here: it is what gives every building in this
city two visible faces of equal weight. A degree and a bit is not worth it.

WHERE THE MOVE STARTS AND ENDS. Both ends are decisions rather than measurements.
It ends on the framing that was already approved, and it starts behind the
Obelisco so the camera crosses the monument on its way - which is what fixes the
heading. See TARGET0 below for what that costs.

WHY THE SHOT IS TWENTY-FOUR SECONDS AND NOT TEN. The length is not chosen, it
falls out of two numbers that are. The travel has to be long enough to start with
the title off frame and to pass the Obelisco, which comes to 1.85 frame widths of
screen travel; the reference pans at 0.05 to 0.10 frame widths per second. Those
two multiply out. There is no ten second arrangement that keeps both the path and
the reference's apparent speed, so what gives is the length: twenty-two seconds of
move and two of hold, at 0.084. Speeding the result up in post is a decision that
can still be made later; a move that whips cannot be slowed down after the fact.
renders/city_move_fast.mp4 is the same shot at x2.4, for comparison.

WHAT IS ADAPTED, NOT COPIED. The reference clip is cut out of a longer continuous
move, so it starts at full speed. Ours is standalone, so it gets a short ease in.
The decelerations at both ends are the only easing: the body of the move is
linear, because that is what was measured.

    ./bl scripts/city/12_camera.py
    ./bl scripts/city/12_camera.py video     # and render the preview
"""
import sys, pathlib, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Vector
from _common import (FPS, FRAMES, MOVE, HERO_WIDTH, AZIMUTH, ELEVATION,
                     open_city, save_city, place_hero, R,
                     SHOT_TARGET0, SHOT_TARGET1, SHOT_OBELISCO, SHOT_TRAVEL,
                     SHOT_WIDTH0, EASE_IN, EASE_OUT, shot_progress, shot_pan)

KEYS = 41   # the shot length, the framing and the orbit come from _common

# The end of the move is the framing that was already approved. It is written
# down rather than read off the camera: this step ANIMATES the camera, so a
# version that read the target back would frame the shot from whatever the last
# run happened to leave. A composition is a decision and belongs in the file.
#
# THEY LIVE IN _common NOW. This step used to own them, which was right while
# it was the only step that cared where the camera goes. Step 04 cares too: it
# plans a company sign for every roof the shot passes over, so it has to trace
# the same path this file flies. Two copies of a camera move is the same setup
# as the FRAMES bug and the HERO_WIDTH bug already recorded in _common, except
# that this one fails even more quietly - the signs would simply be planned
# along a route the camera does not take, and every frame would still render.
TARGET1 = Vector((*SHOT_TARGET1, 0.0))
OBELISCO = Vector((*SHOT_OBELISCO, 0.0))        # what the shot travels past
TRAVEL = SHOT_TRAVEL
TARGET0 = Vector((*SHOT_TARGET0, 0.0))          # (163, -214)

# THE HEADING IS THE OBELISCO'S, NOT THE REFERENCE'S, and that is a trade rather
# than an oversight.
#
# The measured travel is 156 m along (-0.98, -0.20). Using it produced a shot that
# read as a zoom with a bit of slide, which is what it was: it and the reference
# cover nearly the same ground - 0.637 against 0.649 frame widths - but the
# reference does it while zooming x1.48 where we were zooming x2.35, so per unit
# of zoom the reference travels nearly twice as far. Copying one number and not
# the other copies nothing.
#
# Aiming the travel at the Obelisco costs the diagonal. The reference climbs 36.3
# degrees across the screen; this heading is flat, a pure lateral slide, because
# the Obelisco and the title happen to lie along the screen horizontal. Scanning
# every heading that puts the monument in frame gives a range of 0 to 13 degrees
# and nothing above it, and at 13 the monument is cut by the top edge. So: flat,
# and the opening frame has the Obelisco whole, its oval plaza, the 9 de Julio and
# the Metrobus in it.
#
# 320 m puts the start 64 m BEHIND the Obelisco, so the monument sits on the right
# of the opening frame and the camera crosses it in the first third rather than
# opening on top of it. That distance is a ceiling, not a preference: the Obelisco
# is only 177 m from the south edge of the built area, and the opening frame's far
# corner reaches a long way past its centre. At 360 m the bare site shows in the
# top left corner. 320 was the longest run that rendered full of city, and it was
# settled by looking at the frames rather than by the corner arithmetic, which
# turned out to be pessimistic by about 40 m.
#
# What the travel buys either way is that the title starts OUTSIDE the frame and
# slides in: it first touches the frame at 28 per cent of the move and is fully
# inside by 78. The reference looks like this too and gets there a different way -
# its letters pop in one at a time and out of order, so they are animated, not
# revealed by the camera. Ours cannot pop in, they are twenty-four buildings, so
# the camera has to do it.

# The move ENDS on the hero framing, so the final width is not a number this
# file gets to have an opinion about: it is _common.HERO_WIDTH, the same one
# 07_look renders the still at. It was written out as 170.0 here, in 07 and in
# 11, which is the FRAMES bug from _common waiting to happen a second time.
SCALE1 = HERO_WIDTH
SCALE0 = SHOT_WIDTH0           # the opening width. See _common: it was the
                               # reference's x1.479 and is now x1.80, opened so
                               # the move crosses more of the city and can carry
                               # more company signs past the camera.

# progress() and pan_of() moved to _common as shot_progress and shot_pan, with
# the easing constants, for the same reason the path did: step 04 has to walk
# the move to know which roofs are in it. What they do and why is documented
# there - in particular pan_of, which advances the camera in proportion to the
# CURRENT frame width rather than linearly, because constant world speed cannot
# look constant in a shot that is closing.
progress, pan_of = shot_progress, shot_pan


def linear(ob):
    for fc in blib.fcurves(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def main():
    # After 11, or it animates a camera over cars that step 11 has not placed
    # yet - and 11 resets the scene to frame 1, which undoes the hold this step
    # leaves the file on.
    scene = open_city(needs_collections=("TITLE", "TRAFFIC"),
                      hint="run 08_title.py then 11_animate.py first")
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, FRAMES

    cam = bpy.data.objects["HeroCam"]
    cam.animation_data_clear()
    if cam.data.animation_data:
        cam.data.animation_data_clear()

    print(f"  target ({TARGET0.x:.0f}, {TARGET0.y:.0f}) -> "
          f"({TARGET1.x:.0f}, {TARGET1.y:.0f}), {TRAVEL:.0f} m")
    print(f"  width {SCALE0:.0f} -> {SCALE1:.0f} m, "
          f"elevation {ELEVATION:.1f} fixed")

    for i in range(KEYS):
        t = i / (KEYS - 1)
        q = progress(t)
        frame = 1 + round(t * (MOVE - 1))
        # the zoom is exponential in eased time: a constant per cent per second
        # is what the reference does, and it reads as a steady closing rather
        # than a rush at one end. The pan is then tied to it, see pan_of()
        scale = SCALE0 * (SCALE1 / SCALE0) ** q
        place_hero(cam, scale, TARGET0.lerp(TARGET1, pan_of(q)))
        cam.keyframe_insert("location", frame=frame)
        cam.keyframe_insert("rotation_euler", frame=frame)
        cam.data.keyframe_insert("ortho_scale", frame=frame)
    linear(cam)
    linear(cam.data)
    print(f"  {KEYS} keys over {MOVE} frames, then {FRAMES - MOVE} frames held")

    # MOTION BLUR, and it is not a garnish. The camera pans 6 px a frame at
    # 1080p, and every edge in this city is deliberately crisp, so without blur
    # each piece of fine detail - a lane marking, a car, a tree - jumps six
    # pixels between frames with nothing joining them up. The result judders:
    # the eye tries to track something and cannot hold it.
    #
    # The first diagnosis was wrong and worth recording. The suspect was this
    # step's own 41 linear keyframes, one every 13.2 frames, each a small break
    # in velocity. Tracking the exported video frame by frame and taking the
    # autocorrelation of the per-frame pan killed it: there is no peak at lag 13
    # or 26. The keys are not it. What is left is that 24 fps with hard edges
    # and no shutter is simply not enough samples.
    #
    # 0.5 is a 180 degree shutter, the film default. It costs nothing measurable
    # in EEVEE - 2.2 s a frame either way - and changes 10 per cent of the
    # pixels, which is invisible in a still and is the entire point in motion.
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5

    scene.frame_set(FRAMES)
    for f in (1, MOVE // 3, 2 * MOVE // 3, MOVE, FRAMES):
        scene.frame_set(f)
        blib.render(str(R / f"city_12_cam_{f:03d}.png"), "EEVEE", samples=48,
                    resolution=(1280, 720))
    scene.frame_set(FRAMES)
    save_city()

    # Two of them, and the difference is 18 minutes.
    #
    #   video    720p, 48 samples. The one to run while iterating on the move.
    #   export   1080p, 96 samples. The deliverable.
    #
    # Both are EEVEE. Cycles at 1080p measures 10.7 s a frame, which is 1 h 43
    # for the 576, and it is the engine the approved still is rendered in - so
    # if the video ever has to sit next to city_final.png and match its light,
    # that is the cost, and it is a decision rather than a default.
    if "export" in sys.argv:
        blib.render_video(str(R / "city_move_1080.mp4"), fps=FPS, engine="EEVEE",
                          samples=96, resolution=(1920, 1080))
        print("  export: renders/city_move_1080.mp4")
    elif "video" in sys.argv:
        blib.render_video(str(R / "city_move.mp4"), fps=FPS, engine="EEVEE",
                          samples=48, resolution=(1280, 720))
        print("  video: renders/city_move.mp4")


main()
