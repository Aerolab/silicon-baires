"""The real brands, one table, and the order is the priority.

`assign_brands()` in 04 hands out the names by visibility: it ranks the signs
by `shot_cover` and gives the most visible one the first unused entry. So the
ORDER OF THESE LISTS IS THE ORDER THE CAMERA FINDS THEM IN. The brands with an
SVG come first because they are the ones built in 3D, extruded from the real
curve; the ones that only exist as a bitmap come after, with a generic symbol;
and the invented ones go last, which is where the camera no longer reaches.

The table does not have to be any particular length. `DRAW_WIDTH` in 04 is
pinned for a different reason (the draw during placement consumes RNG and moves
buildings), and the brand that draw picks is a placeholder this table overwrites
wholesale at the end of the run.

`svg` is the file under `assets/logos/`. If it is None the brand falls back to
the geometric symbol in `mark`, which is the system the city was built with.
See `assets/logos/SOURCES.md` for where each file came from and what it lacks.

`face` is the colour of the sign and `ink` the colour of the logo. `ink` is only
used when the SVG is monochrome or declares no colour: when the file carries its
own palette (Globant is two colours, Pomelo is six) the file wins, because the
colour is part of the brand and not a decision this city gets to make.


## Adding a brand, in five steps

    ./bl scripts/city/90_brand_sites.py

reports the free buildings with the wall to use, how much of that wall the
camera sees, how far the kerb is and what size fits. Then:

  1. The SVG into `assets/logos/`, with explicit `width`/`height` taken from the
     `viewBox` — Blender's importer does not understand `width="100%"` and
     returns an empty curve without saying so. Record the source in
     `SOURCES.md`.
  2. The brand into `CAMPUS` (B2B) or `AVENUE` (consumer), with its colour.
  3. The building into `EXTRA`, with the coordinate 90 reported. It is an
     ANCHOR: nothing is built from it, it exists so the manifest has a record to
     pin the brand to.
  4. The wall into `HERO`, with `facade_only` and the `facade_side` 90 reported.
     A wordmark is bound by the width of the wall, a symbol by its height, and
     the ground floor is set back: the logo lives between about 5 m and the
     parapet.
  5. `./bl scripts/city/04_buildings.py && ./bl scripts/city/10_signs.py`, and
     LOOK AT THE RENDER. Then the whole chain from 06, and 93 for the number.

What NOT to re-derive — each one of these cost a render:

  · A logo goes on the FRONT, not on the roof. A roofmark at 250 m is a pale
    rectangle; a wall is 28 m of letters.
  · "The longest face" is almost always the one inside the complex.
  · A wall can face the street and still be hidden, by the other arm of its own
    L or by the neighbour a metre away. That is a sightline question.
  · One brand per address, and the address is the CELL, not the wing. The
    exceptions are declared in `SHARED` with their reason.
"""

# (text, mark, face, ink, svg)

# The office park: parapets, roofmarks and masts.
CAMPUS = [
    ("GLOBANT",   "chevron",  "#f7f3e8", "#272425", "globant.svg"),
    ("AEROLAB",   "disc",     "#1c1c1c", "#ff510d", "aerolab.svg"),
    ("VERCEL",    "triangle", "#111111", "#ffffff", "vercel.svg"),
    ("BASEMENT",  "square",   "#f7f3e8", "#111111", "basement.svg"),
    ("AUTH0",     "disc",     "#f7f3e8", "#ea5428", "auth0.svg"),
    ("SATELLOGIC", "ring",    "#f7f3e8", "#123a5e", "satellogic.svg"),
    ("POMELO",    "bars",     "#141118", "#e7377b", "pomelo.svg"),
    ("TECHNISYS", "ring",     "#f7f3e8", "#2b2b2b", "technisys.svg"),
    ("ALEPH",     "triangle", "#151515", "#ffffff", "aleph.svg"),
    ("TAKENOS",   "disc",     "#f7f3e8", "#6d37d5", "takenos_word.svg"),
    ("MERCADO PAGO", "disc",  "#f7f3e8", "#00bcff", "mp_iso.svg"),
    ("HUMAND",    "ring",     "#f7f3e8", "#182d7a", "humand.svg"),
    # These three are pinned through EXTRA, so their place in this list decides
    # nothing — the order above is the camera's, and a pinned brand never goes
    # through it. They are here so the brand exists with its colour.
    #
    # All three are stuck to a FACADE, with no panel behind them, so the wall
    # decides the colour rather than this table. Complif is the case
    # where it shows: both variants of the file were tried and looked at, and
    # the wall on that corner is dark brick, so the white one from the website
    # wins. The dark variant stayed in assets in case the brand moves to a light
    # wall. See SOURCES.md, which already recorded the same for four others.
    ("COMPLIF",   "ring",     "#1c1c1c", "#ffffff", "complif.svg"),
    ("REBILL",    "chevron",  "#f7f3e8", "#111111", "rebill.svg"),
    ("PAISANOS",  "square",   "#101820", "#ffffff", "paisanos.svg"),
    # Spot 75, the whole lockup on the long wall. See HERO for why that wall and
    # why the size is what it is.
    ("REVAMOS",   "triangle", "#101820", "#00d9bd", "revamos.svg"),
    # Dedicated facade-only installation; EXTRA fixes the building and wall.
    ("SLA",       "bars",     "#101113", "#eaeaea", "sla.svg"),
    # wordmark traced from the Commons PNG; the pin keeps it on Sign.069, whose
    # parapet builds it through the ordinary path. `ripio_iso.svg` is traced and
    # sitting in assets for a square site, and is deliberately NOT wired: see
    # the note in HERO for what wiring it cost.
    ("RIPIO",     "disc",     "#f7f3e8", "#7908ff", "ripio.svg"),
    ("ETERMAX",   "bars",     "#f7f3e8", "#28292b", "etermax_word.svg"),
    ("OLX",       "ring",     "#f7f3e8", "#6e2fb8", None),
    # The five below are all pinned as well, and all five are on a facade with
    # no panel behind them, so the wall decides the colour and not this table.
    # WHICH WALL EACH ONE GOT IS A COLOUR DECISION AS MUCH AS A SIZE ONE: the
    # five walls were read with a ray before anything was written, and they are
    # not the same material. OpenZeppelin's near-black wordmark and Bioceres'
    # navy went to the two grey concrete walls; Maslow, whose logo is WHITE on
    # the site and has no dark variant published, went to the teal one. Putting
    # them in the order 90 reported would have hung the white one on grey.
    ("OPENZEPPELIN", "square", "#f7f3e8", "#4f56fa", "openzeppelin.svg"),
    ("MURAL",     "disc",     "#f7f3e8", "#ff4b4b", "mural.svg"),
    ("MASLOW",    "triangle", "#101820", "#168bf6", "maslow.svg"),
    ("BIOCERES",  "ring",     "#f7f3e8", "#004676", "bioceres_word.svg"),
    # Spot 68, west of Humand. Facade is Patmos Black (see 04); the white
    # wordmark is what the landing publishes on dark ground.
    ("PATMOS",    "bars",     "#1a1a1d", "#f5f5f5", "patmos.svg"),
    # Pinned to Sign.025 — an OMBU roofmark, an invented name — and hung on the
    # south arm of Takenos' L, declared in SHARED. `ink` is a fallback nothing
    # reads: `conexa.svg` carries BOTH its colours, the white wordmark and the
    # flattened cyan symbol, and a forced ink would collapse the two into one.
    # See HERO for the wall and `conexa_plate.svg` for why it carries a ground.
    ("CONEXA",    "ring",     "#101820", "#00c9f4", "conexa.svg"),
]

# The avenue: party walls and billboards. It talks to whoever is driving, not to
# whoever is looking for a job, so the mass-market brands go here.
AVENUE = [
    ("MERCADO LIBRE", "disc",    "#ffe600", "#303576", "mercadolibre.svg"),
    ("UALA",         "chevron",  "#f7f7fb", "#406afc", "uala.svg"),
    ("NARANJA X",    "bars",     "#f7f3e8", "#f65100", "naranjax.svg"),
    ("DESPEGAR",     "triangle", "#f7f3e8", "#5516ec", "despegar.svg"),
    ("LEMON",        "square",   "#d6f24a", "#003f20", "lemon.svg"),
    ("TIENDANUBE",   "ring",     "#f7f3e8", "#111111", "tiendanube.svg"),
    ("DIGITAL HOUSE", "square",  "#101820", "#ffffff", "digitalhouse.svg"),
    # also pinned through EXTRA, so their place in this list decides nothing
    ("GALICIA",      "disc",     "#f7f3e8", "#ff7f00", "galicia_iso.svg"),
    ("CODERHOUSE",   "bars",     "#f7f3e8", "#1d1d1d", "coderhouse.svg"),
    # the other arm of Coderhouse's L, declared in SHARED. Pinned, so its place
    # in this list decides nothing; it is here so the brand exists with its
    # colour. White, because the mark goes on a dark plate of its own — see the
    # HERO entry for why that plate is not optional on this facade.
    ("BERRY",        "disc",     "#0a0a0b", "#f5f5f7", "berry_iso.svg"),
    ("BELO",         "disc",     "#f7f3e8", "#5300da", "belo.svg"),
    ("COCOS",        "ring",     "#f7f3e8", "#002c65", "cocos.svg"),
    ("BRUBANK",      "disc",     "#f7f3e8", "#614ad9", "brubank.svg"),
    # the icon alone — this brand publishes no wordmark in vector form, and a
    # square symbol is what the wall it got is bound by anyway
    ("DECENTRALAND", "disc",     "#f7f3e8", "#ff2d55", "decentraland.svg"),
    # no vector
    ("MODO",         "disc",     "#f7f3e8", "#00a15a", None),
]


