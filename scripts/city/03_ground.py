"""Step 03 — the site.

One asphalt sheet under everything, block slabs raised on top. The road is the
gap between the slabs, which is the decision the L1 spike settled.

Layout: a 7 x 7 orthogonal grid, with the middle 3 x 3 replaced by a circus —
a planted disc, a ring road around it, and eight radial sector blocks. That
gives the sweeping curves the reference lives on without a single clipped
polygon: everything is a rectangle or an annulus sector.

    ./bl scripts/city/03_ground.py
"""
import sys, pathlib, math, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from _common import Mesh, collection, mat, pbrmat, rng, counts

R = ROOT / "renders"

BLOCK, STREET, PITCH = 90.0, 22.0, 112.0
WALK = 4.0                    # sidewalk width inside the block edge
CARRIAGE = STREET - WALK * 2  # 14 m of asphalt between kerbs
EXTENT = 7
HALF = (EXTENT - 1) / 2
CITY = EXTENT * BLOCK + (EXTENT + 1) * STREET
MARK_Z = 0.03

# circus, replacing the middle 3 x 3
PLAZA_R = 48.0                # planted disc in the middle
RING_R = PLAZA_R + STREET     # outer kerb of the ring road
SECTOR_R = RING_R + BLOCK     # outer edge of the eight sector blocks
CLEAR_R = SECTOR_R + 12.0     # grid cells touching this are dropped

# lot surface per cell, keyed (i, j) from the south-west corner
SPECIAL = {
    (0, 6): "park", (1, 6): "park", (0, 0): "parking", (6, 6): "plaza",
    (3, 0): "park", (0, 3): "parking", (6, 3): "park", (3, 6): "parking",
    (5, 5): "std", (1, 1): "std",
    # the construction site, and the landmark plots step 06 owns. All of these
    # have to sit inside the hero frame, which only reaches cells 1..5.
    (3, 1): "construction", (2, 1): "construction",
    (5, 1): "std", (1, 5): "std", (5, 3): "std",
}


def retint(name, hex_col):
    """Nudge a palette colour already living in the .blend."""
    from _common import srgb
    m = bpy.data.materials[name]
    c = srgb(hex_col)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = \
        (c[0], c[1], c[2], 1.0)


def cell_centre(i, j):
    return (i - HALF) * PITCH, (j - HALF) * PITCH


def kept(i, j):
    """Grid cells whose square reaches into the circus are dropped."""
    cx, cy = cell_centre(i, j)
    nx = max(0.0, abs(cx) - BLOCK / 2)
    ny = max(0.0, abs(cy) - BLOCK / 2)
    return math.hypot(nx, ny) > CLEAR_R


def lift_for(i, j, r):
    """Blocks stand 0.3-1.2 m proud of the road. Varying it makes terraces."""
    return round(r.uniform(0.35, 1.15), 2)


def pick_kind(i, j, r):
    """Not every block is a lawn. The reference is mostly paving and parking."""
    if (i, j) in SPECIAL:
        return SPECIAL[(i, j)]
    x = r.random()
    return "plaza" if x < 0.34 else ("parking" if x < 0.48 else "std")


def surface_mat(kind):
    return {"park": mat("Grass"), "parking": mat("Asphalt"),
            "plaza": mat("Paving"), "construction": mat("Dirt"),
            "std": mat("Grass")}[kind]


# ---------------------------------------------------------------------------
def build_sheet(m):
    m.quad(0, 0, CITY * 1.25, CITY * 1.25, 0.0, mat("Asphalt"))


def build_grid_blocks(m, r):
    """Each block: a sidewalk slab, then the lot surface inset on top."""
    lots = {}
    for i in range(EXTENT):
        for j in range(EXTENT):
            if not kept(i, j):
                continue
            cx, cy = cell_centre(i, j)
            kind = pick_kind(i, j, r)
            lift = lift_for(i, j, r)
            m.slab(cx, cy, BLOCK, BLOCK, 0.0, lift, mat("Sidewalk"))
            inner = BLOCK - WALK * 2
            m.quad(cx, cy, inner, inner, lift + 0.02, surface_mat(kind))
            lots[(i, j)] = (cx, cy, inner, lift, kind)
    return lots


