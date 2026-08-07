"""What every city script shares: the numbers, the plumbing, the step scaffold.

Three things live here, and each one is here for the same reason - two steps
needed the same fact and disagreed about it:

  THE NUMBERS   how long the shot is, how wide the hero frame is, where the
                files are, where the medians run.
  THE PLUMBING  Mesh, instancing, collections. Primitives, nothing about
                cities. Each asset is accumulated into one mesh with several
                material slots, so placing it later is one object sharing one
                mesh datablock: the cheapest instancing Blender offers.
  THE SCAFFOLD  open_city / purge / preview / save_city, which is the shape
                every step has, written once instead of sixteen times.
"""
import bpy, math, os, random, pathlib
from contextlib import contextmanager
from mathutils import Vector, Euler
from _palette import PALETTE, define, apply_palette
# Re-exported, not used here: five steps do `from _common import paint` rather
# than reaching past it into _palette, so _common is the single door onto the
# shared names. A linter cannot see that and will offer to delete it.
from _palette import paint, srgb  # noqa: F401

# --- where everything is ---------------------------------------------------
# The three JSON files travel with the .blend and are read by later steps. They
# are named here rather than spelled out in a dozen scripts, because a typo in
# one of those spellings is a step that silently reads nothing.
ROOT = pathlib.Path(__file__).resolve().parents[2]
R = ROOT / "renders"
BLEND = R / "city.blend"
LOTS = R / "city_lots.json"       # street and block tables, written by 03
SOLIDS = R / "city_solids.json"   # footprints, written by 04, 06, 06b, 08, 10
SIGNS = R / "city_signs.json"     # the sign manifest, planned by 04, built by 10
# Which WINGS make up each BUILDING, written by 04 and read by 90 and the export.
#
# This is the fact that did not exist, and almost every error in a whole batch
# of brands came out of it. `city_solids.json` publishes one rectangle per wing,
# and an L is several wings that touch: nothing could tell whether two roofs
# were two buildings or two arms of one. The browser overlay called 149 roofs
# free when 68 were, a brand landed on a building another one already had, and
# grouping by overlap does not work either, because footprints are published
# with 0.9 m of padding and two neighbours with a small setback "touch" as well.
#
# 04 knows without ambiguity — a lot cell is a building — so it writes it down.
# Same decision as `own()`: the only step that knows is the one that records it.
BUILDINGS = R / "city_buildings.json"

# --- how long the shot is --------------------------------------------------
# It lives here because steps 11 and 12 both need it and they disagreed once:
# step 12 lengthened the shot to 21 s and step 11 went on animating 10 s of
# traffic, so every car in the city stopped dead at frame 240 and stood there
# for the rest of the shot. Nothing raises an exception when the traffic
# freezes, and the standing checks read frame 1, where it has not happened yet.
# 95_check_traffic reads it too, so its samples cover the whole shot rather
# than the first half of it.
FPS = 24
FRAMES = 624                     # 26 s
# 22 s of camera move, then FOUR seconds held on the title. It was two, and two
# is not enough: the move arrives and the film stops on the same beat, which
# reads as the video ending rather than the shot landing. The city keeps moving
# through the hold - the cars do not stop when the camera does - so the extra
# time is not a freeze frame, it is the shot settling.
MOVE = 528

# --- the camera ------------------------------------------------------------
# The same three numbers were written into four files. HERO_WIDTH in particular
# was 170.0 in 07_look (as CAM_WIDTH), in 12_camera (as SCALE1) and in
# 11_animate (as a literal), which is the identical setup to the FRAMES bug
# above, waiting to happen.
#
# ELEVATION is 30.6 and it was MEASURED off the reference, not chosen: a ground
# line along +x projects to a screen line with tan(theta) = sin(e)*cot(azimuth),
# so a gradient-orientation histogram over the whole frame recovers it. The
# .blend used to carry a static camera at 38, left over from step 00, which
# meant every preview render from steps 03 to 10 was framed at an elevation the
# film never uses.
#
# AZIMUTH stays 45. The measurement says 46.2, which is inside the error, and
# 45 is structural: it is what gives every building two visible faces of equal
# weight.
AZIMUTH = 45.0
ELEVATION = 30.6
DISTANCE = 1450.0                # ortho: affects clipping only, not framing
HERO_WIDTH = 170.0               # metres of city across the final frame
ASPECT = 1080 / 1920             # the deliverable's frame, and what decides
                                 # how much of the city is above and below

