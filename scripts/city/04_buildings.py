"""Step 04 — buildings: massing, facades, roofs.

Every building is a stack of floors. A floor is a solid spandrel band with a
recessed glass band above it and thin mullions across the glass, which is the
pattern the reference repeats everywhere. Four facade styles cover the whole
city; footprints are rectangles combined into L, U, T and bar shapes.

Roof props come from the KIT as instances, because they repeat constantly.

    ./bl scripts/city/04_buildings.py
"""
import sys, pathlib, math, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Matrix, Vector
from _common import Mesh, collection, instance, mat, rng, counts

R = ROOT / "renders"

BLOCK, STREET, PITCH, WALK = 90.0, 22.0, 112.0, 4.0
EXTENT, HALF = 7, 3.0
FLOOR = 3.8
GROUND = 4.6                  # taller ground floor, like the reference
PLAZA_R, RING_R = 48.0, 70.0
SECTOR_R, CLEAR_R = 160.0, 172.0

FAMILIES = [
    ("Concrete Warm", "Glass Light"),
    ("Concrete Warm", "Glass Light"),
    ("Concrete Warm2", "Glass Light"),
    ("Concrete Cool", "Glass Dark"),
    ("Concrete Cool2", "Glass Light"),
    ("Concrete Warm", "Glass Dark"),
    ("Brick Warm", "Glass Dark"),
    ("Facade Teal", "Glass Light"),
    ("Concrete Dark", "Glass Light"),
]

# cells that get something other than a plain low-rise campus
TALL = {(1, 1): 22, (5, 5): 14, (2, 6): 11, (6, 2): 9, (1, 4): 10}
LANDMARKS = {(5, 1), (1, 5), (5, 3)}     # step 06 owns these plots


def xf(cx, cy, rot):
    return Matrix.Translation(Vector((cx, cy, 0))) @ Matrix.Rotation(rot, 4, "Z")


def footprint(kind, w, d):
    """Wings, in local coordinates. Overlaps are fine: they end up inside."""
    if kind == "L":
        return [(0, -d / 4, w, d / 2), (-w / 4, d / 4, w / 2, d / 2)]
    if kind == "U":
        return [(0, -d / 3, w, d / 3), (-w / 3, d / 6, w / 3, 2 * d / 3),
                (w / 3, d / 6, w / 3, 2 * d / 3)]
    if kind == "T":
        return [(0, d / 4, w, d / 2), (0, -d / 4, w / 2, d / 2)]
    if kind == "bar":
        return [(0, 0, w, d * 0.55)]
    return [(0, 0, w, d)]


def facade_ring(m, ox, oy, w, d, z0, h, inset, material, xform):
    """Four walls of a box, without top or bottom: the cheap way to band."""
    t = max(inset, 0.01)
    m.slab(ox, oy + d / 2 - t / 2, w, t, z0, z0 + h, material, xform)
    m.slab(ox, oy - d / 2 + t / 2, w, t, z0, z0 + h, material, xform)
    m.slab(ox - w / 2 + t / 2, oy, t, d - 2 * t, z0, z0 + h, material, xform)
    m.slab(ox + w / 2 - t / 2, oy, t, d - 2 * t, z0, z0 + h, material, xform)


def mullions(m, ox, oy, w, d, z0, h, material, xform, pitch=3.0):
    """Thin verticals across the glass. Only the outer 25 cm is ever seen."""
    for sy, span, fixed in ((1, w, oy + d / 2), (-1, w, oy - d / 2)):
        n = max(1, int(span / pitch))
        for k in range(n + 1):
            x = ox - span / 2 + k * span / n
            m.slab(x, fixed - sy * 0.12, 0.16, 0.30, z0, z0 + h, material,
                   xform)
    for sx, span, fixed in ((1, d, ox + w / 2), (-1, d, ox - w / 2)):
        n = max(1, int(span / pitch))
        for k in range(n + 1):
            y = oy - span / 2 + k * span / n
            m.slab(fixed - sx * 0.12, y, 0.30, 0.16, z0, z0 + h, material,
                   xform)


