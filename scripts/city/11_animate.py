"""Step 11 — put the city in motion.

Everything here is two linear keyframes per object. There is no rig, no path
constraint and no physics: at this scale a car is thirty pixels long and what
sells movement is that the whole frame is drifting in several directions at
once, not that any one vehicle is convincing.

What moves, and why it moves that way:

TRAFFIC. Each vehicle already knows its lane, because step 05 wrote the lane
onto the object when it placed it. Every vehicle in a lane is given the SAME
speed, which is not a simplification for its own sake: it is what makes
rear-end collisions impossible by construction rather than by checking. Speed
varies between lanes instead, and one lane in six is congested, which is where
the sense of traffic comes from.

CROSSINGS. Same-lane is solved; crossing is not. Two constant-velocity cars on
perpendicular streets either miss each other or they do not, and it is decided
before the first frame, so it can be computed. Each conflict is resolved by
holding one car back along its own lane until the other has cleared, which
changes where it starts and nothing else. Held cars can create new conflicts,
so it iterates, and it reports what it could not solve rather than implying it
solved everything.

PEOPLE. The ones step 05 marked as being on a pavement walk along it. They are
turned to face the way they are going, which is the only reason the mark is
needed: a figure that picks its own heading walks into a wall half the time.

A HELICOPTER, crossing high. The kit has had one since step 02 and nothing had
ever placed it.

    ./bl scripts/city/11_animate.py
    ./bl scripts/city/11_animate.py video     # and render the preview
"""
import sys, pathlib, math, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Vector
from _common import (instance, collection, rng, FPS, FRAMES, R, LOTS,
                     SOLIDS, HERO_WIDTH, open_city, save_city, purge, preview)
from _solids import Solids

T = FRAMES / FPS
HELI_SPEED = 34.0                 # m/s, about 120 km/h
HELI_MAST = 3.0                   # rotor plane above the airframe origin

# One turn per second, which is nowhere near a real rotor and is the only
# honest option here. This render has NO motion blur, and without it four
# discrete blades cannot depict fast rotation: anything near a multiple of
# 90 degrees per frame either freezes or flips between two poses, and every
# other fast rate strobes. A rotor that visibly turns at toy speed is
# consistent with a city where the cars' wheels do not turn either. If motion
# blur is ever switched on, this is the number to raise.
ROTOR_HZ = 1.0

CLEAR = 4.0                       # half a car plus half a lane, metres
MAX_HOLD = 45.0                   # how far back a car may be held, metres
PASSES = 6
solids, SUPER = None, (0, 0, 0, 0)
PLAZA = None                      # (x, y, half_w, half_l) or None


def in_super(x, y):
    x0, x1, y0, y1 = SUPER
    return x0 <= x <= x1 and y0 <= y <= y1


def path_blocked(c, samples=16):
    """Does this vehicle's ten seconds take it through something solid?

    **Where a car STARTS is not the question.** Step 05 places every vehicle on
    a clear piece of road and that is all it can check; a car covers 70-145 m
    in the shot, and the streets are not all continuous - two of them stop dead
    at the title's superblock, and the Obelisco's island stands in the middle
    of the bus corridor. A car that begins on a perfectly good stretch of road
    can finish 25 m inside a city block.

    Nothing could see this. Every standing check reads frame 1, and at frame 1
    every one of these vehicles is exactly where it should be. It only surfaced
    because the camera move left the file on frame 240 and the checks ran
    against the last frame by accident.

    So the whole path gets sampled, not the ends: a car can cross a corner of
    a building and come out the other side by frame 240.
    """
    for i in range(samples + 1):
        p = c.p0 + c.dir * c.v * T * (i / samples)
        x, y = (p, c.lane) if c.axis == 0 else (c.lane, p)
        if in_super(x, y):
            return True
        if PLAZA is not None:
            px, py, hw, hl = PLAZA
            if abs(x - px) < hw + 3.0 and abs(y - py) < hl + 3.0:
                return True
        if solids.hit(x, y, 0.0, 2.6) is not None:
            return True
    return False


class Car:
    __slots__ = ("ob", "axis", "lane", "dir", "v", "p0", "held")

    def __init__(self, ob, v):
        self.ob = ob
        self.axis = int(ob["axis"])
        self.lane = float(ob["lane"])
        self.dir = int(ob["dir"])
        self.v = v
        self.p0 = ob.location.x if self.axis == 0 else ob.location.y
        self.held = 0.0

    def window(self, at):
        """When this car is within CLEAR of the crossing coordinate `at`.

        None when it never gets there inside the shot, which is most of the
        time: a car covers about 100 m in ten seconds and the city is 700.
        """
        s = self.dir * self.v
        if abs(s) < 1e-6:
            return None
        t0 = (at - CLEAR - self.p0) / s
        t1 = (at + CLEAR - self.p0) / s
        if t0 > t1:
            t0, t1 = t1, t0
        if t1 < 0.0 or t0 > T:
            return None
        return t0, t1


