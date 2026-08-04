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
from _common import (Mesh, collection, instance, mat, paint, rng, counts,
                     R, LOTS, SOLIDS, SIGNS, open_city, save_city, purge,
                     preview)
from _solids import Solids


# NO GRID CONSTANTS HERE. This file used to open with
#     BLOCK, STREET, PITCH, WALK = 64.0, 12.0, 76.0, 2.5
#     EXTENT, HALF = 9, 4.0
# and not one of the six was ever read. They were the uniform grid from before
# step 03 went to per-row block sizes, sitting at the top of the file that
# builds every building in the city, saying 64 m blocks and 12 m streets to
# anybody who opened it. The real numbers come out of city_lots.json: blocks
# from 52 to 76, streets of 12, 22 and the 70 m of the 9 de Julio.
FLOOR = 3.8
GROUND = 4.6                  # taller ground floor, like the reference

FAMILIES = [
    ("Concrete Warm", "Glass Light"),
    ("Concrete Warm", "Glass Dark"),
    ("Concrete Warm2", "Glass Light"),
    ("Concrete Warm2", "Glass Dark"),
    ("Concrete Cool2", "Glass Dark"),
    ("Concrete Cool", "Glass Dark"),
    ("Concrete Cool2", "Glass Light"),
    ("Brick Warm", "Glass Dark"),          # one in ten, not one in three
    ("Facade Teal", "Glass Light"),
    ("Concrete Dark", "Glass Dark"),
]

# cells that get something other than a plain low-rise campus
TALL = {(1, 2): 18, (7, 6): 12, (7, 2): 8, (1, 5): 9}
LANDMARKS = {(6, 1), (1, 6), (7, 4)}     # step 06 owns these plots
# and step 06b owns this one: the Floralis stands on it. "plaza" is not an
# empty lot - this step builds offices on plazas - so without this the
# monument went up inside somebody's fourth floor. The Obelisco is not here
# any more: it stands in the middle of the avenue, which is nobody's lot.
PORTENO = {(2, 7)}
# The blocks the title stands on. Step 08 builds the letters here as real
# buildings, so step 04 builds nothing: see build_campus().
#
# Two, not four. This set had (5, 4) and (5, 5) in it as well, but the title
# only occupies the two cells step 03 merges into the superblock - column 4 -
# so column 5 was being left empty for a word that never reaches it. That is
# the bare green block sitting immediately right of the title in every frame
# since the title was built, and nothing was wrong with it except that this
# set was a guess and the superblock is the fact.
CAMPUS = {(4, 4), (4, 5)}

# Invented companies. The reference is a parade of real logos and we are not
# reproducing the branding, so these are made up, and made up with an ear for
# where the city is: they are the names a Buenos Aires tech park would have.
# (text, mark, face colour, ink colour)
SIGN_FACES = [
    ("ZONDA", "chevron", "#e8532a", "#ffffff"),
    ("OMBU", "disc", "#1d7fc4", "#ffffff"),
    ("PAMPA", "bars", "#f2b705", "#22201c"),
    ("CEIBO", "triangle", "#c8102e", "#ffffff"),
    ("YERBA", "ring", "#2f8f4e", "#ffffff"),
    ("RIACHO", "square", "#2b2f77", "#ffffff"),
    ("VELOX", "chevron", "#d9d5cc", "#c8102e"),
    ("MATE", "disc", "#5c3d8f", "#ffffff"),
    ("SUR", "bars", "#0f9bd7", "#ffffff"),
    ("ANDA", "triangle", "#ef7d1a", "#22201c"),
    ("LUMA", "ring", "#e8e4da", "#1d7fc4"),
    ("TANGO", "square", "#22201c", "#f2b705"),
    ("KETZAL", "disc", "#0d8a86", "#ffffff"),
    ("NUBE", "bars", "#e8e4da", "#5c3d8f"),
]

# The avenue advertises to drivers, not to recruiters, so it carries a
# different register of invented brand: drink, bank, phone, football boots.
# Same shape of record, different list, so the office park does not suddenly
# start selling soda.
AV_FACES = [
    ("QUILME", "disc", "#1a7f3c", "#ffffff"),
    ("FERNET", "ring", "#3b1f13", "#f2b705"),
    ("BANCOSUR", "square", "#123a8f", "#ffffff"),
    ("TELCO", "chevron", "#e8262a", "#ffffff"),
    ("MEDIALUNA", "triangle", "#f2b705", "#3b1f13"),
    ("PATAGON", "bars", "#0f9bd7", "#ffffff"),
    ("GAUCHO", "square", "#c8102e", "#f7f3e8"),
    ("ALFAJOR", "disc", "#f7f3e8", "#7a3b12"),
    ("COLECTIVO", "chevron", "#ef7d1a", "#22201c"),
    ("SUBTE", "ring", "#2b2f77", "#f2b705"),
    ("ASADO", "triangle", "#8f2a1c", "#f7f3e8"),
    ("BOCA", "bars", "#0d3b8f", "#f2b705"),
]