def build_circus(m, r):
    """Planted disc, ring road, eight sector blocks with radial streets."""
    lots = {}
    lift = 0.9
    # the disc in the middle, a step higher than the blocks around it
    m.arc_band(0.0, PLAZA_R, 0, 2 * math.pi, 0.0, mat("Sidewalk"), segs=64)
    m.prism([(PLAZA_R * math.cos(2 * math.pi * k / 64),
              PLAZA_R * math.sin(2 * math.pi * k / 64)) for k in range(64)],
            0.0, lift + 0.25, mat("Sidewalk"))
    m.arc_band(0.0, PLAZA_R - WALK, 0, 2 * math.pi, lift + 0.27,
               mat("Grass"), segs=64)

    n = 8
    gap = STREET / ((RING_R + SECTOR_R) / 2)      # radial street, in radians
    for k in range(n):
        a0 = 2 * math.pi * k / n + gap / 2
        a1 = 2 * math.pi * (k + 1) / n - gap / 2
        segs = max(6, int((a1 - a0) * SECTOR_R / 3.0))
        poly = ([(SECTOR_R * math.cos(a0 + (a1 - a0) * t / segs),
                  SECTOR_R * math.sin(a0 + (a1 - a0) * t / segs))
                 for t in range(segs + 1)] +
                [(RING_R * math.cos(a1 - (a1 - a0) * t / segs),
                  RING_R * math.sin(a1 - (a1 - a0) * t / segs))
                 for t in range(segs + 1)])
        h = round(0.5 + 0.5 * ((k * 3) % 4) / 3.0, 2)
        m.prism(poly, 0.0, h, mat("Sidewalk"))
        inset = WALK / SECTOR_R
        m.arc_band(RING_R + WALK, SECTOR_R - WALK, a0 + inset, a1 - inset,
                   h + 0.02, mat("Grass"))
        am = (a0 + a1) / 2
        rm = (RING_R + SECTOR_R) / 2
        lots[("c", k)] = (rm * math.cos(am), rm * math.sin(am),
                          (a0, a1, RING_R + WALK, SECTOR_R - WALK), h, "sector")
    return lots


def build_islands(m):
    """The four diagonal pockets the circus leaves against the grid.

    Bounded by the ring road on the inside and by the grid streets on the
    outside: a curved triangle. Without these the middle of the city is a
    large dead apron of asphalt.
    """
    def shape(edge, radius, sx, sy):
        """Corner square of half-size `edge`, minus the disc of `radius`.

        The arc angles have to be derived from the same pair of numbers as the
        straight edges, or the chain does not close and the polygon
        self-intersects into garbage.
        """
        y0 = math.sqrt(max(radius * radius - edge * edge, 1.0))
        a_lo, a_hi = math.atan2(y0, edge), math.atan2(edge, y0)
        poly = [(edge, y0), (edge, edge), (y0, edge)]
        poly += [(radius * math.cos(a_hi + (a_lo - a_hi) * t / 20),
                  radius * math.sin(a_hi + (a_lo - a_hi) * t / 20))
                 for t in range(21)]
        return [(sx * x, sy * y) for x, y in poly]

    lots = {}
    L = PITCH + BLOCK / 2                  # edge of the cleared 3 x 3
    RI = SECTOR_R + STREET                 # inner edge, across the ring road
    lift = 0.75
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.prism(shape(L, RI, sx, sy), 0.0, lift, mat("Sidewalk"))
            m.prism(shape(L - WALK, RI + WALK, sx, sy), lift, lift + 0.02,
                    mat("Grass"))
            d = (L + RI) / 2 / math.sqrt(2) * 1.06
            lots[("i", sx, sy)] = (sx * d, sy * d, 34.0, lift, "island")
    return lots


# --- markings --------------------------------------------------------------
def street_lines():
    """Centres of every street, both axes."""
    return [(-HALF - 0.5 + k) * PITCH for k in range(EXTENT + 1)]


