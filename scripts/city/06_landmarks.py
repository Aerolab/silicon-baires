"""Step 06 — landmarks.

The pieces that break the grid and give the frame something to hang on: a
stadium, a curved organic building, an open-deck parking structure and a
construction site with lattice cranes. Everything else in the city is a box on
a lot; these are the exceptions, and the reference leans on them hard.

    ./bl scripts/city/06_landmarks.py
"""
import sys, pathlib, math, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Matrix, Vector
from _common import Mesh, collection, instance, mat, pbrmat, rng, counts

R = ROOT / "renders"
BLOCK, PITCH, HALF = 90.0, 112.0, 3.0

CELLS = {"stadium": (5, 1), "blob": (1, 5), "garage": (5, 3)}
SITE = [(3, 1), (2, 1)]


def cell(i, j):
    return (i - HALF) * PITCH, (j - HALF) * PITCH


def xf(cx, cy, rot=0.0, sx=1.0, sy=1.0):
    return (Matrix.Translation(Vector((cx, cy, 0))) @
            Matrix.Rotation(rot, 4, "Z") @
            Matrix.Diagonal(Vector((sx, sy, 1.0, 1.0))))


def ring_poly(r0, r1, segs=48):
    ang = [2 * math.pi * i / segs for i in range(segs + 1)]
    return ([(r1 * math.cos(a), r1 * math.sin(a)) for a in ang] +
            [(r0 * math.cos(a), r0 * math.sin(a)) for a in reversed(ang)])


# --- stadium ---------------------------------------------------------------
def stadium(m, cx, cy, lift):
    x = xf(cx, cy, math.radians(20), 1.22, 1.0)
    pitch_r = 20.0
    m.arc_band(0.0, pitch_r, 0, 2 * math.pi, lift + 0.05, mat("Grass"),
               segs=48, xform=x)
    m.arc_band(pitch_r * 0.55, pitch_r * 0.58, 0, 2 * math.pi, lift + 0.07,
               mat("Marking"), segs=48, xform=x)
    steps = 7
    for k in range(steps):
        r0 = pitch_r + k * 2.6
        r1 = r0 + 2.6
        h = lift + 1.6 + k * 2.4
        m.prism(ring_poly(r0, r1), lift, h,
                mat("Concrete Cool" if k % 2 else "Concrete Cool2"), x)
    outer = pitch_r + steps * 2.6
    m.prism(ring_poly(outer, outer + 1.6), lift, lift + 1.6 + steps * 2.4 + 1.2,
            mat("Concrete Warm"), x)
    # the roof ring, cantilevered inwards over the seating
    m.prism(ring_poly(outer - 7.0, outer + 3.0),
            lift + 1.6 + steps * 2.4 + 3.4, lift + 1.6 + steps * 2.4 + 4.2,
            mat("Roof Deck"), x)
    for k in range(24):
        a = 2 * math.pi * k / 24
        m.box(((outer + 1.0) * math.cos(a), (outer + 1.0) * math.sin(a),
               lift + (1.6 + steps * 2.4 + 3.4) / 2),
              (1.0, 1.0, 1.6 + steps * 2.4 + 3.4), mat("Metal Dark"), x)


# --- curved organic building ----------------------------------------------
def rounded_rect(w, d, radius, segs=6):
    pts = []
    for (sx, sy) in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        cxr, cyr = sx * (w / 2 - radius), sy * (d / 2 - radius)
        base = {(1, 1): 0.0, (-1, 1): math.pi / 2,
                (-1, -1): math.pi, (1, -1): 3 * math.pi / 2}[(sx, sy)]
        for k in range(segs + 1):
            a = base + math.pi / 2 * k / segs
            pts.append((cxr + radius * math.cos(a), cyr + radius * math.sin(a)))
    return pts


