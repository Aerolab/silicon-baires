"""Step 20 — publish the city to the web build.

Everything `web/` draws comes out of this one script, so the browser can never
disagree with the .blend about anything: it does not know the palette, the
grade, the camera move or the traffic, it is handed all four.

    ./bl scripts/city/20_export_web.py

It writes four files into `web/public/`:

    city.glb          the geometry, at frame 1. Z-up, NOT y-up, on purpose:
                      every other number here is in Blender's coordinates and
                      one conversion in one place beats four in four.
    city_shot.json    the numbers - the camera move sampled per frame, the
                      grade, the sun, the compositor's knobs, and a stamp the
                      browser uses to bust its own cache
    city_motion.json  world-space keys for everything that moves
    city_sky.exr      the world, baked equirectangular, for the ambient

WHY THE MOTION IS A FILE AND NOT glTF ANIMATION. Step 11 gives almost every
object exactly TWO linear keyframes, so a 1784-object glTF animation track
would be a large encoding of two numbers each, and glTF cannot say "linear"
without sampling it. Read at both ends and lerped in the browser it is not an
approximation of the move: it is the same move, and `check_motion` proves that
against Blender at three frames it did not sample.

THE NAMES ARE THE JOINT. `city_motion.json` addresses objects by name and the
browser looks them up in the glb, so a name the exporter rewrites is an object
that silently stops moving. Checked here, against the glb that was just
written, rather than noticed later as a city where the buses are parked.
"""
import sys, pathlib, math, json, struct, os

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "city"))
import bpy, blib
from mathutils import Quaternion, Vector
from _common import (FPS, FRAMES, MOVE, AZIMUTH, ELEVATION, DISTANCE,
                     HERO_WIDTH, ASPECT, SHOT_ZOOM, EASE_IN, EASE_OUT,
                     LOOK, EXPOSURE, WHITE_BALANCE, SUN_ENERGY, SUN_ANGLE,
                     SUN_COLOR, SKY_STRENGTH, SKY_SATURATION,
                     shot_at, open_city, R, SOLIDS)

WEB = ROOT / "web" / "public"

# The compositor's knobs, imported rather than re-typed: 07_look owns them and
# the browser's post chain is the same chain. Kept as a literal import through
# runpy because 07_look.py is not an importable module name.
LOOK_PY = ROOT / "scripts" / "city" / "07_look.py"

SKY_RES = 512               # equirect width. The sky has no detail in it


def look_numbers():
    """FOCUS_D, F_STOP, BLUR_MAX, FOCUS_SPREAD, GRAIN, VIGNETTE from 07_look.

    Read out of the source rather than copied, because a second copy of
    BLUR_MAX is exactly the failure this project keeps writing shared-number
    comments about. 07_look cannot be imported (the name starts with a digit),
    so its module-level assignments are compiled and exec'd with a stub bpy
    already in sys.modules - it never runs main().
    """
    src = LOOK_PY.read_text()
    body, ns = [], {}
    for line in src.splitlines():
        if line.startswith(("FOCUS_D", "F_STOP", "BLUR_MAX", "FOCUS_SPREAD",
                            "GRAIN", "VIGNETTE")):
            body.append(line)
    exec("\n".join(body), {"DISTANCE": DISTANCE, "HERO_WIDTH": HERO_WIDTH}, ns)
    want = ("FOCUS_D", "F_STOP", "BLUR_MAX", "FOCUS_SPREAD", "GRAIN",
            "VIGNETTE")
    missing = [k for k in want if k not in ns]
    if missing:
        raise SystemExit(f"\n  07_look.py no longer defines {missing}.\n"
                         f"  The web post chain reads its numbers from there.\n")
    return {k: ns[k] for k in want}


def sun_direction():
    """Which way the sun points, straight off the object the render uses."""
    sun = bpy.data.objects["Sun"]
    d = sun.matrix_world.to_quaternion() @ blib.Vector((0.0, 0.0, -1.0)) \
        if hasattr(blib, "Vector") else None
    if d is None:
        from mathutils import Vector
        d = sun.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    return tuple(round(v, 6) for v in d), tuple(round(v, 4)
                                                for v in sun.location)


