"""Dónde entra una marca nueva, y en qué pared. Contesta antes de tocar nada.

    ./bl scripts/city/90_brand_sites.py            los edificios libres
    ./bl scripts/city/90_brand_sites.py 6.0        solo los que dan un logo >= 6 m

Sumar seis clientes costó una tarde y una docena de renders, y ni uno de esos
renders fue por una decisión de gusto: fueron todos por preguntas que tienen
respuesta numérica y que se estaban contestando a ojo. Esas preguntas son
cuatro, y este script las contesta juntas:

  ¿QUÉ EDIFICIO ESTÁ LIBRE?   No qué techo: qué EDIFICIO. Una L son varias alas
                              y el overlay del navegador marcaba libre cada ala
                              que no fuera la del cartel, así que decía 149
                              libres cuando libres había 68. Y "libre" incluye
                              lo que HERO mudó: hay marcas cuyo registro apunta
                              a un techo y cuyo logotipo cuelga de la pared del
                              vecino, y esos edificios figuraban vacíos.

  ¿QUÉ PARED?                 De las dos caras que esta cámara ve, la buena es
                              la que la cámara realmente ve y da a la calle. La
                              "más larga" - que es lo que parece razonable - es
                              casi siempre la de adentro del complejo.

  ¿DE QUÉ TAMAÑO ENTRA?       Lo que ata a un logotipo es el ancho de la pared
                              y a un isotipo el alto, y la planta baja está
                              retranqueada, así que el logo vive entre los 5 m
                              y la cornisa.

  ¿LO VE LA CÁMARA?           Metros de pared no son segundos en cuadro. La
                              medida que importa es la de 93_check_signs: 5 %
                              del ancho de cuadro durante 1 s.

Lo que sale de acá se copia a `_brands.EXTRA` y `_brands.HERO`. El recorrido
completo está en CLAUDE.md, "Cómo se suma una marca".
"""
import sys, pathlib, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
from _common import (SIGNS, SOLIDS, LOTS, BUILDINGS, shot_cover, FACES,
                     wall_seen, wall_to_street, brand_addresses)
from _solids import Solids
from _brands import HERO

# Lo mismo que mide 93: por debajo de esto la marca está y no se entrega.
MIN_FRAC = 0.05
MIN_SECS = 1.0
# La planta baja está retranqueada y el logo se mete adentro si baja de acá.
# Medido: a 4,9 m hay pared, a 3,1 no. 99_check_overlap es quien lo encuentra.
GROUND = 5.0
# Cuánta pared tiene que ver la cámara para que valga la pena. Por debajo de
# esto el logo sale cortado por el techo del vecino o por el propio brazo.
MIN_SEEN = 0.75
# Un logo de empresa va sobre la vereda, no sobre un patio interno.
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
                # el logo vive entre la planta baja y la cornisa, y se mide
                # a media altura de esa banda
                tall = top - GROUND
                z = GROUND + tall / 2
                seen = wall_seen(sol, box, axis, z)
                street = wall_to_street(site, box, axis)
                if seen < MIN_SEEN or street > MAX_STREET:
                    continue
                # un logotipo horizontal: lo ata el ancho. Un isotipo cuadrado:
                # el alto. Se informan los dos, que es la decisión que sigue.
                word = min(run * 0.80, tall * 6.0)
                iso = min(run * 0.80, tall * 0.95)
                secs, frac = shot_cover(wx, wy, z, word, word / 5.0)
                if secs < MIN_SECS or max(word, iso) < floor:
                    continue
                rows.append((frac, secs, at, wx, wy, side, run, top,
                             word, iso, seen, street))

    rows.sort(reverse=True, key=lambda r: r[0])
    best = {}
    for r in rows:                       # una fila por edificio: la mejor cara
        best.setdefault(r[2], r)

    print(f"\n  {len(sites)} edificios, {len(taken)} con marca, "
          f"{len(sites) - len(taken)} libres")
    print(f"  de los libres, {len(best)} tienen una pared que la cámara ve, "
          f"da a la calle y entrega >= {MIN_SECS:.0f} s\n")
    print(f"  {'frac':>6} {'seg':>5} {'edificio':>17} {'pared':>6} "
          f"{'corrida':>8} {'alto':>6} {'logotipo':>9} {'isotipo':>8} "
          f"{'ve':>5} {'calle':>6}")
    for frac, secs, at, wx, wy, side, run, top, word, iso, seen, street in \
            sorted(best.values(), reverse=True, key=lambda r: r[0]):
        flag = "" if frac >= MIN_FRAC else "   << bajo el piso de 93"
        print(f"  {frac:6.3f} {secs:5.1f} "
              f"({wx:7.1f},{wy:8.1f}) {side:>6} "
              f"{run:8.1f} {top:6.1f} {word:9.1f} {iso:8.1f} "
              f"{seen:5.0%} {street:6.1f}{flag}")

    if not best:
        print("  ninguno. El corredor está lleno: la única forma de sumar una "
              "marca es\n  pisar un cartel que hoy lleva un nombre inventado - "
              "ver la lista con\n  93_check_signs y clavarlo con PIN.")
    print("\n  La coordenada va a _brands.EXTRA como `at`, y la pared a la "
          "entrada de\n  HERO como `facade_side`. Ver CLAUDE.md, "
          "\"Cómo se suma una marca\".\n")


main()
