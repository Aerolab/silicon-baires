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


## Sumar una marca, en cinco pasos

    ./bl scripts/city/90_brand_sites.py

devuelve los edificios libres con la pared que hay que usar, cuánto de esa
pared ve la cámara, a qué distancia está la vereda y qué tamaño entra. Después:

  1. El SVG a `assets/logos/`, con `width`/`height` explícitos sacados del
     `viewBox` - el importador de Blender no entiende `width="100%"` y devuelve
     una curva vacía sin avisar. Anotar la fuente en `SOURCES.md`.
  2. La marca a `CAMPUS` (B2B) o `AVENUE` (consumo), con su color.
  3. El edificio a `EXTRA`, con la coordenada que dio 90. Es un ANCLA: no se
     construye, existe para que el manifiesto tenga un registro al que clavarle
     la marca.
  4. La pared a `HERO`, con `facade_only` y el `facade_side` que dio 90. Un
     logotipo lo ata el ancho de la pared, un isotipo el alto, y la planta baja
     está retranqueada: el logo vive entre los 5 m y la cornisa.
  5. `./bl scripts/city/04_buildings.py && ./bl scripts/city/10_signs.py`, y
     MIRAR EL RENDER. Después la cadena completa desde 06, y 93 para el número.

Lo que NO hay que volver a deducir - cada uno costó un render:

  · Un logo va en el FRENTE, no en el techo. Un roofmark a 250 m es un
    rectángulo pálido; una pared son 28 m de letras.
  · "La cara más larga" es casi siempre la de adentro del complejo.
  · Una pared puede dar a la calle y estar tapada igual, por el otro brazo de
    la propia L o por el vecino a un metro. Es una pregunta de línea de visión.
  · Una marca por dirección, y la dirección es la CELDA, no el ala. Las
    excepciones se declaran en `SHARED` con el motivo.
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
    # las tres B2B de la tanda nueva. Van clavadas por EXTRA, así que su lugar
    # en esta lista no decide nada: está para que la marca exista con su color.
    #
    # Las seis van pegadas a una FACHADA, sin panel detrás, así que el color
    # lo decide la pared y no esta tabla. Complif es el caso donde se ve: se
    # probaron las dos variantes del archivo y se miraron, y la pared de esa
    # esquina es de ladrillo oscuro, así que gana el blanco de la web. La
    # variante oscura quedó en assets por si la marca se muda a una pared
    # clara. Ver SOURCES.md, que ya anotaba lo mismo para otras cuatro.
    ("COMPLIF",   "ring",     "#1c1c1c", "#ffffff", "complif.svg"),
    ("REBILL",    "chevron",  "#f7f3e8", "#111111", "rebill.svg"),
    ("PAISANOS",  "square",   "#101820", "#ffffff", "paisanos.svg"),
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
    # las tres de consumo de la tanda nueva, tambien clavadas por EXTRA
    ("GALICIA",      "disc",     "#f7f3e8", "#ff7f00", "galicia_iso.svg"),
    ("CODERHOUSE",   "bars",     "#f7f3e8", "#1d1d1d", "coderhouse.svg"),
    ("BELO",         "disc",     "#f7f3e8", "#5300da", "belo.svg"),
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
    # ---- la tanda de agosto 2026 ------------------------------------------
    # Las seis en la misma clave y la clave es `facade_only`: el logo pegado a
    # la pared del edificio y NADA en el techo. El ancla de cada una está en
    # EXTRA (o en PIN, para las dos que reusan un billboard apagado) y no se
    # construye; lo único que sale de acá es el logotipo sobre la fachada.
    #
    # QUÉ CARA. Son dos las que esta cámara ve, la +X y la +Y, y elegir la más
    # larga con "wide" es elegir mal: la cara larga de estos edificios suele
    # ser la de adentro del complejo. Belo, Paisanos y Complif quedaron
    # colgados de una pared que da a un patio a 17-32 m de la calle, y un logo
    # de empresa va sobre la vereda. La cara buena se midió contra la tabla de
    # calles - la que tiene la vereda a menos de 4 m - y en los tres es la +Y,
    # que es "right". Los otros dos son L y ahí manda otra cosa: la cara que no
    # da contra el propio brazo. Ver los comentarios de cada uno.
    "GALICIA": {"iso": "galicia_iso.svg", "word": "galicia_iso.svg",
                # solo el isotipo, porque es lo único que hay en vector de la
                # marca actual - ver SOURCES.md. Cuadrado y grande, que es
                # justo lo que mejor aguanta una pared vista desde 250 m
                "facade": True, "facade_only": True, "facade_art": "iso",
                # EL ALA CHICA Y SU CARA NORTE, y las dos cosas costaron un
                # render cada una. Este edificio es una L: en el ala grande la
                # cara larga da contra el otro brazo (el disco entraba medio
                # metido adentro y asomaba un gajo naranja detrás del techo) y
                # la otra cara queda a 1,3 m del edificio vecino, que la tapa
                # entera. El ala chica tiene su cara norte al aire.
                "facade_side": "left", "facade_at": (165.3, 11.0),
                # lo que ata a un isotipo cuadrado es el ALTO de la pared, no
                # el ancho: a 0,52 el disco medía 12,7 m sobre 27 m de pared
                "facade_frac": 0.72, "facade_tall": 0.76,
                "facade_z": 0.62, "facade_depth": 0.45},
    "CODERHOUSE": {"word": "coderhouse.svg", "iso": "coderhouse.svg",
                   # 8,4:1 de una sola palabra: lo que la ata es el ancho, y
                   # por eso va en la cara larga del edificio más alto
                   "facade": True, "facade_only": True,
                   # misma L, mismo problema: en la cara larga la palabra
                   # entraba a la mitad en el ala de al lado y se leía "CODE"
                   "facade_side": "left", "facade_at": (201.8, -14.8),
                   # arriba de todo y con cuerpo, que es la receta de
                   # Basement: esta fachada tiene una cornisa por piso y una
                   # palabra chata a media altura sale cortada en tiras
                   "facade_frac": 0.86, "facade_tall": 0.22,
                   "facade_z": 0.93, "facade_depth": 0.55},
    "BELO": {"word": "belo.svg", "iso": "belo.svg",
             "facade": True, "facade_only": True,
             "facade_side": "right", "facade_at": (172.2, -377.2),
             # alto: a 0,74 la mitad de abajo quedaba detrás del techo del
             # edificio de adelante
             "facade_frac": 0.78, "facade_tall": 0.50,
             "facade_z": 0.80, "facade_depth": 0.35},
    # SE MUDÓ DEL 133 AL 188, y la mudanza es la parte que importa. El 133
    # parecía libre y no lo estaba: su dirección ya la tenía Tiendanube, cuyo
    # logotipo está tumbado en el techo del ala de al lado. Dos marcas en una
    # dirección es exactamente lo que la regla prohíbe, y no lo vio nadie
    # porque `thin` no mira los puestos a mano y 93 agrupaba por ala.
    # El 188 tiene 66 m de pared al norte, que es la más larga de la tanda.
    "REBILL": {"word": "rebill.svg", "iso": "rebill.svg",
               "facade": True, "facade_only": True,
               "facade_side": "right", "facade_at": (333.0, -243.0),
               "facade_frac": 0.55, "facade_tall": 0.35,
               "facade_z": 0.72, "facade_depth": 0.30},
    # LAS DOS CARAS DEL 146, una por arte, que es el reparto de Mercado Libre:
    # el isotipo lima en el frente que da a la avenida, y el logotipo cruzando
    # la cara izquierda, que son 35 m de pared contra los 14,5 del frente. Es
    # la respuesta a lo que a este edificio le sobra y le falta: la cara buena
    # es corta y alta, así que ahí va el símbolo, que es cuadrado; la larga es
    # baja, así que ahí va la palabra, que es 6:1.
    #
    # El ala 146 es la otra ala del mismo edificio donde está el ancla, así que
    # las dos artes siguen siendo una marca por dirección. El archivo trae
    # logotipo e isotipo en una pieza cada uno, y se parte por posición como
    # Naranja X: el blanco es la palabra, el lima de la derecha es el símbolo.
    "PAISANOS": {"iso": "paisanos.svg", "word": "paisanos.svg",
                 "iso_x": [0.55, 1.01], "word_x": [-0.01, 0.55],
                 "facade": True, "facade_only": True,
                 "facade_arts": ["iso", "word"],
                 "facade_at": (194.9, -149.8), "facade_depth": 0.40,
                 # el símbolo, en el frente. Este edificio tiene 16,9 m y lo
                 # que lo limita es el alto de la pared. De cornisa a vereda NO
                 # entra: la planta baja está retranqueada y el pie del logo se
                 # metía adentro (99_check_overlap, 8 pares de triángulos).
                 # Entre 4,9 y 16,4 m hay pared de verdad.
                 "iso_facade_side": "right", "iso_facade_frac": 0.90,
                 "iso_facade_tall": 0.68, "iso_facade_z": 0.63,
                 # y la palabra, en un renglón, sobre la cara izquierda
                 "word_facade_side": "left", "word_oneline": True,
                 "word_facade_frac": 0.74, "word_facade_tall": 0.30,
                 "word_facade_z": 0.62},
    "COMPLIF": {"word": "complif.svg", "iso": "complif.svg",
                "facade": True, "facade_only": True,
                "facade_side": "right", "facade_at": (195.0, -368.7),
                # a fondo: la cara que da a la calle de este edificio es la
                # corta, 14,5 m, y es el techo de lo que Complif puede medir
                "facade_frac": 0.95, "facade_tall": 0.34,
                "facade_z": 0.74, "facade_depth": 0.32},
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

