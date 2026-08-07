"""Step 10 — company signs, ready for logos.

The reference is a parade of real logos. We are reproducing the city, not the
branding, so these carry invented companies; what is being reproduced is how a
logo is physically mounted on a building, which is the part that has to be
built now if it is ever going to be swapped for artwork later.

Three mountings, all read off the reference frames:

  parapet   individual extruded letters mounted on the facade wall, hanging
            just under the roof edge and projecting out from it. This is the
            Google one. Note where they are: NOT standing on top of the
            parapet, which is how this was built first. In the reference the
            letters sit on the wall with the roof-edge band running above them
            and they cast their shadow down the facade, which is where all
            their contrast comes from - pale wall behind saturated letter.
            Standing them on the parapet puts them against the sky and the
            roof, and they lose it.
  roofmark  a flat panel lying on the deck with a mark on it, costing no
            height at all. The orange square with the white B.
  mast      a large disc on a pole, standing clear of everything and turned to
            face the camera. One or two in frame, no more: it is a hero.

And two more that belong to 9 de Julio and to nowhere else in this city. The
real avenue is an advertising corridor and the two formats that make it one are
the rooftop billboard and the painted medianera:

  billboard a large panel standing on a visible steel frame on a roof, floating
            about 4 m over the deck on legs, with a catwalk under it. Turned to
            face the camera rather than to face the avenue, which is what the
            real ones do too: they are aimed at the traffic, and here the
            traffic is the lens.
  medianera a mural on a blind party wall, hung from just under the parapet.
            Its size is not a range in this file: art. 5.4.b of Ley 2936 lets
            it cover half the wall it is on and caps nothing in square metres,
            so step 04 measures it against that wall and these come out from
            13 m to nearly 40 m wide. One flat panel and one mark, no letters:
            the artwork is a texture that goes on later.

The two avenue formats get their own material per sign rather than one shared
per brand, because dropping a real mural onto one wall must not repaint every
other wall carrying the same invented company.

Step 04 chooses where they go and reserves the space, and writes the plan to
city_signs.json. This step only builds. That split is not tidiness: the roof
units are placed in step 04, and until it knew about the signs it put nine of
them inside one.

Each sign is its own object with its own material slots, so dropping real
artwork on one later is a material swap on a named object, not a rebuild.

    ./bl scripts/city/05_life.py      # always before this
    ./bl scripts/city/10_signs.py
"""
import sys, pathlib, math, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Matrix, Vector
from _common import (Mesh, mat, pbrmat, counts, R, SIGNS,
                     SOLIDS, SINK, open_city, save_city, purge, preview,
                     screen_xy, title_font)
from _solids import Solids
from _brands import HERO, SIZE

CAP = 4.2                 # letter height on a parapet, metres
DEPTH = 0.9               # how far a letter is extruded
PROUD = 1.05              # how far it stands off the wall. 0.45 was the real
                          # projection of a letter and it was wrong here: this
                          # city's own facades carry a shade frame that already
                          # stands 0.45 m proud, so the letters were cutting
                          # into it. All twenty parapet signs failed the
                          # overlap check the first time they were tested
                          # against a building at all.
DROP = 0.7                # how far under the roof edge the letter tops sit
LOGO_CAP = CAP * 1.45     # the box a real logo gets on a parapet. See build()
MAST = 0.55               # mast height as a fraction of the disc diameter


UNIQUE = ("billboard", "medianera")   # one material each, not one per brand


def facemat(rec):
    # the avenue formats are the ones real artwork is going onto, and there is
    # no point in reserving a wall for a mural if repainting it repaints four
    # other walls that happen to carry the same invented company
    tag = f"{rec['name']} {rec['text']}" if rec["kind"] in UNIQUE \
        else rec["text"]
    return (pbrmat(f"Logo {tag}", rec["face"], 0.42),
            pbrmat(f"Ink {tag}", rec["ink"], 0.42))


def letters(m, rec, face, x):
    """The word as real letterforms, extruded, standing on the parapet.

    Blender's font curve is the whole word in one object, which would make one
    solid the length of the sign. The reference's letters are separate solids
    with daylight between them, so each character is built on its own and
    placed by hand off the measured advance of the whole word.
    """
    body = rec["text"]
    size = CAP / cap_of(body)
    dg = bpy.context.evaluated_depsgraph_get()
    # the run of the whole word, so the letters can be centred as a group
    total, pieces = 0.0, []
    for ch in body:
        cu = bpy.data.curves.new(ch, type="FONT")
        cu.body = ch
        cu.font = title_font()
        cu.size = size
        cu.extrude = DEPTH / 2
        cu.align_x = "LEFT"
        cu.align_y = "BOTTOM_BASELINE"   # "BASELINE" is not one of the five
        ob = bpy.data.objects.new(ch, cu)
        bpy.context.scene.collection.objects.link(ob)
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        xs = [v.co.x for v in me.vertices] or [0.0]
        pieces.append((me, min(xs), max(xs)))
        total += max(xs) - min(xs)
        bpy.data.objects.remove(ob, do_unlink=True)
    gap = size * 0.10
    total += gap * (len(body) - 1)
    # scale the whole word down if it overruns the reserved width, rather than
    # letting it run off the end of the building
    k = min(1.0, rec["w"] / total) if total else 1.0
    cursor = -total * k / 2
    for me, lo, hi in pieces:
        wd = (hi - lo) * k
        for v in me.vertices:
            # the glyph is built in XY and stood up: its own Y becomes height.
            #
            # NOTE THE MINUS. Standing it up by swapping y and z is a
            # REFLECTION, not a rotation, and a reflection turns every face in
            # the glyph inside out: all 17 parapets still built from letters
            # had negative signed volume, which is the exact fault the boxes in
            # _common were fixed for and this is where it survived. Cycles
            # shades both sides so no render ever showed it; a rasteriser with
            # backface culling draws the far face of every letter. Negating z
            # makes it a rotation about X, same geometry, winding intact.
            v.co.x = (v.co.x - lo) * k + cursor
            v.co.y, v.co.z = -v.co.z, v.co.y * k
        m.add_mesh(me, face, x)
        cursor += wd + gap * k
        bpy.data.meshes.remove(me)


_cap = {}


def cap_of(body):
    """Height of this word at size 1, measured. Cap height is not the font
    size and the difference is not a constant across weights."""
    if body not in _cap:
        cu = bpy.data.curves.new(body, type="FONT")
        cu.body = body
        cu.font = title_font()
        cu.size = 1.0
        cu.extrude = 0.01
        ob = bpy.data.objects.new(body, cu)
        bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ys = [v.co.y for v in me.vertices] or [0.0, 1.0]
        _cap[body] = max(max(ys) - min(ys), 1e-6)
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)
    return _cap[body]


