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
from _common import (instance, rng, FPS, FRAMES, R, LOTS,
                     SOLIDS, HERO_WIDTH, open_city, save_city, purge, preview,
                     surfacer, UNDERFOOT)
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
UNDER = None                      # the ray onto the site: what is underfoot


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

    def window(self, at, clear=CLEAR):
        """When this car is within `clear` of the crossing coordinate `at`.

        None when it never gets there inside the shot, which is most of the
        time: a car covers about 100 m in ten seconds and the city is 700.

        `clear` is a parameter because the pedestrians ask the same question
        with a different answer: two cars need half a car plus half a lane
        between them, and a person needs the length of the vehicle plus enough
        room that the near miss does not read as one.
        """
        s = self.dir * self.v
        if abs(s) < 1e-6:
            return None
        t0 = (at - clear - self.p0) / s
        t1 = (at + clear - self.p0) / s
        if t0 > t1:
            t0, t1 = t1, t0
        if t1 < 0.0 or t0 > T:
            return None
        return t0, t1


# Half the length of a vehicle along its own lane, in metres, by name. Same
# table step 05 places from, and it has to be: 11 m of colectivo cleared as if
# it were 4.5 m of hatchback leaves the back half of the bus inside the car
# behind it.
HALF_LEN = {"Colectivo": 5.7, "Bus": 5.6, "Truck": 4.2}
CAR_HALF = 2.3
BUMPER = 1.5                      # and the gap left between two of them


def half_len(name):
    for k, v in HALF_LEN.items():
        if name.startswith(k):
            return v
    return CAR_HALF


def tailgated(car, p, lanes):
    """Would putting `car` at `p` overlap anything else in its lane?"""
    mine = half_len(car.ob.name)
    for other in lanes.get((car.axis, round(car.lane, 2)), ()):
        if other is car:
            continue
        if abs(p - other.p0) < mine + half_len(other.ob.name) + BUMPER:
            return True
    return False


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
        # HOW FAR THEY GET, not whether they may go. A pavement walker covers
        # fifteen metres in the shot and a block is sixty across, so anybody
        # starting within fifteen metres of a corner walks off the kerb and
        # keeps going: 354 of the 1000 ended the shot standing in the
        # carriageway, and refusing all of those outright left 587 people
        # rooted to the spot - which fixes the wrong thing. Somebody who walks
        # eight metres and stops at the corner is a person waiting to cross;
        # somebody who never moves is a bollard.
        want = v * T
        far = reach(base, dx, dy, want)
        if far < 3.0:
            still += 1
            continue
        t_end = far / v
        keys = [(1, 0.0), (frame_at(t_end), far)]
        if t_end < T:
            keys.append((FRAMES, far))
        for f, d in keys:
            ob.location = base + Vector((dx * d, dy * d, 0.0))
            ob.keyframe_insert("location", frame=f)
        ob.location = base
        linear(ob)
        n += 1
    return n, still


def reach(base, dx, dy, want, step=1.0):
    """How far along this heading the pavement lasts, up to `want` metres."""
    got = 0.0
    d = step
    while d <= want + 1e-6:
        p = base + Vector((dx * d, dy * d, 0.0))
        if solids.hit(p.x, p.y, base.z, 0.4) is not None or \
                in_super(p.x, p.y) or UNDER(p.x, p.y) not in UNDERFOOT:
            return got
        got = d
        d += step
    return want


# How much room a person asks a vehicle for, in metres along its lane. A
# colectivo is 11 m long and its origin is the middle of it, so anything under
# about 7 m here is a bus whose back half is still in the crossing.
PED_CLEAR = 9.0
# and the slack at each end of the gap, in seconds. Stepping off the kerb the
# instant the last bumper clears is arithmetically safe and reads as a near
# miss, which is the same defect: the whole point of this is that it LOOKS
# like people and cars are aware of each other.
GAP_MARGIN = 0.7