# Carteles nuevos sobre techos elegidos a mano, y la razón por la que esta
# tabla va por COORDENADA y no por Sign.NNN como PIN.
#
# Sign.NNN es un ordinal: `thin()` ordena los carteles por lo que la cámara ve
# de cada uno y recién ahí los numera, así que un cartel nuevo se mete en el
# medio del ranking y le corre el número a todos los que ve peor. Un cartel
# agregado por acá le habría cambiado el techo a la mitad de las marcas ya
# aprobadas, en silencio. Por eso estos se planifican durante el recorrido de
# lotes (que es lo único que puede reservarles el lugar contra los equipos de
# azotea) pero se numeran DESPUÉS de todo, a partir de Sign.094: el reparto de
# los 94 de siempre queda intacto y estos seis se agregan atrás.
#
#   at     el centro del ala del techo, tal como sale de city_solids.json.
#          Entre paréntesis, el número de spot con `?spots=1` en el navegador,
#          que es como se eligieron.
#   kind   parapet | roofmark | mast, los mismos tres formatos de 04.
#   grow   el multiplicador de tamaño de shape_sign.
#
# EL TAMAÑO LO DECIDE EL TECHO, no este número. `grow` está topeado por lo que
# entra en el ala, así que la escala de una marca se elige eligiendo el techo:
# el mástil de Galicia mide 21 m porque está en un ala de 28, y Complif mide
# 10 en una de 20. `grow` solo termina de acomodar, y el piso es el mismo que
# mide 93_check_signs: 5 % del ancho de cuadro, o el cartel no se entrega.
EXTRA = [
    # LOS CUATRO SON ANCLAS, NO CARTELES. Cada uno lleva su marca a un edificio
    # y ahí termina su trabajo: la entrada de HERO que le corresponde tiene
    # `facade_only`, así que 10_signs no levanta ningún panel y lo único que se
    # construye es el logo pegado a la pared. El formato que dice acá no se ve
    # en ningún lado; está porque un cartel tiene que existir en el manifiesto
    # para que una marca se le pueda clavar.
    #
    # Primero fueron carteles de verdad - roofmarks y billboards - que es lo
    # que el reparto sabe hacer solo. Está mal para esta ciudad: las marcas se
    # vienen sumando colgadas del frente, que es donde un logotipo tiene 28 m
    # de pared y se lee, y no tumbadas en una azotea, donde a 250 m son un
    # rectángulo pálido.
    #
    # Coderhouse en el edificio más alto del corredor (32 m).
    {"at": (201.8, -14.8), "spot": 153, "brand": "CODERHOUSE",
     "kind": "roofmark", "grow": 1.45},
    # Complif, la más chica de las seis, en el último edificio libre del
    # corredor: 14,5 x 18 en el borde sur, 2 s de paso.
    {"at": (195.0, -368.7), "spot": 148, "brand": "COMPLIF",
     "kind": "roofmark", "grow": 1.45},
    {"at": (201.8, -184.2), "spot": 152, "brand": "PAISANOS",
     "kind": "roofmark", "grow": 1.45},
]


