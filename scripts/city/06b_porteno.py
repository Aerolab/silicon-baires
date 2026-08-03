"""Step 06b — the landmarks that say Buenos Aires.

Step 02b handles the things that are everywhere: the jacarandas, the taxis,
the colectivos. This handles the three that are somewhere in particular.

THE OBELISCO. 67.5 m tall on a 6.8 m square base, which makes it taller than
every building in this city including the eighteen-floor tower. That is the
whole reason it works from a camera that flattens everything else into roofs:
it is the only vertical in frame. It goes one block off the title rather than
next to it, because two things that tall in the middle of a frame argue.

THE CUPOLAS. Domes on the corners of buildings on street corners. This is the
one eye-level Buenos Aires detail that survives being seen from above, because
a dome is a silhouette rather than a texture, and downtown is full of them.

FLORALIS GENERICA. Six steel petals, 23 m tall, about 20 m across. In a plaza
it reads as a large bright metal star, which nothing else in the city does.

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

OBELISCO = (3, 4)          # the plaza it stands on
FLORALIS = (5, 4)
# real numbers, and they matter: the ratio of a 67.5 m shaft to a 6.8 m base
# is what makes it read as the Obelisco rather than as a generic spire
OB_H, OB_BASE, OB_TOP, OB_CAP = 67.5, 6.8, 3.5, 3.5
FLOR_H, FLOR_D, PETALS = 23.0, 20.0, 6


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
    shaft = OB_H - OB_CAP
    # eight segments rather than one, so the silhouette stays faceted like
    # everything else here instead of turning into the one smooth object
    for k in range(8):
        t0, t1 = k / 8, (k + 1) / 8
        taper(m, cx, cy, z + shaft * t0, z + shaft * t1,
              OB_BASE + (OB_TOP - OB_BASE) * t0,
              OB_BASE + (OB_TOP - OB_BASE) * t1, stone)
    taper(m, cx, cy, z + shaft, z + shaft + OB_CAP, OB_TOP, 0.25, stone)
    # the door at the foot and the four small openings near the top: two
    # marks, and they are the only detail on it that is not the taper
    m.slab(cx, cy - (OB_BASE / 2 + 0.05), 2.2, 0.2, z + 0.1, z + 4.0, dark)
    for sx, sy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        w = OB_BASE + (OB_TOP - OB_BASE) * 0.93
        m.slab(cx + sx * (w / 2 + 0.05), cy + sy * (w / 2 + 0.05),
               0.9 if sy else 0.2, 0.2 if sy else 0.9,
               z + shaft * 0.93, z + shaft * 0.93 + 1.3, dark)
    return OB_BASE + 5.0, lift + OB_H + 1.0


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
    m.cyl((cx, cy, z), 7.0, 0.5, mat("Water"), segs=24)
    m.cyl((cx, cy, z + 0.5), 1.1, FLOR_H * 0.42, steel, segs=10, top=0.8)
    base = z + FLOR_H * 0.42
    for k in range(PETALS):
        a = 2 * math.pi * k / PETALS
        lean = math.radians(52)
        x = (Matrix.Translation(Vector((cx, cy, base))) @
             Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(lean, 4, "Y"))
        length = FLOR_H * 0.62
        # the petal is a long tapered blade lying along local +Z once leaned
        taper(m, 0, 0, 0.0, length, 2.6, 5.2, steel, x)
        taper(m, 0, 0, length, length + 2.4, 5.2, 0.6, steel, x)
    return FLOR_D, lift + FLOR_H


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

    lots = {tuple(l["key"]): l for l in
            json.loads((R / "city_lots.json").read_text())["lots"]}

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

    lot = lots.get((str(OBELISCO[0]), str(OBELISCO[1])))
    if lot is None:
        raise SystemExit("no lot for the obelisco: the layout moved under it")
    plaza(g, lot["x"], lot["y"], lot["size"][0], lot["size"][1], lot["lift"])
    side, ztop = obelisco(m, lot["x"], lot["y"], lot["lift"])
    sol.add(lot["x"], lot["y"], side, side, 0.0, 0.0, ztop)
    print(f"  obelisco at ({lot['x']:.0f}, {lot['y']:.0f}), "
          f"top at {ztop:.1f} m")

    lot = lots.get((str(FLORALIS[0]), str(FLORALIS[1])))
    if lot is not None:
        plaza(g, lot["x"], lot["y"], lot["size"][0], lot["size"][1],
              lot["lift"])
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
