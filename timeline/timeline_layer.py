"""Convierte la ciudad de silicon-baires en una linea de tiempo.

silicon-baires (Aerolab) genera una Buenos Aires isometrica en Blender headless
y le reparte carteles de empresas reales por los techos y las medianeras. Su
pieza es un travelling de 24 segundos: la camara se mueve y la ciudad esta toda
ahi desde el primer fotograma.

Esto invierte las dos cosas. La camara se clava —se congela en el angulo
isometrico de su plano de apertura, recentrada para que entre la ciudad
entera— y lo que se mueve es el ano: cada cartel de empresa con ano de
fundacion citable arranca apagado y se prende en su ano. El transito y la
gente de la escena original siguen animados, asi que la ciudad esta viva
mientras el ecosistema se va llenando.

No se toca nada de la geometria de upstream: se lee su .blend, se le suma esta
capa y se guarda una copia aparte.

Uso:
    blender -b upstream/renders/city.blend \
        -P scripts/timeline_layer.py -- --repo .
"""

import hashlib
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

YEAR_START = 1995     # Technisys, la mas vieja de la tabla con ano citable
YEAR_END = 2026
FRAMES_PER_YEAR = 9   # 32 anos * 9 = 288 fotogramas = 12 s a 24 fps
# Cuanto de un ano tarda un edificio en levantarse. Bajo a proposito: a 0,7 el
# ano entero era una obra en curso y la pieza se sentia lenta.
GROW_SHARE = 0.45

TAG = "TL_"

# La camara de upstream hace un travelling: sale de un plano ancho y termina
# cerrada sobre el titulo. Se congela en el ANGULO del fotograma 1 (el mas
# abierto) y se recentra sobre la ciudad, porque el encuadre final lo ocupan
# las letras rojas de BUENOS AIRES y aca lo que hay que ver son los carteles.
FREEZE_FRAME = 1
MARGIN = 1.03         # aire alrededor de la caja de la ciudad
# 12 segundos a 24 fps. Los 32 anos entran justos a 9 fotogramas cada uno.
TOTAL_FRAMES = 288
# Topes del encuadre. Abajo, el plano de apertura de upstream (306), que es lo
# mas cerrado que se puede estar y seguir viendo varias marcas. Arriba, el
# punto donde la ciudad empieza a ser una isla en el fondo y los logos dejan
# de leerse.
# La ciudad entera mide unos 1.070 m sobre el eje horizontal de esta camara.
# Los topes se abren para que entre completa: mostrarla toda es el pedido.
ORTHO_MIN = 306.0
ORTHO_MAX = 1250.0

# Se activa con --vertical: 1080x1920 para celular. No es un recorte del
# apaisado, es otro encuadre — en 9:16 la ciudad entera no entra sin quedar
# ilegible, asi que se cierra sobre el nucleo.
VERTICAL = False
# Encuadre del recorrido vertical: cerrado para que se lean los logos en un
# telefono, y abriendo al final para mostrar la ciudad ya llena.
VERTICAL_ORTHO = 330.0
VERTICAL_ORTHO_FINAL = 620.0


def argv_after_ddash():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def repo_root():
    args = argv_after_ddash()
    if "--repo" in args:
        return os.path.abspath(args[args.index("--repo") + 1])
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def upstream_path(root, *partes):
    """Los archivos de la ciudad, este script viva donde viva.

    En el repo de la capa, upstream se clona en `upstream/`. Dentro del repo de
    silicon-baires, en cambio, la carpeta cuelga del raiz y los renders quedan
    un nivel arriba. Se prueban las dos y listo, en vez de exigir una estructura.
    """
    candidatos = (os.path.join(root, "upstream", "renders", *partes),
                  os.path.join(root, "..", "renders", *partes),
                  os.path.join(root, "renders", *partes))
    for ruta in candidatos:
        if os.path.exists(ruta):
            return ruta
    return candidatos[0]


def year_to_frame(year):
    return int(round((year - YEAR_START) * FRAMES_PER_YEAR)) + 1


def purge_previous():
    for obj in [o for o in bpy.data.objects if o.name.startswith(TAG)]:
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in [c for c in bpy.data.collections if c.name.startswith(TAG)]:
        bpy.data.collections.remove(coll)
    for mat in [m for m in bpy.data.materials if m.name.startswith(TAG)]:
        bpy.data.materials.remove(mat)
    for curve in [c for c in bpy.data.curves if c.name.startswith(TAG)]:
        bpy.data.curves.remove(curve)


