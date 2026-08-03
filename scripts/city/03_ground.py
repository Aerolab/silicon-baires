"""Step 03 — the site.

One asphalt sheet under everything, block slabs raised on top. The road is the
gap between the slabs, which is the decision the L1 spike settled.

Layout, third pass. The second one cut the grid with a curved arterial, and a
curve meeting an orthogonal grid always leaves ragged leftovers: a block that
merely touches the corridor loses its whole 64 m footprint to clear a 12 m
verge, so the arterial ended up flanked by two enormous empty roads. Dropped.

The city is now strictly rectangular. Variety comes from the grid itself:
street widths differ (two wide avenues among narrow local streets) and block
sizes differ per row and column, so nothing reads as one repeated module.

Every block corner is cut at 45 degrees. That is the ochava, which Buenos Aires
requires by code on every corner building, and it is the cheapest structural
cue in the whole project: four bevels per block, and the crossings open into
octagons. With square corners this grid reads as Manhattan.

    ./bl scripts/city/03_ground.py
"""
import sys, pathlib, math, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from _common import Mesh, collection, mat, pbrmat, rng, counts, srgb

R = ROOT / "renders"

EXTENT = 9                    # blocks per side
WALK = 2.5                    # sidewalk inside the block edge
MARK_Z = 0.03

# A lane is 3.5 m. Local streets carry two lanes, avenues four.
LOCAL, AVENUE = 12.0, 22.0
# The ochava: Buenos Aires cuts every street corner at 45 degrees by code, so
# no block downtown has a 90-degree corner and the pavement widens into an
# octagon at every crossing. It is the cheapest structural cue there is - four
# bevels per block - and it is the one that decides whether the grid reads as
# Buenos Aires or as Manhattan. 4 m of chord, so 2.83 m off each side.
OCHAVA = 4.0 / math.sqrt(2.0)
AVENUES_X = {2, 6}            # which street indices are wide, per axis
AVENUES_Y = {3, 7}
BLOCK_SIZES = [64.0, 52.0, 76.0, 64.0, 58.0, 70.0, 64.0, 54.0, 72.0]

# The cells that merge into the block the title stands on. Two, not four: with
# the baseline on the street grid the word's footprint measures a*H across and
# W + a*H along, so it wants one block wide by two long, and four left half the
# block as empty paving.
SUPER = {(4, 4), (4, 5)}
SUPER_KEY = (4, 4)
SUPER_LIFT = 0.55

SPECIAL = {
    (0, 7): "park", (7, 7): "park", (1, 0): "construction",
    (2, 0): "construction", (6, 1): "std", (1, 6): "std", (7, 4): "std",
    (3, 1): "park",
    # the construction site used to sit at (4, 5), which is dead centre of the
    # hero frame and therefore dead centre under the title. A word hanging
    # over an excavation reads as a caption, not as part of the city.
    (5, 7): "construction",
    # the hero camera looks at the origin, so the middle of the grid has to be
    # built up: a park there fills the whole frame with trees
    (4, 4): "std", (3, 4): "plaza", (4, 3): "std", (3, 3): "std",
    (5, 4): "plaza",
    # (4, 5) carries the title now, so it is built up like the rest of the
    # campus. Keeping the key here and only changing its value matters: the
    # kinds of every other lot come out of one RNG stream, and adding or
    # removing a key shifts all of them.
    (4, 5): "std",
}


