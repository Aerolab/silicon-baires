"""Las marcas reales, una tabla, y el orden es la prioridad.

`assign_brands()` en 04 reparte los nombres por visibilidad: rankea los carteles
por `shot_cover` y le da al más visible la primera entrada sin usar. Así que el
ORDEN DE ESTAS LISTAS ES EL ORDEN EN QUE LA CÁMARA LOS ENCUENTRA. Las marcas con
SVG van primero porque son las que se construyen en 3D, extruidas de la curva
real; las que solo existen en bitmap van después, con un símbolo genérico; y las
inventadas van al final, que es donde la cámara ya no llega.

No hace falta que la tabla tenga un largo determinado. `DRAW_WIDTH` en 04 está
pinneado por otro motivo (el sorteo durante la colocación consume RNG y mueve
edificios), y la marca que ese sorteo elige es un placeholder que esta tabla
pisa entera al final del run.

`svg` es el archivo bajo `assets/logos/`. Si es None la marca cae al símbolo
geométrico de `mark`, que es el sistema con el que se construyó la ciudad.
Ver `assets/logos/SOURCES.md` para de dónde salió cada archivo y qué le falta.

`face` es el color del cartel y `ink` el del logo. `ink` solo se usa cuando el
SVG es monocromo o no declara color: cuando el archivo trae su propia paleta
(Globant son dos colores, Pomelo son seis) manda el archivo, porque el color es
parte de la marca y no una decisión de esta ciudad.
"""

# (text, mark, face, ink, svg)

# El parque de oficinas: parapetos, roofmarks y mástiles.
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
    # sin vector: símbolo genérico, hasta que aparezca el SVG
    ("RIPIO",     "disc",     "#f7f3e8", "#7b2ff7", None),
    ("ETERMAX",   "bars",     "#f7f3e8", "#28292b", "etermax_word.svg"),
    ("OLX",       "ring",     "#f7f3e8", "#6e2fb8", None),
]

# La avenida: medianeras y billboards. Le habla al que maneja, no al que busca
# trabajo, así que acá van las de consumo masivo.
AVENUE = [
    ("MERCADO LIBRE", "disc",    "#ffe600", "#303576", "mercadolibre.svg"),
    ("UALA",         "chevron",  "#f7f7fb", "#406afc", "uala.svg"),
    ("NARANJA X",    "bars",     "#f7f3e8", "#f65100", "naranjax.svg"),
    ("DESPEGAR",     "triangle", "#f7f3e8", "#5516ec", "despegar.svg"),
    ("LEMON",        "square",   "#d6f24a", "#003f20", "lemon.svg"),
    ("TIENDANUBE",   "ring",     "#f7f3e8", "#111111", "tiendanube.svg"),
    ("DIGITAL HOUSE", "square",  "#101820", "#ffffff", "digitalhouse.svg"),
    # sin vector
    ("MODO",         "disc",     "#f7f3e8", "#00a15a", None),
]


def pools(campus_filler, avenue_filler):
    """Las reales primero, las inventadas de relleno después.

    El relleno son las tablas que ya tenía 04. No se tiran: hay 94 carteles y
    21 marcas reales, así que los 73 restantes (ninguno de los cuales llega a
    la cámara con tamaño legible) siguen llevando las inventadas.
    """
    return ([b[:4] for b in CAMPUS] + list(campus_filler),
            [b[:4] for b in AVENUE] + list(avenue_filler))


LOGOS = {b[0]: b[4] for b in CAMPUS + AVENUE if b[4]}


