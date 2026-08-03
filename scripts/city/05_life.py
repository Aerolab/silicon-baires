"""Step 05 — nature, street furniture and population.

All instances out of the KIT. This is the layer that turns a set of massing
studies into a place: street tree rows following every block edge, clumps in
the parks, lights and signals at the junctions, traffic on the roads and people
clustered where people actually stand.

    ./bl scripts/city/05_life.py
"""
import sys, pathlib, math, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from _common import Mesh, collection, instance, mat, rng, counts

R = ROOT / "renders"

BLOCK, STREET, PITCH, WALK = 90.0, 22.0, 112.0, 4.0
EXTENT, HALF = 7, 3.0
CARRIAGE = STREET - WALK * 2
PLAZA_R, RING_R, SECTOR_R, CLEAR_R = 48.0, 70.0, 160.0, 172.0

TREES = ["Tree0", "Tree1", "Tree2", "Tree3", "Conifer0", "Conifer1"]
STREET_TREES = ["Tree0", "Tree1", "Tree3", "Tree0", "Tree1"]
CARS = ["CarRed", "CarWhite", "CarTeal", "CarBlue", "CarDark", "CarSilver"]
PEOPLE = [f"Person{i}" for i in range(8)]


def centres():
    return [(-HALF - 0.5 + k) * PITCH for k in range(EXTENT + 1)]


def in_circus(x, y, pad=0.0):
    return math.hypot(x, y) < CLEAR_R + pad


# --- nature ----------------------------------------------------------------
def street_trees(kit, coll, lots, r):
    n = 0
    for lot in lots:
        if lot["kind"] in ("sector", "island"):
            continue
        cx, cy, lift = lot["x"], lot["y"], lot["lift"]
        edge = BLOCK / 2 - 2.2
        for axis in (0, 1):
            for side in (-1, 1):
                span = BLOCK - 26.0
                count = int(span / 12.5)
                for k in range(count + 1):
                    t = -span / 2 + k * span / max(count, 1)
                    x, y = ((cx + t, cy + side * edge) if axis == 0
                            else (cx + side * edge, cy + t))
                    x += r.uniform(-0.8, 0.8)
                    y += r.uniform(-0.8, 0.8)
                    name = r.choice(STREET_TREES)
                    instance(kit[name], coll, (x, y, lift),
                             r.uniform(0, 6.28), r.uniform(0.8, 1.15))
                    n += 1
    return n


def clump(kit, coll, cx, cy, radius, lift, count, r, pool=None):
    for _ in range(count):
        a, d = r.uniform(0, 6.28), radius * math.sqrt(r.random())
        name = r.choice(pool or TREES)
        instance(kit[name], coll, (cx + d * math.cos(a), cy + d * math.sin(a),
                                   lift), r.uniform(0, 6.28),
                 r.uniform(0.75, 1.3))


def park_planting(kit, coll, lots, r):
    for lot in lots:
        kind = lot["kind"]
        cx, cy, lift = lot["x"], lot["y"], lot["lift"]
        if kind == "park":
            clump(kit, coll, cx, cy, BLOCK * 0.36, lift, 40, r)
            for _ in range(8):
                instance(kit["Shrub"], coll,
                         (cx + r.uniform(-35, 35), cy + r.uniform(-35, 35),
                          lift), r.uniform(0, 6.28), r.uniform(0.8, 1.4))
            for _ in range(4):
                instance(kit["Bench"], coll,
                         (cx + r.uniform(-30, 30), cy + r.uniform(-30, 30),
                          lift), r.uniform(0, 6.28))
        elif kind == "plaza":
            clump(kit, coll, cx, cy, BLOCK * 0.3, lift, 8, r)
            for _ in range(3):
                instance(kit["Bench"], coll,
                         (cx + r.uniform(-28, 28), cy + r.uniform(-28, 28),
                          lift), r.uniform(0, 6.28))
        elif kind == "parking":
            for _ in range(6):
                instance(kit[r.choice(STREET_TREES)], coll,
                         (cx + r.uniform(-38, 38), cy + r.uniform(-38, 38),
                          lift), r.uniform(0, 6.28), r.uniform(0.8, 1.1))
        elif kind == "island":
            clump(kit, coll, cx, cy, 18.0, lift, 12, r)
        elif kind == "sector":
            a0, a1, r0, r1 = lot["size"]
            for k in range(9):
                a = a0 + (a1 - a0) * (k + 0.5) / 9
                for rad in (r0 + 2.5, r1 - 2.5):
                    instance(kit[r.choice(STREET_TREES)], coll,
                             (rad * math.cos(a), rad * math.sin(a),
                              lot["lift"]), r.uniform(0, 6.28),
                             r.uniform(0.8, 1.1))