def ochava(cx, cy, w, d, cut=None):
    """The block outline: a rectangle with its four corners cut at 45 degrees.

    Returned counter-clockwise. The cut is clamped to a quarter of the shorter
    side so a narrow lot cannot fold in on itself.
    """
    c = min(OCHAVA if cut is None else cut, min(w, d) / 4)
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - d / 2, cy + d / 2
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c),
            (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def axis_layout(avenues):
    """Street centres and block spans down one axis, from cumulative widths."""
    widths = [AVENUE if k in avenues else LOCAL for k in range(EXTENT + 1)]
    sizes = [BLOCK_SIZES[i % len(BLOCK_SIZES)] for i in range(EXTENT)]
    pos, streets, spans = 0.0, [], []
    for k in range(EXTENT + 1):
        streets.append(pos + widths[k] / 2)
        pos += widths[k]
        if k < EXTENT:
            spans.append((pos, sizes[k]))
            pos += sizes[k]
    off = pos / 2
    return ([s - off for s in streets],
            [(a - off + b / 2, b) for a, b in spans],
            widths, pos)


SX, BX, WX, TOTAL_X = axis_layout(AVENUES_X)
SY, BY, WY, TOTAL_Y = axis_layout(AVENUES_Y)
CITY = max(TOTAL_X, TOTAL_Y)


def pick_kind(i, j, r):
    """The reference block interior is mostly paving and parking, not lawn."""
    if (i, j) in SPECIAL:
        return SPECIAL[(i, j)]
    # Buildings only land on "plaza" and "std", so these weights decide how
    # built-up the city is. The first straight-grid pass gave 38 % to parks and
    # the result was a forest with a few offices in it.
    x = r.random()
    if x < 0.22:
        return "plaza"
    if x < 0.36:
        return "parking"
    if x < 0.48:
        return "park"
    return "std"


def surface_mat(kind):
    """Ordinary blocks are lawn. Tried the other two ways and measured both.

    The frame reads 27.7 % green against a reference that runs 21.9 to 26.2,
    and the ground contributes 14.9 points of that against 9.7 from every tree
    canopy in frame put together, so paving the ordinary blocks is the obvious
    lever. It does not work:

        all lawn      green 27.7 %   saturation 0.284
        half paved    green 19.5 %   saturation 0.245
        all paved     green 17.3 %   saturation 0.237

    Half paved lands closer to all paved than to all lawn, which gives the
    game away: the hero frame shows about six blocks out of eighty, so the
    number is decided by which handful the camera happens to see, not by the
    proportion in the city. It is sampling noise at n = 6.

    So this stays as it was. All lawn scores best on saturation, which is the
    measure that actually mattered, and its 1.5-point green overshoot is
    smaller than the 4.3-point spread the four reference frames have between
    themselves. Do not chase this number again from here; the lever would have
    to be the tree count or the palette, not the lot surface.
    """
    return {"park": mat("Grass"), "parking": mat("Asphalt Lot"),
            "plaza": mat("Paving"), "construction": mat("Dirt"),
            "std": mat("Grass")}[kind]


def retint(name, hex_col):
    m = bpy.data.materials[name]
    c = srgb(hex_col)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = \
        (c[0], c[1], c[2], 1.0)


# ---------------------------------------------------------------------------
def build_sheet(m):
    m.quad(0, 0, CITY * 1.3, CITY * 1.3, 0.0, mat("Asphalt"))


def super_bounds():
    """The two cells the title stands on, merged into one block.

    The title takes up real ground, and a word longer than a block otherwise
    crosses a street, which puts letters growing out of the asphalt. The
    reference solves it the way a real campus does: the title occupies one
    block and the streets run around it, so the street between these two cells
    is removed and they become one.

    Two, not four. With the baseline on the street the footprint is the word
    itself, its cap height across by its length along, which wants one block
    wide by two long. Four left half the site as empty paving.
    """
    (i0, j0), (i1, j1) = min(SUPER), max(SUPER)
    x0 = BX[i0][0] - BX[i0][1] / 2
    x1 = BX[i1][0] + BX[i1][1] / 2
    y0 = BY[j0][0] - BY[j0][1] / 2
    y1 = BY[j1][0] + BY[j1][1] / 2
    return x0, x1, y0, y1


def in_super(x, y, pad=0.0):
    x0, x1, y0, y1 = super_bounds()
    return x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad


def build_blocks(m, r):
    lots = {}
    for i, (cx, bw) in enumerate(BX):
        for j, (cy, bd) in enumerate(BY):
            kind = pick_kind(i, j, r)
            # the RNG is consumed either way: the kinds of every other lot come
            # out of this one stream and skipping a draw shifts all of them
            lift = round(r.uniform(0.30, 0.85), 2)
            if (i, j) in SUPER:
                continue
            m.prism(ochava(cx, cy, bw, bd), 0.0, lift, mat("Sidewalk"))
            iw, idp = bw - WALK * 2, bd - WALK * 2
            # the inner surface keeps the same chamfer, so the pavement stays
            # an even width all the way around the corner
            m.flat(ochava(cx, cy, iw, idp), lift + 0.02, surface_mat(kind))
            lots[(i, j)] = (cx, cy, [iw, idp], lift, kind)

    x0, x1, y0, y1 = super_bounds()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bw, bd = x1 - x0, y1 - y0
    lift = SUPER_LIFT
    m.prism(ochava(cx, cy, bw, bd), 0.0, lift, mat("Sidewalk"))
    m.flat(ochava(cx, cy, bw - WALK * 2, bd - WALK * 2), lift + 0.02,
           surface_mat("plaza"))
    lots[SUPER_KEY] = (cx, cy, [bw - WALK * 2, bd - WALK * 2], lift, "plaza")
    print(f"  superblock {bw:.0f} x {bd:.0f} m at ({cx:.0f}, {cy:.0f})")
    return lots


# --- markings --------------------------------------------------------------
def build_markings(m):
    mk = mat("Marking")
    rr = rng(5150)

    def paint(cx, cy, ww, hh):
        # the two streets that used to cross the superblock are gone; their
        # centre lines and zebras would otherwise still be painted across it
        if not in_super(cx, cy, -WALK):
            m.quad(cx, cy, ww, hh, MARK_Z, mk)

    for axis in (0, 1):
        streets, widths = (SX, WX) if axis == 0 else (SY, WY)
        blocks = BX if axis == 0 else BY
        for s, w in zip(streets, widths):
            carriage = w - WALK * 2
            avenue = w >= AVENUE
            for (b, size) in blocks:
                n = max(1, int((size - 8) / 7.0))
                for k in range(n):                     # dashed centre line
                    d = b - (size - 8) / 2 + k * 7.0
                    cx, cy = (d, s) if axis == 0 else (s, d)
                    ww, hh = (3.2, 0.14) if axis == 0 else (0.14, 3.2)
                    paint(cx, cy, ww, hh)
                if avenue:                             # plus two lane dividers
                    for side in (-1, 1):
                        o = side * carriage / 4
                        cx, cy = ((b, s + o) if axis == 0 else (s + o, b))
                        ww, hh = ((size - 8, 0.12) if axis == 0
                                  else (0.12, size - 8))
                        paint(cx, cy, ww, hh)

    for sx, wx in zip(SX, WX):                          # zebras, not everywhere
        for sy, wy in zip(SY, WY):
            for axis in (0, 1):
                if rr.random() < 0.40:
                    continue
                w = wx if axis == 0 else wy
                across = (wy if axis == 0 else wx) - WALK * 2
                for direction in (-1, 1):
                    base = (sx if axis == 0 else sy) + \
                        direction * ((w - WALK * 2) / 2 + 1.2)
                    n = max(3, int(across / 1.6))
                    for k in range(n):
                        o = (sy if axis == 0 else sx) - across / 2 + 0.8 + \
                            k * (across - 1.6) / max(n - 1, 1)
                        cx, cy = (base, o) if axis == 0 else (o, base)
                        ww, hh = (2.2, 0.5) if axis == 0 else (0.5, 2.2)
                        paint(cx, cy, ww, hh)


def build_parking(m, lots):
    mk = mat("Marking")
    for (cx, cy, size, lift, kind) in lots.values():
        if kind != "parking":
            continue
        w, d = size
        rows, z = 3, lift + 0.04
        for row in range(rows):
            y = cy - d / 2 + 7 + row * (d - 14) / (rows - 1)
            n = max(4, int((w - 5) / 2.6))
            for k in range(n):
                x = cx - w / 2 + 2.5 + k * (w - 5) / (n - 1)
                m.quad(x, y, 0.12, 4.6, z, mk)
            m.quad(cx, y - 2.4, w - 5, 0.12, z, mk)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    if "GROUND_placeholder" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["GROUND_placeholder"],
                                do_unlink=True)
    pbrmat("Paving", "#6e6a5e", 0.85)
    pbrmat("Dirt", "#8a7355", 0.92)
    pbrmat("Asphalt Lot", "#26231e", 0.80)
    # the reference's road sits at 0.18 luminance and is warm; the first pass
    # was 0.38 and cool grey, which left no dark values in the frame at all
    retint("Asphalt", "#211e19")
    retint("Sidewalk", "#98938a")
    retint("Marking", "#d8d8d2")
    retint("Grass", "#4d9c26")
    retint("Foliage Dark", "#2a6b1c")
    retint("Foliage Mid", "#4a9422")
    retint("Foliage Light", "#7cc32e")
    retint("Trunk", "#7a3a22")
    retint("Concrete Warm", "#e9dcc0")
    retint("Concrete Warm2", "#d8c4a0")
    retint("Concrete Cool", "#b6bcbd")
    retint("Concrete Cool2", "#8d9599")
    retint("Glass Light", "#5f97a6")
    retint("Glass Dark", "#15181b")

    site = collection("SITE")
    for ob in list(site.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    r = rng(4711)
    m = Mesh()
    build_sheet(m)
    lots = build_blocks(m, r)
    m.build("site", site)

    mm = Mesh()
    build_markings(mm)
    build_parking(mm, lots)
    mm.build("markings", site)

    (R / "city_lots.json").write_text(json.dumps({
        "lots": [{"key": [str(i), str(j)], "x": cx, "y": cy, "size": size,
                  "lift": lift, "kind": kind}
                 for (i, j), (cx, cy, size, lift, kind) in lots.items()],
        "streets_x": SX, "streets_y": SY, "widths_x": WX, "widths_y": WY,
        "blocks_x": BX, "blocks_y": BY, "walk": WALK,
        "superblock": list(super_bounds()),
    }))
    print(f"\n  lots: {len(lots)}   city {CITY:.0f} m")
    u, t = counts()
    print(f"  triangles: {u} unique / {t} total")

    cam = bpy.data.objects["HeroCam"]
    cam.data.ortho_scale = CITY * 1.15
    blib.render(str(R / "city_03_plan.png"), "EEVEE", samples=32,
                resolution=(1500, 850),
                exposure=bpy.context.scene.view_settings.exposure)
    blib.save(str(R / "city.blend"))


main()
