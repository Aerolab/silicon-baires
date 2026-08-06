"""Check that the traffic does not drive through the crowd.

THE QUESTION IS NOT "IS ANYONE STANDING ON THE ASPHALT", and the difference is
the whole reason this file exists rather than a fourth branch of
94_check_road. Step 05 now places people by dropping a ray onto the site and
reading the material it lands on, so a check that drops the same ray can only
ever confirm that the placement ran - it is the circular check 94's own
docstring warns about, wearing a different hat.

So this one asks something no placement pass can answer, because it is not a
question about a position at all: over the 624 frames of the shot, does a
vehicle ever occupy the same two metres of street as a person? That is
dynamic, it reads the evaluated positions of both, and it is exactly the thing
that was wrong - 545 people were driven through and every standing check
passed, because none of them had ever looked at the crowd.

It reports three numbers, and only the first is a failure:

  RUN OVER      a vehicle passes through a person. Zero, always.
  IN THE ROAD   standing on a carriageway without being on a zebra. These are
                people, not crossers: somebody who is crossing is MEANT to be
                on the road, and the point of step 11's timing is that they
                are only there while nothing is coming.
  WAITING       at a kerb, never crossing, because no gap in the traffic was
                long enough. Not a failure - it is what a person does - but
                worth watching: all of them waiting means the timing found no
                gaps anywhere, which is a stuck solver rather than a busy city.

    ./bl scripts/city/91_check_crowd.py
"""
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy
from _common import open_city, surfacer, ROAD, FPS, FRAMES

# How much street a vehicle occupies, as half-extents in metres: along its own
# heading, and across it. Measured off the kit meshes. A colectivo is 11 m
# long, so one blanket box either misses the buses or accuses every car of
# running over the person in the next lane.
LONG = {"Colectivo": 5.7, "Bus": 5.6, "Truck": 4.2}
CAR_LONG, WIDE = 2.3, 1.15
# plus the person, who is about 0.25 m across. A contact is a contact: this is
# not a near-miss detector, and the margin is deliberately small so that the
# number it reports is one nobody can argue with.
BODY = 0.25

# 41 samples over 26 s is one every 0.63 s, and a car covers 7 m in that at
# avenue speed - so it CANNOT be stepped over. That is the check's resolution
# and it is worth stating: the person is 0.5 m wide, so a fine enough sample is
# the difference between counting a collision and missing it.
SAMPLES = 40
CELL = 12.0
# The height step 05 stands a Metrobus passenger at. Anyone at least this high
# is on a platform, not in the busway.
PLATFORM_LIFT = 0.40


def half_long(name):
    for k, v in LONG.items():
        if name.startswith(k):
            return v
    return CAR_LONG


def main():
    scene = open_city(needs_collections=("PEOPLE", "TRAFFIC"),
                      hint="run 05_life.py then 11_animate.py first")
    under = surfacer()

    people = [ob for ob in bpy.data.collections["PEOPLE"].objects
              if ob.type == "MESH" and not ob.hide_render]
    cars = [ob for ob in bpy.data.collections["TRAFFIC"].objects
            if ob.type == "MESH" and not ob.hide_render and "axis" in ob]
    crossers = [ob for ob in people if "cross" in ob]
    # a crosser with no location keyframes never found a gap
    waiting = [ob for ob in crossers
               if ob.animation_data is None or ob.animation_data.action is None]

    # --- standing in the road ------------------------------------------------
    # frame 1, like every other standing check: this file is left on whatever
    # frame ran last and half the scene is animated
    scene.frame_set(1)
    tally, parked_in_road = {}, []
    for ob in people:
        if "cross" in ob:
            continue                    # allowed on the road, and timed for it
        s = under(ob.location.x, ob.location.y)
        tally[s] = tally.get(s, 0) + 1
        # A METROBUS PLATFORM IS AN ISLAND IN THE BUSWAY, so a passenger
        # standing on one measures as road and is exactly where they should
        # be. Told apart by HEIGHT, which is a different question from the one
        # the placement asked: the platform is raised, the carriageway is not,
        # so anybody up there is on something rather than in the way of it.
        if ob.location.z >= PLATFORM_LIFT - 0.05:
            continue
        if s is None or s in ROAD:
            parked_in_road.append(ob)

    # --- run over ------------------------------------------------------------
    # A grid, because the honest version is 2900 people x 800 vehicles x 41
    # frames and Python will not do 95 million distance tests in a check
    # anybody actually runs.
    hits = {}
    for i in range(SAMPLES + 1):
        f = 1 + int((FRAMES - 1) * i / SAMPLES)
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()

        grid = {}
        for ob in cars:
            p = ob.evaluated_get(dg).matrix_world.translation
            grid.setdefault((int(p.x // CELL), int(p.y // CELL)),
                            []).append((p, ob))
        for pob in people:
            p = pob.evaluated_get(dg).matrix_world.translation
            cx, cy = int(p.x // CELL), int(p.y // CELL)
            for ax in (cx - 1, cx, cx + 1):
                for ay in (cy - 1, cy, cy + 1):
                    for cp, cob in grid.get((ax, ay), ()):
                        # the box is along the vehicle's own axis, not the
                        # world's: a bus is 11 m long down its lane and 2.3 m
                        # across it, and a square box of either size is wrong
                        along = abs(p.x - cp.x) if int(cob["axis"]) == 0 \
                            else abs(p.y - cp.y)
                        across = abs(p.y - cp.y) if int(cob["axis"]) == 0 \
                            else abs(p.x - cp.x)
                        if along < half_long(cob.name) + BODY and \
                                across < WIDE + BODY:
                            hits.setdefault(pob.name, set()).add(
                                (cob.name, f))
    scene.frame_set(1)

    # --- and say so ----------------------------------------------------------
    # printed whether it passes or not: a check that goes quiet when its
    # mechanism breaks reads exactly like a check that passes
    print(f"\n  {len(people)} people, {len(cars)} vehicles on the move")
    print(f"  {len(crossers)} at a zebra: {len(crossers) - len(waiting)} "
          f"crossed, {len(waiting)} waiting for a gap")
    print("\n  standing on (crossers excluded, they are meant to be on it):")
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"    {str(k):16s} {v:5d}")

    print("\n  nobody is standing in the road")
    if parked_in_road:
        print(f"    FAIL: {len(parked_in_road)}")
        for ob in parked_in_road[:12]:
            print(f"      {ob.name:24s} at ({ob.location.x:7.1f},"
                  f"{ob.location.y:7.1f})  on "
                  f"{under(ob.location.x, ob.location.y) or 'nothing at all'}")
    else:
        print("    pass")

    print("\n  nobody is driven through")
    if hits:
        print(f"    FAIL: {len(hits)} people hit during the shot")
        for name in sorted(hits)[:12]:
            veh = sorted({v for v, _ in hits[name]})
            frames = sorted({f for _, f in hits[name]})
            print(f"      {name:24s} by {', '.join(veh)[:44]} "
                  f"at frame {frames[0]}")
        if len(hits) > 12:
            print(f"      ... and {len(hits) - 12} more")
    else:
        print(f"    pass: {SAMPLES + 1} samples over {FRAMES / FPS:.0f} s, "
              f"no vehicle shares a body-width with anybody")
    print()


main()