def circus_planting(kit, coll, r):
    lift = 1.17
    for k in range(30):
        a = 2 * math.pi * k / 30
        rad = PLAZA_R - 9.0
        instance(kit[r.choice(TREES)], coll,
                 (rad * math.cos(a), rad * math.sin(a), lift),
                 r.uniform(0, 6.28), r.uniform(0.85, 1.2))
    clump(kit, coll, 0, 0, 22.0, lift, 14, r)
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.4
        instance(kit["Bench"], coll,
                 (26 * math.cos(a), 26 * math.sin(a), lift), a)


# --- street furniture ------------------------------------------------------
def lights_and_signals(kit, coll, r):
    n = 0
    cs = centres()
    blocks = [(i - HALF) * PITCH for i in range(EXTENT)]
    for axis in (0, 1):
        for s in cs:
            for b in blocks:
                if in_circus(s if axis else b, b if axis else s, BLOCK * 0.4):
                    continue
                for side in (-1, 1):
                    for t in (-26.0, 26.0):
                        off = s + side * (CARRIAGE / 2 + 1.4)
                        x, y = ((b + t, off) if axis == 0 else (off, b + t))
                        rot = (math.pi / 2 if axis == 0 else 0.0)
                        rot += 0 if side > 0 else math.pi
                        instance(kit["StreetLight"], coll, (x, y, 0.0),
                                 rot + math.pi)
                        n += 1
    for sx in cs:
        for sy in cs:
            if in_circus(sx, sy, STREET):
                continue
            for k, (dx, dy) in enumerate(((1, 1), (-1, -1))):
                x = sx + dx * (CARRIAGE / 2 + 2.0)
                y = sy + dy * (CARRIAGE / 2 + 2.0)
                instance(kit["TrafficLight"], coll, (x, y, 0.0),
                         math.pi * (0.5 if k == 0 else 1.5))
                n += 1
            if r.random() < 0.4:
                instance(kit["SignPost"], coll,
                         (sx - dx * 9, sy + dy * 9, 0.0), r.uniform(0, 6.28))
    return n


# --- traffic ---------------------------------------------------------------
def traffic(kit, coll, r):
    n = 0
    cs = centres()
    for axis in (0, 1):
        for s in cs:
            for lane, direction in ((-3.6, -1), (3.6, 1)):
                pos = -EXTENT * PITCH / 2
                end = EXTENT * PITCH / 2
                while pos < end:
                    pos += r.uniform(14.0, 46.0)
                    x, y = ((pos, s + lane) if axis == 0 else (s + lane, pos))
                    if in_circus(x, y, 6.0):
                        continue
                    if r.random() < 0.08:
                        name = r.choice(["Bus", "Truck"])
                    else:
                        name = r.choice(CARS)
                    rot = (0.0 if axis == 0 else math.pi / 2)
                    if direction < 0:
                        rot += math.pi
                    instance(kit[name], coll, (x, y, 0.0), rot)
                    n += 1
    # the ring road, where the cars have to follow the curve
    for lane in (PLAZA_R + 5.5, PLAZA_R + 13.0):
        count = int(2 * math.pi * lane / 26.0)
        for k in range(count):
            a = 2 * math.pi * (k + r.uniform(-0.25, 0.25)) / count
            instance(kit[r.choice(CARS)], coll,
                     (lane * math.cos(a), lane * math.sin(a), 0.0),
                     a + math.pi / 2)
            n += 1
    return n


def parked(kit, coll, lots, r):
    n = 0
    for lot in lots:
        if lot["kind"] != "parking":
            continue
        cx, cy, size, lift = lot["x"], lot["y"], lot["size"], lot["lift"]
        for row in range(4):
            y = cy - size / 2 + 9 + row * (size - 18) / 3
            for k in range(15):
                if r.random() < 0.12:
                    continue
                x = cx - size / 2 + 4.5 + k * (size - 6) / 15
                instance(kit[r.choice(CARS)], coll, (x, y, lift + 0.02),
                         math.pi / 2)
                n += 1
    return n


