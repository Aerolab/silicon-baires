"""Step 05 — nature, street furniture and population.

All instances out of the KIT. Rewritten for the straight grid: everything here
is driven by the street and block tables that step 03 writes, so there is no
second copy of the layout to drift out of sync.

    ./bl scripts/city/05_life.py
"""
import sys, pathlib, math, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from _common import collection, instance, mat, rng, counts

R = ROOT / "renders"

TREES = ["Tree0", "Tree1", "Tree2", "Tree3", "Conifer0", "Conifer1"]
CARS = ["CarRed", "CarWhite", "CarTeal", "CarBlue", "CarDark", "CarSilver"]
PEOPLE = [f"Person{i}" for i in range(8)]
AVENUE = 22.0


def street_trees(kit, coll, lots, r):
    """A row down every block edge, with gaps so it is not a regiment."""
    n = 0
    for lot in lots:
        cx, cy = lot["x"], lot["y"]
        w, d = lot["size"]
        lift = lot["lift"]
        for axis in (0, 1):
            length = w if axis == 0 else d
            edge = (d if axis == 0 else w) / 2 - 1.2
            span = length - 8.0
            count = max(1, int(span / 8.5))
            for side in (-1, 1):
                for k in range(count + 1):
                    if r.random() < 0.34:
                        continue
                    t = -span / 2 + k * span / count
                    x, y = ((cx + t, cy + side * edge) if axis == 0
                            else (cx + side * edge, cy + t))
                    instance(kit[r.choice(TREES)], coll,
                             (x + r.uniform(-1.6, 1.6),
                              y + r.uniform(-1.6, 1.6), lift),
                             r.uniform(0, 6.28), r.uniform(1.0, 1.5))
                    n += 1
    return n


def clump(kit, coll, cx, cy, rw, rd, lift, count, r):
    for _ in range(count):
        instance(kit[r.choice(TREES)], coll,
                 (cx + r.uniform(-rw, rw), cy + r.uniform(-rd, rd), lift),
                 r.uniform(0, 6.28), r.uniform(1.0, 1.8))


def planting(kit, coll, lots, r):
    for lot in lots:
        kind, lift = lot["kind"], lot["lift"]
        cx, cy = lot["x"], lot["y"]
        w, d = lot["size"]
        if kind == "park":
            clump(kit, coll, cx, cy, w * 0.42, d * 0.42, lift, 34, r)
            for _ in range(8):
                instance(kit["Shrub"], coll,
                         (cx + r.uniform(-w / 3, w / 3),
                          cy + r.uniform(-d / 3, d / 3), lift),
                         r.uniform(0, 6.28), r.uniform(0.9, 1.5))
            for _ in range(5):
                instance(kit["Bench"], coll,
                         (cx + r.uniform(-w / 3, w / 3),
                          cy + r.uniform(-d / 3, d / 3), lift),
                         r.uniform(0, 6.28))
        elif kind == "plaza":
            clump(kit, coll, cx, cy, w * 0.36, d * 0.36, lift, 12, r)
            for _ in range(3):
                instance(kit["Bench"], coll,
                         (cx + r.uniform(-w / 3, w / 3),
                          cy + r.uniform(-d / 3, d / 3), lift),
                         r.uniform(0, 6.28))
        elif kind == "parking":
            clump(kit, coll, cx, cy, w * 0.42, d * 0.42, lift, 8, r)


def lights_and_signals(kit, coll, data, r):
    n = 0
    walk = data["walk"]
    for axis in (0, 1):
        streets = data["streets_x"] if axis == 0 else data["streets_y"]
        widths = data["widths_x"] if axis == 0 else data["widths_y"]
        blocks = data["blocks_x"] if axis == 0 else data["blocks_y"]
        for s, w in zip(streets, widths):
            half = (w - walk * 2) / 2
            for (b, size) in blocks:
                for side in (-1, 1):
                    for t in (-size * 0.28, size * 0.28):
                        off = s + side * (half + 1.1)
                        x, y = ((b + t, off) if axis == 0 else (off, b + t))
                        rot = (math.pi / 2 if axis == 0 else 0.0)
                        rot += math.pi if side > 0 else 0.0
                        instance(kit["StreetLight"], coll, (x, y, 0.0), rot)
                        n += 1

    for sx, wx in zip(data["streets_x"], data["widths_x"]):
        for sy, wy in zip(data["streets_y"], data["widths_y"]):
            if max(wx, wy) < AVENUE and r.random() < 0.6:
                continue
            for k, (dx, dy) in enumerate(((1, 1), (-1, -1))):
                x = sx + dx * ((wx - walk * 2) / 2 + 1.4)
                y = sy + dy * ((wy - walk * 2) / 2 + 1.4)
                instance(kit["TrafficLight"], coll, (x, y, 0.0),
                         math.pi * (0.5 if k == 0 else 1.5))
                n += 1
    return n


