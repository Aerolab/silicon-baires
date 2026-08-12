"""Check that nothing has been built in front of a logo.

This is the failure the sign report cannot see. `93_check_signs` measures every
brand through `shot_cover`, and `shot_cover` PROJECTS: it takes the rectangle a
sign occupies, works out how much of the frame it covers and for how many
seconds, and knows nothing whatever about what stands between it and the
camera. So a wordmark with a tower in front of it keeps every number it had.

That is not hypothetical. Adding one building to this city put a tower across
Mercado Libre's west arm, and the report went on saying 45.0 m, 12.7 s and
0.208 of the frame - the largest sign in the city, by its own numbers, with
about a fifth of it visible. Nothing failed. The render is what caught it, and
the render only catches the one you happen to be looking at.

THE QUESTION IS ASKED OF THE GEOMETRY, and over the logo's own rectangle
rather than over its wall. `90_brand_sites` already measures walls with
`wall_seen`, at mid-height and across the full run, which is the right question
when you are choosing where a brand could go. It is the wrong one afterwards:
a wall can be 80 % clear and have the clear part above the sign. This samples
the band the artwork actually occupies, read out of `built` in the manifest -
what step 10 made, not what step 04 planned - and marches a ray from each
sample toward the camera.

IT IS NOT A CHECK ABOUT NEW BRANDS, and that is worth saying because a brand
added today passes it trivially: its wall was chosen with `wall_seen` in the
first place. It earns its keep on the change that comes AFTER - a building on a
free lot, a wing made taller, a landmark moved - which is exactly the class of
change that has no reason to think about somebody else's facade.

ROOF SIGNS ARE NOT ASKED. A parapet, a roofmark or a mast can be hidden too,
but the ray leaves those in a different direction and the honest thing is to
say this does not cover them rather than to run something that looks like it
does.

    ./bl scripts/city/89_check_blocking.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
from _common import SIGNS, SOLIDS, view_vector
from _solids import Solids
from _brands import HERO

# What 90_brand_sites demands of a wall before it will offer it, applied here
# to the logo rather than to the wall. Below this the brand is on the building
# and not in the video.
MIN_SEEN = 0.75
# Samples across the artwork, and a step coarse enough to run over a hundred
# signs without being so coarse it walks between two towers.
SAMPLES_U, SAMPLES_Z = 9, 5
STEP, FAR = 2.0, 90.0


def facade_walls():
    """Every brand HERO mounts on a wall, with the face it is mounted on.

    `facade_side` is not always a side. `wide` means "the longer of the two
    faces this camera sees", which is resolved at build time, and a brand with
    `facade_arts` carries one side PER ART - so reading the literal string
    reports the wrong wall for Basement and for both of Paisanos'.
    """
    out = []
    for brand, h in sorted(HERO.items()):
        at = h.get("facade_at")
        if not at or not h.get("facade"):
            continue
        for art in h.get("facade_arts", [h.get("facade_art", "word")]):
            side = h.get(f"{art}_facade_side") or h.get("facade_side", "left")
            out.append((brand, art, at, side))
    return out


def seen(sol, box, axis, cu, cz, width, height):
    """How much of a rectangle on the +axis face of `box` reaches the camera.

    The same march `wall_seen` uses, over the artwork instead of over the wall.

    CLAMPED TO THE FACE, and that is not tidiness. `built` is written per SIGN
    and a sign is one object: where a brand carries two installations they
    arrive as one bounding box around both. Takenos' is 55.5 m wide because it
    wraps a facade logo AND a roof panel on the wing next door, so sampling it
    raw walks 20 m of open air over a neighbouring roof and reports the brand
    as two thirds hidden. Reading it as "the part of that box that lies on THIS
    wall" is the same question asked correctly.
    """
    cx, cy, w, d = box[0], box[1], box[2], box[3]
    half = (w if axis == 0 else d) / 2
    run = d if axis == 0 else w
    face_c = cy if axis == 0 else cx
    lo = max(cu - width / 2, face_c - run / 2)
    hi = min(cu + width / 2, face_c + run / 2)
    if hi <= lo:
        return 1.0
    z_lo = max(cz - height / 2, 0.5)
    z_hi = min(cz + height / 2, box[6])
    vx, vy, vz = view_vector()
    clear = total = 0
    for i in range(SAMPLES_U):
        t = lo + (hi - lo) * i / max(1, SAMPLES_U - 1)
        px, py = ((cx + half + 0.3, t) if axis == 0 else (t, cy + half + 0.3))
        for j in range(SAMPLES_Z):
            z = z_lo + (z_hi - z_lo) * j / max(1, SAMPLES_Z - 1)
            total += 1
            k = STEP
            while k < FAR:
                hit = sol.hit(px + vx * k, py + vy * k, z + vz * k, 0.0,
                              tags=("buildings", "porteno"))
                if hit is not None and hit is not box:
                    break
                k += STEP
            else:
                clear += 1
    return clear / total if total else 1.0


def main():
    for f in (SIGNS, SOLIDS):
        if not f.exists():
            raise SystemExit(f"falta {f.name}: corré 04_buildings.py primero")
    signs = json.loads(SIGNS.read_text())
    sol = Solids.load(SOLIDS)
    built = {r["text"]: r["built"] for r in signs
             if r.get("text") and r.get("built")}

    rows, missing = [], []
    for brand, art, at, side in facade_walls():
        box = sol.hit(at[0], at[1], tags=("buildings", "porteno"))
        b = built.get(brand)
        if box is None or b is None:
            missing.append(brand)
            continue
        axis = 0 if side == "left" else 1
        bx, by, bz, bw, bh = b
        # `built` is a world bounding box: on a +X face the sign runs along y
        rows.append((seen(sol, box, axis, by if axis == 0 else bx, bz, bw, bh),
                     brand, art, side, bw))

    rows.sort()
    print(f"\n  {len(rows)} facade logos, sampled over the band each one "
          f"actually occupies\n")
    print(f"  {'seen':>6}  {'brand':<16} {'art':<7} {'face':<6} {'width':>7}")
    for s, brand, art, side, bw in rows:
        flag = "   <== BLOCKED" if s < MIN_SEEN else ""
        print(f"  {s:6.0%}  {brand:<16} {art:<7} {side:<6} {bw:7.1f}{flag}")
    if missing:
        print(f"\n  not measured (no wall or nothing built): "
              f"{', '.join(sorted(set(missing)))}")

    bad = [r for r in rows if r[0] < MIN_SEEN]
    print("\n  nothing is standing in front of a logo")
    if bad:
        print(f"    FAIL: {len(bad)} of {len(rows)}")
        for s, brand, art, side, bw in bad:
            print(f"      {brand:<16} {art:<7} {s:.0%} of it reaches the camera")
    else:
        print(f"    pass: all {len(rows)} reach the camera whole")
    print()


main()