# --- where the shot actually goes ------------------------------------------
# These were private to 12_camera, and that was fine while 12 was the only step
# that cared where the camera goes. It is not any more: step 04 has to know
# which buildings the shot passes over, because a company sign outside that
# strip is a sign nobody will ever see. 77 of them were planned and 18 reached
# the frame - not because the other 59 were badly made, but because they were
# spread evenly over a 700 m city that the camera crosses on one 320 m
# diagonal. Even distribution is the bug.
#
# So the path lives here now and 12 imports it, the same arrangement FRAMES and
# HERO_WIDTH already have and for the same reason: two steps need one fact.
SHOT_TARGET1 = (-51.84, 22.83)   # the approved hero framing: where it lands
SHOT_OBELISCO = (120.0, -167.0)  # what it travels past, which fixes the heading
SHOT_TRAVEL = 320.0
# THE OPENING WIDTH, and the one number here that is no longer the reference's.
# 1.479 was measured off the reference clip and shipped for a long time. It was
# opened to 1.80 for one reason: the shot has to carry company signs past the
# camera, and at 1.479 the move crosses 25 buildings, which caps the whole film
# at about that many brands however well the signs are made.
#
# 1.80 IS A CEILING, NOT A PREFERENCE, and it was found by rendering frame 1 and
# looking at it rather than by arithmetic - the first attempt at the corner
# arithmetic said the edge of the world was already showing at 1.479, and it is
# not. At 1.80 the opening frame is still full of city. At 1.90 a wedge of bare
# site opens in the top left corner, because the shot starts over the southeast
# of the city and a wider frame reaches past its corner. Past that the only way
# to open further is to build more city to the southeast.
#
# What it costs: the zoom is now x1.80 where the reference does x1.48, so the
# shot closes a little harder than the thing it was measured from. The pan is
# tied to the width by shot_pan(), so the apparent speed stays constant and the
# move still lands on exactly the approved framing - the far end of the shot is
# untouched, and only the opening is wider.
SHOT_ZOOM = 1.80                 # was 1.479, the measured start/end ratio
EASE_IN, EASE_OUT = 0.10, 0.16   # fraction of the move spent accelerating

# --- the grade -------------------------------------------------------------
# THE FIFTH SHARED NUMBER, and it is here for the same reason as the other
# four: two places disagreed about it and nothing said so. 07_look asked for
# "AgX - Punchy" on the line above the render, and blib.render's signature
# carried look="None" as a default, so the assignment was overwritten one call
# later. Every frame this project has ever shipped - the approved still and all
# 624 frames of the move - was rendered with no look at all. It measured as a
# render that was 0.24 saturated against a reference that runs 0.22 to 0.33,
# and as 5.5 % dark pixels against 10 % to 35 %.
#
# So the grade now lives in one table, is applied by open_city() on the way in
# exactly like the palette, and blib.render leaves the scene's view settings
# alone unless a caller says otherwise.
#
# Every number below was fitted against refs/video/frames, measured the same
# way on both sides: mean luma, its standard deviation (contrast), the fraction
# below 0.25 (shadow), the fraction above 0.75 (highlight), and R/B with the
# red title masked out (warmth). Where we landed, against the reference's
# spread over four frames:
#
#              mean      std      dark      bright    sat*     R/B*
#   reference  .41-.50  .20-.26  10-35 %   12-20 %   .20-.32  1.08-1.29
#   before     .526     .178      5.5 %    12.1 %    .185     0.959
#   now        .464     .248     25.2 %    15.5 %    .320     1.118
#                                                    * red title masked out
LOOK = "AgX - Very High Contrast"
# Not "AgX - Punchy", which is what the line that never ran asked for. Punchy
# buys chroma by crushing the top end: rendered for real it puts saturation at
# 0.30 but leaves 0.3 % of the frame above 0.75 where the reference has 12-20 %,
# and a city with no white in it reads as an overcast day. Very High Contrast
# gets the same chroma and keeps the highlights.
EXPOSURE = -0.82
# The reference is warm and we were not: 0.96 R/B against its 1.08-1.29, which
# is the "everything looks slightly grey" complaint in one number. Three levers
# move it and all three are used, because any one of them alone has to be
# pushed far enough to tint the whites: less blue in the ambient, a warmer sun,
# and the white balance. Blender's white balance names the temperature of the
# light it is correcting FOR, so a number ABOVE 6500 warms the image.
WHITE_BALANCE = 7800.0
# --- and the light the grade is graded from --------------------------------
# The sun-to-sky ratio is what decides whether there are shadows at all. It was
# 4.0 / 0.32, which is enough ambient to fill every shadow in the city back to
# within a stop of its lit surface: the frame had 5.5 % dark pixels where the
# reference never goes below 10 %. Raising the sun and dropping the sky trades
# fill for shape.
#
# These override _stage.py, which builds them - and _stage DESTROYS THE CITY, so
# it can never be re-run to change them. That is why they are applied here on
# every open instead.
SUN_ENERGY = 6.0                 # was 4.0
SUN_ANGLE = 2.0                  # degrees; was 3.5. Sharper shadow edges
SUN_COLOR = (1.0, 0.90, 0.78)    # was (1.0, 0.95, 0.87)
SKY_STRENGTH = 0.18              # was 0.32
SKY_SATURATION = 0.15            # was 0.35. How much blue the ambient keeps

