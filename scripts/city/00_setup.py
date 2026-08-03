"""Step 00 — the empty stage.

Creates renders/city.blend with nothing in it but the things every later step
depends on: metric units, the sun and sky, the hero camera, and the palette from
docs/city/STYLE-BIBLE.md.

No city yet. The only mesh is a placeholder ground plane so the camera has
something to land on; step 01 replaces it.

    ./bl scripts/city/00_setup.py
"""
import sys, pathlib, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import bpy, blib
from mathutils import Vector

R = ROOT / "renders"

# --- the scale contract, from docs/city/PLAN.md -----------------------------
BLOCK = 90.0          # m, block module
STREET = 22.0         # m, street corridor
EXTENT = 7            # blocks per side
CITY = EXTENT * BLOCK + (EXTENT + 1) * STREET     # 806 m across

# --- camera ----------------------------------------------------------------
# ORTHOGRAPHIC, and this was measured, not assumed. A 150 mm perspective lens
# at 1450 m still leans verticals 6.5 deg near the frame edge, which the
# reference plainly does not do: its verticals are parallel everywhere. Only an
# orthographic camera gives that.
# Cost of the choice: no perspective depth cue, and camera DOF stops being
# useful. The miniature blur therefore has to come from a compositor defocus
# driven by the Z pass (M5), which is more controllable anyway.
CAM_AZIMUTH = 45.0    # every street runs diagonally, every building shows two faces
CAM_ELEVATION = 38.0
CAM_DISTANCE = 1450.0  # ortho: affects clipping only, not framing
CAM_WIDTH = 620.0     # metres of city across the frame

# --- sun -------------------------------------------------------------------
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


def srgb(hex_str):
    """#rrggbb -> linear RGB, which is what Blender sockets want."""
    h = hex_str.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


# Straight from the style bible. Fake user so they survive a save with no
# objects using them yet.
PALETTE = {
    "Concrete Warm":  ("#e6ded0", 0.85, 0.0),
    "Concrete Warm2": ("#cfc4b2", 0.85, 0.0),
    "Concrete Cool":  ("#b9bcbd", 0.85, 0.0),
    "Concrete Cool2": ("#8e9295", 0.85, 0.0),
    "Glass Light":    ("#7fa3ad", 0.12, 0.0),
    "Glass Dark":     ("#2c3134", 0.08, 0.0),
    "Asphalt":        ("#3a3a3c", 0.75, 0.0),
    "Sidewalk":       ("#c9c6bd", 0.80, 0.0),
    "Marking":        ("#eef0ee", 0.65, 0.0),
    "Grass":          ("#4aa32a", 0.90, 0.0),
    "Foliage Dark":   ("#2f6b25", 0.90, 0.0),
    "Foliage Mid":    ("#4e8f2c", 0.90, 0.0),
    "Foliage Light":  ("#79b93a", 0.90, 0.0),
    "Trunk":          ("#7a3b2a", 0.90, 0.0),
    "Roof Pipe":      ("#d0714a", 0.55, 0.0),
    "Metal Painted":  ("#d8d8d6", 0.40, 0.0),
    "Accent Red":     ("#c8302a", 0.45, 0.0),
    "Accent Yellow":  ("#e8b520", 0.45, 0.0),
    "Accent Magenta": ("#c9268f", 0.45, 0.0),
}


def build_palette():
    for name, (hexcol, rough, metal) in PALETTE.items():
        mat = blib.pbr(name, srgb(hexcol), roughness=rough, metallic=metal)
        mat.use_fake_user = True
    return len(PALETTE)


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
    cam = blib.camera(azimuth=CAM_AZIMUTH, elevation=CAM_ELEVATION,
                      distance=CAM_DISTANCE)
    cam.name = "HeroCam"
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = CAM_WIDTH
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

    n = build_palette()
    build_sky()
    build_ground()
    build_camera()

    print(f"\n  city extent : {CITY:.0f} x {CITY:.0f} m ({EXTENT}x{EXTENT} blocks)")
    print(f"  materials   : {n}")
    blib.report()

    blib.render(str(R / "city_00_setup.png"), "EEVEE", samples=32,
                resolution=(1280, 720), view_transform="AgX", exposure=EXPOSURE)
    blib.save(str(R / "city.blend"))


main()
