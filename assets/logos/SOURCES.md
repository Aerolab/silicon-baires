# Los logos, de dónde salió cada uno

28 marcas para reemplazar a las 42 inventadas de `renders/city_signs.json`. Cada
archivo es el mejor formato que existe públicamente, buscado en este orden:
SVG del sitio oficial → SVG de Wikimedia Commons → PNG de la mayor resolución
que haya.

**Son marcas de terceros.** Ninguno es un asset con licencia de uso: están acá
para maquetar la ciudad. Antes de publicar el video hay que decidir si eso es
uso editorial o si hace falta permiso, y esa decisión no es técnica.

## Vector (18)

| archivo | marca | fuente |
|---|---|---|
| `aerolab.svg` | Aerolab | SVG inline del header de aerolab.co |
| `aleph.svg` | Aleph | SVG inline de alephholding.com |
| `auth0.svg` | Auth0 | worldvectorlogo. Isotipo escudo, sin wordmark |
| `basement.svg` | Basement | SVG inline de basement.studio |
| `despegar.svg` | Despegar | Wikimedia Commons |
| `digitalhouse.svg` | Digital House | CDN Prismic de digitalhouse.com |
| `globant.svg` | Globant | Wikimedia Commons, 2999x520 |
| `increase.svg` | Increase | SVG inline de increasecard.com |
| `lemon.svg` | Lemon | SVG inline de lemon.me |
| `mercadolibre.svg` | Mercado Libre | Commons, wordmark español. **Sin el apretón de manos** |
| `mural.svg` | Mural | Commons, versión 2022. **Trae caja blanca de fondo** |
| `naranjax.svg` | Naranja X | Wikimedia Commons |
| `pomelo.svg` | Pomelo | SVG inline de pomelo.la |
| `satellogic.svg` | Satellogic | WordPress de satellogic.com |
| `technisys.svg` | Technisys | web.archive.org, captura de 2021. La marca ya no existe: SoFi la absorbió |
| `tiendanube.svg` | Tiendanube | SVG inline de tiendanube.com |
| `uala.svg` | Ualá | Wikimedia Commons |
| `vercel.svg` | Vercel | worldvectorlogo |

## Vector, la tanda de agosto 2026 (7)

Los seis clientes nuevos. Todos se normalizaron igual antes de guardarlos:
`width`/`height` explícitos sacados del `viewBox`, porque el importador de
Blender no entiende `width="100%"` y devuelve una curva vacía sin avisar.

| archivo | marca | fuente |
|---|---|---|
| `belo.svg` | Belo | SVG inline de belo.app. El `fill` venía como `var(--token-…, rgb(83,0,218))` y se reemplazó por `#5300da`: Blender no resuelve variables CSS y lo importaba negro |
| `coderhouse.svg` | Coderhouse | CDN de Framer de coderhouse.com, 811x236. Solo logotipo, 8,4:1 |
| `complif.svg` | Complif | CDN de Webflow de complif.com, 690x189. **Blanco**: pide fachada oscura |
| `complif_dark.svg` | Complif | el mismo archivo con el `fill` en `#1c1c1c`, para cuando la marca se mude a una pared clara. Hoy no se usa: la fachada que le tocó es de ladrillo oscuro |
| `galicia_iso.svg` | Galicia | **el isotipo solo**, del sitio de Paisanos, que hizo trabajo para ellos. Es la marca actual (círculo naranja, daga blanca). El logotipo nuevo en minúscula NO está público en vector: Commons, logotyp.us y seeklogo tienen todos el anterior, la caja naranja con "Galicia" en serif |
| `paisanos.svg` | Paisanos | SVG inline de paisanos.io. Logotipo blanco más isotipo lima: pide fondo oscuro |
| `rebill.svg` | Rebill | SVG inline de rebill.com. Viene en `currentColor`, o sea sin color: manda el `ink` de la tabla |

## Raster (5)

| archivo | marca | fuente y tamaño |
|---|---|---|
| `etermax.png` | Etermax | Commons, 3735x2377 |
| `modo.png` | MODO | CDN Storyblok de modo.com.ar, 436x96. **El más chico de todos** |
| `olx.png` | OLX | Commons, 1000x1000 |
| `ripio.png` | Ripio | Commons, 5000x2292 |
| `uala_iso.png` | Ualá | Commons, imagotipo 4501x4501 |

## Lo que hay que resolver antes de aplicarlos

**Cuatro son blancos**: `aerolab`, `aleph`, `digitalhouse`, `pomelo` vienen de
sitios de fondo oscuro y desaparecen sobre una fachada clara. O se consigue la
variante oscura, o el cartel que los lleve tiene que ser de fondo oscuro por
decisión de diseño.

**`mural.svg` trae la caja blanca** del logo, que en un roofmark queda como un
rectángulo blanco alrededor del mark. Hay que recortarla o usarla como el panel
mismo.

**`modo.png` es 436x96** y es raster. En una medianera de 34 m no aguanta. Si
MODO va a un formato grande, hay que buscar el vector.

**Los 45 roofmarks y los 13 mástiles piden isotipo, no wordmark.** Casi todos
estos archivos son el logotipo horizontal completo, que leído desde 250 m de
altura es una línea de texto ilegible. Falta una segunda ronda que junte el
símbolo suelto de las que lo tienen: el apretón de manos de Mercado Libre, la X
de Naranja, las dos nubes de Tiendanube, el triángulo de Vercel, el escudo de
Auth0 (ese ya está así).

`_contact.png` es la hoja de contacto de los 22, para mirarlos juntos.
