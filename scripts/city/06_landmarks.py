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
from _solids import Solids

R = ROOT / "renders"
BLOCK, PITCH, HALF = 64.0, 76.0, 4.0

CELLS = {"stadium": (6, 1), "blob": (1, 6), "garage": (7, 4)}
SITE = [(5, 7), (2, 0)]     # (4, 5) now carries the title


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
def arc_poly(r0, r1, a0, a1, segs=2):
    """Closed outline of an annulus sector, for prism(). ring_poly's wedge."""
    ang = [a0 + (a1 - a0) * i / segs for i in range(segs + 1)]
    p = [(r1 * math.cos(a), r1 * math.sin(a)) for a in ang]
    p += [(r0 * math.cos(a), r0 * math.sin(a)) for a in reversed(ang)]
    return p


# El Monumental, at this city's scale, which is about a quarter of life size -
# the blocks are 76 m where a real one is 110, and the stadium has to fit a
# block. So these are not the real stadium's metres, they are its proportions.
#
# The first version was a smooth white drum with a lawn in the hole, and it read
# as "a stadium" and nothing more. Three things carry which ground it is, in the
# order they survive being 80 px wide:
#
#   1. THE ATHLETICS TRACK. A terracotta oval between the pitch and the stands.
#      Hardly any big stadium still has one and it is the fastest thing to read,
#      because it is a hard colour break against the green and it is visible
#      from directly above, which is where this camera is.
#   2. A RING THAT IS NOT UNIFORM. The ground was a horseshoe, open at one end,
#      until the Centenario stand closed it for the 1978 World Cup, and the ring
#      has never levelled out since. A perfect donut reads as any stadium; the
#      notch is most of the silhouette. It is put on the +x side so the camera,
#      which looks along -x, sees down into the bowl through it.
#   3. AN OVAL RATHER THAN A CIRCLE, with the roof over the two long sides only
#      and the ends open.
#
# NOTE ON WHICH MONUMENTAL. This is the long-standing configuration, the one
# with the running track. The 2023-24 remodelling lowered the pitch and rebuilt
# the lower ring, and I have not verified what became of the track - so this is
# the ground as it has looked for most of its life, not necessarily as it looks
# this season. Worth checking before anyone calls it current.
# THE WHOLE THING HAS TO FIT ITS LOT, which is 59 m inside a 64 m block. The
# first rebuild forgot that: deeper stands and stair towers took the outside
# radius from 27.2 to 30.6, which with the 1.30 oval is 79 m across - fifteen
# metres wider than the block. It overhung the pavement on both sides and
# 99_check_overlap found five trees and people standing inside it. The rake got
# thinner rather than the pitch smaller, because the pitch and the track are the
# cue and the depth of the bowl is not.
PITCH_R = 10.0                    # half the short axis, inside the track
TRACK_W = 2.9
STAND_R0 = PITCH_R + TRACK_W + 0.6
TIERS, TIER_W = 9, 0.88
STAND_H = 17.5                    # the tall sides, above the block
LOW_END = 0.50                    # what the open end keeps of that
LOW_HALF = math.radians(42)       # how far round the notch runs
SEGS = 48


def stand_h(a):
    """Height factor of the ring at local angle a. Deliberately not constant."""
    d = abs((a + math.pi) % (2 * math.pi) - math.pi)
    if d >= LOW_HALF:
        return 1.0
    t = d / LOW_HALF
    return LOW_END + (1.0 - LOW_END) * (t * t * (3.0 - 2.0 * t))


