"""Mesh plumbing shared by the city scripts.

Primitives and instancing, nothing about cities. Each asset is accumulated into
one mesh with several material slots, so placing it later is one object sharing
one mesh datablock: the cheapest instancing Blender offers.
"""
import bpy, math, random
from mathutils import Vector, Matrix, Euler

ROOT = None

# How long the shot is. It lives here because steps 11 and 12 both need it and
# they disagreed once: step 12 lengthened the shot to 21 s and step 11 went on
# animating 10 s of traffic, so every car in the city stopped dead at frame 240
# and stood there for the rest of the shot. Nothing raises an exception when the
# traffic freezes, and the standing checks read frame 1, where it has not
# happened yet. 95_check_traffic reads it too, so its samples cover the whole
# shot rather than the first half of it.
FPS = 24
FRAMES = 624                     # 26 s
# 22 s of camera move, then FOUR seconds held on the title. It was two, and two
# is not enough: the move arrives and the film stops on the same beat, which
# reads as the video ending rather than the shot landing. The city keeps moving
# through the hold - the cars do not stop when the camera does - so the extra
# time is not a freeze frame, it is the shot settling.
MOVE = 528


def mat(name):
    return bpy.data.materials[name]


def median_runs(blocks, plaza_c, plaza_half, margin=3.0, clear=2.0,
                minimum=10.0):
    """The stretches of the 9 de Julio that actually carry a planted median.

    One run per block, reaching `margin` past the block into each crossing,
    cut in two where the plaza stands and dropped where what is left is
    shorter than `minimum` - a 9 m stub of kerb is not a median.

    It lives here because step 03 builds the medians and step 05 plants them,
    and they disagreed: 03 dropped both stubs of the plaza block for being 9 m
    long, 05 went on planting from its own block arithmetic, and four trees
    ended up standing on the bare asphalt of the avenue beside the Obelisco.
    Nothing raises an exception when a tree grows out of the road.
    """
    p0, p1 = plaza_c - plaza_half - clear, plaza_c + plaza_half + clear
    out = []
    for (c, size) in blocks:
        a, b = c - size / 2 - margin, c + size / 2 + margin
        runs = [(a, b)] if not (b > p0 and a < p1) else \
            [(a, min(b, p0)), (max(a, p1), b)]
        out.extend((ra, rb) for ra, rb in runs if rb - ra >= minimum)
    return out