_logos = {}


def logo_pieces(fname):
    """The real logo, imported from its SVG and extruded into actual geometry.

    Returns [(mesh, hex)], normalised to HEIGHT 1 AND THICKNESS 1, centred on
    its own bounding box, lying in XY and extruded in +Z — the same convention
    mark() draws in, so a logo drops into every mounting the geometric marks
    already had. The caller scales height and thickness separately, because
    they are not the same kind of number: how tall a sign is depends on the
    building, and how deep it is is a fact about built letters. Tying the two
    together drove AUTH0's shield — 6 m tall because it is nearly square —
    1.3 m into its own facade, and 99_check_overlap caught it.

    A logo is not a texture here. Blender reads the SVG as curves and extrudes
    them, so the letterforms get the same relief the parapet letters have and
    the same shadow down the facade, which is where those get their contrast.
    That also means no UVs, no image nodes, and nothing for the glTF exporter
    to lose on the way to the browser.

    The colour comes from the file when the file has one. A logo that arrives
    as a single flat colour (or none at all, which is what `currentColor` in a
    website's inline SVG turns into) gets the sign's own ink instead.
    """
    if fname in _logos:
        return _logos[fname]
    path = ROOT / "assets" / "logos" / fname
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=str(path))
    news = [o for o in bpy.data.objects if o not in before and o.type == "CURVE"]
    pieces = []
    if news:
        pts = [o.matrix_world @ Vector(c) for o in news for c in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), 0))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), 0))
        w, h = hi.x - lo.x, hi.y - lo.y
        if w > 0 and h > 0:
            k = 1.0 / h
            ctr = (lo + hi) / 2
            for o in news:
                o.data.dimensions = "2D"
                o.data.fill_mode = "BOTH"
                o.data.extrude = 0.5 / k       # thickness 1 once scaled
                col = None
                if o.data.materials and o.data.materials[0]:
                    c = o.data.materials[0].diffuse_color
                    col = "#%02x%02x%02x" % tuple(
                        int(min(max(v, 0), 1) ** (1 / 2.2) * 255) for v in c[:3])
                dg = bpy.context.evaluated_depsgraph_get()   # after the extrude
                me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
                me.transform(Matrix.Scale(k, 4) @ Matrix.Translation(-ctr) @
                             o.matrix_world)
                pieces.append((me, col))
            pieces = [(me, col, w / h) for me, col in pieces]
    for o in news:
        bpy.data.objects.remove(o, do_unlink=True)
    # the importer leaves a material per fill behind on every call
    for mt in list(bpy.data.materials):   # only the ones with nothing on them
        if mt.name.startswith("SVGMat") and not mt.users:
            bpy.data.materials.remove(mt)
    _logos[fname] = pieces
    return pieces