def bake_sky(path):
    """Render the world, and nothing else, to an equirectangular EXR.

    The browser gets the actual sky - strength, desaturation and all - instead
    of a guess at two colours. It is the ambient light as well as the
    background: three.js runs it through PMREM and lights the city with it,
    which is the closest thing to Cycles' sky fill that a rasteriser has.
    """
    scene = bpy.context.scene
    keep = (scene.render.engine, scene.render.resolution_x,
            scene.render.resolution_y, scene.render.filepath,
            scene.render.image_settings.file_format,
            scene.render.film_transparent, scene.camera,
            scene.view_settings.view_transform, scene.view_settings.look,
            scene.view_settings.exposure, scene.frame_current)
    excluded = []

    cam_data = bpy.data.cameras.new("SkyCam")
    cam_data.type = "PANO"
    cam_data.panorama_type = "EQUIRECTANGULAR"
    cam = bpy.data.objects.new("SkyCam", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (0.0, 0.0, 60.0)
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    scene.camera = cam

    # Hide the city: this is the sky on its own, not the sky with a city in it.
    view_layer = bpy.context.view_layer
    for lc in view_layer.layer_collection.children:
        excluded.append((lc, lc.exclude))
        lc.exclude = True

    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.render.resolution_x = SKY_RES
    scene.render.resolution_y = SKY_RES // 2
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_depth = "16"
    # RAW, not AgX: this is light being handed to a renderer, not an image
    # being handed to an eye. Tone mapping happens once, in the browser.
    scene.view_settings.view_transform = "Raw"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)

    for lc, was in excluded:
        lc.exclude = was
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cam_data)
    (scene.render.engine, scene.render.resolution_x, scene.render.resolution_y,
     scene.render.filepath, scene.render.image_settings.file_format,
     scene.render.film_transparent, scene.camera,
     scene.view_settings.view_transform, scene.view_settings.look,
     scene.view_settings.exposure, frame) = keep
    scene.frame_set(frame)


def cull_closed_materials():
    """Turn on backface culling for every material whose meshes are closed.

    THE BIGGEST SINGLE PERFORMANCE NUMBER IN THE WHOLE PORT, and it comes from
    a checkbox nobody ever ticked. Blender ships with backface culling off in
    the material settings — it costs nothing in Cycles, which does not
    rasterise — so the glTF exporter writes doubleSided on all 180 materials
    and the browser dutifully draws the inside of every building, car and tree
    as well as the outside. Turning it off across the board took the page from
    12 fps to 36.

    IT CANNOT BE DONE ACROSS THE BOARD. The Floralis' petals are open shells,
    one quad thick with nothing behind them, and culled they lose their inner
    surface: the flower goes hollow. So the question is asked of the geometry
    rather than answered by preference — a material is culled only when every
    mesh using it is closed, meaning every edge has exactly two faces.

    Done here, in memory, on the way out. The .blend is not saved, so this
    never becomes a look decision hidden in a viewport setting.
    """
    import bmesh
    # PER MATERIAL, NOT PER MESH, and the difference is most of the saving.
    # The site is one mesh carrying the asphalt, the pavements, the lawns and
    # the kerbs between them: it is neither closed nor flat, so asked as a
    # whole it answers "double-sided" and every road pixel - which from this
    # camera is most of the frame - gets drawn twice. Asked per material, the
    # asphalt is a flat sheet facing the sky and the kerb is not.
    safe = {}                        # (mesh name, material index) -> bool
    for me in bpy.data.meshes:
        bm = bmesh.new()
        bm.from_mesh(me)
        solid = all(len(e.link_faces) == 2 for e in bm.edges)
        by_slot = {}
        for f in bm.faces:
            by_slot.setdefault(f.material_index, []).append(f.normal.z > 0.05)
        for slot, ups in by_slot.items():
            safe[(me.name, slot)] = solid or all(ups)
        bm.free()

    used_by = {}
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH":
            continue
        for i, slot in enumerate(ob.data.materials):
            if slot:
                used_by.setdefault(slot.name, set()).add((ob.data.name, i))

    culled, open_ = [], []
    for name, uses in used_by.items():
        mat = bpy.data.materials[name]
        # A slot with no faces in a given mesh is not evidence either way.
        mat.use_backface_culling = all(safe.get(u, True) for u in uses)
        (culled if mat.use_backface_culling else open_).append(name)
    print(f"  backface culling: {len(culled)} materials on, {len(open_)} off "
          f"(open geometry: {', '.join(sorted(open_)[:4])}"
          f"{'…' if len(open_) > 4 else ''})")


