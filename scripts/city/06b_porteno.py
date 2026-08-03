"""Step 06b — the landmarks that say Buenos Aires.

Step 02b handles the things that are everywhere: the jacarandas, the taxis,
the colectivos. This handles the three that are somewhere in particular.

THE OBELISCO. 67.5 m tall on a 6.8 m square base, which makes it taller than
every building in this city including the eighteen-floor tower. That is the
whole reason it works from a camera that flattens everything else into roofs:
it is the only vertical in frame. It stands in the middle of the 9 de Julio,
on the island step 03 opens at the crossing, because that is where the real one
is and because an avenue is the thing that explains it: a monument in a plaza
is a monument, and a monument in the middle of eight lanes is Buenos Aires.

THE CUPOLAS. Domes on the corners of buildings on street corners. This is the
one eye-level Buenos Aires detail that survives being seen from above, because
a dome is a silhouette rather than a texture, and downtown is full of them.

FLORALIS GENERICA. Six steel petals, 23 m tall, 32 m across, over a 44 m pool.
It reads as a large bright metal star, which nothing else in the city does. It
goes at the far end of the city from the Obelisco: in Buenos Aires they are
four kilometres apart and putting them on adjacent blocks made a souvenir
shelf out of the middle of the frame.

Everything here publishes its footprint, so step 05 keeps its trees out of it.
Run it before step 05 for that reason.

    ./bl scripts/city/06b_porteno.py
"""
import sys, pathlib, math, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Matrix, Vector
from _common import Mesh, collection, mat, pbrmat, rng, counts
from _solids import Solids

R = ROOT / "renders"

# The Obelisco does not stand on a block. It stands in the middle of the
# avenue, on the island step 03 opens for it at the crossing, which is where
# the real one is - Plaza de la Republica is a hole in the traffic, not a
# square beside it. Its position comes out of city_lots.json.
FLORALIS = (2, 7)
# One block off the title was wrong in the way that only shows once you look at
# the whole frame: the Obelisco, the Floralis and the word were inside three
# adjacent blocks, so the eye had three things to look at in the middle and
# nothing anywhere else. They are now at opposite ends of the city. From the
# hero azimuth the Obelisco falls on the left of the frame and the Floralis on
# the right, at about the same height, which is the band a camera move sweeps.
# Real numbers, checked against both Wikipedias rather than remembered, because
# the ratio of the shaft to the base is the whole reason it reads as the
# Obelisco and not as a generic spire.
#
# 67.5 m total, of which 63 m is shaft, from a square base to a 3.50 m square
# where the apex begins; the apex is therefore 4.5 m and ends blunt at 40 cm,
# not in a point. The sources disagree about the base: the Spanish article says
# 7 x 7 m in one place and 6.80 m per side in another. 6.8 is used here and the
# difference is 3 mm on screen.
OB_H, OB_SHAFT, OB_BASE, OB_TOP, OB_TIP = 67.5, 63.0, 6.8, 3.5, 0.40
# 23 m tall, 32 m across with the petals open, standing over a 44 m pool.
# The first pass had it at 20 m across over a 14 m pool, which made it a
# sculpture on a lawn instead of the thing that fills its own plaza.
FLOR_H, FLOR_D, FLOR_POOL, PETALS = 23.0, 32.0, 44.0, 6
FLOR_LEAN = math.radians(52)


def taper(m, cx, cy, z0, z1, w0, w1, material, xform=None):
    """A square shaft that narrows. Two prisms cannot do it and a scaled box
    cannot either; it is eight vertices and six faces, written out."""
    a, b = w0 / 2, w1 / 2
    v = [(cx - a, cy - a, z0), (cx + a, cy - a, z0),
         (cx + a, cy + a, z0), (cx - a, cy + a, z0),
         (cx - b, cy - b, z1), (cx + b, cy - b, z1),
         (cx + b, cy + b, z1), (cx - b, cy + b, z1)]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    m._add(v, f, material, xform)


