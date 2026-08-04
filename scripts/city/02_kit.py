"""Step 02 — the asset kit.

Everything that gets repeated across the city, modelled once: trees, hedges,
vehicles, people, street furniture and roof units. Each asset is a single mesh
with several material slots, so placing one later costs an object and no
geometry.

Lives in a KIT collection that is hidden from renders. Later steps instance out
of it.

    ./bl scripts/city/02_kit.py
"""
import sys, pathlib, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from _common import Mesh, collection, instance, mat, pbrmat, counts

R = ROOT / "renders"
KIT = None


# --- nature ----------------------------------------------------------------
def tree_broadleaf(name, height, foliage, lobes, seed):
    """Trunk plus a few faceted blobs. Deliberately readable as a toy."""
    import random
    rnd = random.Random(seed)
    m = Mesh()
    trunk_h = height * 0.34
    m.cyl((0, 0, 0), height * 0.035, trunk_h, mat("Trunk"), segs=6,
          top=height * 0.028)
    canopy_r = height * 0.30
    for i in range(lobes):
        a = 2 * math.pi * i / lobes + rnd.uniform(-0.4, 0.4)
        d = 0 if i == 0 else canopy_r * rnd.uniform(0.35, 0.55)
        m.sphere((d * math.cos(a), d * math.sin(a),
                  trunk_h + canopy_r * rnd.uniform(0.55, 0.85)),
                 canopy_r * rnd.uniform(0.62, 0.95), foliage,
                 segs=7, rings=5, scale=(1.0, 1.0, rnd.uniform(0.72, 0.92)))
    return m.build(name, KIT)


def tree_conifer(name, height, foliage, tiers, seed):
    import random
    rnd = random.Random(seed)
    m = Mesh()
    trunk_h = height * 0.18
    m.cyl((0, 0, 0), height * 0.03, trunk_h, mat("Trunk"), segs=6)
    z, r = trunk_h, height * 0.26
    for i in range(tiers):
        h = (height - trunk_h) / tiers * 1.45
        m.cone((0, 0, z), r * (1 - i * 0.22), h, foliage, segs=7)
        z += h * 0.55
        rnd.random()
    return m.build(name, KIT)


def hedge(name, w, d, h, foliage):
    m = Mesh()
    m.box((0, 0, h / 2), (w, d, h), foliage)
    return m.build(name, KIT)


# --- vehicles --------------------------------------------------------------
def car(name, body_col, length=4.4, width=1.8, kind="sedan"):
    m = Mesh()
    body, glass, tire = mat(body_col), mat("Car Glass"), mat("Tire")
    if kind == "sedan":
        m.box((0, 0, 0.62), (length, width, 0.72), body)
        m.box((-0.25, 0, 1.22), (length * 0.46, width * 0.86, 0.52), glass)
        m.box((-0.25, 0, 1.46), (length * 0.44, width * 0.84, 0.06), body)
    elif kind == "van":
        m.box((0, 0, 0.70), (length, width, 0.86), body)
        m.box((-0.1, 0, 1.42), (length * 0.72, width * 0.94, 0.62), glass)
        m.box((-0.1, 0, 1.72), (length * 0.72, width * 0.94, 0.10), body)
    elif kind == "pickup":
        m.box((0, 0, 0.66), (length, width, 0.76), body)
        m.box((length * 0.12, 0, 1.28), (length * 0.36, width * 0.88, 0.56),
              glass)
        m.box((-length * 0.28, 0, 1.16), (length * 0.44, width * 0.92, 0.34),
              body)
    elif kind == "bus":
        m.box((0, 0, 1.30), (length, width, 2.10), body)
        for k in range(6):
            m.box((-length / 2 + 1.1 + k * (length - 2.2) / 5.5, 0, 1.75),
                  (1.05, width + 0.04, 0.72), glass)
        m.box((length / 2 - 0.02, 0, 1.75), (0.08, width * 0.86, 0.8), glass)
    elif kind == "truck":
        m.box((length * 0.30, 0, 1.10), (length * 0.34, width, 1.70), body)
        m.box((length * 0.34, 0, 1.62), (length * 0.24, width * 0.9, 0.55),
              glass)
        m.box((-length * 0.20, 0, 1.55), (length * 0.62, width * 1.02, 2.20),
              mat("Metal Painted"))
    wb, tw = length * 0.31, width / 2 - 0.06
    zw = 0.34 if kind not in ("bus", "truck") else 0.45
    for sx in (-1, 1):
        for sy in (-1, 1):
            v, f = _disc(sx * wb, sy * tw, zw, zw, 0.16)
            m._add(v, f, tire)
    return m.build(name, KIT)


