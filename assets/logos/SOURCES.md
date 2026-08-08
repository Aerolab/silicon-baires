# The logos, and where each one came from

> **These are third-party trademarks.** None of them is a licensed asset: they
> are here to mock up the city. Before publishing the video, somebody has to
> decide whether that is editorial use or whether permission is needed, and that
> decision is not a technical one. The same goes for this repository: the files
> under `assets/logos/` are the property of their respective owners and are not
> covered by whatever terms apply to the rest of the project.

Each file is the best format that exists publicly, looked for in this order: SVG
from the official site → SVG from Wikimedia Commons → the highest-resolution PNG
there is.

**This table is the inventory, not a changelog.** Every file in this directory
gets a row, and a file with no row is a gap in the table rather than a file that
does not count. Git already records when each one arrived, so they are listed
alphabetically instead — the question anyone brings here is "is there a vector
for X, and what does it lack", never "what shipped in August".

**Normalise an SVG before saving it**: explicit `width`/`height` taken from the
`viewBox`. Blender's importer does not understand `width="100%"` and returns an
empty curve without saying so.

**`_iso` and `_word` are one lockup split into two files.** `_brands.HERO` mounts
the symbol and the wordmark in different places — the symbol on a wall, the name
laid flat on a roof — so they have to be separate curves. The pairs below share
their parent's `viewBox`, which is what makes them a split rather than two
downloads.

## Vector (44 files)

| file | brand | source |
|---|---|---|
| `aerolab.svg` | Aerolab | inline SVG from the aerolab.co header |
| `aleph.svg` | Aleph | inline SVG from alephholding.com |
| `auth0.svg` | Auth0 | worldvectorlogo. Shield symbol, no wordmark |
| `auth0_iso.svg` | Auth0 | split of the lockup — source not recorded |
| `auth0_word.svg` | Auth0 | split of the lockup — source not recorded |
| `basement.svg` | Basement | inline SVG from basement.studio |
| `belo.svg` | Belo | inline SVG from belo.app. The `fill` arrived as `var(--token-…, rgb(83,0,218))` and was replaced with `#5300da`: Blender does not resolve CSS variables and imported it black |
| `coderhouse.svg` | Coderhouse | Framer CDN, coderhouse.com, 811x236. Wordmark only, 8.4:1 |
| `complif.svg` | Complif | Webflow CDN, complif.com, 690x189. **White**: needs a dark facade |
| `cocos.svg` | Cocos Capital | inline SVG from cocos.capital, 192x86, via a web.archive.org capture: the live site is behind Cloudflare and answers 403 to everything that is not a browser. The stacked lockup — the symbol over the wordmark — with the `clipPath` dropped, because Blender imports the clip rectangle as a curve and it would set the bounds |
| `cocos_iso.svg` | Cocos Capital | split of `cocos.svg` — the two arcs, navy `#002C65` and blue `#0062E1` |
| `cocos_word.svg` | Cocos Capital | split of `cocos.svg` — the five letters, 5:1. **This is the one `_brands` uses**: the lockup is 2.2:1 and its wall is bound by the height |
| `complif_dark.svg` | Complif | the same file with the `fill` at `#1c1c1c`, for when the brand moves to a light wall. Unused today: the facade it landed on is dark brick |
| `despegar.svg` | Despegar | Wikimedia Commons |
| `digitalhouse.svg` | Digital House | Prismic CDN, digitalhouse.com |
| `etermax_new.svg` | Etermax | **source not recorded**. 38x43, the symbol rather than the wordmark |
| `etermax_word.svg` | Etermax | **source not recorded**. 7470x4754. This is the one `_brands` uses |
| `galicia_iso.svg` | Galicia | **the symbol alone**, from the Paisanos site, who did work for them. It is the current brand (orange circle, white dagger). The new lowercase wordmark is NOT public in vector form: Commons, logotyp.us and seeklogo all carry the previous one, the orange box with "Galicia" in serif |
| `globant.svg` | Globant | Wikimedia Commons, 2999x520 |
| `humand.svg` | Humand | **source not recorded**. 139x23, wordmark |
| `increase.svg` | Increase | inline SVG from increasecard.com |
| `lemon.svg` | Lemon | inline SVG from lemon.me |
| `lemon_iso.svg` | Lemon | split of `lemon.svg` — same 274x63 viewBox |
| `lemon_word.svg` | Lemon | split of `lemon.svg` — same 274x63 viewBox |
| `mercadolibre.svg` | Mercado Libre | Commons, Spanish wordmark. **No handshake** |
| `ml_iso.svg` | Mercado Libre | the handshake `mercadolibre.svg` lacks — **source not recorded** |
| `mp_iso.svg` | Mercado Pago | **source not recorded**. 64x64, the light-blue handshake |
| `mural.svg` | Mural | Commons, 2022 version. **Carries a white background box** |
| `naranjax.svg` | Naranja X | Wikimedia Commons. Split by colour at runtime, not into files: the nine orange strokes are the word, the two violet ones the X |
| `paisanos.svg` | Paisanos | inline SVG from paisanos.io. White wordmark plus lime symbol: needs a dark background |
| `pomelo.svg` | Pomelo | inline SVG from pomelo.la |
| `preguntados.svg` | Preguntados (etermax) | **source not recorded**. 1788x1788. Laid flat on the Etermax roof: it is what that company puts on a building ahead of its own name |
| `rebill.svg` | Rebill | inline SVG from rebill.com. Arrives as `currentColor`, i.e. with no colour: the table's `ink` wins |
| `satellogic.svg` | Satellogic | satellogic.com WordPress |
| `takenos_iso.svg` | Takenos | split of the lockup — source not recorded |
| `takenos_word.svg` | Takenos | split of the lockup — source not recorded |
| `technisys.svg` | Technisys | web.archive.org, 2021 capture. The brand no longer exists: SoFi absorbed it |
| `tiendanube.svg` | Tiendanube | inline SVG from tiendanube.com |
| `tiendanube_iso.svg` | Tiendanube | split of `tiendanube.svg` — the two clouds |
| `tiendanube_word.svg` | Tiendanube | split of `tiendanube.svg` — the wordmark |
| `uala.svg` | Ualá | Wikimedia Commons |
| `uala2.svg` | Ualá | **source not recorded**. 1820x420. This is the one `_brands` uses |
| `vercel.svg` | Vercel | worldvectorlogo |
| `vercel_iso.svg` | Vercel | the triangle alone, 24x24 — source not recorded |