# --- people ----------------------------------------------------------------
def crowds(kit, coll, lots, r):
    n = 0
    cs = centres()
    for sx in cs:                                   # knots at the crossings
        for sy in cs:
            if in_circus(sx, sy, STREET):
                continue
            if r.random() < 0.45:
                continue
            for _ in range(r.randint(2, 6)):
                a = r.uniform(0, 6.28)
                d = r.uniform(9.0, 17.0)
                instance(kit[r.choice(PEOPLE)], coll,
                         (sx + d * math.cos(a), sy + d * math.sin(a), 0.0),
                         r.uniform(0, 6.28))
                n += 1
    for lot in lots:                                # on the pavements
        if lot["kind"] in ("sector", "island"):
            continue
        cx, cy, lift = lot["x"], lot["y"], lot["lift"]
        for _ in range(r.randint(3, 9)):
            axis, side = r.randint(0, 1), r.choice((-1, 1))
            t = r.uniform(-BLOCK / 2 + 6, BLOCK / 2 - 6)
            e = BLOCK / 2 - r.uniform(0.8, 3.4)
            x, y = ((cx + t, cy + side * e) if axis == 0
                    else (cx + side * e, cy + t))
            instance(kit[r.choice(PEOPLE)], coll, (x, y, lift),
                     r.uniform(0, 6.28))
            n += 1
    for lot in lots:                                # parks and plazas
        if lot["kind"] not in ("park", "plaza"):
            continue
        for _ in range(r.randint(6, 14)):
            instance(kit[r.choice(PEOPLE)], coll,
                     (lot["x"] + r.uniform(-36, 36),
                      lot["y"] + r.uniform(-36, 36), lot["lift"]),
                     r.uniform(0, 6.28))
            n += 1
    for _ in range(40):                             # the circus lawn
        a, d = r.uniform(0, 6.28), 40 * math.sqrt(r.random())
        instance(kit[r.choice(PEOPLE)], coll,
                 (d * math.cos(a), d * math.sin(a), 1.17), r.uniform(0, 6.28))
        n += 1
    return n


def rooftop_people(kit, coll, r):
    """A handful of figures on the roofs, which the reference is full of."""
    n = 0
    props = bpy.data.collections["ROOFPROPS"]
    for ob in list(props.objects):
        if r.random() < 0.10:
            for _ in range(r.randint(1, 3)):
                instance(kit[r.choice(PEOPLE)], coll,
                         (ob.location.x + r.uniform(-5, 5),
                          ob.location.y + r.uniform(-5, 5), ob.location.z),
                         r.uniform(0, 6.28))
                n += 1
    return n


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    kit = {ob.name: ob for ob in bpy.data.collections["KIT"].objects}
    lots = json.loads((R / "city_lots.json").read_text())

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
    t = street_trees(kit, nat, lots, r)
    park_planting(kit, nat, lots, r)
    circus_planting(kit, nat, r)
    li = lights_and_signals(kit, fur, r)
    ca = traffic(kit, tra, r)
    pk = parked(kit, tra, lots, r)
    pe = crowds(kit, ppl, lots, r)
    pe += rooftop_people(kit, ppl, r)

    print(f"\n  trees {len(nat.objects)}  furniture {li}  "
          f"cars {ca + pk}  people {pe}")
    u, tt = counts()
    print(f"  triangles: {u} unique / {tt} total")
    print(f"  objects: {len(bpy.data.objects)}")

    cam = bpy.data.objects["HeroCam"]
    exposure = bpy.context.scene.view_settings.exposure
    blib.render(str(R / "city_05_hero.png"), "EEVEE", samples=64,
                resolution=(1600, 900), exposure=exposure)
    cam.data.ortho_scale = 180.0
    blib.render(str(R / "city_05_closeup.png"), "EEVEE", samples=64,
                resolution=(1600, 900), exposure=exposure)
    cam.data.ortho_scale = 620.0
    blib.save(str(R / "city.blend"))


main()
