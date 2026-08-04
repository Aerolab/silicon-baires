"""Step 07 — the look: depth of field, grain, vignette.

The single most important step. An orthographic camera has no usable depth of
field of its own, so the miniature blur is built in the compositor from the Z
pass. Without it the city reads as a game level; with it, as a model on a
table.

    ./bl scripts/city/07_look.py [final]
"""
import sys, pathlib, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from _common import HERO_WIDTH, DISTANCE, R, open_city, save_city

# The frame width was measured against the reference with a car as the ruler:
# it runs about 14 px per metre, so its frame spans roughly 140 m. The first
# pass was 590 m, four times too wide, which is why every piece of detail read
# as a speck. Tightened again from 210 when the title went on the grid: the
# word is pinned to its block now, so the frame is what sizes it.
#
# It lives in _common because the camera move has to LAND on it. This file and
# 12_camera each carried their own copy of 170.0.
FOCUS_D = DISTANCE         # camera sits this far out; focus on the middle
F_STOP = 0.55              # unphysical on purpose: this is the miniature cheat
BLUR_MAX = 13.0            # pixels at 1600 wide; scaled to the real width below
FOCUS_SPREAD = 105.0   # metres of depth that stay acceptably sharp
GRAIN = 0.10
VIGNETTE = 0.22


def mix(ng, blend, fac):
    """5.x compositing uses shader Mix nodes; the sockets are per-data-type."""
    n = ng.nodes.new("ShaderNodeMix")
    n.data_type = "RGBA"
    n.blend_type = blend
    n.inputs[0].default_value = fac
    return n


def build_compositor(scene):
    """Blender 5.x: the compositor is a node group hung off the scene, the
    output is a NodeGroupOutput, and CompositorNodeComposite / MixRGB /
    Texture no longer exist."""
    scene.view_layers[0].use_pass_z = True
    ng = bpy.data.node_groups.get("CityComp")
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new("CityComp", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT",
                            socket_type="NodeSocketColor")
    scene.compositing_node_group = ng

    rl = ng.nodes.new("CompositorNodeRLayers")
    rl.scene = scene
    rl.location = (-900, 0)

    # An orthographic camera has no optics for the Defocus node to work from,
    # so the miniature blur is driven straight off the Z pass: blur radius
    # rises with distance from the focus plane, clamped.
    def math(op, value=None, loc=(0, 0)):
        n = ng.nodes.new("ShaderNodeMath")
        n.operation = op
        n.location = loc
        if value is not None:
            n.inputs[1].default_value = value
        return n

    sub = math("SUBTRACT", FOCUS_D, (-720, -140))
    ab = math("ABSOLUTE", None, (-560, -140))
    sc = math("DIVIDE", FOCUS_SPREAD, (-400, -140))
    pw = math("POWER", 1.7, (-320, -140))     # gentler falloff near the focus
    cl = math("MINIMUM", 1.0, (-250, -140))
    ng.links.new(rl.outputs["Depth"], sub.inputs[0])
    ng.links.new(sub.outputs[0], ab.inputs[0])
    ng.links.new(ab.outputs[0], sc.inputs[0])
    ng.links.new(sc.outputs[0], pw.inputs[0])
    ng.links.new(pw.outputs[0], cl.inputs[0])

    blur = ng.nodes.new("CompositorNodeBlur")
    blur.location = (-620, 60)
    # 5.x moved the blur's filter type and radius onto input sockets
    ng.links.new(rl.outputs["Image"], blur.inputs["Image"])
    scale = scene.render.resolution_x / 1600.0   # blur is in pixels
    px = math("MULTIPLY", BLUR_MAX * scale, (-110, -140))
    ng.links.new(cl.outputs[0], px.inputs[0])
    ng.links.new(px.outputs[0], blur.inputs["Size"])
    head = blur.outputs["Image"]

    coords = ng.nodes.new("CompositorNodeImageCoordinates")
    coords.location = (-900, -340)
    noise = ng.nodes.new("ShaderNodeTexWhiteNoise")
    noise.location = (-700, -340)
    ng.links.new(coords.outputs[0], noise.inputs["Vector"])
    g = mix(ng, "OVERLAY", GRAIN)
    g.location = (-400, 0)
    ng.links.new(head, g.inputs[6])
    ng.links.new(noise.outputs["Color"], g.inputs[7])
    head = g.outputs[2]

    try:
        mask = ng.nodes.new("CompositorNodeEllipseMask")
        mask.location = (-700, -600)
        mask.inputs["Size"].default_value = (0.86, 0.94)
        blur = ng.nodes.new("CompositorNodeBlur")
        blur.location = (-460, -600)
        blur.inputs["Size"].default_value = 0.35
        ng.links.new(mask.outputs["Mask"], blur.inputs["Image"])
        v = mix(ng, "MULTIPLY", VIGNETTE)
        v.location = (-180, 0)
        ng.links.new(head, v.inputs[6])
        ng.links.new(blur.outputs["Image"], v.inputs[7])
        head = v.outputs[2]
    except Exception as e:
        print(f"  vignette skipped: {e}")

    out = ng.nodes.new("NodeGroupOutput")
    out.location = (80, 0)
    ng.links.new(head, out.inputs[0])
    return ng


def main():
    scene = open_city(needs_collections=("BUILDINGS", "TITLE"),
                      hint="run the whole chain from 03_ground.py first")
    cam = bpy.data.objects["HeroCam"]
    # Deliberately NOT set here any more. After step 12 the camera is animated
    # and ortho_scale is driven by an fcurve, so assigning it did nothing at
    # render time and the still came out right only because 12's last keyframe
    # happens to hold the same width. The still is the last frame of the move,
    # and now it says so.
    if not blib.fcurves(cam.data):
        cam.data.ortho_scale = HERO_WIDTH
    cam.data.dof.focus_distance = FOCUS_D
    cam.data.dof.aperture_fstop = F_STOP

    # AgX desaturates by design; Punchy pulls the chroma back towards the
    # reference without giving up the highlight rolloff
    scene.view_settings.look = "AgX - Punchy"
    # the reference sits at 0.498 mean luminance; without this the frame drifts
    # bright as soon as the roads stop carrying the dark values
    scene.view_settings.exposure = -0.78
    build_compositor(scene)

    cycles = "final" in sys.argv   # not --cycles: Blender parses that itself
    exposure = scene.view_settings.exposure

    # The still is a STILL, and it does not want the shot's motion blur.
    # Step 12 turns it on and leaves it on, because it belongs to the move; the
    # last frame is inside the two-second hold where the camera has stopped, but
    # 1500 cars have not, so rendering the hero frame with it on smears every
    # vehicle in the city. Off for the render, restored before the save, so the
    # .blend still carries what the shot needs.
    blur = scene.render.use_motion_blur
    scene.render.use_motion_blur = False
    if cycles:
        blib.use_gpu()
        blib.render(str(R / "city_final.png"), "CYCLES", samples=256,
                    resolution=(2560, 1440), exposure=exposure)
    else:
        blib.render(str(R / "city_07_look.png"), "EEVEE", samples=96,
                    resolution=(1600, 900), exposure=exposure)
    scene.render.use_motion_blur = blur
    save_city()


main()