def blob(m, cx, cy, lift):
    """Floors that slide and swell along a curve: the Zaha-ish building."""
    floors, fh = 5, 3.9
    for k in range(floors):
        t = k / (floors - 1)
        ox = math.sin(t * 2.4) * 13.0
        oy = math.cos(t * 1.7) * 7.0
        w = 62.0 - abs(t - 0.4) * 26.0
        d = 26.0 + math.sin(t * 3.1) * 6.0
        z0 = lift + k * fh
        x = xf(cx + ox, cy + oy, 0.22 * math.sin(t * 2.0))
        m.prism(rounded_rect(w, d, 9.0), z0, z0 + fh * 0.72,
                mat("Concrete Warm"), x)
        m.prism(rounded_rect(w - 2.2, d - 2.2, 8.4), z0 + fh * 0.72,
                z0 + fh, mat("Glass Light"), x)
    top = lift + floors * fh
    x = xf(cx, cy)
    m.prism(rounded_rect(40.0, 22.0, 8.0), top, top + 0.5, mat("Roof Deck"), x)
    m.prism(rounded_rect(26.0, 14.0, 5.0), top + 0.5, top + 0.6, mat("Water"),
            xf(cx + 6, cy - 2))


# --- open-deck parking structure -------------------------------------------
def garage(m, kit, coll, cx, cy, lift, r):
    w, d, levels, fh = 74.0, 56.0, 5, 3.1
    x = xf(cx, cy)
    for k in range(levels):
        z = lift + k * fh
        m.slab(0, 0, w, d, z, z + 0.35, mat("Concrete Cool"), x)
        for sy in (-1, 1):                       # the open spandrel band
            m.slab(0, sy * d / 2, w, 0.4, z + 0.35, z + 1.15,
                   mat("Concrete Cool2"), x)
        for sx in (-1, 1):
            m.slab(sx * w / 2, 0, 0.4, d, z + 0.35, z + 1.15,
                   mat("Concrete Cool2"), x)
        for ix in range(6):                      # columns
            for iy in range(4):
                m.box((-w / 2 + 7 + ix * (w - 14) / 5,
                       -d / 2 + 7 + iy * (d - 14) / 3, z + fh / 2),
                      (1.1, 1.1, fh), mat("Concrete Cool"), x)
        if k:
            for row in range(3):
                yy = cy - d / 2 + 11 + row * (d - 22) / 2
                for c in range(9):
                    if r.random() < 0.3:
                        continue
                    instance(kit[r.choice(["CarRed", "CarWhite", "CarTeal",
                                           "CarBlue", "CarDark",
                                           "CarSilver"])], coll,
                             (cx - w / 2 + 8 + c * (w - 16) / 8, yy,
                              z + 0.37), math.pi / 2)
    top = lift + levels * fh
    m.slab(0, 0, w, d, top, top + 0.4, mat("Roof Deck"), x)
    m.slab(0, d / 2, w, 0.4, top + 0.4, top + 1.3, mat("Concrete Cool2"), x)


# --- construction ----------------------------------------------------------
def lattice(m, length, section, material, xform, bays=None):
    """A crane member: four chords plus zig-zag bracing."""
    bays = bays or max(2, int(length / (section * 1.4)))
    s = section / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box((length / 2, sx * s, sy * s), (length, 0.22, 0.22),
                  material, xform)
    for k in range(bays):
        x0 = k * length / bays
        x1 = (k + 1) * length / bays
        for sy in (-1, 1):
            m.box(((x0 + x1) / 2, 0, sy * s), (0.16, section, 0.16),
                  material, xform)
        for sx in (-1, 1):
            m.box(((x0 + x1) / 2, sx * s, 0), (0.16, 0.16, section),
                  material, xform)


