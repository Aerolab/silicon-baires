"""Step 08 — the title, built as buildings.

The reference title is not type placed over the city. **The letters are the
buildings.** Zoom into the S of SILICON and there is a curved glass facade
directly under it following the curve of the S; the red is the roof of a
building whose plan is the letterform. That is the whole gag of the sequence
and it is the thing worth getting right.

The first version of this step got it wrong: flat red plates floating a metre
over a campus of ordinary offices. It measured well against the reference
frame and it looked like a caption.

So each letter is a real building standing on the ground, carrying the same
banded facade as the rest of the city: a concrete spandrel at the letter
outline, a glass band inset 0.75 m above it, repeated per floor, with a red
roof. The inset is what makes this possible — Blender's font curves take an
outline offset in metres, so a letter can be shrunk perpendicular to its own
contour, which is what a facade band needs and what scaling cannot do.

The words sit on the street grid, which is measurable in the reference: beside
SILICON the city's own edges run at -27 deg and SILICON runs at -25.6; at the
bottom of frame the city runs at -13 and VALLEY at -13.5. Both are parallel to
the streets, and they differ from each other only because that render is
perspective and its parallel lines converge.

The letters themselves are ordinary letters. Baseline along +Y, letter
vertical along -X, both city axes, no compensation for what the camera makes
of them.

Run it after step 05, always. It deletes the trees, cars and people the
earlier steps left standing inside the letters, and those only come back when
step 05 rebuilds them, so running this one twice in a row over a title that
has moved quietly erodes the city.

    ./bl scripts/city/05_life.py && ./bl scripts/city/08_title.py
"""
import sys, pathlib, math, json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from _common import (collection, paint, srgb, R, LOTS, open_city,
                     save_city, purge, preview, HERO_WIDTH)


LINES = ("BUENOS", "AIRES")
FONT = "/Users/bilune/Library/Fonts/PPMonumentNormal-Black.otf"
# What the letter buildings are made of. Dark glass against pale concrete
# turned every letter into a zebra and fought the red; the reference's title
# buildings are ordinary offices in the city's own commonest pair.
FAM = ("Concrete Warm", "Glass Light")

# The two title colours themselves live in _palette.py. This is the one thing
# the palette does not model: at the default specular level a matte red roof
# catches enough white sky to come back from the render as salmon, not scarlet.
SPEC = 0.02

CAP = 20.0           # metres. Sized off the block, not off the frame: at
                     # TRACKING 0.93 BUENOS runs 5.2 caps long, so 20 fills the
                     # 132 m of block length and two of them plus GAP still
                     # leave a margin inside its 53 m width
GAP = 8.0            # metres between the two words
TRACKING = 0.93      # letterspacing, both words. Below about 0.88 a Black
                     # weight closes up and the letters weld into each other

FLOORS = 5
GROUND = 4.6         # taller ground floor, same as the rest of the city
FLOOR = 3.8
INSET = 0.75         # how far the glass sits back from the spandrel
PARAPET = 0.9

# where the title lands in frame, as a fraction of it, measured off the
# reference: it is all but centred, and it is big
TARGET_CX, TARGET_CY = 0.479, 0.546


def plan(x, y):
    """Glyph coordinates to ground coordinates. A rotation, nothing else.

    The letters are normal letters, laid out on the street grid: the baseline
    runs along +Y and the letter's own vertical along -X, both of them city
    axes. How that reads from any particular camera is the camera's problem.

    An earlier version pre-sheared the glyphs 45 degrees in plan so that they
    would come back upright on screen under this one camera. It did, and it was
    wrong: it made the buildings parallelograms to flatter a single viewpoint.
    """
    return -y, x


def materials():
    """The two title colours live in _palette.py like every other colour.

    What stays here is the one thing the palette does not model: at the
    default specular level a matte red roof catches enough white sky to come
    back from the render as salmon rather than scarlet.
    """
    for name in ("Title Red", "Title Edge"):
        m = paint(name)
        m.node_tree.nodes["Principled BSDF"] \
            .inputs["Specular IOR Level"].default_value = SPEC


def font_curve(body, size, spacing, offset, extrude):
    cu = bpy.data.curves.new(body, type="FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(FONT)
    cu.size = size
    cu.space_character = spacing
    cu.offset = offset
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    return cu


def band(body, coll, size, spacing, z0, z1, offset, mats, dx=0.0, dy=0.0):
    """One horizontal slice of a word, extruded from its own outline.

    Blender extrudes a font curve symmetrically about its origin and caps both
    ends, so the slice is built at zero and moved to the middle of its range.
    The glyph comes out in its own 2D frame and is put on the ground by plan().
    """
    ob = bpy.data.objects.new(body, font_curve(body, size, spacing, offset,
                                               (z1 - z0) / 2))
    coll.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob, do_unlink=True)
    for v in me.vertices:
        v.co.x, v.co.y = plan(v.co.x + dx, v.co.y + dy)
        v.co.z += (z0 + z1) / 2
    out = bpy.data.objects.new(f"{body}_{z0:05.1f}", me)
    coll.objects.link(out)
    for name in mats:
        me.materials.append(bpy.data.materials[name])
    if len(mats) > 1:                     # slot 0 faces up, slot 1 the sides
        for poly in me.polygons:
            poly.material_index = 0 if abs(poly.normal.z) > 0.7 else 1
    return out