def emission_material(name, rgb, strength):
    mat = bpy.data.materials.new(TAG + name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    emit.inputs["Strength"].default_value = strength
    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def solid_material(name, rgb, roughness=0.5):
    """Material opaco comun. El de emision no sirve para el suelo: brillaria."""
    mat = bpy.data.materials.new(TAG + name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
    return mat


def set_key_interpolation(kind):
    """Blender 5 saco Action.fcurves (acciones con slots y capas), asi que la
    interpolacion se fija en las preferencias ANTES de insertar en vez de
    recorrer las curvas despues."""
    bpy.context.preferences.edit.keyframe_new_interpolation_type = kind


def keyframe_visible_from(obj, frame_in):
    set_key_interpolation("CONSTANT")
    for prop in ("hide_viewport", "hide_render"):
        setattr(obj, prop, True)
        obj.keyframe_insert(prop, frame=1)
        obj.keyframe_insert(prop, frame=max(1, frame_in - 1))
        setattr(obj, prop, False)
        obj.keyframe_insert(prop, frame=frame_in)


def keyframe_visible_range(obj, frame_in, frame_out):
    set_key_interpolation("CONSTANT")
    for prop in ("hide_viewport", "hide_render"):
        setattr(obj, prop, True)
        obj.keyframe_insert(prop, frame=max(1, frame_in - 1))
        setattr(obj, prop, False)
        obj.keyframe_insert(prop, frame=frame_in)
        setattr(obj, prop, True)
        obj.keyframe_insert(prop, frame=frame_out)


# ---------------------------------------------------------------------------


def extent_in_camera_plane(cam, objects, trim=0.08):
    """Caja de esos objetos medida en el plano de la camara, no en el mundo.

    Un bounding box alineado a los ejes del mundo no dice nada sobre cuanto
    ortho_scale hace falta: lo que importa es cuanto ocupan sobre los ejes
    derecha/arriba de ESTA camara.
    """
    basis = cam.matrix_world.to_3x3()
    right, up = basis @ Vector((1, 0, 0)), basis @ Vector((0, 1, 0))
    us, vs = [], []
    for obj in objects:
        centre = obj.matrix_world.translation
        us.append(centre.dot(right))
        vs.append(centre.dot(up))

    # Percentiles y no min/max: un solo cartel perdido en una punta estiraba el
    # encuadre y dejaba media pantalla de fondo vacio. Se recorta el 8% de cada
    # extremo, asi el cuadro lo decide el grueso de las marcas.
    def band(values):
        values = sorted(values)
        if trim <= 0.0:
            return values[0], values[-1]      # la ciudad entera, sin recortar
        low = values[int(len(values) * trim)]
        high = values[min(len(values) - 1, int(len(values) * (1.0 - trim)))]
        return low, high

    u0, u1 = band(us)
    v0, v1 = band(vs)
    return right, up, u0, u1, v0, v1


cam_axes = []          # [right, up] de la camara, lo llena freeze_camera


def animate_camera_tour(cam, scene, animated, report):
    """Solo en vertical: la camara recorre la ciudad siguiendo a las empresas.

    En apaisado la camara no se mueve — esa es la pieza. En un telefono el plano
    general no funciona: la ciudad entera en 9:16 queda ilegible. Asi que en
    vertical la camara viaja, pero NO por un recorrido inventado: va a donde
    esta pasando algo. Cada parada es el centro de los edificios que se levantan
    en ese tramo de anos, y llega justo cuando empiezan a construirse.
    """
    if not cam_axes:
        return
    right, up = cam_axes

    porano = {}
    for ficha in animated:
        obj = bpy.data.objects.get(ficha["edificio"] or "")
        if obj is not None:
            porano.setdefault(ficha["year"], []).append(obj)
    if not porano:
        return

    # Agrupar en tramos: una parada por ano marearia, y hay anos con una sola
    # empresa. Se juntan anos consecutivos hasta llegar a PARADAS tramos.
    anos = sorted(porano)
    paradas = max(4, min(8, len(anos)))
    tam = max(1, len(anos) // paradas)
    tramos = [anos[i:i + tam] for i in range(0, len(anos), tam)]

    set_key_interpolation("BEZIER")
    detalle = []
    for tramo in tramos:
        objetos = [o for a in tramo for o in porano[a]]
        cx = sum(o.location.x for o in objetos) / len(objetos)
        cy = sum(o.location.y for o in objetos) / len(objetos)
        centro = Vector((cx, cy, 25.0))
        frame = year_to_frame(tramo[0]) + int(FRAMES_PER_YEAR * 0.3)

        loc = cam.location.copy()
        cam.location = (loc
                        + right * (centro.dot(right) - loc.dot(right))
                        + up * (centro.dot(up) - loc.dot(up)))
        cam.keyframe_insert("location", frame=max(1, frame))
        detalle.append({
            "frame": max(1, frame),
            "anos": [tramo[0], tramo[-1]],
            "empresas": sorted({f["brand"] for f in animated
                                if f["year"] in tramo}),
            "centro": [round(cx, 1), round(cy, 1)],
        })

    # El zoom NO se anima. El HUD del ano va parenteado a la camara y ubicado
    # en unidades del cuadro: si ortho_scale cambia, el cuadro cambia de tamano
    # pero el texto no, y el ano se va de pantalla. Se viaja, no se hace zoom.
    cam.data.ortho_scale = VERTICAL_ORTHO

    report["recorrido_camara"] = detalle
    report["camera"]["keyframes"] = len(detalle)
    report["camera"]["nota"] = (
        "Solo en vertical la camara se mueve, y va a donde se estan "
        "construyendo los edificios de cada tramo de anos. En apaisado sigue "
        "sin un solo keyframe.")


def freeze_camera(scene, report, subjects):
    """Le saca la animacion a la camara y la deja mirando la ciudad entera.

    Hay DOS animaciones que sacar: la del objeto (posicion) y la del dato de
    camara (ortho_scale, que en upstream va de 306 a 170). Borrar solo la del
    objeto deja la camara quieta pero el encuadre siguiendo haciendo zoom, que
    es justo lo que esta pieza no quiere.
    """
    cam = scene.camera
    scene.frame_set(FREEZE_FRAME)
    rotation = cam.rotation_euler.copy()
    location = cam.location.copy()

    cam.animation_data_clear()
    if cam.data.animation_data:
        cam.data.animation_data_clear()
    cam.rotation_euler = rotation
    cam.location = location

    # Encuadre sobre la ciudad ENTERA: es lo que la pieza tiene que mostrar,
    # porque lo que cuenta es como se llena. Los logos quedan chicos; el precio
    # esta aceptado.
    if VERTICAL:
        # En 9:16 se llena el ALTO con la ciudad y se dejan recortar los
        # costados. Encajarla entera dejaba media pantalla de suelo vacio
        # arriba y abajo, y la ciudad chiquita en el medio: lo peor de los dos
        # mundos en un telefono.
        objetivos, recorte = [], 0.0
        for nombre in ("BUILDINGS", "SIGNS", "LANDMARKS", "TITLE"):
            coll = bpy.data.collections.get(nombre)
            if coll:
                objetivos += [o for o in coll.all_objects if o.type == "MESH"]
        objetivos += [o for o in bpy.data.objects
                      if o.name.startswith("TL_bld_")]
    else:
        objetivos = []
        for nombre in ("BUILDINGS", "SIGNS", "LANDMARKS", "TITLE"):
            coll = bpy.data.collections.get(nombre)
            if coll:
                objetivos += [o for o in coll.all_objects if o.type == "MESH"]
        objetivos += [o for o in bpy.data.objects
                      if o.name.startswith("TL_bld_")]
        recorte = 0.0
    right, up, u0, u1, v0, v1 = extent_in_camera_plane(
        cam, objetivos or subjects, trim=recorte)
    width, height = u1 - u0, v1 - v0
    aspect = scene.render.resolution_x / scene.render.resolution_y
    # ortho_scale es la dimension MAYOR del encuadre, asi que hay que cubrir
    # tanto el ancho como la altura convertida a ancho equivalente.
    # ortho_scale cubre SIEMPRE el lado mayor del render. En apaisado ese lado
    # es el ancho; en vertical es el alto. Usar la formula del apaisado en un
    # 9:16 deja la ciudad cortada por los costados.
    if scene.render.resolution_x >= scene.render.resolution_y:
        fitted = max(width, height * aspect)
    else:
        # Vertical: se ajusta SOLO al alto. Meter tambien el ancho
        # (width / aspect) alejaba la camara hasta 938 y dejaba la ciudad
        # nadando en suelo vacio.
        fitted = height
    fitted *= MARGIN
    cam.data.ortho_scale = max(ORTHO_MIN, min(ORTHO_MAX, fitted))

    # Recentrar: correr la camara sobre su propio plano hasta que el centro de
    # la ciudad caiga en el centro del cuadro.
    target_u, target_v = (u0 + u1) * 0.5, (v0 + v1) * 0.5
    cam.location = (location
                    + right * (target_u - location.dot(right))
                    + up * (target_v - location.dot(up)))

    cam_axes[:] = [right, up]
    report["camera"] = {
        "congelada_en_frame": FREEZE_FRAME,
        "location": [round(v, 1) for v in cam.location],
        "rotation_deg": [round(math.degrees(v), 2) for v in cam.rotation_euler],
        "ortho_scale": round(cam.data.ortho_scale, 1),
        "ciudad_ancho_m": round(width, 1),
        "ciudad_alto_m": round(height, 1),
        "keyframes": 0,
        "nota": "Se limpio la animacion del objeto Y la del dato de camara "
                "(upstream anima ortho_scale de 306 a 170).",
    }
    return cam


def hitos_de(info):
    """`hito` puede venir como texto o como lista. Devuelve siempre lista."""
    hito = info.get("hito")
    if not hito:
        return []
    return [hito] if isinstance(hito, str) else list(hito)


def hito_year(text):
    head = text.split(":", 1)[0].strip()
    return int(head) if head.isdigit() else None


# Que fraccion de su altura tiene el edificio el dia que la empresa se funda.
# El resto lo gana creciendo.
SEED_HEIGHT = 0.30
# Si la empresa no tiene hitos con fecha, tarda esto en llegar a su altura.
DEFAULT_GROWTH_YEARS = 7


def parent_inverse_of(part):
    """La inversa del padre, calculada y no leida de matrix_world.

    ESTE ERA EL BUG DE LOS LOGOS TIRADOS EN CUALQUIER LADO. Blender no
    recalcula `matrix_world` cuando uno le asigna `location` por Python: espera
    a que corra el depsgraph. Al emparentar en la misma pasada en que se crea el
    edificio, `part.matrix_world` todavia devolvia la identidad, la inversa daba
    identidad, y el cartel quedaba corrido por las coordenadas del sitio — un
    logo aparecia tirado en el pasto a cien metros de su edificio.

    El edificio se crea con rotacion cero y escala uno, y su `location` es el
    punto del sitio, asi que su matriz en reposo es una traslacion pura. La
    inversa se arma de ahi y no depende de que el depsgraph haya corrido.
    """
    return Matrix.Translation(part.location).inverted()


def reveal_delay(grow):
    """El cartel aparece cuando la obra termino, no mientras sube.

    Va colgado del edificio, asi que mientras la escala sube desde 0,001 el
    cartel viene aplastado contra el piso. Probamos revelarlo al 40% de la obra
    y no alcanzo: con la curva de aceleracion el edificio sigue bajo y el
    barrido seguia encontrando 34 carteles tirados en el pasto, ahora durante
    dos a cuatro fotogramas cada uno.

    Esperar a que termine no le saca nada a la pieza: el edificio igual se
    construye a la vista, y el cartel se prende cuando hay donde apoyarlo.
    """
    return grow + 1


def growth_steps(founded, info):
    """Los escalones de altura del edificio, de la fundacion a su tamano final.

    El edificio NO aparece entero: nace chico y va subiendo. Los escalones caen
    en los hitos con fecha de la empresa (salidas a bolsa, rondas, compras),
    que es lo unico documentado que tenemos para las veintidos por igual. NO es
    una curva de valuacion: no hay valuaciones comparables para todas, y
    fabricar uma seria inventar el dato.

    Sin hitos, el edificio crece parejo durante DEFAULT_GROWTH_YEARS.
    """
    years = sorted({y for y in (hito_year(h) for h in hitos_de(info))
                    if y and y > founded})
    if not years:
        years = [founded + DEFAULT_GROWTH_YEARS]
    span = 1.0 - SEED_HEIGHT
    steps = [(founded, SEED_HEIGHT)]
    for index, year in enumerate(years, start=1):
        steps.append((year, SEED_HEIGHT + span * index / len(years)))
    return steps


def site_index(root):
    """Los 126 sitios de upstream, indexados por su coordenada.

    city_buildings.json trae, por cada edificio, su punto 'at', su altura 'top'
    y los rectangulos 'wings' que lo componen. El campo 'owner' de cada cartel
    es exactamente ese 'at', asi que la marca se puede atar a su edificio sin
    adivinar nada.
    """
    with open(upstream_path(root, "city_buildings.json"),
              encoding="utf-8") as fh:
        return json.load(fh)["sites"]


def site_for_owner(sites, owner):
    """Encuentra el sitio al que pertenece el 'owner' de un cartel.

    NO se puede matchear por igualdad: el 'owner' del cartel viene redondeado
    (-26.0, -167.0) y el 'at' del sitio cae en la grilla con decimales
    (-351.75, -327.75). Se busca el sitio cuyo rectangulo contiene el punto, y
    si ninguno lo contiene, el mas cercano dentro de un radio corto.
    """
    ox, oy = owner
    best, best_d = None, 1e18
    for site in sites:
        for wx, wy, ww, wd in site["wings"]:
            if (abs(ox - wx) <= ww * 0.5 + 1.0
                    and abs(oy - wy) <= wd * 0.5 + 1.0):
                return site
        dx, dy = ox - site["at"][0], oy - site["at"][1]
        d = dx * dx + dy * dy
        if d < best_d:
            best, best_d = site, d
    return best if best_d <= 30.0 ** 2 else None


def site_rects(site):
    return [(w[0] - w[2] * 0.5 - 0.6, w[0] + w[2] * 0.5 + 0.6,
             w[1] - w[3] * 0.5 - 0.6, w[1] + w[3] * 0.5 + 0.6)
            for w in site["wings"]]


def split_buildings(city, targets, collection):
    """Separa del mesh unico de la ciudad los edificios que hay que animar.

    upstream une TODA la ciudad en un solo objeto llamado 'buildings', asi que
    no hay nada que escalar por edificio. Se hace con bmesh y NO con
    bpy.ops.mesh.separate: en background el operador depende del contexto y del
    objeto activo, y en una tanda de veintipico separaciones deja de encontrar
    geometria despues de la primera.

    Cada parte nace con su origen en el piso del sitio. Si el origen queda en
    el centro del volumen, escalar en Z hunde media torre bajo tierra en vez de
    hacerla crecer desde el suelo.

    `targets` es [(clave, site)]. Devuelve {clave: objeto}.
    """
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(city.data)
    bm.faces.ensure_lookup_table()

    boxes = [(key, site, site_rects(site), float(site["top"]) + 2.0)
             for key, site in targets]
    claimed = {}
    for face in bm.faces:
        center = face.calc_center_median()
        for key, site, rects, top in boxes:
            if center.z > top:
                continue
            if any(x0 <= center.x <= x1 and y0 <= center.y <= y1
                   for x0, x1, y0, y1 in rects):
                claimed.setdefault(key, []).append(face)
                break

    made = {}
    materials = list(city.data.materials)
    for key, site in targets:
        faces = claimed.get(key)
        if not faces or len(faces) < 4:
            continue
        base = Vector((site["at"][0], site["at"][1], 0.0))
        part_bm = bmesh.new()
        vmap = {}
        for face in faces:
            verts = []
            for vert in face.verts:
                if vert not in vmap:
                    vmap[vert] = part_bm.verts.new(vert.co - base)
                verts.append(vmap[vert])
            try:
                new_face = part_bm.faces.new(verts)
            except ValueError:
                continue          # cara duplicada: la geometria unida las tiene
            new_face.material_index = face.material_index
            new_face.smooth = face.smooth
        mesh = bpy.data.meshes.new(TAG + "bld_" + key)
        part_bm.to_mesh(mesh)
        part_bm.free()
        for material in materials:
            mesh.materials.append(material)
        obj = bpy.data.objects.new(TAG + "bld_" + key, mesh)
        obj.location = base
        collection.objects.link(obj)
        made[key] = obj

    bmesh.ops.delete(
        bm, geom=[f for group in claimed.values() for f in group],
        context="FACES")
    bm.to_mesh(city.data)
    bm.free()
    city.data.update()
    return made


def deterministic_unit(*parts):
    """Un numero estable en [0,1) a partir de coordenadas.

    Estable entre corridas: la ciudad tiene que completarse siempre en el mismo
    orden, si no cada render cuenta una historia distinta.
    """
    seed = "|".join("%.2f" % p if isinstance(p, float) else str(p)
                    for p in parts)
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / float(0xFFFFFFFF)


def fabric_year(at):
    """En que ano aparece un edificio que NO es de ninguna empresa.

    Esto es una decision de puesta en escena, no un dato: la ciudad arranca
    casi vacia y se completa a lo largo del periodo. El exponente sesga el
    reparto hacia los anos tardios, asi que al principio hay pocos edificios y
    el barrio se llena a medida que avanza. Las empresas, en cambio, aparecen
    en su ano documentado.
    """
    unit = deterministic_unit(at[0], at[1])
    return YEAR_START + int((YEAR_END - YEAR_START) * (unit ** 0.62))


def animate_city_fabric(city, sites, claimed_at, collection, report):
    """Levanta TODO el resto de la ciudad a lo largo del periodo."""
    rest = [(("fabric_%d" % index), site)
            for index, site in enumerate(sites)
            if (round(site["at"][0], 2), round(site["at"][1], 2))
            not in claimed_at]
    parts = split_buildings(city, rest, collection)
    grow = int(FRAMES_PER_YEAR * 0.6)
    for key, site in rest:
        part = parts.get(key)
        if part is None:
            continue
        frame_in = year_to_frame(fabric_year(site["at"]))
        set_key_interpolation("BEZIER")
        part.scale = (1.0, 1.0, 0.001)
        part.keyframe_insert("scale", index=2, frame=1)
        part.keyframe_insert("scale", index=2, frame=frame_in)
        part.scale = (1.0, 1.0, 1.0)
        part.keyframe_insert("scale", index=2, frame=frame_in + grow)
    report["tejido_animado"] = len(parts)
    report["tejido_nota"] = (
        "Puesta en escena, no dato: los edificios que no son de ninguna "
        "empresa se reparten a lo largo del periodo con un sesgo hacia los "
        "anos tardios, para que la ciudad arranque casi vacia. El reparto es "
        "determinista, asi que siempre se construye en el mismo orden.")


def thin_early_life(collection_name, keep_at_start, report_key, report):
    """Menos autos y menos gente al principio, mas a medida que avanza.

    Tambien es puesta en escena. Cada objeto recibe un ano deterministico a
    partir de su nombre; antes de ese ano no esta.
    """
    coll = bpy.data.collections.get(collection_name)
    if coll is None:
        return
    objects = [o for o in coll.all_objects if o.type == "MESH"]
    hidden = 0
    for obj in objects:
        unit = deterministic_unit(obj.name)
        if unit < keep_at_start:
            continue                       # estos estan desde el principio
        share = (unit - keep_at_start) / max(1e-6, 1.0 - keep_at_start)
        year = YEAR_START + int((YEAR_END - YEAR_START) * (share ** 0.75))
        keyframe_visible_from(obj, year_to_frame(year))
        hidden += 1
    report[report_key] = {"total": len(objects), "escalonados": hidden,
                          "presentes_desde_1995": len(objects) - hidden}


def build_title_progressively(collection_name, report):
    """Las letras de BUENOS AIRES se van armando de a una."""
    coll = bpy.data.collections.get(collection_name)
    if coll is None:
        return
    letters = sorted((o for o in coll.all_objects if o.type == "MESH"),
                     key=lambda o: o.name)
    if not letters:
        return
    span = YEAR_END - YEAR_START
    for index, obj in enumerate(letters):
        year = YEAR_START + int(span * (index + 1) / (len(letters) + 1))
        keyframe_visible_from(obj, year_to_frame(year))
    report["titulo_letras"] = len(letters)


def animate_landmarks(root, collection, by_year, report):
    """Separa piezas del objeto 'landmarks' y les pone su año.

    upstream funde el Obelisco, la Floralis, el estadio y varios props en un
    solo objeto. Se separa por radio alrededor de un punto medido con raycast,
    con la misma tecnica de bmesh que los edificios.
    """
    import bmesh

    path = os.path.join(root, "data", "landmarks.json")
    landmarks = bpy.data.objects.get("landmarks")
    if not os.path.exists(path) or landmarks is None:
        return
    with open(path, encoding="utf-8") as fh:
        piezas = json.load(fh)["piezas"]

    bm = bmesh.new()
    bm.from_mesh(landmarks.data)
    bm.faces.ensure_lookup_table()

    claimed = {}
    for face in bm.faces:
        center = face.calc_center_median()
        for pieza in piezas:
            at = pieza["at"]
            if math.hypot(center.x - at[0], center.y - at[1]) <= pieza["radius"]:
                claimed.setdefault(pieza["id"], []).append(face)
                break

    grow = int(FRAMES_PER_YEAR * GROW_SHARE)
    hechas = []
    materials = list(landmarks.data.materials)
    for pieza in piezas:
        faces = claimed.get(pieza["id"])
        if not faces or len(faces) < 4:
            report["warnings"].append(
                "sin geometria para el landmark %s en (%s)"
                % (pieza["name"], pieza["at"]))
            continue

        base = Vector((pieza["at"][0], pieza["at"][1], 0.0))
        part_bm = bmesh.new()
        vmap = {}
        for face in faces:
            verts = []
            for vert in face.verts:
                if vert not in vmap:
                    vmap[vert] = part_bm.verts.new(vert.co - base)
                verts.append(vmap[vert])
            try:
                new_face = part_bm.faces.new(verts)
            except ValueError:
                continue
            new_face.material_index = face.material_index
            new_face.smooth = face.smooth
        mesh = bpy.data.meshes.new(TAG + "lm_" + pieza["id"])
        part_bm.to_mesh(mesh)
        part_bm.free()
        for material in materials:
            mesh.materials.append(material)
        part = bpy.data.objects.new(TAG + "lm_" + pieza["id"], mesh)
        part.location = base
        collection.objects.link(part)

        set_key_interpolation("BEZIER")
        appears = pieza.get("appears")
        obras = pieza.get("obras") or []
        if appears:
            # Se construye en su ano, como cualquier edificio.
            frame_in = year_to_frame(int(appears))
            part.scale = (1.0, 1.0, 0.001)
            part.keyframe_insert("scale", index=2, frame=1)
            part.keyframe_insert("scale", index=2, frame=frame_in)
            part.scale = (1.0, 1.0, 1.0)
            part.keyframe_insert("scale", index=2, frame=frame_in + grow)
            by_year.setdefault(int(appears), set()).add(pieza["name"])
        elif obras:
            # Ya estaba: lo que se anima son las obras. Cada una lo agranda un
            # escalon, que es lo que las obras hicieron con la capacidad.
            part.scale = (1.0, 1.0, 1.0)
            part.keyframe_insert("scale", index=2, frame=1)
            for index, obra in enumerate(obras, start=1):
                frame = year_to_frame(int(obra["year"]))
                part.keyframe_insert("scale", index=2, frame=frame)
                part.scale = (1.0, 1.0, 1.0 + 0.16 * index)
                part.keyframe_insert("scale", index=2, frame=frame + grow)

        hechas.append({
            "pieza": pieza["name"],
            "appears": appears,
            "obras": [o["year"] for o in obras],
            "caras": len(faces),
        })

    bmesh.ops.delete(
        bm, geom=[f for group in claimed.values() for f in group],
        context="FACES")
    bm.to_mesh(landmarks.data)
    bm.free()
    landmarks.data.update()
    report["landmarks"] = hechas


def plan_closed(root, sites, targets, report):
    """Le busca terreno a las empresas que cerraron.

    Ninguna tiene cartel en la ciudad de upstream, asi que se les asigna un
    sitio libre —de los que ningun cartel con ano reclamo— cerca del centro del
    cuadro y con altura suficiente para que se note cuando se cae.
    """
    path = os.path.join(root, "data", "cerraron.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        empresas = json.load(fh)["empresas"]

    taken = {key for key, _ in targets}
    taken_at = {(round(s["at"][0], 2), round(s["at"][1], 2))
                for _, s in targets}
    # El centro del cuadro es el de los sitios que ya reclamaron los carteles
    # con ano: es sobre esa caja que despues se calcula el encuadre.
    if targets:
        focus = Vector((sum(s["at"][0] for _, s in targets) / len(targets),
                        sum(s["at"][1] for _, s in targets) / len(targets)))
    else:
        focus = Vector((0.0, 0.0))
    free = [s for s in sites
            if (round(s["at"][0], 2), round(s["at"][1], 2)) not in taken_at
            and float(s["top"]) >= 18.0]
    free.sort(key=lambda s: (Vector((s["at"][0], s["at"][1])) - focus).length)

    planned = []
    for empresa in empresas:
        if not free:
            report["warnings"].append(
                "sin terreno libre para %s" % empresa["name"])
            continue
        site = free.pop(0)
        key = "cerro_" + empresa["id"]
        if key in taken:
            continue
        targets.append((key, site))
        planned.append((empresa, site, key))
    return planned


def animate_closed(planned, parts, collection, by_year, end_by_year, report):
    """Sube el edificio en el ano de fundacion y lo baja el ano que cerro."""
    grow = int(FRAMES_PER_YEAR * GROW_SHARE)
    hechas = []
    for empresa, site, key in planned:
        part = parts.get(key)
        founded, closed = int(empresa["founded"]), int(empresa["closed"])
        frame_in, frame_out = year_to_frame(founded), year_to_frame(closed)

        if part is not None:
            set_key_interpolation("BEZIER")
            part.scale = (1.0, 1.0, 0.001)
            part.keyframe_insert("scale", index=2, frame=1)
            part.keyframe_insert("scale", index=2, frame=frame_in)
            part.scale = (1.0, 1.0, 1.0)
            part.keyframe_insert("scale", index=2, frame=frame_in + grow)
            part.keyframe_insert("scale", index=2, frame=frame_out)
            part.scale = (1.0, 1.0, 0.001)
            part.keyframe_insert("scale", index=2, frame=frame_out + grow)

        # Cartel propio: la ciudad de upstream no trae uno para estas.
        at = (site["at"][0], site["at"][1])
        curve = bpy.data.curves.new(TAG + "cerro_" + empresa["id"], type="FONT")
        curve.body = empresa["name"]
        curve.size = max(7.0, min(13.0, float(site["top"]) * 0.35))
        curve.align_x = "CENTER"
        curve.align_y = "BOTTOM"
        curve.extrude = 0.4
        sign = bpy.data.objects.new(TAG + "cerro_" + empresa["id"], curve)
        # La altura sale del edificio QUE QUEDO, no del 'top' declarado del
        # sitio: si en ese lote la geometria es mas baja, el cartel queda
        # flotando en el aire sobre un terreno vacio.
        # Se mide sobre los vertices del mesh y no sobre matrix_world: para
        # cuando llega aca el objeto ya tiene la escala animada en 0.001 del
        # primer keyframe, y el bounding box del mundo daria una altura
        # aplastada.
        if part is not None and part.data.vertices:
            sign_z = (part.location.z
                      + max(v.co.z for v in part.data.vertices) + 0.3)
        else:
            sign_z = float(site["top"]) + 0.3
        sign.location = (at[0], at[1], sign_z)
        # Encarar la camara es copiarle la rotacion: es ortografica, asi que
        # todos los rayos son paralelos y una sola rotacion sirve para todos
        # los carteles, esten donde esten.
        sign.rotation_euler = bpy.context.scene.camera.rotation_euler
        sign.data.materials.append(emission_material(
            "cerro_%s" % empresa["id"], (1.0, 0.30, 0.22), 4.0))
        collection.objects.link(sign)
        # Se cuelga del edificio, igual que los carteles de las empresas.
        # Keyframear su altura en paralelo lo dejaba flotando sobre un terreno
        # vacio mientras la obra subia.
        # Este cartel lo creamos nosotros y su origen esta en el techo, asi que
        # emparentarlo es seguro: no hay cadena previa que romper.
        if part is not None:
            sign.parent = part
            sign.matrix_parent_inverse = parent_inverse_of(part)
        keyframe_visible_range(
            sign, frame_in + (reveal_delay(grow) if part else 0), frame_out)

        by_year.setdefault(founded, set()).add(empresa["name"])
        end_by_year.setdefault(closed, set()).add(empresa["name"])
        hechas.append({
            "empresa": empresa["name"],
            "founded": founded,
            "closed": closed,
            "como_termino": empresa["como_termino"],
            "edificio": part.name if part else None,
            "sitio": [round(v, 2) for v in site["at"]],
        })
    report["cerraron"] = hechas


def animate_signs(root, scene, report, collection):
    """Cada empresa levanta su edificio en su ano y lo baja cuando deja de ser
    independiente. El cartel se prende cuando el edificio termino de crecer."""
    with open(os.path.join(root, "data", "brand_years.json"),
              encoding="utf-8") as fh:
        table = json.load(fh)["years"]
    with open(upstream_path(root, "city_signs.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    sites = site_index(root)
    city = bpy.data.objects.get("buildings")

    grow = int(FRAMES_PER_YEAR * GROW_SHARE)
    by_year, end_by_year = {}, {}
    animated, missing_objects, sin_ano, objects = [], [], set(), []
    built = 0
    huerfanos = 0

    # Primera pasada: que carteles tienen ano y a que sitio pertenecen.
    plan, targets = [], []
    for entry in manifest:
        obj = bpy.data.objects.get(entry["name"])
        brand = entry["text"]
        if obj is None:
            missing_objects.append(entry["name"])
            continue
        info = table.get(brand)
        if info is None:
            # Sin ano citable la marca no tiene fecha propia, pero el cartel NO
            # puede estar desde el primer fotograma: su edificio es del tejido y
            # se construye en un ano posterior, asi que el logo quedaba tirado
            # en un lote vacio hasta que le llegaba el edificio. Es exactamente
            # el "logo en el pasto" que se veia. Se revela cuando su edificio
            # esta terminado.
            sin_ano.add(brand)
            site = site_for_owner(sites, entry["owner"])
            # Si no matchea ningun sitio igual se le da un ano: es preferible a
            # dejarlo prendido desde 1995 sobre un lote pelado. fabric_year es
            # deterministico sobre cualquier coordenada.
            anchor_xy = site["at"] if site else entry["owner"]
            keyframe_visible_from(
                obj,
                year_to_frame(fabric_year(anchor_xy))
                + int(FRAMES_PER_YEAR * 0.6) + 1)
            huerfanos += 1
            continue
        key = "%s_%s" % (brand.replace(" ", "_").lower(),
                         entry["name"].split(".")[-1])
        site = site_for_owner(sites, entry["owner"])
        plan.append((entry, obj, info, key, site))
        if site is not None:
            targets.append((key, site))

    # Las que cerraron no tienen cartel en la ciudad de upstream: se les da un
    # terreno libre. Van en la MISMA tanda de bmesh, porque separar el mesh dos
    # veces sobre el mismo objeto duplicaria caras ya sacadas.
    closed = plan_closed(root, sites, targets, report)

    # Segunda pasada: una sola de bmesh para separarlos a todos.
    parts = split_buildings(city, targets, collection) if (
        city is not None and targets) else {}

    for entry, obj, info, key, site in plan:
        brand = entry["text"]
        year = int(info["year"])
        frame_in = year_to_frame(year)
        end_year = info.get("end_year")
        frame_end = year_to_frame(int(end_year)) if end_year else None
        part = parts.get(key)

        if part is not None:
            built += 1
            steps = growth_steps(year, info)
            # El cartel se cuelga del edificio y hereda su escala.
            #
            # Antes de esto probamos keyframear la altura del cartel EN PARALELO
            # a la del edificio: primero con obj.location.z * escala, despues
            # con el desplazamiento del punto de apoyo tomado del campo `z` del
            # manifiesto. Ninguna de las dos prendio. Medido sobre el depsgraph
            # evaluado, 29 de 30 carteles no se movian un centimetro entre el
            # primer fotograma y el ultimo.
            #
            # Emparentar no depende de que dos animaciones separadas coincidan:
            # hay una sola, la del edificio, y el cartel va colgado. El precio
            # es que el cartel se achata mientras la obra sube; en reposo no se
            # deforma, porque la escala vuelve a 1, y un cartel achatado sobre
            # un edificio a medio construir es exactamente lo que uno espera
            # ver.
            # NO se toca el padre del cartel. Los carteles de upstream ya vienen
            # emparentados, y su ubicacion en el mundo sale de esa cadena:
            # reasignarles el padre al edificio los descoloca. Medido, 29 de 39
            # terminaban corridos, el peor a 445 m de su edificio — un logo
            # tirado en el pasto a dos cuadras.
            #
            # Tampoco hace falta que lo siga: el cartel se revela cuando la obra
            # ya termino, asi que el edificio esta a su altura final y el cartel
            # calza donde upstream lo puso.

            set_key_interpolation("BEZIER")
            part.scale = (1.0, 1.0, 0.001)
            part.keyframe_insert("scale", index=2, frame=1)
            part.keyframe_insert("scale", index=2, frame=frame_in)
            for step_year, height in steps:
                part.scale = (1.0, 1.0, height)
                part.keyframe_insert(
                    "scale", index=2, frame=year_to_frame(step_year) + grow)
            if frame_end:
                part.keyframe_insert("scale", index=2, frame=frame_end)
                part.scale = (1.0, 1.0, 0.001)
                part.keyframe_insert("scale", index=2, frame=frame_end + grow)

        # El cartel entra con la obra ya arrancada, no en el fotograma exacto de
        # la fundacion. En ese fotograma el edificio todavia esta en escala
        # 0,001 y el cartel, que va colgado, aparece aplastado contra el piso.
        # En el video dura 1/24 de segundo, pero arrastrando la barra de tiempo
        # se cae justo ahi y se ve el logo tirado en el pasto.
        keyframe_visible_from(obj, frame_in + (reveal_delay(grow) if part else 0))
        if frame_end:
            set_key_interpolation("CONSTANT")
            for prop in ("hide_viewport", "hide_render"):
                setattr(obj, prop, True)
                obj.keyframe_insert(prop, frame=frame_end)

        by_year.setdefault(year, set()).add(brand)
        if end_year:
            end_by_year.setdefault(int(end_year), set()).add(brand)
        objects.append(obj)
        animated.append({
            "sign": entry["name"],
            "brand": brand,
            "year": year,
            "frame_in": frame_in,
            "end_year": end_year,
            "end_reason": info.get("end_reason"),
            "edificio": part.name if part else None,
            "sitio": [round(v, 2) for v in site["at"]] if site else None,
            "confidence": info.get("confidence"),
        })

    animate_closed(closed, parts, collection, by_year, end_by_year, report)

    # Y ahora el resto de la ciudad: arranca casi vacia y se completa.
    claimed_at = {(round(s["at"][0], 2), round(s["at"][1], 2))
                  for _, s in targets}
    if city is not None:
        animate_city_fabric(city, sites, claimed_at, collection, report)
    animate_landmarks(root, collection, by_year, report)
    thin_early_life("TRAFFIC", 0.12, "transito", report)
    thin_early_life("PEOPLE", 0.10, "gente", report)
    build_title_progressively("TITLE", report)

    report["signs_animated"] = animated
    report["edificios_animados"] = built
    report["signs_sin_ano"] = sorted(sin_ano)
    report["signs_sin_ano_atados_a_su_edificio"] = huerfanos
    report["objetos_del_manifiesto_ausentes"] = missing_objects
    if missing_objects:
        report["warnings"].append(
            "%d entradas del manifiesto no tienen objeto en el .blend"
            % len(missing_objects))
    if built < len(animated):
        report["warnings"].append(
            "%d carteles quedaron sin edificio propio: su 'owner' no matchea "
            "ningun sitio de city_buildings.json (son anclajes de fachada). El "
            "cartel se anima igual, el edificio no."
            % (len(animated) - built))
    return by_year, end_by_year, table, objects


def extend_ground(cam, scene, collection, report):
    """Alarga el suelo mas alla de la ciudad.

    upstream construye la ciudad sobre una placa del tamano justo, porque su
    camara nunca se aleja tanto. Con el encuadre abierto a la ciudad entera esa
    placa termina antes que el cuadro y la ciudad queda como una isla flotando
    en el fondo oscuro.

    El material NO se inventa: se toma el del objeto mas grande de SITE, que es
    la calzada que ya esta puesta, asi que el suelo nuevo empalma con el viejo
    en vez de parchear con un gris a ojo.
    """
    site = bpy.data.collections.get("SITE")
    fuente = None
    if site:
        mallas = [o for o in site.all_objects
                  if o.type == "MESH" and o.data.materials]
        if mallas:
            fuente = max(mallas, key=lambda o: o.dimensions.x * o.dimensions.y)

    # El suelo de fondo va MAS OSCURO que la calzada de la ciudad. Copiando el
    # material tal cual, el fondo quedaba del mismo tono que las calles y la
    # trama vial se perdia: la ciudad se leia como una mancha. Se toma el color
    # de la calzada real y se lo baja, asi el fondo sigue siendo pavimento pero
    # las calles vuelven a recortarse contra el.
    base_rgb, z = (0.055, 0.05, 0.048), 0.0
    origen = "creado (SITE sin mallas)"
    if fuente is not None:
        origen = fuente.name
        z = min((fuente.matrix_world @ Vector(c)).z for c in fuente.bound_box)
        # El slot puede estar vacio o el material no usar nodos: la calzada de
        # upstream es geometria generada y no hay garantia de ninguna de las dos.
        calzada = fuente.data.materials[0] if fuente.data.materials else None
        bsdf = None
        if calzada is not None and calzada.use_nodes:
            bsdf = calzada.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None and "Base Color" in bsdf.inputs:
            r, g, b, _ = bsdf.inputs["Base Color"].default_value
            base_rgb = (r * 0.45, g * 0.45, b * 0.45)
    material = solid_material("asfalto_fondo", base_rgb, roughness=0.92)

    # En vertical la camara recorre la ciudad, asi que el suelo tiene que
    # cubrir todo el trayecto y no solo el cuadro de una parada.
    lado = max(cam.data.ortho_scale * 2.2, 2600.0 if VERTICAL else 0.0)
    bpy.ops.mesh.primitive_plane_add(size=lado, location=(0.0, 0.0, z - 0.05))
    plano = bpy.context.active_object
    plano.name = TAG + "suelo"
    plano.data.name = TAG + "suelo"
    plano.data.materials.append(material)
    for coll in list(plano.users_collection):
        coll.objects.unlink(plano)
    collection.objects.link(plano)

    report["suelo_extendido"] = {
        "lado_m": round(lado, 1),
        "z": round(z - 0.05, 3),
        "material": material.name,
        "color_derivado_de": origen,
        "factor_oscurecido": 0.45,
    }
    return plano


def build_hud(cam, scene, by_year, end_by_year, table, collection, report):
    """Ano y titulares, pegados a la camara. Como la camara es fija, quedan
    clavados en el cuadro."""
    # Igual que el encuadre: ortho_scale es el lado mayor del render.
    res_x, res_y = scene.render.resolution_x, scene.render.resolution_y
    if res_x >= res_y:
        half_w = cam.data.ortho_scale * 0.5
        half_h = half_w * res_y / res_x
    else:
        half_h = cam.data.ortho_scale * 0.5
        half_w = half_h * res_x / res_y
    # Justo delante del plano de recorte, no a mitad de la ciudad: a 600 el
    # texto quedaba DENTRO del casco urbano y las torres lo tapaban.
    cam.data.clip_start = min(cam.data.clip_start, 0.5)
    depth = -8.0

    year_mat = emission_material("hud_year", (1.0, 0.97, 0.92), 3.4)
    # Fuerte a proposito: las lineas cruzan techos claros y un rojo apagado
    # sobre hormigon blanco no se lee.
    line_mat = emission_material("hud_line", (1.0, 0.42, 0.26), 7.0)
    fixed_mat = emission_material("hud_fixed", (0.92, 0.93, 0.95), 2.0)

    def text(name, body, x, y, size, mat, align="LEFT"):
        curve = bpy.data.curves.new(TAG + name, type="FONT")
        curve.body = body
        curve.size = size
        curve.align_x = align
        curve.align_y = "CENTER"
        obj = bpy.data.objects.new(TAG + name, curve)
        obj.location = (x, y, depth)
        obj.data.materials.append(mat)
        collection.objects.link(obj)
        obj.parent = cam
        return obj

    # Los hitos van en SU ano, no en el de fundacion. El hito de Ualá habla de
    # 2026 y aparecia debajo de un cartel que decia 2017.
    hitos = {}
    for brand, info in table.items():
        for hito in hitos_de(info):
            year = hito_year(hito)
            if year is None:
                continue
            hitos.setdefault(year, []).append(
                "%s  -  %s" % (brand, hito.split(":", 1)[1].strip()))

    for year in range(YEAR_START, YEAR_END + 1):
        frame_in = year_to_frame(year)
        # El ultimo ano se estira hasta el final: la pieza dura mas que el
        # ultimo ano y si no el contador se apaga y quedan segundos sin fecha.
        frame_out = (scene.frame_end + 1 if year == YEAR_END
                     else frame_in + FRAMES_PER_YEAR)
        year_obj = text("hud_year_%d" % year, str(year),
                        -half_w * 0.90, half_h * 0.78, half_h * 0.20, year_mat)
        keyframe_visible_range(year_obj, frame_in, frame_out)

    # Sin lineas de titulares debajo del ano y sin encabezado. Con la ciudad
    # entera en cuadro el texto queda chico y sucio, y compite con lo unico que
    # esta pieza tiene para mirar, que es como se construye. El ano solo alcanza
    # para leer el paso del tiempo; los datos y sus fuentes viven en data/ y en
    # el README, que es donde se pueden verificar.
    report["hud"] = {"anos": YEAR_END - YEAR_START + 1,
                     "titulares": len(by_year)}


def main():
    global VERTICAL
    root = repo_root()
    VERTICAL = "--vertical" in argv_after_ddash()
    scene = bpy.context.scene
    if VERTICAL:
        scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
        # Sin motion blur. Con la camara quieta el desenfoque solo tocaba a los
        # autos y quedaba bien; moviendo la camara desenfoca la ciudad entera y
        # el plano queda inmirable.
        scene.render.use_motion_blur = False
    purge_previous()

    report = {
        "upstream": "https://github.com/Aerolab/silicon-baires",
        "upstream_commit": "963da3133d7cfd7cc30239cb57dca2696067d242",
        "year_start": YEAR_START,
        "year_end": YEAR_END,
        "frames_per_year": FRAMES_PER_YEAR,
        "fps": scene.render.fps,
        "warnings": [],
    }

    scene.frame_start = 1
    scene.frame_end = max(TOTAL_FRAMES,
                          year_to_frame(YEAR_END) + FRAMES_PER_YEAR - 1)
    report["frame_end"] = scene.frame_end
    if scene.frame_end > 624:
        report["warnings"].append(
            "la linea de tiempo (%d) pasa los 624 fotogramas que tiene animado "
            "el transito de upstream" % scene.frame_end)

    # Los carteles primero: el encuadre se decide a partir de donde caen los
    # que tienen ano, asi que hay que saber cuales son antes de tocar la camara.
    bld_coll = bpy.data.collections.new(TAG + "BUILDINGS")
    scene.collection.children.link(bld_coll)
    by_year, end_by_year, table, sign_objects = animate_signs(
        root, scene, report, bld_coll)
    if not sign_objects:
        raise SystemExit("ningun cartel del manifiesto tiene ano en "
                         "data/brand_years.json: no hay linea de tiempo")
    cam = freeze_camera(scene, report, sign_objects)

    hud_coll = bpy.data.collections.new(TAG + "HUD")
    scene.collection.children.link(hud_coll)
    # Las obras de los landmarks entran al HUD por la misma puerta que los
    # hitos de las empresas, que ya sabe leer "ANO: texto".
    lm_path = os.path.join(root, "data", "landmarks.json")
    if os.path.exists(lm_path):
        with open(lm_path, encoding="utf-8") as fh:
            for pieza in json.load(fh)["piezas"]:
                obras = pieza.get("obras") or []
                if obras:
                    table[pieza["name"]] = {
                        "hito": ["%d: %s" % (int(o["year"]), o["texto"])
                                 for o in obras]}

    if VERTICAL:
        animate_camera_tour(cam, scene, report["signs_animated"], report)
    extend_ground(cam, scene, bld_coll, report)
    build_hud(cam, scene, by_year, end_by_year, table, hud_coll, report)

    out_dir = os.path.join(root, "scene_city")
    os.makedirs(out_dir, exist_ok=True)
    nombre = "city_timeline_vertical.blend" if VERTICAL else "city_timeline.blend"
    report["orientacion"] = "vertical 1080x1920" if VERTICAL else "apaisado 1920x1080"
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, nombre))
    informe = ("timeline_report_vertical.json" if VERTICAL
               else "timeline_report.json")
    with open(os.path.join(out_dir, informe), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    print("TIMELINE OK:", json.dumps({
        "frames": scene.frame_end,
        "carteles_animados": len(report["signs_animated"]),
        "marcas_sin_ano": len(report["signs_sin_ano"]),
        "ortho_scale": report["camera"]["ortho_scale"],
        "warnings": report["warnings"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