def wing(m, ox, oy, w, d, floors, style, fam, xform, r):
    conc, glass = mat(fam[0]), mat(fam[1])
    z = 0.0
    # ground floor: mostly glass, set back, with the mass sitting on top
    m.slab(ox, oy, w - 1.0, d - 1.0, 0.0, GROUND, glass, xform)
    mullions(m, ox, oy, w - 1.0, d - 1.0, 0.3, GROUND - 0.6, conc, xform, 4.0)
    z = GROUND

    for f in range(floors):
        if style == "louvre":
            m.slab(ox, oy, w, d, z, z + 0.9, conc, xform)
            for k in range(3):
                zz = z + 1.05 + k * 0.85
                facade_ring(m, ox, oy, w + 0.5, d + 0.5, zz, 0.22, 0.25,
                            conc, xform)
            m.slab(ox, oy, w - 0.8, d - 0.8, z + 0.9, z + FLOOR, glass, xform)
        elif style == "punched":
            m.slab(ox, oy, w, d, z, z + FLOOR, conc, xform)
            for sy, fixed in ((1, oy + d / 2), (-1, oy - d / 2)):
                n = max(1, int(w / 4.2))
                for k in range(n):
                    x = ox - w / 2 + w / n * (k + 0.5)
                    m.slab(x, fixed - sy * 0.16, 1.5, 0.30, z + 1.2,
                           z + 3.0, glass, xform)
            for sx, fixed in ((1, ox + w / 2), (-1, ox - w / 2)):
                n = max(1, int(d / 4.2))
                for k in range(n):
                    y = oy - d / 2 + d / n * (k + 0.5)
                    m.slab(fixed - sx * 0.16, y, 0.30, 1.5, z + 1.2,
                           z + 3.0, glass, xform)
        elif style == "curtain":
            m.slab(ox, oy, w, d, z, z + FLOOR, glass, xform)
            facade_ring(m, ox, oy, w + 0.16, d + 0.16, z + FLOOR - 0.22, 0.22,
                        0.14, conc, xform)
            mullions(m, ox, oy, w, d, z, FLOOR, conc, xform, 2.6)
        else:                                   # banded, the default
            m.slab(ox, oy, w, d, z, z + 1.15, conc, xform)
            m.slab(ox, oy, w - 0.55, d - 0.55, z + 1.15, z + FLOOR, glass,
                   xform)
            mullions(m, ox, oy, w - 0.55, d - 0.55, z + 1.15, FLOOR - 1.15,
                     conc, xform, 3.0)
        z += FLOOR

    # parapet ring and roof plate. The deck is always a light concrete: in the
    # reference roofs read pale whatever colour the facade is.
    m.quad(ox, oy, w, d, z + 0.02, mat("Roof Deck"), xform)
    facade_ring(m, ox, oy, w, d, z, 0.85, 0.55, mat("Concrete Cool"), xform)
    return z + 0.85


def roof_props(kit, coll, cx, cy, w, d, top, rot, r, big):
    """Never leave a roof empty: it is most of what this camera sees."""
    placed = []
    pool = ["RoofHVAC", "RoofHVAC", "RoofHVACSmall", "RoofHVACSmall",
            "RoofPipes", "RoofPipes", "RoofPipesSmall", "RoofPipesSmall",
            "RoofSolar", "RoofBulkhead", "RoofBulkhead", "RoofTank",
            "RoofDish"]
    area = w * d
    n = max(3, min(14, int(area / 170)))
    for _ in range(n):
        name = r.choice(pool)
        if min(w, d) < 24 and name in ("RoofPipes", "RoofSolarBig"):
            name = "RoofPipesSmall"
        lx = r.uniform(-w / 2 + 6, w / 2 - 6)
        ly = r.uniform(-d / 2 + 5, d / 2 - 5)
        a = rot + r.choice([0, math.pi / 2])
        wx = cx + lx * math.cos(rot) - ly * math.sin(rot)
        wy = cy + lx * math.sin(rot) + ly * math.cos(rot)
        placed.append(instance(kit[name], coll, (wx, wy, top), a,
                               r.uniform(1.3, 2.1)))
    if r.random() < 0.25:
        lx, ly = r.uniform(-w / 4, w / 4), r.uniform(-d / 4, d / 4)
        wx = cx + lx * math.cos(rot) - ly * math.sin(rot)
        wy = cy + lx * math.sin(rot) + ly * math.cos(rot)
        placed.append(instance(kit["PingPong"], coll, (wx, wy, top), rot))
    return placed