# How often a building that looks at the avenue carries each format, and how
# large each is allowed to be. These are not taste: they come off the GCBA Ley
# 2936 de Publicidad Exterior, which is what decides how the real avenue looks.
#
# The mural is the common format and the rooftop board the rare one, which is
# the opposite of what this file did first. Art. 12.16.2 prohibits structures
# on roofs and terraces along the stretches that take in 9 de Julio, so the
# thing that gives the avenue its face is the painted medianera, not the
# hoarding. The first pass had it 14 boards to 12 murals and that is a picture
# of a different avenue.
#
# A strict reading of 12.16.2 puts the rooftop count at zero on this frontage.
# It is kept low rather than zero on instruction. No building carries both: a
# board and a mural on one address is the reading of this avenue the law most
# specifically rules out.
AV_MEDIANERA = 0.90
# 0.35, after the rate was tuned from 0.85 to 0.22 to 0.60 to 0.18 with the
# count stuck at one or two. The limit was never the rate: the board was being
# offered the narrow wing. With that fixed the rate means something again.
# The mural dominates because the law makes it the format of this avenue; the
# board is present because the same research says plainly that systematic
# non-compliance is what produces the real image of the place, and the
# photograph this was built from is full of them.
AV_BILLBOARD = 0.35
MAST_POLE = 0.55          # pole height as a fraction of the disc diameter, and
                          # it has to match MAST in 10_signs.py: this step
                          # decides where the disc is and that one builds it
AV_REACH = 15.0           # how close a wall has to be to count as on the avenue
BOARD_LIFT = 4.2          # legs: how far the panel floats over the roof deck.
                          # Art. 5.5 allows 10 m of structure over the roof, so
                          # this is well inside it and is a look decision.
# Art. 5.5, rooftop sign area, by the height of the building it stands on.
BOARD_AREA = ((15.0, 100.0), (10.0, 80.0), (0.0, 60.0))
MED_COVER = 0.50          # art. 5.4.b: a mural may cover half the visible party
                          # wall. No cap in square metres - it scales with the
                          # wall, which is why these can be enormous. It is a
                          # ceiling and not a target, but a 0.92 x 0.55 panel
                          # lands within a percent of it on any wall.
# Art. 5.8 fixes the panel module at 1.09 x 1.48 m and multiples of it. The
# mural is snapped down to whole modules, which only ever shrinks it, so it
# cannot break a fit that was already checked.
MODULE_W, MODULE_H = 1.09, 1.48
# How low a mural can start, and it is not one number. The entrance canopy
# reaches 2.8 m off the wall at z 3.1-3.5 and a panel standing 1.05 m proud is
# inside it - but wing() only ever builds canopies on the +/-y walls, so that
# cost is only owed on the east bank, where the mural is on +y. On the west
# bank the mural is on +x, where there is nothing but a 0.45 m shade frame, and
# it can run down almost to the pavement the way a real medianera does. Holding
# both banks at 6.1 threw away four metres of every west wall and, with the
# area cap in, refused every two-floor building on that side outright.
#
# 3.8 on the east bank, not 6.1. The canopy's top face is at GROUND - 1.1, so
# 3.5 - the 6.1 was a floor's worth of guesswork on top of a number that could
# be read off wing(). It costs a low building its whole mural shape: on a 16 m
# wall, 6.1 of base and 1.2 of parapet gap leave 8.7 m of an area allowance
# that would happily have paid for more, and every east-bank mural on a short
# building came out as a long thin band across the middle of the facade
# instead of as a mural.
MED_BASE = {"x": 2.2, "y": 3.8}
AV_MED_CROSS = 0.45       # a west-bank building's +y wall is a party wall too,
                          # and art. 5.4.b is written per wall, not per address.
                          # A corner on the real avenue is painted on both.
MED_PROUD = 1.05          # the same projection the parapet letters use, and
                          # for the same reason: a real mural is painted flat
                          # on the wall, but this city's facades carry a shade
                          # frame standing 0.45 m proud and are published 0.45
                          # out, so a panel at the honest 0.2 m is inside the
                          # building. See PROUD in 10_signs.py.


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
        # 0.72, not 0.55. A bar is meant to be a slab that leaves a forecourt,
        # not a building that gives back nearly half its lot: at 0.55 the two
        # bars on a split block left a strip of lawn down the middle wider than
        # the street beside it.
        return [(0, 0, w, d * 0.72)]
    # twins: two wings with a slot between them. One slab per block held the
    # title up fine and turned the middle of the frame into four blank boxes;
    # a 4 m slot costs almost no roof and gives the campus back its facades.
    if kind == "twinx":
        return [(-w / 4 - 1, 0, w / 2 - 2, d), (w / 4 + 1, 0, w / 2 - 2, d)]
    if kind == "twiny":
        return [(0, -d / 4 - 1, w, d / 2 - 2), (0, d / 4 + 1, w, d / 2 - 2)]
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


