"""
blib — verified helpers for headless Blender 5.2.

Built for an agent that CANNOT see the viewport: everything normally eyeballed
(framing, camera distance, light intensity) is derived here from the actual
geometry of the scene.

Usage:
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    import blib

Prefer the data API (bpy.data.*) over operators (bpy.ops.*): in background mode
operators depend on context and fail in confusing ways.
"""

import math
import os

import bpy
from mathutils import Vector

# ----------------------------------------------------------------- scene

def reset(world_color=(0.05, 0.05, 0.055), world_strength=1.0):
    """Empty, reproducible scene. Always start here."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*world_color, 1.0)
    bg.inputs["Strength"].default_value = world_strength
    sc.world = world
    return sc


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


# -------------------------------------------------------------- geometry

def bounds(objects=None):
    """(center, radius) of the bounding sphere, in world coordinates."""
    pts = _corners(objects)
    if not pts:
        return Vector((0, 0, 0)), 1.0
    lo = Vector((min(p[i] for p in pts) for i in range(3)))
    hi = Vector((max(p[i] for p in pts) for i in range(3)))
    center = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 1e-4)
    return center, radius


def _mesh_objects(objects=None):
    if objects is None:
        return [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not isinstance(objects, (list, tuple)):
        objects = [objects]
    return list(objects)


# ---------------------------------------------------------------- camera

def camera(target=None, azimuth=45, elevation=25, distance=None,
           lens=50, margin=1.25, ortho=False, shift=(0.0, 0.0)):
    """Self-framing camera.

    azimuth/elevation in degrees (orbits around the target).
    distance=None -> computed so the subject fits the frame exactly.
    margin: 1.0 = flush against the edges; 1.25 = comfortable breathing room.
    """
    center, radius = bounds(target)
    corners = _corners(target) or [center]

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = lens
    cam_data.shift_x, cam_data.shift_y = shift

    sc = bpy.context.scene
    aspect = sc.render.resolution_x / max(sc.render.resolution_y, 1)
    # cam_data.angle is the FOV of the LARGER sensor side
    if aspect >= 1:
        fov_x = cam_data.angle
        fov_y = 2 * math.atan(math.tan(fov_x / 2) / aspect)
    else:
        fov_y = cam_data.angle
        fov_x = 2 * math.atan(math.tan(fov_y / 2) * aspect)

    az, el = math.radians(azimuth), math.radians(elevation)
    direction = Vector((math.cos(el) * math.cos(az),
                        math.cos(el) * math.sin(az),
                        math.sin(el)))          # from target TOWARDS the camera

    # camera basis: it looks along -direction
    forward = -direction
    up_hint = Vector((0, 0, 1)) if abs(forward.z) < 0.999 else Vector((0, 1, 0))
    right = forward.cross(up_hint).normalized()
    up = right.cross(forward).normalized()

    # project the real geometry onto the camera axes for a tight fit, unlike
    # using the bounding sphere (which overestimates ~73% on a cube)
    ext_x = max(abs((c - center).dot(right)) for c in corners)
    ext_y = max(abs((c - center).dot(up)) for c in corners)
    depth = max((c - center).dot(-forward) for c in corners)

    if distance is None:
        distance = depth + margin * max(ext_x / math.tan(fov_x / 2),
                                        ext_y / math.tan(fov_y / 2))
    if ortho:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = 2 * margin * max(ext_x, ext_y * aspect)
        distance = max(distance, radius * 3)

    cam = link(bpy.data.objects.new("Camera", cam_data))
    cam.location = center + direction * distance
    look_at(cam, center)
    sc.camera = cam
    return cam


def _corners(objects=None):
    """Points of the EVALUATED geometry (modifiers and geometry nodes applied).

    Raw obj.bound_box returns the base mesh box: with a GN scatter extending
    past the object, framing would come out wrong.
    """
    dg = bpy.context.evaluated_depsgraph_get()
    wanted = {o.name for o in _mesh_objects(objects)}
    pts = []
    for o in _mesh_objects(objects):
        ev = o.evaluated_get(dg)
        mesh = None
        try:
            mesh = ev.to_mesh()
        except Exception:
            mesh = None
        if mesh and len(mesh.vertices):
            mw = ev.matrix_world
            verts = mesh.vertices
            step = max(1, len(verts) // 20000)   # sampling: 20k points is plenty
            pts += [mw @ verts[i].co for i in range(0, len(verts), step)]
            ev.to_mesh_clear()
        else:
            pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    # geometry nodes instances: absent from the host's evaluated mesh
    for inst in dg.object_instances:
        if inst.is_instance and inst.parent and inst.parent.original.name in wanted:
            pts.append(inst.matrix_world.translation.copy())
    return pts


def look_at(obj, target):
    target = Vector(target) if not isinstance(target, Vector) else target
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj


# ---------------------------------------------------------------- lights

def light(kind="AREA", location=(4, -4, 6), energy=500, size=3.0,
          color=(1, 1, 1), target=(0, 0, 0), angle=None):
    data = bpy.data.lights.new("Light", type=kind)
    data.energy = energy
    data.color = color
    if kind == "AREA":
        data.size = size
    elif kind == "SUN":
        data.angle = math.radians(angle if angle is not None else 3.0)
    elif kind in {"POINT", "SPOT"}:
        data.shadow_soft_size = size
    obj = link(bpy.data.objects.new("Light", data))
    obj.location = location
    if kind in {"SUN", "SPOT", "AREA"}:
        look_at(obj, target)
    return obj


def three_point(target=None, strength=1.0, key_azimuth=40, softness=1.0):
    """Key/fill/rim rig scaled to the actual size of the scene.

    Power scales with the square of the distance, so the rig works the same on
    a 1cm object and a 100m one.
    """
    center, radius = bounds(target)
    d = radius * 4
    # Empirically calibrated: with this constant an albedo 0.8 material lands
    # just below clipping under AgX. Raising it by eye blows out the highlights.
    watts = 28 * strength * (d ** 2)

    def place(az_deg, el_deg, dist):
        az, el = math.radians(az_deg), math.radians(el_deg)
        return center + Vector((
            math.cos(el) * math.cos(az),
            math.cos(el) * math.sin(az),
            math.sin(el),
        )) * dist

    key = light("AREA", place(key_azimuth, 35, d), watts, radius * 2.5 * softness, target=center)
    fill = light("AREA", place(key_azimuth + 110, 15, d * 1.1), watts * 0.25,
                 radius * 4 * softness, target=center)
    rim = light("AREA", place(key_azimuth + 200, 30, d), watts * 0.6,
                radius * 1.5 * softness, (0.95, 0.97, 1.0), target=center)
    key.name, fill.name, rim.name = "Key", "Fill", "Rim"
    return key, fill, rim


def hdri(path=None, strength=1.0, rotation=0.0, visible=True):
    """World lit by an HDRI (when a file is given) or a neutral studio grey."""
    world = bpy.context.scene.world
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    if path and os.path.exists(path):
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(path)
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Rotation"].default_value[2] = math.radians(rotation)
        coord = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    else:
        bg.inputs["Color"].default_value = (0.35, 0.36, 0.38, 1.0)
    bpy.context.scene.render.film_transparent = not visible
    return world


# ------------------------------------------------------------- materials

# Exact Principled BSDF socket names for 5.2 (verified by introspection).
# Note they changed since 3.x: there is no bare "Specular", "Subsurface",
# "Sheen", "Clearcoat" or "Transmission" any more.
def pbr(name="Material", base_color=(0.8, 0.8, 0.8), roughness=0.5, metallic=0.0,
        ior=1.5, alpha=1.0, emission=None, emission_strength=0.0,
        coat=0.0, transmission=0.0, **extra):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    _set(b, "Base Color", base_color)
    _set(b, "Roughness", roughness)
    _set(b, "Metallic", metallic)
    _set(b, "IOR", ior)
    _set(b, "Alpha", alpha)
    _set(b, "Coat Weight", coat)
    _set(b, "Transmission Weight", transmission)
    if emission is not None:
        _set(b, "Emission Color", emission)
        _set(b, "Emission Strength", emission_strength or 1.0)
    for k, v in extra.items():
        _set(b, k.replace("_", " ").title(), v)
    if alpha < 1.0 or transmission > 0:
        mat.surface_render_method = "BLENDED"
    return mat


def _set(node, socket, value):
    if socket not in node.inputs:
        raise KeyError(f"socket '{socket}' does not exist. Available: "
                       f"{[i.name for i in node.inputs]}")
    inp = node.inputs[socket]
    if hasattr(inp.default_value, "__len__") and not isinstance(value, (list, tuple)):
        value = (value, value, value, 1.0)
    elif hasattr(inp.default_value, "__len__") and len(value) == 3:
        value = (*value, 1.0)
    inp.default_value = value


def assign(obj, mat, slot=0):
    if obj.data.materials:
        obj.data.materials[slot] = mat
    else:
        obj.data.materials.append(mat)
    return obj


def emissive(name, color=(1, 1, 1), strength=5.0):
    return pbr(name, base_color=(0, 0, 0), emission=color, emission_strength=strength)


# ---------------------------------------------------------------- render

def render(path, engine="EEVEE", samples=None, resolution=(1280, 720),
           transparent=False, view_transform="AgX", look="None", exposure=0.0,
           denoise=True, gpu=True, quiet=True):
    """Render a PNG. Returns the absolute path.

    engine: "EEVEE" (fast, for iterating) | "CYCLES" (final) | "WORKBENCH" (clay)
    view_transform: "AgX" (cinematic) | "Khronos PBR Neutral" (product/web,
                    faithful colors) | "Standard" (no tone mapping) | "Filmic"
    """
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = resolution
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    sc.view_settings.view_transform = view_transform
    sc.view_settings.look = look
    sc.view_settings.exposure = exposure

    if engine.upper() in {"EEVEE", "BLENDER_EEVEE"}:
        sc.render.engine = "BLENDER_EEVEE"
        sc.eevee.taa_render_samples = samples or 64
        sc.eevee.use_raytracing = True
        sc.eevee.use_shadows = True
    elif engine.upper() == "CYCLES":
        sc.render.engine = "CYCLES"
        sc.cycles.samples = samples or 256
        sc.cycles.use_denoising = denoise
        sc.cycles.use_adaptive_sampling = True
        if gpu:
            use_gpu()
    else:
        sc.render.engine = "BLENDER_WORKBENCH"

    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if not quiet:
        print("render ->", path)
    return path


def use_gpu():
    """Metal on Apple Silicon. The first render compiles kernels (~10s), then caches."""
    prefs = bpy.context.preferences.addons.get("cycles")
    if not prefs:
        return False
    cp = prefs.preferences
    for backend in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            cp.compute_device_type = backend
            cp.get_devices()
            if any(d.type == backend for d in cp.devices):
                for d in cp.devices:
                    d.use = d.type == backend
                bpy.context.scene.cycles.device = "GPU"
                return backend
        except Exception:
            continue
    return False


def contact_sheet(path, views=(("front", 0, 5), ("three_quarter", 45, 25),
                               ("side", 90, 10), ("top", 45, 75)), **kw):
    """Several views of the same subject -> several PNGs. To check in one shot
    that the shape reads from every angle, not just the flattering one."""
    out = []
    base, ext = os.path.splitext(os.path.abspath(path))
    for name, az, el in views:
        for c in [o for o in bpy.context.scene.objects if o.type == "CAMERA"]:
            bpy.data.objects.remove(c, do_unlink=True)
        camera(azimuth=az, elevation=el)
        out.append(render(f"{base}_{name}{ext or '.png'}", **kw))
    return out


# ---------------------------------------------------------------- geometry nodes

def gn_tree(name="Nodes", inputs=(), geometry_io=True):
    """Geometry node group with its interface declared.

    inputs: [("Density", "NodeSocketFloat", 10.0), ...]
    Returns (node_group, group_input_node, group_output_node).
    """
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    if geometry_io:
        ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    for spec in inputs:
        sock_name, sock_type = spec[0], spec[1]
        s = ng.interface.new_socket(sock_name, in_out="INPUT", socket_type=sock_type)
        if len(spec) > 2:
            s.default_value = spec[2]
    gin = ng.nodes.new("NodeGroupInput"); gin.location = (-700, 0)
    gout = ng.nodes.new("NodeGroupOutput"); gout.location = (700, 0)
    return ng, gin, gout


def gn_apply(obj, node_group, name="GeometryNodes", **values):
    mod = obj.modifiers.new(name, "NODES")
    mod.node_group = node_group
    for k, v in values.items():
        gn_set(mod, k.replace("_", " "), v)
    return mod


def gn_set(mod, socket_name, value):
    """Set a modifier input by socket NAME.

    Blender 5.x changed this: it used to be mod["Socket_2"] = v (a direct
    IDProperty), now it is mod.properties.inputs["Socket_2"]["value"] = v.
    """
    ids = {s.name: s.identifier for s in mod.node_group.interface.items_tree
           if s.item_type == "SOCKET" and s.in_out == "INPUT"}
    if socket_name not in ids:
        raise KeyError(f"input '{socket_name}' does not exist. Available: {list(ids)}")
    ident = ids[socket_name]
    if hasattr(mod, "properties") and hasattr(mod.properties, "inputs"):   # 5.x
        mod.properties.inputs[ident]["value"] = value
    else:                                                                  # 4.x
        mod[ident] = value
    mod.node_group.interface_update(bpy.context)
    return mod


def sockets(node):
    """USABLE socket names of a node.

    Critical: sockets with enabled=False (for example 'Density' when
    distribute_method='POISSON') vanish from name lookup even though they
    still show up when iterating node.inputs.
    """
    return {
        "in": [i.name for i in node.inputs if i.enabled],
        "in_disabled": [i.name for i in node.inputs if not i.enabled],
        "out": [o.name for o in node.outputs if o.enabled],
    }


# ------------------------------------------------------------- animation

def turntable(obj_or_none=None, frames=60, axis="Z"):
    """Rotation keyframes 0->360 on the object (or on a parent empty)."""
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, frames
    target = obj_or_none
    if target is None:
        target = link(bpy.data.objects.new("Turntable", None))
        for o in _mesh_objects():
            if o.parent is None:
                o.parent = target
    idx = "XYZ".index(axis.upper())
    for f, ang in ((1, 0.0), (frames + 1, 2 * math.pi)):
        target.rotation_euler[idx] = ang
        target.keyframe_insert("rotation_euler", index=idx, frame=f)
    for fc in fcurves(target):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    return target


def fcurves(obj):
    """fcurve access compatible with "slotted" Actions (Blender 4.4+).

    In 5.x `action.fcurves` NO LONGER EXISTS: the curves live in
    action.layers[].strips[].channelbag(slot).fcurves
    """
    ad = getattr(obj, "animation_data", None)
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):          # Blender <= 4.3
        return list(act.fcurves)
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            if strip.type != "KEYFRAME":
                continue
            cb = strip.channelbag(ad.action_slot)
            if cb:
                out += list(cb.fcurves)
    return out


def render_video(path, fps=30, codec="H264", container="MPEG4", quality="HIGH", **kw):
    """5.x GOTCHA: media_type='VIDEO' must be set BEFORE file_format='FFMPEG'."""
    sc = bpy.context.scene
    sc.render.fps = fps
    render_kwargs = dict(kw)
    render_kwargs.setdefault("engine", "EEVEE")
    # reuse render() to leave engine/color management/resolution configured;
    # the single frame it produces is throwaway
    import tempfile
    probe = os.path.join(tempfile.mkdtemp(), "_probe.png")
    render(probe, **render_kwargs)
    try:
        os.remove(probe)
    except OSError:
        pass
    ims = sc.render.image_settings
    ims.media_type = "VIDEO"
    ims.file_format = "FFMPEG"
    sc.render.ffmpeg.format = container
    sc.render.ffmpeg.codec = codec
    sc.render.ffmpeg.constant_rate_factor = quality
    sc.render.ffmpeg.ffmpeg_preset = "GOOD"
    sc.render.filepath = os.path.abspath(path)
    bpy.ops.render.render(animation=True)
    return sc.render.filepath


# ---------------------------------------------------------------- export

def export_glb(path, selected_only=False, draco=True):
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=selected_only,
        export_draco_mesh_compression_enable=draco,
        export_apply=True,
        export_yup=True,
    )
    return path


def save(path):
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    return path


# ------------------------------------------------------------ inspection

def report():
    """What is actually in the scene. The stand-in for the outliner."""
    sc = bpy.context.scene
    lines = [f"engine={sc.render.engine} res={sc.render.resolution_x}x{sc.render.resolution_y} "
             f"view={sc.view_settings.view_transform} frames={sc.frame_start}-{sc.frame_end}"]
    for o in sc.objects:
        d = f"  {o.type:<9} {o.name:<22} loc=({o.location.x:.2f},{o.location.y:.2f},{o.location.z:.2f})"
        if o.type == "MESH":
            d += f" verts={len(o.data.vertices)} polys={len(o.data.polygons)}"
            d += f" mats={[m.name for m in o.data.materials if m]}"
            if o.modifiers:
                d += f" mods={[m.type for m in o.modifiers]}"
        elif o.type == "LIGHT":
            d += f" {o.data.type} energy={o.data.energy:.0f}"
        elif o.type == "CAMERA":
            c, r = bounds()
            d += f" lens={o.data.lens:.0f}mm dist_to_center={(o.location - c).length:.2f}"
        lines.append(d)
    c, r = bounds()
    lines.append(f"  bounds center=({c.x:.2f},{c.y:.2f},{c.z:.2f}) radius={r:.2f}")
    text = "\n".join(lines)
    print(text)
    return text
