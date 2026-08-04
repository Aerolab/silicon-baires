"""Check that nothing green is standing in the road.

A tree in the middle of the carriageway is the failure this catches. Like the
tree inside a building it raises no exception, and it is worse to spot by eye:
it is a tree, it is upright, it is the right size, and the only thing wrong
with it is the two metres of asphalt it is standing on. Four of them stood
beside the Obelisco through a dozen renders.

The question is answered against the ground itself, not against the street
tables. A ray is dropped from above each object and the material of the first
face it meets is the surface that object is standing on: asphalt or busway
means the road, anything else is kerb, pavement, lawn, paving or car park. That
is deliberately a different mechanism from the one that places the trees - a
check that reads the same tables the placement read can only ever confirm the
arithmetic, and the arithmetic was not the thing that was wrong. Here, step 03
built no median across the plaza block and step 05 planted one anyway; both
tables were correct.

Nothing under the ray at all is a failure too. It means the object is off the
edge of the site, which is the same error read from the other side.

    ./bl scripts/city/94_check_road.py
"""
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy
from mathutils import Vector

R = ROOT / "renders"
# Where a vehicle belongs and a tree does not. "Asphalt Lot" is not here: that
# is the surface of a car park, which is inside a block, and the planting in
# those is on purpose.
ROAD = ("Asphalt", "Busway")
# The collections of things that are meant to stand on a block. FURNITURE is
# not one of them: a street light stands at the kerb line and a traffic light
# is a mast on the corner of the carriageway, so both legitimately measure as
# road. TRAFFIC belongs there by definition, and 95_check_traffic owns it.
GROWN = ("NATURE",)


def surfacer(site):
    """What is directly under (x, y), by name of material."""
    mats = [m.name if m else "?" for m in site.data.materials]
    inv = site.matrix_world.inverted()
    down = (inv.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()

    def under(x, y):
        ok, loc, nor, idx = site.ray_cast(inv @ Vector((x, y, 400.0)), down)
        if not ok:
            return None
        return mats[site.data.polygons[idx].material_index]

    return under


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    # frame 1, for the same reason 99_check_overlap says so out loud: this file
    # is left on whatever frame ran last, and half the scene is animated
    bpy.context.scene.frame_set(1)

    if "site" not in bpy.data.objects:
        raise SystemExit("no site mesh: run 03_ground.py first")
    under = surfacer(bpy.data.objects["site"])

    tally, bad, tested = {}, [], 0
    for cname in GROWN:
        if cname not in bpy.data.collections:
            continue
        for ob in bpy.data.collections[cname].objects:
            if ob.type != "MESH" or ob.hide_render:
                continue
            tested += 1
            s = under(ob.location.x, ob.location.y)
            tally[s] = tally.get(s, 0) + 1
            if s is None or s in ROAD:
                bad.append((ob.name, ob.location.x, ob.location.y,
                            ob.location.z, s or "nothing at all"))

    # printed whether it passes or not: a check that goes quiet when its
    # mechanism breaks reads exactly like a check that passes
    print(f"\n  {tested} objects tested, on:")
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"    {str(k):14s} {v:5d}")

    print("\n  nothing planted in the road")
    if bad:
        print(f"    FAIL: {len(bad)}")
        for name, x, y, z, s in sorted(bad, key=lambda t: t[2])[:20]:
            print(f"      {name:24s} at ({x:7.1f},{y:7.1f}, z={z:5.2f})"
                  f"  standing on {s}")
        if len(bad) > 20:
            print(f"      ... and {len(bad) - 20} more")
    else:
        print("    pass: every tree, shrub and bench is on a block or a median")
    print()


main()