def pools(campus_filler, avenue_filler):
    """The real ones first, the invented filler after.

    The filler is the tables 04 already had. They are not thrown away: there are
    100 signs and 38 real brands, so the rest — none of which reaches the camera
    at a legible size — still carry the invented ones. The ratio is the thing to
    watch rather than either number: every real brand added takes a record away
    from a made-up one, and six of them did exactly that in the last batch.
    """
    return ([b[:4] for b in CAMPUS] + list(campus_filler),
            [b[:4] for b in AVENUE] + list(avenue_filler))


LOGOS = {b[0]: b[4] for b in CAMPUS + AVENUE if b[4]}


# Brands that get the hero treatment.
#
# A whole wordmark hung off a parapet is the least legible of everything that
# was tried: the lockup's bounding box includes the symbol, the air and the
# ascenders, so at the height that fits under the eaves the letters come out the
# size of a window. Splitting it in two solves each half separately, and it is
# also how these are really mounted: the big symbol on the wall, which is a
# shape and reads at any distance, and the name laid flat on the roof, where it
# competes with nothing and can be forty metres long.
#
#   iso        the symbol alone, hung off the parapet
#   word       the wordmark alone, laid flat on the owning building's roof
#   iso_frac   height of the symbol as a fraction of the building's height
#   roof_frac  how much of the roof the wordmark may occupy
#   iso_ink    colour of the symbol, and word_ink that of the wordmark. There
#              are two because they are not always the same: Lemon is green on
#              top and black below.
#   face       overrides the colour of the sign carrying the symbol
#   roof_at    (x, y) of the roof the wordmark goes on. Without it, the roof of
#              the building that owns the sign is used, which is the normal
#              case; with it, the wordmark can cross to the roof next door,
#              which is what Lemon asked for.
HERO = {
    # ---- stuck to a wall, with nothing on the roof -------------------------
    # The entries below share one key and the key is `facade_only`: the logo on the
    # building's wall and NOTHING on the deck. Each one's anchor is in EXTRA (or
    # in PIN, for the two that reuse a switched-off billboard) and is never
    # built; the only thing that comes out of here is the wordmark on the
    # facade.
    #
    # WHICH FACE. This camera sees two of them, +X and +Y, and picking the
    # longest with "wide" is picking wrong: the long face of these buildings is
    # usually the one inside the complex. Belo, Paisanos and Complif ended up
    # hanging off a wall facing a courtyard 17–32 m from the street, and a
    # company logo goes over the pavement. The good face was measured against
    # the street table — the one with the kerb under 4 m away — and on all three
    # it is +Y, which is "right". The other two are Ls and there something else
    # decides: the face that does not look into its own arm. See the comment on
    # each.
    "SLA": {"word": "sla.svg", "iso": "sla.svg",
            "facade": True, "facade_only": True, "facade_art": "word",
            # The dedicated black building replaces the placeholder at cell 4,6.
            # Its +X face is deliberately broad and open to the camera.
            "facade_side": "left", "facade_at": (-26.0, 153.0),
            "facade_frac": 0.82, "facade_tall": 0.31,
            "facade_z": 0.67, "facade_depth": 0.36},
    "GALICIA": {"iso": "galicia_iso.svg", "word": "galicia_iso.svg",
                # the symbol only, because it is the only thing the current
                # brand has in vector form — see SOURCES.md. Square and large,
                # which is exactly what holds up best on a wall seen from 250 m
                "facade": True, "facade_only": True, "facade_art": "iso",
                # THE SMALL WING AND ITS NORTH FACE, and both of those cost a
                # render each. This building is an L: on the big wing the long
                # face looks into the other arm (the disc sat half inside it and
                # an orange sliver poked out behind the roof) and the other face
                # is 1.3 m from the neighbouring building, which hides it
                # entirely. The small wing has its north face in open air.
                "facade_side": "left", "facade_at": (165.3, 11.0),
                # what binds a square symbol is the HEIGHT of the wall, not its
                # width: at 0.52 the disc measured 12.7 m on a 27 m wall
                "facade_frac": 0.72, "facade_tall": 0.76,
                "facade_z": 0.62, "facade_depth": 0.45},
    "CODERHOUSE": {"word": "coderhouse.svg", "iso": "coderhouse.svg",
                   # 8.4:1 of a single word: what binds it is the width, which
                   # is why it goes on the long face of the tallest building
                   "facade": True, "facade_only": True,
                   # same L, same problem: on the long face the word ran half
                   # into the wing next door and read as "CODE"
                   "facade_side": "left", "facade_at": (201.8, -14.8),
                   # right at the top and with some body to it, which is the
                   # Basement recipe: this facade has a cornice per storey, and
                   # a flat word at mid-height comes out sliced into strips
                   "facade_frac": 0.86, "facade_tall": 0.22,
                   "facade_z": 0.93, "facade_depth": 0.55},
    # THE OTHER ARM OF CODERHOUSE'S L, spot 147, and asked for. The cell at
    # (201.75, -2.0) is two wings: Coderhouse is on (201.8, -14.8) and this is
    # (194.95, 10.83), 14.5 x 26.6 and the same 32.05 m top. Two brands on one
    # address, declared in SHARED with the same test the Ualá / Brubank pair
    # passes — the two walls are two PLANES, 13.7 m apart in x and 25 in y, and
    # the two logos sit at different heights (Coderhouse at 0.93 of the
    # parapet, this at 0.718), which is what stops the eye reading them as one
    # band of signage.
    #
    # THE +X FACE, AND THE KERB IS 16.8 m AWAY ON PURPOSE. Every other warning
    # in this file about a wall that far from a street is about a courtyard,
    # and this one is not: the strip in front was walked and it is empty —
    # open ground out to the kerb of the street at x=225, `wall_seen` 1.00 at
    # every height from 8 m up. The Revamos case exactly. The alternative, the
    # +Y face, has the pavement 2.9 m off and only 14.5 m of run, which lands
    # the symbol at 0.045 of the frame — under the 0.05 floor 93 measures, so
    # the brand would be there and not delivered. This face runs 26.6 and
    # clears it.
    #
    # AND IT NEEDS A PLATE, which is the whole reason this entry is not four
    # lines. The mark is a rosette of THIN RINGS and this facade is banded
    # every metre between `Glass Dark` #1c1e21 and `Concrete Warm` #e8dbbf.
    # Sampled across the run at the band the sign occupies it is roughly 56 %
    # glass and 44 % concrete, and no monochrome ink survives both — white is
    # 16.1:1 on the glass and 1.2:1 on the concrete, black is the same numbers
    # the other way round. The rule in CLAUDE.md says fit the logo inside one
    # clean band; here the longest one is 2.5 m, which on a 32 m building is a
    # symbol the shot cannot see. Mural's exception does not apply either —
    # that logo is black-and-primary and reads on everything it crosses, and
    # this one is one colour. So the mark brings its own ground, at 17.9:1, the
    # way Berry's own app icon draws it. See `berry_plate.svg`.
    #
    # THE SIZE. 16.0 m of plate with a 12.5 m mark inside it, centred at
    # z=23.0: the plate spans 15.0 to 31.0, which is 0.5 m clear of the
    # parapet cap at 31.5 and 10 m clear of the ground floor's setback. Across
    # the wall it is 16.0 on a run of 26.6 — and `run` is the PADDED footprint,
    # so the real wall is nearer 24.7 and this leaves about 4.4 m of it at each
    # end. That margin is the point: the fault this file keeps recording is a
    # symbol hanging off the corner into open air, and nothing checks for it.
    "BERRY": {"iso": "berry_iso.svg", "word": "berry_iso.svg",
              "plate": "berry_plate.svg",
              "facade": True, "facade_only": True,
              "facade_arts": ["plate", "iso"],
              "facade_side": "left", "facade_at": (194.95, 10.83),
              # two arts, two depths. The plate 0.02..0.14 off the box and the
              # mark 0.16..0.46, so there is 2 cm of air between them: coplanar
              # is what 92_check_zfight fails on.
              "plate_facade_proud": 0.02, "plate_facade_depth": 0.12,
              "iso_facade_proud": 0.16, "iso_facade_depth": 0.30,
              "plate_facade_frac": 0.603, "plate_facade_tall": 0.499,
              "iso_facade_frac": 0.471, "iso_facade_tall": 0.390,
              "facade_z": 0.718,
              # both files carry these already; forcing them is what makes the
              # colour a decision this table records rather than one buried in
              # an asset somebody may re-download
              "plate_ink": "#0a0a0b", "iso_ink": "#f5f5f7"},
    # THE SOUTH ARM OF TAKENOS' L, and it is the wall CLAUDE.md already names:
    # "the best free wall in the city — 34.5 m, on Takenos' building". 90 does
    # not offer it any more, and correctly — `brand_addresses` claims the whole
    # cell for Takenos — so it is taken the declared way instead, through
    # SHARED. It passes the Ualá / Brubank test by a wider margin than either
    # pair already there: the two faces are two PLANES 15.5 m apart in x and
    # 34.5 in y, the two logos sit at 0.60 and 0.72 of the same parapet, and the
    # formats differ — a bare wordmark up there, a plated lockup down here.
    #
    # THE WALL IS UNAMBIGUOUS, which is rare here and worth recording: sampled
    # every 2 m from z=8 to z=26, `wall_seen` is 1.00 at EVERY height and
    # `shot_cover` is flat at 2.3 s / 0.081. The tower problem in CLAUDE.md —
    # the two curves pulling apart up the wall — does not arise, so `facade_z`
    # is free and is spent on the separation from Takenos rather than on
    # sightlines. The kerb is 3.3 m off the +X face.
    #
    # AND IT NEEDS A PLATE, for the Berry reason and not a weaker version of it.
    # This facade is `Glass Light` #5f97a6 panes in a `Facade Teal` #2f7f74
    # grid, 69/31 across the run at the band the sign occupies, and the lockup
    # is white letters beside a cyan symbol: white is 4.8:1 on the teal and
    # 3.3:1 on the glass, the cyan 2.4:1 and 1.7:1 — and 1.5:1 is the number
    # Bioceres shipped wrong. Fitting inside one band is not on the table
    # either: the clean teal runs are the frames at z = 16, 20 and 24 and none
    # is a metre deep. So the lockup carries its own ground, 17.9:1 and 9.1:1.
    #
    # SIZE. `run` here is the PADDED box, 35.40, and the plan wing is 34.5, so
    # the plate at 0.734 is 26.0 m — about 79 % of the real wall, leaving some
    # 3.5 m at each end. That is deliberately short of Berry's 0.603-of-a-small-
    # wall and of the 0.945 Revamos needed: this wall has the width to spare and
    # the corner is the fault nothing checks for.
    "CONEXA": {"word": "conexa.svg", "iso": "conexa.svg",
               "plate": "conexa_plate.svg",
               "facade": True, "facade_only": True,
               "facade_arts": ["plate", "word"],
               "facade_side": "left", "facade_at": (349.75, -184.25),
               # two arts, two depths. The plate 0.02..0.14 off the box and the
               # lockup 0.16..0.46, so there is 2 cm of air between them:
               # coplanar is what 92_check_zfight fails on.
               "plate_facade_proud": 0.02, "plate_facade_depth": 0.12,
               "word_facade_proud": 0.16, "word_facade_depth": 0.30,
               # plate 26.0 x 9.29, lockup 24.0 x 7.08 — a margin of 0.99 m at
               # the sides and 1.10 above and below. The lockup's aspect is
               # 3.389 measured off the imported curves, NOT the 2.337 of its
               # viewBox: the file has padding the geometry does not.
               "plate_facade_frac": 0.734, "plate_facade_tall": 0.329,
               "word_facade_frac": 0.678, "word_facade_tall": 0.251,
               # 0.72 puts the plate between 15.7 and 25.0 m: clear of the 5 m
               # setback, under the 28.25 parapet, and 3.4 m above Takenos'
               # 0.60 on the other arm, which is what stops the two reading as
               # one band of signage.
               "facade_z": 0.72,
               # only the plate's colour is forced. `conexa.svg` carries its own
               # two — see the CAMPUS note — and `force_ink` is all-or-nothing.
               "plate_ink": "#101820"},
    # AND IT COSTS ONE OF 93's GAP PAIRS, 0.069 against Rebill where the floor
    # is 0.10, for the first 0.7 s of the shot. It is recorded rather than
    # quietly shipped, and it is not a placement that was left unmeasured:
    # `facade_z` was swept 0.62..0.80 against `facade_shift` -0.08..0.08 and
    # NOTHING on this wall reaches 0.10. The two best readings both cost more
    # than they buy — 0.078 at `facade_z` 0.62 pairs with TAKENOS instead, and
    # 0.62 is also 0.02 off Takenos' own height, which is the separation the
    # SHARED entry rests on; `facade_shift` 0.08 buys 0.005 and spends 2.83 m
    # of the north margin, leaving 0.93 m to the corner where there is now
    # 3.76 m. The corner is the fault nothing checks for, so it keeps the
    # margin. Measured on the mesh: the wall runs y -201.0..-167.5 at this
    # height and the plate -197.24..-171.26, symmetric.
    #
    # WHAT THE PAIR ACTUALLY LOOKS LIKE, because 0.069 is a number about
    # centres and the rule is about reading as one patch: Rebill is dark type
    # laid flat on a WHITE roof deck and this is a white-and-cyan lockup on a
    # near-black plate on a teal wall — different plane, different format,
    # opposite value. Rendered and looked at. The check already reports 6 such
    # pairs on main at 0.067..0.070, so this is the band it lives in rather
    # than a new kind of fault.
    "BELO": {"word": "belo.svg", "iso": "belo.svg",
             "facade": True, "facade_only": True,
             "facade_side": "right", "facade_at": (172.2, -377.2),
             # high: at 0.74 the bottom half sat behind the roof of the building
             # in front
             "facade_frac": 0.78, "facade_tall": 0.50,
             "facade_z": 0.80, "facade_depth": 0.35},
    # SPOT 75, THE LONG WALL, AND AS BIG AS THAT WALL ALLOWS — which is a
    # smaller number than it looks, for a reason worth writing down.
    #
    # The building is a U of three wings. `facade_at` names the east one, and
    # `hero_facade` centres the artwork on the box it names, with no way to
    # slide it along. So the size is bounded by the SHORTER half-run from that
    # centre, not by how much wall the elevation has:
    #
    #   east wing face   y -64.95 .. -46.17   centred on -55.56
    #   half-run north    9.39 m   <- this is the binding one
    #   half-run south    9.39 m of its own wing, then the south wing carries on
    #                     to -74.79, but centring cannot reach it
    #
    # 2 x 9.39 = 18.78 m of usable wall. `run` in hero_facade is the PADDED box,
    # 19.68, so 0.945 of it lands the mark at 18.6 m — 9 cm of air at each end.
    # Bigger than that and the north end leaves the building: at 24.6 m it hung
    # 2.91 m into open air, which is what a previous pass shipped.
    #
    # WHY THE WHOLE LOCKUP AND NOT THE SYMBOL. This wall is the one that makes
    # it possible. The short +Y wall of the same wing is 9.09 m, and 7.9:1 of
    # artwork on 9 m gives a 1.04 m cap height. On 18.6 it is 2.36 m.
    #
    # THE COST IS THE STREET, AND IT IS NOT A COURTYARD. This building is a U
    # and it does have an internal court — 9.09 x 18.78 m between the two
    # vertical wings, opening north — but the sign is not on it. It is on the
    # OUTER face of the east wing, at x -100.1, looking east across open lawn.
    # `wall_to_street` reports 31.3 m for it because the nearest kerb on that
    # axis is genuinely that far, not because anything is in the way; the +Y
    # face of the same wing has pavement 2.7 m off. Worth stating plainly
    # because every other warning in this file about a wall 17-32 m from a
    # street IS about a courtyard, and this one reads like one and is not.
    #
    # Taken deliberately: the camera sees 100 % of this face, which is the
    # question the film asks, and 93 counts it at 0.073 where the short wall
    # never cleared the 0.05 floor.
    "REVAMOS": {"lock": "revamos.svg", "plate": "revamos_plate.svg",
                # TWO ARTS ON ONE WALL, AT TWO DEPTHS. This is the sign panel
                # this brand needs and the only way to get one on a facade: the
                # `facade_only` path raises no panel of its own, `medianera` is
                # planned by plan_avenue and cannot be asked for through EXTRA,
                # and a rectangle drawn into revamos.svg would be extruded into
                # the same slab as the letters and swallow them.
                #
                # `facade_arts` is a list and `par()` resolves every key per
                # art, so the plate and the lockup get their own proud and
                # depth. Order in the list does not decide what is in front —
                # the two `_facade_proud` values do:
                #
                #   plate  proud 0.02  depth 0.12   ->  0.02 .. 0.14 off the box
                #   lock   proud 0.16  depth 0.30   ->  0.16 .. 0.46
                #
                # 1.6 cm of air between the plate's face and the logo's back.
                # Coplanar is what 92_check_zfight fails on, and touching would
                # be coplanar.
                "facade": True, "facade_only": True,
                "facade_arts": ["plate", "lock"],
                "plate_facade_proud": 0.02, "plate_facade_depth": 0.12,
                "lock_facade_proud": 0.16, "lock_facade_depth": 0.30,
                # the plate takes the whole usable wall; the mark sits inside it
                # with 70 cm of black at each end
                "plate_facade_frac": 0.945, "plate_facade_tall": 0.20,
                "lock_facade_frac": 0.874, "lock_facade_tall": 0.20,
                "facade_side": "left", "facade_at": (-104.66, -55.56),
                # WIDTH BINDS. `facade_tall` is left loose at 0.20 (4.1 m) so it
                # never clamps first — at 7.9:1 the height it asks for is 2.36.
                "facade_frac": 0.945, "facade_tall": 0.20,
                # 0.889 = 18.4 m, AND THE HEIGHT IS DOING THE JOB OF A PANEL.
                # This wordmark is white, and white on this city's warm concrete
                # is the weakest thing on the block — SOURCES.md lists four
                # other brands with the same problem and no answer. A black
                # backing plate is the obvious fix and is not available: there
                # is no panel in the `facade_only` path, `medianera` is planned
                # by plan_avenue and cannot be asked for through EXTRA, and a
                # rectangle drawn into the SVG does not work either — `logo()`
                # extrudes every piece to the same depth off the same plane, so
                # the plate would swallow the letters rather than back them.
                #
                # The building has the dark ground already. A ray fired at this
                # wall reads the bands off it, WITH THE DEPTH EACH ONE SITS AT,
                # and the depth is the half that matters:
                #
                #   cornice          x -99.67   stands 0.45 m proud
                #   spandrel         x -100.12  the warm concrete
                #   glazing          x -100.87  RECESSED 0.75 m behind it
                #
                #   14.00 .. 15.40   Glass Dark   1.40 m   too short for 2.36
                #    9.34 .. 12.37   Glass Dark   3.03 m   tried, and see below
                #   17.20 .. 19.60   Glass Dark   2.40 m   <- this one
                #
                # The 9.34 band is the tallest and it did not work, because the
                # logo stands ~0.7 m proud of the spandrel and the glass is 0.75
                # behind it: at 45 degrees of elevation the camera looks over the
                # letters onto the spandrel BELOW them, so a band chosen on
                # height alone still renders against concrete. Parallax, not
                # arithmetic. The 17.20 band works because the parapet caps it —
                # there is no spandrel above to fall into view.
                "facade_z": 0.889, "facade_depth": 0.40},
    # MOVED FROM 133 TO 188, and the move is the part that matters. 133 looked
    # free and was not: its address already belonged to Tiendanube, whose
    # wordmark is laid flat on the roof of the wing next door. Two brands on one
    # address is exactly what the rule forbids, and nobody saw it because `thin`
    # does not look at hand-placed sites and 93 grouped by wing.
    # 188 has 66 m of north wall, the longest of the facade-mounted six.
    "REBILL": {"word": "rebill.svg", "iso": "rebill.svg",
               "facade": True, "facade_only": True,
               "facade_side": "right", "facade_at": (333.0, -243.0),
               "facade_frac": 0.55, "facade_tall": 0.35,
               "facade_z": 0.72, "facade_depth": 0.30},
    # BOTH FACES OF 146, one art each, which is the Mercado Libre arrangement:
    # the lime symbol on the front facing the avenue, and the wordmark across
    # the left face, which is 35 m of wall against the front's 14.5. It is the
    # answer to what this building has too much and too little of: the good face
    # is short and tall, so the symbol goes there, being square; the long one is
    # low, so the word goes there, being 6:1.
    #
    # Wing 146 is the other wing of the same building the anchor is on, so the
    # two arts are still one brand per address. The file carries the wordmark
    # and the symbol as one piece each, and is split by position like Naranja X:
    # the white part is the word, the lime on the right is the symbol.
    "PAISANOS": {"iso": "paisanos.svg", "word": "paisanos.svg",
                 "iso_x": [0.55, 1.01], "word_x": [-0.01, 0.55],
                 "facade": True, "facade_only": True,
                 "facade_arts": ["iso", "word"],
                 "facade_at": (194.9, -149.8), "facade_depth": 0.40,
                 # the symbol, on the front. This building is 16.9 m and what
                 # limits it is the height of the wall. From cornice to kerb it
                 # does NOT fit: the ground floor is set back and the foot of
                 # the logo pushed inside it (99_check_overlap, 8 triangle
                 # pairs). Between 4.9 and 16.4 m there is real wall.
                 "iso_facade_side": "right", "iso_facade_frac": 0.90,
                 "iso_facade_tall": 0.68, "iso_facade_z": 0.63,
                 # and the word, on one line, across the left face
                 "word_facade_side": "left", "word_oneline": True,
                 "word_facade_frac": 0.74, "word_facade_tall": 0.30,
                 "word_facade_z": 0.62},
    # THE BEST FREE WALL THERE WAS, and it stayed free for months: 41.2 m of
    # north face on a 16.9 m building, seen whole, 10.7 s of the shot. The word
    # alone, not the lockup: the brand stacks the symbol over the name, which is
    # 2.2:1, and this wall's usable band — above the ground floor's setback,
    # under the parapet — is about 11 m on 41, so a 2.2:1 lockup is bound by the
    # height and lands smaller than the 5:1 word bound by the width. The symbol
    # has nowhere to go here: the other face of this building looks into the
    # complex, which is the mistake three brands already made.
    "COCOS": {"word": "cocos_word.svg", "iso": "cocos_iso.svg",
              "facade": True, "facade_only": True, "facade_art": "word",
              "facade_side": "left", "facade_at": (187.0, -75.0),
              "facade_frac": 0.80, "facade_tall": 0.42,
              "facade_z": 0.68, "facade_depth": 0.35},
    "COMPLIF": {"word": "complif.svg", "iso": "complif.svg",
                "facade": True, "facade_only": True,
                "facade_side": "right", "facade_at": (195.0, -368.7),
                # all the way: the street-facing wall of this building is the
                # short one, 14.5 m, and it is the ceiling on what Complif can
                # measure
                "facade_frac": 0.95, "facade_tall": 0.34,
                "facade_z": 0.74, "facade_depth": 0.32},
    # ---- the five that came in when the corridor was already full ----------
    #
    # THE CITY HAD THREE FREE WALLS AND FIVE BRANDS TO PLACE, and the two extra
    # ones did not come from relaxing anything. They came from two questions 90
    # does not ask:
    #
    #   · a sign carrying an INVENTED name is not a client. Taking one over
    #     removes a made-up roofmark and adds a real logo, which is the trade
    #     the video wants. Maslow took Pampa's and Mural took Ombú's.
    #   · a building with two arms has two walls on two different PLANES. That
    #     is the Ualá / Brubank arrangement, and it is declared in SHARED.
    #     Mural and Bioceres share the U at (33.75, -231.25).
    #
    # Every one of the five is `facade_only`: a logo hung high on the front,
    # nothing built on the deck.
    #
    # THE WALL WAS READ BEFORE THE BRAND WAS ASSIGNED. A ray fired at each of
    # the five reports the material band by band, and they are not alike:
    #
    #   (-84.2, -89.8)   Concrete Cool2  #8d9599   cornices every 7.6 m
    #   ( 66.2,-231.2)   Brick Warm      #a86a4c   4.6 m to 23.8, unbroken
    #   ( 66.2,-260.4)   Facade Teal     #2f7f74   banded with Glass Light
    #   ( 44.0,-227.5)   Concrete Cool2  #8d9599   plain to 12.2 m
    #   ( 23.5,-227.5)   Concrete Cool2  #8d9599   the other arm of the same U
    #
    # so the two dark logos went to grey walls, the white one to the teal wall,
    # and the coral symbol to the brick. SOURCES.md lists four brands that are
    # white on warm concrete with no answer; this batch does not add a fifth.
    #
    # The tallest wall in the free set (32 m) and the widest (21.3 m), which is
    # what a 6.7:1 lockup needs: the width binds and `facade_tall` is only there
    # to stop the height taking over. It sits in the band between the cornices
    # at 23.4 and 31.0 m — those stand 0.45 m proud of the wall and a logo
    # crossing one comes out sliced, which is the Coderhouse lesson.
    "OPENZEPPELIN": {"word": "openzeppelin.svg", "iso": "openzeppelin.svg",
                     "facade": True, "facade_only": True,
                     "facade_side": "left", "facade_at": (-84.2, -89.8),
                     "facade_frac": 0.78, "facade_tall": 0.12,
                     "facade_z": 0.85, "facade_depth": 0.45},
    # A SQUARE SYMBOL ON THE WALL WITH THE MOST SECONDS ON IT — 10.0, against
    # 1.0 for the wall above. What binds a square is the HEIGHT, and this one
    # has 19.2 m of unbroken brick to work with, so the symbol lands at 12.2 m
    # where a wordmark on the same wall would have been 12.9 wide and 2.6 tall.
    # This brand publishes no wordmark in vector form; the icon is the whole
    # logo and it is the format this wall wanted anyway.
    "DECENTRALAND": {"iso": "decentraland.svg", "word": "decentraland.svg",
                     "facade": True, "facade_only": True, "facade_art": "iso",
                     "facade_side": "left", "facade_at": (66.2, -231.2),
                     "facade_frac": 0.80, "facade_tall": 0.50,
                     "facade_z": 0.62, "facade_depth": 0.40},
    # THE FRONT OF SPOT 172, one wing at (270.2, -243.0), which is the biggest
    # wall this project has given a brand: 45.9 m of run, `wall_seen` 1.00 and
    # the kerb 3.0 m away. It was held by a SECOND Ripio record whose art was a
    # generic violet disc — there was no SVG yet — so the trade is the one the
    # video wants, a duplicate mark out and a real logo in. See the pin on
    # Sign.019. Ripio now has a traced wordmark and keeps Sign.069.
    #
    # The dark file, not the white one. The wall is `Glass Light`, #5f97a6:
    # white on it is 3.1:1 and the near-black wordmark is 7:1, and this is the
    # first of these walls bright enough for that to be the right way round.
    # Its old home was a teal band where white was the only option.
    "MASLOW": {"word": "maslow_dark.svg", "iso": "maslow_dark.svg",
               "facade": True, "facade_only": True,
               "facade_side": "left", "facade_at": (270.2, -243.0),
               "facade_frac": 0.48, "facade_tall": 0.36,
               "facade_z": 0.75, "facade_depth": 0.50},
    # THE RIGHT FACE OF SPOT 107, the 32 m tower at (33.75, -254.75), asked
    # for. Only one of its two faces is usable at all: the left one is `seen`
    # 0.00, hidden whole by the block in front of it.
    #
    # AND ON A TOWER THE HEIGHT IS THE WHOLE DECISION, because visibility and
    # framing pull opposite ways. Measured up this wall:
    #
    #     z      seen    in frame
    #     6–9    0.00    6–7 s      the base is behind the neighbour
    #     11     0.52    5.7 s
    #     18     0.81    3.3 s
    #     26+    1.00    0.0 s      seen whole, and the move never frames it
    #
    # So the best band of wall on this building — 7.5 m of clean concrete from
    # 4.8 to 12.2, enough for a logo twice this size — is the one nothing can
    # see, and the part that is seen whole is above the top of the shot. 19 m
    # is where the two curves cross.
    #
    # It crosses floor lines on purpose: every band between 16 and 22 is teal
    # or pale glass, so a black-and-primary wordmark reads across all of them.
    # That is the opposite of the Bioceres call one entry down, and the reason
    # is the ink, not the wall.
    "MURAL": {"word": "mural.svg", "iso": "mural.svg",
              "facade": True, "facade_only": True,
              "facade_side": "right", "facade_at": (33.75, -254.75),
              "facade_frac": 0.50, "facade_tall": 0.19,
              "facade_z": 0.592, "facade_depth": 0.35},
    # THE LEFT FACE OF SPOT 155, the east arm of the C at (211.0, -303.4), and
    # asked for. It is the same wall on paper as its neighbour at (192.5,
    # -303.4) — 38.4 m of run, seen whole — and the difference is the only one
    # that matters here: this one has the kerb 2.9 m away and that one has it
    # 21.4, because it faces into the complex.
    #
    # THE WHITE FILE, AND A MATERIAL IS A DISTRIBUTION. One ray at the centre
    # of this face answers `Concrete Cool2`, #8d9599, and on that the navy is a
    # comfortable 3.4:1 — so the navy went up, and the render showed it on
    # near-black glass. The single ray had hit a MULLION. Sampled across the
    # run at the band the logo occupies, 8.8–11.5 m, the wall is 64 % `Glass
    # Dark` #15181b and 36 % concrete: navy on it is 1.5:1. White is 12:1, and
    # is what the brand uses on dark ground.
    #
    # AND THEN IT HAS TO SIT IN ONE BAND. White reads on the glass and vanishes
    # on the slab, so a logo spanning both loses the letters that fall on the
    # pale part — the first three, in the render that caught it. This wall has
    # two clean glass runs, 5.75–8.35 and 9.75–12.15, and the sign is sized to
    # fit inside the upper one rather than centred on the wall and left to
    # cross a floor line. That costs about 3 m of width and it is worth it.
    #
    # THE WORDMARK ALONE, NOT THE LOCKUP, and it is the same call Cocos made
    # for a different reason. The full lockup sets "CROP SOLUTIONS" on a second
    # line under the name: at this size that line is a few centimetres of serif
    # text and the whole thing renders as a blue smudge. The name alone is 6:1,
    # so the width binds.
    "BIOCERES": {"word": "bioceres_word_light.svg", "iso": "bioceres_iso.svg",
                 "facade": True, "facade_only": True,
                 "facade_side": "left", "facade_at": (211.0, -303.4),
                 "facade_frac": 0.45, "facade_tall": 0.20,
                 "facade_z": 0.842, "facade_depth": 0.35},
    # RIPIO IS NOT HERE, AND THAT IS THE ENTRY. It was, with an iso and an
    # iso_frac of 0.86, and a HERO record on a parapet means hero_parapet: that
    # path sizes the symbol against the BUILDING, not against the sign, because
    # a hero symbol is meant to hang the full drop of the wall. Sign.069 is a
    # parapet of 22 x 4.6 at z=20.65 and what came out was 41.85 x 18.09 at
    # z=11.24 — the symbol ran down the whole facade and 99_check_overlap
    # counted 860 triangle pairs inside the building.
    #
    # The plain parapet path is what this brand wants and it already does the
    # job: `elif art` in 10_signs.build() extrudes ripio.svg at LOGO_CAP and
    # hangs it off the same cap line as the built letters. The table's ink is
    # already #7908ff, so word_ink said nothing either. A brand only belongs in
    # HERO when it is going on a wall or a deck this file names.
    "AUTH0": {"iso": "auth0_iso.svg", "word": "auth0_word.svg",
              "iso_frac": 0.55, "roof_frac": 0.72},
    "LEMON": {"iso": "lemon_iso.svg", "word": "lemon_word.svg",
              "iso_frac": 0.86, "roof_frac": 0.78,
              "roof_at": (181.5, -303.4),
              "iso_ink": "#44df19", "word_ink": "#111111",
              # the disc turns cream: the symbol's green on the green the mast
              # already had did not read, and the colour that wins is the logo's
              "face": "#f7f3e8"},
    # the symbol in the roofmark and the wordmark across the left facade, which
    # is the face this camera sees on that side
    # `facade_at` IS NOT DECORATION HERE, it is the fix for a wordmark that
    # moved on its own. This building is an L of two wings and the sign's owner
    # — (349.75, -167.0), the CELL's address — falls in the 0.1 m gap between
    # their padded footprints, so `site.hit` answered with whichever box the
    # solids file happened to list first. Adding five brands elsewhere in the
    # city changed that order, and Takenos' word silently jumped 21 m from the
    # north arm to the south one. Nothing failed and no check covers it: the
    # logo was on a wall either way. Naming the wing takes the question away.
    "TAKENOS": {"iso": "takenos_iso.svg", "word": "takenos_word.svg",
                "iso_frac": 0.80, "roof_frac": 0.0,
                "facade": True, "facade_side": "left",
                "facade_at": (342.0, -149.8),
                "facade_frac": 0.80, "facade_tall": 0.26, "facade_z": 0.60,
                "iso_ink": "#6d37d5", "word_ink": "#6d37d5"},
    # the symbol alone on the party wall, with no panel, and the wordmark laid
    # flat on the roof of 128, which runs along the 35 m side
    "TIENDANUBE": {"iso": "tiendanube_iso.svg", "word": "tiendanube_word.svg",
                   "wall_frac": 1.0, "roof_frac": 0.80,
                   "roof_at": (165.34, -149.69)},
    # the same file split by colour: the nine orange strokes are the word, the
    # two violet ones are the X. No panel: the letters straight onto the roof
    # and the X hung off the front
    "NARANJA X": {"iso": "naranjax.svg", "word": "naranjax.svg",
                  "iso_x": [0.85, 1.01], "word_x": [-0.01, 0.85],
                  "wall_frac": 1.0, "roof_frac": 0.78},
    # the whole lockup hung off the front, nothing on the roof. The file carries
    # a colourless shape occupying the left 40 % that is not part of the brand:
    # the crop starts at 0.38 and leaves it out
    "POMELO": {"word": "pomelo.svg", "iso": "pomelo.svg",
               "word_x": [0.55, 1.01], "iso_x": [0.38, 0.55],
               "roof_art": "iso", "iso_roof_frac": 0.42,
               # towards the entrance corner, not the middle of the roof
               "iso_roof_shift": (0.0, 0.22), "iso_roof_rot": 90,
               "facade_depth": 0.30,
               "facade": True, "facade_only": True, "facade_side": "right",
               # high on the wall on purpose: in front of it are two 9.1 m
               # street lamps and pavement trees, and at mid-height the logo
               # ends up behind them
               "facade_frac": 0.74, "facade_tall": 0.26, "facade_z": 0.86},
    # the huge symbol over the street on one building and the wordmark laid flat
    # on the roof of the one next door: two different addresses for one brand
    "AEROLAB": {"iso": "aerolab.svg", "word": "aerolab.svg",
                "iso_x": [-0.01, 0.21], "word_x": [0.21, 1.01],
                "facade": True, "facade_only": True, "facade_art": "iso",
                "facade_side": "right", "facade_at": (25.92, 17.37),
                "facade_frac": 0.58, "facade_tall": 0.50, "facade_z": 0.74,
                "facade_depth": 0.35,
                "roof_art": "word", "roof_at": (33.75, 5.13),
                "word_roof_frac": 0.78,
                "iso_ink": "#ff510d", "word_ink": "#1c1c1c"},
    # moves from 113 to 179: the wordmark on one line across the wall and the
    # Preguntados icon laid flat on the roof, which is what that company puts on
    # a building ahead of its own name
    "ETERMAX": {"word": "etermax_word.svg", "icon": "preguntados.svg",
                "iso": "etermax_word.svg",
                "facade": True, "facade_only": True, "facade_side": "right",
                "facade_at": (316.25, -149.69),
                # two lines is how this brand is written, so what binds it is
                # the height and not the width: 0.24 gave a 5.8 m logo on a 35 m
                # wall
                "facade_frac": 0.74, "facade_tall": 0.54,
                "facade_z": 0.76, "facade_depth": 0.30,
                # white: the file carries the brand's near-black grey and that
                # facade is dark brown, so the logo disappeared
                "word_ink": "#ffffff",
                "roof_art": "icon", "roof_at": (316.25, -149.69),
                "icon_roof_frac": 0.46},
    # takes 84, which came free when Basement moved to 123
    "HUMAND": {"iso": "humand.svg", "word": "humand.svg",
               "facade": True, "facade_only": True, "facade_side": "left",
               "facade_at": (-84.25, 57.75),
               # THIS ONE IS STILL OFF ITS WALL, and on purpose. This building's
               # footprint runs 1.2 m wider than the facade, and the sign rests
               # on the edge of the footprint. Pulling it in with a negative
               # `facade_proud` does not stick it to the wall: it puts it INSIDE
               # the volume, and 99_check_overlap finds it there (246 to 1685
               # triangle pairs depending on how far in it goes). It is the only
               # one of the ten with air to spare.
               "facade_frac": 0.70, "facade_tall": 0.18,
               "facade_z": 0.93, "facade_depth": 0.55},
    # moves from 84 to 123: the parapet disappears from its building and the
    # wordmark appears hung off the other one's wall, leaving 84 free
    "BASEMENT": {"iso": "basement.svg", "word": "basement.svg",
                 "facade": True, "facade_only": True, "facade_side": "wide",
                 "facade_at": (66.25, 17.63),
                 # right at the top and with some body: these facades have a
                 # cornice per storey and a flat logo at mid-height comes out
                 # sliced into strips by them
                 "facade_frac": 0.80, "facade_tall": 0.20,
                 "facade_z": 0.93, "facade_depth": 0.55},
    # Spot 68. Facade was the first placement; Vercel HQ (PR #6) now hides that
    # wall from the hero camera, so the wordmark moved to the deck — centred on
    # the Patmos Black building, readable in the shot.
    "PATMOS": {"word": "patmos.svg", "iso": "patmos.svg",
               "facade": True, "facade_only": True, "facade_arts": [],
               "roof_art": "word", "roof_at": (-113.75, 57.75),
               "roof_readable_at": (-113.75, 57.75),
               "word_roof_frac": 0.62, "word_roof_depth": 0.28,
               "word_roof_shift": (0, 0),
               "word_ink": "#f5f5f5"},
    # the triangle alone on the disc, small, and the whole logo on the wall.
    # White on black since the building went near-black: the cream panel read
    # as a hole in the facade. The camera-facing side keeps the triangle; the
    # far side carries the rabbit, which is the owner's mark and the one place
    # in the city a back face is worth a logo — free orbit is the only camera
    # that ever comes round there.
    "VERCEL": {"iso": "vercel_iso.svg", "word": "vercel.svg",
               "iso_frac": 0.52, "face": "#111111",
               "back": "evilrabbit.svg", "back_ink": "#ffffff",
               "facade": True, "facade_side": "left",
               "facade_frac": 0.66, "facade_tall": 0.20, "facade_z": 0.74,
               "facade_depth": 0.30,
               "iso_ink": "#ffffff", "word_ink": "#ffffff"},
    # THE OTHER ARM OF UALA'S L, and that is the whole point of this entry.
    # Spots 100 and 101 are not two buildings: they are the two wings of one
    # cell at (-12.75, -75.0), same 20.65 m top, sharing a continuous west wall.
    # The `?spots=1` overlay paints every wing of an occupied building green,
    # which is why both read UALA — Ualá is on 101 and 100 belongs to it.
    #
    # So this is a second brand on one address, on purpose, and it is declared
    # in SHARED below with its reason. What makes it work is that the two walls
    # are different walls: Ualá takes the east face of the south arm, Brubank
    # the east face of the north arm, 12 m apart in x and 30 in y.
    #
    # `left`, and it IS the biggest face — 29.47 m of run against 13.32 on the
    # other one, seen whole, 12.7 s at 13.6 % of the frame. left/right here name
    # which face lands to the left ON SCREEN under the hero camera, not a
    # compass direction: on this wing the long east wall is the left one.
    # A pure wordmark at 4.8:1, so the width binds and `facade_tall` is only
    # there to stop the height taking over.
    "BRUBANK": {"iso": "brubank.svg", "word": "brubank.svg",
                "facade": True, "facade_only": True, "facade_art": "word",
                "facade_side": "left", "facade_at": (-18.96, -60.71),
                "facade_frac": 0.80, "facade_tall": 0.26,
                "facade_z": 0.72, "facade_depth": 0.30},
    # 120 is left empty: the whole mural moves to the wall of 101
    "UALA": {"iso": "uala2.svg", "word": "uala2.svg",
             "facade": True, "facade_only": True, "facade_side": "left",
             "facade_at": (-12.79, -89.29),
             "facade_frac": 0.80, "facade_tall": 0.20, "facade_z": 0.80,
             "facade_depth": 0.30},
    # the three-wing complex: the handshake on the roof of 114, the wordmark on
    # the left wall of that same wing, which looks onto the plaza
    "MERCADO LIBRE": {"iso": "ml_iso.svg", "word": "mercadolibre.svg",
                      "facade": True, "facade_only": True,
                      "facade_arts": ["iso", "word"],
                      "facade_at": (43.75, -155.38),
                      "facade_depth": 0.35,
                      # the handshake on the front face
                      "iso_facade_side": "right", "iso_facade_frac": 0.82,
                      "iso_facade_tall": 0.52, "iso_facade_z": 0.74,
                      # and the wordmark, on a single line, across the long face
                      # that looks onto the plaza
                      "word_facade_side": "left", "word_oneline": True,
                      "word_facade_frac": 0.88, "word_facade_tall": 0.30,
                      "word_facade_z": 0.72},
    # and the light-blue handshake on the wing next door
    "MERCADO PAGO": {"iso": "mp_iso.svg", "word": "mp_iso.svg",
                     "facade_only": True, "facade_arts": ["iso"],
                     "facade_at": (23.66, -155.38),
                     "iso_facade_side": "right", "iso_facade_frac": 0.82,
                     "iso_facade_tall": 0.52, "iso_facade_z": 0.74,
                     "facade_depth": 0.35},
}


