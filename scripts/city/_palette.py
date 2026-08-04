"""Every colour in the city, once.

WHY THIS FILE EXISTS. The palette used to live in four places at the same time
and the last one to run won:

    00_setup.PALETTE      19 materials, created at build time
    03_ground.retint()    17 of them overwritten, and this is the one that won
    06_landmarks.repaint()  a few more overwritten again
    pbrmat("X", "#hex")   scattered through 02b, 03, 04, 06b, 10

`retint` and `repaint` are the same six lines written twice, and both carry the
same comment explaining that they had to exist because `pbrmat` fetches an
existing material by name and returns it UNTOUCHED - so once a colour is saved
in city.blend with a fake user, editing the hex in the script does nothing at
all and raises nothing at all. Two rebuilds were lost to that, once for the bus
shelters and once for the stadium facade.

So: one table, one value per material, and it always wins over what is already
in the .blend. The values below were read back out of the .blend rather than
copied from the scripts, so they are what the city actually renders, not what
the scripts hoped it rendered. Where the two disagreed, the .blend was right:
STYLE-BIBLE.md still lists asphalt as #3a3a3c and it has been #211e19 since
step 03 darkened the roads to put some black back in the frame.

WHAT IS NOT HERE. The company signs. Steps 04 and 10 invent one `Logo <brand>`
and one `Ink <brand>` per company, and the avenue formats (billboards and
medianeras) get a private pair per sign - `Logo Sign.045 BOCA` - on purpose, so
that dropping real artwork on one wall does not repaint four others. Those are
generated, not art-directed, and they stay with `pbrmat()`.

    from _palette import paint, apply_palette
    apply_palette()          # done for you by _common.open_city()
    paint("Asphalt")         # fetch, and enforce the table's colour
"""
import bpy

