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
from _common import (SIGNS, SOLIDS, BUILDINGS, FPS, FRAMES, ASPECT,
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
    """Dónde está y qué mide ESTE cartel, tal como quedó construido.

    `built` lo escribe 10_signs midiendo la malla; el registro de 04 es el
    plan. Para casi todos son lo mismo. Para una marca con `facade_only` no:
    el plan es un ancla que no se levanta y dice "roofmark de 7,1 m" mientras
    en la pared hay un logotipo de 27,6, así que este chequeo informaba mal
    justo las marcas que mejor se entregan. Si falta `built` - un manifiesto
    de antes de que 10 lo escribiera - cae al plan, que es la respuesta vieja.
    """
    b = s.get("built")
    return (b[0], b[1], b[2], b[3], b[4]) if b else \
        (s["x"], s["y"], s["z"], s["w"], s["h"])


def main():
    signs = json.loads(SIGNS.read_text())
    boxes = json.loads(SOLIDS.read_text())["boxes"]
    if not any(s.get("built") for s in signs):
        print("  ! el manifiesto no trae `built`: corré 10_signs.py y este\n"
              "    chequeo pasa a medir la malla en vez del plan\n")

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
    # POR `owner`, QUE ES LA CELDA, y no por la caja de footprint en la que cae
    # el cartel. Esta prueba se hacía contra las cajas con el argumento de que
    # la geometría es el hecho y preguntarle al cartel es preguntarle al código
    # que lo puso si lo puso bien. El argumento es bueno y la ejecución estaba
    # mal: UNA CAJA ES UN ALA, NO UN EDIFICIO. Una L son varios rectángulos, y
    # dos marcas en dos alas de la misma dirección caen en cajas distintas y
    # pasaban las dos. Tiendanube y Rebill compartieron edificio así.
    #
    # Y CUENTA LO QUE HERO MUDÓ, que es la otra mitad y la que faltaba: el
    # logotipo de una marca puede colgar de la pared de otro edificio, así que
    # una dirección con dos marcas encima podía pasar con las dos contentas.
    # `brand_addresses` en _common es la respuesta, una sola vez, y 90 usa la
    # misma para no ofrecer un edificio ocupado.
    if not BUILDINGS.exists():
        raise SystemExit("falta city_buildings.json: corré 04_buildings.py")
    sites = json.loads(BUILDINGS.read_text())["sites"]
    shared = {k: sorted(v)
              for k, v in brand_addresses(sites, signs, HERO).items()
              if len(v) > 1 and k not in SHARED}
    for k in SHARED:
        print(f"  · dos marcas por decisión en {k}: {SHARED[k]}")
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