# Signs whose size is set by hand, as a fraction of the one 04 planned. The plan
# sizes by what fits on the roof and by what reads at a distance, which are two
# good rules and neither of them looks at the frame: a 19 m disc can fit and
# still eat the corner.
#
# The published solid does NOT shrink with this. It goes on reserving the
# original space, so a shrunken sign leaves air around it instead of inviting a
# tree to be planted beside it.
SIZE = {"Sign.005": 0.62,
        # the Vercel disc: just a triangle, and small
        "Sign.001": 0.42}

# New signs on hand-picked roofs, and the reason this table goes by COORDINATE
# rather than by Sign.NNN like PIN.
#
# Sign.NNN is an ordinal: `thin()` sorts the signs by how much of each one the
# camera sees and only then numbers them, so a new sign lands in the middle of
# the ranking and shifts the number of everything it sees less of. A sign added
# here would have silently changed the roof of half the already-approved brands.
# So these are planned during the lot pass (which is the only thing that can
# reserve their space against the rooftop plant) but numbered AFTER everything
# else, starting at Sign.094: the usual 94 keep their allocation intact and
# these are appended behind them.
#
#   at     the centre of the roof wing, straight out of city_solids.json.
#          In brackets, the spot number from `?spots=1` in the browser, which is
#          how they were picked.
#   kind   parapet | roofmark | mast, the same three formats as 04.
#   grow   the size multiplier for shape_sign.
#
# THE ROOF DECIDES THE SIZE, not this number. `grow` is capped by what fits on
# the wing, so a brand's scale is chosen by choosing the roof: the Galicia mast
# is 21 m because it is on a 28 m wing, and Complif is 10 on a 20 m one. `grow`
# only finishes the fit, and the floor is the one 93_check_signs measures: 5 %
# of the frame width, or the sign is not delivered.
EXTRA = [
    # ALL THREE ARE ANCHORS, NOT SIGNS. Each one carries its brand to a building
    # and its job ends there: the matching HERO entry has `facade_only`, so
    # 10_signs raises no panel and the only thing built is the logo stuck to the
    # wall. The format named here is never seen anywhere; it is here because a
    # sign has to exist in the manifest for a brand to be pinned to it.
    #
    # They started as real signs — roofmarks and billboards — which is what the
    # allocation knows how to do on its own. That is wrong for this city: brands
    # have been going up hung off the front, where a wordmark has 28 m of wall
    # and reads, rather than laid flat on a roof, where at 250 m they are a pale
    # rectangle.
    #
    # Coderhouse on the tallest building of the corridor (32 m).
    {"at": (201.8, -14.8), "spot": 153, "brand": "CODERHOUSE",
     "kind": "roofmark", "grow": 1.45},
    # Complif, the smallest of the six, on the last free building of the
    # corridor: 14.5 x 18 on the south edge, 2 s of screen time.
    {"at": (195.0, -368.7), "spot": 148, "brand": "COMPLIF",
     "kind": "roofmark", "grow": 1.45},
    {"at": (201.8, -184.2), "spot": 152, "brand": "PAISANOS",
     "kind": "roofmark", "grow": 1.45},
    # Revamos on spot 75. `at` is a WING coordinate and not the building's
    # address — plan_extra matches it against bx+ox within 0.8 m — and this
    # building is a U whose address (-113.75, -60.25) is none of its three
    # wings. An anchor like the three above: HERO is `facade_only`, so no
    # roofmark is ever raised from it.
    {"at": (-104.66, -55.56), "spot": 75, "brand": "REVAMOS",
     "kind": "roofmark", "grow": 1.45},
    # OpenZeppelin, and it is the only one of the five new brands that needs an
    # anchor. Its cell — the 32 m tower at (-84.25, -89.75) — carries NO sign at
    # all, which is the one condition `plan_extra` runs under. The other four
    # took over a record that already existed (Pampa's, Ombú's, Salto's and
    # Timbó's), and a cell that already has a record is where an anchor is
    # silently never placed: see the note on Cocos below.
    #
    # THE ORDER OF THIS LIST DOES NOT DECIDE THE ORDINALS, and that is worth
    # knowing before trusting one. The anchors are numbered from Sign.094 in
    # the order the LOT PASS reaches their cells, not in the order they are
    # written here, so adding this entry — at the end of the list — renamed the
    # four below it anyway: Revamos went from 094 to 095 and so on down.
    #
    # It costs nothing today because none of these five is in PIN: each is
    # carried by its `brand` key and finds its wall through `facade_at`. It
    # would cost something the day one of them is pinned by ordinal, which is
    # why the numbers here are not to be quoted anywhere else.
    {"at": (-84.2, -89.8), "spot": 132, "brand": "OPENZEPPELIN",
     "kind": "roofmark", "grow": 1.45},
    # Built after the normal lot pass so the existing hand-placed signs keep
    # their Sign.NNN identity.
    # The roofmark is only an anchor: HERO puts the official wordmark on the
    # facade and leaves the studio roof clear for its own equipment.
    {"at": (-26.0, 153.0), "spot": "SLA", "brand": "SLA",
     "kind": "roofmark", "grow": 1.15},
    # PATMOS IS NOT HERE. Spot 68 already has a sign record: Sign.046, the
    # Decentraland anchor, whose art HERO moved to (66.2, -231.2). plan_extra
    # only runs on a cell with no sign, so an anchor here prints NO ENTRARON
    # and nothing more. Same shape as Cocos below: the pin holds the brand on a
    # far record and facade_at in HERO puts the wordmark on the wall.
    # COCOS IS NOT HERE, and the reason is worth the six lines. Its wall —
    # (187, -75), the best free one in the city — is a building that already has
    # a sign record: Sign.002, the Mercado Libre anchor, whose own art HERO
    # moved to (43.75, -155.38). `plan_extra` only runs on a cell the allocation
    # left with NO sign at all, so an anchor here is silently never placed: the
    # step prints `NO ENTRARON: COCOS` and nothing else says a word.
    #
    # It does not need one. An anchor exists so a brand has a record to be
    # pinned to, and the allocation already gives every brand in the tables
    # above a record; where the art goes is `facade_at`'s decision, not the
    # record's. So Cocos is pinned in PIN, like the rest, and 90's coordinate
    # goes straight into HERO.
]