def built_bounds():
    """The rectangle the city actually occupies, and how tall it gets.

    NOT the bounding box of the scene: step 03 lays a sheet of ground well past
    the last block, so a scene bbox is mostly bare site. This is the extent of
    the SOLIDS — every footprint steps 04, 06, 06b, 08 and 10 published — which
    is the same table `05_life` uses to decide where the city is, and it is
    what the browser fences free navigation to.
    """
    boxes = json.loads(SOLIDS.read_text())["boxes"]
    xs, ys, top = [], [], 0.0
    for cx, cy, w, d, rot, z0, z1, tag in boxes:
        # The half-extent of a rotated rectangle, projected on each axis.
        c, s = abs(math.cos(rot)), abs(math.sin(rot))
        hx, hy = (w * c + d * s) / 2.0, (w * s + d * c) / 2.0
        xs += [cx - hx, cx + hx]
        ys += [cy - hy, cy + hy]
        top = max(top, z1)
    return {"x": [round(min(xs), 2), round(max(xs), 2)],
            "y": [round(min(ys), 2), round(max(ys), 2)],
            "top": round(top, 2), "boxes": len(boxes)}


def glb_node_names(path):
    """The node names the exporter actually wrote. See THE NAMES ARE THE JOINT."""
    data = path.read_bytes()
    length = struct.unpack("<I", data[12:16])[0]
    doc = json.loads(data[20:20 + length])
    return {n.get("name") for n in doc.get("nodes", [])}, doc


def _wxyz(q):
    """(x,y,z,w) as the file stores it -> (w,x,y,z) as mathutils wants it."""
    return (q[3], q[0], q[1], q[2])


def sample_world(scene, objects, frame):
    """(position, quaternion) of each object at this frame, in WORLD space."""
    scene.frame_set(frame)
    out = {}
    for o in objects:
        loc, quat, _ = o.matrix_world.decompose()
        out[o.name] = (tuple(loc), (quat.x, quat.y, quat.z, quat.w))
    return out