def _disc(cx, cy, cz, radius, width, segs=8):
    v, f = [], []
    for side in (-1, 1):
        for i in range(segs):
            a = 2 * math.pi * i / segs
            v.append((cx + radius * math.cos(a), cy + side * width / 2,
                      cz + radius * math.sin(a)))
    for i in range(segs):
        j = (i + 1) % segs
        f.append((i, j, j + segs, i + segs))
    f.append(tuple(range(segs)))
    f.append(tuple(range(2 * segs - 1, segs - 1, -1)))
    return v, f


HELI_MAST = 3.0                   # where the rotor plane sits above the body
# Blade length from the hub, so the disc is twice this. It was 8.0, which is a
# 16 m disc over a 4 m fuselage - four times the body length, where a real
# helicopter runs about two and a half. The overlapping pairs hid it: half the
# blades were on top of each other, so the thing read as smaller than it was.
BLADE = 4.6


def helicopter(name):
    """The airframe only. The rotor is a separate asset - see heli_rotor().

    They used to be one mesh, which meant the blades could not turn: an instance
    shares one datablock and there is nothing inside it to animate."""
    m = Mesh()
    body, glass = mat("Accent Red"), mat("Car Glass")
    m.sphere((0, 0, 1.5), 1.35, body, segs=8, rings=5, scale=(1.5, 0.9, 0.8))
    m.box((1.5, 0, 1.75), (1.1, 1.1, 0.9), glass)
    m.box((-3.2, 0, 1.9), (4.2, 0.35, 0.35), body)
    m.box((-5.0, 0, 2.3), (0.3, 0.16, 1.1), body)
    m.cyl((0, 0, 2.5), 0.12, 0.5, mat("Tire"), segs=6)
    for sx in (-1, 1):
        m.box((sx * 0.9, 0, 0.35), (0.25, 2.6, 0.16), mat("Tire"))
    return m.build(name, KIT)


def heli_rotor(name):
    """Four blades and the hub, built around the ORIGIN.

    The origin is the axis of rotation, and that is the whole reason this is a
    separate asset rather than a second lump of geometry in the right place: the
    object is parented to the airframe and turned about its own Z. Geometry
    modelled at the mast height would orbit the mast instead of spinning on it.
    """
    m = Mesh()
    m.cyl((0, 0, -0.28), 0.20, 0.34, mat("Metal Dark"), segs=8)
    for k in range(4):
        # The centre goes at (L/2, 0) and _rotz swings it round. It used to be
        # written as (L/2*cos a, L/2*sin a) WITH the same _rotz applied, which
        # rotates the centre twice: blade 0 and blade 2 both landed at (+4, 0)
        # and blades 1 and 3 both at (-4, 0), so the "four blades" were two
        # overlapping pairs, one of them lying across the tail boom. It had been
        # like that since the kit was written and was invisible while the rotor
        # was a static lump - it only had to look vaguely like blades. Making it
        # turn is what exposed it, which is the usual way: motion is a test.
        a = math.pi / 2 * k
        m.box((BLADE / 2, 0.0, 0.0), (BLADE, 0.26, 0.06),
              mat("Metal Painted"), xform=_rotz(a, (0, 0, 0)))
    return m.build(name, KIT)