# --- how far a detail sinks into the thing it is stuck on -------------------
# THE SIXTH SHARED NUMBER, and like the others it is here because two places
# disagreed about it silently. A mark placed exactly on the face of its panel
# gives two faces on one plane, pointing the same way, covering the same
# pixels. Cycles answers that arbitrarily but CONSISTENTLY, so every render
# this project has shipped looks fine; a rasteriser answers it per pixel from
# an interpolated depth, so in the browser the signs and the roof marks tear
# into patches that swap as the camera moves. It is a geometry fault that only
# one of the two renderers is honest about.
#
# So a detail is sunk into its backing instead of resting on it. 4 mm: deeper
# than any depth buffer this scene will ever have and far below a pixel at
# every framing the shot uses - the hero frame is 170 m across 1920 px, so one
# pixel is 89 mm.
#
# `92_check_zfight.py` is what finds these. Run it after adding any detail that
# lies flat on a surface.
SINK = 0.004

_h = (SHOT_TARGET1[0] - SHOT_OBELISCO[0], SHOT_TARGET1[1] - SHOT_OBELISCO[1])
_hn = math.hypot(*_h)
SHOT_HEADING = (_h[0] / _hn, _h[1] / _hn)
SHOT_TARGET0 = (SHOT_TARGET1[0] - SHOT_HEADING[0] * SHOT_TRAVEL,
                SHOT_TARGET1[1] - SHOT_HEADING[1] * SHOT_TRAVEL)
SHOT_WIDTH0 = HERO_WIDTH * SHOT_ZOOM


# --- the title typeface ----------------------------------------------------
# PP Monument Normal Black, and it is NOT in this repository: it is a commercial
# font and not ours to redistribute. Override with CITY_TITLE_FONT.
#
# It is one name now because it was three, each spelled out as an absolute path
# into one machine's home directory — in 08_title, in 10_signs and in an
# archived spike. On any other machine all three failed the same way, inside
# `bpy.data.fonts.load`, with a RuntimeError that names the file and not the
# reason. Two of the three are the steps that build every letter in the city.
FONT_TITLE = os.environ.get(
    "CITY_TITLE_FONT",
    str(pathlib.Path.home() / "Library/Fonts/PPMonumentNormal-Black.otf"))


def title_font():
    """Load the title typeface, or say what is missing and how to replace it."""
    p = pathlib.Path(FONT_TITLE).expanduser()
    if not p.exists():
        raise SystemExit(
            f"\n  the title typeface is not here:\n    {p}\n\n"
            "  It is PP Monument Normal Black, a commercial font this repo\n"
            "  does not ship. Point CITY_TITLE_FONT at your own copy:\n\n"
            "    CITY_TITLE_FONT=/path/to/font.otf ./bl "
            "scripts/city/08_title.py\n\n"
            "  Any heavy grotesque stands in. The title and the signs are\n"
            "  built as geometry, so the letterforms are all that changes.\n")
    # check_existing, because this is called once per LETTER. Without it every
    # glyph in the city loads its own copy of the font datablock.
    return bpy.data.fonts.load(str(p), check_existing=True)


def mat(name):
    return bpy.data.materials[name]


# --- the screen, without a camera ------------------------------------------
# The hero camera is ORTHOGRAPHIC at a fixed azimuth and elevation, which is
# what makes all of this arithmetic rather than rendering: the projection is one
# fixed linear map from world to screen, and the camera moving only translates
# the result. So "where does this end up in frame" is answerable in a step that
# has no camera in it yet, and "are these two signs too close on screen" is
# answerable once for the whole shot instead of frame by frame.
_a, _e = math.radians(AZIMUTH), math.radians(ELEVATION)
_fwd = (-math.cos(_a) * math.cos(_e), -math.sin(_a) * math.cos(_e),
        -math.sin(_e))
SCREEN_RIGHT = (-math.sin(_a), math.cos(_a), 0.0)
SCREEN_UP = (SCREEN_RIGHT[1] * _fwd[2] - SCREEN_RIGHT[2] * _fwd[1],
             SCREEN_RIGHT[2] * _fwd[0] - SCREEN_RIGHT[0] * _fwd[2],
             SCREEN_RIGHT[0] * _fwd[1] - SCREEN_RIGHT[1] * _fwd[0])


def screen_xy(x, y, z=0.0):
    """Where a world point lands on screen, in metres, relative to the target.

    Note the z: it is not decoration. A sign 30 m up projects half its height
    further up the frame than its own footprint does, so answering this in plan
    puts every rooftop sign in the wrong place by a third of a frame height.
    """
    p = (x, y, z)
    return (sum(p[i] * SCREEN_RIGHT[i] for i in range(3)),
            sum(p[i] * SCREEN_UP[i] for i in range(3)))


def _ramp(u):
    """Integral of smoothstep 3u^2-2u^3 from 0 to u. Half the area of the box."""
    return u ** 3 - u ** 4 / 2.0


def _covered(u, a, b):
    """Distance covered by time u under a trapezoidal velocity profile."""
    if u <= a:
        return a * _ramp(u / a)
    s = a * _ramp(1.0) + min(u, 1.0 - b) - a
    if u <= 1.0 - b:
        return s
    return s + b * (_ramp(1.0) - _ramp((1.0 - u) / b))


