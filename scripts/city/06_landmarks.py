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
from _common import (Mesh, collection, instance, mat, pbrmat, rng, counts,
                     srgb, R, LOTS, SOLIDS, open_city, save_city, purge,
                     preview, paint)
from _solids import Solids

# NO GRID CONSTANTS HERE, and that is the point. This file used to open with
# BLOCK, PITCH, HALF = 64.0, 76.0, 4.0 feeding a cell(i, j) that nothing ever
# called: the uniform-grid formula from the layout BEFORE step 03 went to
# per-row block sizes. The real grid is in city_lots.json, where the blocks run
# 52 to 76 m and the streets 12, 22 or 70. Anything that needs a plot reads the
# lots table, like main() does.

CELLS = {"stadium": (6, 1), "blob": (1, 6), "garage": (7, 4)}
SITE = [(5, 7), (2, 0)]     # (4, 5) now carries the title


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
# as "a stadium" and nothing more. The second added a track and a notch and read
# as "a stadium with a track". What was still wrong is the thing a photograph of
# the ground makes obvious in a second: from outside you SEE THE BOWL. The
# facade is low and the white-and-red rake stands above it. The old code ran the
# outer wall from the ground to the top of the stands, which is a drum with a
# lawn in it however good the lawn is.
#
# Four things carry which ground it is, in the order they survive being 80 px
# wide:
#
#   1. THE SEATS: white with big red chevrons. Every photograph of this place,
#      from 1978 to last week, is white and red zig-zags. It is the only cue
#      that is a colour break the size of the whole building, so it is the one
#      that reads first, and it is the one the model did not have at all.
#   2. THE FACADE IS LOWER THAN THE STANDS, mid-grey concrete banded with
#      advertising, with the white rake and the roof rim rising over it. This is
#      the whole silhouette. Under 40 px it is all that is left.
#   3. A RING THAT IS NOT UNIFORM. The ground was a horseshoe until the
#      Centenario stand closed it for 1978, and the ends have stayed lower.
#      The dip is on the +x side, so the camera, which looks along -x, still
#      sees down into the bowl.
#   4. AN OVAL RATHER THAN A CIRCLE, roofed the whole way round, with the
#      scoreboard slung between two red columns over the far end.
#
# NOTE ON WHICH MONUMENTAL. This is the ground AS IT IS NOW: the 2023-24
# remodelling lowered the pitch, rebuilt the lower ring and took the athletics
# track out. TRACK below puts it back for the configuration this place had for
# most of its life - the rest of the geometry is shared, since the remodelling
# rebuilt the inside of the bowl and left the drum around it alone.
#
# THE WHOLE THING HAS TO FIT ITS LOT, which is 59 m inside a 64 m block. An
# early rebuild forgot that: deeper stands and stair towers took the outside
# radius from 27.2 to 30.6, which with the 1.30 oval is 79 m across - fifteen
# metres wider than the block. It overhung the pavement on both sides and
# 99_check_overlap found five trees and people standing inside it. Every radius
# here is therefore left exactly where it was; this rebuild changes what fills
# them and how tall each piece is, and not how much ground the stadium takes.
TRACK = False                     # the 2023-24 remodelling took it out
PITCH_R = 10.0                    # half the short axis, inside the track
TRACK_W = 2.9
STAND_R0 = PITCH_R + TRACK_W + 0.6
TIERS, TIER_W = 9, 0.88
STAND_H = 17.5                    # the tall sides, above the block
LOW_END = 0.66                    # what the dipped end keeps of that
LOW_HALF = math.radians(50)       # how far round the dip runs
SEGS = 48
LOWER = 4                         # tiers below the band of boxes
BAND = 4                          # the dark tier: press boxes and hospitality
FACADE_H = 10.6                   # how high the ramp towers and the ads reach


def stand_h(a):
    """Height factor of the ring at local angle a. Deliberately not constant."""
    d = abs((a + math.pi) % (2 * math.pi) - math.pi)
    if d >= LOW_HALF:
        return 1.0
    t = d / LOW_HALF
    return LOW_END + (1.0 - LOW_END) * (t * t * (3.0 - 2.0 * t))