def crossers(scene, cars, r):
    """The people step 05 stood at a zebra, walked across it in a real gap.

    THIS IS THE INTERACTION. Everything else in this file is one kind of thing
    avoiding another kind of thing; this is the only place where the crowd and
    the traffic are solved against each other, and it is the answer to 545
    people being driven through during the shot.

    It reuses the vehicles' own conflict machinery rather than approximating
    it. A pedestrian on a zebra is at a fixed coordinate along the street they
    are crossing, so the question "when is a car near me" is exactly
    `Car.window(that coordinate)` - the same function that stops two cars
    meeting in a crossing, asked with a person's clearance instead of a car's.
    Every occupied interval is collected, the gaps between them are what is
    left, and the first gap long enough to walk the carriageway in is the one
    they take.

    A pedestrian with no gap long enough does not cross. They stand at the
    kerb for the whole shot, which is what a person actually does, and which
    is why this can never produce the thing it was written to prevent: the
    failure mode is somebody waiting, not somebody under a bus.
    """
    crossing, waiting, walked = 0, 0, 0
    for ob in scene.objects:
        if ob.type != "MESH" or "cross" not in ob:
            continue
        ob.animation_data_clear()
        # like the walkers' "w0" and the vehicles' "p0": without it a second
        # run reads the END of the first as the start. This file is left on
        # frame 240 by the camera step.
        if "c0" not in ob:
            ob["c0"] = [ob.location.x, ob.location.y, ob.location.z]
        base = Vector(tuple(ob["c0"]))
        ob.location = base
        crossing += 1

        dx, dy = ob["cross"][0], ob["cross"][1]
        axis = 0 if abs(dx) > abs(dy) else 1        # the axis they travel on
        fixed = base.y if axis == 0 else base.x     # and where they sit on it
        street, half = float(ob["cstreet"]), float(ob["chalf"])
        dist = float(ob["cdist"])
        ob.rotation_euler.z = math.atan2(dy, dx)

        v = r.uniform(1.1, 1.6)

        # Every vehicle running down the street being crossed, as (when it is
        # near this crossing, which lane it is in). PER LANE, and that is the
        # whole difference between a city where people cross and one where 138
        # of 173 stand at the kerb for 26 seconds.
        #
        # Treating the carriageway as one hazard means a 12 m crossing needs a
        # 9-second gap in the traffic, and on a street with a car every 13 to
        # 44 m there is never one. But a car in the far lane cannot hit
        # somebody who is still in the near one. The exposure to any given
        # vehicle is only the second or two spent in ITS lane, which is a gap
        # that exists constantly.
        busy = []
        for c in cars:
            if c.axis == axis:
                continue                  # travelling the same way; not a risk
            if abs(c.lane - street) > half + 1.0:
                continue                  # a different street entirely
            w = c.window(fixed, PED_CLEAR)
            if w is not None:
                busy.append((w[0], w[1], c.lane))

        start = when_to_go(busy, base, dx, dy, dist, v)
        if start is None:
            waiting += 1
            continue

        end = start + dist / v
        keys = [(1, 0.0), (frame_at(start), 0.0), (frame_at(end), dist)]
        if end < T:
            keys.append((FRAMES, dist))
        seen = set()
        for f, d in keys:
            if f in seen:
                continue                  # start at t=0 collapses onto frame 1
            seen.add(f)
            ob.location = base + Vector((dx * d, dy * d, 0.0))
            ob.keyframe_insert("location", frame=f)
        ob.location = base
        linear(ob)
        walked += 1
    return crossing, walked, waiting


def frame_at(t):
    return max(1, min(FRAMES, 1 + int(round(t * FPS))))


# How wide a lane a pedestrian is exposed in, in metres either side of the
# vehicle's own line. A lane is 3.5 m and a person is 0.5 m across, so 2.0 is
# the lane plus a body: outside that the vehicle passes behind or in front of
# them, which is what crossing a street actually looks like.
LANE_HALF = 2.0
STEP = 0.25                       # how finely the departure time is searched