# name -> (hex, roughness, metallic)
PALETTE = {
    # --- the ground -------------------------------------------------------
    # The road sits at 0.18 luminance and is warm. The first pass was #3a3a3c,
    # cool grey at 0.38, which left no dark values in the frame at all.
    "Asphalt":          ("#211e19", 0.75, 0.0),
    "Asphalt Lot":      ("#26231e", 0.80, 0.0),   # car parks, inside the blocks
    "Busway":           ("#332a24", 0.86, 0.0),   # the Metrobus corridor
    "Sidewalk":         ("#98938a", 0.80, 0.0),
    "Marking":          ("#d8d8d2", 0.65, 0.0),
    "Paving":           ("#6e6a5e", 0.80, 0.0),
    "Paving Pale":      ("#a8a294", 0.85, 0.0),
    "Dirt":             ("#a08a6c", 0.90, 0.0),
    "Grass":            ("#4d9c26", 0.90, 0.0),
    "Water":            ("#6fb6cc", 0.08, 0.0),

    # --- the buildings ----------------------------------------------------
    # Four concrete families and two glasses. Warm is the dominant tone and
    # cool is the second family; brick is one facade in ten, not one in three.
    "Concrete Warm":    ("#e9dcc0", 0.85, 0.0),
    "Concrete Warm2":   ("#d8c4a0", 0.85, 0.0),
    "Concrete Cool":    ("#b6bcbd", 0.85, 0.0),
    "Concrete Cool2":   ("#8d9599", 0.85, 0.0),
    "Concrete Dark":    ("#6e7276", 0.85, 0.0),
    "Brick Warm":       ("#a86a4c", 0.85, 0.0),
    "Facade Teal":      ("#2f7f74", 0.75, 0.0),
    "Glass Light":      ("#5f97a6", 0.12, 0.0),
    "Glass Dark":       ("#15181b", 0.08, 0.0),
    "Glass Roof":       ("#c8d6d8", 0.10, 0.0),

    # --- roofs and rooftop plant -----------------------------------------
    "Roof Deck":        ("#d5d2c9", 0.88, 0.0),
    "Roof Dark":        ("#3a3a36", 0.90, 0.0),
    "Roof Bright":      ("#f4f3ef", 0.55, 0.0),
    "Roof Pipe":        ("#d0714a", 0.55, 0.0),   # the ductwork, terracotta
    "Solar":            ("#26436e", 0.20, 0.0),
    "Metal Painted":    ("#d8d8d6", 0.40, 0.0),
    "Metal Dark":       ("#3c4043", 0.55, 0.0),
    "Pole":             ("#9a9d9e", 0.45, 0.0),
    "Lamp":             ("#f2efe2", 0.30, 0.0),

    # --- planting ---------------------------------------------------------
    "Foliage Dark":     ("#2a6b1c", 0.90, 0.0),
    "Foliage Mid":      ("#4a9422", 0.90, 0.0),
    "Foliage Light":    ("#7cc32e", 0.90, 0.0),
    "Trunk":            ("#7a3a22", 0.90, 0.0),
    # The jacarandas are the one plant that is not green, and they are the
    # loudest porteno cue in the whole city from above.
    "Jacaranda Deep":   ("#6c5bb8", 0.80, 0.0),
    "Jacaranda Mid":    ("#8878d6", 0.80, 0.0),
    "Jacaranda Pale":   ("#a99ae4", 0.80, 0.0),

    # --- street furniture -------------------------------------------------
    "Bench Wood":       ("#8a5a34", 0.70, 0.0),
    "Table Green":      ("#1c7a46", 0.55, 0.0),
    "Signal Body":      ("#232628", 0.60, 0.0),
    "Signal Red":       ("#d02b22", 0.35, 0.0),
    "Signal Amber":     ("#e2a01c", 0.35, 0.0),
    "Signal Green":     ("#2fa04a", 0.35, 0.0),
    "Station Roof":     ("#3b3e42", 0.70, 0.0),   # the Metrobus shelters
    "Station Line":     ("#eceae4", 0.60, 0.0),
    "Sign Frame":       ("#2b2b28", 0.55, 0.0),

    # --- traffic ----------------------------------------------------------
    "Car Glass":        ("#9fc4cc", 0.10, 0.0),
    "Tire":             ("#1c1d1f", 0.85, 0.0),
    "Car White":        ("#e8e9e6", 0.35, 0.0),
    "Car Silver":       ("#a8adb0", 0.30, 0.0),
    "Car Dark":         ("#2f3336", 0.35, 0.0),
    "Car Red":          ("#c0332c", 0.35, 0.0),
    "Car Blue":         ("#3d6fb5", 0.35, 0.0),
    "Car Teal":         ("#1f9e93", 0.35, 0.0),
    "Car Yellow":       ("#e0a81c", 0.35, 0.0),
    # This camera sees mostly roof, and on a porteno taxi the roof IS the
    # livery. The yellow is egg yolk, not lemon.
    "Taxi Black":       ("#141416", 0.45, 0.0),
    "Taxi Yellow":      ("#f2c300", 0.45, 0.0),
    # Colectivo liveries. The name carries the hex because step 02b builds one
    # material per colour pair straight off the LIVERIES table.
    "Livery #1b5fa8":   ("#1b5fa8", 0.50, 0.0),
    "Livery #2f7d46":   ("#2f7d46", 0.50, 0.0),
    "Livery #c62828":   ("#c62828", 0.50, 0.0),
    "Livery #e2601a":   ("#e2601a", 0.50, 0.0),
    "Livery #f2c300":   ("#f2c300", 0.50, 0.0),
    "Livery #f2efe6":   ("#f2efe6", 0.50, 0.0),

    # --- people -----------------------------------------------------------
    "Skin Light":       ("#e0b48c", 0.75, 0.0),
    "Skin Mid":         ("#b57f52", 0.75, 0.0),
    "Skin Dark":        ("#6f4a30", 0.75, 0.0),
    "Hair Dark":        ("#2b2320", 0.80, 0.0),
    "Hair Blonde":      ("#d9b25e", 0.80, 0.0),
    "Hair Grey":        ("#b9b6b0", 0.80, 0.0),
    "Hair Red":         ("#a4482a", 0.80, 0.0),
    "Shirt White":      ("#e6e6e2", 0.75, 0.0),
    "Shirt Blue":       ("#3f6fa8", 0.75, 0.0),
    "Shirt Red":        ("#b83b34", 0.75, 0.0),
    "Shirt Green":      ("#3f8f52", 0.75, 0.0),
    "Shirt Grey":       ("#7e8386", 0.75, 0.0),
    "Shirt Teal":       ("#2f9c93", 0.75, 0.0),
    "Shirt Orange":     ("#d97b28", 0.75, 0.0),
    "Shirt Purple":     ("#6a4b9c", 0.75, 0.0),
    "Pants Dark":       ("#33363a", 0.75, 0.0),
    "Pants Denim":      ("#4a6484", 0.75, 0.0),
    "Pants Khaki":      ("#a89168", 0.75, 0.0),
    "Pants Navy":       ("#2c3a52", 0.75, 0.0),

    # --- accents ----------------------------------------------------------
    "Accent Red":       ("#c8302a", 0.45, 0.0),
    "Accent Yellow":    ("#e8b520", 0.45, 0.0),
    "Accent Magenta":   ("#c9268f", 0.45, 0.0),

    # --- the stadium ------------------------------------------------------
    # The facade is DARK and that is the whole point of it. At #8d8b86 it
    # rendered the same value as the seats and the stadium went back to being
    # one smooth white drum with a lawn in it: the rake reads from outside only
    # because there is something darker underneath it.
    "Stadium Facade":   ("#403e3a", 0.90, 0.0),
    "Stadium Shell":    ("#8b877f", 0.90, 0.0),
    "Stadium Apron":    ("#6e716d", 0.94, 0.0),
    "Stadium Red":      ("#bd2b2f", 0.82, 0.0),
    "Stadium Ad Dark":  ("#26282c", 0.74, 0.0),
    "Stadium Ad Blue":  ("#1d4f9e", 0.72, 0.0),
    "Seat White":       ("#e2dfd7", 0.90, 0.0),
    "Seat Red":         ("#c1212c", 0.86, 0.0),
    # Brick dust, warm and a good deal more saturated than anything else on
    # that block, which is what makes it read against the pitch from above.
    "Track Clay":       ("#b1573c", 0.92, 0.0),
    "Pitch Grass":      ("#3f8a39", 0.94, 0.0),

    # --- the porteno landmarks -------------------------------------------
    "Obelisco Stone":   ("#d9d2c2", 0.72, 0.0),
    "Obelisco Dark":    ("#2a2724", 0.80, 0.0),
    "Steel Bright":     ("#c9ccd0", 0.22, 0.9),   # the Floralis petals
    "Shield Bronze":    ("#8a6a3c", 0.45, 0.5),
    "Flag Blue":        ("#74acdf", 0.70, 0.0),
    "Flag White":       ("#f2f2ee", 0.70, 0.0),
    "Tile Red":         ("#9c4a33", 0.85, 0.0),
    "Cupola Slate":     ("#4a6b63", 0.65, 0.0),
    "Cupola Trim":      ("#cfc7b4", 0.75, 0.0),

    # --- the title --------------------------------------------------------
    "Title Red":        ("#ac0300", 0.55, 0.0),
    "Title Edge":       ("#1a1210", 0.70, 0.0),
}