def _rotz(angle, pivot):
    from mathutils import Matrix, Vector
    p = Vector(pivot)
    return Matrix.Translation(p) @ Matrix.Rotation(angle, 4, "Z") @ \
        Matrix.Translation(-p)


# --- people ----------------------------------------------------------------
def person(name, shirt, pants, hair, skin="Skin Light", stride=0.0):
    """1.75 m, boxy, no face. Reads at 10-20 px, which is all it needs to."""
    m = Mesh()
    sh, pa, ha, sk = mat(shirt), mat(pants), mat(hair), mat(skin)
    for sx in (-1, 1):
        m.box((stride * sx, sx * 0.11, 0.42), (0.20, 0.17, 0.84), pa)
        m.box((stride * sx * 1.2, sx * 0.11, 0.03), (0.26, 0.17, 0.07),
              mat("Tire"))
    m.box((0, 0, 1.14), (0.26, 0.42, 0.58), sh)
    for sx in (-1, 1):
        swing = -stride * sx * 0.6
        m.box((swing, sx * 0.26, 1.14), (0.15, 0.14, 0.54), sh)
        m.box((swing, sx * 0.26, 0.84), (0.13, 0.12, 0.10), sk)
    m.box((0, 0, 1.50), (0.19, 0.17, 0.15), sk)
    m.box((0, 0, 1.63), (0.21, 0.19, 0.13), ha)
    return m.build(name, KIT)


# --- street furniture ------------------------------------------------------
def streetlight(name):
    m = Mesh()
    p = mat("Pole")
    m.cyl((0, 0, 0), 0.16, 0.35, p, segs=8)
    m.cyl((0, 0, 0.3), 0.09, 8.2, p, segs=8, top=0.07)
    for k in range(6):                       # the arm, as a shallow arc
        t = k / 5.0
        m.box((0.42 + t * 1.9, 0, 8.5 + 0.55 * math.sin(t * math.pi * 0.5)),
              (0.55, 0.10, 0.10), p)
    m.box((2.55, 0, 8.94), (0.95, 0.32, 0.12), p)
    m.box((2.55, 0, 8.86), (0.80, 0.26, 0.05), mat("Lamp"))
    return m.build(name, KIT)


def traffic_light(name):
    m = Mesh()
    p, dark = mat("Pole"), mat("Signal Body")
    m.cyl((0, 0, 0), 0.18, 0.4, p, segs=8)
    m.cyl((0, 0, 0.35), 0.10, 6.6, p, segs=8)
    m.box((3.0, 0, 6.85), (6.0, 0.11, 0.11), p)
    for x in (2.6, 5.2):
        m.box((x, 0, 6.35), (0.30, 0.36, 0.95), dark)
        for k, c in enumerate(("Signal Red", "Signal Amber", "Signal Green")):
            m.box((x, -0.19, 6.68 - k * 0.30), (0.16, 0.04, 0.16), mat(c))
    m.box((0.32, 0, 3.1), (0.26, 0.30, 0.62), dark)      # pedestrian head
    return m.build(name, KIT)


def sign_post(name):
    m = Mesh()
    m.cyl((0, 0, 0), 0.07, 2.6, mat("Pole"), segs=6)
    m.box((0, 0.02, 2.85), (0.95, 0.05, 0.42), mat("Marking"))
    return m.build(name, KIT)


def bench(name):
    m = Mesh()
    w = mat("Bench Wood")
    m.box((0, 0, 0.44), (1.9, 0.52, 0.08), w)
    m.box((0, -0.22, 0.68), (1.9, 0.08, 0.42), w)
    for sx in (-1, 1):
        m.box((sx * 0.72, 0, 0.22), (0.10, 0.46, 0.44), mat("Metal Dark"))
    return m.build(name, KIT)