def when_to_go(busy, base, dx, dy, dist, v):
    """The first moment they can set off and clear every lane safely.

    `busy` is (from, until, lane) per vehicle: when it is within a body's
    length of this crossing, and which line it runs down. The walker's own
    position is known for every instant, so the test is direct - for each
    vehicle, work out when the walker is inside ITS lane and ask whether the
    two intervals touch.

    Searched by sweeping the departure time rather than by merging intervals
    into gaps, because there are no gaps to merge: the constraint is different
    for every vehicle, since each one is passed at a different point in the
    walk. A sweep at a quarter of a second is 100 candidates against about 20
    vehicles, which is nothing, and it cannot be subtly wrong about a
    coincidence the way interval arithmetic can.
    """
    if not busy:
        return 0.0
    # where the walker is along each axis is linear in t, so the moment they
    # reach a given lane coordinate is too
    axis_d = dy if abs(dy) > abs(dx) else dx
    at = base.y if abs(dy) > abs(dx) else base.x
    latest = T - dist / v
    if latest < 0:
        return None
    t = 0.0
    while t <= latest:
        for lo, hi, lane in busy:
            # when this walker enters and leaves that vehicle's lane
            c = (lane - at) / (axis_d * v)
            a, b = t + c - LANE_HALF / v, t + c + LANE_HALF / v
            if a > hi + GAP_MARGIN or b < lo - GAP_MARGIN:
                continue                # passed long before, or long after
            break
        else:
            return t
        t += STEP
    return None


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
    global solids, SUPER, PLAZA, UNDER
    solids = Solids.load(SOLIDS)
    UNDER = surfacer()
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

    # who shares a lane with whom, so a hold can check what it is backing into.
    # Holds the Car objects and reads `c.p0` live, so it stays correct as the
    # passes move things.
    lanes = {}
    for c in cars:
        lanes.setdefault((c.axis, round(c.lane, 2)), []).append(c)

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
            # A HOLD HAS TO PASS EVERYTHING THE PLACEMENT PASSED, and for a
            # long time it passed less. Moving a car up to 45 m back along its
            # lane gives it a different ten seconds, so it is a new placement,
            # not an adjustment - and this checked one point against the
            # buildings and the superblock, where `path_blocked` checks the
            # whole path against those PLUS the Obelisco's island. Every
            # failure it let through was silent, because frame 1 always looked
            # right:
            #
            #   a bus held into the plaza clipped two people standing on the
            #   island, and
            #   a car held back 36 m landed on the car behind it, where it then
            #   stayed for all 624 frames, since everything in a lane shares
            #   one speed. Seven pairs shipped like that, one at a separation
            #   of exactly zero.
            #
            # So the hold is applied, tested with the same function that vets
            # every other vehicle, and rolled back if it does not hold up.
            p = late.p0 - late.dir * back
            if tailgated(late, p, lanes):
                continue
            was = late.p0
            late.p0 = p
            if path_blocked(late):
                late.p0 = was
                continue
            late.held += back
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

    # and say out loud that nothing shares a lane position, because that is
    # what the holds above quietly broke for a long time. Measured after the
    # culls, on what actually ships.
    stacked = 0
    for k, group in lanes.items():
        live = sorted((c for c in group if c in cars), key=lambda c: c.p0)
        for a, b in zip(live, live[1:]):
            if b.p0 - a.p0 < half_len(a.ob.name) + half_len(b.ob.name):
                stacked += 1
                print(f"    STACKED: {a.ob.name} and {b.ob.name} share lane "
                      f"{k} at {a.p0:.1f} / {b.p0:.1f}")
    print(f"  vehicles overlapping another in their own lane: {stacked}")

    drive(cars)
    people, still = walkers(scene, r)
    # after drive(), and it has to be: every crossing is timed against where
    # the vehicles ACTUALLY end up, which is not where step 05 put them - the
    # holds above move cars up to 45 m back along their lane, and the culls
    # take some off the road entirely. Timed against step 05's positions the
    # pedestrians would be avoiding traffic that is no longer there.
    cross, walked, waiting = crossers(scene, cars, r)
    heli = helicopter(scene)
    print(f"  walking: {people} people ({still} left standing)   helicopter: "
          f"{'yes' if heli else 'no Heli in the kit'}")
    print(f"  crossing: {cross} at a zebra - {walked} found a gap in the "
          f"traffic and crossed, {waiting} are waiting at the kerb")

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