def build_markings(m):
    mk = mat("Marking")
    half = CARRIAGE / 2
    centres = street_lines()
    blocks = [(i - HALF) * PITCH for i in range(EXTENT)]

    for axis in (0, 1):
        for s in centres:
            for b in blocks:
                if math.hypot(s, b) < CLEAR_R + BLOCK * 0.4:
                    continue
                # solid edge lines beside the block, stopping short of the ends
                for side in (-1, 1):
                    off = s + side * (half - 0.45)
                    cx, cy = (b, off) if axis == 0 else (off, b)
                    w, h = (BLOCK - 6.0, 0.18) if axis == 0 else (0.18, BLOCK - 6.0)
                    m.quad(cx, cy, w, h, MARK_Z, mk)
                # centre dashes
                for k in range(-6, 7):
                    d = b + k * 7.0
                    if abs(d - b) > BLOCK / 2 - 5:
                        continue
                    cx, cy = (d, s) if axis == 0 else (s, d)
                    w, h = (3.4, 0.16) if axis == 0 else (0.16, 3.4)
                    m.quad(cx, cy, w, h, MARK_Z, mk)

    # crosswalks and stop bars at every surviving intersection
    for sx in centres:
        for sy in centres:
            if math.hypot(sx, sy) < CLEAR_R + STREET:
                continue
            for axis in (0, 1):
                for direction in (-1, 1):
                    base = (sx, sy)[axis] + direction * (half + 1.3)
                    for k in range(9):
                        o = (sx, sy)[1 - axis] - half + 0.9 + k * 1.55
                        cx, cy = (base, o) if axis == 0 else (o, base)
                        w, h = (3.0, 0.72) if axis == 0 else (0.72, 3.0)
                        m.quad(cx, cy, w, h, MARK_Z, mk)
                    st = (sx, sy)[axis] + direction * (half + 5.4)
                    cx, cy = (st, sy) if axis == 0 else (sx, st)
                    w, h = (0.4, CARRIAGE) if axis == 0 else (CARRIAGE, 0.4)
                    m.quad(cx, cy, w, h, MARK_Z, mk)

    # ring road: two lane lines that need no joints at all
    rr = (PLAZA_R + RING_R) / 2
    for r_off in (-3.6, 3.6):
        m.arc_band(rr + r_off - 0.09, rr + r_off + 0.09, 0, 2 * math.pi,
                   MARK_Z, mk, segs=96)


def build_parking(m, lots):
    """Bays on the parking lots: cheap, and they fill dead ground."""
    mk = mat("Marking")
    for (cx, cy, inner, lift, kind) in lots.values():
        if kind != "parking":
            continue
        rows, z = 4, lift + 0.04
        for row in range(rows):
            y = cy - inner / 2 + 9 + row * (inner - 18) / (rows - 1)
            for k in range(16):
                x = cx - inner / 2 + 3 + k * (inner - 6) / 15
                m.quad(x, y, 0.14, 5.0, z, mk)
            m.quad(cx, y - 2.6, inner - 6, 0.14, z, mk)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    if "GROUND_placeholder" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["GROUND_placeholder"],
                                do_unlink=True)
    pbrmat("Paving", "#c2beb4", 0.80)
    pbrmat("Dirt", "#a08a6c", 0.90)
    # the first pass read as neon against all that concrete
    retint("Grass", "#4f8f33")
    retint("Sidewalk", "#bdb9ae")

    site = collection("SITE")
    for ob in list(site.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    r = rng(4711)
    m = Mesh()
    build_sheet(m)
    lots = build_grid_blocks(m, r)
    lots.update(build_circus(m, r))
    lots.update(build_islands(m))
    m.build("site", site)

    mm = Mesh()
    build_markings(mm)
    build_parking(mm, lots)
    mm.build("markings", site)

    # hand the lot table to the later steps instead of re-deriving it
    table = []
    for key, (cx, cy, size, lift, kind) in lots.items():
        table.append({"key": [str(k) for k in (key if isinstance(key, tuple)
                                               else (key,))],
                      "x": cx, "y": cy,
                      "size": size if not isinstance(size, tuple) else list(size),
                      "lift": lift, "kind": kind})
    (R / "city_lots.json").write_text(json.dumps(table))
    print(f"\n  lots: {len(lots)}")
    u, t = counts()
    print(f"  triangles: {u} unique / {t} total")

    cam = bpy.data.objects["HeroCam"]
    exposure = bpy.context.scene.view_settings.exposure
    cam.data.ortho_scale = 900.0
    blib.render(str(R / "city_03_plan.png"), "EEVEE", samples=32,
                resolution=(1500, 850), exposure=exposure)
    cam.data.ortho_scale = 620.0
    blib.render(str(R / "city_03_hero.png"), "EEVEE", samples=64,
                resolution=(1500, 850), exposure=exposure)
    blib.save(str(R / "city.blend"))


main()