def lane_speeds(cars, r):
    """One speed per lane, so nothing can ever run into the car in front."""
    speeds = {}
    for ob in cars:
        key = (int(ob["axis"]), round(float(ob["lane"]), 2), int(ob["dir"]))
        if key not in speeds:
            if r.random() < 0.17:
                v = r.uniform(3.0, 4.5)          # a queue
            elif int(ob["avenue"]):
                v = r.uniform(11.0, 14.5)
            else:
                v = r.uniform(7.0, 10.0)
            speeds[key] = v
    return speeds


def conflicts(cars):
    """Pairs that would meet in a crossing, with how long one must be held."""
    ax = [c for c in cars if c.axis == 0]
    ay = [c for c in cars if c.axis == 1]
    # only the stretch of street each car actually covers in the shot
    reach = {}
    for c in cars:
        a = c.p0
        b = c.p0 + c.dir * c.v * T
        reach[id(c)] = (min(a, b) - CLEAR, max(a, b) + CLEAR)
    out = []
    for a in ax:
        lo_a, hi_a = reach[id(a)]
        for b in ay:
            if not (lo_a <= b.lane <= hi_a):
                continue                       # a never reaches b's street
            lo_b, hi_b = reach[id(b)]
            if not (lo_b <= a.lane <= hi_b):
                continue
            wa = a.window(b.lane)
            wb = b.window(a.lane)
            if wa is None or wb is None:
                continue
            if wa[0] > wb[1] or wb[0] > wa[1]:
                continue
            # the one that would arrive later is the one that yields
            late, early = (b, a) if wb[0] >= wa[0] else (a, b)
            wl = late.window(b.lane if late is a else a.lane)
            we = early.window(b.lane if early is a else a.lane)
            out.append((late, we[1] - wl[0] + 0.25))
    return out


def drive(cars):
    for c in cars:
        base = c.ob.location.copy()
        for f, t in ((1, 0.0), (FRAMES, T)):
            d = c.dir * c.v * t
            c.ob.location = (base + Vector((d, 0, 0)) if c.axis == 0
                             else base + Vector((0, d, 0)))
            c.ob.keyframe_insert("location", frame=f)
        c.ob.location = base
        linear(c.ob)