def obelisco(m, cx, cy, lift):
    stone, dark = mat("Obelisco Stone"), mat("Obelisco Dark")
    z = lift
    m.slab(cx, cy, OB_BASE + 5.0, OB_BASE + 5.0, z, z + 0.9, mat("Paving Pale"))
    z += 0.9
    shaft = OB_SHAFT
    # eight segments rather than one, so the silhouette stays faceted like
    # everything else here instead of turning into the one smooth object
    for k in range(8):
        t0, t1 = k / 8, (k + 1) / 8
        taper(m, cx, cy, z + shaft * t0, z + shaft * t1,
              OB_BASE + (OB_TOP - OB_BASE) * t0,
              OB_BASE + (OB_TOP - OB_BASE) * t1, stone)
    taper(m, cx, cy, z + shaft, z + OB_H - 0.4, OB_TOP, OB_TIP * 2.2, stone)
    taper(m, cx, cy, z + OB_H - 0.4, z + OB_H, OB_TIP * 2.2, OB_TIP, stone)
    # the door at the foot and the four small openings near the top: two
    # marks, and they are the only detail on it that is not the taper
    m.slab(cx, cy - (OB_BASE / 2 + 0.05), 2.2, 0.2, z + 0.1, z + 4.0, dark)
    for sx, sy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        w = OB_BASE + (OB_TOP - OB_BASE) * 0.93
        m.slab(cx + sx * (w / 2 + 0.05), cy + sy * (w / 2 + 0.05),
               0.9 if sy else 0.2, 0.2 if sy else 0.9,
               z + shaft * 0.93, z + shaft * 0.93 + 1.3, dark)
    return OB_BASE + 5.0, lift + OB_H + 0.9


def shields(m, cx, cy, lift, radius=15.0):
    """The 24 provincial coats of arms set into the paving around the monument.

    They are 2 m discs on a 30 m ring, which is 14 px each from this camera:
    small, but a regular ring of them is the single most legible thing about
    Plaza de la Republica from above - more than any paving texture, because
    a ring is a shape and a texture is not.

    The radius is passed in now: the island in the avenue is 23 m across, and a
    30 m ring on it put eight of the twenty-four shields out on the asphalt.
    """
    for k in range(24):
        a = 2 * math.pi * k / 24
        m.cyl((cx + radius * math.cos(a), cy + radius * math.sin(a),
               lift + 0.05), radius / 15.0, 0.04, mat("Shield Bronze"),
              segs=10)


def plaza(m, cx, cy, w, d, lift):
    """Radial paving under it. Plaza de la Republica is not a rectangle and
    this block is, so the pattern is what carries the resemblance."""
    pale, mid = mat("Paving Pale"), mat("Paving")
    m.quad(cx, cy, w * 0.94, d * 0.94, lift + 0.03, pale)
    rings = 4
    for k in range(rings):
        rr = 6.0 + k * 5.0
        for s in range(16):
            if (s + k) % 2:
                continue
            a0 = 2 * math.pi * s / 16
            a1 = 2 * math.pi * (s + 1) / 16
            m.arc_band(rr, rr + 5.0, a0, a1, lift + 0.05, mid,
                       xform=Matrix.Translation(Vector((cx, cy, 0))))


def floralis(m, cx, cy, lift):
    """Six petals on a stem, opened. Steel: the only polished thing in the
    city, which is what makes it read at this size."""
    steel = mat("Steel Bright")
    z = lift
    m.cyl((cx, cy, z), FLOR_POOL / 2, 0.4, mat("Water"), segs=32)
    m.cyl((cx, cy, z + 0.4), 1.3, FLOR_H * 0.40, steel, segs=10, top=0.9)
    base = z + FLOR_H * 0.40
    # the petal leans out and the spread is what is published, so the length
    # is solved from it rather than picked: half the spread over sin(lean)
    total = (FLOR_D / 2) / math.sin(FLOR_LEAN)
    blade, tip = total * 0.86, total * 0.14
    for k in range(PETALS):
        a = 2 * math.pi * k / PETALS
        x = (Matrix.Translation(Vector((cx, cy, base))) @
             Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(FLOR_LEAN, 4, "Y"))
        # the petal is a long tapered blade lying along local +Z once leaned
        taper(m, 0, 0, 0.0, blade, 3.0, 6.4, steel, x)
        taper(m, 0, 0, blade, blade + tip, 6.4, 0.8, steel, x)
    return FLOR_POOL, lift + FLOR_H


def oval(cx, cy, rx, ry, segs=44):
    return [(cx + rx * math.cos(2 * math.pi * i / segs),
             cy + ry * math.sin(2 * math.pi * i / segs)) for i in range(segs)]


