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
from _solids import Solids

R = ROOT / "renders"

# Three jacaranda entries against twelve of everything else: one street tree
# in five is in flower. The first version put six against six and half the
# city came out violet, which reads as a fantasy rather than as November.
TREES = (["Tree0", "Tree1", "Tree2", "Tree3", "Conifer0", "Conifer1"] * 2 +
         ["Jacaranda0", "Jacaranda1", "Jacaranda2"])
# a taxi is one car in five here, which is not far off the real proportion in
# the middle of Buenos Aires and is the cheapest of all the cues: from this
# camera a car is mostly its roof, and this one has a yellow roof
CARS = ["CarRed", "CarWhite", "CarTeal", "CarBlue", "CarDark", "CarSilver",
        "Taxi", "Taxi", "Taxi"]
# a taxi is a working vehicle: it belongs on the road, not in the car park of
# an office block. With Taxi in this list a third of every parking lot came
# out yellow, which reads as a taxi rank and there is no rank there.
PARKED = CARS[:6]
COLECTIVOS = [f"Colectivo{i}" for i in range(4)]
PEOPLE = [f"Person{i}" for i in range(8)]
AVENUE = 22.0
SUPER = None          # set from the JSON: the block the title stands on

# Clearance each kind of object asks for, in metres. A person is queried at
# almost nothing on purpose: somebody standing against a shop window is right,
# somebody standing inside the shop is not.
SOLIDS = Solids()
CLEAR = {"tree": 3.2, "shrub": 1.6, "bench": 1.2, "person": 0.4,
         "car": 2.4, "pole": 0.8}
# Measured off the KIT meshes, not guessed. The canopy is what goes through a
# wall, not the trunk, and these differ by a factor of two and a half: one
# blanket clearance either lets Tree2 into the building or refuses Tree3 for
# nothing, and 790 street trees were refused on a number that fitted neither.
# It is the largest hypot(x, y), not the largest x or y, because every one of
# these is dropped in at a random rotation about Z.
RAD = {"Tree0": 3.33, "Tree1": 2.60, "Tree2": 4.38, "Tree3": 1.84,
       "Conifer0": 2.73, "Conifer1": 2.08, "Shrub": 1.13,
       "Jacaranda0": 3.53, "Jacaranda1": 4.68, "Jacaranda2": 4.71}
# a bus is two and a half cars long. One "car" clearance let the buses through
VEHICLE = {"Bus": 5.6, "Truck": 4.2, "Colectivo0": 5.7, "Colectivo1": 5.7,
           "Colectivo2": 5.7, "Colectivo3": 5.7}
SKIPPED = {}


def free(kind, x, y, z=0.0):
    """Is there room for this here? Counts its refusals so they get reported.

    Silence is the failure mode of a filter like this one: if the footprints
    ever stop being published the query returns True for everything and the
    trees go back into the walls with nothing in the log to say so.
    """
    if SOLIDS.hit(x, y, z, CLEAR[kind]) is None:
        return True
    SKIPPED[kind] = SKIPPED.get(kind, 0) + 1
    return False


def fit_tree(name, sc, x, y, z):
    """The largest of these that fits here, or None.

    Refusing outright leaves a bare pavement in front of every building, which
    is the opposite of the reference. A narrower species, or the same one
    smaller, is what a real street does when the setback is tight.
    """
    for nm, s in ((name, sc), (name, sc * 0.7), ("Tree3", 0.85),
                  ("Shrub", 1.3)):
        if SOLIDS.hit(x, y, z, RAD[nm] * s) is None:
            return nm, s
    SKIPPED["tree"] = SKIPPED.get("tree", 0) + 1
    return None


def in_super(x, y, pad=0.0):
    """The two streets that used to cross the title block are gone, so nothing
    that belongs to a street may be placed there any more: a traffic light in
    the middle of a lawn, or a bus driving through a letter."""
    if SUPER is None:
        return False
    x0, x1, y0, y1 = SUPER
    return x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad


def street_trees(kit, coll, lots, walk, r):
    """A row down every block edge, with gaps so it is not a regiment.

    On the pavement, which is outside the lot interior. The first version put
    the row 1.2 m inside the interior edge and the buildings come to within
    0.75 m of that same edge, so nearly half the street trees were standing
    inside an office: 917 of them, once there was a test that could count.
    """
    n = 0
    for lot in lots:
        cx, cy = lot["x"], lot["y"]
        w, d = lot["size"]
        lift = lot["lift"]
        for axis in (0, 1):
            length = w if axis == 0 else d
            edge = (d if axis == 0 else w) / 2 + walk * 0.5
            # 12, not 8: the block corners are cut at 45 degrees now and the
            # last tree of a row used to sit out over the chamfer with nothing
            # under it
            span = length - 12.0
            count = max(1, int(span / 8.5))
            for side in (-1, 1):
                for k in range(count + 1):
                    if r.random() < 0.34:
                        continue
                    t = -span / 2 + k * span / count
                    x, y = ((cx + t, cy + side * edge) if axis == 0
                            else (cx + side * edge, cy + t))
                    # Every draw happens whether or not the tree is placed:
                    # the whole city comes out of one stream, so a conditional
                    # draw would reshuffle every lot downstream of the first
                    # refusal. The jitter runs along the pavement and barely
                    # across it: 1.6 m across a 2.5 m walk is the road.
                    name = r.choice(TREES)
                    a = r.uniform(-2.2, 2.2)
                    b = r.uniform(-0.5, 0.5)
                    px, py = ((x + a, y + b) if axis == 0 else (x + b, y + a))
                    rot, sc = r.uniform(0, 6.28), r.uniform(1.0, 1.5)
                    got = fit_tree(name, sc, px, py, lift)
                    if got is None:
                        continue
                    instance(kit[got[0]], coll, (px, py, lift), rot, got[1])
                    n += 1
    return n