def signage(m, cx, cy, w, d, top, rot, r):
    """Abstract volumes where the reference puts logos. No branding."""
    col = mat(r.choice(["Accent Red", "Accent Yellow", "Accent Magenta",
                        "Concrete Cool2", "Solar"]))
    x = xf(cx, cy, rot)
    length = min(w, d) * 0.72
    height = max(3.0, length * 0.28)
    if r.random() < 0.5:
        for sx in (-1, 1):                       # legs, so it reads as a sign
            m.slab(sx * length * 0.35, d / 2 - 1.4, 0.5, 0.5, top,
                   top + height * 0.5, mat("Metal Dark"), x)
        m.slab(0, d / 2 - 1.4, length, 0.7, top + height * 0.4,
               top + height * 1.4, col, x)
    else:
        m.slab(-w * 0.2, 0, 0.7, length, top + 0.2, top + height * 1.2, col, x)


def place_on_lot(m, kit, coll, cx, cy, size, lift, kind, r):
    """One to four buildings on a block, with setbacks."""
    if kind in ("park", "construction", "parking"):
        return
    tops = []
    plan = r.choice([1, 2, 2, 4])
    cells = {1: [(0, 0, 1.0, 1.0)],
             2: [(-0.25, 0, 0.5, 1.0), (0.25, 0, 0.5, 1.0)],
             4: [(-0.25, -0.25, 0.5, 0.5), (0.25, -0.25, 0.5, 0.5),
                 (-0.25, 0.25, 0.5, 0.5), (0.25, 0.25, 0.5, 0.5)]}[plan]
    if plan == 2 and r.random() < 0.5:
        cells = [(0, -0.25, 1.0, 0.5), (0, 0.25, 1.0, 0.5)]
    for (fx, fy, fw, fh) in cells:
        if r.random() < 0.12:
            continue                       # a gap: courtyard or car park
        w = size * fw - r.uniform(6.0, 12.0)
        d = size * fh - r.uniform(6.0, 12.0)
        if min(w, d) < 12:
            continue
        bx, by = cx + size * fx, cy + size * fy
        floors = r.choice([1, 1, 2, 2, 2, 3, 3, 4, 5])
        style = r.choice(["banded", "banded", "banded", "louvre", "punched"])
        fam = FAMILIES[r.randrange(len(FAMILIES))]
        kindf = r.choice(["rect", "rect", "L", "U", "T", "bar"])
        x = xf(bx, by, 0.0)
        top = 0.0
        for (ox, oy, ww, dd) in footprint(kindf, w, d):
            t = wing(m, ox, oy, ww, dd, floors, style, fam, x, r)
            top = max(top, t)
        roof = top - 0.83
        for (ox, oy, ww, dd) in footprint(kindf, w, d):
            roof_props(kit, coll, bx + ox, by + oy, ww, dd, roof, 0.0, r,
                       ww * dd > 700)
        if r.random() < 0.45:
            signage(m, bx, by, w, d, top, 0.0, r)
        tops.append(top)
    return tops


