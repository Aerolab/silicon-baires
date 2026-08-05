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
from _common import (Mesh, collection, mat, pbrmat, rng, counts, R, SIGNS,
                     SOLIDS, SINK, open_city, save_city, purge, preview)
from _solids import Solids

FONT = "/Users/bilune/Library/Fonts/PPMonumentNormal-Black.otf"
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
        cu.font = bpy.data.fonts.load(FONT)
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
            # the glyph is built in XY and stood up: its own Y becomes height
            v.co.x = (v.co.x - lo) * k + cursor
            v.co.y, v.co.z = v.co.z, v.co.y * k
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
        cu.font = bpy.data.fonts.load(FONT)
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


def billboard(m, rec, face, ink, frame, x):
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
    mark(m, rec["mark"], h * 1.10, ink,
         x @ upright(0.0, 0.0, lift + h / 2, t / 2))


def medianera(m, rec, face, ink, frame, x):
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
    mark(m, rec["mark"], min(w, h) * 1.15, ink,
         x @ upright(0.0, 0.0, h / 2, PROUD + t))


def build(rec, coll):
    m = Mesh()
    face, ink = facemat(rec)
    frame = mat("Sign Frame")
    kind = rec["kind"]
    x = Matrix.Rotation(rec["rot"], 4, "Z")

    if kind == "parapet":
        # down the wall, so the tops clear the roof edge by DROP and the whole
        # word reads against the facade rather than against the sky
        letters(m, rec, face,
                x @ Matrix.Translation(Vector((0, -PROUD, -CAP - DROP))))
    elif kind == "billboard":
        billboard(m, rec, face, ink, frame, x)
    elif kind == "medianera":
        medianera(m, rec, face, ink, frame, x)
    elif kind == "roofmark":
        s = rec["w"]
        m.slab(0, 0, s, s, 0.0, 0.10, face, x)
        mark(m, rec["mark"], s, ink, x @ Matrix.Translation(Vector((0, 0, 0.10))))
    else:                                   # mast
        s = rec["w"]
        h = s * MAST
        m.cyl((0, 0, 0), 0.45, h, frame, segs=10, xform=x)
        # the disc is a flat cylinder stood on edge, so the mark sits on its
        # face and not on its rim
        up = x @ Matrix.Translation(Vector((0, 0, h + s / 2))) @ \
            Matrix.Rotation(math.radians(90), 4, "X")
        m.cyl((0, 0, -0.2), s / 2, 0.4, face, segs=32, xform=up)
        mark(m, rec["mark"], s * 0.9, ink,
             up @ Matrix.Translation(Vector((0, 0, 0.2))))

    ob = m.build(rec["name"], coll)
    ob.location = (rec["x"], rec["y"], rec["z"])
    return ob


def main():
    open_city(needs_collections=("BUILDINGS",), needs_files=(SIGNS,),
              hint="run 04_buildings.py first: it plans the signs this builds")
    plan = json.loads((SIGNS).read_text())

    coll = purge("SIGNS")

    sol = Solids()
    for rec in plan:
        ob = build(rec, coll)
        # published so the overlap check knows these are meant to be there,
        # and so anything placed later keeps out of them
        zs = [(ob.matrix_world @ v.co).z for v in ob.data.vertices]
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