def clump(kit, coll, cx, cy, rw, rd, lift, count, r):
    for _ in range(count):
        name = r.choice(TREES)
        px, py = cx + r.uniform(-rw, rw), cy + r.uniform(-rd, rd)
        rot, sc = r.uniform(0, 6.28), r.uniform(1.0, 1.8)
        got = fit_tree(name, sc, px, py, lift)
        if got is None:
            continue
        instance(kit[got[0]], coll, (px, py, lift), rot, got[1])


def planting(kit, coll, lots, r):
    for lot in lots:
        kind, lift = lot["kind"], lot["lift"]
        cx, cy = lot["x"], lot["y"]
        w, d = lot["size"]
        # counts were fixed per lot, which is fine while every block is about
        # 60 m square and wrong the moment one of them is the 140 m superblock
        # the title stands on: it came out as a bare lawn
        n = max(1.0, w * d / 3600.0)
        if kind == "park":
            clump(kit, coll, cx, cy, w * 0.42, d * 0.42, lift, int(34 * n), r)
            for _ in range(8):
                px, py = cx + r.uniform(-w / 3, w / 3), cy + r.uniform(-d / 3, d / 3)
                rot, sc = r.uniform(0, 6.28), r.uniform(0.9, 1.5)
                if free("shrub", px, py, lift):
                    instance(kit["Shrub"], coll, (px, py, lift), rot, sc)
            for _ in range(5):
                px, py = cx + r.uniform(-w / 3, w / 3), cy + r.uniform(-d / 3, d / 3)
                rot = r.uniform(0, 6.28)
                if free("bench", px, py, lift):
                    instance(kit["Bench"], coll, (px, py, lift), rot)
        elif kind == "plaza":
            clump(kit, coll, cx, cy, w * 0.36, d * 0.36, lift, int(12 * n), r)
            for _ in range(int(3 * n)):
                px, py = cx + r.uniform(-w / 3, w / 3), cy + r.uniform(-d / 3, d / 3)
                rot = r.uniform(0, 6.28)
                if free("bench", px, py, lift):
                    instance(kit["Bench"], coll, (px, py, lift), rot)
        elif kind == "parking":
            clump(kit, coll, cx, cy, w * 0.42, d * 0.42, lift, int(8 * n), r)


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
                        if in_super(x, y, -1.0) or not free("pole", x, y):
                            continue
                        instance(kit["StreetLight"], coll, (x, y, 0.0), rot)
                        n += 1

    for sx, wx in zip(data["streets_x"], data["widths_x"]):
        for sy, wy in zip(data["streets_y"], data["widths_y"]):
            if max(wx, wy) < AVENUE and r.random() < 0.6:
                continue
            for k, (dx, dy) in enumerate(((1, 1), (-1, -1))):
                x = sx + dx * ((wx - walk * 2) / 2 + 1.4)
                y = sy + dy * ((wy - walk * 2) / 2 + 1.4)
                if in_super(x, y, -1.0) or not free("pole", x, y):
                    continue
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
                    name = (r.choice(COLECTIVOS + ["Truck"])
                            if r.random() < 0.09 else r.choice(CARS))
                    if in_super(x, y, -1.0):
                        continue
                    if SOLIDS.hit(x, y, 0.0, VEHICLE.get(name, 2.4)):
                        SKIPPED["car"] = SKIPPED.get("car", 0) + 1
                        continue
                    rot = 0.0 if axis == 0 else math.pi / 2
                    if direction < 0:
                        rot += math.pi
                    ob = instance(kit[name], coll, (x, y, 0.0), rot)
                    # which lane this vehicle is in, so step 11 can drive it
                    # without having to reconstruct the street layout from the
                    # position it ended up at
                    ob["axis"] = axis
                    ob["lane"] = s + lane
                    ob["dir"] = direction
                    ob["avenue"] = 1 if w >= AVENUE else 0
                    # where it started, so step 11 can be run twice. It moves
                    # cars along their lane to keep them out of each other,
                    # and without this the second run moves the moved ones
                    ob["p0"] = x if axis == 0 else y
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
                name = r.choice(PARKED)
                if not free("car", x, y, lot["lift"]):
                    continue
                instance(kit[name], coll, (x, y, lot["lift"] + 0.02),
                         math.pi / 2)
                n += 1
    return n


