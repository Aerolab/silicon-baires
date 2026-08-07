"""Step 92 — what is fighting for the same plane.

    ./bl scripts/city/92_check_zfight.py
    ./bl scripts/city/92_check_zfight.py --all    # include sub-pixel faces

It reports; it does not repair. Two fixes, and the first one is the one to
check first:

  THE WINDING. If a solid's faces point inward, the face a rasteriser draws is
  its far side, which is usually sitting on top of something else. This is what
  the whole investigation turned out to be. `bmesh.calc_volume(signed=True)` on
  a closed mesh answers it: positive is outward. See the note in _common.box().
  THE OFFSET. A detail resting exactly on its backing, both facing the same
  way. Sink it by `_common.SINK`; `10_signs.mark()` is the worked example.

WHAT THIS CATCHES. Two faces that occupy the SAME plane, overlap, and point the
same way have no answer to "which one is in front". Cycles picks one and picks
it consistently, so the render looks fine and this has never mattered. A
rasteriser decides per pixel, from a depth value it interpolated across a
triangle, so the answer changes with sub-pixel error: the surface tears into
patches that swap as the camera moves. In the browser the roof marks flicker,
and this is why.

It is a geometry fault either way. The render is not "correct", it is arbitrary
and stable — a logo on a roof draws over the roof by luck, and a different
Blender version could pick the other one.

IN WORLD SPACE, ACROSS OBJECTS, and that is the whole point. The first version
of this compared faces inside each mesh datablock, found the marks resting on
their own panels, and reported the signs clean once those were fixed. They were
not: `Sign.020` is a 40 m2 plate whose top face is at z = 12.220, and the roof
it stands on is a 383 m2 slab whose top face is at z = 12.220. Two objects, one
plane, complete overlap — the worst case there is, and invisible to any check
that looks at one mesh at a time.

WHAT IT IS NOT. Faces that are merely close, and faces that are coplanar but do
not overlap: a wordmark cut out of the panel it sits in is exactly coplanar and
perfectly fine, because the two never cover the same pixel. Faces pointing
OPPOSITE ways are also not it — with backface culling only one of them is ever
drawn.

AND WHAT NOBODY CAN SEE IS DROPPED, which is three quarters of it. A face
counts only if a ray reaches it from one of five viewpoints: the shot's own
elevation at four azimuths, plus straight down. Anything else is the inside of
a solid, the underside of a building on the asphalt it stands on, or a roof
between two towers — 88 000 m2 of perfect z-fight that no camera can ever be on
the wrong side of. Two things this got wrong on the way, both of which hid the
one fault it was written to find:

  A RAY FROM THE CENTROID IS NOT ENOUGH. A sign plate carries its own mark
  standing proud of the middle, so every ray from the centre hits that mark and
  the plate reports hidden. What flickers is the border around the mark, so the
  corners and edge midpoints are sampled too.
  QUANTISING THE PLANE OFFSET IS NOT ENOUGH. Rounding into 1.5 mm cells splits
  two faces at identical heights whenever that height lands near a cell edge,
  and floating point puts it there often. Sort by offset and cluster by gap
  instead; it cannot do that.
"""
import sys, pathlib, math
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy
from mathutils import Vector
from _common import open_city, AZIMUTH, ELEVATION

GAP = 0.0015        # metres: closer than this is the same plane, 1.5 mm
NORMAL = 2          # decimals the normal is quantised to
# A face smaller than this is under a pixel in the frame the film ships at
# (170 m across 1920 px is 89 mm per pixel, so a pixel is 0.008 m2), and
# fighting under a pixel is not what anybody is looking at. It also keeps the
# hash down from 1.5 M faces to something Python can hold. --all lifts it.
MIN_AREA = 0.05


def tri_overlap(a, b):
    """Do these two 2D triangles share any area? Separating axis theorem.

    Touching along an edge is not overlapping: the tolerance is negative so
    that tiled faces — which this city has everywhere — do not report.
    """
    for tri in (a, b):
        for i in range(3):
            p, q = tri[i], tri[(i + 1) % 3]
            axis = (-(q[1] - p[1]), q[0] - p[0])
            n = math.hypot(*axis)
            if n < 1e-12:
                continue
            axis = (axis[0] / n, axis[1] / n)
            pa = [v[0] * axis[0] + v[1] * axis[1] for v in a]
            pb = [v[0] * axis[0] + v[1] * axis[1] for v in b]
            if min(pa) >= max(pb) - 1e-6 or min(pb) >= max(pa) - 1e-6:
                return False
    return True