def place_on_sector(m, kit, coll, geom, lift, r):
    """Sector blocks: two buildings each, so the circus is not ringed by a wall."""
    a0, a1, r0, r1 = geom
    rm = (r0 + r1) / 2
    for k in (0, 1):
        f0 = a0 + (a1 - a0) * (0.04 + k * 0.5)
        f1 = a0 + (a1 - a0) * (0.46 + k * 0.5)
        am = (f0 + f1) / 2
        depth = (r1 - r0) * r.uniform(0.55, 0.8)
        rmid = r0 + depth / 2 + r.uniform(0.0, (r1 - r0) - depth)
        cx, cy = rmid * math.cos(am), rmid * math.sin(am)
        w = depth
        d = (f1 - f0) * rmid
        if min(w, d) < 13:
            continue
        floors = r.choice([1, 2, 2, 3, 3, 4, 6])
        fam = FAMILIES[r.randrange(len(FAMILIES))]
        style = r.choice(["banded", "banded", "curtain", "louvre", "punched"])
        x = xf(cx, cy, am)
        top = wing(m, 0, 0, w, d, floors, style, fam, x, r)
        roof_props(kit, coll, cx, cy, w, d, top - 0.83, am, r, True)
        if r.random() < 0.45:
            signage(m, cx, cy, w, d, top, am, r)


def build_towers(m, kit, coll, r):
    for (i, j), floors in TALL.items():
        cx, cy = (i - HALF) * PITCH, (j - HALF) * PITCH
        w = r.uniform(30, 42)
        d = r.uniform(26, 38)
        fam = FAMILIES[2] if floors > 12 else FAMILIES[0]
        style = "curtain" if floors > 12 else "banded"
        x = xf(cx, cy, 0.0)
        top = wing(m, 0, 0, w, d, floors, style, fam, x, r)
        roof_props(kit, coll, cx, cy, w, d, top - 0.83, 0.0, r, True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    kit = {ob.name: ob for ob in bpy.data.collections["KIT"].objects}
    from _common import pbrmat
    pbrmat("Brick Warm", "#a86a4c", 0.85)
    pbrmat("Facade Teal", "#2f7f74", 0.75)
    pbrmat("Concrete Dark", "#6e7276", 0.85)
    pbrmat("Roof Deck", "#d5d2c9", 0.88)

    for name in ("BUILDINGS", "ROOFPROPS"):
        if name in bpy.data.collections:
            c = bpy.data.collections[name]
            for ob in list(c.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
    bcoll = collection("BUILDINGS")
    pcoll = collection("ROOFPROPS")

    r = rng(90210)
    m = Mesh()

    lots = json.loads((R / "city_lots.json").read_text())
    for lot in lots:
        if lot["kind"] in ("sector", "island"):
            continue
        i, j = int(lot["key"][0]), int(lot["key"][1])
        if (i, j) in TALL or (i, j) in LANDMARKS:
            continue
        place_on_lot(m, kit, pcoll, lot["x"], lot["y"], lot["size"],
                     lot["lift"], lot["kind"], r)

    n = 8
    gap = STREET / ((RING_R + SECTOR_R) / 2)
    for k in range(n):
        a0 = 2 * math.pi * k / n + gap / 2
        a1 = 2 * math.pi * (k + 1) / n - gap / 2
        place_on_sector(m, kit, pcoll, (a0, a1, RING_R + WALK, SECTOR_R - WALK),
                        0.7, r)

    build_towers(m, kit, pcoll, r)
    m.build("buildings", bcoll)

    u, t = counts()
    print(f"\n  roof props: {len(pcoll.objects)}")
    print(f"  triangles: {u} unique / {t} total")

    cam = bpy.data.objects["HeroCam"]
    exposure = bpy.context.scene.view_settings.exposure
    blib.render(str(R / "city_04_hero.png"), "EEVEE", samples=64,
                resolution=(1600, 900), exposure=exposure)
    cam.data.ortho_scale = 190.0
    blib.render(str(R / "city_04_closeup.png"), "EEVEE", samples=64,
                resolution=(1600, 900), exposure=exposure)
    cam.data.ortho_scale = 620.0
    blib.save(str(R / "city.blend"))


main()