## Raster (5 files)

| file | brand | source and size |
|---|---|---|
| `etermax.png` | Etermax | Commons, 3735x2377 |
| `modo.png` | MODO | Storyblok CDN, modo.com.ar, 436x96. **The smallest of the lot** |
| `olx.png` | OLX | Commons, 1000x1000 |
| `ripio.png` | Ripio | Commons, 5000x2292 |
| `uala_iso.png` | Ualá | Commons, 4501x4501 combination mark |

`_contact.png` is the contact sheet, for looking at them together. It is not a
logo and has no row above.

## What has to be sorted out

**Sixteen files had no provenance at all**, and twelve of them are mounted by
`_brands.HERO` today. They are marked "source not recorded" above rather than
left out, because a table that silently covers two thirds of a directory reads
as complete. Filling them in means finding where each came from; until then the
gap is at least visible.

**Four are white**: `aerolab`, `aleph`, `digitalhouse` and `pomelo` come from
dark-background sites and disappear on a light facade. Either the dark variant
gets sourced, or the sign carrying them has to be dark by design decision.

**`mural.svg` carries the logo's white box**, which on a roofmark comes out as a
white rectangle around the mark. It has to be cropped out or used as the panel
itself.

**`modo.png` is 436x96** and raster. On a 34 m party wall it does not hold up.
If MODO goes on a large format, the vector has to be found.

**The roofmarks and the masts want a symbol, not a wordmark.** Most of these
files are the full horizontal lockup, which read from 250 m up is an illegible
line of text. The `_iso` splits above are that problem being worked through one
brand at a time; the ones without a split still want one.
