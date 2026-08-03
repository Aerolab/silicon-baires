"""Spike — how to build a crossroads.

Risk #1 in docs/city/PLAN.md. Two swept road ribbons crossing leave a hole and
z-fight, and every later layer sits on top of whatever this decides. Three
approaches, built side by side, judged on the same render.

  A  corridors + patch   ribbons stop short of the crossing; a separate square
                         patch fills it, with corner pieces for the sidewalk
  B  boolean union       overlap the ribbons and boolean them together
  E  negative space      one asphalt sheet under everything; the blocks are
                         raised slabs on top, so the road is simply the gap
                         between them and no intersection is ever built

Opens city.blend for the real sun and palette, builds, renders, EXITS WITHOUT
SAVING.

    ./bl scripts/city/01_spike_intersections.py
"""
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import bpy, blib

R = ROOT / "renders"

BLOCK, STREET = 90.0, 22.0
LANE, WALK = 7.0, 4.0          # per side: 7 m carriageway + 4 m sidewalk
KERB = 0.15
CARRIAGE = LANE * 2            # 14 m of asphalt between kerbs
TILE = BLOCK + STREET          # 112 m, the block pitch
MARK_Z = 0.02                  # markings float above the asphalt


def mat(name):
    return bpy.data.materials[name]


def rect(name, cx, cy, w, h, z, material, coll):
    """A flat quad. Built from mesh data, not ops: faster and no context games."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([(cx - w / 2, cy - h / 2, z), (cx + w / 2, cy - h / 2, z),
                    (cx + w / 2, cy + h / 2, z), (cx - w / 2, cy + h / 2, z)],
                   [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    coll.objects.link(ob)
    return ob


def box(name, cx, cy, w, h, z0, z1, material, coll):
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    verts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    coll.objects.link(ob)
    return ob


def markings(coll, z=MARK_Z):
    """Edge lines, centre dashes, crosswalks and stop lines on both axes."""
    m = mat("Marking")
    half_road = CARRIAGE / 2
    inter = half_road            # the intersection square is 14 x 14

    for axis in (0, 1):
        def place(name, along, across, la, ac):
            # along = coordinate down the street, across = sideways
            cx, cy = (along, across) if axis == 0 else (across, along)
            w, h = (la, ac) if axis == 0 else (ac, la)
            rect(name, cx, cy, w, h, z, m, coll)

        for side in (-1, 1):
            # solid edge line, in the two stretches either side of the crossing
            for direction in (-1, 1):
                start = inter + 6.0
                length = TILE / 2 - start
                place(f"edge{axis}{side}{direction}",
                      direction * (start + length / 2), side * (half_road - 0.4),
                      length, 0.18)
        # centre dashes
        for k in range(-9, 10):
            d = k * 6.0
            if abs(d) < inter + 6.0:
                continue
            place(f"dash{axis}{k}", d, 0.0, 3.0, 0.16)
        # crosswalk: bars across the carriageway on both approaches
        for direction in (-1, 1):
            base = direction * (inter + 1.2)
            for k in range(9):
                off = -half_road + 0.9 + k * 1.5
                place(f"zebra{axis}{direction}{k}", base, off, 3.2, 0.7)
            place(f"stop{axis}{direction}", direction * (inter + 5.4), 0.0,
                  0.4, CARRIAGE)


# ---------------------------------------------------------------------------
# A — corridors that stop short, plus a patch over the crossing
# ---------------------------------------------------------------------------
def variant_a(coll):
    inter = CARRIAGE / 2
    arm = TILE / 2 - inter                       # length of one corridor arm
    for axis in (0, 1):
        for direction in (-1, 1):
            c = direction * (inter + arm / 2)
            la, ac = (arm, CARRIAGE) if axis == 0 else (CARRIAGE, arm)
            cx, cy = (c, 0.0) if axis == 0 else (0.0, c)
            rect(f"roadA{axis}{direction}", cx, cy, la, ac, 0.0,
                 mat("Asphalt"), coll)
            # sidewalk strips flanking the corridor
            for side in (-1, 1):
                off = side * (inter + WALK / 2)
                sx, sy = (c, off) if axis == 0 else (off, c)
                sw, sh = (arm, WALK) if axis == 0 else (WALK, arm)
                box(f"walkA{axis}{direction}{side}", sx, sy, sw, sh,
                    0.0, KERB, mat("Sidewalk"), coll)
    # the patch: asphalt square over the crossing
    rect("patchA", 0, 0, CARRIAGE, CARRIAGE, 0.0, mat("Asphalt"), coll)
    # four corner pieces so the sidewalk turns the corner
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"cornerA{sx}{sy}", sx * (inter + WALK / 2),
                sy * (inter + WALK / 2), WALK, WALK, 0.0, KERB,
                mat("Sidewalk"), coll)
    markings(coll)


# ---------------------------------------------------------------------------
# B — overlap everything and let the boolean sort it out
# ---------------------------------------------------------------------------
def variant_b(coll):
    road_h = 0.02
    a = box("roadB_x", 0, 0, TILE, CARRIAGE, 0.0, road_h, mat("Asphalt"), coll)
    b = box("roadB_y", 0, 0, CARRIAGE, TILE, 0.0, road_h, mat("Asphalt"), coll)
    walk_a = box("walkB_x", 0, 0, TILE, CARRIAGE + WALK * 2, 0.0, KERB,
                 mat("Sidewalk"), coll)
    walk_b = box("walkB_y", 0, 0, CARRIAGE + WALK * 2, TILE, 0.0, KERB,
                 mat("Sidewalk"), coll)

    vl = bpy.context.view_layer

    def boolean(target, cutter, op):
        vl.objects.active = target
        m = target.modifiers.new("bool", "BOOLEAN")
        m.operation, m.object, m.solver = op, cutter, "EXACT"
        bpy.ops.object.modifier_apply(modifier=m.name)

    boolean(walk_a, walk_b, "UNION")
    bpy.data.objects.remove(walk_b, do_unlink=True)
    boolean(a, b, "UNION")
    bpy.data.objects.remove(b, do_unlink=True)
    boolean(walk_a, a, "DIFFERENCE")     # carve the road out of the sidewalk
    markings(coll, z=road_h + MARK_Z)


# ---------------------------------------------------------------------------
# E — no intersection at all: asphalt underneath, blocks raised on top
# ---------------------------------------------------------------------------
def variant_e(coll):
    rect("sheetE", 0, 0, TILE * 1.2, TILE * 1.2, 0.0, mat("Asphalt"), coll)
    lift = 0.9                       # block slabs stand proud of the road
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * TILE / 2, sy * TILE / 2
            box(f"slabE{sx}{sy}", cx, cy, BLOCK, BLOCK, 0.0, lift,
                mat("Sidewalk"), coll)
            # the block interior, inset from the sidewalk edge
            rect(f"padE{sx}{sy}", cx, cy, BLOCK - WALK * 2, BLOCK - WALK * 2,
                 lift + 0.01, mat("Grass"), coll)
    markings(coll)


# ---------------------------------------------------------------------------
# E2 — the actual test: does negative space survive a curved arterial?
# If the road is a gap, a curve only bends the BLOCK outline. The road itself
# is still the same flat asphalt sheet and still needs no geometry.
# ---------------------------------------------------------------------------
import math


def prism(name, poly, z0, z1, material, coll):
    """Extrude a flat polygon (list of (x, y)) into a slab."""
    n = len(poly)
    verts = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    coll.objects.link(ob)
    return ob


def arc_band(name, r0, r1, a0, a1, z, material, coll, segs=48):
    """A flat annulus sector: kerb lines, lane lines and dashes on a curve."""
    ang = [a0 + (a1 - a0) * i / segs for i in range(segs + 1)]
    poly = [(r1 * math.cos(a), r1 * math.sin(a)) for a in ang]
    poly += [(r0 * math.cos(a), r0 * math.sin(a)) for a in reversed(ang)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x, y, z) for x, y in poly], [], [tuple(range(len(poly)))])
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    coll.objects.link(ob)
    return ob


def variant_e2(coll):
    RAD = 150.0                       # arterial centreline radius
    A0, A1 = math.radians(35), math.radians(145)
    lift, half = 0.9, CARRIAGE / 2
    edge = half + WALK                # block boundary either side of the road

    rect("sheetE2", 0, 0, TILE * 2.4, TILE * 2.4, 0.0, mat("Asphalt"), coll)

    # the two blocks flanking the curve: their inner edge IS the arc
    for sign, depth in ((+1, 95.0), (-1, 95.0)):
        r_in = RAD + sign * edge
        r_out = r_in + sign * depth
        prism(f"slabE2{sign}", _sector(min(r_in, r_out), max(r_in, r_out),
                                       A0, A1), 0.0, lift,
              mat("Sidewalk"), coll)
        # block interior, inset by the sidewalk width
        arc_band(f"padE2{sign}", min(r_in, r_out) + WALK,
                 max(r_in, r_out) - WALK, A0 + 0.03, A1 - 0.03,
                 lift + 0.01, mat("Grass"), coll)

    # markings, bent to the same radii
    m = mat("Marking")
    for sign in (+1, -1):
        r = RAD + sign * (half - 0.4)
        arc_band(f"edgeE2{sign}", r - 0.09, r + 0.09, A0, A1, MARK_Z, m, coll)
    step = (A1 - A0) / 14
    for k in range(14):
        a = A0 + k * step
        arc_band(f"dashE2{k}", RAD - 0.08, RAD + 0.08, a, a + step * 0.45,
                 MARK_Z, m, coll)


def _sector(r0, r1, a0, a1, segs=48):
    ang = [a0 + (a1 - a0) * i / segs for i in range(segs + 1)]
    return ([(r1 * math.cos(a), r1 * math.sin(a)) for a in ang] +
            [(r0 * math.cos(a), r0 * math.sin(a)) for a in reversed(ang)])


VARIANTS = [("A_patch", variant_a), ("B_boolean", variant_b),
            ("E_negative", variant_e), ("E2_curve", variant_e2)]


def tris(coll):
    n = 0
    for ob in coll.objects:
        if ob.type == "MESH":
            n += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    return n


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    bpy.data.objects.remove(bpy.data.objects["GROUND_placeholder"],
                            do_unlink=True)
    cam = bpy.data.objects["HeroCam"]
    exposure = bpy.context.scene.view_settings.exposure

    for name, fn in VARIANTS:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
        fn(coll)
        print(f"\n  {name}: {len(coll.objects)} objects, {tris(coll)} tris")

        # E2 is built around an arc centre 150 m away; bring it into frame
        if name == "E2_curve":
            for ob in coll.objects:
                ob.location.y -= 150.0
            cam.data.ortho_scale = 260.0
        else:
            cam.data.ortho_scale = TILE * 1.15
        blib.render(str(R / f"spike_{name}_hero.png"), "EEVEE", samples=64,
                    resolution=(1400, 900), exposure=exposure)

        bpy.data.collections.remove(coll)

    print("\n  nothing saved: city.blend is untouched")


main()