def traffic(kit, coll, data, r):
    n = 0
    span = max(data["blocks_x"][-1][0], data["blocks_y"][-1][0]) + 60
    for axis in (0, 1):
        streets = data["streets_x"] if axis == 0 else data["streets_y"]
        widths = data["widths_x"] if axis == 0 else data["widths_y"]
        for s, w in zip(streets, widths):
            lanes = ((-5.25, -1), (-1.75, -1), (1.75, 1), (5.25, 1)) \
                if w >= AVENUE else ((-1.75, -1), (1.75, 1))
            for lane, direction in lanes:
                pos = -span
                while pos < span:
                    pos += r.uniform(13.0, 44.0)
                    x, y = ((pos, s + lane) if axis == 0 else (s + lane, pos))
                    name = r.choice(["Bus", "Truck"]) if r.random() < 0.08 \
                        else r.choice(CARS)
                    rot = 0.0 if axis == 0 else math.pi / 2
                    if direction < 0:
                        rot += math.pi
                    instance(kit[name], coll, (x, y, 0.0), rot)
                    n += 1
    return n


def parked(kit, coll, lots, r):
    n = 0
    for lot in lots:
        if lot["kind"] != "parking":
            continue
        cx, cy = lot["x"], lot["y"]
        w, d = lot["size"]
        for row in range(3):
            y = cy - d / 2 + 7 + row * (d - 14) / 2
            count = max(4, int((w - 5) / 2.6))
            for k in range(count):
                if r.random() < 0.15:
                    continue
                x = cx - w / 2 + 3.8 + k * (w - 5) / (count - 1)
                instance(kit[r.choice(CARS)], coll, (x, y, lot["lift"] + 0.02),
                         math.pi / 2)
                n += 1
    return n


def crowds(kit, coll, lots, data, r):
    n = 0
    for lot in lots:                                   # along the pavements
        cx, cy = lot["x"], lot["y"]
        w, d = lot["size"]
        for _ in range(r.randint(14, 30)):
            axis, side = r.randint(0, 1), r.choice((-1, 1))
            length = w if axis == 0 else d
            edge = (d if axis == 0 else w) / 2 - r.uniform(0.5, 2.2)
            t = r.uniform(-length / 2 + 4, length / 2 - 4)
            x, y = ((cx + t, cy + side * edge) if axis == 0
                    else (cx + side * edge, cy + t))
            instance(kit[r.choice(PEOPLE)], coll, (x, y, lot["lift"]),
                     r.uniform(0, 6.28))
            n += 1
        if lot["kind"] in ("park", "plaza"):
            for _ in range(r.randint(10, 22)):
                instance(kit[r.choice(PEOPLE)], coll,
                         (cx + r.uniform(-w / 3, w / 3),
                          cy + r.uniform(-d / 3, d / 3), lot["lift"]),
                         r.uniform(0, 6.28))
                n += 1

    for sx in data["streets_x"]:                       # knots at the crossings
        for sy in data["streets_y"]:
            if r.random() < 0.3:
                continue
            for _ in range(r.randint(3, 9)):
                a, dd = r.uniform(0, 6.28), r.uniform(9.0, 16.0)
                instance(kit[r.choice(PEOPLE)], coll,
                         (sx + dd * math.cos(a), sy + dd * math.sin(a), 0.0),
                         r.uniform(0, 6.28))
                n += 1
    return n


def rooftop_people(kit, coll, r):
    n = 0
    for ob in list(bpy.data.collections["ROOFPROPS"].objects):
        if r.random() < 0.10:
            for _ in range(r.randint(1, 3)):
                instance(kit[r.choice(PEOPLE)], coll,
                         (ob.location.x + r.uniform(-2.0, 2.0),
                          ob.location.y + r.uniform(-2.0, 2.0), ob.location.z),
                         r.uniform(0, 6.28))
                n += 1
    return n


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    kit = {ob.name: ob for ob in bpy.data.collections["KIT"].objects}
    data = json.loads((R / "city_lots.json").read_text())
    lots = data["lots"]

    for name in ("NATURE", "FURNITURE", "TRAFFIC", "PEOPLE"):
        if name in bpy.data.collections:
            c = bpy.data.collections[name]
            for ob in list(c.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
    nat = collection("NATURE")
    fur = collection("FURNITURE")
    tra = collection("TRAFFIC")
    ppl = collection("PEOPLE")

    r = rng(31337)
    street_trees(kit, nat, lots, r)
    planting(kit, nat, lots, r)
    li = lights_and_signals(kit, fur, data, r)
    ca = traffic(kit, tra, data, r) + parked(kit, tra, lots, r)
    pe = crowds(kit, ppl, lots, data, r) + rooftop_people(kit, ppl, r)

    print(f"\n  trees {len(nat.objects)}  furniture {li}  cars {ca}  people {pe}")
    u, t = counts()
    print(f"  triangles: {u} unique / {t} total   objects {len(bpy.data.objects)}")

    cam = bpy.data.objects["HeroCam"]
    exposure = bpy.context.scene.view_settings.exposure
    cam.data.ortho_scale = 200.0
    blib.render(str(R / "city_05_closeup.png"), "EEVEE", samples=64,
                resolution=(1600, 900), exposure=exposure)
    blib.save(str(R / "city.blend"))


main()