# --- roof units ------------------------------------------------------------
def roof_hvac(name, w=3.2, d=2.2, h=1.5):
    m = Mesh()
    body = mat("Metal Painted")
    m.box((0, 0, h / 2), (w, d, h), body)
    m.box((0, 0, h + 0.06), (w * 0.7, d * 0.7, 0.12), mat("Metal Dark"))
    for sx in (-1, 1):
        m.box((sx * w * 0.28, 0, h * 0.55), (w * 0.34, d * 1.02, h * 0.5),
              mat("Metal Dark"))
    return m.build(name, KIT)


def roof_pipes(name, w=9.0, d=5.5):
    """The salmon pipe frame: a loop of pipe with a couple of boxes on it."""
    m = Mesh()
    p, r = mat("Roof Pipe"), 0.22
    for sy in (-1, 1):
        m.box((0, sy * d / 2, 0.55), (w, r, r), p)
    for sx in (-1, 1):
        m.box((sx * w / 2, 0, 0.55), (r, d, r), p)
    for x, y in ((-w * 0.22, d / 2), (w * 0.3, -d / 2)):
        m.box((x, y, 0.72), (1.5, 1.1, 1.0), p)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box((sx * w / 2, sy * d / 2, 0.22), (0.3, 0.3, 0.45), p)
    return m.build(name, KIT)


def roof_solar(name, cols=5, rows=3, pitch=2.0):
    m = Mesh()
    panel, frame = mat("Solar"), mat("Metal Dark")
    for i in range(cols):
        for j in range(rows):
            x = (i - (cols - 1) / 2) * pitch
            y = (j - (rows - 1) / 2) * (pitch * 0.78)
            m.box((x, y, 0.42), (pitch * 0.88, pitch * 0.6, 0.07), panel)
            m.box((x, y, 0.20), (0.08, 0.08, 0.40), frame)
    return m.build(name, KIT)


def roof_bulkhead(name, w=4.5, d=3.5, h=2.8):
    m = Mesh()
    m.box((0, 0, h / 2), (w, d, h), mat("Concrete Cool"))
    m.box((0, 0, h + 0.08), (w + 0.3, d + 0.3, 0.16), mat("Concrete Cool2"))
    m.box((0, -d / 2, h * 0.42), (1.0, 0.1, h * 0.72), mat("Metal Dark"))
    return m.build(name, KIT)


def roof_tank(name):
    m = Mesh()
    m.cyl((0, 0, 0.9), 1.5, 2.6, mat("Metal Painted"), segs=10)
    for k in range(4):
        a = math.pi / 2 * k
        m.box((1.3 * math.cos(a), 1.3 * math.sin(a), 0.45), (0.14, 0.14, 0.9),
              mat("Metal Dark"))
    return m.build(name, KIT)


def roof_dish(name):
    m = Mesh()
    m.cyl((0, 0, 0), 0.5, 0.2, mat("Metal Dark"), segs=8)
    m.cyl((0, 0, 0.2), 0.12, 1.1, mat("Pole"), segs=6)
    m.sphere((0, 0, 1.6), 1.05, mat("Metal Painted"), segs=10, rings=4,
             scale=(1, 1, 0.28))
    return m.build(name, KIT)


