"""Check that nothing is standing inside a building.

A tree growing out of an office wall is the failure this catches. It raises no
exception, it does not show from every angle, and from the hero camera it hides
behind the very wall it is inside, so it survives review indefinitely.

Three tests, from cheap to honest.

TEST A — footprints. Every loose instance is checked against the rectangles
that steps 04 and 06 publish in city_solids.json. This is the same query step
05 makes before placing anything, so a failure here means the two disagree:
either a footprint stopped being published or something was placed without
asking. It is the test that would go quiet if the whole mechanism broke, which
is why the count of published footprints is printed whether it passes or not.

TEST B — real triangles. Instance against building, by BVH overlap, in world
space. This is the ground truth: it does not care what anybody published, and
it catches the cases the rectangle misses, such as a canopy leaning over a
parapet or a car clipping a garage column.

Resting contact is not intersection. Every tested instance is lifted 5 cm
before the query, because a roof unit sits with its bottom face exactly on the
roof plate and coplanar triangles report as overlapping. Without the lift this
test reported all 300-odd roof props as errors on its first run.

TEST C — the big meshes against each other. Buildings, landmarks and the title
are three separate objects, so a crane jib swinging through a neighbour's
facade belongs to nobody and no per-instance test will ever see it.

    ./bl scripts/city/99_check_overlap.py
"""
import sys, pathlib, math

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from _solids import Solids
from _common import open_city, R, LOTS, SOLIDS

EPS = 0.05                       # lift before testing: contact is not overlap
SUPPORTS = ("buildings", "landmarks", "porteno")
LOOSE = ("NATURE", "FURNITURE", "TRAFFIC", "PEOPLE", "ROOFPEOPLE",
         "ROOFPROPS", "LANDMARK_PROPS", "SIGNS")
# ROOFPROPS and LANDMARK_PROPS stand inside a building footprint on purpose -
# that is what a roof is - so the rectangle test would report every one of them
# FURNITURE is not in this list. A traffic light is a 6 m arm cantilevered
# over the road and a street light is a 3 m one, so their vertices are
# legitimately above ground that belongs to somebody: the plan test cannot
# tell that from an error and TEST B can, so TEST B owns them.
GROUNDED = ("NATURE", "TRAFFIC", "PEOPLE")
_sample = {}


