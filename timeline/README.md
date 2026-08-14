# timeline — la ciudad, año por año

Esta carpeta agrega una capa opcional sobre `renders/city.blend`: en vez de
mover la cámara sobre una ciudad terminada, **clava la cámara y hace avanzar el
año**. Cada marca cuya empresa tiene año de fundación citable arranca con el
lote vacío, se le construye el edificio en su año, y el cartel aparece cuando la
obra termina. Tres empresas que existieron y cerraron se levantan y se derrumban.

No toca nada del generador. Lee `renders/city.blend` y `renders/city_signs.json`,
y guarda su propio `.blend` aparte.

```bash
./bl timeline/timeline_layer.py -- --repo timeline              # 1920x1080
./bl timeline/timeline_layer.py -- --repo timeline --vertical   # 1080x1920
```

## Qué hay acá

| Archivo | Qué es |
|---|---|
| `timeline_layer.py` | La capa: congela la cámara, separa los edificios, los construye por año |
| `data/brand_years.json` | Año de fundación de 40 de las 72 marcas de la ciudad, con fuente |
| `data/cerraron.json` | Tres empresas que cerraron: DeRemate, Sonico, Taringa! |
| `data/landmarks.json` | BOTR y las obras del Monumental |
| `scene_city/city_timeline.blend` | La escena apaisada ya construida |
| `scene_city/city_timeline_vertical.blend` | La vertical, con recorrido de cámara |
| `scene_city/timeline_report.json` | Qué se animó, con qué años y qué quedó sin resolver |

## La regla de los datos

De las 72 marcas que reparte `_brands.py`, **40 tienen año**. Las otras 32 no
reciben una fecha inventada: se revelan junto con su edificio, pero sin
pretender que ese año signifique algo. Son las que el propio `_brands.py`
declara inventadas, más un puñado de reales que no encontramos con fuente.

Cada año lleva un campo `confidence`:

- `confirmed` — está en Wikipedia o en la propia empresa
- `reported` — sólo en prensa o bases de terceros
- `conflicting_sources` — Tiendanube figura como 2010 y como 2011 según dónde se
  mire; se usó 2011 y quedó anotado
- `user_provided` — **sin fuente publicada.** Son Basement, Belo, Complif,
  Maslow, MODO, OpenZeppelin, Paisanos, Patmos, Revamos, Takenos, SLA y BOTR.
  Van marcadas así justamente para que se puedan chequear o descartar.

Los hitos posteriores —Mercado Libre en Nasdaq 2007, Naspers tomando OLX 2010,
Globant en la NYSE 2014, Okta comprando Auth0 en 2021— aparecen en **su** año y
hacen crecer el edificio un escalón.

Una adquisición no derrumba nada: Auth0, Technisys, Despegar y OLX se vendieron
bien y sus edificios quedan en pie. Caerse queda para las que efectivamente
desaparecieron.

## Lo que es dato y lo que es puesta en escena

Vale separarlo, porque no es lo mismo:

- **Dato.** Las 40 empresas aparecen en su año documentado, y sus hitos también.
- **Puesta en escena.** Los 95 edificios que no son de ninguna marca, el
  tránsito, la gente y las letras del título se reparten a lo largo del período
  con sesgo hacia los años tardíos, para que la ciudad arranque casi vacía. Es
  determinista —siempre se construye en el mismo orden— y queda declarado así en
  `timeline_report.json`.

## Notas de implementación

Tres cosas que costaron y conviene no re-derivar:

- **`BUILDINGS` es un solo mesh.** No hay nada que escalar por edificio.
  `bpy.ops.mesh.separate` no sirve en tanda: en background depende del objeto
  activo y después de la primera separación deja de encontrar geometría —separó
  1 de 22—. Con bmesh en una sola pasada, 40 de 40.
- **El `owner` del cartel no es el `at` del sitio.** Viene redondeado
  (`-26.0, -167.0`) contra la grilla con decimales (`-351.75, -327.75`). Se
  matchea por contención en el footprint, no por igualdad.
- **En vertical, sin motion blur.** Con la cámara quieta el desenfoque sólo toca
  a los autos y queda bien; moviéndola desenfoca la ciudad entera.

## Crédito

La ciudad, los materiales, la luz y los logos son de este repo. Esta capa sólo
le agrega el eje del tiempo.