# Marcas que reciben el trato de hero, y por ahora es una.
#
# Un logotipo entero colgado de un parapeto es lo que menos se lee de todo lo
# que se probó: la caja del lockup incluye el isotipo, el aire y las
# ascendentes, así que a la altura que entra bajo el alero las letras salen del
# tamaño de una ventana. Partirlo en dos resuelve las dos mitades por separado,
# y es además como se monta de verdad: el símbolo grande en la pared, que es una
# forma y se lee a cualquier distancia, y el nombre acostado en la azotea, donde
# no compite con nada y puede medir cuarenta metros.
#
#   iso        el símbolo solo, colgado del parapeto
#   word       el logotipo solo, tumbado en la azotea del edificio dueño
#   iso_frac   alto del símbolo como fracción de la altura del edificio
#   roof_frac  cuánto del techo puede ocupar el logotipo
#   iso_ink    color del isotipo, y word_ink el del logotipo. Son dos porque
#              no siempre son el mismo: Lemon va verde arriba y negro abajo.
#   face       pisa el color del cartel que sostiene el isotipo
#   roof_at    (x, y) del techo donde va el logotipo. Sin esto usa el del
#              edificio dueño del cartel, que es lo normal; con esto se puede
#              cruzar a la azotea de al lado, que es lo que pidió Lemon.
HERO = {
    "AUTH0": {"iso": "auth0_iso.svg", "word": "auth0_word.svg",
              "iso_frac": 0.55, "roof_frac": 0.72},
    "LEMON": {"iso": "lemon_iso.svg", "word": "lemon_word.svg",
              "iso_frac": 0.86, "roof_frac": 0.78,
              "roof_at": (181.5, -303.4),
              "iso_ink": "#44df19", "word_ink": "#111111",
              # el disco pasa a crema: el verde del isotipo sobre el verde que
              # tenia el mastil no se veia, y el color que manda es el del logo
              "face": "#f7f3e8"},
    # el isotipo en el roofmark del techo y el logotipo cruzando la fachada
    # izquierda, que es la cara que esta camara ve de ese lado
    "TAKENOS": {"iso": "takenos_iso.svg", "word": "takenos_word.svg",
                "iso_frac": 0.80, "roof_frac": 0.0,
                "facade": True, "facade_side": "left",
                "facade_frac": 0.80, "facade_tall": 0.26, "facade_z": 0.60,
                "iso_ink": "#6d37d5", "word_ink": "#6d37d5"},
    # el isotipo solo sobre la medianera, sin panel, y el logotipo tumbado en
    # el techo del 128, que corre a lo largo del lado de 35 m
    "TIENDANUBE": {"iso": "tiendanube_iso.svg", "word": "tiendanube_word.svg",
                   "wall_frac": 1.0, "roof_frac": 0.80,
                   "roof_at": (165.34, -149.69)},
    # el mismo archivo partido por color: los nueve trazos naranjas son la
    # palabra, los dos violetas son la X. Sin panel: las letras directas en el
    # techo y la X colgada del frente
    "NARANJA X": {"iso": "naranjax.svg", "word": "naranjax.svg",
                  "iso_x": [0.85, 1.01], "word_x": [-0.01, 0.85],
                  "wall_frac": 1.0, "roof_frac": 0.78},
    # el lockup entero colgado del frente, nada en el techo. El archivo trae
    # una forma sin color ocupando el 40% izquierdo que no es parte de la
    # marca: el corte empieza en 0.38 y la deja afuera
    "POMELO": {"word": "pomelo.svg", "iso": "pomelo.svg",
               "word_x": [0.55, 1.01], "iso_x": [0.38, 0.55],
               "roof_art": "iso", "iso_roof_frac": 0.42,
               # hacia la esquina de la entrada, no en el medio del techo
               "iso_roof_shift": (0.0, 0.22), "iso_roof_rot": 90,
               "facade_depth": 0.30,
               "facade": True, "facade_only": True, "facade_side": "right",
               # alto en la pared a proposito: delante hay dos farolas de
               # 9.1 m y arboles de vereda, y a media altura el logo queda
               # detras de ellos
               "facade_frac": 0.74, "facade_tall": 0.26, "facade_z": 0.86},
    # el isotipo enorme sobre la calle en un edificio y el logotipo tumbado en
    # el techo del de al lado: dos direcciones distintas para una marca sola
    "AEROLAB": {"iso": "aerolab.svg", "word": "aerolab.svg",
                "iso_x": [-0.01, 0.21], "word_x": [0.21, 1.01],
                "facade": True, "facade_only": True, "facade_art": "iso",
                "facade_side": "right", "facade_at": (25.92, 17.37),
                "facade_frac": 0.58, "facade_tall": 0.50, "facade_z": 0.74,
                "facade_depth": 0.35,
                "roof_art": "word", "roof_at": (33.75, 5.13),
                "word_roof_frac": 0.78,
                "iso_ink": "#ff510d", "word_ink": "#1c1c1c"},
    # se muda del 113 al 179: el logotipo en un renglon sobre la pared y el
    # icono de Preguntados acostado en el techo, que es lo que esa empresa
    # pone en un edificio antes que su propio nombre
    "ETERMAX": {"word": "etermax_word.svg", "icon": "preguntados.svg",
                "iso": "etermax_word.svg",
                "facade": True, "facade_only": True, "facade_side": "right",
                "facade_at": (316.25, -149.69),
                # dos renglones es como se escribe esta marca, asi que lo que
                # ata es la altura y no el ancho: 0.24 daba un logo de 5.8 m
                # en una pared de 35
                "facade_frac": 0.74, "facade_tall": 0.54,
                "facade_z": 0.76, "facade_depth": 0.30,
                # blanco: el archivo trae el gris casi negro de la marca y
                # esa fachada es marron oscura, asi que el logo desaparecia
                "word_ink": "#ffffff",
                "roof_art": "icon", "roof_at": (316.25, -149.69),
                "icon_roof_frac": 0.46},
    # ocupa el 84, que quedo libre cuando basement se fue al 123
    "HUMAND": {"iso": "humand.svg", "word": "humand.svg",
               "facade": True, "facade_only": True, "facade_side": "left",
               "facade_at": (-84.25, 57.75),
               # ESTE SIGUE SEPARADO DE SU PARED, y a proposito. El footprint
               # de este edificio va 1.2 m mas ancho que la fachada, y el
               # cartel se apoya en el borde del footprint. Acercarlo con un
               # `facade_proud` negativo no lo pega: lo mete DENTRO del
               # volumen, y 99_check_overlap lo encuentra ahi (246 a 1685
               # pares de triangulos segun cuanto se acerque). Es el unico de
               # los diez al que le sobra aire.
               "facade_frac": 0.70, "facade_tall": 0.18,
               "facade_z": 0.93, "facade_depth": 0.55},
    # se muda del 84 al 123: el parapeto desaparece de su edificio y el
    # logotipo aparece colgado de la pared del otro, dejando el 84 libre
    "BASEMENT": {"iso": "basement.svg", "word": "basement.svg",
                 "facade": True, "facade_only": True, "facade_side": "wide",
                 "facade_at": (66.25, 17.63),
                 # arriba de todo y con cuerpo: estas fachadas tienen una
                 # cornisa por piso y un logo chato a media altura queda
                 # cortado en tiras por ellas
                 "facade_frac": 0.80, "facade_tall": 0.20,
                 "facade_z": 0.93, "facade_depth": 0.55},
    # el triangulo solo en el disco, chico, y el logo entero sobre la pared
    "VERCEL": {"iso": "vercel_iso.svg", "word": "vercel.svg",
               "iso_frac": 0.52,
               "facade": True, "facade_side": "left",
               "facade_frac": 0.66, "facade_tall": 0.20, "facade_z": 0.74,
               "facade_depth": 0.30,
               "iso_ink": "#111111", "word_ink": "#111111"},
    # el 120 queda vacio: el mural se va entero a la pared del 101
    "UALA": {"iso": "uala2.svg", "word": "uala2.svg",
             "facade": True, "facade_only": True, "facade_side": "left",
             "facade_at": (-12.79, -89.29),
             "facade_frac": 0.80, "facade_tall": 0.20, "facade_z": 0.80,
             "facade_depth": 0.30},
    # el complejo de tres alas: el apreton en el techo del 114, el logotipo
    # sobre la pared izquierda de esa misma ala, que mira a la plaza
    "MERCADO LIBRE": {"iso": "ml_iso.svg", "word": "mercadolibre.svg",
                      "facade": True, "facade_only": True,
                      "facade_arts": ["iso", "word"],
                      "facade_at": (43.75, -155.38),
                      "facade_depth": 0.35,
                      # el apreton en la cara del frente
                     "iso_facade_side": "right", "iso_facade_frac": 0.82,
                      "iso_facade_tall": 0.52, "iso_facade_z": 0.74,
                      # y el logotipo, en un solo renglon, sobre la cara larga
                      # que mira a la plaza
                      "word_facade_side": "left", "word_oneline": True,
                      "word_facade_frac": 0.88, "word_facade_tall": 0.30,
                      "word_facade_z": 0.72},
    # y el apreton celeste en el ala de al lado
    "MERCADO PAGO": {"iso": "mp_iso.svg", "word": "mp_iso.svg",
                     "facade_only": True, "facade_arts": ["iso"],
                     "facade_at": (23.66, -155.38),
                     "iso_facade_side": "right", "iso_facade_frac": 0.82,
                     "iso_facade_tall": 0.52, "iso_facade_z": 0.74,
                     "facade_depth": 0.35},
}