# Addresses where TWO brands coexist on purpose, and why.
#
# 93_check_signs forbids two brands on one address, and the rule is a good one:
# two logos on a building read as one company with two brands. But there is a
# case where the right answer is yes, and without this table the only way out
# was to switch the check off or lie to it. It is declared, with the reason, and
# it shows up in the report: a recorded exception is not the same thing as a
# rule that does not run.
SHARED = {
    # the three-wing complex: Mercado Libre on one wing and the light-blue
    # Mercado Pago handshake on the one next door. Two brands from the same
    # house, and that is how they are really mounted.
    (33.75, -167.0): "Mercado Libre and Mercado Pago, same house",
    # The L at spots 100 / 101, and this one is NOT two brands from one house:
    # it is two banks on one building, which is exactly what the rule forbids.
    # It is here because the alternative on the table was worse. Splitting the
    # cell into two sites in city_buildings.json would silence the check without
    # changing anything the camera sees — the two arms are one continuous mass
    # at 20.65 m sharing a 57 m west wall — and it would hand the same licence to
    # the other 57 multi-wing buildings, undoing the very grouping `roof_spots`
    # was fixed to do. So the exception is declared instead of engineered away.
    #
    # What keeps it from reading as one company with two brands is the STEP,
    # and it is the thing to look at if either of them ever moves. Both logos
    # are on east-facing walls, but the arms are offset 12 m in x, so the two
    # walls are two planes and not one elevation. They also sit at different
    # heights on purpose — Ualá at 0.80 of the parapet, Brubank at 0.72 — which
    # is what stops the eye reading them as one band of signage.
    #
    # `right` was rendered as the alternative and is worse: 13.3 m of run
    # instead of 29.5, and the brown building next door eats the far half of it.
    (-12.75, -75.0): "Ualá on the south arm, Brubank on the north one, asked for",
    # The L at spot 147 / 153, and it passes the same test as the pair above:
    # the two walls are two PLANES, not one elevation. Coderhouse's wordmark is
    # on the +X face of (201.8, -14.8) at 0.93 of the parapet; Berry's symbol is
    # on the +X face of (194.95, 10.83), 13.7 m west and 25 m north, at 0.718.
    # Different plane, different height, different format — a word and a symbol
    # — which is three ways of not reading as one company with two brands.
    (201.75, -2.0): "Coderhouse on the south arm, Berry on the north one, asked for",
    # The L at (349.75, -167.0), and it passes the same test with more room to
    # spare than either pair above. Takenos' wordmark is on the +X face of the
    # north arm (342.0, -149.75) at 0.60 of the parapet; Conexa's plated lockup
    # is on the +X face of the south arm (349.75, -184.25), 15.5 m east and
    # 34.5 m south, at 0.72. Different plane, different height, different
    # format — a bare wordmark against a lockup on its own dark ground.
    (349.75, -167.0): "Takenos on the north arm, Conexa on the south one",
    # THE U AT (33.75, -231.25) WAS HERE and no longer needs to be: it carried
    # Mural and Bioceres, one per arm, because the corridor had three free walls
    # and five brands to place. Bioceres moved to spot 155 and the U is down to
    # one brand, so the exception is retired rather than left declared — a
    # standing exception nobody re-reads is how the rule stops being a rule.
    #
    # Worth keeping from it: the U's THIRD arm, the 30.8 m one at (33.8,
    # -238.7), is its longest wall and faces INTO the complex. Nothing goes on
    # it. That is the mistake three brands already made.
}