def sample(ob):
    """Up to 16 of the object's own vertices, in world space.

    Two earlier versions modelled the object as a disc of some radius and both
    were wrong in the same direction: a traffic light is a 6 m cantilever arm
    over the road and a 6 m disc swallows the building behind it, so 105
    healthy signals were reported as errors. The vertices are not a model of
    the object, they are the object.
    """
    if ob.data.name not in _sample:
        vs = ob.data.vertices
        step = max(1, len(vs) // 16)
        _sample[ob.data.name] = [vs[i].co.copy() for i in range(0, len(vs), step)]
    mw = ob.matrix_world
    return [mw @ p for p in _sample[ob.data.name]]


def tris(me):
    """Triangles by vertex index. The meshes here are full of n-gons: prism
    caps and arc bands are single faces with up to 98 corners, and BVHTree
    only takes triangles and quads."""
    me.calc_loop_triangles()
    return [tuple(lt.vertices) for lt in me.loop_triangles]


def world_bvh(obs, lift=0.0):
    verts, faces = [], []
    for ob in obs:
        mw = ob.matrix_world
        n = len(verts)
        verts.extend((mw @ v.co) + Vector((0, 0, lift)) for v in ob.data.vertices)
        faces.extend(tuple(i + n for i in t) for t in tris(ob.data))
    return BVHTree.FromPolygons(verts, faces), verts, faces


def where(verts, faces, idx):
    a, b, c = (verts[i] for i in faces[idx])
    p = (a + b + c) / 3
    return f"({p.x:7.1f},{p.y:7.1f},{p.z:6.1f})"


def main():
    open_city(needs_collections=('BUILDINGS',),
              hint="run the chain in CLAUDE.md first")
    # Frame 1, always, and said out loud because it matters: this file may be
    # left on any frame by the step that ran last, and the vehicles are
    # animated. Reading "the current frame" makes the result depend on where
    # somebody happened to leave the playhead.
    bpy.context.scene.frame_set(1)
    scene = bpy.context.scene

    solids = Solids.load(SOLIDS)
    print(f"\n  {len(solids.boxes)} footprints published by steps 04 and 06")

    supports = [bpy.data.objects[n] for n in SUPPORTS if n in bpy.data.objects]
    # TitleRoot is an Empty and has no mesh to test
    title = [o for o in bpy.data.collections["TITLE"].objects
             if o.type == "MESH"] if "TITLE" in bpy.data.collections else []

    # --- TEST A ------------------------------------------------------------
    inside = []
    for cname in GROUNDED:
        if cname not in bpy.data.collections:
            continue
        for ob in bpy.data.collections[cname].objects:
            if ob.type != "MESH" or ob.hide_render:
                continue
            box = next((b for b in (solids.hit(p.x, p.y, p.z)
                                    for p in sample(ob)) if b), None)
            if box is not None:
                inside.append((cname, ob.name, ob.location.x, ob.location.y,
                               box[7]))

    print(f"\n  TEST A  loose objects inside a published footprint")
    if inside:
        print(f"    FAIL: {len(inside)}")
        for cname, name, x, y, tag in inside[:20]:
            print(f"      {cname:10s} {name:24s} at ({x:7.1f},{y:7.1f})  "
                  f"in a {tag} footprint")
        if len(inside) > 20:
            print(f"      ... and {len(inside) - 20} more")
    else:
        print("    pass: nothing loose is standing in a footprint")

    # --- TEST B ------------------------------------------------------------
    if not supports:
        print("\n  TEST B  skipped: no building mesh in the file")
        return
    solid_bvh, sv, sf = world_bvh(supports + title)
    print(f"\n  TEST B  {len(sf)} building triangles to test against")

    hits, tested = [], 0
    for cname in LOOSE:
        if cname not in bpy.data.collections:
            continue
        for ob in bpy.data.collections[cname].objects:
            if ob.type != "MESH" or ob.hide_render or not ob.data.vertices:
                continue
            tested += 1
            bvh, v, f = world_bvh([ob], EPS)
            pairs = bvh.overlap(solid_bvh)
            if pairs:
                hits.append((len(pairs), cname, ob.name,
                             where(sv, sf, pairs[0][1])))
    hits.sort(reverse=True)

    print(f"          {tested} loose objects tested")
    if hits:
        print(f"    FAIL: {len(hits)} intersect a building")
        for n, cname, name, pos in hits[:20]:
            print(f"      {n:5d} triangle pairs  {cname:10s} {name:22s} {pos}")
        if len(hits) > 20:
            print(f"      ... and {len(hits) - 20} more")
    else:
        print("    pass: no loose object intersects a building")

    # --- TEST C ------------------------------------------------------------
    groups = [(n, [o for o in supports if o.name == n]) for n in SUPPORTS]
    groups.append(("title", title))
    groups = [(n, g) for n, g in groups if g]
    print(f"\n  TEST C  the {len(groups)} big meshes against each other")
    bad = []
    # each group twice: flat, and lifted by the same 5 cm TEST B uses. A
    # cupola rests its drum on a roof plate and the two are coplanar there,
    # which reported as 812 intersecting triangles until one side was lifted.
    built = {n: world_bvh(g) for n, g in groups}
    high = {n: world_bvh(g, EPS) for n, g in groups}
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            na, nb = groups[i][0], groups[j][0]
            ba, va, fa = built[na]
            bb, vb, fb = high[nb]
            pairs = ba.overlap(bb)
            if pairs:
                bad.append((len(pairs), na, nb, where(va, fa, pairs[0][0])))
    if bad:
        print(f"    FAIL: {len(bad)} pairs touch")
        for n, na, nb, pos in bad:
            print(f"      {n:6d} triangle pairs   {na} x {nb}   near {pos}")
    else:
        print("    pass: they do not touch")
    print()


main()