def srgb(hex_str):
    h = hex_str.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def pbrmat(name, hex_col, roughness=0.8, metallic=0.0):
    """Fetch or create. Materials live in city.blend, so this is idempotent."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    import blib
    m = blib.pbr(name, srgb(hex_col), roughness=roughness, metallic=metallic)
    m.use_fake_user = True
    return m


def rng(seed):
    return random.Random(seed)


class Mesh:
    """Accumulates geometry, then builds it into a single object."""

    def __init__(self):
        self.v, self.f, self.fm, self.mats = [], [], [], []

    def slot(self, material):
        if material not in self.mats:
            self.mats.append(material)
        return self.mats.index(material)

    def _add(self, verts, faces, material, xform=None):
        if xform is not None:
            verts = [xform @ Vector(p) for p in verts]
        n = len(self.v)
        self.v.extend(tuple(p) for p in verts)
        s = self.slot(material)
        for face in faces:
            self.f.append(tuple(i + n for i in face))
            self.fm.append(s)

    # -- primitives ---------------------------------------------------------
    def box(self, center, size, material, xform=None):
        (cx, cy, cz), (sx, sy, sz) = center, size
        x0, x1 = cx - sx / 2, cx + sx / 2
        y0, y1 = cy - sy / 2, cy + sy / 2
        z0, z1 = cz - sz / 2, cz + sz / 2
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        self._add(v, f, material, xform)

    def slab(self, cx, cy, w, h, z0, z1, material, xform=None):
        self.box((cx, cy, (z0 + z1) / 2), (w, h, z1 - z0), material, xform)

    def quad(self, cx, cy, w, h, z, material, xform=None):
        v = [(cx - w / 2, cy - h / 2, z), (cx + w / 2, cy - h / 2, z),
             (cx + w / 2, cy + h / 2, z), (cx - w / 2, cy + h / 2, z)]
        self._add(v, [(0, 1, 2, 3)], material, xform)

    def prism(self, poly, z0, z1, material, xform=None, cap=True):
        """Extrude a flat polygon [(x, y), ...] between two heights.

        The winding is normalised to counter-clockwise first: a clockwise
        polygon builds with its top cap facing down, which renders black and
        raises no error.
        """
        area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] -
                   poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))
        if area < 0:
            poly = list(reversed(poly))
        n = len(poly)
        v = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
        f = [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
        if cap:
            f += [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
        self._add(v, f, material, xform)

    def cyl(self, center, radius, height, material, segs=8, top=None,
            xform=None):
        top = radius if top is None else top
        cx, cy, cz = center
        z0, z1 = cz, cz + height
        v, f = [], []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            v.append((cx + radius * math.cos(a), cy + radius * math.sin(a), z0))
        for i in range(segs):
            a = 2 * math.pi * i / segs
            v.append((cx + top * math.cos(a), cy + top * math.sin(a), z1))
        for i in range(segs):
            j = (i + 1) % segs
            f.append((i, j, j + segs, i + segs))
        f.append(tuple(range(segs - 1, -1, -1)))
        if top > 1e-6:
            f.append(tuple(range(segs, 2 * segs)))
        self._add(v, f, material, xform)

    def cone(self, center, radius, height, material, segs=8, xform=None):
        cx, cy, cz = center
        v = [(cx + radius * math.cos(2 * math.pi * i / segs),
              cy + radius * math.sin(2 * math.pi * i / segs), cz)
             for i in range(segs)] + [(cx, cy, cz + height)]
        f = [(i, (i + 1) % segs, segs) for i in range(segs)]
        f.append(tuple(range(segs - 1, -1, -1)))
        self._add(v, f, material, xform)

    def sphere(self, center, radius, material, segs=8, rings=5, scale=(1, 1, 1),
               xform=None):
        """Faceted low-poly sphere. Left flat shaded on purpose."""
        cx, cy, cz = center
        sx, sy, sz = scale
        v, f = [], []
        for r in range(1, rings):
            phi = math.pi * r / rings
            for s in range(segs):
                th = 2 * math.pi * s / segs
                v.append((cx + radius * sx * math.sin(phi) * math.cos(th),
                          cy + radius * sy * math.sin(phi) * math.sin(th),
                          cz + radius * sz * math.cos(phi)))
        top = len(v); v.append((cx, cy, cz + radius * sz))
        bot = len(v); v.append((cx, cy, cz - radius * sz))
        for r in range(rings - 2):
            for s in range(segs):
                a = r * segs + s
                b = r * segs + (s + 1) % segs
                f.append((a, b, b + segs, a + segs))
        for s in range(segs):
            f.append((top, (s + 1) % segs, s))
            f.append((bot, (rings - 2) * segs + s,
                      (rings - 2) * segs + (s + 1) % segs))
        self._add(v, f, material, xform)

    def flat(self, poly, z, material, xform=None):
        """One flat n-gon at a height. The block surfaces are octagons now and
        quad() only makes rectangles."""
        self._add([(x, y, z) for x, y in poly],
                  [tuple(range(len(poly)))], material, xform)

    def arc_band(self, r0, r1, a0, a1, z, material, segs=None, xform=None):
        """Flat annulus sector: road markings and kerbs that follow a curve."""
        if segs is None:
            segs = max(2, min(48, int(abs(a1 - a0) * max(r0, r1) / 2.5)))
        ang = [a0 + (a1 - a0) * i / segs for i in range(segs + 1)]
        poly = [(r1 * math.cos(a), r1 * math.sin(a)) for a in ang]
        poly += [(r0 * math.cos(a), r0 * math.sin(a)) for a in reversed(ang)]
        v = [(x, y, z) for x, y in poly]
        self._add(v, [tuple(range(len(v)))], material, xform)

    def add_mesh(self, me, material, xform=None):
        """Absorb an existing Blender mesh. Font curves arrive this way: a
        letterform is not expressible as any primitive here."""
        self._add([v.co.copy() for v in me.vertices],
                  [tuple(p.vertices) for p in me.polygons], material, xform)

    # -- output -------------------------------------------------------------
    def build(self, name, coll=None, smooth=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        for m in self.mats:
            me.materials.append(m)
        for poly, s in zip(me.polygons, self.fm):
            poly.material_index = s
        if smooth:
            for poly in me.polygons:
                poly.use_smooth = True
        me.update()
        me.validate()
        ob = bpy.data.objects.new(name, me)
        (coll or bpy.context.scene.collection).objects.link(ob)
        return ob


def collection(name, parent=None, hide=False):
    if name in bpy.data.collections:
        c = bpy.data.collections[name]
    else:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    if hide:
        c.hide_render = c.hide_viewport = True
    return c


def instance(source, coll, location=(0, 0, 0), rotation_z=0.0, scale=1.0,
             name=None):
    """A new object sharing the source mesh: no geometry is duplicated."""
    ob = bpy.data.objects.new(name or (source.name + ".i"), source.data)
    ob.location = location
    ob.rotation_euler = Euler((0, 0, rotation_z))
    ob.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    coll.objects.link(ob)
    return ob


def counts():
    """Unique vs instanced triangles: the memory budget, at a glance."""
    uniq, seen, total = 0, set(), 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.hide_render:
            continue
        t = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        total += t
        if ob.data.name not in seen:
            seen.add(ob.data.name)
            uniq += t
    return uniq, total