def logo(m, fname, w_max, h_max, ink, x, depth=0.20, anchor="center",
         rest=True, force_ink=False, only=None, only_x=None, lift=None,
         oneline=False, stack=False):
    """Place a logo inside a w_max x h_max box, as large as it fits.

    `rest` is the one that is easy to get wrong. A curve extrudes SYMMETRICALLY
    about its own plane, so a logo placed the way mark() places a mark is half
    its thickness INSIDE whatever it lies on — mark() runs from -SINK upward,
    a curve runs from -depth/2 to +depth/2. Every flat logo in the city was
    sunk into its panel that way and only one of them was caught, because a
    roof panel is the only mounting with a building right behind it: ALEPH's
    846 triangle pairs against its own tower in 99_check_overlap. So the back
    face is put ON the surface, at -SINK, and the logo stands out of it.

    `rest=False` keeps the curve centred on the plane, which is what a parapet
    wants: those hang PROUD of the facade with air behind them, exactly like
    the extruded letters they replace.

    `anchor="top"` hangs it from the top of the box instead of centring it,
    which is what a parapet needs: the wordmark's cap line sits DROP under the
    roof edge whatever the logo's proportions turn out to be.
    """
    pieces = logo_pieces(fname)
    if not pieces:
        return 0.0
    ar = pieces[0][2]
    fit = Matrix.Identity(4)
    if only or only_x:
        # HALF A LOGO, taken out of the file rather than by keeping a second
        # pair of SVGs in sync with it.
        #
        # BY POSITION, not by colour, and Naranja X is why: its mark is a
        # bicolour X — one orange stroke and two violet ones — so splitting on
        # colour tore the X in half and sent its orange stroke to the roof with
        # the word. Where a piece sits is the thing that actually separates a
        # symbol from a wordmark; what colour it is happens to correlate.
        #
        # The subset has to be re-normalised. logo_pieces centres and scales
        # against the WHOLE artwork, so the X on its own would arrive as a
        # small shape sitting off to the right of an empty box.
        if only:
            pieces = [p for p in pieces if near_colour(p[1], only)]
        if only_x:
            span, keep = ar, []
            for me, col, a in pieces:
                xs = [v.co.x for v in me.vertices]
                mid = ((min(xs) + max(xs)) / 2 + span / 2) / span
                if only_x[0] <= mid <= only_x[1]:
                    keep.append((me, col, a))
            pieces = keep
        if not pieces:
            return 0.0
        xs, ys = [], []
        for me, _c, _a in pieces:
            for v in me.vertices:
                xs.append(v.co.x); ys.append(v.co.y)
        lo, hi = Vector((min(xs), min(ys), 0)), Vector((max(xs), max(ys), 0))
        sub_w, sub_h = hi.x - lo.x, hi.y - lo.y
        if sub_h <= 0 or sub_w <= 0:
            return 0.0
        ar = sub_w / sub_h
        # IN X AND Y ONLY. A uniform scale here also stretches the extrusion,
        # and `rest` has already been told how thick the logo is: the symbol
        # of POMELO is 58% of the whole artwork's height, so re-normalising it
        # uniformly made it 1/0.58 times deeper and pushed 16 cm of it out the
        # BACK, through the roof it was supposed to be resting on. Depth is
        # set once, in metres, by the caller — nothing downstream may touch it.
        fit = Matrix.Diagonal(Vector((1.0 / sub_h, 1.0 / sub_h, 1.0, 1.0))) @ \
            Matrix.Translation(-(lo + hi) / 2)
    shift = {}
    if oneline:
        # TWO LINES INTO ONE. "mercado libre" is drawn stacked, and stacked on
        # a long facade it comes out half the size it could: the wall has width
        # to spare and it is the height that binds. Split on Y, send the lower
        # line to the right of the upper one, line up their baselines.
        mids = [(min(v.co.y for v in me.vertices) +
                 max(v.co.y for v in me.vertices)) / 2 for me, _c, _a in pieces]
        cut = (min(mids) + max(mids)) / 2
        top = [i for i, my in enumerate(mids) if my >= cut]
        bot = [i for i, my in enumerate(mids) if my < cut]
        if top and bot:
            def bbox(idx):
                xs_ = [v.co.x for i in idx for v in pieces[i][0].vertices]
                ys_ = [v.co.y for i in idx for v in pieces[i][0].vertices]
                return min(xs_), max(xs_), min(ys_), max(ys_)
            tx0, tx1, ty0, _ = bbox(top)
            bx0, _, by0, _ = bbox(bot)
            dx, dy = tx1 + (tx1 - tx0) * 0.06 - bx0, ty0 - by0
            for i in bot:
                shift[i] = (dx, dy)
            xs2, ys2 = [], []
            for i, (me, _c, _a) in enumerate(pieces):
                ox, oy = shift.get(i, (0.0, 0.0))
                for v in me.vertices:
                    xs2.append(v.co.x + ox)
                    ys2.append(v.co.y + oy)
            sh = max(ys2) - min(ys2)
            ar = (max(xs2) - min(xs2)) / sh
            fit = Matrix.Diagonal(Vector((1.0 / sh, 1.0 / sh, 1.0, 1.0))) @ \
                Matrix.Translation(Vector((-(min(xs2) + max(xs2)) / 2,
                                           -(min(ys2) + max(ys2)) / 2, 0.0)))
    h = min(h_max, w_max / ar)
    # SINK pulls the back face 4 mm UNDER the plane, which is right when the
    # plane is a panel this logo is part of — the two never fight for pixels.
    # It is wrong when the plane is the roof of a building: 4 mm under a slab
    # is 4 mm INSIDE it, and 99_check_overlap counted 1464 triangle pairs of
    # POMELO's symbol buried in its own deck. `lift` puts it just above
    # instead; a centimetre is invisible across 250 m and touches nothing.
    off = (-SINK if lift is None else lift) + (depth / 2 if rest else 0.0)
    # height and thickness scale separately: `depth` is metres of relief, not
    # a proportion of the logo. A non-uniform scale with all three factors
    # positive keeps the winding, which a mirror would not.
    place = x @ Matrix.Translation(Vector((0, 0, off))) @ \
        Matrix.Diagonal(Vector((h, h, depth, 1.0)))
    if anchor == "top":
        place = place @ Matrix.Translation(Vector((0, -0.5, 0)))
    place = place @ fit
    # force_ink: the table wins over the file. A path with no `fill` does not
    # import as "no colour" — Blender gives it a default BLACK material — so a
    # logo stripped of its fill silently ignores the ink it was given and comes
    # out black. Takenos shipped that way for one render. When a brand states
    # its colour, that is the colour.
    for i, (me, col, _a) in enumerate(pieces):
        c = ink if force_ink else (col or ink)
        dx, dy = shift.get(i, (0.0, 0.0))
        # ALWAYS STEPPED, and by a fixed total rather than per piece. A logo
        # drawn in layers — a disc with a mark on it, Despegar's two-tone D —
        # has every layer on the SAME plane in the file, because a renderer
        # paints them in order and the last one wins. Extruded, they share one
        # slab and tear into stripes wherever they overlap.
        #
        # A FIXED STEP, CAPPED. Spreading one total fan across every piece put
        # Despegar's two-tone D — pieces 0 and 1 of ten — 2.8% of the relief
        # apart, which 92_check_zfight still called a shared plane over 5.5 m2.
        # Consecutive pieces are the ones that overlap, so they need a real gap
        # between them; the cap keeps a thirteen-letter wordmark from turning
        # into a staircase.
        # KNOWN LIMIT: stepping fixes layers that merely sit on top of each
        # other, and does nothing for two shapes whose OUTLINES coincide.
        # Despegar's D is two halves cut along the same curve, so their side
        # walls share a vertical plane no matter how far apart in depth they
        # are — pushing them further apart only puts MORE of that wall face to
        # face (5 m2 at one step, 33 m2 at four). Fixing it means editing the
        # artwork so the halves do not share an edge, not moving them.
        dz = (i / max(1, len(pieces) - 1)) * 0.25
        put = place @ Matrix.Translation(Vector((dx, dy, dz)))
        m.add_mesh(me, pbrmat(f"Logo {fname} {c}", c, 0.38), put)
    return h


def near_colour(col, wanted):
    """Same colour, allowing for the trip through Blender's gamma.

    A hex compared as a string does not survive it: #f75000 in the file comes
    back as #f65100 after linear-to-sRGB and rounding. Close enough is the only
    workable test.
    """
    if not col:
        return False
    a = tuple(int(col[i:i + 2], 16) for i in (1, 3, 5))
    for w in wanted:
        b = tuple(int(w[i:i + 2], 16) for i in (1, 3, 5))
        if sum((x - y) ** 2 for x, y in zip(a, b)) < 900:      # ~30 per channel
            return True
    return False


