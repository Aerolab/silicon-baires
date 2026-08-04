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
from _common import (collection, instance, mat, rng, counts, median_runs, R,
                     LOTS, SOLIDS as SOLIDS_JSON, open_city,
                     save_city, purge, preview)
from _solids import Solids


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

# The south rim: the row 03_ground bolts on outside the grid, keyed j = -1 and
# appended to city_lots.json last. Planted from its own stream at the end of
# main() - see the note there.
RIM_ROW = -1
RIM_SEED = 8123


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


MEDIAN_TREES = (["Jacaranda0", "Jacaranda1", "Tree1", "Tree3", "Conifer1",
                 "Tree3", "Jacaranda2", "Tree1"])


def avenue_trees(kit, coll, data, r):
    """Two rows down the planted medians of the 9 de Julio.

    This is the whole reason the medians are there. A 52 m avenue with nothing
    growing in it is a runway; the same avenue with two lines of trees down it
    is the widest street in the world, which is what it is famous for being.

    The median is 5 m wide, so the species are the narrow ones - and the
    jacaranda is over-represented on purpose, because the real avenue is one
    of the places people go to see them.

    Where the median is: `median_runs`, the same list step 03 builds the kerbs
    from. This used to plant off its own block arithmetic and skip a band
    around the plaza, which agrees with step 03 everywhere except the one block
    that matters. There, both stubs come out 9 m long and step 03 drops them,
    so the block has no median at all - and four trees stood in the middle of
    the avenue beside the Obelisco, floating at median height on bare asphalt.
    """
    av = data.get("avenue9j")
    if av is None:
        return 0
    n = 0
    lift = av["median_lift"]
    px, py, pw, pl = av["plaza"]
    mid = (av["median"][0] + av["median"][1]) / 2
    # 1.5 m in from each end, so the trunk stands on kerb rather than on the
    # chamfer of it, and the canopy does not lean over the crossing
    runs = [(a + 1.5, b - 1.5) for a, b in
            median_runs(data["blocks_y"], py, pl)]
    for (cy, size) in data["blocks_y"]:
        # 7 m, not 9. The median is the one planting in this city that is meant
        # to read as a continuous line rather than as a row of individuals, and
        # at 9 m it came out with bald stretches between the crossings.
        span = size - 10.0
        count = max(1, int(span / 7.0))
        for side in (-1, 1):
            for k in range(count + 1):
                t = cy - span / 2 + k * span / count
                name = r.choice(MEDIAN_TREES)
                sc = r.uniform(0.85, 1.15)
                jitter = r.uniform(-1.1, 1.1)
                x, y = av["x"] + side * mid, t + jitter
                if not any(a <= y <= b for a, b in runs):
                    # no kerb here: the plaza, or a stub too short to build
                    SKIPPED["tree"] = SKIPPED.get("tree", 0) + 1
                    continue
                if SOLIDS.hit(x, y, lift, RAD[name] * sc * 0.7) is not None:
                    SKIPPED["tree"] = SKIPPED.get("tree", 0) + 1
                    continue
                instance(kit[name], coll, (x, y, lift),
                         r.uniform(0, 6.28), sc)
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
        # the street runs along this axis, so its position is a coordinate on
        # the other one: see the note in 03_ground.build_markings
        streets = data["streets_y"] if axis == 0 else data["streets_x"]
        widths = data["widths_y"] if axis == 0 else data["widths_x"]
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


def avenue_lanes(av):
    """The 9 de Julio's lanes, which are not a wider version of an avenue's.

    Two one-way lateral carriageways of four lanes each, and a bus corridor in
    the middle that only buses may use. Read as an ordinary 52 m avenue it puts
    four lanes of cars straight down the Metrobus platform.

    Which side goes which way is not a choice: driving on the right, the
    carriageway heading +y is the one on the +x side, because that is where the
    driver's right hand is.
    """
    out = []
    lat = (av["median"][1] + av["width"] / 2) / 2      # centre of a lateral
    for side in (-1, 1):
        for o in (-7.0, -3.5, 0.0, 3.5, 7.0):          # five lanes each
            out.append((side * lat + o, side, False))
    for side in (-1, 1):
        out.append((side * (av["platform"] + 1.75), side, True))
    return out


