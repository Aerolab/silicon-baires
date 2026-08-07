"""Standing check — how many brands the shot actually delivers.

The whole point of the company signs is that they go past the camera. Nothing
in the build knew that. Signs were planned evenly over a 700 m city, the camera
crosses it on one 320 m diagonal, and the result was 77 signs planned, 18 in
frame, 14 distinct brands - a number nobody could have named before this file
existed, because a sign outside the shot looks exactly like a sign inside it
from every angle except the one that ships.

Three failures, and none of them raises anything:

  NOT IN THE SHOT     the sign is beautiful and off camera.
  TOO SMALL           it is in frame and four pixels wide.
  STUCK TOGETHER      two brands land on the same corner of the frame and read
                      as one busy patch instead of two clients.

Plus the rule that is not about the camera at all: ONE SIGN PER BUILDING. Two
brands on one address reads as one company with two logos.

    ./bl scripts/city/93_check_signs.py
"""
import sys, pathlib, json, math, collections

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
from _common import (SIGNS, BUILDINGS, FPS, FRAMES, ASPECT,
                     screen_xy, shot_at, shot_cover, brand_addresses)
from _brands import HERO, SHARED

# What counts as delivered. Both, not either: 5 per cent of the frame width is
# 96 px at 1080p, which is the point a wordmark stops being a coloured smudge,
# and a second is the point the eye has time to land on it.
MIN_FRAC = 0.05
MIN_SECS = 1.0
# and how far apart two of them have to be, as a fraction of the frame width
# they share. 0.10 is about a sign own width apart, centre to centre: enough
# that two brands read as two, and 0.12 was costing three of them.
MIN_GAP = 0.10


def where(s):
    """Where THIS sign is and what it measures, as actually built.

    `built` is written by 10_signs measuring the mesh; 04's record is the plan.
    For nearly all of them the two agree. For a `facade_only` brand they do not:
    the plan is an anchor that is never raised and says "roofmark, 7.1 m" while
    on the wall there is a 27.6 m wordmark, so this check reported exactly the
    best-delivered brands wrongly. If `built` is missing — a manifest from
    before 10 started writing it — it falls back to the plan, which is the old
    answer.
    """
    b = s.get("built")
    return (b[0], b[1], b[2], b[3], b[4]) if b else \
        (s["x"], s["y"], s["z"], s["w"], s["h"])


