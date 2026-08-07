# A city, generated

An isometric Buenos Aires in the style of the *Silicon Valley* title sequence,
built entirely from code in headless Blender — then exported and run at 60 fps
in a browser, and recorded to video by the page itself.

![The hero frame: BUENOS AIRES built as buildings on the street grid, with real
company signs on the roofs and facades around it](renders/city_final.png)

No viewport, no mouse. Every building, tree, car, pedestrian, sign and camera
move comes out of a Python script, and the whole thing is reproducible from a
clean checkout.

## Quickstart

```bash
./bl scripts/verify_setup.py     # 9 checks, ~3 s. 9/9 means the environment is ready
./bl scripts/city/07_look.py     # the final Cycles frame
./bl                             # or open the GUI with the newest .blend
```

`bl` runs a script inside headless Blender. It finds the binary on its own, or
honours `BLENDER_BIN`.

To see the same city in a browser:

```bash
./bl scripts/city/20_export_web.py     # the glb, the motion, the shot, the sky
cd web && npm install && npm run dev   # http://localhost:5173
cd web && npm run record               # and the video, drawn frame by frame
```

## What is here

```
bl                     run a script inside headless Blender
blib/                  the library: framing, lights, materials, render, GN, export
scripts/city/          the city, one numbered script per layer
docs/city/             the dependency graph, the plan, the style bible
web/                   the same city in WebGL. Has its own README
renders/               outputs. city.blend is committed; the rest is regenerated
assets/logos/          the brand artwork, with SOURCES.md on where each came from
```

`blib` derives cameras and light power from the real geometry of the scene, so
the same code frames a 2 cm object and a 100 m one. Nothing is positioned by
hand.

The city itself is built by the numbered scripts in `scripts/city/`, each one
opening `city.blend`, adding its layer and saving. **The numbers are not the
order** — the dependencies are real, and `docs/city/MAP.md` is the graph. Every
step declares what it needs, so a missing prerequisite stops the run with the
command that fixes it.

## Two rules this project runs on

**A render is not validated until it has been looked at.** Framing, exposure and
material mistakes raise no exception: they come out ugly and the script exits 0.
`verify_setup.py` automates the cheapest version of this by measuring render
luminance, which catches the black or blown-out frame.

**Count it before you fix it.** Every defect here arrived as one instance
somebody happened to see, and most turned out to be a rule that was wrong
everywhere it applied — four people standing in a street was 685 of 2883 on a
carriageway; one tree in a wall was 917. So the first move on a defect is not to
fix it, it is to write the thing that counts how many there are. The count is
the scope.

That is what the nine standing checks are, and none of the failures they find
raises an exception:

```bash
./bl scripts/city/99_check_overlap.py    # nothing standing inside a building
./bl scripts/city/98_check_floating.py   # nothing buried, nothing hovering
./bl scripts/city/96_check_title_move.py # the title from other angles
./bl scripts/city/95_check_traffic.py    # right-hand traffic, and on the road
./bl scripts/city/94_check_road.py       # nothing green ON the road
./bl scripts/city/93_check_signs.py      # how many brands the shot delivers
./bl scripts/city/92_check_zfight.py     # nothing fights for the same plane
./bl scripts/city/91_check_crowd.py      # and nobody is driven through
python3 scripts/city/97_check_title.py renders/city_08_title_only.png
```

## Documentation

| | |
|---|---|
| [`docs/city/MAP.md`](docs/city/MAP.md) | the dependency graph. Read before changing the build |
| [`docs/city/STYLE-BIBLE.md`](docs/city/STYLE-BIBLE.md) | read before changing the look |
| [`docs/city/PLAN.md`](docs/city/PLAN.md) | how the build is organised, and which decisions are settled |
| [`web/README.md`](web/README.md) | the browser build, the grade, and the video |
| [`CLAUDE.md`](CLAUDE.md) | the working notes: every failure mode, and why each rule exists |

`CLAUDE.md` is the long one and the honest one. It records the attempts that
were wrong as well as the ones that stuck.

## Requirements

- **Blender 5.2 LTS** (Python 3.13). The `blender` skill under
  `.claude/skills/` documents the 5.x API changes that break code written from
  memory, all verified against the installed binary.
- **Node 18+** for `web/`, and **ffmpeg** on `PATH` for `npm run record`.
- **A heavy grotesque** for the title and the signs. The city was built with PP
  Monument Normal Black, which is commercial and not shipped here. Point
  `CITY_TITLE_FONT` at your own copy — the letters are built as geometry, so
  substituting the typeface changes the letterforms and nothing else:

  ```bash
  CITY_TITLE_FONT=/path/to/font.otf ./bl scripts/city/08_title.py
  ```
- Cycles on GPU is configured automatically by `blib.use_gpu()`. Developed on an
  Apple M4 Pro via Metal; measured at 960×540, EEVEE 64 spp is 0.65 s and Cycles
  GPU 512 spp is 3.2 s.

## Licensing, and what this repository does not grant

**There is no licence.** By default that means all rights reserved: you may read
this, and you do not have permission to use, copy, modify or redistribute it.
If you want to, ask.

Two things are not the author's to license in the first place:

- **The logos under `assets/logos/` are third-party trademarks**, collected to
  mock up the city. They belong to their owners and are not covered by anything
  here. See [`assets/logos/SOURCES.md`](assets/logos/SOURCES.md).
- **The Blender MCP add-on is not vendored here.** The optional live-session
  workflow needs `addon.py` from the upstream project,
  [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp), under its own
  licence.