def deck_z(x, y, default):
    """Height of the actual roof slab under (x, y), asked of the geometry.

    NOT the footprint's z1, which is what this used first. A published solid is
    the box the building occupies, so its top is the top of the PARAPET — on
    the AUTH0 tower that is 20.65 while the deck you would stand on is 19.82.
    A logo laid at z1 hangs 83 cm in the air with its own shadow underneath,
    which is visible from anywhere and raises nothing.

    The same distinction bit the trees and the crowd: the table and the mesh
    disagree, and the mesh is the one that gets rendered. See _common.surfacer,
    which asks the site the same way for the same reason.
    """
    ob = bpy.data.objects.get("buildings")
    if ob is None:
        return default
    inv = ob.matrix_world.inverted()
    down = (inv.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    ok, loc, _nor, _idx = ob.ray_cast(inv @ Vector((x, y, 400.0)), down)
    return (ob.matrix_world @ loc).z if ok else default


def deck_top(cx, cy, w, d, rot, default):
    """The HIGHEST point of the roof under a rectangle, not the height at its
    centre.

    A roof is not one plane. This building has a step in it — 12.06 on one side
    and 12.22 on the other — so a logo laid at the height of its own centre had
    732 vertices sixteen centimetres inside the slab at the far end. Asking one
    point is the same mistake as reading z1 off the footprint, one level down.

    Sampled on an 11x11 grid. A 5x5 was not enough: its columns fell either
    side of the step and every one of them answered 12.06, so the logo was
    placed 16 cm under the higher half and the check still failed. 121 rays
    cost nothing here and the grid only has to be finer than the smallest
    change in roof height, not accurate.
    """
    best = default
    c, s_ = math.cos(rot), math.sin(rot)
    N = 11
    for i in range(N):
        for j in range(N):
            lx = (i / (N - 1) - 0.5) * w
            ly = (j / (N - 1) - 0.5) * d
            best = max(best, deck_z(cx + lx * c - ly * s_,
                                    cy + lx * s_ + ly * c, default))
    return best


def hero_word(m, rec, hero, site, key="word"):
    """The name, lying on a roof. The roof is not always this sign's own.

    `roof_at` names another building's deck: Lemon's symbol goes on the mast
    and its wordmark on the white roof one lot over, because that is where
    there is room for it and because somebody looked at the frame and said so.
    Without it the sign's own owner is used, which is the ordinary case.
    """
    ox, oy = hero.get("roof_at") or rec["owner"]
    box = site.hit(ox, oy, tags=("buildings", "porteno"))
    if box is None:
        return
    frac = hero.get(f"{key}_roof_frac", hero.get("roof_frac", 0.7))
    bx, by, bw, bd, brot, _bz0, bz1 = box[:7]
    # ON the deck, not above it. logo() rests its BACK FACE on the plane it is
    # given, sunk by SINK, so the plane is the roof itself: any clearance here
    # is a gap you can see under the letters, with their own shadow in it. And
    # the deck is asked of the mesh, never taken from the footprint — see
    # deck_z, where that cost 83 cm of daylight under AUTH0.
    # ALONG THE BUILDING, not along world X. A wordmark is five or six times
    # wider than it is tall and these roofs are long and narrow: laid across a
    # 10 m frontage this one came out 1.3 m tall on a deck with 39 m of run
    # going spare. So the long side of the roof is the reading direction, and
    # the logo is measured against that.
    turn = 0.0 if bw >= bd else math.pi / 2
    along, across = (bw, bd) if bw >= bd else (bd, bw)
    # `roof_shift` moves the piece around the roof, in fractions of the building
    # and along WORLD axes, which is how a plan is read: "towards the entrance"
    # is a direction in the city, not in the local frame of a rotated footprint.
    sx, sy = hero.get(f"{key}_roof_shift", hero.get("roof_shift", (0.0, 0.0)))
    px, py = bx + sx * bw, by + sy * bd
    # THE DECK IS MEASURED WHERE THE PIECE LANDS, not at the centre of the
    # footprint. A shifted logo asked the middle of the building how high the
    # roof was and then went and lay down eleven metres away, where a taller
    # body of the same building put the slab above it: 1464 triangle pairs of
    # POMELO's symbol buried in its own roof, and the check found it because
    # the logo was inside a building, not on it.
    top = deck_top(px, py, along * frac, across * frac, brot + turn, 0.0) \
        or deck_z(px, py, bz1)
    flat = Matrix.Translation(Vector((px - rec["x"], py - rec["y"],
                                      top - rec["z"])))
    flat = flat @ Matrix.Rotation(brot + turn, 4, "Z")
    flat = flat @ readable(rec, rot=brot + turn)
    # a quarter turn by hand, for when the orientation that fits the roof best
    # is not the one the brand wants. In degrees and anticlockwise seen from
    # above, which is how it gets asked for while looking at the plan.
    spin = hero.get(f"{key}_roof_rot", hero.get("roof_rot", 0.0))
    if spin:
        flat = flat @ Matrix.Rotation(math.radians(spin), 4, "Z")
    w = along * frac
    d = across * frac
    logo(m, hero[key], w, d, hero.get(f"{key}_ink", rec["ink"]), flat,
         depth=0.45, lift=0.01, force_ink=f"{key}_ink" in hero,
         only=hero.get(f"{key}_only"), only_x=hero.get(f"{key}_x"))
    clear_roof(bx, by, w, d, brot + turn)


def wall_out(cx, cy, z, ang, fallback, run=0.0, tall=5.0):
    """How far the outermost skin of the building is, along `ang`.

    NOT half the footprint, which is padded, and NOT a ray either. Rays were
    tried three ways and all three failed on the same three signs: these
    facades are banded, the cornices that stand proud of the glass are thin,
    and a sampled ray falls between them. Taking the set-back reading buried
    the logo behind every band it crossed; taking the proud reading still
    missed the band that was between two samples, and 99_check_overlap counted
    up to 1454 triangle pairs inside the wall.

    So the geometry is asked directly: every vertex of the building mesh that
    falls inside the patch of wall this logo covers, and the furthest one out.
    Exact, and there is nothing left to fall between.
    """
    ob = bpy.data.objects.get("buildings")
    if ob is None:
        return fallback
    n = Vector((math.cos(ang), math.sin(ang), 0.0))
    side = Vector((-math.sin(ang), math.cos(ang), 0.0))
    origin = Vector((cx, cy, z))
    mw = ob.matrix_world
    half_run = max(run, 4.0) / 2.0
    best = None
    for v in ob.data.vertices:
        p = mw @ v.co
        if abs(p.z - z) > tall / 2:
            continue
        d = (p - origin)
        if abs(d.dot(side)) > half_run:
            continue
        out = d.dot(n)
        # close to THIS building's face: the mesh is a single one and the
        # neighbour opposite also has vertices in this band
        if fallback - 3.5 < out < fallback + 1.0 and (best is None or out > best):
            best = out
    return fallback if best is None else best


def hero_facade(m, rec, hero, site, key="word"):
    """The wordmark standing on a wall, across the whole face of the building.

    Not a parapet sign: that hangs in the band under the eaves and is limited
    to it. This is the wall itself, so the logo is measured against the facade
    and can be twenty metres wide.

    WHICH WALL. "The left face" is a thing you say looking at the frame, so it
    is answered against the frame: the camera is orthographic and fixed, its
    two visible faces are +X and +Y, and screen_xy puts +X on the left. Written
    as a lookup rather than a constant because the day the azimuth changes,
    a hardcoded +X becomes a logo painted on the side nobody can see.
    """
    def par(name, default):
        return hero.get(f"{key}_{name}", hero.get(name, default))
    ox, oy = par("facade_at", None) or rec["owner"]
    box = site.hit(ox, oy, tags=("buildings", "porteno"))
    if box is None:
        return
    bx, by, bw, bd, brot, _bz0, bz1 = box[:7]
    o = screen_xy(bx, by, bz1)
    # of the two faces this camera can see, the one that lands to the left
    faces = []
    for ang, half, run in ((0.0, bw / 2, bd), (math.pi / 2, bd / 2, bw)):
        nx, ny = math.cos(brot + ang), math.sin(brot + ang)
        p = screen_xy(bx + nx * 10.0, by + ny * 10.0, bz1)
        faces.append((p[0] - o[0], ang, half, run))
    side = par("facade_side", "left")
    if side == "wide":
        # the longer of the two faces this camera sees, whichever side it falls
        # on: a wordmark wants metres of wall, not one particular side
        _, ang, half, run = max(faces, key=lambda f: f[3])
    else:
        faces.sort(key=lambda f: f[0])
        _, ang, half, run = faces[0] if side == "left" else faces[-1]

    zc = bz1 * par("facade_z", 0.62)
    # FRAME, not PROUD. PROUD is 1.05 m and it is right for a parapet, where
    # separate letters hang clear of the wall on their own fixings. A logo
    # applied to a facade is not hung, it is stuck on: at 1.05 there was a
    # metre of daylight between the wall and the back of the letters and the
    # whole lockup read as floating. The facade's own shade frame stands 0.45
    # proud, so that is the surface, and `rest` puts the logo's back face on
    # it instead of centring the extrusion across it.
    # VERTICALLY ONLY, and at the centre of the face. Sampling across the width
    # as well looked more thorough and is worse: at the ends of a 25 m facade
    # there are courtyards and setbacks, the minimum lands in one of them and
    # the whole logo pushes inside the building. Eight buried signs.
    # A FIXED 5 m WINDOW, not the height of the logo. With the range tied to the
    # size of the sign, a tall one samples 9 m of facade, finds the ground
    # floor's setback or a courtyard, and pushes inside it: eight buried signs.
    # Five metres around its own height is the right thing to ask.
    #
    # THE EDGE OF THE FOOTPRINT, and nothing cleverer than that. Six ways of
    # finding the real wall were tried — one ray, seven rays, a grid, the
    # minimum, the maximum, the mesh vertices — and they all fail the same way:
    # these facades are banded and ARE NOT A PLANE, so any measurement that
    # sticks the logo to one part pushes it inside another. Up to 1454 triangle
    # pairs inside the building, in 99_check_overlap.
    #
    # The published footprint wraps the WHOLE building, cornices included.
    # Resting on its edge, the sign cannot end up inside anything; the air left
    # over is the box's padding, half a metre, and it is the price of not
    # burying it. Lowering `facade_proud` does not bring it closer: it brings
    # the logo closer to the edge of the box, which is already where it is.
    wall = Matrix.Rotation(brot + ang + math.pi / 2, 4, "Z") @ \
        upright(0.0, -(half + par("facade_proud", 0.02)),
                zc - rec["z"], 0.0)
    wall = Matrix.Translation(Vector((bx - rec["x"], by - rec["y"], 0.0))) @ wall
    logo(m, hero[key], run * par("facade_frac", 0.78),
         bz1 * par("facade_tall", 0.30),
         hero.get(f"{key}_ink", rec["ink"]), wall,
         depth=par("facade_depth", DEPTH), rest=True,
         oneline=bool(hero.get(f"{key}_oneline")),
         stack=bool(hero.get(f"{key}_stack")),
         force_ink=f"{key}_ink" in hero, only=hero.get(f"{key}_only"),
         only_x=hero.get(f"{key}_x"))


def hero_wall(m, rec, hero, site):
    """The symbol straight onto the party wall, with no panel behind it.

    A medianera is a painted mural and its panel is the paint. A hero brand
    does not want the paint: it wants the mark itself standing on the wall, so
    the panel, the surround and the mark all go and the symbol takes the whole
    area step 04 reserved. Nothing grows past that reservation — the published
    solid is what keeps trees and people off this wall, and a logo that reaches
    outside it is a logo with a jacaranda in front of it.
    """
    x = Matrix.Rotation(rec["rot"], 4, "Z")
    wall = x @ upright(0.0, 0.0, rec["h"] / 2, PROUD)
    logo(m, hero["iso"], rec["w"] * hero.get("wall_frac", 1.0),
         rec["h"] * hero.get("wall_frac", 1.0),
         hero.get("iso_ink", rec["ink"]), wall, depth=DEPTH, rest=False,
         force_ink="iso_ink" in hero, only=hero.get("iso_only"),
         only_x=hero.get("iso_x"))


def clear_roof(cx, cy, w, d, rot):
    """Take the rooftop clutter out from under a wordmark.

    Step 04 keeps its roof units off the sign it plans for THAT building, which
    is the ordinary case and works. A hero wordmark is not that case: it lands
    on whichever deck somebody pointed at, often a neighbour's, and no sign was
    ever planned there for 04 to keep clear of. So the sign clears its own
    ground, after the fact — the logo is the reason the roof is interesting and
    the water tank is not.
    """
    coll = bpy.data.collections.get("ROOFPROPS")
    if coll is None:
        return 0
    c, s = math.cos(-rot), math.sin(-rot)
    doomed = []
    for ob in coll.all_objects:
        p = ob.matrix_world.translation
        dx, dy = p.x - cx, p.y - cy
        dx, dy = dx * c - dy * s, dx * s + dy * c
        if abs(dx) <= w / 2 + 1.5 and abs(dy) <= d / 2 + 1.5:
            doomed.append(ob)
    for ob in doomed:
        bpy.data.objects.remove(ob, do_unlink=True)
    return len(doomed)


def hero_parapet(m, rec, hero, site):
    """The symbol down the facade, sized against the BUILDING.

    Not against the band under the eaves, which is what an ordinary parapet
    logo is measured against: a hero symbol hangs down the wall the way a real
    one does, so it reads at any distance. The name goes on the roof, and that
    is hero_word's job.
    """
    box = site.hit(rec["owner"][0], rec["owner"][1],
                   tags=("buildings", "porteno"))
    x = Matrix.Rotation(rec["rot"], 4, "Z")
    tall = box[6] * hero["iso_frac"] if box else LOGO_CAP
    logo(m, hero["iso"], rec["w"], tall, hero.get("iso_ink", rec["ink"]),
         x @ upright(0, -PROUD, -DROP, 0), depth=DEPTH, anchor="top",
         rest=False, force_ink="iso_ink" in hero)
    hero_word(m, rec, hero, site)


def readable(rec, rot=None):
    """Half a turn, when the logo would otherwise read right to left.

    A roofmark lies flat, so which way round it sits is free — and until now it
    was also invisible, because every geometric mark is symmetric: a disc, a
    ring and three bars look identical rotated 180 degrees. A wordmark does not.
    INCREASE shipped mirrored across the whole shot and nothing could have
    caught it, because there was no rule saying a mark has a reading direction.

    The camera is orthographic and never rolls, so this is decided once against
    screen_xy rather than per frame: walk 5 m along the logo's own +X, the
    direction it reads in, and if that lands to the LEFT on screen the panel is
    turned around. It costs nothing else — the panel under it is square.
    """
    r = rec["rot"] if rot is None else rot
    a = screen_xy(rec["x"], rec["y"], rec["z"])
    b = screen_xy(rec["x"] + math.cos(r) * 5.0,
                  rec["y"] + math.sin(r) * 5.0, rec["z"])
    return Matrix.Rotation(math.pi, 4, "Z") if b[0] < a[0] else Matrix.Identity(4)


def mark(m, kind, size, ink, x):
    """The abstract glyph on a panel or a disc. Flat, one colour, no detail:
    at this distance a logo is a silhouette and nothing else.

    IT STARTS BELOW ZERO, and its callers all place z=0 on the face of the
    panel. Resting exactly on that face put the glyph's underside on the same
    plane as the panel's front, pointing the same way and covering the same
    pixels: 15 of these signs flickered in the browser, and none of them ever
    looked wrong in a render, because a path tracer resolves the tie the same
    way every frame. See _common.SINK and 92_check_zfight.py.
    """
    s = size
    if kind == "disc":
        m.cyl((0, 0, -SINK), s * 0.34, 0.06 + SINK, ink, segs=24, xform=x)
    elif kind == "ring":
        for k in range(24):
            a0 = 2 * math.pi * k / 24
            a1 = 2 * math.pi * (k + 1) / 24
            r0, r1 = s * 0.22, s * 0.36
            m.prism([(r1 * math.cos(a0), r1 * math.sin(a0)),
                     (r1 * math.cos(a1), r1 * math.sin(a1)),
                     (r0 * math.cos(a1), r0 * math.sin(a1)),
                     (r0 * math.cos(a0), r0 * math.sin(a0))],
                    -SINK, 0.06, ink, x)
    elif kind == "square":
        m.slab(0, 0, s * 0.5, s * 0.5, -SINK, 0.06, ink, x)
        # INSET, not flush with the corner. At s*0.14 with a side of s*0.22 the
        # small square reached exactly s*0.25 — the same edge as the big one —
        # so their side faces were coplanar and overlapping, which is the same
        # fault as resting on the face and looks the same in the browser.
        m.slab(s * 0.135, s * 0.135, s * 0.21, s * 0.21, 0.06 - SINK, 0.09,
               mat("Sign Frame"), x)
    elif kind == "triangle":
        m.prism([(-s * 0.34, -s * 0.26), (s * 0.34, -s * 0.26),
                 (0.0, s * 0.34)], -SINK, 0.06, ink, x)
    elif kind == "chevron":
        for sy in (-1, 1):
            m.prism([(-s * 0.34, sy * s * 0.06), (0.0, sy * s * 0.30),
                     (s * 0.34, sy * s * 0.06), (s * 0.20, sy * s * 0.02),
                     (0.0, sy * s * 0.19), (-s * 0.20, sy * s * 0.02)],
                    -SINK, 0.06, ink, x)
    else:                                   # bars
        for k in range(3):
            m.slab(0, (k - 1) * s * 0.16, s * (0.5 - k * 0.10), s * 0.09,
                   -SINK, 0.06, ink, x)


def upright(x, y, z, h):
    """A transform that stands the flat mark up in a vertical panel.

    mark() draws in XY and extrudes in +Z, which is right for a panel lying on
    a roof deck and useless for one facing sideways. Rotating 90 about X sends
    the mark's own +Z to world -Y, which is the direction every panel here
    faces, so the glyph ends up standing on the front of the panel instead of
    lying on its top edge.
    """
    return Matrix.Translation(Vector((x, y, z))) @ \
        Matrix.Rotation(math.radians(90), 4, "X") @ \
        Matrix.Translation(Vector((0, 0, h)))


def billboard(m, rec, face, ink, frame, x, art=None):
    w, h, lift = rec["w"], rec["h"], rec["lift"]
    t = 0.35                              # panel thickness
    b = 0.34                              # border width
    # legs: two pairs, front and back, so the support reads as a truss and not
    # as a panel levitating. They carry on past the panel foot on purpose.
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.slab(sx * w * 0.33, sy * 0.62, 0.52, 0.52, 0.0,
                   lift + h * 0.18, frame, x)
    for sx in (-1, 1):                    # diagonal-ish knee braces, cheaply
        m.slab(sx * w * 0.33, 0.0, 0.34, 1.6, lift * 0.42, lift * 0.42 + 0.34,
               frame, x)
    m.slab(0.0, 0.0, w * 0.70, 0.34, lift * 0.62, lift * 0.62 + 0.34, frame, x)
    # the catwalk, in front and below: the thing that makes it read as a real
    # hoarding rather than as a floating rectangle
    m.slab(0.0, -1.05, w * 0.94, 1.10, lift - 0.80, lift - 0.62, frame, x)
    for sx in (-1, 1):
        m.slab(sx * w * 0.47, -1.05, 0.16, 1.10, lift - 0.62, lift - 0.02,
               frame, x)
    # the face
    m.slab(0.0, 0.0, w, t, lift, lift + h, face, x)
    m.slab(0.0, -t / 2 - 0.09, w, 0.18, lift, lift + b, frame, x)
    m.slab(0.0, -t / 2 - 0.09, w, 0.18, lift + h - b, lift + h, frame, x)
    for sx in (-1, 1):
        m.slab(sx * (w / 2 - b / 2), -t / 2 - 0.09, b, 0.18, lift, lift + h,
               frame, x)
    panel = x @ upright(0.0, 0.0, lift + h / 2, t / 2)
    # inside the border, which is b wide on all four sides
    if not (art and logo(m, art, w - b * 3.2, h - b * 2.6, rec["ink"], panel)):
        mark(m, rec["mark"], h * 1.10, ink, panel)


def medianera(m, rec, face, ink, frame, x, art=None):
    """Flush on the wall, or as flush as this city's facades allow.

    PROUD, not the 0.2 m a painted wall really stands off its own bricks: the
    facades here carry a shade frame 0.45 m proud and are published 0.45 m out,
    so the honest number puts the mural inside the building it is painted on.
    """
    w, h = rec["w"], rec["h"]
    t = 0.28
    m.slab(0.0, -PROUD - t / 2, w, t, 0.0, h, face, x)
    # a thin surround, so the mural reads as applied to the wall and has an
    # edge to catch the light rather than dissolving into the concrete
    m.slab(0.0, -PROUD - t - 0.06, w, 0.12, 0.0, 0.26, frame, x)
    m.slab(0.0, -PROUD - t - 0.06, w, 0.12, h - 0.26, h, frame, x)
    for sx in (-1, 1):
        m.slab(sx * (w / 2 - 0.13), -PROUD - t - 0.06, 0.26, 0.12, 0.0, h,
               frame, x)
    wall = x @ upright(0.0, 0.0, h / 2, PROUD + t)
    if not (art and logo(m, art, w * 0.84, h * 0.66, rec["ink"], wall)):
        mark(m, rec["mark"], min(w, h) * 1.15, ink, wall)


def build(rec, coll, site):
    m = Mesh()
    face, ink = facemat(rec)
    frame = mat("Sign Frame")
    kind = rec["kind"]
    x = Matrix.Rotation(rec["rot"], 4, "Z")
    # the real artwork, when this brand has one. Step 04 puts the real brands
    # at the head of the pool and deals by visibility, so `art` is set on the
    # signs the camera actually reads and None out where it never gets to.
    art = rec.get("logo")
    hero = HERO.get(rec["text"]) if art else None
    k = SIZE.get(rec["name"])
    if k:
        rec = dict(rec, w=rec["w"] * k, h=rec["h"] * k)
    if rec["name"] == "Sign.009":
        print(f"  DEBUG {rec['name']} text={rec['text']!r} art={art!r} "
              f"hero={None if hero is None else sorted(hero)} "
              f"kind={rec['kind']!r}")
    if hero and hero.get("face"):
        face = pbrmat(f"Logo {rec['text']} hero", hero["face"], 0.42)

    if kind == "parapet":
        # down the wall, so the tops clear the roof edge by DROP and the whole
        # word reads against the facade rather than against the sky
        if hero and hero.get("facade_only"):
            # the parapet moves away: nothing is left on this building
            for k in hero.get("facade_arts",
                              [hero.get("facade_art", "word")]):
                hero_facade(m, rec, hero, site, key=k)
            if hero.get("roof_art"):
                hero_word(m, rec, hero, site, key=hero["roof_art"])
        elif hero:
            hero_parapet(m, rec, hero, site)
        elif art:
            # the real wordmark, extruded, hung from the same cap line. DEPTH,
            # not the 0.06 a flat mark gets: on a facade the relief is what
            # casts the shadow the letters read against.
            # CAP is a CAP HEIGHT and a logo's box is not one: it includes
            # ascenders, descenders and the air the lockup is drawn with, so a
            # wordmark set to CAP comes out with letters two thirds the size of
            # the ones it replaces. LOGO_CAP is the box that puts a logo's
            # letters back on the parapet at the size the built letters had.
            logo(m, art, rec["w"], LOGO_CAP, rec["ink"],
                 x @ upright(0, -PROUD, -DROP, 0), depth=DEPTH,
                 anchor="top", rest=False)
        else:
            letters(m, rec, face,
                    x @ Matrix.Translation(Vector((0, -PROUD, -CAP - DROP))))
    elif kind == "billboard":
        if hero and hero.get("facade_only"):
            # the sign is never raised: the brand lives on a wall. Parapet,
            # party wall and roofmark already did this and it was missing here —
            # a billboard is a free-standing structure on a roof, so leaving it
            # built with the logo moved away leaves a blank panel on stilts,
            # which is worse than nothing at all.
            for k in hero.get("facade_arts",
                              [hero.get("facade_art", "word")]):
                hero_facade(m, rec, hero, site, key=k)
            if hero.get("roof_art"):
                hero_word(m, rec, hero, site, key=hero["roof_art"])
        else:
            billboard(m, rec, face, ink, frame, x, art)
    elif kind == "medianera":
        if hero and hero.get("facade_only"):
            # the whole mural leaves: the brand lives on another building's wall
            for k in hero.get("facade_arts",
                              [hero.get("facade_art", "word")]):
                hero_facade(m, rec, hero, site, key=k)
            if hero.get("roof_art"):
                hero_word(m, rec, hero, site, key=hero["roof_art"])
        elif hero:
            hero_wall(m, rec, hero, site)
            if hero.get("facade"):
                for k in hero.get("facade_arts",
                                  [hero.get("facade_art", "word")]):
                    hero_facade(m, rec, hero, site, key=k)
            if hero.get("roof_frac") or hero.get("roof_art"):
                hero_word(m, rec, hero, site,
                          key=hero.get("roof_art", "word"))
        else:
            medianera(m, rec, face, ink, frame, x, art)
    elif kind == "roofmark":
        s = rec["w"]
        if hero and hero.get("facade_only"):
            # no panel: the wordmark goes on the wall and, when the brand asks
            # for it, the symbol lies bare on the deck
            for k in hero.get("facade_arts",
                              [hero.get("facade_art", "word")]):
                hero_facade(m, rec, hero, site, key=k)
            if hero.get("roof_art"):
                hero_word(m, rec, hero, site, key=hero["roof_art"])
            ob = m.build(rec["name"], coll)
            ob.location = (rec["x"], rec["y"], rec["z"])
            return ob
        m.slab(0, 0, s, s, 0.0, 0.10, face, x)
        top = x @ Matrix.Translation(Vector((0, 0, 0.10)))
        if art:
            top = top @ readable(rec)
        if hero:
            # a symbol is round-ish: it takes the panel almost whole, where a
            # wordmark had to fit its aspect ratio inside it
            f = hero["iso_frac"]
            logo(m, hero["iso"], s * f, s * f,
                 hero.get("iso_ink", rec["ink"]), top, depth=0.28,
                 force_ink="iso_ink" in hero)
            if hero.get("facade"):
                hero_facade(m, rec, hero, site)
            elif hero.get("roof_frac"):
                hero_word(m, rec, hero, site)
        elif not (art and logo(m, art, s * 0.92, s * 0.80, rec["ink"], top,
                                depth=0.28)):
            mark(m, rec["mark"], s, ink, top)
    else:                                   # mast
        s = rec["w"]
        h = s * MAST
        m.cyl((0, 0, 0), 0.45, h, frame, segs=10, xform=x)
        # the disc is a flat cylinder stood on edge, so the mark sits on its
        # face and not on its rim
        up = x @ Matrix.Translation(Vector((0, 0, h + s / 2))) @ \
            Matrix.Rotation(math.radians(90), 4, "X")
        m.cyl((0, 0, -0.2), s / 2, 0.4, face, segs=32, xform=up)
        disc = up @ Matrix.Translation(Vector((0, 0, 0.2)))
        if hero:
            # a symbol is round-ish, so it takes the disc almost whole, where a
            # wordmark had to fit inside the inscribed square
            f = hero["iso_frac"]
            logo(m, hero["iso"], s * f, s * f,
                 hero.get("iso_ink", rec["ink"]), disc, depth=0.22,
                 force_ink="iso_ink" in hero, only_x=hero.get("iso_x"))
            if hero.get("facade"):
                for k in hero.get("facade_arts",
                                  [hero.get("facade_art", "word")]):
                    hero_facade(m, rec, hero, site, key=k)
            if hero.get("roof_frac") or hero.get("roof_art"):
                hero_word(m, rec, hero, site,
                          key=hero.get("roof_art", "word"))
        # inside the disc, not across it: a wordmark on a circle has to clear
        # the rim on both sides, so the box is the inscribed square
        elif not (art and logo(m, art, s * 0.66, s * 0.52, rec["ink"], disc)):
            mark(m, rec["mark"], s * 0.9, ink, disc)

    ob = m.build(rec["name"], coll)
    ob.location = (rec["x"], rec["y"], rec["z"])
    return ob


def main():
    open_city(needs_collections=("BUILDINGS",), needs_files=(SIGNS,),
              hint="run 04_buildings.py first: it plans the signs this builds")
    plan = json.loads((SIGNS).read_text())

    coll = purge("SIGNS")

    # the footprints as they stand, so a hero sign can measure the roof it is
    # going to lie on. Separate from `sol`, which is what THIS step publishes.
    site = Solids.load(SOLIDS)

    sol = Solids()
    for rec in plan:
        if rec.get("drop"):        # taken out by hand: see _brands.DROP
            continue
        ob = build(rec, coll, site)
        # published so the overlap check knows these are meant to be there,
        # and so anything placed later keeps out of them
        zs = [(ob.matrix_world @ v.co).z for v in ob.data.vertices]
        # WHAT WAS ACTUALLY BUILT, written back into the manifest.
        #
        # 04's record is a PLAN, and for a `facade_only` brand it is an anchor
        # that is never raised: it says "roofmark, 7.1 m" while on the wall
        # there is a 27.6 m wordmark. 93_check_signs measured the plan, so it
        # reported exactly the best-delivered brands wrongly — and called them
        # too small when they were not. This step writes it because it is the
        # only one that has the mesh.
        if len(ob.data.vertices):
            # ob.location + v.co, and NOT matrix_world: the matrix is
            # recomputed on the next depsgraph evaluation, so reading it here
            # returns the identity and all 97 signs measure from the origin.
            loc = ob.location
            pts = [(v.co[0] + loc[0], v.co[1] + loc[1], v.co[2] + loc[2])
                   for v in ob.data.vertices]
            lo = [min(p[i] for p in pts) for i in range(3)]
            hi = [max(p[i] for p in pts) for i in range(3)]
            rec["built"] = [round((lo[0] + hi[0]) / 2, 2),
                            round((lo[1] + hi[1]) / 2, 2),
                            round((lo[2] + hi[2]) / 2, 2),
                            round(max(hi[0] - lo[0], hi[1] - lo[1]), 2),
                            round(hi[2] - lo[2], 2)]
        if rec["kind"] == "medianera":
            # a square the width of a 34 m mural would reach 17 m out over the
            # pavement and refuse every tree and every pedestrian along the
            # avenue. A mural is a rotated slot, so publish the slot: it runs
            # the length of the panel and 1.9 m off the wall.
            sol.add(rec["x"] + math.sin(rec["rot"]) * 0.8,
                    rec["y"] - math.cos(rec["rot"]) * 0.8,
                    rec["w"] + 1.0, 2.2, rec["rot"], min(zs), max(zs))
        elif rec["kind"] == "billboard":
            sol.add(rec["x"], rec["y"], rec["w"] + 1.0, 3.4, rec["rot"],
                    min(zs), max(zs))
        else:
            sol.add(rec["x"], rec["y"], rec["w"] + 1.0, rec["w"] + 1.0,
                    0.0, min(zs), max(zs))
    sol.merge_into(SOLIDS, "signs")
    # the manifest leaves here with one key more than it arrived with: see `built`
    (SIGNS).write_text(json.dumps(plan, indent=1))

    # the SVG importer leaves one material per fill behind on every import, and
    # they outlive the curves: new_from_object copies them onto the mesh, and
    # the cache holds those meshes for the whole run. Nothing reads them — the
    # colour is re-made as a pbrmat — so they are dropped once the last logo is
    # built, rather than shipping 31 stray materials inside the .blend and out
    # through the glTF.
    # dropping the cache is not enough: new_from_object's meshes live in
    # bpy.data and keep their copy of the material alive, so they go first
    for pieces in _logos.values():
        for me, _col, _ar in pieces:
            bpy.data.meshes.remove(me)
    _logos.clear()
    # unconditionally, not just the unused ones: the .blend already carries the
    # ones every previous run left behind, and none of them is ever reachable
    # from the built geometry — add_mesh takes the material from its caller, so
    # the importer's own material is dropped on the way in.
    # AND THE COLLECTIONS. The importer makes one collection per file, named
    # after it, and leaves it behind: 20 logos x a run added ~29 of them each
    # time, so the .blend had hundreds of empty `pomelo.svg.014` collections
    # that nobody sees in a render and that the glTF exporter faithfully
    # writes out as nodes. They are removed by name because that name is the
    # importer's, not ours: nothing else in this city is called *.svg.
    junk = [c for c in bpy.data.collections
            if c.name.endswith(".svg") or ".svg." in c.name]
    for c in junk:
        bpy.data.collections.remove(c)
    print(f"  {len(junk)} SVG collections dropped")

    stray = [mt for mt in bpy.data.materials if mt.name.startswith("SVGMat")]
    for mt in stray:
        bpy.data.materials.remove(mt)
    print(f"  {len(stray)} SVG materials dropped")

    kinds = {}
    for rec in plan:
        kinds[rec["kind"]] = kinds.get(rec["kind"], 0) + 1
    print(f"\n  {len(plan)} signs built   " +
          "  ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    u, t = counts()
    print(f"  triangles: {u} unique / {t} total")

    exposure = bpy.context.scene.view_settings.exposure
    with preview(target=(0, 0, 0)):
        blib.render(str(R / "city_10_signs.png"), "EEVEE", samples=64,
                    resolution=(1600, 900), exposure=exposure)
    save_city()


main()