def pingpong(name):
    m = Mesh()
    m.box((0, 0, 0.72), (2.7, 1.5, 0.05), mat("Table Green"))
    m.box((0, 0, 0.80), (0.03, 1.55, 0.14), mat("Marking"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box((sx * 1.2, sy * 0.6, 0.36), (0.07, 0.07, 0.72),
                  mat("Metal Dark"))
    return m.build(name, KIT)


# --- palette additions -----------------------------------------------------
EXTRA = [
    ("Car Red", "#c0332c", 0.35), ("Car Teal", "#1f9e93", 0.35),
    ("Car Blue", "#3d6fb5", 0.35), ("Car White", "#e8e9e6", 0.35),
    ("Car Dark", "#2f3336", 0.35), ("Car Yellow", "#e0a81c", 0.35),
    ("Car Silver", "#a8adb0", 0.30), ("Car Glass", "#9fc4cc", 0.10),
    ("Tire", "#1c1d1f", 0.85), ("Pole", "#9a9d9e", 0.45),
    ("Lamp", "#f2efe2", 0.30), ("Signal Body", "#232628", 0.60),
    ("Signal Red", "#d02b22", 0.35), ("Signal Amber", "#e2a01c", 0.35),
    ("Signal Green", "#2fa04a", 0.35), ("Metal Dark", "#3c4043", 0.55),
    ("Solar", "#26436e", 0.20), ("Bench Wood", "#8a5a34", 0.70),
    ("Table Green", "#1c7a46", 0.55), ("Skin Light", "#e0b48c", 0.75),
    ("Skin Mid", "#b57f52", 0.75), ("Skin Dark", "#6f4a30", 0.75),
    ("Hair Dark", "#2b2320", 0.80), ("Hair Blonde", "#d9b25e", 0.80),
    ("Hair Red", "#a4482a", 0.80), ("Hair Grey", "#b9b6b0", 0.80),
    ("Shirt Blue", "#3f6fa8", 0.75), ("Shirt Red", "#b83b34", 0.75),
    ("Shirt Green", "#3f8f52", 0.75), ("Shirt White", "#e6e6e2", 0.75),
    ("Shirt Purple", "#6a4b9c", 0.75), ("Shirt Teal", "#2f9c93", 0.75),
    ("Shirt Orange", "#d97b28", 0.75), ("Shirt Grey", "#7e8386", 0.75),
    ("Pants Navy", "#2c3a52", 0.75), ("Pants Denim", "#4a6484", 0.75),
    ("Pants Khaki", "#a89168", 0.75), ("Pants Dark", "#33363a", 0.75),
    ("Water", "#6fb6cc", 0.08), ("Glass Roof", "#c8d6d8", 0.10),
]


def build_kit():
    for name, hexcol, rough in EXTRA:
        pbrmat(name, hexcol, roughness=rough)

    assets = {}
    fol = ["Foliage Dark", "Foliage Mid", "Foliage Light"]
    for i, (h, lobes) in enumerate([(9.0, 3), (7.0, 4), (11.0, 3), (6.2, 2)]):
        assets[f"Tree{i}"] = tree_broadleaf(f"Tree{i}", h, mat(fol[i % 3]),
                                            lobes, 100 + i)
    for i, (h, t) in enumerate([(10.5, 3), (8.0, 2)]):
        assets[f"Conifer{i}"] = tree_conifer(f"Conifer{i}", h,
                                             mat("Foliage Dark"), t, 200 + i)
    assets["Hedge"] = hedge("Hedge", 4.0, 1.2, 1.0, mat("Foliage Mid"))
    assets["Shrub"] = hedge("Shrub", 1.6, 1.6, 1.1, mat("Foliage Light"))

    cars = [("CarRed", "Car Red", "sedan"), ("CarWhite", "Car White", "sedan"),
            ("CarTeal", "Car Teal", "pickup"), ("CarBlue", "Car Blue", "van"),
            ("CarDark", "Car Dark", "sedan"),
            ("CarSilver", "Car Silver", "van")]
    for n, c, k in cars:
        assets[n] = car(n, c, kind=k)
    assets["Bus"] = car("Bus", "Car Yellow", length=11.0, width=2.5, kind="bus")
    assets["Truck"] = car("Truck", "Car White", length=8.0, width=2.4,
                          kind="truck")
    assets["Heli"] = helicopter("Heli")
    assets["HeliRotor"] = heli_rotor("HeliRotor")

    people = [("Shirt Blue", "Pants Navy", "Hair Dark", "Skin Light", 0.16),
              ("Shirt Red", "Pants Denim", "Hair Blonde", "Skin Light", 0.0),
              ("Shirt Green", "Pants Khaki", "Hair Dark", "Skin Mid", 0.20),
              ("Shirt White", "Pants Dark", "Hair Red", "Skin Light", 0.0),
              ("Shirt Purple", "Pants Denim", "Hair Grey", "Skin Dark", 0.14),
              ("Shirt Teal", "Pants Navy", "Hair Dark", "Skin Mid", 0.0),
              ("Shirt Orange", "Pants Khaki", "Hair Blonde", "Skin Light", 0.18),
              ("Shirt Grey", "Pants Dark", "Hair Dark", "Skin Dark", 0.0)]
    for i, (s, p, h, sk, st) in enumerate(people):
        assets[f"Person{i}"] = person(f"Person{i}", s, p, h, sk, st)

    assets["StreetLight"] = streetlight("StreetLight")
    assets["TrafficLight"] = traffic_light("TrafficLight")
    assets["SignPost"] = sign_post("SignPost")
    assets["Bench"] = bench("Bench")

    assets["RoofHVAC"] = roof_hvac("RoofHVAC")
    assets["RoofHVACSmall"] = roof_hvac("RoofHVACSmall", 1.8, 1.5, 1.0)
    assets["RoofPipes"] = roof_pipes("RoofPipes")
    assets["RoofPipesSmall"] = roof_pipes("RoofPipesSmall", 5.5, 3.6)
    assets["RoofSolar"] = roof_solar("RoofSolar")
    assets["RoofSolarBig"] = roof_solar("RoofSolarBig", 8, 5)
    assets["RoofBulkhead"] = roof_bulkhead("RoofBulkhead")
    assets["RoofTank"] = roof_tank("RoofTank")
    assets["RoofDish"] = roof_dish("RoofDish")
    assets["PingPong"] = pingpong("PingPong")
    return assets


def contact_sheet(assets):
    """Lay the whole kit out on a plane and look at it."""
    show = collection("KIT_PREVIEW")
    m = Mesh()
    m.quad(0, 0, 200, 200, 0.0, mat("Sidewalk"))
    m.build("preview_ground", show)

    names = list(assets)
    cols = 8
    for i, n in enumerate(names):
        x = (i % cols - (cols - 1) / 2) * 12.0
        y = ((i // cols) - (len(names) / cols - 1) / 2) * 12.0
        instance(assets[n], show, location=(x, y, 0))

    cam = bpy.data.objects["HeroCam"]
    cam.data.ortho_scale = 108.0
    blib.render(str(R / "kit_contact.png"), "EEVEE", samples=64,
                resolution=(1800, 1000),
                exposure=bpy.context.scene.view_settings.exposure)
    bpy.data.collections.remove(show)
    cam.data.ortho_scale = 620.0


def main():
    global KIT
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    KIT = collection("KIT")

    # Purge before rebuilding, and understand what that does before running it.
    #
    # Without this, a second run builds an object called Heli.001 while every
    # instance in the city goes on pointing at Heli, so the edit appears to do
    # nothing at all and raises no error. That is the trap CLAUDE.md warns about
    # and this is the cause of it, not a property of the universe.
    #
    # Purging fixes the naming and makes the warning WORSE in the honest
    # direction: a re-run now leaves every existing instance pointing at a mesh
    # whose source object is gone, so it MUST be followed by the whole chain
    # from 03. Broken loudly beats broken silently.
    stale = len(KIT.objects)
    for ob in list(KIT.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    if stale:
        print(f"  purged {stale} stale kit objects: re-run the chain from 03")

    assets = build_kit()
    print(f"\n  kit: {len(assets)} assets")
    contact_sheet(assets)

    KIT.hide_render = KIT.hide_viewport = True
    u, t = counts()
    print(f"  triangles: {u} unique / {t} total")
    blib.save(str(R / "city.blend"))


main()