# Carteles con la marca clavada a mano, y carteles que no se construyen.
#
# El reparto por visibilidad de 04 es una buena regla y no sabe mirar. Cuando
# alguien mira el cuadro y dice "esta marca va en ESE cartel", eso gana: es la
# única información que ninguna métrica de este proyecto puede producir. PIN se
# aplica antes del reparto y saca esa marca del pool, así que el resto se
# reparte igual que siempre entre los que quedan.
#
# DROP es lo mismo por la negativa. El billboard de Lemon se sacó porque la
# marca se mudó al mástil de al lado y al techo vecino, y dos veces la misma
# marca en el mismo cuadro es una marca menos en el video.
# Carteles a los que se les cambia el tamano a mano, como fraccion del que
# planifico 04. El plan dimensiona por lo que entra en el techo y por lo que se
# lee a distancia, que son dos buenas reglas y ninguna de las dos mira el
# cuadro: un disco de 19 m puede caber y aun asi comerse la esquina.
#
# El solido publicado NO se achica con esto. Sigue reservando el espacio
# original, asi que un cartel encogido deja aire alrededor en vez de invitar a
# que le planten un arbol al lado.
SIZE = {"Sign.005": 0.62,
        # el disco de Vercel: solo un triangulo, y chico
        "Sign.001": 0.42}

