"""Step 10 — company signs, ready for logos.

The reference is a parade of real logos. We are reproducing the city, not the
branding, so these carry invented companies; what is being reproduced is how a
logo is physically mounted on a building, which is the part that has to be
built now if it is ever going to be swapped for artwork later.

Three mountings, all read off the reference frames:

  parapet   individual extruded letters standing on the roof edge, projecting
            out past the facade. This is the Google one, and it is the type
            that reads from furthest away because it breaks the roofline.
  roofmark  a flat panel lying on the deck with a mark on it, costing no
            height at all. The orange square with the white B.
  mast      a large disc on a pole, standing clear of everything and turned to
            face the camera. One or two in frame, no more: it is a hero.

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
from _common import Mesh, collection, mat, pbrmat, rng, counts
from _solids import Solids

R = ROOT / "renders"
FONT = "/Users/bilune/Library/Fonts/PPMonumentNormal-Black.otf"
CAP = 4.2                 # letter height on a parapet, metres
DEPTH = 0.9               # how far a letter is extruded
PROUD = 0.45              # how far it stands out past the facade
MAST = 0.55               # mast height as a fraction of the disc diameter


def facemat(rec):
    return (pbrmat(f"Logo {rec['text']}", rec["face"], 0.42),
            pbrmat(f"Ink {rec['text']}", rec["ink"], 0.42))


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
    at this distance a logo is a silhouette and nothing else."""
    s = size
    if kind == "disc":
        m.cyl((0, 0, 0), s * 0.34, 0.06, ink, segs=24, xform=x)
    elif kind == "ring":
        for k in range(24):
            a0 = 2 * math.pi * k / 24
            a1 = 2 * math.pi * (k + 1) / 24
            r0, r1 = s * 0.22, s * 0.36
            m.prism([(r1 * math.cos(a0), r1 * math.sin(a0)),
                     (r1 * math.cos(a1), r1 * math.sin(a1)),
                     (r0 * math.cos(a1), r0 * math.sin(a1)),
                     (r0 * math.cos(a0), r0 * math.sin(a0))],
                    0.0, 0.06, ink, x)
    elif kind == "square":
        m.slab(0, 0, s * 0.5, s * 0.5, 0.0, 0.06, ink, x)
        m.slab(s * 0.14, s * 0.14, s * 0.22, s * 0.22, 0.06, 0.09,
               mat("Sign Frame"), x)
    elif kind == "triangle":
        m.prism([(-s * 0.34, -s * 0.26), (s * 0.34, -s * 0.26),
                 (0.0, s * 0.34)], 0.0, 0.06, ink, x)
    elif kind == "chevron":
        for sy in (-1, 1):
            m.prism([(-s * 0.34, sy * s * 0.06), (0.0, sy * s * 0.30),
                     (s * 0.34, sy * s * 0.06), (s * 0.20, sy * s * 0.02),
                     (0.0, sy * s * 0.19), (-s * 0.20, sy * s * 0.02)],
                    0.0, 0.06, ink, x)
    else:                                   # bars
        for k in range(3):
            m.slab(0, (k - 1) * s * 0.16, s * (0.5 - k * 0.10), s * 0.09,
                   0.0, 0.06, ink, x)


def build(rec, coll):
    m = Mesh()
    face, ink = facemat(rec)
    frame = mat("Sign Frame")
    kind = rec["kind"]
    x = Matrix.Rotation(rec["rot"], 4, "Z")

    if kind == "parapet":
        # the letters stand on the parapet and lean out past the wall, which
        # is what makes them catch the light against the facade behind
        letters(m, rec, face, x @ Matrix.Translation(Vector((0, -PROUD, 0))))
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
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    pbrmat("Sign Frame", "#2b2b28", 0.55)
    plan = json.loads((R / "city_signs.json").read_text())

    if "SIGNS" in bpy.data.collections:
        c = bpy.data.collections["SIGNS"]
        for ob in list(c.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(c)
    coll = collection("SIGNS")

    sol = Solids()
    for rec in plan:
        ob = build(rec, coll)
        # published so the overlap check knows these are meant to be there,
        # and so anything placed later keeps out of them
        zs = [(ob.matrix_world @ v.co).z for v in ob.data.vertices]
        sol.add(rec["x"], rec["y"], rec["w"] + 1.0, rec["w"] + 1.0,
                0.0, min(zs), max(zs))
    sol.merge_into(R / "city_solids.json", "signs")

    kinds = {}
    for rec in plan:
        kinds[rec["kind"]] = kinds.get(rec["kind"], 0) + 1
    print(f"\n  {len(plan)} signs built   " +
          "  ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    u, t = counts()
    print(f"  triangles: {u} unique / {t} total")

    cam = bpy.data.objects["HeroCam"]
    exposure = bpy.context.scene.view_settings.exposure
    blib.render(str(R / "city_10_signs.png"), "EEVEE", samples=64,
                resolution=(1600, 900), exposure=exposure)
    blib.save(str(R / "city.blend"))


main()