def traffic(kit, coll, data, r):
    n = 0
    span = max(data["blocks_x"][-1][0], data["blocks_y"][-1][0]) + 60
    av = data.get("avenue9j")
    for axis in (0, 1):
        # a street running along X is at a Y coordinate: the Y table
        streets = data["streets_y"] if axis == 0 else data["streets_x"]
        widths = data["widths_y"] if axis == 0 else data["widths_x"]
        for idx, (s, w) in enumerate(zip(streets, widths)):
            nine = av is not None and axis == 1 and idx == av["index"]
            if nine:
                lanes = [(o, d) for o, d, _ in avenue_lanes(av)]
                buses = {o for o, _, b in avenue_lanes(av) if b}
            else:
                lanes = ((-5.25, -1), (-1.75, -1), (1.75, 1), (5.25, 1)) \
                    if w >= AVENUE else ((-1.75, -1), (1.75, 1))
                buses = set()
            for lane, direction in lanes:
                # Argentina drives on the right, and the lane table above is
                # written once for both axes, which cannot be right for both:
                # the two axes have opposite handedness about the offset sign.
                # Heading +x the driver's right hand points at -y, so the +x
                # traffic belongs on the negative side; heading +y it points at
                # +x, so the +y traffic belongs on the positive side. The y
                # streets came out correct by luck and the x streets came out
                # British, which is a thing you can only see by picking one car
                # and following it: every street looked plausible on its own.
                if axis == 0:
                    direction = -direction
                pos = -span
                while pos < span:
                    # a bus lane is not a car lane with buses in it. At car
                    # spacing the corridor came out as one unbroken line of
                    # colectivos nose to tail down the middle of the avenue,
                    # which reads as a parked queue rather than as a service.
                    # 2.2, not 3.4: at car spacing the corridor is a solid line
                    # of colectivos nose to tail, which reads as a queue, and
                    # at 3.4 there were sixteen buses in 762 m of busway, which
                    # reads as a corridor nobody uses
                    pos += r.uniform(13.0, 44.0) * (2.2 if lane in buses else 1.0)
                    x, y = ((pos, s + lane) if axis == 0 else (s + lane, pos))
                    name = (r.choice(COLECTIVOS + ["Truck"])
                            if r.random() < 0.09 else r.choice(CARS))
                    if lane in buses:
                        # a bus lane with cars in it is not a bus lane, and the
                        # corridor is the one part of this avenue that a viewer
                        # can actually name
                        name = r.choice(COLECTIVOS)
                        px, py, pw, pl = av["plaza"]
                        if abs(y - py) < pl + 4.0:
                            continue       # the plaza stands in the busway
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


def plaza_people(kit, coll, data, r):
    """Somebody on the island, and somebody waiting for a bus.

    The plaza used to get its crowd for free, from the knot of people step 05
    scatters at every crossing - and then it moved mid-block and came out
    deserted. An empty plaza around a monument reads as a model rather than as
    a city, and this is the one place in frame the eye is sent to.
    """
    av = data.get("avenue9j")
    if av is None:
        return 0
    n = 0
    px, py, hw, hl = av["plaza"]
    for _ in range(34):
        # rejection-sample the oval: a rectangle puts a third of them on the
        # asphalt outside it
        a, rad = r.uniform(0, 6.28), math.sqrt(r.random())
        x, y = px + hw * rad * math.cos(a), py + hl * rad * math.sin(a)
        name, rot = r.choice(PEOPLE), r.uniform(0, 6.28)
        if not free("person", x, y, 0.24):
            continue
        instance(kit[name], coll, (x, y, 0.24), rot)
        n += 1
    # and the platforms. A Metrobus station with nobody on it is a shelter.
    plat = av["platform"]
    for (cy, size) in data["blocks_y"]:
        if abs(cy - py) < hl + 6.0:
            continue
        for _ in range(r.randint(0, 7)):
            x = av["x"] + r.uniform(-plat + 0.8, plat - 0.8)
            y = cy + r.uniform(-13.0, 13.0)
            name, rot = r.choice(PEOPLE), r.uniform(0, 6.28)
            if not free("person", x, y, 0.40):
                continue
            instance(kit[name], coll, (x, y, 0.40), rot)
            n += 1
    return n