def crowds(kit, coll, lots, data, walk, r):
    n = 0
    for lot in lots:                                   # along the pavements
        cx, cy = lot["x"], lot["y"]
        w, d = lot["size"]
        for _ in range(r.randint(14, 30)):
            axis, side = r.randint(0, 1), r.choice((-1, 1))
            length = w if axis == 0 else d
            # outside the lot interior, like the trees: the pavement is the
            # band between the interior edge and the kerb, and people walking
            # 2.2 m the other side of that line are walking through a wall
            edge = (d if axis == 0 else w) / 2 + r.uniform(0.3, walk - 0.3)
            t = r.uniform(-length / 2 + 4, length / 2 - 4)
            x, y = ((cx + t, cy + side * edge) if axis == 0
                    else (cx + side * edge, cy + t))
            name = r.choice(PEOPLE)
            rot = r.uniform(0, 6.28)
            if not free("person", x, y, lot["lift"]):
                continue
            ob = instance(kit[name], coll, (x, y, lot["lift"]), rot)
            # the pavement runs along one axis and this is the only place that
            # knows which. Step 11 walks these; without it a walking figure
            # has to guess a heading and half of them set off into a wall.
            if r.random() < 0.55:
                ob["walk"] = [1.0, 0.0] if axis == 0 else [0.0, 1.0]
                if r.random() < 0.5:
                    ob["walk"] = [-ob["walk"][0], -ob["walk"][1]]
            n += 1
        if lot["kind"] in ("park", "plaza"):
            for _ in range(r.randint(10, 22)):
                name = r.choice(PEOPLE)
                px, py = cx + r.uniform(-w / 3, w / 3), cy + r.uniform(-d / 3, d / 3)
                rot = r.uniform(0, 6.28)
                if not free("person", px, py, lot["lift"]):
                    continue
                instance(kit[name], coll, (px, py, lot["lift"]), rot)
                n += 1

    for sx in data["streets_x"]:                       # knots at the crossings
        for sy in data["streets_y"]:
            if r.random() < 0.3:
                continue
            for _ in range(r.randint(3, 9)):
                a, dd = r.uniform(0, 6.28), r.uniform(9.0, 16.0)
                px, py = sx + dd * math.cos(a), sy + dd * math.sin(a)
                name = r.choice(PEOPLE)
                rot = r.uniform(0, 6.28)
                if in_super(px, py, -1.0) or not free("person", px, py):
                    continue
                instance(kit[name], coll, (px, py, 0.0), rot)
                n += 1
    return n


def rooftop_people(kit, coll, r):
    """ROOFPROPS only. CAMPUSROOF exists but is empty: the title blocks carry
    the letters themselves now, so there are no campus roofs to stand on."""
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
    global SUPER, SOLIDS
    SUPER = data.get("superblock")
    SOLIDS = Solids.load(R / "city_solids.json")
    if not SOLIDS.boxes:
        raise SystemExit("no city_solids.json: run steps 04 and 06 first, or "
                         "everything below plants itself inside a wall")
    print(f"  {len(SOLIDS.boxes)} footprints to keep clear of")

    for name in ("NATURE", "FURNITURE", "TRAFFIC", "PEOPLE", "ROOFPEOPLE"):
        if name in bpy.data.collections:
            c = bpy.data.collections[name]
            for ob in list(c.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
    nat = collection("NATURE")
    fur = collection("FURNITURE")
    tra = collection("TRAFFIC")
    ppl = collection("PEOPLE")
    # their own collection because they are standing on roofs, which is inside
    # a building footprint on purpose. Mixed in with the pavement crowd they
    # made the footprint check fail 63 times a run, correctly and uselessly.
    rpl = collection("ROOFPEOPLE")

    walk = data["walk"]
    r = rng(31337)
    street_trees(kit, nat, lots, walk, r)
    planting(kit, nat, lots, r)
    li = lights_and_signals(kit, fur, data, r)
    ca = traffic(kit, tra, data, r) + parked(kit, tra, lots, r)
    pe = crowds(kit, ppl, lots, data, walk, r) + rooftop_people(kit, rpl, r)

    print(f"\n  trees {len(nat.objects)}  furniture {li}  cars {ca}  people {pe}")
    print("  refused for want of room: " +
          ("  ".join(f"{k} {v}" for k, v in sorted(SKIPPED.items())) or "none"))
    u, t = counts()
    print(f"  triangles: {u} unique / {t} total   objects {len(bpy.data.objects)}")

    cam = bpy.data.objects["HeroCam"]
    exposure = bpy.context.scene.view_settings.exposure
    cam.data.ortho_scale = 200.0
    blib.render(str(R / "city_05_closeup.png"), "EEVEE", samples=64,
                resolution=(1600, 900), exposure=exposure)
    blib.save(str(R / "city.blend"))


main()