def outline_size(body, size, spacing):
    ob = bpy.data.objects.new(body, font_curve(body, size, spacing, 0.0, 0.1))
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return max(xs) - min(xs), max(ys) - min(ys)


def fit(body, cap):
    """Cap height sets the size; the letterspacing is a fixed number.

    Both words get the same TRACKING and the same cap height, so the gaps
    between letters are literally the same in metres and the shorter word just
    comes out shorter and centred under the longer one. The earlier version
    solved the spacing per word so that both spanned the same width, which
    tracked AIRES out to nearly twice the gaps of BUENOS to cover for having
    one letter fewer.
    """
    _, h0 = outline_size(body, 10.0, 1.0)
    return 10.0 * cap / h0, TRACKING


def build_word(body, coll, cap, root, dx=0.0, dy=0.0):
    """Ground floor, then a spandrel and a glass band per floor, then the red
    roof. The same recipe as wing() in step 04, applied to a letter."""
    size, spacing = fit(body, cap)
    conc, glass = FAM
    parts = [band(body, coll, size, spacing, 0.0, GROUND, -INSET, (glass,),
                  dx, dy)]
    z = GROUND
    for _ in range(FLOORS):
        parts.append(band(body, coll, size, spacing, z, z + 1.15, 0.0,
                          (conc,), dx, dy))
        parts.append(band(body, coll, size, spacing, z + 1.15, z + FLOOR,
                          -INSET, (glass,), dx, dy))
        z += FLOOR
    # the roof: red from above, a dark cut edge from the side, which is what
    # reads as the crisp outline around every letter in the reference
    parts.append(band(body, coll, size, spacing, z, z + PARAPET, 0.0,
                      ("Title Red", "Title Edge"), dx, dy))
    for p in parts:
        p.parent = root
    w, h = outline_size(body, size, spacing)
    return parts, w, h, z + PARAPET


def title_points(root, roofs_only=False):
    """The framing targets the roofs, not the whole volume.

    The measurements taken off the reference are of its red pixels, and its
    red is the roofs. Framing the buildings instead puts the centre of a 25 m
    tall mass where the reference puts the centre of a flat word, which lands
    the roofs a fifth of a frame too high.
    """
    pts = []
    for ob in root.children:
        if roofs_only and "Title Red" not in [m.name for m in ob.data.materials]:
            continue
        mw = ob.matrix_world
        pts += [mw @ v.co for v in ob.data.vertices]
    return pts


def screen_box(scene, cam, pts):
    from bpy_extras.object_utils import world_to_camera_view
    us = [world_to_camera_view(scene, cam, p) for p in pts]
    return (min(c.x for c in us), max(c.x for c in us),
            min(c.y for c in us), max(c.y for c in us))


def title_bvh(root):
    """The letters as triangles, in world space, lifted 5 cm.

    The lift is the same one 99_check_overlap.py uses: a car resting on the
    pavement is not intersecting it, and coplanar triangles report as
    overlapping.
    """
    verts, faces = [], []
    for ob in root.children:
        if ob.type != "MESH":
            continue
        mw = ob.matrix_world
        n = len(verts)
        verts.extend((mw @ v.co) + Vector((0, 0, 0.05))
                     for v in ob.data.vertices)
        ob.data.calc_loop_triangles()
        faces.extend(tuple(i + n for i in lt.vertices)
                     for lt in ob.data.loop_triangles)
    return BVHTree.FromPolygons(verts, faces)


def touches(bvh, ob):
    """Does this object's actual geometry cut a letter?

    Sampling points and asking whether each one is inside was tried twice, at
    eight directions and then at thirty-two, and it kept missing: a canopy can
    straddle the bar of an A with every sample point falling in the daylight
    either side of it. Four trees survived both versions and every one of them
    had branches inside a letter. This asks the triangles.
    """
    mw = ob.matrix_world
    verts = [(mw @ v.co) for v in ob.data.vertices]
    ob.data.calc_loop_triangles()
    faces = [tuple(lt.vertices) for lt in ob.data.loop_triangles]
    if not faces:
        return False
    return bool(BVHTree.FromPolygons(verts, faces).overlap(bvh))