def shot_progress(t):
    """Eased time over the move. Drives the zoom, and the pan through shot_pan."""
    return _covered(t, EASE_IN, EASE_OUT) / _covered(1.0, EASE_IN, EASE_OUT)


def shot_pan(q):
    """Fraction of the travel covered by eased time q. NOT q - see 12_camera."""
    r = HERO_WIDTH / SHOT_WIDTH0
    return (1.0 - r ** q) / (1.0 - r)


def shot_at(frame):
    """(width, target) of the hero camera on this frame. The move, in one call."""
    t = min(1.0, max(0.0, (frame - 1) / (MOVE - 1)))
    q = shot_progress(t)
    p = shot_pan(q)
    return (SHOT_WIDTH0 * (HERO_WIDTH / SHOT_WIDTH0) ** q,
            (SHOT_TARGET0[0] + (SHOT_TARGET1[0] - SHOT_TARGET0[0]) * p,
             SHOT_TARGET0[1] + (SHOT_TARGET1[1] - SHOT_TARGET0[1]) * p))


def shot_cover(x, y, z=0.0, w=0.0, h=0.0, step=8):
    """How much of the shot a thing of this size spends fully inside the frame.

    Returned as (seconds, largest fraction of the frame width it ever fills).
    Both numbers are needed and they answer different questions: a sign can be
    on screen for the whole shot and be four pixels wide, and it can be huge
    for six frames and gone. A sign worth planning has to pass both.

    Sampled every `step` frames rather than solved, because the pan is eased and
    the zoom is exponential: closed form here would be a second copy of the move
    that could disagree with the first one.
    """
    secs, biggest = 0.0, 0.0
    sx, sy = screen_xy(x, y, z)
    for f in range(1, FRAMES + 1, step):
        width, (tx, ty) = shot_at(f)
        ox, oy = screen_xy(tx, ty, 0.0)
        dx, dy = sx - ox, sy - oy
        if abs(dx) < width / 2 - w / 2 and abs(dy) < width * ASPECT / 2 - h / 2:
            secs += step / FPS
            biggest = max(biggest, w / width)
    return secs, biggest


def median_runs(blocks, plaza_c, plaza_half, margin=3.0, clear=2.0,
                minimum=10.0):
    """The stretches of the 9 de Julio that actually carry a planted median.

    One run per block, reaching `margin` past the block into each crossing,
    cut in two where the plaza stands and dropped where what is left is
    shorter than `minimum` - a 9 m stub of kerb is not a median.

    It lives here because step 03 builds the medians and step 05 plants them,
    and they disagreed: 03 dropped both stubs of the plaza block for being 9 m
    long, 05 went on planting from its own block arithmetic, and four trees
    ended up standing on the bare asphalt of the avenue beside the Obelisco.
    Nothing raises an exception when a tree grows out of the road.
    """
    p0, p1 = plaza_c - plaza_half - clear, plaza_c + plaza_half + clear
    out = []
    for (c, size) in blocks:
        a, b = c - size / 2 - margin, c + size / 2 + margin
        runs = [(a, b)] if not (b > p0 and a < p1) else \
            [(a, min(b, p0)), (max(a, p1), b)]
        out.extend((ra, rb) for ra, rb in runs if rb - ra >= minimum)
    return out


# --- what is under your feet -----------------------------------------------
# The site is one mesh with a material slot per surface, so the cheapest true
# answer to "what am I standing on" is a ray dropped from above it. That is
# what 94_check_road has always done for the trees; it lives here now because
# the crowd needs to ASK the same question at placement time rather than only
# be audited on it afterwards.
#
# It is worth being explicit about what that costs. 94's whole argument is that
# a check reading the same table the placement read can only confirm the
# arithmetic - so for the trees, which are still placed off the street tables,
# the ray stays independent and 94 still means something. For the PEOPLE it
# does not: the placement now reads the geometry, so a check that reads the
# geometry is circular. That is why 91_check_crowd asks a different question
# entirely - not "is anyone on the asphalt" but "does a vehicle drive through
# anyone", which is dynamic and which no placement pass can answer.
ROAD = ("Asphalt", "Busway")
# Where a person may stand. Named rather than derived as "not ROAD", because
# "nothing under the ray at all" has to fail too: that is off the edge of the
# site, which is the same error read from the other side.
UNDERFOOT = ("Sidewalk", "Grass", "Paving", "Dirt", "Asphalt Lot")


