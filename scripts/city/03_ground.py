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

One street is not like the others: the Avenida 9 de Julio, 52 m wide, two
blocks off centre. It is built as a section rather than as a wide road - two
one-way carriageways, two planted medians, a Metrobus corridor down the middle
and an island at one crossing for the Obelisco to stand on. See the constants
below for why the proportions are what they are.

    ./bl scripts/city/03_ground.py
"""
import sys, pathlib, math, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from _common import (Mesh, collection, mat, rng, counts, srgb, R,
                     median_runs, LOTS, open_city, save_city, purge, preview)


EXTENT = 9                    # blocks per side
WALK = 2.5                    # sidewalk inside the block edge
MARK_Z = 0.03

# A lane is 3.5 m. Local streets carry two lanes, avenues four.
LOCAL, AVENUE = 12.0, 22.0

# --- Avenida 9 de Julio ----------------------------------------------------
# The real one is 110 m between building lines, 140 counting the lateral
# streets, which is 20 % of this city and about 82 % of the hero frame: at that
# width it stops being a street in a city and becomes a city cut in half.
#
# 70 m, and the number is not a compromise between 110 and "what fits". It is
# set by one fact: **the real avenue is wider than a city block** - 110 m
# against a porteno block of about 100 - and being narrower than a block is
# exactly what stops a wide road from reading as the widest avenue in the
# world. Our blocks average 64 m. So 70 is the smallest width that keeps the
# relationship, and the relationship is the whole cue. The first attempt was
# 52 m, which is a wide avenue and nothing more.
#
# The section, from the west building line, all of it inside the street gap
# because the pavements belong to the blocks:
#
#     0 .. 19   lateral carriageway (five lanes, one way)
#    19 .. 28   planted median
#    28 .. 31.5 busway
#    31.5 .. 38.5  Metrobus platform
#    38.5 .. 42 busway
#    42 .. 51   planted median
#    51 .. 70   lateral carriageway (five lanes, the other way)
#
# The bus corridor stays at 14 m however wide the avenue gets: four exclusive
# lanes are 13-14 m and that is sourced. An earlier version gave it 16 and the
# carriageways 10, and from above that reads as a dark canal with two service
# roads beside it. It is the wrong way round - what makes the avenue enormous
# is the asphalt, and the busway is a thin thing laid down the middle of it.
#
# It runs north-south, like the real one, so its position is an X coordinate
# and it is an entry in the X street table.
AVE9J = 70.0
NINE_X = 6                    # which X street index it replaces
MEDIAN = (7.0, 16.0)          # from the centre line: |offset| in this band
BUSWAY = 7.0                  # half-width of the whole bus corridor
PLATFORM = 3.5                # half-width of the island between the bus lanes
MEDIAN_LIFT = 0.18
# The shelters. Two to a block where the block is long enough, and clear of the
# crossings by STATION_MARGIN at each end: a canopy hanging over an
# intersection is the one place it must not be, because that is where the cross
# traffic and the zebras are.
STATION_LEN = 22.0
STATION_GAP = 8.0
STATION_MARGIN = 5.0
# 40 cm, which is the published figure for the real platform: the buses have a
# level-boarding door and the height is the reason the platform exists
PLATFORM_LIFT = 0.40
# Plaza de la Republica: where the Obelisco stands, in the middle of the
# avenue - and MID-BLOCK, not on a crossing.
#
# It was on a crossing first, which is where the real one is. It does not work,
# because our crossings are crossings: the cross street runs straight through
# the island, so traffic drives over the plaza and through the monument. The
# real Corrientes does not do that - it was diverted in 1971 and bends around
# the Obelisco, so the plaza is a hole in the traffic rather than a junction.
# Mid-block gives the same read with none of the geometry: nothing crosses it
# except the busway, which is dealt with in step 11.
PLAZA_J = 2                   # which Y BLOCK the plaza sits in the middle of
# The island is an OVAL, not a rectangle. Off a photograph: the plaza swells
# out of the avenue as a long rounded lens, with curved planting beds in the
# two ends and the monument on paving in the middle. A rectangle of the same
# size reads as a platform - part of the road - and the curve is the whole
# difference, because it is the only curve anywhere in this city and the eye
# goes straight to it.
#
# 31 x 60 m. The real Plaza de la Republica is about 100 and there is no room
# for that inside the avenue, but the plaza's own dimensions are not what
# carries the resemblance: a monument standing in the middle of a road too wide
# to cross is.
PLAZA_HALF = 30.0             # how far the plaza runs along the avenue
PLAZA_WIDE = 15.5             # half-width: it swallows both medians, and stops
                              # half a metre short of the lateral carriageway
# The ochava: Buenos Aires cuts every street corner at 45 degrees by code, so
# no block downtown has a 90-degree corner and the pavement widens into an
# octagon at every crossing. It is the cheapest structural cue there is - four
# bevels per block - and it is the one that decides whether the grid reads as
# Buenos Aires or as Manhattan. 4 m of chord, so 2.83 m off each side.
OCHAVA = 4.0 / math.sqrt(2.0)
AVENUES_X = {2, 6}            # which street indices are wide, per axis
AVENUES_Y = {3, 7}
BLOCK_SIZES = [64.0, 52.0, 76.0, 64.0, 58.0, 70.0, 64.0, 54.0, 72.0]

# --- the south rim ---------------------------------------------------------
# One more row of blocks, hanging off the south edge of the grid, and it exists
# for exactly one reason: the opening frame of the move runs off the end of the
# map. The camera starts over the southeast at (163, -214) and its top-left
# corner reaches y = -440, where the built area stops at -357. That is 83 m of
# bare sheet in the corner of frame 1 - 7 per cent of the opening cut, and 2.5
# per cent even at the old x1.479 zoom, so this was already shipping before the
# zoom was opened. The x edge is fine: the same corner arithmetic gives 8 m of
# overshoot there, and it lands behind the buildings on the last column.
#
# WHY IT IS A RIM AND NOT A TENTH ROW. `EXTENT = 10` is the obvious move and it
# is the wrong one. axis_layout centres the grid on the origin - `off = pos / 2`
# - so one more row shifts EVERY coordinate in the city by half a block, which
# moves the Obelisco, the title, the landmarks and the approved hero framing,
# and reshuffles the RNG stream that decides what kind every lot is on top of
# that. The rim is bolted on outside the grid instead: nothing in axis_layout
# changes, no street table gains an entry, and the existing city comes out
# byte-identical.
#
# The same care applies downstream. The rim lots are appended to city_lots.json
# AFTER the superblock, and every step that walks the lots with a shared RNG -
# 04 and 05 - skips them in its main pass and builds them at the end from a
# private stream, the device avenue_rng() and sign_rng() already document.
#
# 76 m deep, which is the deepest size in the table and not a coincidence: the
# rim has to reach past -440 on its own, because there is no second row behind
# it to hide its far edge. 76 lands the outer pavement at -433 and the street
# beyond it carries to -445, which clears the corner with 5 m to spare.
RIM_DEPTH = 76.0
RIM_STREET = 12.0             # the road along its outer side. See build_rim
RIM_SEED = 8123

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
    (4, 4): "std", (4, 3): "std", (3, 3): "std",
    # The two plazas that used to flank the title held the Obelisco and the
    # Floralis, one block either side of the word. Two monuments and a title
    # inside three blocks is a souvenir shelf: nothing has room to be the
    # thing you look at. The Obelisco has moved into the middle of the avenue,
    # where it belongs.
    (3, 4): "std",
    # "park", not "plaza". The real Floralis stands in a 4 ha park with a 44 m
    # pool and nothing built anywhere near it - it is 2.5 km from the Obelisco,
    # which is three and a half times the width of this entire city. A plaza
    # lot puts offices around it and turns it into a fountain in a forecourt.
    #
    # It used to be (2, 7), the far corner of the city, chosen so it would read
    # on the opposite side of the frame from the Obelisco. That reasoning held
    # for a STILL. Once the camera moved it stopped being true: the shot sweeps
    # a narrow diagonal corridor and crosses 13 of the 81 blocks, and (2, 7) is
    # 2.83 frame half-widths off the nearest point of it. The Floralis was being
    # built for nobody.
    #
    # (5, 3) is 0.08 half-widths off the axis and is centred at 54 % of the move,
    # which is the stretch between the Obelisco leaving frame and the title
    # arriving. Not (4, 3) or (5, 4), which are just as central and are both
    # ADJACENT to the title superblock: a monument beside the word is the
    # souvenir-shelf mistake this file already made once.
    (5, 3): "park",
    # (2, 7) keeps its key and only changes its value, and (5, 4) gives its key
    # up to (5, 3). That pair of edits is deliberate: a block listed here
    # consumes no draw from the RNG, so ADDING a key silently reshuffles the
    # kind of every block after it. (5, 3) and (5, 4) are consecutive in the
    # iteration - i outer, j inner - so removing one key exactly where another
    # is added realigns the stream immediately, and (5, 4) inherits the draw
    # (5, 3) used to take. Everything downstream is byte-identical. Verified by
    # diffing city_lots.json, not assumed.
    (2, 7): "std",
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


def axis_layout(avenues, wide=None):
    """Street centres and block spans down one axis, from cumulative widths.

    `wide` overrides individual streets, which is how the 9 de Julio gets its
    52 m without every other avenue growing with it.
    """
    wide = wide or {}
    widths = [wide.get(k, AVENUE if k in avenues else LOCAL)
              for k in range(EXTENT + 1)]
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


SX, BX, WX, TOTAL_X = axis_layout(AVENUES_X, {NINE_X: AVE9J})
SY, BY, WY, TOTAL_Y = axis_layout(AVENUES_Y)
CITY = max(TOTAL_X, TOTAL_Y)
NINE = SX[NINE_X]             # the centre line of the avenue, an X coordinate
PLAZA = BY[PLAZA_J][0]        # and the middle of the block it stands in


def pick_kind(i, j, r):
    """The reference block interior is mostly paving and parking, not lawn."""
    if (i, j) in SPECIAL:
        return SPECIAL[(i, j)]
    # Buildings only land on "plaza" and "std", so these weights decide how
    # built-up the city is. The first straight-grid pass gave 38 % to parks and
    # the result was a forest with a few offices in it.
    # Only the thresholds move here, never the number of draws: the kinds of
    # every other lot come out of this one stream. A quarter of the city was a
    # lot with no building on it at all (parking or park), which is where most
    # of the bare green comes from - not from the setbacks.
    x = r.random()
    if x < 0.24:
        return "plaza"
    if x < 0.35:
        return "parking"
    if x < 0.43:
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


def build_rim(m, g, lots):
    """The extra row along the south edge, so the opening frame stays in the city.

    Keyed (i, -1) and appended to `lots` after the superblock, which is the
    contract every downstream step reads: a lot whose j is -1 is rim, it came
    last, and it must go on coming last. See the RIM_DEPTH note above for why
    this is bolted outside the grid rather than being a tenth row.

    Its own RNG, seeded once, for the same reason: pick_kind() and the lift draw
    in build_blocks() come out of the stream that decides the kind of all eighty
    lots, and taking nine more draws from it at any point would repaint the city.

    No parks and no plazas out here. The rim is at the very corner of one frame,
    out of focus and on screen for about three seconds, so what it has to do is
    read as more city - which means roofs. An empty lot at that distance is
    indistinguishable from the bare sheet it was built to cover.
    """
    r = rng(RIM_SEED)
    cy = -TOTAL_Y / 2 - RIM_DEPTH / 2
    for i, (cx, bw) in enumerate(BX):
        kind = "std" if r.random() < 0.82 else "parking"
        lift = round(r.uniform(0.30, 0.85), 2)
        m.prism(ochava(cx, cy, bw, RIM_DEPTH), 0.0, lift, mat("Sidewalk"))
        iw, idp = bw - WALK * 2, RIM_DEPTH - WALK * 2
        m.flat(ochava(cx, cy, iw, idp), lift + 0.02, surface_mat(kind))
        lots[(i, -1)] = (cx, cy, [iw, idp], lift, kind)

    # THE AVENUE HAS TO COME WITH IT. The 9 de Julio runs down x = NINE, which
    # is inside the exposed wedge, and build_avenue stops its busway and medians
    # at -TOTAL_Y / 2 like everything else. Without this the widest street in
    # the city loses its section exactly where the rim starts and turns into 70 m
    # of plain grey - which is more conspicuous than the bare sheet was.
    #
    # Built here rather than by extending build_avenue's runs, and that is the
    # whole point: those runs come out of _common.median_runs(BY, ...), which
    # step 05 reads to plant the median trees. Adding a run there would hand 05
    # a longer list and shift the stream that plants every tree in the city.
    # So the rim gets its section and no trees on it - at this distance, out of
    # focus and behind the last row of roofs, that is not a difference anyone
    # can see.
    north = -TOTAL_Y / 2
    outer = north - RIM_DEPTH - RIM_STREET
    m.quad(NINE, (north + outer) / 2, BUSWAY * 2, north - outer, 0.04,
           mat("Busway"))
    for side in (-1, 1):
        mc = side * (MEDIAN[0] + MEDIAN[1]) / 2
        mw = MEDIAN[1] - MEDIAN[0]
        a, b = north - RIM_DEPTH, north
        m.prism([(NINE + mc - mw / 2, a), (NINE + mc + mw / 2, a),
                 (NINE + mc + mw / 2, b), (NINE + mc - mw / 2, b)],
                0.0, MEDIAN_LIFT, mat("Sidewalk"))
        g.quad(NINE + mc, (a + b) / 2, mw - 1.0, b - a,
               MEDIAN_LIFT + 0.02, mat("Grass"))

    # and the paint. One rim-length span added to what build_markings and
    # avenue_markings already do per block: the dashed centre line of every
    # street that runs north-south, and the lane dividers of the two lateral
    # carriageways. Its own pass rather than an extra entry in BY, for the
    # reason above - BY is published and read downstream.
    mk = mat("Marking")
    n = max(1, int((RIM_DEPTH - 8) / 7.0))
    for k in range(n):
        d = cy - (RIM_DEPTH - 8) / 2 + k * 7.0
        for s, w in zip(SX, WX):
            if abs(s - NINE) < 1.0:
                continue                     # the avenue paints its own lanes
            g.quad(s, d, 0.14, 3.2, MARK_Z, mk)
        for side in (-1, 1):
            c = side * (MEDIAN[1] + AVE9J / 2) / 2
            for lane in (-5.25, -1.75, 1.75, 5.25):
                g.quad(NINE + c + lane, d, 0.12, 3.2, MARK_Z, mk)

    print(f"  south rim: {len(BX)} blocks at y={cy:.0f}, "
          f"reaching {outer:.0f}")
    return cy


# --- Avenida 9 de Julio ----------------------------------------------------
def ellipse(cx, cy, rx, ry, segs=44):
    """A closed oval as a polygon, counter-clockwise."""
    return [(cx + rx * math.cos(2 * math.pi * i / segs),
             cy + ry * math.sin(2 * math.pi * i / segs)) for i in range(segs)]


def build_avenue(m, g):
    """The medians, the busway and the Metrobus platforms.

    Solid geometry into `m`, flat paint into `g`. The medians are the whole
    point: a 52 m sheet of asphalt is a runway, and what makes the real avenue
    read from above is that it is striped along its length - carriageway,
    trees, buses, trees, carriageway - so the width is legible as structure
    rather than as absence.

    Everything stops at the crossings. A planted median that runs through an
    intersection is a wall, and the cross streets have to get across.
    """
    grass, kerb = mat("Grass"), mat("Sidewalk")
    plat, deck = mat("Paving Pale"), mat("Busway")
    stations = 0

    # the bus corridor: its own surface, so the two lanes read as a separate
    # road from the lateral carriageways. In two pieces, because the plaza
    # stands in the middle of it: left continuous, a dark ribbon came out from
    # behind the plaza at both ends and read as a tunnel mouth.
    y0, y1 = -TOTAL_Y / 2, TOTAL_Y / 2
    for a, b in ((y0, PLAZA - PLAZA_HALF), (PLAZA + PLAZA_HALF, y1)):
        m.quad(NINE, (a + b) / 2, BUSWAY * 2, b - a, 0.04, deck)

    # Cut against the plaza rather than dropping the whole run: skipping any
    # block that came near it took out two full block-lengths - 140 m of
    # avenue with no planting at all - to clear a 60 m island. And it has to be
    # a cut into TWO runs, not a trim of one end: the plaza sits mid-block, so
    # it lands in the middle of a median run with planting owed on both sides.
    #
    # The rule lives in _common because step 05 plants what this builds, and it
    # has to plant into the same runs rather than into its own idea of them.
    for (ra, rb) in median_runs(BY, PLAZA, PLAZA_HALF):
        for side in (-1, 1):
            mc = side * (MEDIAN[0] + MEDIAN[1]) / 2
            mw = MEDIAN[1] - MEDIAN[0]
            m.prism([(NINE + mc - mw / 2, ra), (NINE + mc + mw / 2, ra),
                     (NINE + mc + mw / 2, rb), (NINE + mc - mw / 2, rb)],
                    0.0, MEDIAN_LIFT, kerb)
            g.quad(NINE + mc, (ra + rb) / 2, mw - 1.0, rb - ra,
                   MEDIAN_LIFT + 0.02, grass)

    p0, p1 = PLAZA - PLAZA_HALF - 2.0, PLAZA + PLAZA_HALF + 2.0
    for (cy, size) in BY:
        # Shelters the length of the boulevard: up to two per block, never
        # over an intersection. The real corridor is 3 km with 17 stations,
        # which is 175-185 m apart, or one every three blocks at our size, and
        # this is deliberately not that. It is a shorter shelter repeated along
        # the median - what the avenue looks like rather than what the
        # timetable says. Recorded as a departure, not as the sourced number.
        room = size - STATION_MARGIN * 2
        if room >= STATION_LEN * 2 + STATION_GAP:
            centres = [cy - (STATION_LEN + STATION_GAP) / 2,
                       cy + (STATION_LEN + STATION_GAP) / 2]
        elif room >= STATION_LEN:
            centres = [cy]
        else:
            centres = []
        for sc in centres:
            if p0 - STATION_LEN < sc < p1 + STATION_LEN:
                continue                    # the plaza is standing there
            sl = STATION_LEN
            m.prism([(NINE - PLATFORM, sc - sl / 2), (NINE + PLATFORM, sc - sl / 2),
                     (NINE + PLATFORM, sc + sl / 2), (NINE - PLATFORM, sc + sl / 2)],
                    0.04, PLATFORM_LIFT, plat)
            # the canopy: a flat roof on four posts, which is the whole form at
            # this size. The real ones are glazed boxes and none of that reads.
            for t in (-1, 1):
                for s2 in (-1, 1):
                    m.box((NINE + s2 * (PLATFORM - 0.5),
                           sc + t * (sl / 2 - 1.5), PLATFORM_LIFT + 1.5),
                          (0.28, 0.28, 3.0), mat("Concrete Cool"))
            # +1.2 of oversail, not +3.0. At 3 m the roof is 13 m wide over a
            # 7 m platform, so from this camera it is a slab lying across the
            # avenue with no visible platform under it at all - which reads as
            # a lid, not as a station. At 1.2 the deck shows on both sides.
            m.box((NINE, sc, PLATFORM_LIFT + 3.1),
                  (PLATFORM * 2 + 1.2, sl, 0.35), mat("Station Roof"))
            # one white line down the roof, and it is load-bearing: the roof is
            # dark now, and from overhead a dark rectangle on dark asphalt is a
            # hole in the avenue. The line is what makes the shelter read.
            m.box((NINE, sc, PLATFORM_LIFT + 3.30),
                  (1.1, sl - 1.4, 0.06), mat("Station Line"))
            # the crossing that reaches it. A station nobody can walk to reads
            # as an object dropped in the road, and this is two rows of quads.
            for side in (-1, 1):
                for k in range(5):
                    g.quad(NINE + side * (PLATFORM + 1.2 + k * 1.3), sc,
                           0.7, 3.4, 0.05, mat("Marking"))
            # one totem, at the near end. Two of them on a 22 m shelter, twice
            # per block, is a picket fence down the middle of the avenue.
            m.box((NINE, sc - sl / 2 - 0.9, PLATFORM_LIFT + 2.2),
                  (1.6, 0.35, 4.4), mat("Station Roof"))
            stations += 1

    # Plaza de la Republica. The medians and the platform give way to one paved
    # island wide enough to stand a monument on, which is what the real plaza
    # is: the avenue opens around it rather than the plaza sitting beside it.
    #
    # An oval. It is the only curve in this city - the grid is strictly
    # rectangular and even the ochavas are straight cuts - so it costs nothing
    # to build and the eye goes to it before anything else in the frame. Built
    # as a rectangle first, and a rectangle of exactly these dimensions reads as
    # a widening of the road rather than as a place in it.
    m.prism(ellipse(NINE, PLAZA, PLAZA_WIDE, PLAZA_HALF), 0.0, 0.22, kerb)
    g.flat(ellipse(NINE, PLAZA, PLAZA_WIDE - 0.8, PLAZA_HALF - 0.8), 0.24,
           plat)
    print(f"  9 de Julio at x={NINE:.0f}, {AVE9J:.0f} m wide, "
          f"{stations} Metrobus stations")
    print(f"  Plaza de la Republica at y={PLAZA:.0f}")


def avenue_markings(m):
    """Lane lines for the two lateral carriageways, and nothing in the middle:
    the busway carries its own surface and the medians are grass.

    Each carriageway is one way, like Cerrito and Carlos Pellegrini are, so
    there is no centre line to paint - only the four dividers between five
    lanes.
    """
    mk = mat("Marking")
    for side in (-1, 1):
        c = side * (MEDIAN[1] + AVE9J / 2) / 2      # centre of the lateral
        for lane in (-5.25, -1.75, 1.75, 5.25):
            x = NINE + c + lane
            for (cy, size) in BY:
                n = max(1, int((size - 8) / 7.0))
                for k in range(n):
                    d = cy - (size - 8) / 2 + k * 7.0
                    m.quad(x, d, 0.12, 3.2, MARK_Z, mk)


# --- markings --------------------------------------------------------------
def build_markings(m):
    mk = mat("Marking")
    rr = rng(5150)

    def paint(cx, cy, ww, hh):
        # the two streets that used to cross the superblock are gone; their
        # centre lines and zebras would otherwise still be painted across it
        if in_super(cx, cy, -WALK):
            return
        # and a zebra crossing the 9 de Julio is 47 m long, so it runs up over
        # both planted medians and across the Metrobus platform. Real ones stop
        # at each island; here they simply stop.
        if abs(cx - NINE) > MEDIAN[0] - 1.0 and abs(cx - NINE) < AVE9J / 2:
            return
        m.quad(cx, cy, ww, hh, MARK_Z, mk)

    for axis in (0, 1):
        # A street running along X sits at a Y coordinate, so it comes out of
        # the Y table. The two tables are not interchangeable: the wide streets
        # are at different indices per axis, so reading the X table here put
        # the four-lane markings of an avenue down a 12 m local street and left
        # the real avenue painted as a local. It is off by 5 to 6 m, which is
        # under a lane width, which is why nothing looked wrong - 46 vehicles
        # were driving 1.75 m up on the pavement and every street still read as
        # a street.
        streets, widths = (SY, WY) if axis == 0 else (SX, WX)
        blocks = BX if axis == 0 else BY
        for k, (s, w) in enumerate(zip(streets, widths)):
            if axis == 1 and k == NINE_X:
                continue                   # the avenue paints its own lanes
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
    open_city(needs_collections=("KIT",),
              hint="run 02_kit.py then 02b_porteno_kit.py first")
    if "GROUND_placeholder" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["GROUND_placeholder"],
                                do_unlink=True)
    # The colours of the site used to be set here twice - once with pbrmat(),
    # which only ever CREATES, and then again with a local retint() because of
    # it. Both tables now live in _palette.py and open_city() has already
    # applied them, so the notes that justified the values live there too:
    # the road at 0.18 luminance and warm, the bus shelters dark so they sit
    # into the asphalt instead of pulling the eye off the monument, the busway
    # a warm cast rather than a painted red lane.

    site = purge("SITE")

    r = rng(4711)
    m = Mesh()
    mm = Mesh()
    build_sheet(m)
    lots = build_blocks(m, r)
    build_avenue(m, mm)
    # after build_blocks, always: the rim lots are appended to `lots` behind the
    # superblock and every step downstream relies on them coming last
    build_rim(m, mm, lots)
    m.build("site", site)

    build_markings(mm)
    avenue_markings(mm)
    build_parking(mm, lots)
    mm.build("markings", site)

    (LOTS).write_text(json.dumps({
        "lots": [{"key": [str(i), str(j)], "x": cx, "y": cy, "size": size,
                  "lift": lift, "kind": kind}
                 for (i, j), (cx, cy, size, lift, kind) in lots.items()],
        "streets_x": SX, "streets_y": SY, "widths_x": WX, "widths_y": WY,
        "blocks_x": BX, "blocks_y": BY, "walk": WALK,
        "superblock": list(super_bounds()),
        # everything downstream needs the section, not just the centre line:
        # step 05 plants the medians and drives buses down the busway, and
        # step 06b stands the Obelisco on the plaza
        "avenue9j": {"x": NINE, "width": AVE9J, "index": NINE_X,
                     "median": list(MEDIAN), "busway": BUSWAY,
                     "platform": PLATFORM, "median_lift": MEDIAN_LIFT,
                     "plaza": [NINE, PLAZA, PLAZA_WIDE, PLAZA_HALF]},
    }))
    print(f"\n  lots: {len(lots)}   city {CITY:.0f} m")
    u, t = counts()
    print(f"  triangles: {u} unique / {t} total")

    with preview(CITY * 1.15, target=(0, 0, 0)):
        blib.render(str(R / "city_03_plan.png"), "EEVEE", samples=32,
                    resolution=(1500, 850),
                    exposure=bpy.context.scene.view_settings.exposure)
    save_city()


main()