def crane(m, cx, cy, height, jib, rot):
    y = mat("Accent Yellow")
    mast = Matrix.Translation(Vector((cx, cy, 0))) @ \
        Matrix.Rotation(rot, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")
    lattice(m, height, 2.6, y, mast)
    base = xf(cx, cy, rot)
    m.box((0, 0, 0.6), (5.0, 5.0, 1.2), mat("Concrete Cool"), base)
    top = Matrix.Translation(Vector((cx, cy, height))) @ \
        Matrix.Rotation(rot, 4, "Z")
    lattice(m, jib, 2.0, y, top)
    lattice(m, jib * 0.32, 2.0, y,
            top @ Matrix.Rotation(math.pi, 4, "Z"))
    m.box((-jib * 0.30, 0, 1.2), (5.0, 2.6, 2.4), mat("Metal Dark"), top)
    m.box((2.0, 0, 2.6), (3.0, 2.6, 3.0), y, top)
    hook = jib * 0.62
    m.box((hook, 0, -6.0), (0.14, 0.14, 12.0), mat("Metal Dark"), top)
    m.box((hook, 0, -12.6), (1.6, 1.6, 1.4), mat("Metal Dark"), top)


def construction(m, kit, coll, cx, cy, lift, r, frame=True):
    if frame:
        cols, rows, levels = 6, 4, 4
        w, d, fh = 60.0, 40.0, 3.9
        x = xf(cx, cy)
        for ix in range(cols):
            for iy in range(rows):
                px = -w / 2 + ix * w / (cols - 1)
                py = -d / 2 + iy * d / (rows - 1)
                m.box((px, py, lift + levels * fh / 2), (0.55, 0.55,
                      levels * fh), mat("Accent Red"), x)
        for k in range(1, levels + 1):
            z = lift + k * fh
            for iy in range(rows):
                py = -d / 2 + iy * d / (rows - 1)
                m.slab(0, py, w, 0.4, z - 0.4, z, mat("Accent Red"), x)
            for ix in range(cols):
                px = -w / 2 + ix * w / (cols - 1)
                m.slab(px, 0, 0.4, d, z - 0.4, z, mat("Accent Red"), x)
            if k <= 2:
                m.quad(0, 0, w * 0.55, d * 0.7, z + 0.01,
                       mat("Concrete Cool"), x)
    for _ in range(5):                            # spoil heaps and materials
        px = cx + r.uniform(-38, 38)
        py = cy + r.uniform(-30, 30)
        m.cone((px, py, lift), r.uniform(3.0, 6.0), r.uniform(2.0, 4.0),
               mat("Dirt"), segs=7)
    for _ in range(4):
        px, py = cx + r.uniform(-35, 35), cy + r.uniform(-30, 30)
        for k in range(3):
            m.box((px, py, lift + 0.3 + k * 0.55), (7.0, 1.4, 0.5),
                  mat("Metal Painted"))


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    kit = {ob.name: ob for ob in bpy.data.collections["KIT"].objects}
    lots = {tuple(l["key"]): l for l in
            json.loads((R / "city_lots.json").read_text())}

    for name in ("LANDMARKS", "LANDMARK_PROPS"):
        if name in bpy.data.collections:
            c = bpy.data.collections[name]
            for ob in list(c.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
    lm = collection("LANDMARKS")
    lp = collection("LANDMARK_PROPS")

    r = rng(777)
    m = Mesh()

    def lift_of(i, j):
        key = (str(i), str(j))
        return lots[key]["lift"] if key in lots else 0.75

    i, j = CELLS["stadium"]
    cx, cy = cell(i, j)
    stadium(m, cx, cy, lift_of(i, j))

    i, j = CELLS["blob"]
    cx, cy = cell(i, j)
    blob(m, cx, cy, lift_of(i, j))

    i, j = CELLS["garage"]
    cx, cy = cell(i, j)
    garage(m, kit, lp, cx, cy, lift_of(i, j), r)

    for n, (i, j) in enumerate(SITE):
        cx, cy = cell(i, j)
        construction(m, kit, lp, cx, cy, lift_of(i, j), r, frame=(n == 0))
    cx, cy = cell(*SITE[0])
    crane(m, cx - 34, cy - 26, 46.0, 40.0, math.radians(35))
    cx, cy = cell(*SITE[1])
    crane(m, cx + 30, cy + 24, 38.0, 34.0, math.radians(200))
    for _ in range(3):
        instance(kit["Truck"], lp,
                 (cx + r.uniform(-35, 35), cy + r.uniform(-30, 30), 0.0),
                 r.uniform(0, 6.28))

    m.build("landmarks", lm)
    u, t = counts()
    print(f"\n  triangles: {u} unique / {t} total")

    cam = bpy.data.objects["HeroCam"]
    exposure = bpy.context.scene.view_settings.exposure
    blib.render(str(R / "city_06_hero.png"), "EEVEE", samples=64,
                resolution=(1600, 900), exposure=exposure)
    blib.save(str(R / "city.blend"))


main()
