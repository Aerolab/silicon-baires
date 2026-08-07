"""Where a new brand fits, and on which wall. Ask before editing anything.

    ./bl scripts/city/90_brand_sites.py            the free buildings
    ./bl scripts/city/90_brand_sites.py 6.0        only those giving a logo >= 6 m

Adding six clients cost an afternoon and a dozen renders, and not one of those
renders was a matter of taste: every one of them was a question with a numeric
answer being answered by eye. There are four such questions, and this script
answers them together:

  WHICH BUILDING IS FREE?     Not which roof: which BUILDING. An L is several
                              wings, and the browser overlay marked every wing
                              free except the one with the sign, so it said 149
                              were free when 68 were. And "free" includes what
                              HERO moved: some brands have a record pointing at
                              one roof while their wordmark hangs off the
                              neighbour's wall, and those buildings read as
                              empty.

  WHICH WALL?                 Of the two faces this camera sees, the good one is
                              the one the camera actually sees and that faces
                              the street. The "longest" — which is what sounds
                              reasonable — is almost always the one inside the
                              complex.

  WHAT SIZE FITS?             A wordmark is bound by the width of the wall and a
                              symbol by its height, and the ground floor is set
                              back, so the logo lives between about 5 m and the
                              cornice.

  DOES THE CAMERA SEE IT?     Metres of wall are not seconds on screen. The
                              measure that matters is 93_check_signs': 5 % of
                              the frame width for 1 s.

What comes out of here is copied into `_brands.EXTRA` and `_brands.HERO`. The
full walkthrough is in CLAUDE.md, "How a brand gets added".
"""
import sys, pathlib, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
from _common import (SIGNS, SOLIDS, LOTS, BUILDINGS, shot_cover, FACES,
                     wall_seen, wall_to_street, brand_addresses)
from _solids import Solids
from _brands import HERO

# The same thing 93 measures: below this the brand is there and not delivered.
MIN_FRAC = 0.05
MIN_SECS = 1.0
# The ground floor is set back and the logo pushes inside it below this height.
# Measured: at 4.9 m there is wall, at 3.1 there is not. 99_check_overlap is
# what finds it.
GROUND = 5.0
# How much of the wall the camera has to see for it to be worth it. Below this
# the logo comes out cut by the neighbour's roof or by its own arm.
MIN_SEEN = 0.75
# A company logo goes over the pavement, not over an internal courtyard.
MAX_STREET = 8.0


def main():
    floor = float(sys.argv[-1]) if sys.argv[-1].replace(".", "").isdigit() \
        else 0.0
    for f in (BUILDINGS, SIGNS, SOLIDS, LOTS):
        if not f.exists():
            raise SystemExit(f"falta {f.name}: corré 04_buildings.py primero")
    sites = json.loads(BUILDINGS.read_text())["sites"]
    signs = json.loads(SIGNS.read_text())
    site = json.loads(LOTS.read_text())
    sol = Solids.load(SOLIDS)
    boxes = {(round(b[0], 1), round(b[1], 1)): b for b in sol.boxes
             if b[7] in ("buildings", "porteno")}

    taken = brand_addresses(sites, signs, HERO)
    rows = []
    for s in sites:
        at = tuple(s["at"])
        if at in taken:
            continue
        for wx, wy, w, d in s["wings"]:
            box = boxes.get((round(wx, 1), round(wy, 1)))
            if box is None or box[6] < GROUND + 4.0:
                continue
            top = box[6]
            for axis, side in FACES:
                run = d if axis == 0 else w
                # the logo lives between the ground floor and the cornice, and
                # is measured at the middle of that band
                tall = top - GROUND
                z = GROUND + tall / 2
                seen = wall_seen(sol, box, axis, z)
                street = wall_to_street(site, box, axis)
                if seen < MIN_SEEN or street > MAX_STREET:
                    continue
                # a horizontal wordmark is bound by the width; a square symbol
                # by the height. Both are reported: that is the next decision.
                word = min(run * 0.80, tall * 6.0)
                iso = min(run * 0.80, tall * 0.95)
                secs, frac = shot_cover(wx, wy, z, word, word / 5.0)
                if secs < MIN_SECS or max(word, iso) < floor:
                    continue
                rows.append((frac, secs, at, wx, wy, side, run, top,
                             word, iso, seen, street))

    rows.sort(reverse=True, key=lambda r: r[0])
    best = {}
    for r in rows:                       # one row per building: the best face
        best.setdefault(r[2], r)

    print(f"\n  {len(sites)} buildings, {len(taken)} with a brand, "
          f"{len(sites) - len(taken)} free")
    print(f"  of the free ones, {len(best)} have a wall the camera sees, that "
          f"faces the street and delivers >= {MIN_SECS:.0f} s\n")
    print(f"  {'frac':>6} {'secs':>5} {'building':>17} {'wall':>6} "
          f"{'run':>8} {'top':>6} {'wordmark':>9} {'symbol':>8} "
          f"{'seen':>5} {'street':>6}")
    for frac, secs, at, wx, wy, side, run, top, word, iso, seen, street in \
            sorted(best.values(), reverse=True, key=lambda r: r[0]):
        flag = "" if frac >= MIN_FRAC else "   << below 93's floor"
        print(f"  {frac:6.3f} {secs:5.1f} "
              f"({wx:7.1f},{wy:8.1f}) {side:>6} "
              f"{run:8.1f} {top:6.1f} {word:9.1f} {iso:8.1f} "
              f"{seen:5.0%} {street:6.1f}{flag}")

    if not best:
        print("  none. The corridor is full: the only way to add a brand is to "
              "take over\n  a sign that currently carries an invented name — "
              "list them with\n  93_check_signs and pin it with PIN.")
    print("\n  The coordinate goes into _brands.EXTRA as `at`, and the wall "
          "into that\n  brand's HERO entry as `facade_side`. See CLAUDE.md, "
          "\"How a brand gets added\".\n")


main()
