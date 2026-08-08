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
    ("VERCEL",    "triangle", "#f7f3e8", "#111111", "vercel.svg"),
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
    # no vector: generic symbol, until the SVG turns up
    ("RIPIO",     "disc",     "#f7f3e8", "#7b2ff7", None),
    ("ETERMAX",   "bars",     "#f7f3e8", "#28292b", "etermax_word.svg"),
    ("OLX",       "ring",     "#f7f3e8", "#6e2fb8", None),
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
    ("BELO",         "disc",     "#f7f3e8", "#5300da", "belo.svg"),
    ("COCOS",        "ring",     "#f7f3e8", "#002c65", "cocos.svg"),
    # no vector
    ("MODO",         "disc",     "#f7f3e8", "#00a15a", None),
]


def pools(campus_filler, avenue_filler):
    """The real ones first, the invented filler after.

    The filler is the tables 04 already had. They are not thrown away: there are
    94 signs and 21 real brands, so the remaining 73 — none of which reaches the
    camera at a legible size — still carry the invented ones.
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
    # The six below share one key and the key is `facade_only`: the logo on the
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
    "BELO": {"word": "belo.svg", "iso": "belo.svg",
             "facade": True, "facade_only": True,
             "facade_side": "right", "facade_at": (172.2, -377.2),
             # high: at 0.74 the bottom half sat behind the roof of the building
             # in front
             "facade_frac": 0.78, "facade_tall": 0.50,
             "facade_z": 0.80, "facade_depth": 0.35},
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
    "TAKENOS": {"iso": "takenos_iso.svg", "word": "takenos_word.svg",
                "iso_frac": 0.80, "roof_frac": 0.0,
                "facade": True, "facade_side": "left",
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
    # the triangle alone on the disc, small, and the whole logo on the wall
    "VERCEL": {"iso": "vercel_iso.svg", "word": "vercel.svg",
               "iso_frac": 0.52,
               "facade": True, "facade_side": "left",
               "facade_frac": 0.66, "facade_tall": 0.20, "facade_z": 0.74,
               "facade_depth": 0.30,
               "iso_ink": "#111111", "word_ink": "#111111"},
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
       # and Rebill on 188, which carried RIPIO: not a client, no vector, and it
       # was showing up with the generic symbol. Ripio drops one place in the
       # allocation, it does not leave the frame.
       "Sign.015": "REBILL",
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
       "Sign.058": "ETERMAX"}
DROP = {"Sign.054",          # flat Satellogic on 98: the 3D one on 163 remains
        # the RIPIO roof on 179, which is the Etermax building: its wordmark
        # hangs off that facade and the Preguntados icon is laid flat on that
        # roof. Two brands on one address, and Ripio came out repeated on camera
        # on top of that. It surfaced when Rebill moved and the allocation gave
        # that site to the next brand on the list.
        "Sign.013",
        # the second copy of a brand that already appears elsewhere. The one the
        # camera sees least is dropped, and on a tie the flatter one: a sign
        # outside the frame does not earn its keep by being more three-
        # dimensional.
        "Sign.053", "Sign.055", "Sign.056"}