def linear(ob):
    for fc in blib.fcurves(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def walkers(scene, r):
    """Everything step 05 marked as being on a pavement walks along it.

    The start position is stored on the object the first time, exactly like the
    vehicles' "p0", and this is not belt-and-braces: without it the step is not
    re-runnable. `ob.location` on an already-animated object is whatever the
    current frame evaluates to, so a second run takes the END of the first run
    as its start and everybody walks the distance twice. It went unnoticed
    while step 11 was the last step and left the file on frame 1; the camera
    move now leaves it on 240, and the next run marched 888 people fifteen
    metres further, several of them into buildings.

    A walker whose fifteen metres would take it through something solid simply
    stands still. Same policy as the vehicles, and cheaper: a person standing
    on a pavement is not a defect, and a person walking through a wall is.
    """
    n, still = 0, 0
    for ob in scene.objects:
        if ob.type != "MESH" or "walk" not in ob:
            continue
        ob.animation_data_clear()
        if "w0" not in ob:
            ob["w0"] = [ob.location.x, ob.location.y, ob.location.z]
        base = Vector(tuple(ob["w0"]))
        ob.location = base
        dx, dy = ob["walk"][0], ob["walk"][1]
        v = r.uniform(1.0, 1.6)
        ob.rotation_euler.z = math.atan2(dy, dx)
        end = base + Vector((dx * v * T, dy * v * T, 0.0))
        if solids.hit(end.x, end.y, base.z, 0.4) is not None or \
                in_super(end.x, end.y):
            still += 1
            continue
        for f, t in ((1, 0.0), (FRAMES, T)):
            ob.location = base + Vector((dx * v * t, dy * v * t, 0.0))
            ob.keyframe_insert("location", frame=f)
        ob.location = base
        linear(ob)
        n += 1
    return n, still


def helicopter(scene):
    """Across the frame, high, in a straight line. It is the one thing in the
    shot that is not on the grid, which is exactly why it is worth having."""
    kit = {ob.name: ob for ob in bpy.data.collections["KIT"].objects}
    if "Heli" not in kit:
        return None
    coll = purge("AIR")
    ob = instance(kit["Heli"], coll, (0, 0, 0), math.radians(20), 1.6,
                  name="Heli.fly")
    start = Vector((-260.0, -60.0, 78.0))
    heading = Vector((math.cos(math.radians(20)), math.sin(math.radians(20)), 0))
    for f, t in ((1, 0.0), (FRAMES, T)):
        ob.location = start + heading * (HELI_SPEED * t)
        ob.keyframe_insert("location", frame=f)
    linear(ob)

    if "HeliRotor" in kit:
        rot = instance(kit["HeliRotor"], coll, (0, 0, 0), 0.0, 1.0,
                       name="Heli.rotor")
        # parented, not keyframed along: the blades follow the airframe for
        # free, including its 20 degrees of heading and its 1.6 of scale, and
        # the only thing animated here is the one number that has to be
        rot.parent = ob
        rot.location = (0.0, 0.0, HELI_MAST)
        for f, t in ((1, 0.0), (FRAMES, T)):
            rot.rotation_euler = (0.0, 0.0, 2 * math.pi * ROTOR_HZ * t)
            rot.keyframe_insert("rotation_euler", frame=f)
        linear(rot)
    return ob


def main():
    # After 08, or it animates cars that step 08 then deletes.
    scene = open_city(needs_collections=("TRAFFIC", "TITLE"),
                      needs_files=(LOTS, SOLIDS),
                      hint="run 05_life.py then 08_title.py first")
    global solids, SUPER, PLAZA
    solids = Solids.load(SOLIDS)
    lots = json.loads((LOTS).read_text())
    SUPER = lots["superblock"]
    PLAZA = lots.get("avenue9j", {}).get("plaza")
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, FRAMES
    # frame 1 before reading any position. This file may be left on frame 240
    # by the camera step, and every position read below would then be an
    # evaluated one rather than a placed one.
    scene.frame_set(1)

    r = rng(2718)
    vehicles = [ob for ob in scene.objects
                if ob.type == "MESH" and "axis" in ob]
    # back to how step 05 left them. This step moves cars along their lane and
    # hides the ones it cannot place, so without a reset the second run holds
    # the already-held ones again and the road empties a little every time.
    for ob in vehicles:
        ob.animation_data_clear()
        ob.hide_render = ob.hide_viewport = False
        if ob["axis"] == 0:
            ob.location.x = ob["p0"]
        else:
            ob.location.y = ob["p0"]
    speeds = lane_speeds(vehicles, r)
    cars = [Car(ob, speeds[(int(ob["axis"]), round(float(ob["lane"]), 2),
                            int(ob["dir"]))]) for ob in vehicles]
    print(f"\n  {len(cars)} vehicles in {len(speeds)} lanes")

    # before anything else: take off the road anything whose ten seconds would
    # carry it through something solid. Hidden and not deleted, like everything
    # else this step takes off the road, so it stays re-runnable.
    over = [c for c in cars if path_blocked(c)]
    for c in over:
        c.ob.hide_render = c.ob.hide_viewport = True
        cars.remove(c)
    if over:
        print(f"  {len(over)} vehicles would have driven through something "
              f"solid before the shot ends")

    first = len(conflicts(cars))
    for k in range(PASSES):
        cs = conflicts(cars)
        if not cs:
            break
        moved = 0
        for late, dt in cs:
            back = late.v * dt
            if late.held + back > MAX_HOLD:
                continue
            # holding a car up to 45 m back along its lane can walk it into a
            # building, or onto the block the title stands on where there is
            # no longer a street at all. Refuse the hold rather than move it
            # there: it gets taken off the road below instead.
            p = late.p0 - late.dir * back
            x, y = (p, late.lane) if late.axis == 0 else (late.lane, p)
            if solids.hit(x, y, 0.0, 2.4) is not None or in_super(x, y):
                continue
            late.held += back
            late.p0 -= late.dir * back
            if late.axis == 0:
                late.ob.location.x = late.p0
            else:
                late.ob.location.y = late.p0
            moved += 1
        if not moved:
            break
    held = len([c for c in cars if c.held])
    # Holding cars back settles about seventy per cent of it and then stalls,
    # because every car held creates work for the next pass. The rest are
    # taken off the road. A city with 6 % fewer cars in it is not a thing
    # anybody can see; two cars driving through each other is.
    culled = 0
    while True:
        left = conflicts(cars)
        if not left:
            break
        count = {}
        for late, _ in left:
            count[id(late)] = count.get(id(late), 0) + 1
        worst = max(count, key=count.get)
        victim = next(c for c in cars if id(c) == worst)
        # hidden, not deleted, so this step stays re-runnable
        victim.ob.hide_render = victim.ob.hide_viewport = True
        cars.remove(victim)
        culled += 1
    print(f"  crossing conflicts: {first} found, {held} cars held back, "
          f"{culled} taken off the road, 0 left")

    drive(cars)
    people, still = walkers(scene, r)
    heli = helicopter(scene)
    print(f"  walking: {people} people ({still} left standing)   helicopter: "
          f"{'yes' if heli else 'no Heli in the kit'}")

    for f in (1, FRAMES // 2, FRAMES):
        # HERO_WIDTH, not a literal 170.0: this is a control render of the
        # traffic and it has to be the framing the shot actually lands on.
        with preview(HERO_WIDTH, target=(0, 0, 0), frame=f):
            blib.render(str(R / f"city_11_move_{f:03d}.png"), "EEVEE",
                        samples=48, resolution=(1280, 720))
    scene.frame_set(1)
    save_city()

    if "video" in sys.argv:
        blib.render_video(str(R / "city_move.mp4"), fps=FPS, engine="EEVEE",
                          samples=48, resolution=(1280, 720))
        print("  video: renders/city_move.mp4")


main()