def surfacer(site=None):
    """What is directly under (x, y), by name of material. None off the site.

    Returns a closure because the inverse matrix and the material table are
    worth computing once: this gets called about forty thousand times in a
    run of step 05.
    """
    if site is None:
        site = bpy.data.objects.get("site")
    if site is None:
        raise SystemExit("no site mesh: run 03_ground.py first")
    mats = [m.name if m else "?" for m in site.data.materials]
    inv = site.matrix_world.inverted()
    down = (inv.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()

    def under(x, y):
        ok, loc, nor, idx = site.ray_cast(inv @ Vector((x, y, 400.0)), down)
        if not ok:
            return None
        return mats[site.data.polygons[idx].material_index]

    return under


def pbrmat(name, hex_col, roughness=0.8, metallic=0.0):
    """Create or update a material. For generated artwork, not for the palette.

    The company signs need this: steps 04 and 10 invent a `Logo <brand>` per
    company and a private pair per avenue sign, and those are data rather than
    art direction.

    If the name IS in the palette, the palette wins and the disagreement is
    printed. That is the whole point: this function used to fetch an existing
    material and return it untouched, so editing a hex in a script changed
    nothing at all and raised nothing at all, and two rebuilds were lost to it.
    """
    if name in PALETTE:
        want = PALETTE[name]
        if (hex_col.lower(), roughness, metallic) != \
                (want[0].lower(), want[1], want[2]):
            _clashes.setdefault(name, (hex_col, want[0]))
        return define(name, *want)
    return define(name, hex_col, roughness, metallic)


_clashes = {}


def palette_clashes():
    """What a step asked for and the palette overruled. Printed by save_city."""
    return _clashes


def rng(seed):
    return random.Random(seed)


class Mesh:
    """Accumulates geometry, then builds it into a single object."""

    def __init__(self):
        self.v, self.f, self.fm, self.mats = [], [], [], []

    def slot(self, material):
        if material not in self.mats:
            self.mats.append(material)
        return self.mats.index(material)

    def _add(self, verts, faces, material, xform=None):
        if xform is not None:
            verts = [xform @ Vector(p) for p in verts]
        n = len(self.v)
        self.v.extend(tuple(p) for p in verts)
        s = self.slot(material)
        for face in faces:
            self.f.append(tuple(i + n for i in face))
            self.fm.append(s)

    # -- primitives ---------------------------------------------------------
    def box(self, center, size, material, xform=None):
        (cx, cy, cz), (sx, sy, sz) = center, size
        x0, x1 = cx - sx / 2, cx + sx / 2
        y0, y1 = cy - sy / 2, cy + sy / 2
        z0, z1 = cz - sz / 2, cz + sz / 2
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        # WOUND OUTWARD. Every one of these six was inside out, so every box in
        # the city had its normals pointing into itself — 100 of the 118 closed
        # meshes in the .blend, by signed volume. Cycles never said a word: it
        # shades both sides of a face, so the render is correct and always has
        # been. A rasteriser is not so forgiving. With backface culling on, the
        # face you see is the one you should not: a roof sign showed its
        # UNDERSIDE, which sits exactly on the roof deck, and the two tore at
        # each other pixel by pixel. That is the flicker.
        #
        # Check it with bmesh.calc_volume(signed=True): outward is positive.
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self._add(v, f, material, xform)

    def slab(self, cx, cy, w, h, z0, z1, material, xform=None):
        self.box((cx, cy, (z0 + z1) / 2), (w, h, z1 - z0), material, xform)

    def quad(self, cx, cy, w, h, z, material, xform=None):
        v = [(cx - w / 2, cy - h / 2, z), (cx + w / 2, cy - h / 2, z),
             (cx + w / 2, cy + h / 2, z), (cx - w / 2, cy + h / 2, z)]
        self._add(v, [(0, 1, 2, 3)], material, xform)

    def prism(self, poly, z0, z1, material, xform=None, cap=True):
        """Extrude a flat polygon [(x, y), ...] between two heights.

        The winding is normalised to counter-clockwise first: a clockwise
        polygon builds with its top cap facing down, which renders black and
        raises no error.
        """
        area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] -
                   poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))
        if area < 0:
            poly = list(reversed(poly))
        n = len(poly)
        v = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
        f = [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
        if cap:
            f += [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
        self._add(v, f, material, xform)

    def cyl(self, center, radius, height, material, segs=8, top=None,
            xform=None):
        top = radius if top is None else top
        cx, cy, cz = center
        z0, z1 = cz, cz + height
        v, f = [], []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            v.append((cx + radius * math.cos(a), cy + radius * math.sin(a), z0))
        for i in range(segs):
            a = 2 * math.pi * i / segs
            v.append((cx + top * math.cos(a), cy + top * math.sin(a), z1))
        for i in range(segs):
            j = (i + 1) % segs
            f.append((i, j, j + segs, i + segs))
        f.append(tuple(range(segs - 1, -1, -1)))
        if top > 1e-6:
            f.append(tuple(range(segs, 2 * segs)))
        self._add(v, f, material, xform)

    def cone(self, center, radius, height, material, segs=8, xform=None):
        cx, cy, cz = center
        v = [(cx + radius * math.cos(2 * math.pi * i / segs),
              cy + radius * math.sin(2 * math.pi * i / segs), cz)
             for i in range(segs)] + [(cx, cy, cz + height)]
        f = [(i, (i + 1) % segs, segs) for i in range(segs)]
        f.append(tuple(range(segs - 1, -1, -1)))
        self._add(v, f, material, xform)

    def sphere(self, center, radius, material, segs=8, rings=5, scale=(1, 1, 1),
               xform=None):
        """Faceted low-poly sphere. Left flat shaded on purpose."""
        cx, cy, cz = center
        sx, sy, sz = scale
        v, f = [], []
        for r in range(1, rings):
            phi = math.pi * r / rings
            for s in range(segs):
                th = 2 * math.pi * s / segs
                v.append((cx + radius * sx * math.sin(phi) * math.cos(th),
                          cy + radius * sy * math.sin(phi) * math.sin(th),
                          cz + radius * sz * math.cos(phi)))
        top = len(v); v.append((cx, cy, cz + radius * sz))
        bot = len(v); v.append((cx, cy, cz - radius * sz))
        # Wound outward, like box() and for the same reason: this one made
        # every tree, every jacaranda, the helicopter and the roof dishes
        # inside out. See the note in box().
        for r in range(rings - 2):
            for s in range(segs):
                a = r * segs + s
                b = r * segs + (s + 1) % segs
                f.append((a, a + segs, b + segs, b))
        for s in range(segs):
            f.append((top, s, (s + 1) % segs))
            f.append((bot, (rings - 2) * segs + (s + 1) % segs,
                      (rings - 2) * segs + s))
        self._add(v, f, material, xform)

    def flat(self, poly, z, material, xform=None):
        """One flat n-gon at a height. The block surfaces are octagons now and
        quad() only makes rectangles."""
        self._add([(x, y, z) for x, y in poly],
                  [tuple(range(len(poly)))], material, xform)

    def arc_band(self, r0, r1, a0, a1, z, material, segs=None, xform=None):
        """Flat annulus sector: road markings and kerbs that follow a curve."""
        if segs is None:
            segs = max(2, min(48, int(abs(a1 - a0) * max(r0, r1) / 2.5)))
        ang = [a0 + (a1 - a0) * i / segs for i in range(segs + 1)]
        poly = [(r1 * math.cos(a), r1 * math.sin(a)) for a in ang]
        poly += [(r0 * math.cos(a), r0 * math.sin(a)) for a in reversed(ang)]
        v = [(x, y, z) for x, y in poly]
        self._add(v, [tuple(range(len(v)))], material, xform)

    def add_mesh(self, me, material, xform=None):
        """Absorb an existing Blender mesh. Font curves arrive this way: a
        letterform is not expressible as any primitive here."""
        self._add([v.co.copy() for v in me.vertices],
                  [tuple(p.vertices) for p in me.polygons], material, xform)

    # -- output -------------------------------------------------------------
    def build(self, name, coll=None, smooth=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        for m in self.mats:
            me.materials.append(m)
        for poly, s in zip(me.polygons, self.fm):
            poly.material_index = s
        if smooth:
            for poly in me.polygons:
                poly.use_smooth = True
        me.update()
        me.validate()
        ob = bpy.data.objects.new(name, me)
        (coll or bpy.context.scene.collection).objects.link(ob)
        return ob


def collection(name, parent=None, hide=False):
    if name in bpy.data.collections:
        c = bpy.data.collections[name]
    else:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    if hide:
        c.hide_render = c.hide_viewport = True
    return c


def instance(source, coll, location=(0, 0, 0), rotation_z=0.0, scale=1.0,
             name=None):
    """A new object sharing the source mesh: no geometry is duplicated."""
    ob = bpy.data.objects.new(name or (source.name + ".i"), source.data)
    ob.location = location
    ob.rotation_euler = Euler((0, 0, rotation_z))
    ob.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    coll.objects.link(ob)
    return ob


def counts():
    """Unique vs instanced triangles: the memory budget, at a glance."""
    uniq, seen, total = 0, set(), 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.hide_render:
            continue
        t = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        total += t
        if ob.data.name not in seen:
            seen.add(ob.data.name)
            uniq += t
    return uniq, total


# ---------------------------------------------------------------------------
# The shape of a step
#
# Every step in scripts/city does the same five things: open city.blend, check
# that what it depends on is actually there, throw away its own layer, build it
# again, save. That was written out longhand in every file, which is how the
# steps drifted apart - eight different spellings of the purge loop, two of the
# repaint helper, and prerequisite checks in two files out of fourteen.
# ---------------------------------------------------------------------------

def require(collections=(), files=(), hint=""):
    """Fail loudly, early, and with the command that fixes it.

    Without this a missing prerequisite surfaces thirty lines later as a
    KeyError on bpy.data.collections["KIT"], or - much worse - as nothing at
    all: step 05 planted a whole city of trees inside the buildings the first
    time it ran before step 04, because an empty footprint table is
    indistinguishable from a city with nothing in it.
    """
    missing = [f"collection {c!r}" for c in collections
               if c not in bpy.data.collections]
    missing += [f"file {p.name}" for p in files if not p.exists()]
    if missing:
        raise SystemExit(f"\n  missing: {', '.join(missing)}\n"
                         f"  {hint or 'see CLAUDE.md for the build order'}\n")


def apply_grade(scene=None):
    """Put the view settings and the key light where the GRADE block says.

    Applied on the way in, like the palette, and for the identical reason: a
    grade set by whichever step happens to render last is a grade that differs
    between the still and the move. The sun and the sky are here rather than in
    _stage.py because _stage destroys the city and cannot be re-run.
    """
    scene = scene or bpy.context.scene
    vs = scene.view_settings
    vs.view_transform = "AgX"
    vs.look = LOOK
    vs.exposure = EXPOSURE
    vs.use_white_balance = True
    vs.white_balance_temperature = WHITE_BALANCE

    sun = bpy.data.objects.get("Sun")
    if sun and sun.type == "LIGHT":
        sun.data.energy = SUN_ENERGY
        sun.data.angle = math.radians(SUN_ANGLE)
        sun.data.color = SUN_COLOR

    world = scene.world
    if world and world.node_tree:
        for n in world.node_tree.nodes:
            if n.bl_idname == "ShaderNodeBackground":
                n.inputs["Strength"].default_value = SKY_STRENGTH
            elif n.bl_idname == "ShaderNodeHueSaturation":
                n.inputs["Saturation"].default_value = SKY_SATURATION


def open_city(needs_collections=(), needs_files=(), hint=""):
    """Open city.blend, bring the palette and the grade up to date, check
    prerequisites.

    The palette is applied on the way in rather than by whichever step happens
    to create a material first, so a colour edited in _palette.py lands in the
    very next step that runs. The grade rides along for the same reason.
    """
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    apply_palette()
    apply_grade()
    require(needs_collections, needs_files, hint)
    return bpy.context.scene


def save_city():
    if _clashes:
        print("\n  the palette overruled these (edit _palette.py instead):")
        for name, (asked, won) in sorted(_clashes.items()):
            print(f"    {name:20s} asked {asked}  ->  {won}")
    import blib
    blib.save(str(BLEND))


def purge(*names):
    """Empty and drop these collections, then make them again.

    Returns them in the order given, so a step reads:

        nat, fur, tra = purge("NATURE", "FURNITURE", "TRAFFIC")

    Deleting the objects and not just unlinking them is the point: unlinking
    leaves the meshes behind and the file grows a little every run.
    """
    out = []
    for name in names:
        if name in bpy.data.collections:
            c = bpy.data.collections[name]
            for ob in list(c.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
        out.append(collection(name))
    return out[0] if len(out) == 1 else out


def place_hero(cam, width=HERO_WIDTH, target=(0, 0, 0),
               azimuth=AZIMUTH, elevation=ELEVATION, distance=DISTANCE):
    """Put the camera on the canonical orbit, looking at `target`."""
    target = Vector(target)
    a, e = math.radians(azimuth), math.radians(elevation)
    eye = target + Vector((math.cos(a) * math.cos(e),
                           math.sin(a) * math.cos(e),
                           math.sin(e))) * distance
    cam.location = eye
    cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = width
    return cam


@contextmanager
def preview(width=HERO_WIDTH, target=None, frame=None):
    """Frame a control render, then put the camera back exactly as it was.

    Two bugs live here, both of the kind that render fine and are wrong.

    THE CAMERA WAS WHEREVER THE LAST STEP LEFT IT. Twelve steps set
    ortho_scale before their preview render and then saved the .blend; one of
    them restored it. So the framing stored in the file was a side effect of
    which step you happened to run last, and the final still only came out
    right because 07 sets it again and the numbers happened to agree.

    THE PREVIEW IGNORED THE ANIMATION, OR THE ANIMATION IGNORED THE PREVIEW.
    Once step 12 has keyframed the camera, setting ortho_scale does nothing at
    render time - the fcurve wins - so re-running an earlier step after 12 gave
    you a "close-up" rendered at whatever the move was doing on that frame.
    Muting the action for the duration is what makes a preview mean the same
    thing before and after the move exists.
    """
    scene = bpy.context.scene
    cam = bpy.data.objects["HeroCam"]
    keep = (cam.location.copy(), cam.rotation_euler.copy(),
            cam.data.ortho_scale, scene.frame_current)
    for holder in (cam, cam.data):
        for fc in blib_fcurves(holder):
            fc.mute = True
    if frame is not None:
        scene.frame_set(frame)
    if target is not None:
        place_hero(cam, width, target)
    else:
        cam.data.ortho_scale = width
    try:
        yield cam
    finally:
        for holder in (cam, cam.data):
            for fc in blib_fcurves(holder):
                fc.mute = False
        cam.location, cam.rotation_euler, cam.data.ortho_scale = keep[:3]
        scene.frame_set(keep[3])


def blib_fcurves(ob):
    import blib
    return blib.fcurves(ob)


# --- can the camera see this wall? -----------------------------------------
# A brand logo on a facade has three ways of not existing, and all three cost a
# render each if they are chosen by eye:
#
#   1. the wall looks into the other arm of its own L,
#   2. the wall looks into the neighbour, a metre away,
#   3. the wall faces a courtyard rather than the street.
#
# In one batch of six brands all three happened. The "longest" face was being
# picked, and on these buildings that is almost always the one inside the
# complex. This answers it by measuring, and it lives here because two callers
# ask: 90_brand_sites to choose, and 93_check_signs to report when what was
# chosen ended up hidden.
#
# The camera is orthographic and fixed, so "towards the camera" is a single
# vector for the whole city. Asking by distance is not enough: a building 12 m
# away and 20 m tall hides a wall with 6 m of clear air in front of it.
def view_vector():
    """The unit vector pointing at the camera from anywhere in the city."""
    az, el = math.radians(AZIMUTH), math.radians(ELEVATION)
    return (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
            math.sin(el))


# The two faces this camera sees. 0 is +X and 1 is +Y; screen_xy puts +X on the
# left of the frame, which is what 10_signs calls "left".
FACES = ((0, "left"), (1, "right"))


def wall_seen(sol, box, axis, z, samples=21, far=90.0, step=2.0):
    """What fraction of `box`'s +axis face reaches the camera, at height z.

    `sol` is a Solids carrying the footprints; `box` is one of its rectangles.
    It casts a ray towards the camera from points spread along the face and
    counts the ones that hit NO other footprint.

    It is measured at one specific height rather than "in general" on purpose:
    the same wall can be hidden at 15 m and clear at 19 because the neighbour
    stops at 16.9.
    """
    cx, cy, w, d = box[0], box[1], box[2], box[3]
    run = d if axis == 0 else w
    half = (w if axis == 0 else d) / 2
    vx, vy, vz = view_vector()
    seen = 0
    for i in range(samples):
        t = -run / 2 + run * i / (samples - 1)
        px, py = ((cx + half + 0.3, cy + t) if axis == 0
                  else (cx + t, cy + half + 0.3))
        k = step
        while k < far:
            hit = sol.hit(px + vx * k, py + vy * k, z + vz * k, 0.0,
                          tags=("buildings", "porteno"))
            if hit is not None and hit is not box:
                break
            k += step
        else:
            seen += 1
    return seen / samples


def wall_to_street(site, box, axis):
    """Metres from the +axis face to the edge of the nearest street.

    The other half of the question: a wall can be perfectly visible to the
    camera and still face an internal courtyard. A company logo goes over the
    pavement. Three brands out of six ended up hanging 17–32 m from the street.
    """
    edge = box[0] + box[2] / 2 if axis == 0 else box[1] + box[3] / 2
    lines = zip(site["streets_x"], site["widths_x"]) if axis == 0 else \
        zip(site["streets_y"], site["widths_y"])
    return min(abs(s - edge) - w / 2 for s, w in lines)


def brand_addresses(sites, signs, hero):
    """Which brand occupies each building. The full answer, not the record's.

    A sign points at the roof it was planned on, and its wordmark can end up
    hung off ANOTHER building: `facade_at` and `roof_at` in HERO move the art,
    and Basement, Ualá and Etermax are all like that. Asking the record leaves
    those three addresses marked empty, and that is where two extra brands
    landed on an already-taken address in a single batch — one caught by looking
    at a render, the other because a brand was missing from the browser map.

    It lives here because two callers ask it and need the same answer: 93 to
    report an address carrying two brands, and 90 to avoid offering a building
    that is already taken. Two copies of this question is how one of them ends
    up falling short.

    Returns {(bx, by): {brand, ...}} over the cells in city_buildings.json.
    """
    def lands_on(x, y):
        for s in sites:
            for wx, wy, w, d in s["wings"]:
                if abs(x - wx) <= w / 2 + 2.0 and abs(y - wy) <= d / 2 + 2.0:
                    return tuple(s["at"])
        return None

    # THE ADDRESS IS WHERE THE ART IS, not where the sign was planned.
    # `built` is written by 10_signs measuring the mesh, so it already carries
    # the logo moved to the neighbour's wall without having to re-read HERO.
    # When it is missing — an old manifest — it falls back to the plan and to
    # the destination declared in HERO, which is the approximate answer.
    claims = []
    for rec in signs:
        if rec.get("drop"):
            continue
        b = rec.get("built")
        if b:
            claims.append((b[0], b[1], rec["text"]))
            continue
        claims += [(rec["owner"][0], rec["owner"][1], rec["text"]),
                   (rec["x"], rec["y"], rec["text"])]
        h = hero.get(rec["text"]) or {}
        for k in ("facade_at", "roof_at"):
            if h.get(k):
                claims.append((h[k][0], h[k][1], rec["text"]))
    out = {}
    for x, y, who in claims:
        at = lands_on(x, y)
        if at is not None:
            out.setdefault(at, set()).add(who)
    return out
