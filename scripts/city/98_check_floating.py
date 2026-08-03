"""Check for anything floating or buried.

Looking at renders does not prove nothing floats: a crane mast rotated into the
ground read as a foreshortened jib for a dozen frames before anyone caught it.
This measures instead. Two tests, because the two failures are different.

TEST A — buried geometry. Every asset in this project is modelled sitting on
z = 0, so any vertex below the ground is a modelling or orientation error. This
is the one that catches the crane: its mast ran from 0 down to -44.

TEST B — floating instances. Trees, cars, people, street furniture and roof
units are whole assets whose origin is their point of contact, so the question
"is there a surface right under it" is meaningful for them. The ray is cast
against the site, the buildings and the landmarks specifically, never against
the asset itself, so nothing can shadow its own test. The AIR collection is
exempt: the helicopter in it is supposed to be 78 m off the ground.

Deliberately NOT tested: individual pieces inside the merged building mesh. A
facade band has nothing directly under it by design, and testing it produced
65,000 false positives on the first attempt.

    ./bl scripts/city/98_check_floating.py
"""
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import bpy
from mathutils import Vector

R = ROOT / "renders"
BURIED = -0.25            # metres below ground before we call it buried
GAP = 0.4                 # metres of air under an instance before it floats
SUPPORTS = ("site", "buildings", "landmarks", "porteno")
# the one collection whose whole point is that it is not resting on anything
AIRBORNE = "AIR"


def world_min_z(ob):
    mw = ob.matrix_world
    return min((mw @ v.co).z for v in ob.data.vertices) if ob.data.vertices \
        else 0.0


def local_min_z(me):
    return min(v.co.z for v in me.vertices) if me.vertices else 0.0


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    # Frame 1, always, and said out loud because it matters: this file may be
    # left on any frame by the step that ran last, and the vehicles are
    # animated. Reading "the current frame" makes the result depend on where
    # somebody happened to leave the playhead.
    bpy.context.scene.frame_set(1)
    scene = bpy.context.scene
    kit = {ob.data.name for ob in bpy.data.collections["KIT"].objects}
    supports = [bpy.data.objects[n] for n in SUPPORTS if n in bpy.data.objects]
    print(f"  supports: {[s.name for s in supports]}")

    # --- TEST A ------------------------------------------------------------
    buried = []
    for ob in scene.objects:
        if ob.type != "MESH":
            continue
        z = world_min_z(ob)
        if z < BURIED:
            buried.append((z, ob.name))
    buried.sort()

    # --- TEST B ------------------------------------------------------------
    base_cache = {}
    floating, tested = [], 0
    for ob in scene.objects:
        if ob.type != "MESH" or ob.hide_render or ob.data.name not in kit:
            continue
        if any(c.name == AIRBORNE for c in ob.users_collection):
            continue
        if ob.data.name not in base_cache:
            base_cache[ob.data.name] = local_min_z(ob.data)
        z_base = (ob.matrix_world @ Vector((0, 0, base_cache[ob.data.name]))).z
        tested += 1
        if z_base <= 0.12:                      # resting on the asphalt sheet
            continue
        origin = Vector((ob.location.x, ob.location.y, z_base + 0.6))
        best = None
        for sup in supports:
            inv = sup.matrix_world.inverted()
            hit, loc, _, _ = sup.ray_cast(inv @ origin,
                                          (inv.to_3x3() @ Vector((0, 0, -1))))
            if hit:
                wz = (sup.matrix_world @ loc).z
                if wz <= z_base + 0.05 and (best is None or wz > best):
                    best = wz
        gap = z_base - best if best is not None else z_base
        if gap > GAP:
            floating.append((gap, ob.name, ob.location.x, ob.location.y,
                             z_base))
    floating.sort(reverse=True)

    print(f"\n  TEST A  buried geometry, {len(scene.objects)} objects scanned")
    if buried:
        print(f"    FAIL: {len(buried)}")
        for z, name in buried[:15]:
            print(f"      {z:8.2f} m below ground   {name}")
    else:
        print("    pass: nothing below ground")

    print(f"\n  TEST B  floating instances, {tested} tested")
    if floating:
        print(f"    FAIL: {len(floating)}")
        for gap, name, x, y, z in floating[:25]:
            print(f"      {gap:7.2f} m of air   {name:22s} "
                  f"at ({x:7.1f},{y:7.1f},{z:6.1f})")
        if len(floating) > 25:
            print(f"      ... and {len(floating) - 25} more")
    else:
        print("    pass: every instance is resting on something")
    print()


main()
