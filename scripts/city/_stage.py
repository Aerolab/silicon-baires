"""The empty stage. NOT part of the numbered chain: it DESTROYS the city.

Creates renders/city.blend with nothing in it but the things every later step
depends on: metric units, the sun and sky, the hero camera, and the palette.

It was called 00_setup.py, which put it at the head of a list of numbered steps
that are all safe to re-run - and this one opens with blib.reset(). Anybody
following the numbers wiped the city. It is underscored now, like _common and
_palette, because it is not a step: it is the bootstrap, it runs once, and
running it again means rebuilding everything from 02_kit.py onwards.

    ./bl scripts/city/_stage.py     # and then the whole chain, from 02_kit
"""
import sys, pathlib, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Vector
from _common import (R, BLEND, AZIMUTH, ELEVATION, DISTANCE, HERO_WIDTH,
                     place_hero, apply_palette)

# How big to make the placeholder ground and how far out to hang the sun. Not
# a grid: this file used to declare BLOCK = 90, STREET = 22, EXTENT = 7 as "the
# scale contract", and step 03 has been building 52-to-76 m blocks on 12, 22 and
# 70 m streets for a long time. The real extent comes out of city_lots.json.
CITY = 806.0

# --- camera ----------------------------------------------------------------
# ORTHOGRAPHIC, and this was measured, not assumed. A 150 mm perspective lens
# at 1450 m still leans verticals 6.5 deg near the frame edge, which the
# reference plainly does not do: its verticals are parallel everywhere. Only an
# orthographic camera gives that.
# Cost of the choice: no perspective depth cue, and camera DOF stops being
# useful. The miniature blur therefore has to come from a compositor defocus
# driven by the Z pass (M5), which is more controllable anyway.
# The orbit and the framing come from _common, so the camera this file leaves
# in the .blend is the same one the shot lands on. It used to carry its own
# CAM_ELEVATION = 38.0, which meant every preview render from steps 03 to 10
# was framed at an elevation the film never uses: the move measured off the
# reference sits at 30.6.

# --- sun -------------------------------------------------------------------
# THE FOUR INTENSITY NUMBERS BELOW ARE DEAD. SUN_ENERGY, SUN_ANGLE, the sun
# colour, SKY_STRENGTH and SKY_SATURATION are overridden by _common.apply_grade
# on every open_city(), because they are look and this file cannot be re-run to
# change them: it destroys the city. Edit _common.GRADE. What is still live
# here is the GEOMETRY - the azimuth and the elevation, which decide where the
# shadows fall and are what the whole grid is composed against.
#
# Shadows must fall towards screen lower-left, which puts the sun at world
# azimuth 180 deg for a camera at 45 deg. High and late-morning.
SUN_AZIMUTH = 180.0
SUN_ELEVATION = 55.0
SUN_ANGLE = 3.5       # degrees of angular diameter: soft shadows, never black
# Sun-to-sky ratio decides the colour of the concrete. Sky-heavy turns the warm
# cream into cold blue-white, which is what a first pass at 3.2/0.55 did.
SUN_ENERGY = 4.0
SKY_STRENGTH = 0.32
SKY_SATURATION = 0.35   # how much blue the ambient keeps
EXPOSURE = -0.5         # the warm concretes are albedo ~0.8 and clip without this


def build_sky():
    """Nishita sky + a matching sun lamp.

    The sky alone gives the bright even ambient the look needs; the sun lamp
    gives the crisp directional shadow. Using both is what keeps shadows dark
    but not black.
    """
    world = bpy.context.scene.world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    sky = nt.nodes.new("ShaderNodeTexSky")
    # 5.2 renamed the Nishita model: it is MULTIPLE_SCATTERING now, and
    # dust_density became aerosol_density.
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(SUN_ELEVATION)
    sky.sun_rotation = math.radians(SUN_AZIMUTH)
    sky.sun_disc = False          # the sun lamp does the shadows, not the sky
    sky.altitude = 200.0
    sky.air_density = 1.0
    sky.aerosol_density = 1.2     # slight haze: takes the edge off the blue

    # A physically blue sky paints every roof blue, and from this camera roofs
    # are most of the frame. The reference has warm cream roofs, so the ambient
    # gets desaturated before it is used. This is a look decision, not physics.
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = SKY_SATURATION

    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = SKY_STRENGTH
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs["Color"], hsv.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    az, el = math.radians(SUN_AZIMUTH), math.radians(SUN_ELEVATION)
    direction = Vector((math.cos(el) * math.cos(az),
                        math.cos(el) * math.sin(az),
                        math.sin(el)))
    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = SUN_ENERGY
    sun_data.angle = math.radians(SUN_ANGLE)
    sun_data.color = (1.0, 0.95, 0.87)
    sun = blib.link(bpy.data.objects.new("Sun", sun_data))
    sun.location = direction * (CITY * 1.5)
    blib.look_at(sun, Vector((0, 0, 0)))
    return sun


def build_camera():
    cam = blib.camera(azimuth=AZIMUTH, elevation=ELEVATION, distance=DISTANCE)
    cam.name = "HeroCam"
    cam.data.type = "ORTHO"
    place_hero(cam, HERO_WIDTH)
    cam.data.clip_start = 1.0
    cam.data.clip_end = 5000.0

    # Marks the plane the compositor defocus will keep sharp at M5. It does
    # nothing on its own: an orthographic camera has no usable DOF.
    focus = blib.link(bpy.data.objects.new("FocusPlane", None))
    focus.empty_display_size = 30.0
    focus.location = (0, 0, 12)      # rooftop height, middle of frame
    return cam


def build_ground():
    """Placeholder only. Step 01 replaces this with the real site."""
    bpy.ops.mesh.primitive_plane_add(size=CITY * 1.4)
    plane = bpy.context.object
    plane.name = "GROUND_placeholder"
    blib.assign(plane, bpy.data.materials["Grass"])
    return plane


def main():
    blib.reset()
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    sc.unit_settings.length_unit = "METERS"
    sc.render.resolution_x, sc.render.resolution_y = 2560, 1440
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = EXPOSURE

    n = apply_palette()
    build_sky()
    build_ground()
    build_camera()

    print(f"\n  materials   : {n} from _palette.py")
    blib.report()

    blib.render(str(R / "city_00_setup.png"), "EEVEE", samples=32,
                resolution=(1280, 720), view_transform="AgX", exposure=EXPOSURE)
    blib.save(str(BLEND))


main()