def republica(m, g, sol, cx, cy, rx, ry, lift):
    """What is actually around the Obelisco, off a photograph.

    Step 03 opens the oval island in the avenue; this dresses it. Three things
    do the work, and none of them is the paving pattern a plaza usually gets:

    THE RED BORDER. A band of red tile all the way round the edge. It is the
    strongest single element in the photograph after the monument itself - a
    saturated ring against grey asphalt and green median, and the only red on
    the ground anywhere in this city.

    THE TWO BEDS. Curved planting in each end of the oval, which is what stops
    the island from being a car park with a spire on it. They are ovals of
    their own rather than the real crescents: at this size the difference is
    two pixels and a crescent costs a boolean.

    THE FLAGPOLE. Argentine flag on a mast at the south end. It is 15 m of
    vertical in a frame where the only other vertical is the monument, and it
    is the cue that says which country this is without any text.
    """
    tile, pale, dark = mat("Tile Red"), mat("Paving Pale"), mat("Paving")
    z = lift
    g.flat(oval(cx, cy, rx - 0.5, ry - 0.5), z + 0.01, tile)
    g.flat(oval(cx, cy, rx - 3.6, ry - 3.6), z + 0.02, dark)
    # the beds: one in each end, clear of the monument's own apron.
    #
    # Into `g`, the ground mesh, and not into `m`. A 26 cm kerb is a floor and
    # not a solid, and the overlap check treats everything in `m` as something
    # to test against: built into `m` it reported a bus and two people standing
    # inside a planting bed, which is true, and useless - it is the same call
    # that was made for the plaza paving itself.
    for side in (-1, 1):
        by = cy + side * (ry * 0.58)
        g.prism(oval(cx, by, rx * 0.66, ry * 0.24), z, z + 0.26,
                mat("Sidewalk"))
        g.flat(oval(cx, by, rx * 0.66 - 0.6, ry * 0.24 - 0.6), z + 0.28,
               mat("Grass"))
    # the flagpole, in the end furthest from the monument's door
    fy = cy - ry * 0.80
    m.cyl((cx, fy, z), 1.9, 0.35, pale, segs=12)
    m.cyl((cx, fy, z + 0.35), 0.22, 18.0, pale, segs=8, top=0.14)
    # +135, the same number the mast discs needed and for the same reason: a
    # flag is a plane, and hung along a world axis it is edge-on to a camera at
    # azimuth 45 and disappears into a line. Turned into the diagonal it faces
    # the lens square.
    fx = (Matrix.Translation(Vector((cx, fy, 0.0))) @
          Matrix.Rotation(math.radians(135), 4, "Z"))
    for k, col in enumerate(("Flag Blue", "Flag White", "Flag Blue")):
        m.box((3.4, 0.0, z + 16.0 - k * 1.25), (6.4, 0.06, 1.25), mat(col), fx)
    # the pole IS solid and does get published: 18 m of it, and a tree or a
    # person growing through a flagpole is the same error as through a wall
    sol.add(cx, fy, 5.0, 5.0, 0.0, 0.0, z + 18.0)


def cupola(m, cx, cy, top, radius):
    """Drum, dome, lantern. Faceted on purpose, like everything else."""
    slate, trim = mat("Cupola Slate"), mat("Cupola Trim")
    m.cyl((cx, cy, top), radius * 1.12, 1.6, trim, segs=12)
    z = top + 1.6
    rings = 5
    for k in range(rings):
        t0, t1 = k / rings, (k + 1) / rings
        r0 = radius * math.cos(t0 * math.pi / 2)
        r1 = radius * math.cos(t1 * math.pi / 2)
        h = radius * 1.15
        m.cyl((cx, cy, z + h * t0), r0, h * (t1 - t0), slate, segs=12, top=r1)
    z += radius * 1.15
    m.cyl((cx, cy, z), radius * 0.22, radius * 0.5, trim, segs=8,
          top=radius * 0.18)
    m.cone((cx, cy, z + radius * 0.5), radius * 0.22, radius * 0.7, trim,
           segs=8)


def corner_domes(m, sol, boxes, props, removed, r):
    """On buildings that stand on a street corner, which is where they are in
    the real city. A dome in the middle of a block is a chapel, not a corner
    building, and it looks like a mistake."""
    n = 0
    for (cx, cy, w, d, rot, z0, z1, tag) in boxes:
        if tag != "buildings" or z1 < 12.0 or min(w, d) < 18.0:
            continue
        if r.random() > 0.16:
            continue
        # a corner of the roof, not the centre
        sx, sy = r.choice((-1, 1)), r.choice((-1, 1))
        rad = min(min(w, d) * 0.20, 5.0)
        px = cx + sx * (w / 2 - rad * 1.5)
        py = cy + sy * (d / 2 - rad * 1.5)
        # Step 04 furnished this roof before anybody thought of putting a
        # dome on it, so the corner usually already has a chiller on it. The
        # first version skipped those roofs and got three domes out of a whole
        # city, because a solar array reaches ten metres and there are not many
        # clear corners. The dome wins instead and the unit comes off: it is
        # the larger thing and it is the one that carries the resemblance.
        for ob, qx, qy, qr in list(props):
            if (px - qx) ** 2 + (py - qy) ** 2 < (rad * 1.3 + qr) ** 2:
                bpy.data.objects.remove(ob, do_unlink=True)
                props.remove((ob, qx, qy, qr))
                removed[0] += 1
        cupola(m, px, py, z1 - 0.85, rad)
        sol.add(px, py, rad * 2.6, rad * 2.6, 0.0, z1 - 0.85,
                z1 + rad * 2.4)
        n += 1
    return n