PIN = {"Sign.023": "LEMON", "Sign.014": "TAKENOS",
       "Sign.018": "TIENDANUBE", "Sign.008": "NARANJA X",
       "Sign.009": "POMELO", "Sign.020": "AEROLAB",
       "Sign.005": "AUTH0", "Sign.001": "VERCEL",
       "Sign.006": "SATELLOGIC", "Sign.007": "DESPEGAR",
       "Sign.004": "UALA", "Sign.002": "MERCADO LIBRE",
       "Sign.016": "MERCADO PAGO",
       # las que sobrevivieron al descarte de repetidas, clavadas para que el
       # proximo pin no las mueva a otro techo
       "Sign.000": "GLOBANT", "Sign.003": "BASEMENT",
       "Sign.010": "TECHNISYS", "Sign.011": "ALEPH",
       # el parapeto que sobraba de basement, reusado para humand
       "Sign.052": "HUMAND", "Sign.003": "BASEMENT",
       "Sign.058": "ETERMAX"}
DROP = {"Sign.017",          # billboard de Lemon, la marca se mudo
        "Sign.054",          # satellogic plano en el 98: queda el 3d del 163
        "Sign.012",          # billboard de despegar en el 134
        # la segunda copia de una marca que ya aparece en otro lado. Se
        # descarta la que la camara ve peor, y a igualdad la mas plana: un
        # cartel fuera del cuadro no compensa ser mas tridimensional.
        "Sign.053", "Sign.055", "Sign.056"}