def tri_area(t):
    """Area of a 2D triangle, for ranking a fault by how much of it there is."""
    (ax, ay), (bx, by), (cx, cy) = t
    return abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay)) / 2.0


def plane_basis(n):
    """Two axes spanning the plane, so triangles on it can be compared in 2D."""
    up = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    u = n.cross(up).normalized()
    return u, n.cross(u).normalized()


# Towards the camera, from the canonical orbit. Several directions rather
# than one: the film only ever shoots 45 degrees, but free orbit in the browser goes
# all the way round, and a fault that only shows from the north is still a
# fault. ELEVATION is the film's; anything the free camera can drop to sees
# MORE of the city's sides, not less.
def _eyes():
    e = math.radians(ELEVATION)
    for az in (AZIMUTH, AZIMUTH + 90, AZIMUTH + 180, AZIMUTH + 270):
        a = math.radians(az)
        yield Vector((math.cos(a) * math.cos(e),
                      math.sin(a) * math.cos(e), math.sin(e)))
    # AND STRAIGHT DOWN, which is not a nicety. A roof 12 m up between 30 m
    # towers is blocked from every one of the four side views, and it is the
    # single most visible surface in a city shot from above — the first version
    # of this filter dropped the 40 m2 roof mark that started the whole
    # investigation.
    yield Vector((0.0, 0.0, 1.0))


EYES = None


def hidden(scene, dg, tri, normal):
    """Is there anything between this face and the camera?

    THE QUESTION IS VISIBILITY, NOT TOPOLOGY. An earlier version asked whether
    a face was inside its own solid, which is a different question and answers
    the wrong one loudest: the undersides of every glass tower are coplanar
    with the asphalt they stand on, 88 000 m2 of perfect z-fight that nobody
    can ever be on the wrong side of, because the tower is in the way. One ray
    towards the camera settles it — and settles the interior faces too, since
    a face inside a solid is a face with the solid in front of it.
    """
    global EYES
    if EYES is None:
        EYES = list(_eyes())
    centre = (tri[0] + tri[1] + tri[2]) / 3.0
    # SAMPLE THE WHOLE FACE, not just the middle of it. A sign plate carries
    # its own mark standing 10 cm proud of the centre, so every ray fired from
    # anywhere near the middle hits that mark and the plate reports hidden —
    # which is how the 40 m2 fault this check was written for went missing
    # three times running. What flickers is the BORDER around the mark, so the
    # corners and the edge midpoints have to be asked too.
    edges = [(tri[i] + tri[(i + 1) % 3]) / 2.0 for i in range(3)]
    points = [centre]
    points += [centre + (v - centre) * 0.95 for v in tri]
    points += [centre + (e - centre) * 0.9 for e in edges]
    for d in EYES:
        if d.dot(normal) <= 0.05:
            continue                      # facing away from this viewpoint
        for o in points:
            hit, _, _, _, _, _ = scene.ray_cast(dg, o + d * 0.01, d)
            if not hit:
                return False              # this one can see it
    return True