def stadium(m, cx, cy, lift):
    x = xf(cx, cy, math.radians(20), 1.30, 1.0)
    cool, cool2 = mat("Concrete Cool"), mat("Concrete Cool2")
    warm, red = mat("Concrete Warm"), mat("Stadium Red")

    # the track, then the pitch as a RECTANGLE inside it. A round pitch inside a
    # round track is a bullseye; the whole point of a track stadium seen from
    # above is the rectangle sitting in the oval.
    m.arc_band(0.0, PITCH_R + TRACK_W, 0, 2 * math.pi, lift + 0.04,
               mat("Track Clay"), segs=56, xform=x)
    m.box((0, 0, lift + 0.07), (18.4, 15.2, 0.06), mat("Pitch Grass"), x)
    m.box((0, 0, lift + 0.10), (0.16, 15.2, 0.02), mat("Marking"), x)
    m.arc_band(2.6, 2.9, 0, 2 * math.pi, lift + 0.10, mat("Marking"),
               segs=28, xform=x)

    outer = STAND_R0 + TIERS * TIER_W
    for k in range(SEGS):
        a0, a1 = 2 * math.pi * k / SEGS, 2 * math.pi * (k + 1) / SEGS
        f = stand_h((a0 + a1) / 2)
        for t in range(TIERS):
            r0 = STAND_R0 + t * TIER_W
            h = lift + 1.3 + (STAND_H - 1.3) * ((t + 1) / TIERS) * f
            m.prism(arc_poly(r0, r0 + TIER_W, a0, a1), lift, h,
                    cool if t % 2 else cool2, x)
        top = lift + 1.0 + (STAND_H + 1.4 - 1.0) * f
        m.prism(arc_poly(outer, outer + 1.2, a0, a1), lift, top, warm, x)
        m.prism(arc_poly(outer - 0.05, outer + 1.3, a0, a1),
                top - 1.9, top - 0.7, red, x)

    # The roof, over the two long sides only. The long axis is local x, so the
    # long SIDES are at plus and minus 90 degrees from it.
    #
    # It has to be MEAN. A first pass cantilevered 7.6 m of it inwards and the
    # stadium turned into a covered dish: this camera looks down at 30 degrees,
    # so a roof that covers half the rake hides the bowl, and the bowl is the
    # only reason to model a stadium instead of a drum. 4.4 m, thin, and only
    # over the upper tier.
    for c in (math.pi / 2, -math.pi / 2):
        z = lift + STAND_H + 1.9
        m.prism(arc_poly(outer - 3.8, outer + 1.5, c - 0.80, c + 0.80, segs=12),
                z, z + 0.42, mat("Roof Deck"), x)
        for k in range(6):
            a = c - 0.80 + 1.60 * k / 5
            m.box(((outer - 3.1) * math.cos(a), (outer - 3.1) * math.sin(a),
                   z + 0.72), (1.3, 0.42, 0.42), mat("Lamp"), x)

    # stair towers at the open end, where there is no roof to break the drum
    for k in range(3):
        a = math.radians(-52 + 52 * k)
        h = 1.0 + (STAND_H + 1.4 - 1.0) * stand_h(a)
        m.box(((outer + 0.6) * math.cos(a), (outer + 0.6) * math.sin(a),
               lift + h / 2), (1.8, 1.8, h), warm, x)


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
        ox = math.sin(t * 2.4) * 9.0
        oy = math.cos(t * 1.7) * 5.0
        w = 46.0 - abs(t - 0.4) * 18.0
        d = 20.0 + math.sin(t * 3.1) * 5.0
        z0 = lift + k * fh
        x = xf(cx + ox, cy + oy, 0.22 * math.sin(t * 2.0))
        m.prism(rounded_rect(w, d, 7.0), z0, z0 + fh * 0.72,
                mat("Concrete Warm"), x)
        m.prism(rounded_rect(w - 2.0, d - 2.0, 6.6), z0 + fh * 0.72,
                z0 + fh, mat("Glass Light"), x)
    top = lift + floors * fh
    x = xf(cx, cy)
    m.prism(rounded_rect(30.0, 17.0, 6.0), top, top + 0.5, mat("Roof Deck"), x)
    m.prism(rounded_rect(19.0, 10.0, 4.0), top + 0.5, top + 0.6, mat("Water"),
            xf(cx + 6, cy - 2))