# Signs with the brand pinned by hand, and signs that are not built at all.
#
# 04's allocation by visibility is a good rule and it cannot look at anything.
# When somebody looks at the frame and says "this brand goes on THAT sign", that
# wins: it is the only information no metric in this project can produce. PIN is
# applied before the allocation and takes that brand out of the pool, so the
# rest is shared out among what is left exactly as before.
#
# DROP is the same thing in the negative. The Lemon billboard was removed
# because the brand moved to the mast next door and the neighbouring roof, and
# the same brand twice in one frame is one brand fewer in the video.
PIN = {"Sign.023": "LEMON", "Sign.014": "TAKENOS",
       "Sign.018": "TIENDANUBE", "Sign.008": "NARANJA X",
       "Sign.009": "POMELO", "Sign.020": "AEROLAB",
       "Sign.005": "AUTH0", "Sign.001": "VERCEL",
       "Sign.006": "SATELLOGIC", "Sign.007": "DESPEGAR",
       "Sign.004": "UALA", "Sign.002": "MERCADO LIBRE",
       "Sign.016": "MERCADO PAGO",
       # THE TWO THAT COME BACK ON. 012 and 017 are billboards that were
       # switched off because the brand they carried had moved elsewhere in the
       # frame, not because the site was bad: 012 is the best free site in the
       # city (13.7 s on camera) and it was dark. A new brand is pinned to them
       # and they come out of DROP.
       "Sign.012": "GALICIA", "Sign.017": "BELO",
       # and Rebill on 188, which carried a second RIPIO drawn as a generic
       # disc before the wordmark landed. Ripio keeps Sign.069 (pinned below).
       "Sign.015": "REBILL",
       # the parapet that still carries Ripio after the duplicate cull. With
       # ripio.svg in the table, this pin is what stops the allocation walking
       # the brand off to another roof the next time a sign is added.
       "Sign.069": "RIPIO",
       # Sign.013 was tried for Complif and DOES NOT WORK, even though the
       # allocation called it free: its owner is the Etermax building, whose
       # wordmark hangs off the facade and whose icon is laid flat on the roof,
       # both moved there by HERO. A sign's record points at the roof it was
       # planned on, so a building with two logos on it read as empty. Complif
       # went to spot 148, which is genuinely free, and this is recorded here
       # because the next person to read the table will see the same gap.
       #
       # the ones that survived the duplicate cull, pinned so the next pin does
       # not move them to another roof
       "Sign.000": "GLOBANT",
       "Sign.010": "TECHNISYS", "Sign.011": "ALEPH",
       # the parapet Basement no longer needed, reused for Humand
       "Sign.052": "HUMAND", "Sign.003": "BASEMENT",
       # Cocos. The record is a medianera out at (50, 309) and nothing is built
       # on it — `facade_only` — so the only thing this pin does is stop the
       # allocation moving the brand the next time a sign is added. The wall it
       # actually lands on is in HERO.
       "Sign.060": "COCOS",
       # Brubank, same shape as Cocos: the record is a billboard out at
       # (172, 74) that is never built — `facade_only` — and the wall it lands
       # on is the one in HERO. The pin only stops the allocation walking the
       # brand off to another roof the next time this table grows.
       "Sign.061": "BRUBANK",
       # Patmos on spot 68. Sign.026 was ZONDA on the far south-west rim; the
       # record stays so nothing renumbers, and nothing is built from it —
       # facade_only. The wall is in HERO at (-113.75, 57.75).
       "Sign.026": "PATMOS",
       "Sign.058": "ETERMAX",
       # THE FOUR THAT TAKE OVER A SIGN NOBODY WOULD MISS. Three were carrying
       # a company that does not exist and the fourth a duplicate drawn with a
       # generic symbol, and all four brands below are `facade_only`, so what
       # happens is a trade: the roofmark or mast is never built and a real
       # logo appears on a wall.
       #
       # Mural lands on the very building its record is on, Ombú's. The other
       # three are the Cocos arrangement: the record is a sign the shot never
       # reaches or never raises, and it is here only so the allocation cannot
       # walk the brand off to another roof the next time this table grows.
       # Maslow moved off Pampa's building and onto Sign.019, which is a
       # different kind of takeover: 019 was a SECOND Ripio, drawn as a generic
       # violet disc before the wordmark existed. The brand keeps its parapet
       # on Sign.069, now with ripio.svg.
       "Sign.019": "MASLOW",        # was a second RIPIO, generic disc
       # Mural moved to spot 107, whose record is Sign.057 — the parapet
       # Bioceres used to hold as an unbuilt anchor. When Bioceres left, the
       # allocation gave it to PILAR, an invented name, which DOES build it:
       # 16.6 x 3.8 m and legible enough to enter 93's count. Pinning Mural
       # here puts a real brand on the site and retires that sign in one move.
       "Sign.057": "MURAL",         # was PILAR; before that Bioceres' anchor
       "Sign.046": "DECENTRALAND",  # was SALTO; the wall is at (66.2, -231.2)
       # Bioceres came off the U's west arm and onto spot 155, asked for.
       # 021 had been a walked Ripio disc before the brand got a real vector.
       "Sign.021": "BIOCERES",      # was RIPIO on spot 155, before that OLX
       # Berry, and the same shape as Cocos and Patmos: spot 147's cell already
       # carries a sign record (Sign.097, the Coderhouse anchor), and
       # `plan_extra` only runs on a cell with NO sign at all — so an EXTRA
       # anchor here would print NO ENTRARON and place nothing. It does not need
       # one. The record below is a roofmark on the far north-east rim that the
       # shot never reaches, carrying the invented name MATE; it is never built,
       # because the HERO entry is `facade_only`. All this pin does is keep the
       # allocation from walking the brand off to another roof the next time
       # this table grows. The wall it actually lands on is in HERO.
       "Sign.078": "BERRY",         # was MATE, an invented name
       # Conexa, and the same shape as Cocos, Patmos and Berry: the cell it
       # lands on — Takenos' L at (349.75, -167.0) — already carries a sign
       # record, so an EXTRA anchor there would print NO ENTRARON and place
       # nothing. It does not need one; `facade_at` decides where the art goes.
       #
       # THE RECORD IT TAKES IS THE TRADE, and this one is the version of it
       # that pays. Sign.025 is a roofmark carrying OMBU, an invented name, and
       # unlike Berry's MATE it is not off camera: it is BUILT and in frame for
       # 7.0 s at 0.023 of the frame width — under 93's 0.05 floor, so it is a
       # made-up company delivered as a smudge. It is the last such record the
       # shot still reaches; the only other two are ZONDA at 0.016 and YERBA,
       # which is in DROP. Pinning Conexa here retires it and puts a real brand
       # on a wall at 0.081, which is the trade the video wants.
       "Sign.025": "CONEXA"}        # was OMBU, an invented name
DROP = {"Sign.054",          # retired placeholder on SLA's replaced lot; its
                              # record stays so existing signs are not renumbered
        # the RIPIO roof on 179, which is the Etermax building: its wordmark
        # hangs off that facade and the Preguntados icon is laid flat on that
        # roof. Two brands on one address. Kept dropped after Ripio got its
        # SVG so a rebuild does not put a second copy back on that deck.
        "Sign.013",
        # the second copy of a brand that already appears elsewhere. The one the
        # camera sees least is dropped, and on a tie the flatter one: a sign
        # outside the frame does not earn its keep by being more three-
        # dimensional.
        "Sign.053", "Sign.055", "Sign.056"}
