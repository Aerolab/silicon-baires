"""Where the solid things are.

A tree growing through an office wall raises no exception and does not look
wrong from every angle, so it survives. The fix is not to look harder: it is
for the scripts that place loose objects to know where the buildings are.

Buildings are built into one merged mesh, so by the time step 05 runs there is
no per-building object left to query. Instead each script that puts a solid
volume on the ground records its footprint here, and the file travels with the
.blend. A footprint is a rotated rectangle plus a height range, which is what
every building in this city actually is; the round landmarks record the
rectangle they sit inside, so they are over-protective rather than wrong.

Written by steps 04, 06, 06b and 10, one tag each; read by steps 05 and 11
and by 99_check_overlap.py. See docs/city/MAP.md.

    from _solids import Solids
    s = Solids()
    s.add(cx, cy, w, d, rot, z0, z1)
    s.merge_into(path, "buildings")     # replaces only this tag
"""
import json, math


class Solids:
    """Rotated footprints with a height range. Queried by point, not by mesh."""

    CELL = 24.0                       # spatial hash cell, about a third of a block

    def __init__(self, boxes=None):
        self.boxes = list(boxes or [])
        self._grid = None

    # -- building ------------------------------------------------------------
    def add(self, cx, cy, w, d, rot=0.0, z0=0.0, z1=100.0, tag=""):
        self.boxes.append([cx, cy, w, d, rot, z0, z1, tag])
        self._grid = None

    def extend(self, other):
        self.boxes.extend(other.boxes)
        self._grid = None

    # -- persistence ---------------------------------------------------------
    def save(self, path):
        path.write_text(json.dumps({"boxes": self.boxes}))

    @classmethod
    def load(cls, path):
        if not path.exists():
            return cls()
        return cls(json.loads(path.read_text())["boxes"])

    def merge_into(self, path, tag):
        """Replace every box carrying this tag, keep the rest.

        The steps run one at a time and each one rebuilds only its own layer,
        so a whole-file rewrite would silently drop the layers that are still
        standing in the .blend.
        """
        keep = [b for b in Solids.load(path).boxes if b[7] != tag]
        for b in self.boxes:
            b[7] = tag
        Solids(keep + self.boxes).save(path)

    # -- query ---------------------------------------------------------------
    def _build_grid(self):
        self._grid = {}
        for idx, (cx, cy, w, d, rot, z0, z1, tag) in enumerate(self.boxes):
            # AABB of the rotated rectangle
            c, s = abs(math.cos(rot)), abs(math.sin(rot))
            ex = (w * c + d * s) / 2
            ey = (w * s + d * c) / 2
            for gi in range(int((cx - ex) // self.CELL),
                            int((cx + ex) // self.CELL) + 1):
                for gj in range(int((cy - ey) // self.CELL),
                                int((cy + ey) // self.CELL) + 1):
                    self._grid.setdefault((gi, gj), []).append(idx)

    def hit(self, x, y, z=None, pad=0.0, tags=None):
        """The box this point is inside, or None.

        `pad` grows every footprint outwards, which is how a caller asks for
        clearance: a tree is not a point, so it is queried with its own canopy
        radius and stays that far off the wall.

        `tags` narrows the query to some of the layers. Somebody standing on a
        roof is inside the building's own footprint by definition, so asking
        "is this person inside anything" always says yes; asking "is this
        person inside a sign or a cupola" is the question that means something.
        """
        if self._grid is None:
            self._build_grid()
        # every cell the padded query disc touches, not just the one the point
        # is in. Looking only at its own cell is the same bug as a broad-phase
        # that forgets the query has a radius: a tree with an 8 m canopy stood
        # 2 m outside a footprint that lived one 24 m cell over, and the test
        # cheerfully passed while the canopy went through the wall.
        seen = set()
        for gi in range(int((x - pad) // self.CELL),
                        int((x + pad) // self.CELL) + 1):
            for gj in range(int((y - pad) // self.CELL),
                            int((y + pad) // self.CELL) + 1):
                seen.update(self._grid.get((gi, gj), ()))
        for idx in seen:
            cx, cy, w, d, rot, z0, z1, tag = self.boxes[idx]
            if tags is not None and tag not in tags:
                continue
            # pad is a clearance in plan and deliberately does not apply here:
            # a rooftop unit standing at z1 belongs to the building, and the
            # question being asked is always "is this thing inside the walls"
            if z is not None and not (z0 - 0.5 <= z < z1):
                continue
            dx, dy = x - cx, y - cy
            if rot:
                c, s = math.cos(-rot), math.sin(-rot)
                dx, dy = dx * c - dy * s, dx * s + dy * c
            if abs(dx) <= w / 2 + pad and abs(dy) <= d / 2 + pad:
                return self.boxes[idx]
        return None

    def clear(self, x, y, z=None, pad=0.0):
        return self.hit(x, y, z, pad) is None