def srgb(hex_str):
    """#rrggbb -> linear RGB, which is what Blender sockets want."""
    h = hex_str.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def _write(m, hex_col, rough, metal):
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = tuple(srgb(hex_col)) + (1.0,)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal


def define(name, hex_col, rough=0.8, metal=0.0):
    """Create or update one material. The values passed here always win."""
    import blib
    m = bpy.data.materials.get(name)
    if m is None:
        m = blib.pbr(name, srgb(hex_col), roughness=rough, metallic=metal)
        m.use_fake_user = True
    else:
        _write(m, hex_col, rough, metal)
    return m


def apply_palette():
    """Bring every material in the table up to date. Idempotent, and cheap.

    Called once by `_common.open_city()`, so a colour edited here shows up in
    the very next step that runs, whichever one it is - no rebuild of the layer
    that happened to create the material first.
    """
    for name, (hex_col, rough, metal) in PALETTE.items():
        define(name, hex_col, rough, metal)
    return len(PALETTE)


def paint(name):
    """The material, with the table's colour enforced.

    Use this instead of `bpy.data.materials[name]` when a step is art-directing
    a colour. It raises on an unknown name rather than inventing a grey one:
    a typo used to give you a default material and a slightly wrong render.
    """
    if name not in PALETTE:
        raise KeyError(f"'{name}' is not in the palette. Add it to "
                       f"_palette.PALETTE, or use pbrmat() if it is generated "
                       f"artwork rather than an art-directed colour.")
    return define(name, *PALETTE[name])