# --- open-deck parking structure -------------------------------------------
def garage(m, kit, coll, cx, cy, lift, r):
    w, d, levels, fh = 55.0, 44.0, 5, 3.1
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
    # -90 deg, not +90: rotating +X about Y by +90 sends it to -Z, which buries
    # the mast underground and leaves the jib floating in mid-air on its own.
    mast = Matrix.Translation(Vector((cx, cy, 0))) @ \
        Matrix.Rotation(rot, 4, "Z") @ Matrix.Rotation(-math.pi / 2, 4, "Y")
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
        cols, rows, levels = 4, 3, 3
        w, d, fh = 30.0, 22.0, 3.9
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
        px = cx + r.uniform(-26, 26)
        py = cy + r.uniform(-22, 22)
        m.cone((px, py, lift), r.uniform(3.0, 6.0), r.uniform(2.0, 4.0),
               mat("Dirt"), segs=7)
    for _ in range(4):
        px, py = cx + r.uniform(-24, 24), cy + r.uniform(-20, 20)
        for k in range(3):
            m.box((px, py, lift + 0.3 + k * 0.55), (7.0, 1.4, 0.5),
                  mat("Metal Painted"))


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    kit = {ob.name: ob for ob in bpy.data.collections["KIT"].objects}
    lots = {tuple(l["key"]): l for l in
            json.loads((R / "city_lots.json").read_text())["lots"]}

    for name in ("LANDMARKS", "LANDMARK_PROPS"):
        if name in bpy.data.collections:
            c = bpy.data.collections[name]
            for ob in list(c.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
    lm = collection("LANDMARKS")
    lp = collection("LANDMARK_PROPS")

    # The track is the loudest cue in the stadium, so it gets a real colour
    # rather than a tint of the road: brick dust, warm and a good deal more
    # saturated than anything else on that block, which is what makes it read
    # against the pitch from directly above.
    pbrmat("Track Clay", "#b1573c", 0.92)
    pbrmat("Pitch Grass", "#3f8a39", 0.94)
    pbrmat("Stadium Red", "#bd2b2f", 0.82)

    r = rng(777)
    m = Mesh()
    sol = Solids()

    def lot_of(i, j):
        """None when the arterial ate that cell: a landmark there would float."""
        return lots.get((str(i), str(j)))

    # the rectangle each landmark sits inside. The stadium and the blob are
    # round, so their box claims more ground than they occupy: over-protective
    # is the right way to be wrong here, since the cost is a tree that could
    # have stood a metre closer.
    # The stadium's is derived from its own constants rather than typed in:
    # it was typed in, the stadium was rebuilt bigger, and the two silently
    # disagreed by seven metres a side until the overlap check found trees
    # inside the stands. The widest thing is the facade on the long axis and
    # the roof on the short one.
    _st_out = STAND_R0 + TIERS * TIER_W
    FOOT = {"stadium": ((_st_out + 1.2) * 1.30 * 2 + 1.0,
                        (_st_out + 1.5) * 2 + 1.0, math.radians(20), 17.0),
            "blob": (64.0, 40.0, 0.0, 21.0),
            "garage": (56.0, 45.0, 0.0, 17.5)}

    for name, fn in (
            ("stadium", lambda l: stadium(m, l["x"], l["y"], l["lift"])),
            ("blob", lambda l: blob(m, l["x"], l["y"], l["lift"])),
            ("garage", lambda l: garage(m, kit, lp, l["x"], l["y"],
                                        l["lift"], r))):
        lot = lot_of(*CELLS[name])
        if lot is None:
            print(f"  {name} skipped: the arterial took its cell")
            continue
        fn(lot)
        fw, fd, frot, fh = FOOT[name]
        sol.add(lot["x"], lot["y"], fw, fd, frot, 0.0, lot["lift"] + fh)

    for k, (i, j) in enumerate(SITE):
        lot = lot_of(i, j)
        if lot is None:
            continue
        construction(m, kit, lp, lot["x"], lot["y"], lot["lift"], r,
                     frame=(k == 0))
        if k == 0:
            sol.add(lot["x"], lot["y"], 30.0, 22.0, 0.0, 0.0,
                    lot["lift"] + 11.7)
    for k, (i, j) in enumerate(SITE):
        lot = lot_of(i, j)
        if lot is None:
            continue
        cx, cy = lot["x"], lot["y"]
        mx, my = cx - 24 + k * 45, cy - 19 + k * 36
        crane(m, mx, my, 44.0 - k * 8, 34.0 - k * 4,
              math.radians(35 + k * 165))
        sol.add(mx, my, 5.0, 5.0, 0.0, 0.0, 44.0 - k * 8)
        tx, ty, trot = (cx + r.uniform(-24, 24), cy + r.uniform(-20, 20),
                        r.uniform(0, 6.28))
        if sol.hit(tx, ty, 0.0, 4.2) is None:      # a truck is 8 m long
            instance(kit["Truck"], lp, (tx, ty, 0.0), trot)

    m.build("landmarks", lm)
    sol.merge_into(R / "city_solids.json", "landmarks")
    u, t = counts()
    print(f"\n  triangles: {u} unique / {t} total")

    cam = bpy.data.objects["HeroCam"]
    exposure = bpy.context.scene.view_settings.exposure
    blib.render(str(R / "city_06_hero.png"), "EEVEE", samples=64,
                resolution=(1600, 900), exposure=exposure)
    blib.save(str(R / "city.blend"))


main()