def wing(m, ox, oy, w, d, floors, style, fam, xform, r, deep=False,
         deck=None, sol=None, wx=0.0, wy=0.0):
    conc, glass = mat(fam[0]), mat(fam[1])
    # ground floor: recessed glass with an entrance canopy poking out. The
    # comparison against the reference showed my facades had 0.2-0.5 m of
    # relief where it has 0.5-3 m, and no ground-floor threshold at all.
    m.slab(ox, oy, w - 1.6, d - 1.6, 0.0, GROUND, glass, xform)
    mullions(m, ox, oy, w - 1.6, d - 1.6, 0.3, GROUND - 0.6, conc, xform, 4.0)
    for sy in (-1, 1):
        if r.random() < 0.55:
            cx0 = ox + r.uniform(-w * 0.2, w * 0.2)
            cw = min(w * 0.42, 11.0)
            m.slab(cx0, oy + sy * (d / 2 + 1.1), cw, 3.4,
                   GROUND - 1.5, GROUND - 1.1, mat("Concrete Cool"), xform)
            # the canopy reaches 2.8 m past the wall, over the pavement, and
            # the street tree row runs at 1.25 m: this was the single largest
            # source of trees growing through solid geometry. It is published
            # as its own small box rather than by inflating the whole wing,
            # so the trees that get refused are the ones in front of a door.
            if sol is not None:
                sol.add(wx + cx0, wy + oy + sy * (d / 2 + 1.1), cw, 3.4,
                        0.0, 0.0, GROUND - 1.1)
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
            m.slab(ox, oy, w - 1.5, d - 1.5, z + 1.15, z + FLOOR, glass, xform)
            mullions(m, ox, oy, w - 1.5, d - 1.5, z + 1.15, FLOOR - 1.15,
                     conc, xform, 3.0)
            if deep and f % 2 == 0:             # projecting shade frame
                facade_ring(m, ox, oy, w + 0.9, d + 0.9, z + FLOOR - 0.55,
                            0.5, 0.45, mat("Concrete Cool"), xform)
        z += FLOOR

    # parapet ring and roof plate. The deck is always a light concrete: in the
    # reference roofs read pale whatever colour the facade is.
    pick = deck or ("Roof Dark" if r.random() < 0.45 else "Roof Deck")
    m.quad(ox, oy, w, d, z + 0.02, mat(pick), xform)
    facade_ring(m, ox, oy, w, d, z, 0.85, 0.55, mat("Concrete Cool"), xform)
    return z + 0.85


_plan_radius = {}


def plan_radius(ob):
    """How far the asset reaches in plan, from its own mesh. Rotation about Z
    is random, so it is the largest hypot, not the largest x or y."""
    if ob.data.name not in _plan_radius:
        _plan_radius[ob.data.name] = max(
            (math.hypot(v.co.x, v.co.y) for v in ob.data.vertices), default=0.0)
    return _plan_radius[ob.data.name]


def straddles(lx, ly, rad, ox, oy, siblings):
    """Does this roof unit sit across a neighbouring wing's parapet?

    An L or a U is several overlapping rectangles and each one gets its own
    parapet ring, including along the seams that end up inside the building.
    A unit placed safely inside wing A can therefore be sitting on wing B's
    parapet, which is a 0.55 m ledge standing 0.85 m proud of the roof it
    shares. Nine units were doing exactly that.
    """
    for (sx, sy, sw, sd) in siblings:
        if (sx, sy) == (ox, oy):
            continue                       # this is the wing it is standing on
        dx, dy = abs(lx + ox - sx), abs(ly + oy - sy)
        outside = dx > sw / 2 + rad + 0.6 or dy > sd / 2 + rad + 0.6
        within = dx < sw / 2 - rad - 0.6 and dy < sd / 2 - rad - 0.6
        if not (outside or within):
            return True
    return False