def collect_motion(scene):
    """Every animated object, as world-space keys the browser can interpolate.

    WORLD SPACE, AND NOT THE OBJECT'S OWN location/rotation_euler. Three things
    broke when this read the local transform, and only one of them was visible
    as an error:

      THE ROTATION IS USUALLY NOT ANIMATED AT ALL. Step 11 keyframes location
      and nothing else for a car, because a car does not turn: its heading is a
      static 0 or 90 degrees set when step 05 placed it. Exporting rotation
      only when it CHANGES therefore told the browser nothing about the heading
      of every car in the city, and half of them drove sideways down the
      avenue at a perfectly plausible speed.

      SOME OBJECTS HAVE A PARENT. Heli.rotor hangs off Heli.fly, so its local
      transform is meaningless on its own - the glb has the hierarchy flattened
      into instances, and the browser needs the flattened answer too.

      QUATERNIONS DO NOT CARE ABOUT rotation_mode. Reading euler angles is
      reading one of several representations the .blend may or may not be using.

    THE SAMPLING IS ADAPTIVE. Almost everything gets two keys, because step 11
    gives almost everything two linear keyframes and a lerp between them is not
    an approximation of that, it is the same motion. The rotor is the exception
    - it turns 26 times, and two keys of a quaternion cannot say "26 turns",
    they say "back where you started". Anything that rotates more than a
    quarter turn between its keys gets sampled until no segment does.
    """
    # MESH only. The camera is animated too and it is deliberately not in the
    # glb - the browser flies the move from the track table instead - so
    # sweeping up "everything with an action" hands the name check a HeroCam
    # it can never find.
    animated = [o for o in scene.objects
                if o.type == "MESH" and o.animation_data
                and o.animation_data.action]
    scale = {}
    scene.frame_set(1)
    for o in animated:
        scale[o.name] = tuple(o.matrix_world.decompose()[2])

    ends = [sample_world(scene, animated, 1),
            sample_world(scene, animated, FRAMES)]

    def angle_between(qa, qb):
        d = abs(sum(a * b for a, b in zip(qa, qb)))
        return 2.0 * math.acos(min(1.0, d))

    # WHO NEEDS MORE THAN THE TWO ENDS, and the answer is not "whoever ends up
    # far from where they started". The rotor turns EXACTLY 26 times, so it
    # ends where it began and a comparison of the two ends says it never moved:
    # first version of this check passed it with two keys and the browser drew
    # a helicopter with a rotor welded in place. Ask the curves instead: how
    # far the value travels, not where it lands.
    LIMIT = math.pi / 2

    def turns_far(o):
        if angle_between(ends[0][o.name][1], ends[1][o.name][1]) > LIMIT:
            return True
        for fc in blib.fcurves(o):
            if "rotation" not in fc.data_path:
                continue
            ys = [k.co.y for k in fc.keyframe_points]
            if len(ys) > 2 or (ys and max(ys) - min(ys) > LIMIT):
                return True
        return False

    dense = [o for o in animated if turns_far(o)]

    frames = {1: ends[0], FRAMES: ends[1]}

    # ANYTHING THAT DOES NOT MOVE AT A CONSTANT SPEED KEEPS ITS OWN KEYS, and
    # the crossing pedestrians are the first things in this city that do not.
    # They wait at the kerb, walk across when the traffic gives them a gap, and
    # stop on the far pavement - four keyframes, and the two ends of that are
    # "on one pavement" and "on the other". Exported as two keys the browser
    # would walk them slowly and evenly from one to the other across the whole
    # shot, straight through the traffic they were timed to avoid: the exact
    # defect this was written to fix, reappearing only in the browser.
    #
    # Their own break frames, not a denser global grid. The grid is shared by
    # every object in `frames`, so resolving a walk that starts at frame 143
    # would cost every densely-sampled object a key every few frames too.
    # grouped by frame, not by object: one frame_set evaluates the whole
    # depsgraph, and there are 7600 objects in this scene
    breaks = {}
    for o in animated:
        marks = set()
        for fc in blib.fcurves(o):
            if not fc.data_path.endswith("location"):
                continue
            marks.update(int(round(k.co.x)) for k in fc.keyframe_points)
        for f in marks - {1, FRAMES}:
            breaks.setdefault(f, []).append(o)
    for f in sorted(breaks):
        frames.setdefault(f, {}).update(sample_world(scene, breaks[f], f))
    if breaks:
        print(f"  {sum(len(v) for v in breaks.values())} extra keys for "
              f"{len({o.name for v in breaks.values() for o in v})} objects "
              f"that stop and start (the pedestrians waiting to cross)")

    if dense:
        # SUBDIVIDE UNTIL THE MIDPOINT AGREES, not until the ends are close
        # together. The distance between two quaternions cannot tell "did not
        # move" from "went round thirteen times", which is how the second
        # version of this check settled on a key every 312 frames for a rotor
        # turning once a second. Sampling the middle of a segment and asking
        # whether the slerp would have found it is a question aliasing cannot
        # answer wrongly.
        TOL = math.radians(5.0)
        step = FRAMES - 1
        while step > 1:
            step = max(1, step // 2)
            marks = sorted(set(range(1, FRAMES + 1, step)) | {FRAMES})
            for f in marks:
                # `f in frames` is no longer the same question as "the dense
                # objects are sampled at f": the pedestrians' break frames put
                # entries in `frames` holding one walker and nothing else, and
                # the slerp below would then KeyError on the rotor
                if any(o.name not in frames.get(f, {}) for o in dense):
                    frames.setdefault(f, {}).update(
                        sample_world(scene, dense, f))
            worst = 0.0
            for a, b in zip(marks, marks[1:]):
                mid = (a + b) // 2
                if mid in (a, b):
                    continue
                probe = sample_world(scene, dense, mid)
                for o in dense:
                    qa = Quaternion(_wxyz(frames[a][o.name][1]))
                    qb = Quaternion(_wxyz(frames[b][o.name][1]))
                    qm = Quaternion(_wxyz(probe[o.name][1]))
                    worst = max(worst, qa.slerp(qb, 0.5).rotation_difference(qm).angle)
            if worst <= TOL:
                break
        print(f"  {len(dense)} object(s) turn far enough to need dense keys "
              f"(every {step} frames): {', '.join(o.name for o in dense[:4])}")
    scene.frame_set(1)

    marks = sorted(frames)
    out = []
    for o in sorted(animated, key=lambda o: o.name):
        n = o.name
        keys = [[f, [round(v, 3) for v in frames[f][n][0]],
                 [round(v, 5) for v in frames[f][n][1]]]
                for f in marks if n in frames[f]]
        e = {"n": n, "k": keys}
        s = scale[n]
        if any(abs(v - 1.0) > 1e-4 for v in s):
            e["s"] = [round(v, 5) for v in s]
        out.append(e)
    return out, len(animated), len(dense)


def check_motion(scene, motion):
    """Does the browser's interpolation land where Blender does?

    The whole file is a bet that lerp plus slerp reproduces step 11's
    keyframes. Nothing about a wrong bet looks wrong - the city simply moves
    slightly differently than it renders - so the bet is measured here, at
    three frames nobody sampled, against Blender itself.
    """

    index = {e["n"]: e["k"] for e in motion}
    worst_p, worst_a, worst_name = 0.0, 0.0, ""
    for frame in (int(FRAMES * 0.25), int(FRAMES * 0.5), int(FRAMES * 0.77)):
        scene.frame_set(frame)
        for o in scene.objects:
            keys = index.get(o.name)
            if not keys:
                continue
            i = max(i for i in range(len(keys)) if keys[i][0] <= frame)
            i = min(i, len(keys) - 2)
            (fa, pa, qa), (fb, pb, qb) = keys[i], keys[i + 1]
            t = (frame - fa) / (fb - fa)
            p = Vector(pa).lerp(Vector(pb), t)
            q = Quaternion((qa[3], qa[0], qa[1], qa[2])).slerp(
                Quaternion((qb[3], qb[0], qb[1], qb[2])), t)
            loc, quat, _ = o.matrix_world.decompose()
            dp = (loc - p).length
            da = math.degrees(quat.rotation_difference(q).angle)
            if dp > worst_p:
                worst_p, worst_name = dp, o.name
            worst_a = max(worst_a, da)
    scene.frame_set(1)
    print(f"  interpolation vs Blender: worst {worst_p * 100:.1f} cm "
          f"({worst_name}), {worst_a:.1f} deg")
    if worst_p > 0.25 or worst_a > 5.0:
        raise SystemExit(
            f"\n  the browser would not follow the .blend: {worst_p:.2f} m / "
            f"{worst_a:.1f} deg off at mid-shot.\n"
            f"  Something in the scene is animated with curves two keys "
            f"cannot describe.\n")


def main():
    scene = open_city(needs_collections=("BUILDINGS", "TITLE", "TRAFFIC"),
                      hint="run the whole chain from 03_ground.py, then 11 and 12")
    WEB.mkdir(parents=True, exist_ok=True)
    scene.frame_set(1)

    # --- the geometry ------------------------------------------------------
    cull_closed_materials()
    glb = WEB / "city.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(glb),
        export_format="GLB",
        export_apply=True,
        export_yup=False,             # Z-up, like every other number here
        export_cameras=False,
        export_lights=False,
        export_animations=False,      # see the docstring: motion is a file
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
    )
    names, doc = glb_node_names(glb)
    meshes = len(doc.get("meshes", []))
    print(f"  city.glb        {glb.stat().st_size / 1e6:6.2f} MB  "
          f"{len(doc.get('nodes', []))} nodes, {meshes} meshes, "
          f"{len(doc.get('materials', []))} materials")

    # --- the motion --------------------------------------------------------
    motion, total, dense = collect_motion(scene)
    check_motion(scene, motion)
    lost = [e["n"] for e in motion if e["n"] not in names]
    if lost:
        raise SystemExit(
            f"\n  {len(lost)} animated objects are not in the glb under the "
            f"name the motion file uses.\n  first few: {lost[:5]}\n"
            f"  The browser looks them up by name, so they would silently "
            f"stand still.\n")
    (WEB / "city_motion.json").write_text(json.dumps(motion, separators=(",", ":")))
    keys = sum(len(e["k"]) for e in motion)
    print(f"  city_motion.json{(WEB / 'city_motion.json').stat().st_size / 1e6:6.2f} MB  "
          f"{len(motion)} objects, {keys} keys, {dense} densely sampled")

    # --- the numbers -------------------------------------------------------
    direction, position = sun_direction()
    shot = [[round(w, 4), round(t[0], 4), round(t[1], 4)]
            for w, t in (shot_at(f) for f in range(1, FRAMES + 1))]
    # A version stamp, so a re-export cannot be masked by the browser cache.
    # city_shot.json is fetched with no-store and everything else is fetched
    # with ?v=<stamp>, which changes exactly when the files do. Half an hour
    # went into a bug that was a cached copy of the previous motion file.
    stamp = str(int(max(glb.stat().st_mtime,
                        (WEB / "city_motion.json").stat().st_mtime)))
    payload = {
        "generated_by": "scripts/city/20_export_web.py",
        "stamp": stamp,
        "shot": {
            "fps": FPS, "frames": FRAMES, "move": MOVE,
            "azimuth": AZIMUTH, "elevation": ELEVATION, "distance": DISTANCE,
            "hero_width": HERO_WIDTH, "aspect": ASPECT, "zoom": SHOT_ZOOM,
            "ease": [EASE_IN, EASE_OUT],
            # width, target x, target y - one row per frame. Sampled here so
            # the browser cannot re-derive the easing and get it wrong.
            "track": shot,
        },
        "grade": {
            "view_transform": "AgX", "look": LOOK, "exposure": EXPOSURE,
            "white_balance": WHITE_BALANCE,
        },
        "sun": {
            "energy": SUN_ENERGY, "angle": SUN_ANGLE, "color": list(SUN_COLOR),
            "direction": list(direction), "position": list(position),
        },
        "sky": {"strength": SKY_STRENGTH, "saturation": SKY_SATURATION,
                "file": "city_sky.exr"},
        # Where the built city is, so free navigation can be fenced to it.
        "bounds": built_bounds(),
        "post": look_numbers(),
    }
    (WEB / "city_shot.json").write_text(json.dumps(payload, indent=1))
    b = payload["bounds"]
    print(f"  city_shot.json        {len(shot)} camera frames, "
          f"grade + sun + post")
    print(f"                        built area {b['x'][1] - b['x'][0]:.0f} x "
          f"{b['y'][1] - b['y'][0]:.0f} m from {b['boxes']} footprints, "
          f"top {b['top']:.0f} m")

    # --- the sky -----------------------------------------------------------
    sky = WEB / "city_sky.exr"
    bake_sky(sky)
    print(f"  city_sky.exr    {sky.stat().st_size / 1e6:6.2f} MB  "
          f"{SKY_RES}x{SKY_RES // 2} equirectangular")

    # NOT save_city(): this step reads the city and writes somewhere else. It
    # is the only one, and saving here would put a SkyCam in the .blend.
    print("\n  the .blend is untouched. Now: cd web && npm install && npm run dev")


main()
