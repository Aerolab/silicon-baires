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
from _solids import Solids

R = ROOT / "renders"

BLOCK, STREET, PITCH, WALK = 64.0, 12.0, 76.0, 2.5
EXTENT, HALF = 9, 4.0
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
TALL = {(1, 2): 18, (7, 6): 12, (2, 7): 10, (7, 2): 8, (1, 5): 9}
LANDMARKS = {(6, 1), (1, 6), (7, 4)}     # step 06 owns these plots
# and step 06b owns these two: the Obelisco and the Floralis stand on them.
# "plaza" is not an empty lot - this step builds offices on plazas - so
# without this the Obelisco went up inside somebody's fourth floor.
PORTENO = {(3, 4), (5, 4)}
# the blocks the title stands on. Step 08 builds the letters here as real
# buildings, so step 04 builds nothing: see build_campus().
CAMPUS = {(4, 4), (4, 5), (5, 4), (5, 5)}
GROUND_INSET = 0.6

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


def place_on_lot(m, kit, coll, sol, signs, cx, cy, size, lift, kind, r):
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
        if r.random() < 0.10:
            continue                       # a gap: courtyard, planting or car park
        # setbacks were 6-12 m, which left every building floating in a lawn.
        # The reference puts the wall almost on the pavement.
        w = sw * fw - r.uniform(1.5, 4.0)
        d = sd * fh - r.uniform(1.5, 4.0)
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
        keep = plan_sign(bx + hx, by + hy, hw, hd, top, floors, r, signs, sol)
        if keep is not None:
            keep = (keep[0] + hx, keep[1] + hy, keep[2], keep[3])
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
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    kit = {ob.name: ob for ob in bpy.data.collections["KIT"].objects}
    from _common import pbrmat
    pbrmat("Brick Warm", "#b0603c", 0.85)
    pbrmat("Facade Teal", "#1f8478", 0.75)
    pbrmat("Concrete Dark", "#6e7276", 0.85)
    pbrmat("Roof Deck", "#a8a292", 0.88)
    pbrmat("Roof Dark", "#2b2b28", 0.90)

    for name in ("BUILDINGS", "ROOFPROPS", "CAMPUSROOF"):
        if name in bpy.data.collections:
            c = bpy.data.collections[name]
            for ob in list(c.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
    bcoll = collection("BUILDINGS")
    pcoll = collection("ROOFPROPS")
    # its own collection so step 05 can leave these roofs alone: the title
    # hangs half a metre over them and a person up there stands through a letter
    ccoll = collection("CAMPUSROOF")

    r = rng(90210)
    m = Mesh()
    sol = Solids()
    signs = []

    lots = json.loads((R / "city_lots.json").read_text())["lots"]
    for lot in lots:
        i, j = int(lot["key"][0]), int(lot["key"][1])
        if (i, j) in TALL or (i, j) in LANDMARKS or (i, j) in CAMPUS \
                or (i, j) in PORTENO:
            continue
        place_on_lot(m, kit, pcoll, sol, signs, lot["x"], lot["y"],
                     lot["size"], lot["lift"], lot["kind"], r)

    build_campus(m, kit, pcoll, ccoll, lots, r)
    build_towers(m, kit, pcoll, sol, signs, lots, r)
    m.build("buildings", bcoll)

    # Second pass over the words. A sign is planned in the same loop that
    # publishes the buildings, so when it is planned the buildings that come
    # after it do not exist yet and it cannot see the one it is about to run
    # into. Re-checking here, with everything published, is the whole fix.
    dropped = 0
    for rec in list(signs):
        if rec["kind"] != "parapet":
            continue
        fit = sign_fits(sol, rec["x"], rec["y"], rec["w"], rec["z"], rec["h"])
        if fit is None:
            signs.remove(rec)
            dropped += 1
        else:
            rec["w"] = fit
    if dropped:
        print(f"  {dropped} words dropped: no room once every building was in")

    sol.merge_into(R / "city_solids.json", "buildings")
    (R / "city_signs.json").write_text(json.dumps(signs, indent=1))
    kinds = {}
    for s in signs:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    print(f"  footprints published: {len(sol.boxes)}")
    print(f"  signs planned: {len(signs)}   " +
          "  ".join(f"{k} {v}" for k, v in sorted(kinds.items())))

    u, t = counts()
    print(f"\n  roof props: {len(pcoll.objects)}")
    print(f"  triangles: {u} unique / {t} total")

    cam = bpy.data.objects["HeroCam"]
    exposure = bpy.context.scene.view_settings.exposure
    blib.render(str(R / "city_04_hero.png"), "EEVEE", samples=64,
                resolution=(1600, 900), exposure=exposure)
    cam.data.ortho_scale = 200.0
    blib.render(str(R / "city_04_closeup.png"), "EEVEE", samples=64,
                resolution=(1600, 900), exposure=exposure)
    cam.data.ortho_scale = 700.0
    blib.save(str(R / "city.blend"))


main()