def main():
    bpy.ops.wm.open_mainfile(filepath=str(R / "city.blend"))
    pbrmat("Obelisco Stone", "#d9d2c2", 0.72)
    pbrmat("Obelisco Dark", "#2a2724", 0.80)
    pbrmat("Paving Pale", "#a8a294", 0.85)
    pbrmat("Steel Bright", "#c9ccd0", 0.22, metallic=0.9)
    pbrmat("Cupola Slate", "#4a6b63", 0.65)      # oxidised copper, not grey
    pbrmat("Cupola Trim", "#cfc7b4", 0.75)
    pbrmat("Shield Bronze", "#8a6a3c", 0.45, metallic=0.5)
    # the red tile of the plaza border. It is the only red on the ground in
    # the whole city, which is exactly why it works from this distance.
    pbrmat("Tile Red", "#9c4a33", 0.85)
    pbrmat("Flag Blue", "#74acdf", 0.70)     # the celeste of the flag, sourced
    pbrmat("Flag White", "#f2f2ee", 0.70)    # off the official 74ACDF

    data = json.loads((R / "city_lots.json").read_text())
    lots = {tuple(l["key"]): l for l in data["lots"]}
    av = data.get("avenue9j")

    if "PORTENO" in bpy.data.collections:
        c = bpy.data.collections["PORTENO"]
        for ob in list(c.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(c)
    coll = collection("PORTENO")

    r = rng(1810)
    m = Mesh()
    # the paving goes into a separate mesh from the monuments. It is a floor,
    # and 99_check_overlap.py treats "porteno" as something solid to test
    # against: with the paving in it, every person standing on the plaza was
    # reported as intersecting the ground they were standing on.
    g = Mesh()
    sol = Solids()

    if av is None:
        raise SystemExit("no avenue9j in city_lots.json: re-run step 03, or "
                         "the Obelisco has nowhere to stand")
    ox, oy, half_w, half_l = av["plaza"]
    lift = 0.24                            # the island, as step 03 built it
    # no radial paving here: step 03 already paved the island, and the pattern
    # is sized for a whole block. What the real plaza has instead is a red tile
    # border, two curved beds and a flagpole.
    republica(m, g, sol, ox, oy, half_w, half_l, lift)
    # 9 m, not 12: the ring has to sit on the monument's own apron, between the
    # two planting beds, or a third of the shields end up in the grass
    shields(g, ox, oy, lift + 0.03, radius=9.0)
    side, ztop = obelisco(m, ox, oy, lift)
    sol.add(ox, oy, side, side, 0.0, 0.0, ztop)
    print(f"  obelisco at ({ox:.0f}, {oy:.0f}) in the middle of the avenue, "
          f"top at {ztop:.1f} m")

    lot = lots.get((str(FLORALIS[0]), str(FLORALIS[1])))
    if lot is None:
        raise SystemExit(f"no lot {FLORALIS} for the floralis")
    plaza(g, lot["x"], lot["y"], lot["size"][0], lot["size"][1], lot["lift"])
    dia, ztop = floralis(m, lot["x"], lot["y"], lot["lift"])
    sol.add(lot["x"], lot["y"], dia, dia, 0.0, 0.0, ztop)
    print(f"  floralis at ({lot['x']:.0f}, {lot['y']:.0f}), "
          f"top at {ztop:.1f} m")

    boxes = Solids.load(R / "city_solids.json").boxes
    props = []
    for cname in ("ROOFPROPS", "SIGNS"):
        if cname in bpy.data.collections:
            for ob in bpy.data.collections[cname].objects:
                if ob.type != "MESH" or not ob.data.vertices:
                    continue
                rr = max(math.hypot(v.co.x, v.co.y) for v in ob.data.vertices)
                props.append((ob, ob.location.x, ob.location.y,
                              rr * max(abs(ob.scale.x), abs(ob.scale.y))))
    removed = [0]
    n = corner_domes(m, sol, boxes, props, removed, r)
    print(f"  cupolas: {n}   roof units removed for them: {removed[0]}")

    m.build("porteno", coll)
    g.build("porteno_ground", coll)
    sol.merge_into(R / "city_solids.json", "porteno")

    u, t = counts()
    print(f"  triangles: {u} unique / {t} total")
    cam = bpy.data.objects["HeroCam"]
    cam.data.ortho_scale = 170.0
    blib.render(str(R / "city_06b_porteno.png"), "EEVEE", samples=64,
                resolution=(1600, 900),
                exposure=bpy.context.scene.view_settings.exposure)
    blib.save(str(R / "city.blend"))


main()
