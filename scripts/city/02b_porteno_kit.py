"""Step 02b — the kit assets that make the city read as Buenos Aires.

Three additions, chosen by what survives being twelve pixels tall seen from
above. That rules out most of what makes a city recognisable at eye level:
tiled pavements, cafe tables, kiosks and painted party walls are all invisible
from here. What is left is silhouette and colour.

JACARANDA. The strongest of the three by a distance, and the cheapest. In
bloom the canopy is violet, and a violet tree in a green street is legible at
any size, from any angle, with no detail at all. It is also the only one of
these that is already everywhere in the city rather than in one place.

TAXI. Black body, yellow roof. This camera looks down, so what it sees of a
car is almost entirely its roof: a livery whose distinguishing feature is the
roof colour is a piece of luck and it should be used.

COLECTIVO. Buenos Aires buses are painted per line, in flat saturated
two-tone, which reads as a small bright rectangle among the cars.

These are added to the KIT rather than built into step 02, so that step does
not have to be re-run: rebuilding the kit makes new mesh datablocks and every
instance in the city goes on pointing at the old ones.

    ./bl scripts/city/02b_porteno_kit.py
"""
import sys, pathlib, math, random

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy
from _common import (Mesh, mat, pbrmat, paint, counts, open_city, save_city)


# Measured off photographs of the trees in flower, not off the name of the
# colour: jacaranda reads blue-violet in sun and closer to lilac in shade.
JACARANDA = [("Jacaranda Deep", "#6c5bb8"),
             ("Jacaranda Mid", "#8878d6"),
             ("Jacaranda Pale", "#a99ae4")]
LIVERIES = [("#c62828", "#f2efe6"),        # red over cream
            ("#1b5fa8", "#f2c300"),        # blue over yellow
            ("#2f7d46", "#f2efe6"),        # green over cream
            ("#e2601a", "#1b5fa8")]        # orange over blue


def _disc(cx, cy, cz, radius, width, segs=8):
    v, f = [], []
    for side in (-1, 1):
        for i in range(segs):
            a = 2 * math.pi * i / segs
            v.append((cx + radius * math.cos(a), cy + side * width / 2,
                      cz + radius * math.sin(a)))
    for i in range(segs):
        j = (i + 1) % segs
        f.append((i, j, j + segs, i + segs))
    f.append(tuple(range(segs)))
    f.append(tuple(range(2 * segs - 1, segs - 1, -1)))
    return v, f


def wheels(m, length, width, kind="sedan"):
    wb, tw = length * 0.31, width / 2 - 0.06
    zw = 0.34 if kind not in ("bus", "truck") else 0.45
    for sx in (-1, 1):
        for sy in (-1, 1):
            v, f = _disc(sx * wb, sy * tw, zw, zw, 0.16)
            m._add(v, f, mat("Tire"))


def jacaranda(name, height, foliage, lobes, seed, kit):
    """Same construction as the other broadleaves, so it sits in the same rows
    without looking like it came from somewhere else. Only the colour differs,
    and a slightly wider, flatter crown, which is what a jacaranda has."""
    rnd = random.Random(seed)
    m = Mesh()
    trunk_h = height * 0.36
    m.cyl((0, 0, 0), height * 0.033, trunk_h, mat("Trunk"), segs=6,
          top=height * 0.026)
    canopy_r = height * 0.34
    for i in range(lobes):
        a = 2 * math.pi * i / lobes + rnd.uniform(-0.4, 0.4)
        d = 0 if i == 0 else canopy_r * rnd.uniform(0.40, 0.62)
        m.sphere((d * math.cos(a), d * math.sin(a),
                  trunk_h + canopy_r * rnd.uniform(0.45, 0.70)),
                 canopy_r * rnd.uniform(0.60, 0.92), foliage,
                 segs=7, rings=5, scale=(1.0, 1.0, rnd.uniform(0.58, 0.74)))
    return m.build(name, kit)


def taxi(name, kit):
    """Black with a yellow roof, which from directly above is a yellow car."""
    length, width = 4.4, 1.8
    body, roof = mat("Taxi Black"), mat("Taxi Yellow")
    m = Mesh()
    # Ley 2.148 art. 12.3.3.1: black below, yellow from the lower line of the
    # window upward. So the whole greenhouse is yellow with a glass band cut
    # into it, not a black cabin with a yellow lid. It matters here more than
    # it would at eye level: this camera sees a car almost entirely from above,
    # so the yellow area is most of what the vehicle is.
    m.box((0, 0, 0.62), (length, width, 0.72), body)
    m.box((-0.25, 0, 1.24), (length * 0.46, width * 0.86, 0.60), roof)
    m.box((-0.25, 0, 1.16), (length * 0.47, width * 0.88, 0.34),
          mat("Car Glass"))
    # the roof sign, the other half of the read
    m.box((0.55, 0, 1.62), (0.75, 0.34, 0.18), roof)
    wheels(m, length, width)
    return m.build(name, kit)


def colectivo(name, lower, upper, kit):
    length, width = 11.0, 2.5
    lo, up, glass = mat(lower), mat(upper), mat("Car Glass")
    m = Mesh()
    m.box((0, 0, 0.75), (length, width, 1.00), lo)          # skirt
    m.box((0, 0, 1.83), (length, width, 1.16), up)          # roof band
    for k in range(6):
        m.box((-length / 2 + 1.1 + k * (length - 2.2) / 5.5, 0, 1.75),
              (1.05, width + 0.04, 0.72), glass)
    m.box((length / 2 - 0.02, 0, 1.75), (0.08, width * 0.86, 0.8), glass)
    # the stripe between the two colours: on a real one this is where the
    # fileteado goes, and at this size a stripe is all of it that survives
    m.box((0, 0, 1.26), (length, width + 0.05, 0.13), up)
    wheels(m, length, width, "bus")
    return m.build(name, kit)


def main():
    open_city(needs_collections=("KIT",), hint="run 02_kit.py first")
    kit = bpy.data.collections["KIT"]
    for name, hexcol in JACARANDA:
        pbrmat(name, hexcol, 0.80)
    paint("Taxi Black")
    paint("Taxi Yellow")
    for lo, up in LIVERIES:
        pbrmat(f"Livery {lo}", lo, 0.50)
        pbrmat(f"Livery {up}", up, 0.50)

    made = []
    for ob in list(kit.objects):
        if ob.name.startswith(("Jacaranda", "Taxi", "Colectivo")):
            bpy.data.objects.remove(ob, do_unlink=True)

    for i, (mname, _) in enumerate(JACARANDA):
        made.append(jacaranda(f"Jacaranda{i}", 9.0 + i * 1.4, mat(mname),
                              3 + i % 2, 4200 + i, kit))
    made.append(taxi("Taxi", kit))
    for i, (lo, up) in enumerate(LIVERIES):
        made.append(colectivo(f"Colectivo{i}", f"Livery {lo}",
                              f"Livery {up}", kit))

    # the masters park off to the side, out of the city, like the rest of the
    # kit: step 08 deletes whatever stands inside the letters and it skips the
    # KIT collection precisely because these live near the origin
    for k, ob in enumerate(made):
        ob.location = (-620.0 + k * 14.0, -620.0, 0.0)

    rads = {ob.name: max(math.hypot(v.co.x, v.co.y) for v in ob.data.vertices)
            for ob in made}
    print("\n  added to the kit:")
    for n, rr in sorted(rads.items()):
        print(f"    {n:14s} plan radius {rr:5.2f} m")
    u, t = counts()
    print(f"  triangles: {u} unique / {t} total")
    save_city()


main()