def clear_ground(scene, root):
    """Take out whatever the earlier steps left standing inside the letters.

    Steps 04 and 05 run before this one and know nothing about where the words
    land, so they plant trees and park cars across ground the title now
    occupies. A tree growing out of the middle of a letter is invisible from
    this camera and obvious from any other.
    """
    kit = set(bpy.data.collections["KIT"].objects)
    # the box the words stand in, plus the widest thing that could lean into
    # them. Without this the ray casts below run on all seven thousand objects
    # in the city and the step takes minutes; almost none of them are within a
    # block of the title.
    tp = title_points(root)
    tx0, tx1 = min(p.x for p in tp) - 12.0, max(p.x for p in tp) + 12.0
    ty0, ty1 = min(p.y for p in tp) - 12.0, max(p.y for p in tp) + 12.0
    bvh = title_bvh(root)
    doomed = []
    for ob in scene.objects:
        if ob.type != "MESH" or ob.parent == root:
            continue
        if ob.name in ("site", "markings", "buildings", "landmarks",
                       "porteno"):
            continue
        lx, ly = ob.location.x, ob.location.y
        if not (tx0 <= lx <= tx1 and ty0 <= ly <= ty1):
            continue
        # never the KIT masters. They live near the origin, so the title lands
        # on top of them, and deleting one takes every instance of that asset
        # in the city with it: step 05 then dies on KeyError: 'Tree1'.
        if ob in kit:
            continue
        # sampled vertices, not just the origin and the bounding box: a
        # streetlight's arm reaches into a letter while its origin and its
        # corners stay outside, and footing() then reports it and this does not
        mw = ob.matrix_world
        vs = ob.data.vertices
        step = max(1, len(vs) // 12)
        # range(), not vs[::step]: bpy_prop_collection rejects a slice with a
        # step, and the TypeError left the step exiting 0 as if it had worked
        pts = [mw.translation] + [mw @ vs[i].co
                                  for i in range(0, len(vs), step)]
        # plus a ring at the object's own plan radius. A tree standing just
        # clear of a letter still puts its canopy through the wall, and every
        # sampled vertex of it can be outside while the volume is not: the
        # overlap check found exactly one of these and it was a tree.
        rad = max((math.hypot(p.x - mw.translation.x, p.y - mw.translation.y)
                   for p in pts), default=0.0)
        if rad > 0.5:
            # two rings, not one. Eight points at the full radius fall
            # between the strokes of a letter often enough to miss: four
            # trees survived that version and every one of them had its
            # canopy inside an O.
            pts += [mw.translation +
                    Vector((math.cos(k * math.pi / 8) * rad * f,
                            math.sin(k * math.pi / 8) * rad * f, 0))
                    for k in range(16) for f in (1.0, 0.6)]
        if any(inside(root, p) for p in pts) or touches(bvh, ob):
            doomed.append(ob)
    for ob in doomed:
        bpy.data.objects.remove(ob, do_unlink=True)
    print(f"  cleared {len(doomed)} instances out of the letters' footprint")


def footing(scene, root):
    """The title occupies real ground now, so the question is no longer how
    much air is under it but what it is standing in. Anything of the ordinary
    city left inside the letters would be buried in them."""
    pts = title_points(root)
    x0, x1 = min(p.x for p in pts), max(p.x for p in pts)
    y0, y1 = min(p.y for p in pts), max(p.y for p in pts)
    print(f"  footprint  x {x0:7.1f} to {x1:7.1f}   y {y0:7.1f} to {y1:7.1f}")

    kit = set(bpy.data.collections["KIT"].objects)
    bad = {}
    for ob in scene.objects:
        if ob.type != "MESH" or ob.parent == root or ob.hide_render:
            continue
        # the KIT masters park near the origin and the title block sits on top
        # of them. They are excluded from the view layer, so they are not in
        # the frame, and clear_ground must never delete them.
        if ob.name in ("site", "markings") or ob in kit:
            continue
        mw = ob.matrix_world
        for vert in ob.data.vertices:
            w = mw @ vert.co
            if x0 <= w.x <= x1 and y0 <= w.y <= y1 and w.z > 1.0:
                if inside(root, w):
                    bad[ob.name] = bad.get(ob.name, 0) + 1
                break
    if bad:
        print(f"  WARNING: {len(bad)} objects stand inside the letters")
        for name, n in sorted(bad.items(), key=lambda kv: -kv[1])[:8]:
            print(f"      {name}")
    else:
        print("  nothing of the city is left standing inside the letters")


def inside(root, w):
    up = Vector((0, 0, 1))
    for ob in root.children:
        inv = ob.matrix_world.inverted()
        o = inv @ Vector((w.x, w.y, -1.0))
        if ob.ray_cast(o, (inv.to_3x3() @ up).normalized())[0]:
            return True
    return False


def main():
    # After 05, always: this step clears the ground it stands on, and
    # anything 05 placed there would otherwise survive inside the letters.
    scene = open_city(needs_collections=("BUILDINGS", "NATURE"),
                      needs_files=(LOTS,),
                      hint="run 04_buildings.py and 05_life.py first")
    materials()

    coll = purge("TITLE")

    root = bpy.data.objects.new("TitleRoot", None)
    coll.objects.link(root)
    root.empty_display_size = 20.0

    # Offsets go in glyph space, before plan(). Both words get the same cap
    # height and the same letterspacing, so the short one is simply shorter and
    # centred under the long one; the only offset is the leading.
    #
    # The second word is deliberately NOT slid back along the baseline. The
    # reference appears to nest VALLEY under SILICON that way, but the baseline
    # descends, so a backward shift also lifts the word on screen by sin(e)
    # times the shift, and that ate the clearance between the lines.
    for k, body in enumerate(LINES):
        dy = (+1 if k == 0 else -1) * (CAP + GAP) / 2
        parts, w, h, top = build_word(body, coll, CAP, root, 0.0, dy)
        print(f"  {body:8s} cap {h:5.1f} m   word {w:6.1f} m   "
              f"roof {top:5.1f} m   {len(parts)} bands")

    # Centre it on the block it was sized for. The block is the constraint
    # now, not the frame: the word has to sit on real ground.
    data = json.loads((LOTS).read_text())
    x0, x1, y0, y1 = data["superblock"]
    pts = title_points(root)
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    root.location = Vector(((x0 + x1) / 2 - cx, (y0 + y1) / 2 - cy, 0.0))
    bpy.context.view_layer.update()
    pts = title_points(root)
    print(f"  block   x {x0:7.1f} to {x1:7.1f}   y {y0:7.1f} to {y1:7.1f}")
    print(f"  title   x {min(p.x for p in pts):7.1f} to "
          f"{max(p.x for p in pts):7.1f}   "
          f"y {min(p.y for p in pts):7.1f} to {max(p.y for p in pts):7.1f}")

    # Then frame it by moving the CAMERA. The title is pinned to its block, so
    # the camera is the only thing left free; an orthographic camera slid
    # perpendicular to its own axis just shifts the frame.
    #
    # Inside preview(), because the framing solved here is a MEASUREMENT, not
    # the shot. Step 12 owns the camera in the .blend and overwrites all of
    # this with keyframes; what this loop is for is the roof bbox printed
    # below, which is the number that gets compared to the reference. Leaving
    # the camera where the solve put it just meant the file carried whichever
    # framing the last step to run happened to want.
    scene.render.resolution_x, scene.render.resolution_y = 2560, 1440
    aspect = scene.render.resolution_y / scene.render.resolution_x
    with preview(HERO_WIDTH) as cam:
        right = cam.matrix_world.col[0].to_3d().normalized()
        up = cam.matrix_world.col[1].to_3d().normalized()

        for _ in range(4):
            bpy.context.view_layer.update()
            u0, u1, v0, v1 = screen_box(scene, cam, title_points(root, True))
            du = (TARGET_CX - (u0 + u1) / 2) * HERO_WIDTH
            dv = (TARGET_CY - (v0 + v1) / 2) * HERO_WIDTH * aspect
            cam.location -= right * du + up * dv
        bpy.context.view_layer.update()
        u0, u1, v0, v1 = screen_box(scene, cam, title_points(root, True))
        print(f"\n  roof bbox {u1 - u0:.3f} x {v1 - v0:.3f}   "
              f"(reference 0.642 x 0.437)")
        print(f"  centre     {(u0 + u1) / 2:.3f}, {(v0 + v1) / 2:.3f}   "
              f"(reference {TARGET_CX}, {TARGET_CY})")
        print(f"  root at    ({root.location.x:.1f}, {root.location.y:.1f})")
        clear_ground(scene, root)
        footing(scene, root)

        blib.render(str(R / "city_08_title.png"), "EEVEE", samples=64,
                    resolution=(1600, 900),
                    exposure=scene.view_settings.exposure)

        # an isolation pass, so measuring the title does not mean picking it
        # out of a city that also contains red cars and a red rooftop sign
        hidden = [ob for ob in scene.objects
                  if ob.type == "MESH" and ob not in coll.objects[:]
                  and not ob.hide_render]
        for ob in hidden:
            ob.hide_render = True
        was = scene.render.film_transparent
        scene.render.film_transparent = True
        blib.render(str(R / "city_08_title_only.png"), "EEVEE", samples=32,
                    resolution=(1600, 900),
                    exposure=scene.view_settings.exposure)
        scene.render.film_transparent = was
        for ob in hidden:
            ob.hide_render = False

    save_city()


main()
