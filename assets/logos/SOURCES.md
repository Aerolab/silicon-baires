# The logos, and where each one came from

> **These are third-party trademarks.** None of them is a licensed asset: they
> are here to mock up the city. Before publishing the video, somebody has to
> decide whether that is editorial use or whether permission is needed, and that
> decision is not a technical one. The same goes for this repository: the files
> under `assets/logos/` are the property of their respective owners and are not
> covered by whatever terms apply to the rest of the project.

28 brands replacing the 42 invented ones in `renders/city_signs.json`. Each file
is the best format that exists publicly, looked for in this order: SVG from the
official site → SVG from Wikimedia Commons → the highest-resolution PNG there
is.

## Vector (18)

| file | brand | source |
|---|---|---|
| `aerolab.svg` | Aerolab | inline SVG from the aerolab.co header |
| `aleph.svg` | Aleph | inline SVG from alephholding.com |
| `auth0.svg` | Auth0 | worldvectorlogo. Shield symbol, no wordmark |
| `basement.svg` | Basement | inline SVG from basement.studio |
| `despegar.svg` | Despegar | Wikimedia Commons |
| `digitalhouse.svg` | Digital House | Prismic CDN, digitalhouse.com |
| `globant.svg` | Globant | Wikimedia Commons, 2999x520 |
| `increase.svg` | Increase | inline SVG from increasecard.com |
| `lemon.svg` | Lemon | inline SVG from lemon.me |
| `mercadolibre.svg` | Mercado Libre | Commons, Spanish wordmark. **No handshake** |
| `mural.svg` | Mural | Commons, 2022 version. **Carries a white background box** |
| `naranjax.svg` | Naranja X | Wikimedia Commons |
| `pomelo.svg` | Pomelo | inline SVG from pomelo.la |
| `satellogic.svg` | Satellogic | satellogic.com WordPress |
| `technisys.svg` | Technisys | web.archive.org, 2021 capture. The brand no longer exists: SoFi absorbed it |
| `tiendanube.svg` | Tiendanube | inline SVG from tiendanube.com |
| `uala.svg` | Ualá | Wikimedia Commons |
| `vercel.svg` | Vercel | worldvectorlogo |

## Vector, the August 2026 batch (7)

The six new clients. All of them were normalised the same way before being
saved: explicit `width`/`height` taken from the `viewBox`, because Blender's
importer does not understand `width="100%"` and returns an empty curve without
saying so.

| file | brand | source |
|---|---|---|
| `belo.svg` | Belo | inline SVG from belo.app. The `fill` arrived as `var(--token-…, rgb(83,0,218))` and was replaced with `#5300da`: Blender does not resolve CSS variables and imported it black |
| `coderhouse.svg` | Coderhouse | Framer CDN, coderhouse.com, 811x236. Wordmark only, 8.4:1 |
| `complif.svg` | Complif | Webflow CDN, complif.com, 690x189. **White**: needs a dark facade |
| `complif_dark.svg` | Complif | the same file with the `fill` at `#1c1c1c`, for when the brand moves to a light wall. Unused today: the facade it landed on is dark brick |
| `galicia_iso.svg` | Galicia | **the symbol alone**, from the Paisanos site, who did work for them. It is the current brand (orange circle, white dagger). The new lowercase wordmark is NOT public in vector form: Commons, logotyp.us and seeklogo all carry the previous one, the orange box with "Galicia" in serif |
| `paisanos.svg` | Paisanos | inline SVG from paisanos.io. White wordmark plus lime symbol: needs a dark background |
| `rebill.svg` | Rebill | inline SVG from rebill.com. Arrives as `currentColor`, i.e. with no colour: the table's `ink` wins |

## Raster (5)

| file | brand | source and size |
|---|---|---|
| `etermax.png` | Etermax | Commons, 3735x2377 |
| `modo.png` | MODO | Storyblok CDN, modo.com.ar, 436x96. **The smallest of the lot** |
| `olx.png` | OLX | Commons, 1000x1000 |
| `ripio.png` | Ripio | Commons, 5000x2292 |
| `uala_iso.png` | Ualá | Commons, 4501x4501 combination mark |

## What has to be sorted out before applying them

**Four are white**: `aerolab`, `aleph`, `digitalhouse` and `pomelo` come from
dark-background sites and disappear on a light facade. Either the dark variant
gets sourced, or the sign carrying them has to be dark by design decision.

**`mural.svg` carries the logo's white box**, which on a roofmark comes out as a
white rectangle around the mark. It has to be cropped out or used as the panel
itself.

**`modo.png` is 436x96** and raster. On a 34 m party wall it does not hold up.
If MODO goes on a large format, the vector has to be found.

**The 45 roofmarks and the 13 masts want a symbol, not a wordmark.** Almost all
of these files are the full horizontal wordmark, which read from 250 m up is an
illegible line of text. A second round is missing, to collect the standalone
symbol from the brands that have one: the Mercado Libre handshake, the Naranja
X, the two Tiendanube clouds, the Vercel triangle, the Auth0 shield (that one is
already like this).

`_contact.png` is the contact sheet of all of them, for looking at them together.