def roof_props(kit, coll, cx, cy, w, d, top, rot, r, big, siblings=(),
               ox=0.0, oy=0.0, keep=None):
    """Never leave a roof empty: it is most of what this camera sees."""
    placed = []
    # the coral pipe frame was on nearly every roof and read as a repeated
    # diagram; it is now one option among many
    pool = ["RoofHVAC", "RoofHVAC", "RoofHVACSmall", "RoofHVACSmall",
            "RoofBulkhead", "RoofBulkhead", "RoofTank", "RoofTank",
            "RoofDish", "RoofSolar", "RoofPipesSmall", "RoofPipes"]
    area = w * d
    n = max(3, min(14, int(area / 170)))
    # Reversed after the second review: the reference's roofs are mostly quiet
    # with one memorable thing on them, not a mechanical carpet on every block.
    n = max(3, min(12, int(area / 130)))
    mood = r.random()
    if mood < 0.55:                # most roofs stay quiet
        n = max(1, n // 4)
    elif mood > 0.88:              # a few get one large single feature
        n = 1
        pool = ["RoofSolarBig", "RoofBulkhead", "RoofTank"]
    for _ in range(n):
        name = r.choice(pool)
        if min(w, d) < 24 and name in ("RoofPipes", "RoofSolarBig"):
            name = "RoofPipesSmall"
        lx = r.uniform(-w / 2 + 6, w / 2 - 6)
        ly = r.uniform(-d / 2 + 5, d / 2 - 5)
        a = rot + r.choice([0, math.pi / 2])
        sc = r.uniform(1.3, 2.1)
        # a fixed 6 m inset assumed every unit was the same size. A solar array
        # scaled 2.1 reaches 10 m from its origin, so it hung a third of itself
        # over the parapet, which reads from this camera as a shelf of nothing.
        # The clamp happens after every draw, so the rest of the city is not
        # reshuffled by fixing it.
        rad = plan_radius(kit[name]) * sc
        mx, my = w / 2 - rad - 1.2, d / 2 - rad - 1.2
        if mx < 0 or my < 0:
            continue                          # too big for this roof, at all
        lx = max(-mx, min(mx, lx))
        ly = max(-my, min(my, ly))
        if straddles(lx, ly, rad, ox, oy, siblings):
            continue
        if keep is not None:
            kx, ky, kw, kd = keep
            if (abs(lx + ox - kx) < kw / 2 + rad and
                    abs(ly + oy - ky) < kd / 2 + rad):
                continue                       # the company sign goes there
        wx = cx + lx * math.cos(rot) - ly * math.sin(rot)
        wy = cy + lx * math.sin(rot) + ly * math.cos(rot)
        placed.append(instance(kit[name], coll, (wx, wy, top), a, sc))
    if r.random() < 0.25:
        lx, ly = r.uniform(-w / 4, w / 4), r.uniform(-d / 4, d / 4)
        wx = cx + lx * math.cos(rot) - ly * math.sin(rot)
        wy = cy + lx * math.sin(rot) + ly * math.cos(rot)
        placed.append(instance(kit["PingPong"], coll, (wx, wy, top), rot))
    return placed


def sign_fits(sol, bx, by, length, top, h):
    """The longest word that clears whatever else is standing there.

    A lot carries up to four separate buildings and the word is mounted on one
    wall of one of them, so a long word runs off the end of its own wing and
    into the next building along.

    The query has to sit where the letters actually are and no closer: they
    span 0.6 to 1.5 m outside the wall, and this building's own published box
    already reaches 0.45 m out. Sampling at 1.05 with 0.4 of clearance leaves
    0.65 and finds only somebody else's building. The first version sampled at
    1.0 with 0.6, which reaches back to 0.4, inside the sign's own building -
    so it refused all twenty of them and the count going to zero is the only
    reason anyone noticed.
    """
    for trial in (length, length * 0.8, length * 0.6):
        clear = True
        for k in range(9):
            t = -trial / 2 + trial * k / 8
            if sol.hit(bx + t, by + 1.05, top - h / 2, 0.4) is not None:
                clear = False
                break
        if clear:
            return trial
    return None


def mast_fits(sol, cx, cy, rot, disc, z):
    """The largest disc that clears its neighbours, or None.

    The disc stands on edge on a pole, so in plan it is a line of length `disc`
    lying along the rotation - and at 135 degrees that is 0.707 * disc/2 in
    both x and y at once. The pole is at `z`, the disc sits above it, so the
    height to test at is the middle of the disc and not the roof.
    """
    ux, uy = math.cos(rot), math.sin(rot)
    for trial in (disc, disc * 0.8, disc * 0.6):
        mid = z + MAST_POLE * trial + trial / 2
        clear = True
        for k in range(7):
            t = -trial / 2 + trial * k / 6
            if sol.hit(cx + ux * t, cy + uy * t, mid, 0.3) is not None:
                clear = False
                break
        if clear:
            return trial
    return None


def plan_sign(bx, by, w, d, top, floors, r, signs, sol=None):
    """Reserve a place for a company sign, and record where it is.

    Step 04 decides, step 10 builds. It has to be this way round: this step
    knows the roof it goes on and owns the RNG, while the sign itself has to
    be a separate object with its own material slot so a logo can be dropped
    onto it later, and everything this step builds ends up merged into one
    mesh with no per-building object left to address.

    The reservation matters as much as the record. When the signs were built
    here as loose volumes that nobody published, nine roof units ended up
    standing inside one, which is how they were found: not by looking, but by
    the overlap check reporting a building nobody could name.
    """
    kind = None
    if floors >= 3 and w >= 26 and r.random() < 0.42:
        kind = "parapet"
    elif w * d > 520 and r.random() < 0.5:
        kind = "roofmark"
    elif r.random() < 0.14:
        kind = "mast"
    if kind is None:
        return None
    idx = len(signs)
    face = r.choice(SIGN_FACES)
    if kind == "parapet":
        # On the +y wall, turned to face it, because that is a wall this
        # camera can see. The hero camera sits at azimuth 45, so it looks at
        # the +x and +y faces of everything; the first version put the letters
        # on -y, where they were geometrically perfect and permanently behind
        # the building. Turned through pi the word also runs along world -x,
        # which is screen-right from here, so it reads forwards.
        # 0.55 and 22, not 0.62 and 26: an L or a U is several wings and the
        # word was running off the end of the one it is mounted on and into
        # the next one along
        length = min(w * 0.55, 22.0)
        if sol is not None:
            length = sign_fits(sol, bx, by + d / 2, length, top, 4.6)
            if length is None:
                return None
        rec = dict(kind=kind, x=bx, y=by + d / 2, z=top, rot=math.pi,
                   w=length, h=min(4.6, length * 0.26))
        keep = (0.0, d / 2 - 2.0, length + 2.0, 5.0)
    elif kind == "roofmark":
        # a flat panel lying on the deck, like the orange square in the
        # reference: the only type that costs no height at all
        # same reason: a panel that drifts far enough off centre ends up
        # sitting across a neighbouring wing's parapet
        side = min(w, d) * 0.36
        rec = dict(kind=kind, x=bx + r.uniform(-w * 0.07, w * 0.07),
                   y=by + r.uniform(-d * 0.07, d * 0.07), z=top - 0.83,
                   rot=r.choice([0.0, math.pi / 2]), w=side, h=side)
        keep = (rec["x"] - bx, rec["y"] - by, side + 2.0, side + 2.0)
    else:
        disc = min(min(w, d) * 0.55, 16.0)
        rec = dict(kind=kind, x=bx + r.uniform(-w * 0.2, w * 0.2),
                   y=by + r.uniform(-d * 0.2, d * 0.2), z=top,
                   # +135, not -45. The disc is a cylinder stood on edge, so
                   # its face points along local -Y, and the camera is out at
                   # azimuth 45: at -45 the face pointed exactly away and every
                   # mast in the city showed its blank back.
                   rot=math.radians(135), w=disc, h=disc)
        keep = (rec["x"] - bx, rec["y"] - by, disc + 2.0, disc + 2.0)
    rec.update(name=f"Sign.{idx:03d}", text=face[0], mark=face[1],
               face=face[2], ink=face[3])
    signs.append(rec)
    return keep


def avenue_bank(av, bx, by, w, d):
    """Which bank of 9 de Julio this building stands on, or None.

    "west" means the building sits west of the avenue, so the wall that looks
    at it is its +x wall - a wall this camera can see. "east" means the wall
    that looks at the avenue is a -x wall, which from azimuth 45 is the back
    of the building and is permanently invisible however well it is built. So
    the two banks do not get the same treatment: on the east bank the mural
    goes on the +y wall, facing the cross street, which is where a real
    medianera on that side would be exposed anyway.
    """
    if av is None:
        return None
    half = av["width"] / 2
    if 0 <= (av["x"] - half) - (bx + w / 2) <= AV_REACH:
        return "west"
    if 0 <= (bx - w / 2) - (av["x"] + half) <= AV_REACH:
        return "east"
    return None


def panel_fits(sol, wx, wy, rot, length, z):
    """The longest wall panel that clears whatever else stands along this wall.

    Same shape of question as sign_fits, and the same trap: sample where the
    panel actually is and no closer. The panel spans MED_PROUD to about
    MED_PROUD + 0.3 off the wall and this building's own published box already
    reaches 0.45 out, so sampling at 1.35 with 0.4 of clearance reaches back to
    0.95 and finds only somebody else's building.
    """
    ux, uy = math.cos(rot), math.sin(rot)            # along the wall
    nx, ny = math.sin(rot), -math.cos(rot)           # outward, local -Y
    for trial in (length, length * 0.8, length * 0.6):
        clear = True
        for k in range(9):
            t = -trial / 2 + trial * k / 8
            if sol.hit(wx + ux * t + nx * (MED_PROUD + 0.3),
                       wy + uy * t + ny * (MED_PROUD + 0.3),
                       z, 0.4) is not None:
                clear = False
                break
        if clear:
            return trial
    return None


def plan_medianera(side, bx, by, w, d, top, r, signs, sol):
    """A mural on a blind party wall. The format the avenue is famous for.

    No letters and no relief: one panel with a face colour and a mark, because
    the artwork is a texture that goes on later and anything modelled here
    would have to be unmodelled then.

    `side` is which wall, "x" or "y", and not which bank. They came in as the
    same argument at first and they are not the same question: a west-bank
    building looks at the avenue over its +x wall and at the cross street over
    its +y wall, and both of those are party walls that can be painted.
    """
    if side == "x":
        wx, wy, rot, run = bx + w / 2, by, math.pi / 2, d
    else:
        wx, wy, rot, run = bx, by + d / 2, math.pi, w
    wall = top - 0.85                        # under the parapet, not over it
    base0 = MED_BASE[side]
    if wall - base0 < 9.0:
        return None                          # too short to read as a mural
    # no arbitrary cap on the width any more. Art. 5.4.b has no limit in square
    # metres: a mural may take half of whatever wall it is on, so it scales
    # with the building and a 30 m wall is entitled to 300 m of it. The 34 m
    # ceiling this had was invented and was holding the big walls back.
    length = panel_fits(sol, wx, wy, rot, run * 0.92,
                        (base0 + wall) / 2)
    if length is None:
        return None
    length = modules(length, MODULE_W)
    if length < 10 * MODULE_W:
        return None
    height = modules(min(wall - base0 - 1.2,
                         MED_COVER * run * wall / length), MODULE_H)
    if height < 5 * MODULE_H:
        return None                          # 7.4 m: under this it is a poster
    # and a mural is not a banner. The area allowance alone let a short wall
    # spend all of it on width - 57 m by 7.4 is legal, is 42 % of the wall, and
    # reads as a strip of tape across the middle of the building. Trimming the
    # width to four times the height only ever gives area back, so the cap and
    # the fit both still hold.
    length = modules(min(length, height * 4.0), MODULE_W)
    if length < 10 * MODULE_W:
        return None
    # hung from the top of the wall, not stood on MED_BASE. Once the area is
    # capped the panel no longer reaches both ends of the wall, and the half it
    # should keep is the top one: that is the half that clears the roofs of
    # whatever is in front of it, which is the entire reason a medianera is
    # worth renting.
    base = max(base0, wall - 1.2 - height)
    face = r.choice(AV_FACES)
    rec = dict(kind="medianera", x=wx, y=wy, z=base, rot=rot,
               w=length, h=height, run=run, wall=wall,
               name=f"Sign.{len(signs):03d}", text=face[0], mark=face[1],
               face=face[2], ink=face[3])
    signs.append(rec)
    return rec


def plan_billboard(bx, by, w, d, top, rot, r, signs, siblings, ox, oy):
    """A panel on legs on the roof, turned to face the camera.

    Returned in wing-local coordinates as a keep-out for the roof units, the
    same contract plan_sign has: the sign is chosen first and the mechanical
    plant is told to go somewhere else.
    """
    # The panel is a line of length `board` lying at 45 degrees in plan, so it
    # reaches 0.354 * board in both x and y whichever way the roof runs. Size
    # it off what the roof can hold rather than off the roof's own proportion:
    # taking 0.70 of the smaller dimension refused half the avenue, because the
    # wing that faces it is often a 12 m arm of a U and a hoarding is 2 m deep.
    room = min(w, d) / 2 - 3.0               # 1.6 of frame, 1.4 off the parapet
    board = min(20.0, room / 0.354, max(w, d) * 0.9)
    if board < 12.0:
        return None
    # art. 5.5: 100 square metres over 15 m of building, 80 over 10, 60 below.
    # Scaled down about its own proportion rather than trimmed on one side, so
    # a legal board is still the shape of a board: 20 x 8 is 160 and was over
    # the largest allowance by sixty per cent.
    cap = next(a for h, a in BOARD_AREA if top >= h)
    high = min(8.0, max(5.0, board * 0.40))
    if board * high > cap:
        k = math.sqrt(cap / (board * high))
        board, high = board * k, high * k
        if high < 5.0:                       # the shape gives out before the
            high, board = 5.0, cap / 5.0     # area does on a low building
        if board < 12.0:
            return None
    rad = board * 0.354 + 1.6
    mx, my = w / 2 - rad - 1.4, d / 2 - rad - 1.4
    lx = max(-mx, min(mx, r.uniform(-w * 0.12, w * 0.12)))
    ly = max(-my, min(my, r.uniform(-d * 0.12, d * 0.12)))
    if straddles(lx, ly, rad, ox, oy, siblings):
        return None                          # standing on a neighbour's parapet
    face = r.choice(AV_FACES)
    rec = dict(kind="billboard", x=bx + lx, y=by + ly, z=top - 0.83, rot=rot,
               w=board, h=high, lift=BOARD_LIFT,
               name=f"Sign.{len(signs):03d}", text=face[0], mark=face[1],
               face=face[2], ink=face[3])
    signs.append(rec)
    return (lx, ly, 2 * rad + 1.0, 2 * rad + 1.0)


def modules(x, unit):
    """Down to a whole number of art. 5.8 panel modules.

    1.09 x 1.48 m is the sheet an Argentine mural is actually assembled from,
    so a mural that is a whole number of them has proportions off the street
    rather than off a random number generator. It only ever rounds down, which
    is why it is safe to apply after the fit has been checked.
    """
    return math.floor(x / unit) * unit


def avenue_rng(bx, by):
    """A random stream of this building's own, not the city's.

    Every avenue draw used to come out of the shared `r`, so adding one coin
    flip here reshuffled all eighty lots downstream of it: the mural count came
    out 7, then 11, then 9, then 8 across four runs whose only difference was a
    rate that murals do not read. Twice that made a change look like it had
    done the opposite of what it does, and the rate was tuned against the
    noise. Seeded off the position, so it still varies building to building and
    is still deterministic, but the avenue now costs the rest of the city no
    draws at all and the counts move only when the rates do.
    """
    return rng(int(round(abs(bx) * 977 + abs(by) * 131)))


def plan_avenue(bank, bx, by, w, d, top, floors, r, signs, sol, siblings,
                ox, oy, board=None):
    """The mural first, and the rooftop board only if there is no mural.

    Art. 12.16.2 prohibits rooftop structures on this stretch, so the board is
    the exception here and not the rule.

    `board` is the wing the rooftop panel goes on, which is NOT the wing the
    mural goes on. The mural needs the wall that looks at the avenue; the board
    needs a roof wide enough to stand on, and once it is up there it is visible
    from the length of the avenue whichever wing it stands on. Given the same
    wing as the mural it was being offered the 12 m arm of an L over and over
    - a hoarding turned 45 degrees in plan reaches 0.354 of its length in both
    axes at once, so it needs about 15 m of roof in the short direction and was
    refused on nearly every candidate. The rate was then tuned from 0.85 down
    to 0.18 and back with the count stuck at one or two, which is the tell: a
    rate that moves by a factor of five and changes nothing is not the limit.

    Returns (planned, keep). The two are not the same question and reading one
    off the other is a real bug: a mural reserves no roof, so returning its
    empty keep-out let the caller decide nothing had been planned and hang a
    parapet word on the same wall the mural is painted on.
    """
    # The rare format is drawn first, and the common one takes what is left.
    # That is the wrong way round for reading the rates off the page and the
    # right way round for the result: drawn second, the board only ever landed
    # on the four buildings no mural would fit, which put every board on the
    # avenue within one block of the next.
    ar = avenue_rng(bx, by)
    if ar.random() < AV_BILLBOARD:
        # 135 degrees, not 45. The panel is built facing its own local -Y,
        # which Rz(135) turns into (+0.71, +0.71) - straight at a camera
        # sitting at azimuth 45. This is the same number the mast disc needed
        # and for the same reason.
        gx, gy, gw, gd = board if board is not None else (ox, oy, w, d)
        keep = plan_billboard(bx - ox + gx, by - oy + gy, gw, gd, top,
                              math.radians(135), ar, signs, siblings, gx, gy)
        if keep is not None:
            # the keep-out comes back in the board wing's local frame and the
            # caller works in the mural wing's, so it is rebased here rather
            # than at the call site, where the two frames are easy to confuse
            return True, (keep[0] + gx - ox, keep[1] + gy - oy,
                          keep[2], keep[3])
    # no floor count here. It was standing in for "is this wall tall enough",
    # and now that the mural is measured against the wall it is on, the wall
    # answers that itself - and answers it differently on the two banks, which
    # a floor count cannot.
    side = "x" if bank == "west" else "y"
    got = False
    if ar.random() < AV_MEDIANERA:
        got = plan_medianera(side, bx, by, w, d, top, ar, signs,
                             sol) is not None
    # and the cross-street wall of a west-bank building, which is a second
    # party wall and not a second sign on the same one. Only west: on the east
    # bank "y" is already the wall the mural went on, and "x" there is the -x
    # face this camera never sees.
    if bank == "west" and ar.random() < AV_MED_CROSS:
        if plan_medianera("y", bx, by, w, d, top, ar, signs, sol) is not None:
            got = True
    return got, None


def place_on_lot(m, kit, coll, sol, signs, cx, cy, size, lift, kind, r,
                 av=None):
    sw, sd = size
    """One to four buildings on a block, with setbacks."""
    if kind in ("park", "construction", "parking"):
        return
    tops = []
    plan = r.choice([1, 2, 2, 2, 4])
    cells = {1: [(0, 0, 1.0, 1.0)],
             2: [(-0.25, 0, 0.5, 1.0), (0.25, 0, 0.5, 1.0)],
             4: [(-0.25, -0.25, 0.5, 0.5), (0.25, -0.25, 0.5, 0.5),
                 (-0.25, 0.25, 0.5, 0.5), (0.25, 0.25, 0.5, 0.5)]}[plan]
    if plan == 2 and r.random() < 0.5:
        cells = [(0, -0.25, 1.0, 0.5), (0, 0.25, 1.0, 0.5)]
    for (fx, fy, fw, fh) in cells:
        # 0.04, not 0.10. On a block split in two this draw is the difference
        # between a built block and a half-built one, and one in ten was
        # frequent enough that the city read as unfinished rather than as
        # having the odd courtyard in it.
        if r.random() < 0.04:
            continue                       # a gap: courtyard, planting or car park
        # setbacks were 6-12 m, which left every building floating in a lawn.
        # The reference puts the wall almost on the pavement.
        w = sw * fw - r.uniform(1.0, 2.6)
        d = sd * fh - r.uniform(1.0, 2.6)
        if min(w, d) < 11:
            continue
        bx, by = cx + sw * fx, cy + sd * fy
        floors = r.choice([2, 2, 3, 3, 4, 4, 5, 6, 7])
        style = r.choice(["banded", "banded", "banded", "louvre", "punched"])
        fam = FAMILIES[r.randrange(len(FAMILIES))]
        kindf = r.choice(["rect", "rect", "L", "U", "T", "bar"])
        x = xf(bx, by, 0.0)
        top = 0.0
        for (ox, oy, ww, dd) in footprint(kindf, w, d):
            t = wing(m, ox, oy, ww, dd, floors, style, fam, x, r,
                     deep=(floors >= 4), sol=sol, wx=bx, wy=by)
            top = max(top, t)
        for (ox, oy, ww, dd) in footprint(kindf, w, d):
            # +0.9: the projecting shade frame on a deep facade stands 0.45 m
            # off the wall on every side
            sol.add(bx + ox, by + oy, ww + 0.9, dd + 0.9, 0.0, 0.0, top)
        roof = top - 0.83
        wings = footprint(kindf, w, d)
        # the sign is chosen before the roof units, so the units can be told
        # to keep out of its way. The other order is what put nine of them
        # inside one.
        #
        # and it goes on the largest wing, not on the lot. An L is two wings
        # inside a cell and the cell's own +y edge is thin air over one of
        # them: the first version hung a word off the end of a building.
        hx, hy, hw, hd = max(wings, key=lambda s: s[2] * s[3])
        # On the avenue the sign goes on the wing that looks at it, not on the
        # biggest one. An L is two wings and the big one is as often the back
        # one, and a mural on the back wing is painted onto the courtyard.
        if av is not None:
            near = min(wings, key=lambda s: abs(bx + s[0] - av["x"]))
            if avenue_bank(av, bx + near[0], by + near[1], near[2],
                           near[3]) is not None:
                hx, hy, hw, hd = near
        # a building that looks at 9 de Julio advertises to the avenue instead
        # of to the office park. If the billboard draw misses it still gets an
        # ordinary sign, so the corridor does not end up with bald roofs.
        bank = avenue_bank(av, bx + hx, by + hy, hw, hd)
        planned, keep = False, None
        if bank is not None:
            # the board goes on the widest roof the building has, the mural on
            # the wall that looks at the avenue. On a rectangle these are the
            # same wing and nothing changes; on an L or a U they are not.
            planned, keep = plan_avenue(bank, bx + hx, by + hy, hw, hd, top,
                                        floors, r, signs, sol, wings, hx, hy,
                                        board=max(wings,
                                                  key=lambda s: s[2] * s[3]))
        if not planned:
            keep = plan_sign(bx + hx, by + hy, hw, hd, top, floors, r, signs,
                             sol)
        if keep is not None:
            keep = (keep[0] + hx, keep[1] + hy, keep[2], keep[3])
        # A U has two arms on the avenue and a T has an arm and a flank, so
        # they have two party walls looking at it and were being given one.
        # Capped at one extra: three murals on one address is a lot advertising
        # to itself, and the fit check refuses the buried ones anyway.
        if bank is not None:
            for (ox2, oy2, ww2, dd2) in wings:
                if (ox2, oy2) == (hx, hy):
                    continue
                b2 = avenue_bank(av, bx + ox2, by + oy2, ww2, dd2)
                ar2 = avenue_rng(bx + ox2, by + oy2)
                if b2 is None or ar2.random() >= AV_MEDIANERA:
                    continue
                if plan_medianera("x" if b2 == "west" else "y",
                                  bx + ox2, by + oy2, ww2, dd2, top, ar2,
                                  signs, sol) is not None:
                    break
        for (ox, oy, ww, dd) in wings:
            roof_props(kit, coll, bx + ox, by + oy, ww, dd, roof, 0.0, r,
                       ww * dd > 700, siblings=wings, ox=ox, oy=oy, keep=keep)
        tops.append(top)
    return tops


def build_campus(m, kit, coll, ccoll, lots, r):
    """These four blocks are left empty on purpose.

    They are the blocks the title stands on, and since step 08 builds the
    letters as real buildings there is nothing for step 04 to put here: an
    ordinary office on this lot either hides a letter or stands inside one.
    The ground stays as step 03 laid it and step 05 plants it, which is what
    the reference shows around its own title buildings.

    An earlier version filled these lots with a seven-floor campus, back when
    the title was flat plates that needed a roof to lie on. That is gone.
    """
    print(f"  campus: {len(CAMPUS)} blocks left clear for the title")


def build_towers(m, kit, coll, sol, signs, lots, r):
    """Only on lots that survived. A tower on a dropped cell stands alone in
    the middle of the road, which is exactly what happened the first time."""
    for (i, j), floors in TALL.items():
        key = [str(i), str(j)]
        lot = next((l for l in lots if l["key"] == key), None)
        if lot is None:
            print(f"  tower at {i},{j} skipped: no lot there")
            continue
        cx, cy = lot["x"], lot["y"]
        w = r.uniform(30, 42)
        d = r.uniform(26, 38)
        fam = FAMILIES[2] if floors > 12 else FAMILIES[0]
        style = "curtain" if floors > 12 else "banded"
        x = xf(cx, cy, 0.0)
        top = wing(m, 0, 0, w, d, floors, style, fam, x, r,
                   sol=sol, wx=cx, wy=cy)
        sol.add(cx, cy, w + 0.9, d + 0.9, 0.0, 0.0, top)
        # a tower always gets a sign: in the reference the tall buildings are
        # exactly the ones that carry a name
        keep = plan_sign(cx, cy, w, d, top, floors, r, signs, sol)
        roof_props(kit, coll, cx, cy, w, d, top - 0.83, 0.0, r, True,
                   keep=keep)


def main():
    open_city(needs_collections=("KIT", "SITE"), needs_files=(LOTS,),
              hint="run 03_ground.py first: the block table is its output")
    kit = {ob.name: ob for ob in bpy.data.collections["KIT"].objects}
    paint("Brick Warm")
    paint("Facade Teal")
    paint("Concrete Dark")
    paint("Roof Deck")
    paint("Roof Dark")

    # its own collection for CAMPUSROOF so step 05 can leave those roofs
    # alone: the title hangs half a metre over them and a person up there
    # stands through a letter
    bcoll, pcoll, ccoll = purge("BUILDINGS", "ROOFPROPS", "CAMPUSROOF")

    r = rng(90210)
    m = Mesh()
    sol = Solids()
    signs = []

    site = json.loads((LOTS).read_text())
    lots = site["lots"]
    av = site.get("avenue9j")
    for lot in lots:
        i, j = int(lot["key"][0]), int(lot["key"][1])
        if (i, j) in TALL or (i, j) in LANDMARKS or (i, j) in CAMPUS \
                or (i, j) in PORTENO:
            continue
        place_on_lot(m, kit, pcoll, sol, signs, lot["x"], lot["y"],
                     lot["size"], lot["lift"], lot["kind"], r, av)

    build_campus(m, kit, pcoll, ccoll, lots, r)
    build_towers(m, kit, pcoll, sol, signs, lots, r)
    m.build("buildings", bcoll)

    # Second pass over the words. A sign is planned in the same loop that
    # publishes the buildings, so when it is planned the buildings that come
    # after it do not exist yet and it cannot see the one it is about to run
    # into. Re-checking here, with everything published, is the whole fix.
    dropped = 0
    for rec in list(signs):
        if rec["kind"] == "parapet":
            fit = sign_fits(sol, rec["x"], rec["y"], rec["w"], rec["z"],
                            rec["h"])
        elif rec["kind"] == "medianera":
            # a mural is 34 m of wall, so it has more of the neighbour's
            # building to run into than a word does, not less
            fit = panel_fits(sol, rec["x"], rec["y"], rec["rot"], rec["w"],
                             rec["z"] + rec["h"] / 2)
            if fit is not None:
                fit = modules(fit, MODULE_W)   # still whole panels afterwards
                if fit < 10 * MODULE_W:
                    fit = None
        elif rec["kind"] == "mast":
            # The mast had no fit check at all, on either pass, and it is the
            # one format that reaches furthest: a 16 m disc stood on edge at
            # 45 degrees in plan swings 5.7 m out in x and y at once, well past
            # the parapet it is standing behind. One of them was inside the
            # building next door and the only reason it was found is that the
            # overlap check tests every loose object, not the ones somebody
            # remembered to validate.
            fit = mast_fits(sol, rec["x"], rec["y"], rec["rot"], rec["w"],
                            rec["z"])
        else:
            continue
        if fit is None:
            signs.remove(rec)
            dropped += 1
        else:
            rec["w"] = fit
    if dropped:
        print(f"  {dropped} signs dropped: no room once every building was in")

    sol.merge_into(SOLIDS, "buildings")
    (SIGNS).write_text(json.dumps(signs, indent=1))
    kinds = {}
    for s in signs:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    print(f"  footprints published: {len(sol.boxes)}")
    print(f"  signs planned: {len(signs)}   " +
          "  ".join(f"{k} {v}" for k, v in sorted(kinds.items())))

    u, t = counts()
    print(f"\n  roof props: {len(pcoll.objects)}")
    print(f"  triangles: {u} unique / {t} total")

    exposure = bpy.context.scene.view_settings.exposure
    for tag, width in (("hero", 620.0), ("closeup", 200.0)):
        with preview(width, target=(0, 0, 0)):
            blib.render(str(R / f"city_04_{tag}.png"), "EEVEE", samples=64,
                        resolution=(1600, 900), exposure=exposure)
    save_city()


main()
