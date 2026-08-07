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

THERE ARE NO CUPOLAS ANY MORE, and the reason is worth keeping. A dome is a
real porteno cue and it does survive this camera, so it was built - scattered
across roofs at a fixed rate. It looked wrong, and the first fix was to put
each one on an actual street corner instead of a random corner of a published
box, which is correct and was still not enough. What was missing is that a
cupola belongs to a KIND OF BUILDING: it crowns an academic pile with a
mansard and a corner rotunda, and stuck on a flat modern office block it reads
as a hat on the wrong head however carefully it is placed. Adding one dome is
cheap; adding the building it belongs to is a different job. Until that job is
done there are none, because a cue that reads as a mistake is worse than an
absent cue.

FLORALIS GENERICA. Six steel petals of 20 m and four stamens, 23 m to the tips
and 26 above them, over a 44 m pool. It is the only polished thing in the city.
It goes at the far end from the Obelisco: in Buenos Aires they are four
kilometres apart and putting them on adjacent blocks made a souvenir shelf out
of the middle of the frame.

The petals are dished leaves on curved spines, not flat tapers - see blade().
Flat, and whatever you call it, it reads as a six-pointed star. And the stamens
were simply missing: they are what makes it that flower rather than a generic
metal one.

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
from _common import (Mesh, mat, paint, counts, R, LOTS,
                     SOLIDS, open_city, save_city, purge, preview)
from _solids import Solids


# The Obelisco does not stand on a block. It stands in the middle of the
# avenue, on the island step 03 opens for it at the crossing, which is where
# the real one is - Plaza de la Republica is a hole in the traffic, not a
# square beside it. Its position comes out of city_lots.json.
FLORALIS = (5, 3)
# One block off the title was wrong in the way that only shows once you look at
# the whole frame: the Obelisco, the Floralis and the word were inside three
# adjacent blocks, so the eye had three things to look at in the middle and
# nothing anywhere else. That rule still holds, and it is why this is (5, 3) and
# not (4, 3) or (5, 4), which are equally central and both touch the title
# superblock.
#
# But the answer that rule first produced - (2, 7), the far corner - was right
# for a STILL and wrong once the camera moved. The shot sweeps a narrow diagonal
# corridor and crosses 13 of the 81 blocks; (2, 7) is 2.83 frame half-widths off
# the nearest point of it, so the Floralis was never in the film at all. (5, 3)
# is 0.08 off the axis and is centred at 54 % of the move, in the gap between
# the Obelisco leaving frame and the title arriving.
#
# A composition rule written for one frame does not survive a camera move by
# itself. Check it against the corridor, not against the hero still.
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
# Sourced: six petals of 20 m and four stamens, about 23 m to the top of the
# petals and 25 to the stamens, 18 tonnes, over a 44 m pool. An early pass had
# it 20 m across over a 14 m pool, which made it a sculpture on a lawn instead
# of the thing that fills its own plaza.
#
# The stem height is not a free choice. A 20 m petal reaching 16 m out and
# 23 m up has to start at about 9.5 m, or the arithmetic does not close: the
# straight line from a 5 m root to the tip is already 23 m long. That is why
# the real flower sits up in the air on a stalk rather than opening off the
# ground, and getting it wrong is what made the first version look like a
# desk ornament.
FLOR_H, FLOR_D, FLOR_POOL, PETALS = 23.0, 32.0, 44.0, 6
FLOR_STEM = 9.5               # where the petals start
FLOR_STAM = 26.5              # the stamens finish well above the petals
# Six petals at a 16 m radius have about 16.7 m of arc each. 7.2 read as six
# separate blades with sky between them, which is a star; 13.5 closed the gaps
# entirely and made one continuous bowl, which is a cup. The flower needs the
# V-shaped notches between petals to be visible, so about two thirds of the
# available arc.
FLOR_PETAL_W = 10.6           # width at the tip, where a petal is widest
FLOR_STAM_LEAN = 2.8          # how far the stamens lean out of the bowl
# How close a building's corner has to be to a block corner to count as a
# corner building. The lot in the JSON is the interior - the pavement is
# already taken off it - and step 04 sets the wall back another 0.5 to 1.3,
# then publishes the box 0.45 proud of that. So the honest gap is small and
# the tolerance only has to cover the setback.


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