def seat_mat(k, t, white, red):
    """White seats, red chevrons: four V's around the upper ring.

    The pattern is per (segment, tier) rather than a texture, because at this
    scale the tiers ARE the pixels - nine of them up the rake, forty-eight
    round - and a painted stripe on a smooth cone would not survive the
    orthographic camera the way a step that changes colour does.
    """
    if t < LOWER:                             # lower ring: one red hoop
        return red if t == LOWER - 1 else white
    p = (k % (SEGS // 4)) / (SEGS // 4)        # 0..1 within one chevron
    v = abs(p * 2.0 - 1.0)                     # 1 at the ends, 0 in the middle
    u = (t - BAND - 0.5) / (TIERS - BAND - 1)  # how far up the upper ring
    return red if abs(u - v) < 0.30 else white


def stadium(m, cx, cy, lift):
    x = xf(cx, cy, math.radians(20), 1.30, 1.0)
    white, red = mat("Seat White"), mat("Seat Red")
    facade, dark = mat("Stadium Facade"), mat("Stadium Ad Dark")

    # The floor of the bowl: the track if this is the old ground, a plain dark
    # apron if it is the new one, and then the pitch as a RECTANGLE inside it.
    # A round pitch inside a round surround is a bullseye; the point of the
    # thing seen from above is the rectangle sitting in the oval.
    m.arc_band(0.0, PITCH_R + TRACK_W if TRACK else STAND_R0, 0, 2 * math.pi,
               lift + 0.04,
               mat("Track Clay") if TRACK else mat("Stadium Apron"),
               segs=56, xform=x)
    pw, pd = (18.4, 15.2) if TRACK else (20.4, 16.6)
    m.box((0, 0, lift + 0.07), (pw, pd, 0.06), mat("Pitch Grass"), x)
    m.box((0, 0, lift + 0.10), (0.16, pd, 0.02), mat("Marking"), x)
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
                    dark if t == BAND else seat_mat(k, t, white, red), x)

        # The facade: DARK concrete nearly all the way up, banded with
        # advertising over its lower half, and a white parapet under the roof.
        # From outside, this ground is a dark drum with a white crown; the
        # white and the red are what you see over that crown and inside.
        #
        # Three passes to get here and not one of them was about hue. A pale
        # wall under a pale rake reads as one smooth drum. Four ad bands on it
        # turned the drum into a hoarding. Splitting it into a low dark facade
        # and a tall light shell put the light half straight back on top, which
        # is the first silhouette again. What fixes it is PROPORTION: the dark
        # has to be most of the height, and everything else is trim.
        rim = lift + 1.0 + (STAND_H + 2.2 - 1.0) * f
        m.prism(arc_poly(outer, outer + 1.2, a0, a1), lift, rim - 3.0,
                facade, x)
        m.prism(arc_poly(outer - 0.05, outer + 1.2, a0, a1),
                rim - 3.0, rim, white, x)
        m.prism(arc_poly(outer - 0.06, outer + 1.25, a0, a1),
                rim - 3.0, rim - 2.6, mat("Stadium Shell"), x)
        for z0, z1, band in ((0.3, 2.4, dark),
                             (8.4, 9.6, mat("Stadium Red"))):
            m.prism(arc_poly(outer - 0.05, outer + 1.3, a0, a1),
                    lift + z0, lift + z1, band, x)

        # The roof: all the way round now, following the ring, thin, and
        # cantilevered 3.8 m and no more. An earlier one reached 7.6 m and
        # turned the stadium into a covered dish, because a camera at 30 deg
        # sees the rake and the rake is the only reason to model a stadium.
        z = rim
        # outer + 1.2 and not a centimetre more: on the long axis that radius
        # is multiplied by 1.30, and 58.8 m of a 59 m lot is already spent.
        m.prism(arc_poly(outer - 3.8, outer + 1.2, a0, a1),
                z, z + 0.34, mat("Roof Deck"), x)
        m.prism(arc_poly(outer + 0.8, outer + 1.2, a0, a1),
                z + 0.34, z + 0.80, mat("Roof Bright"), x)
        if k % 4 == 0:                        # the floodlight strip under it
            m.prism(arc_poly(outer - 3.4, outer - 2.4, a0, a1),
                    z - 0.34, z, mat("Lamp"), x)

    # Stair and ramp towers, dark against the pale drum, at the quarters.
    # The ramp towers. They are RIBS ON the facade and not boxes outside it,
    # for the same two reasons: a box at outer + 0.2 is inside the wall and
    # renders perfectly while being invisible, and the only radius left to put
    # one at would overhang the pavement on the long axis, which is the mistake
    # this stadium has already made once. Pale concrete against the dark drum,
    # cutting the advertising, which is how they read from above anyway.
    for k in range(6):
        a = math.radians(28 + 61 * k)
        m.prism(arc_poly(outer, outer + 1.35, a - 0.055, a + 0.055, segs=2),
                lift, lift + FACADE_H + 1.6, mat("Stadium Shell"), x)
        for s in range(4):
            m.prism(arc_poly(outer - 0.02, outer + 1.4,
                             a - 0.05, a + 0.05, segs=2),
                    lift + 1.6 + s * 2.5, lift + 1.9 + s * 2.5, dark, x)

    # The scoreboard over the far end, slung between the two red columns.
    # Small, but it is the one asymmetry above the roofline, so the silhouette
    # stops being a closed oval.
    # It stands at the DIPPED end, on tall legs, with its top above the ring -
    # which is where the real screen is, and it is the one thing on this
    # building that breaks the roofline. The +x end is also the near end for
    # this camera, so what the shot sees is the back of it, and the back is
    # where the ground writes its own name.
    #
    # Two earlier placements were both invisible and neither raised anything.
    # At outer - 1.0 the columns were between the tiers, inside the seating.
    # Sitting it down on the far stand put it below the rim from every angle
    # the city is ever seen from.
    sx = STAND_R0 + 1.4
    foot = lift + 1.3 + (STAND_H - 1.3) * (3.0 / TIERS) * stand_h(0.0)
    top = lift + 21.8                          # the tall side of the ring: 18.7
    for sy in (-6.0, 6.0):
        m.cyl((sx, sy, foot), 0.75, top - foot - 0.4,     # cyl builds from its
              mat("Stadium Red"), segs=10, xform=x)       # base, not its middle
    m.box((sx, 0, top - 3.0), (1.1, 13.4, 5.4), dark, x)
    m.box((sx + 0.62, 0, top - 3.0), (0.3, 12.2, 4.2), mat("Glass Light"), x)


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
    open_city(needs_collections=("KIT", "SITE"), needs_files=(LOTS,),
              hint="run 03_ground.py first")
    kit = {ob.name: ob for ob in bpy.data.collections["KIT"].objects}
    lots = {tuple(l["key"]): l for l in
            json.loads((LOTS).read_text())["lots"]}

    lm, lp = purge("LANDMARKS", "LANDMARK_PROPS")

    # The track is the loudest cue in the stadium, so it gets a real colour
    # rather than a tint of the road: brick dust, warm and a good deal more
    # saturated than anything else on that block, which is what makes it read
    # against the pitch from directly above.
    paint("Track Clay")
    paint("Pitch Grass")
    paint("Stadium Red")
    # White seats and red chevrons. The white is warm and a good deal lighter
    # than any concrete in the city, because it has to be legible as SEATS
    # against the facade right below it, and the two are three metres apart.
    paint("Seat White")
    paint("Seat Red")
    # The facade is DARK, and that is the whole point of it. At #8d8b86 it
    # rendered the same value as the seats under this sun and the stadium went
    # back to being one smooth white drum with a lawn in it - the rake reads
    # from outside only because there is something darker underneath it.
    paint("Stadium Facade")
    paint("Stadium Shell")
    paint("Stadium Apron")
    paint("Stadium Ad Dark")
    paint("Roof Bright")

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
    FOOT = {"stadium": ((_st_out + 1.4) * 1.30 * 2 + 1.0,
                        (_st_out + 1.4) * 2 + 1.0, math.radians(20), 20.5),
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
    sol.merge_into(SOLIDS, "landmarks")
    u, t = counts()
    print(f"\n  triangles: {u} unique / {t} total")

    exposure = bpy.context.scene.view_settings.exposure
    with preview(620.0, target=(0, 0, 0)):
        blib.render(str(R / "city_06_hero.png"), "EEVEE", samples=64,
                    resolution=(1600, 900), exposure=exposure)
    save_city()


main()