def rooftop_people(kit, coll, r):
    """ROOFPROPS only. CAMPUSROOF exists but is empty: the title blocks carry
    the letters themselves now, so there are no campus roofs to stand on."""
    n = 0
    for ob in list(bpy.data.collections["ROOFPROPS"].objects):
        if r.random() < 0.10:
            for _ in range(r.randint(1, 3)):
                px = ob.location.x + r.uniform(-2.0, 2.0)
                py = ob.location.y + r.uniform(-2.0, 2.0)
                name, rot = r.choice(PEOPLE), r.uniform(0, 6.28)
                # a roof carries signs and cupolas now, and standing inside
                # one of those is the same error as standing inside a wall
                if SOLIDS.hit(px, py, ob.location.z, 0.4,
                              tags=("signs", "porteno")) is not None:
                    continue
                instance(kit[name], coll, (px, py, ob.location.z), rot)
                n += 1
    return n


def main():
    open_city(needs_collections=("KIT", "SITE", "BUILDINGS"),
              needs_files=(LOTS, SOLIDS_JSON),
              hint="run 03, 04, 06, 06b and 10 first: this step queries the "
                   "footprints they publish, and an empty table plants a whole "
                   "city of trees inside the buildings")
    kit = {ob.name: ob for ob in bpy.data.collections["KIT"].objects}
    data = json.loads((LOTS).read_text())
    lots = data["lots"]
    global SUPER, SOLIDS
    SUPER = data.get("superblock")
    SOLIDS = Solids.load(SOLIDS_JSON)
    if not SOLIDS.boxes:
        raise SystemExit("no city_solids.json: run steps 04 and 06 first, or "
                         "everything below plants itself inside a wall")
    print(f"  {len(SOLIDS.boxes)} footprints to keep clear of")

    # ROOFPEOPLE get their own collection because they are standing on roofs,
    # which is inside a building footprint on purpose. Mixed in with the
    # pavement crowd they made the footprint check fail 63 times a run,
    # correctly and uselessly.
    nat, fur, tra, ppl, rpl = purge("NATURE", "FURNITURE", "TRAFFIC",
                                    "PEOPLE", "ROOFPEOPLE")

    walk = data["walk"]
    # The south rim comes out of its own stream, at the end. Every pass below
    # walks the lots in order and they all share `r`, so nine more lots taken in
    # sequence in street_trees would move where planting starts, which moves
    # traffic, which moves the crowds: the whole city relit for the sake of a
    # row of blocks in the corner of one frame. Same device 03 and 04 use for
    # the same row - see 03_ground.build_rim.
    rim = [l for l in lots if int(l["key"][1]) == RIM_ROW]
    lots = [l for l in lots if int(l["key"][1]) != RIM_ROW]

    r = rng(31337)
    street_trees(kit, nat, lots, walk, r)
    med = avenue_trees(kit, nat, data, r)
    planting(kit, nat, lots, r)
    li = lights_and_signals(kit, fur, data, r)
    ca = traffic(kit, tra, data, r) + parked(kit, tra, lots, r)
    pe = (crowds(kit, ppl, lots, data, walk, r)
          + plaza_people(kit, ppl, data, r) + rooftop_people(kit, rpl, r))

    rr = rng(RIM_SEED)
    street_trees(kit, nat, rim, walk, rr)
    planting(kit, nat, rim, rr)
    ca += parked(kit, tra, rim, rr)
    pe += crowds(kit, ppl, rim, data, walk, rr)

    print(f"\n  trees {len(nat.objects)} ({med} down the 9 de Julio medians)"
          f"  furniture {li}  cars {ca}  people {pe}")
    print("  refused for want of room: " +
          ("  ".join(f"{k} {v}" for k, v in sorted(SKIPPED.items())) or "none"))
    u, t = counts()
    print(f"  triangles: {u} unique / {t} total   objects {len(bpy.data.objects)}")

    exposure = bpy.context.scene.view_settings.exposure
    with preview(200.0, target=(0, 0, 0)):
        blib.render(str(R / "city_05_closeup.png"), "EEVEE", samples=64,
                    resolution=(1600, 900), exposure=exposure)
    save_city()


main()
