"""Is the traffic on the right side of the road, and on the road at all?

Two failures that this city produced, neither of which raises an exception and
neither of which looks wrong in a still frame:

ONE. Everything drove on the left. The lane table in step 05 is written once
and used for both axes, and the two axes have opposite handedness about the
offset sign: heading +x the driver's right hand points at -y, heading +y it
points at +x. So one axis came out correct and the other came out British, and
every individual street looked completely plausible. You can only see it by
picking one car and following it, or by counting.

TWO. The street tables are per axis and were being read on the wrong axis, so
the four-lane markings of an avenue were painted down a 12 m local street. It
is off by 5 to 6 m, which is less than a lane width, so every street still read
as a street and 46 vehicles were quietly driving along the pavement.

Both are the same class of bug as the trees inside buildings: invisible from
the hero angle, obvious to arithmetic. So this counts.

    ./bl scripts/city/95_check_traffic.py
"""
import sys, pathlib, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy

R = ROOT / "renders"
COLECTIVO = "Colectivo"


def nearest(value, table):
    return min(table, key=lambda s: abs(s - value))


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    data = json.loads((R / "city_lots.json").read_text())
    av = data.get("avenue9j")
    lots = [(l["x"], l["y"], l["size"][0], l["size"][1]) for l in data["lots"]]

    vehicles = [ob for ob in bpy.data.objects
                if ob.type == "MESH" and "axis" in ob]
    print(f"\n  {len(vehicles)} moving vehicles\n")

    # -- TEST A: which side of the street ----------------------------------
    # A street running along X is at a Y coordinate, so its centre comes out of
    # the Y table. On the 9 de Julio the unit is not the street but the
    # carriageway: each lateral is one way, so the sign that has to agree with
    # the direction is the side of the avenue the carriageway is on.
    wrong, checked = [], 0
    for ob in vehicles:
        axis, lane, d = int(ob["axis"]), float(ob["lane"]), int(ob["dir"])
        if av is not None and axis == 1 and abs(lane - av["x"]) < av["width"] / 2:
            side = 1 if lane > av["x"] else -1
            # inside a one-way carriageway every lane goes the same way, so
            # what is being asked is whether the carriageway is on the correct
            # side of the avenue for the way it runs
            ok = (d * side) > 0
        else:
            table = data["streets_y"] if axis == 0 else data["streets_x"]
            centre = nearest(lane, table)
            offset = lane - centre
            if abs(offset) < 0.5:
                continue                     # dead on the centre line: no side
            # right-hand traffic: heading +x you are at -y, heading +y at +x
            ok = (d * offset) < 0 if axis == 0 else (d * offset) > 0
        checked += 1
        if not ok:
            wrong.append((ob.name, axis, round(lane, 2), d))

    print(f"  TEST A  which side of the road, {checked} vehicles")
    if wrong:
        print(f"    FAIL: {len(wrong)} driving on the left")
        for row in wrong[:10]:
            print(f"      {row[0]:22s} axis {row[1]}  lane {row[2]:8.2f}"
                  f"  dir {row[3]:+d}")
    else:
        print("    pass: everything is on the right, which is the Argentine side")

    # -- TEST B: on the road at all ----------------------------------------
    def depth(x, y):
        best = -1e9
        for (cx, cy, w, d) in lots:
            best = max(best, min(w / 2 - abs(x - cx), d / 2 - abs(y - cy)))
        return best

    on_block = []
    for ob in vehicles:
        dp = depth(ob.location.x, ob.location.y)
        if dp > 0.0:
            on_block.append((round(dp, 2), ob.name))
    on_block.sort(reverse=True)
    print(f"\n  TEST B  on the carriageway, not the pavement")
    if on_block:
        print(f"    FAIL: {len(on_block)} vehicles standing inside a block")
        for dp, n in on_block[:10]:
            print(f"      {n:22s} {dp:5.2f} m in")
    else:
        print("    pass: nothing is driving on a pavement")

    # -- TEST C: the busway is for buses -----------------------------------
    print(f"\n  TEST C  the Metrobus corridor")
    if av is None:
        print("    skipped: no avenue in this layout")
        return
    intruders, buses = [], 0
    for ob in vehicles:
        if int(ob["axis"]) != 1:
            continue
        if abs(float(ob["lane"]) - av["x"]) > av["busway"]:
            continue
        buses += 1
        if COLECTIVO not in ob.data.name:
            intruders.append(ob.name)
    if intruders:
        print(f"    FAIL: {len(intruders)} things in the bus lanes that are "
              f"not buses")
        for n in intruders[:10]:
            print(f"      {n}")
    else:
        print(f"    pass: {buses} buses in the corridor and nothing else")


main()