def main():
    # said here rather than left to `read_text`, which raises a FileNotFoundError
    # naming a path and no way to produce it. Same shape as the BUILDINGS guard
    # below, and the same shape `open_city(needs_files=...)` gives every step
    # that opens the .blend — this check never opens it.
    if not SIGNS.exists():
        raise SystemExit(f"\n  {SIGNS.name} is missing: run 04_buildings.py\n")
    signs = json.loads(SIGNS.read_text())
    if not any(s.get("built") for s in signs):
        print("  ! the manifest carries no `built`: run 10_signs.py and this\n"
              "    check starts measuring the mesh instead of the plan\n")

    rows = []
    for s in signs:
        if s.get("drop"):
            continue
        x, y, z, w, h = where(s)
        secs, frac = shot_cover(x, y, z, w, h)
        rows.append((s, secs, frac))

    seen = [(s, secs, frac) for s, secs, frac in rows if secs > 0]
    good = [(s, secs, frac) for s, secs, frac in seen
            if frac >= MIN_FRAC and secs >= MIN_SECS]
    brands = sorted({s["text"] for s, _, _ in good})

    print(f"  planned          {len(signs)}")
    print(f"  reach the frame  {len(seen)}")
    print(f"  legible          {len(good)}   "
          f"(>= {MIN_FRAC:.0%} of frame width, >= {MIN_SECS:.0f} s)")
    print(f"  DISTINCT BRANDS  {len(brands)}")

    dupes = [b for b, n in collections.Counter(
        s["text"] for s, _, _ in good).items() if n > 1]
    if dupes:
        print(f"  repeated on camera: {', '.join(sorted(dupes))}")

    # --- one sign per building ---------------------------------------------
    # BY `owner`, WHICH IS THE CELL, and not by the footprint box the sign falls
    # in. This test used to run against the boxes, on the argument that the
    # geometry is the fact and asking the sign is asking the code that placed it
    # whether it placed it right. The argument is good and the execution was
    # wrong: A BOX IS A WING, NOT A BUILDING. An L is several rectangles, and
    # two brands on two wings of the same address land in different boxes and
    # both passed. Tiendanube and Rebill shared a building that way.
    #
    # AND IT COUNTS WHAT HERO MOVED, which is the other half and the one that
    # was missing: a brand's wordmark can hang off another building's wall, so
    # an address carrying two brands could pass with both of them happy.
    # `brand_addresses` in _common is the answer, written once, and 90 uses the
    # same one to avoid offering a building that is taken.
    if not BUILDINGS.exists():
        raise SystemExit("city_buildings.json is missing: run 04_buildings.py")
    sites = json.loads(BUILDINGS.read_text())["sites"]
    shared = {k: sorted(v)
              for k, v in brand_addresses(sites, signs, HERO).items()
              if len(v) > 1 and k not in SHARED}
    for k in SHARED:
        print(f"  · two brands here by decision, {k}: {SHARED[k]}")
    if shared:
        print(f"\n  ✗ {len(shared)} buildings carry more than one sign:")
        for k, v in sorted(shared.items())[:8]:
            print(f"      {k}  {', '.join(v)}")
    else:
        print("\n  ✓ no building carries two signs")

    # --- how close they get on screen --------------------------------------
    # Only among signs on screen AT THE SAME TIME. Two signs 4 m apart in the
    # world that the shot never holds together are not a crowd.
    worst = []
    for f in range(1, FRAMES + 1, 8):
        width, (tx, ty) = shot_at(f)
        ox, oy = screen_xy(tx, ty, 0.0)
        here = []
        for s, secs, frac in good:
            sx, sy = screen_xy(*where(s)[:3])
            dx, dy = (sx - ox) / width, (sy - oy) / width
            if abs(dx) < 0.5 and abs(dy) < ASPECT / 2:
                here.append((dx, dy, s["text"]))
        for i in range(len(here)):
            for j in range(i + 1, len(here)):
                d = math.hypot(here[i][0] - here[j][0],
                               here[i][1] - here[j][1])
                worst.append((d, (f - 1) / FPS, here[i][2], here[j][2]))
    worst.sort()
    tight = [w for w in worst if w[0] < MIN_GAP]
    pairs = {tuple(sorted((a, b))) for _, _, a, b in tight}
    if pairs:
        print(f"\n  ✗ {len(pairs)} pairs closer than {MIN_GAP:.2f} of the frame:")
        for d, t, a, b in worst[:6]:
            print(f"      {d:.3f}  t={t:5.1f}s   {a} / {b}")
    else:
        closest = worst[0] if worst else None
        if closest:
            print(f"  ✓ closest pair {closest[0]:.3f} of the frame "
                  f"({closest[2]} / {closest[3]} at {closest[1]:.1f}s)")

    # --- the shape of the pass ---------------------------------------------
    print("\n  brands on screen through the shot:")
    for f in range(1, FRAMES + 1, 48):
        width, (tx, ty) = shot_at(f)
        ox, oy = screen_xy(tx, ty, 0.0)
        n = 0
        for s, secs, frac in good:
            sx, sy = screen_xy(*where(s)[:3])
            if abs(sx - ox) < width / 2 and abs(sy - oy) < width * ASPECT / 2:
                n += 1
        print(f"    t={(f - 1) / FPS:5.1f}s  {'█' * n} {n}")

    print("\n  " + ", ".join(brands))


main()