# Direcciones donde DOS marcas conviven a propósito, y por qué.
#
# 93_check_signs prohíbe dos marcas en una dirección, y la regla es buena: dos
# logos en un edificio leen como una empresa con dos marcas. Pero hay un caso
# donde la respuesta correcta es que sí, y sin esta tabla la única salida era
# apagar el chequeo o mentirle. Se declara, con el motivo, y se ve en el
# informe: una excepción anotada no es lo mismo que una regla que no corre.
SHARED = {
    # el complejo de tres alas: Mercado Libre en un ala y el apretón celeste de
    # Mercado Pago en la de al lado. Son dos marcas de la misma casa y así se
    # montan de verdad.
    (33.75, -167.0): "Mercado Libre y Mercado Pago, misma casa",
}


PIN = {"Sign.023": "LEMON", "Sign.014": "TAKENOS",
       "Sign.018": "TIENDANUBE", "Sign.008": "NARANJA X",
       "Sign.009": "POMELO", "Sign.020": "AEROLAB",
       "Sign.005": "AUTH0", "Sign.001": "VERCEL",
       "Sign.006": "SATELLOGIC", "Sign.007": "DESPEGAR",
       "Sign.004": "UALA", "Sign.002": "MERCADO LIBRE",
       "Sign.016": "MERCADO PAGO",
       # LOS TRES QUE VUELVEN A ENCENDERSE. 012 y 017 son billboards que se
       # apagaron porque la marca que llevaban se había mudado a otro lado del
       # cuadro, no porque el lugar estuviera mal: 012 es el mejor lugar libre
       # de la ciudad (13,7 s en cuadro) y estaba oscuro. Se les clava una
       # marca nueva y se los saca de DROP.
       "Sign.012": "GALICIA", "Sign.017": "BELO",
       # y Rebill en el 188, que llevaba a RIPIO: no es cliente, no tiene
       # vector y aparecía con el símbolo genérico. Ripio baja un lugar en el
       # reparto, no se va del cuadro.
       "Sign.015": "REBILL",
       # Sign.013 se probó para Complif y NO SIRVE, aunque el reparto lo diera
       # por libre: su dueño es el edificio de Etermax, cuyo logotipo cuelga de
       # la fachada y cuyo ícono está tumbado en el techo, los dos mudados ahí
       # por HERO. El registro de un cartel apunta al techo donde se planificó,
       # así que un edificio con dos logos encima figuraba vacío. Complif se fue
       # al spot 148, que está libre de verdad, y esto quedó anotado porque el
       # próximo que mire la tabla va a ver el mismo hueco.
       # las que sobrevivieron al descarte de repetidas, clavadas para que el
       # proximo pin no las mueva a otro techo
       "Sign.000": "GLOBANT", "Sign.003": "BASEMENT",
       "Sign.010": "TECHNISYS", "Sign.011": "ALEPH",
       # el parapeto que sobraba de basement, reusado para humand
       "Sign.052": "HUMAND", "Sign.003": "BASEMENT",
       "Sign.058": "ETERMAX"}
DROP = {"Sign.054",          # satellogic plano en el 98: queda el 3d del 163
        # el techo de RIPIO en el 179, que es el edificio de Etermax: su
        # logotipo cuelga de esa fachada y el ícono de Preguntados está tumbado
        # en ese techo. Dos marcas en una dirección, y encima Ripio quedaba
        # repetido en cámara. Apareció cuando Rebill se mudó y el reparto le
        # dio ese lugar al siguiente de la lista.
        "Sign.013",
        # la segunda copia de una marca que ya aparece en otro lado. Se
        # descarta la que la camara ve peor, y a igualdad la mas plana: un
        # cartel fuera del cuadro no compensa ser mas tridimensional.
        "Sign.053", "Sign.055", "Sign.056"}