def blade(m, material, r0, z0, r1, z1, width, xform,
          segs=12, across=6, curl=math.radians(52), thick=0.30, root=0.19):
    """One petal, and it is a SCOOP: a deep trough that widens to a broad
    rounded tip, curling in towards the axis.

    Measured off photographs after two versions that were wrong in different
    ways. What decides whether this is a flower or a six-pointed star:

    IT CURLS INWARD, hard, and the section is a CIRCULAR ARC - `curl` is the
    half-angle of that arc. The six petals together make a bowl. Earlier
    versions had a shallow parabolic dish, which is a flat blade with a crease
    in it; then a deep parabolic one, which is worse - a parabola keeps
    steepening, so the edges shot up into two spikes and the petal came out as
    a folded paper dart. An arc has constant curvature and reads as sheet metal
    bent on a roller, which is what it is.

    IT WIDENS TOWARDS THE TIP. Narrow at the root, widest at the very top,
    where neighbouring petals nearly touch. It was widest at 40 % out and came
    to a point, which is a leaf. This is a scoop.

    THE TIP IS BROAD AND ROUNDED, not a point. The real petal ends in a wide
    arc. A pointed tip is what makes a star out of six of anything.
    """
    def spine(t):
        # Out first, up second, and it is the TANGENT AT THE TIP that decides
        # whether this is a bowl or an umbrella. The previous pair reached t=1
        # with dz/dt = 0 - dead horizontal - so every petal finished by
        # flattening outward and the flower read as a blown-out umbrella. Here
        # the radius eases off (t^0.8) while the height accelerates (t^1.5), so
        # the tip leaves at about 60 degrees above horizontal: a wide shallow
        # floor that turns up into near-vertical walls, which is a bowl.
        return (r0 + (r1 - r0) * t ** 0.8,
                z0 + (z1 - z0) * t ** 1.5)

    def half(t):
        # root -> full width, then rounded off over the last 12 % so the tip
        # is an arc rather than a point
        w = width * 0.5 * (root + (1.0 - root) * t ** 0.72)
        if t > 0.88:
            u = (t - 0.88) / 0.12
            w *= math.sqrt(max(0.0, 1.0 - u * u))
        return max(0.06, w)

    verts, faces = [], []
    stride = 2 * (across + 1)
    for i in range(segs + 1):
        t = i / segs
        r, z = spine(t)
        ra, za = spine(max(0.0, t - 0.02))
        rb, zb = spine(min(1.0, t + 0.02))
        dr, dz = rb - ra, zb - za
        n = math.hypot(dr, dz) or 1.0
        nr, nz = -dz / n, dr / n            # normal, in the radial plane
        hw = half(t)
        arc = hw / math.sin(curl)           # radius of the section's arc
        for layer in (0, 1):
            for k in range(across + 1):
                phi = curl * (-1.0 + 2.0 * k / across)
                d = arc * (1.0 - math.cos(phi)) - (thick if layer else 0.0)
                verts.append((r + nr * d, arc * math.sin(phi), z + nz * d))
    for i in range(segs):
        for k in range(across):
            a = i * stride + k
            b = (i + 1) * stride + k
            faces.append((a, a + 1, b + 1, b))                     # top
            faces.append((b + across + 1, b + across + 2,
                          a + across + 2, a + across + 1))         # underside
        for k, flip in ((0, True), (across, False)):               # the edges
            a = i * stride + k
            b = (i + 1) * stride + k
            q = (a, b, b + across + 1, a + across + 1)
            faces.append(q if flip else tuple(reversed(q)))
    m._add(verts, faces, material, xform)


def floralis(m, cx, cy, lift):
    """Six petals and four stamens, opened. Steel: the only polished thing in
    the city, which is what makes it read at this size.

    Sourced: six petals of 20 m and four stamens, about 23 m overall, over a
    44 m pool. The stamens were simply missing before, and they are the part
    that stops it from being a flower-shaped thing and makes it that flower -
    four thin verticals standing up out of the middle of the bowl.
    """
    steel = mat("Steel Bright")
    z = lift
    m.cyl((cx, cy, z), FLOR_POOL / 2, 0.4, mat("Water"), segs=32)
    # the stem, and it is tall: the petals of the real one start well above
    # head height and the whole flower sits up in the air on a stalk
    m.cyl((cx, cy, z + 0.4), 2.1, FLOR_STEM - 0.4, steel, segs=12, top=1.15)
    base = z + FLOR_STEM
    for k in range(PETALS):
        x = (Matrix.Translation(Vector((cx, cy, 0.0))) @
             Matrix.Rotation(2 * math.pi * k / PETALS + 0.22, 4, "Z"))
        blade(m, steel, 1.4, base, FLOR_D / 2, z + FLOR_H, FLOR_PETAL_W, x)
    # Four stamens: thin rods that lean out of the middle of the bowl, each
    # with a small ball on the end. Off the photograph they are slender - much
    # thinner than a first guess makes them - and the balls are small. Built
    # as a short stack of segments so they can lean progressively and read as
    # curved rather than as four straight pins.
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        segsn = 5
        z0s, z1s = base - 2.5, z + FLOR_STAM
        for i in range(segsn):
            t0, t1 = i / segsn, (i + 1) / segsn
            r_0 = FLOR_STAM_LEAN * t0 ** 1.8
            za, zb = z0s + (z1s - z0s) * t0, z0s + (z1s - z0s) * t1
            m.cyl((cx + r_0 * math.cos(a), cy + r_0 * math.sin(a), za),
                  0.30, zb - za, steel, segs=6, top=0.26)
            if i:                            # close the kink between segments
                m.sphere((cx + r_0 * math.cos(a), cy + r_0 * math.sin(a), za),
                         0.30, steel, segs=6, rings=3)
        m.sphere((cx + FLOR_STAM_LEAN * math.cos(a),
                  cy + FLOR_STAM_LEAN * math.sin(a), z1s), 0.80, steel,
                 segs=8, rings=5)
    return FLOR_POOL, z + FLOR_STAM


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
def main():
    open_city(needs_collections=("KIT", "SITE"), needs_files=(LOTS,),
              hint="run 03_ground.py first")
    paint("Obelisco Stone")
    paint("Obelisco Dark")
    paint("Paving Pale")
    paint("Steel Bright")
    paint("Shield Bronze")
    # the red tile of the plaza border. It is the only red on the ground in
    # the whole city, which is exactly why it works from this distance.
    paint("Tile Red")
    paint("Flag Blue")     # the celeste of the flag, sourced
    paint("Flag White")    # off the official 74ACDF

    data = json.loads((LOTS).read_text())
    lots = {tuple(l["key"]): l for l in data["lots"]}
    av = data.get("avenue9j")

    coll = purge("PORTENO")

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

    m.build("porteno", coll)
    g.build("porteno_ground", coll)
    sol.merge_into(SOLIDS, "porteno")

    u, t = counts()
    print(f"  triangles: {u} unique / {t} total")
    with preview(target=(0, 0, 0)):
        blib.render(str(R / "city_06b_porteno.png"), "EEVEE", samples=64,
                    resolution=(1600, 900),
                    exposure=bpy.context.scene.view_settings.exposure)
    save_city()


main()