def main():
    scene = open_city()
    dg = bpy.context.evaluated_depsgraph_get()
    everything = "--all" in sys.argv
    min_area = 0.0 if everything else MIN_AREA

    # --- one pass over the city, hashed by plane ---------------------------
    planes = defaultdict(list)
    faces = 0
    # THE VIEW LAYER, NOT THE SCENE. The kit's assets are all modelled at the
    # origin, one inside another, and its collection is excluded from the view
    # layer precisely because none of it is drawn. Walking scene.objects put
    # every bus inside every coach and reported 394 000 pairs, all of them at
    # (-4.2, -0.4, 1.4), which is the inside of a kit nobody renders.
    kit = bpy.data.collections.get("KIT")
    kit_members = {o.name for o in kit.all_objects} if kit else set()
    for ob in bpy.context.view_layer.objects:
        if ob.type != "MESH" or not ob.data.polygons or ob.hide_render:
            continue
        if ob.name in kit_members:
            continue
        me = ob.data
        mw, nm = ob.matrix_world, ob.matrix_world.to_3x3()
        mats = [m.name if m else "?" for m in me.materials] or ["?"]
        me.calc_loop_triangles()
        for t in me.loop_triangles:
            if t.area < min_area:
                continue
            n = (nm @ t.normal).normalized()
            p = [mw @ me.vertices[i].co for i in t.vertices]
            faces += 1
            key = (round(n.x, NORMAL), round(n.y, NORMAL), round(n.z, NORMAL))
            who = (ob.name, mats[min(t.material_index, len(mats) - 1)])
            planes[key].append((n.dot(p[0]), who, p, n))

    # CLUSTERED ALONG THE NORMAL, NOT QUANTISED. Rounding the offset into
    # 1.5 mm cells splits two faces that sit at exactly the same height
    # whenever that height lands near a cell boundary, and floating point puts
    # it there often enough that the 40 m2 roof mark this check was written for
    # went missing three times running. Sorting and grouping by gap cannot do
    # that.
    groups = []
    for key, entries in planes.items():
        entries.sort(key=lambda e: e[0])
        run = [entries[0]]
        for e in entries[1:]:
            if e[0] - run[-1][0] <= GAP:
                run.append(e)
            else:
                if len(run) > 1:
                    groups.append(run)
                run = [e]
        if len(run) > 1:
            groups.append(run)

    print(f"\n  {faces} faces over {min_area} m2, {len(planes)} orientations, "
          f"{len(groups)} shared planes")

    # --- and then only the planes that carry more than one thing -----------
    report = defaultdict(lambda: [0, None, 0.0])
    checked = skipped = 0
    for entries in groups:
        # DOWNWARD FACES CANNOT FLICKER, because this camera is never below
        # 24 degrees above the ground and backface culling drops them anyway.
        # Without this the loudest entry in the report was the underside of
        # every building fighting the asphalt it stands on: 88 000 m2 of a
        # plane no one can be on the wrong side of.
        if entries[0][3].z < -0.05:
            continue
        by_who = defaultdict(list)
        for _, who, p, n in entries:
            by_who[who].append((p, n))
        if len(by_who) < 2:
            continue                      # one material fighting itself
        names = sorted(by_who)
        u, v = plane_basis(entries[0][3])
        flat = {w: [[(q.dot(u), q.dot(v)) for q in p] for p, _ in tris]
                for w, tris in by_who.items()}
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                hit, area = None, 0.0
                for ai, ta in enumerate(flat[a]):
                    for tb in flat[b]:
                        if tri_overlap(ta, tb):
                            # The smaller of the two: the overlap cannot be
                            # bigger than that, and it is the number that says
                            # how much of the screen tears.
                            area += min(tri_area(ta), tri_area(tb))
                            if hit is None:
                                hit = ai
                            break
                if hit is None:
                    continue
                checked += 1
                p, n = by_who[a][hit]
                centre = (p[0] + p[1] + p[2]) / 3.0
                if hidden(scene, dg, p, n):
                    skipped += 1
                    continue
                pair = (f"{a[0]}/{a[1]}", f"{b[0]}/{b[1]}")
                entry = report[tuple(sorted(pair))]
                entry[0] += 1
                entry[1] = entry[1] or centre
                # AREA, not the number of triangles, is what ranks these. The
                # worst fault in the city — a 40 m2 sign plate flush with the
                # roof it lies on — is two triangles, and sorting by count
                # buried it under the stadium's nineteen tiny ones.
                entry[2] += area

    print(f"  {checked} overlapping pairs, {skipped} of them hidden behind "
          f"something")

    if not report:
        print("\n  nothing visible fights for a plane. Nothing can flicker.\n")
        return

    total = sum(e[0] for e in report.values())
    print(f"\n  {len(report)} pairs fight for the same plane, "
          f"{total} face pairs, worst first by area:\n")
    for (a, b), (count, where, area) in sorted(report.items(),
                                               key=lambda kv: -kv[1][2])[:30]:
        w = f"({where.x:7.1f},{where.y:7.1f},{where.z:6.1f})" if where else ""
        print(f"    {area:9.2f} m2  {count:4d} faces  {a:30s} vs {b:30s} {w}")

    print("\n  Fix these where they are built, by sinking the detail into its "
          "backing\n  by _common.SINK. 10_signs.mark() is the worked "
          "example.\n")


main()
