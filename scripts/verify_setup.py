"""Environment self-check. Run with: ./bl scripts/verify_setup.py

Exercises every critical path and validates the results, not merely that
nothing raised. Includes the check that matters most when working without a
viewport: that the render actually contains an image and is not a black frame.
"""
import sys, pathlib, time, os, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import bpy

RESULTS = []


def check(name):
    def deco(fn):
        t0 = time.time()
        try:
            detail = fn() or ""
            RESULTS.append(("PASS", name, f"{time.time() - t0:.1f}s {detail}"))
        except Exception as e:
            RESULTS.append(("FAIL", name, f"{type(e).__name__}: {e}"))
        return fn
    return deco


def brightness(png):
    """Mean luminance of a PNG. Catches the black render, which raises nothing."""
    img = bpy.data.images.load(png)
    px = list(img.pixels)
    n = len(px) // 4
    mean = sum(px[i * 4 + 0] + px[i * 4 + 1] + px[i * 4 + 2] for i in range(n)) / (3 * n)
    spread = max(px[:4000] or [0]) - min(px[:4000] or [0])
    bpy.data.images.remove(img)
    return mean, spread


TMP = tempfile.mkdtemp(prefix="blib_verify_")

# ---------------------------------------------------------------------------

@check("Blender 5.x")
def _():
    v = bpy.app.version
    assert v[0] >= 5, f"expected Blender 5.x, found {bpy.app.version_string}"
    return bpy.app.version_string


@check("import blib")
def _():
    import blib
    assert hasattr(blib, "camera") and hasattr(blib, "render")
    return f"{len([x for x in dir(blib) if not x.startswith('_')])} symbols"


@check("scene + automatic framing")
def _():
    import blib
    blib.reset()
    bpy.ops.mesh.primitive_monkey_add(size=0.04)      # deliberately tiny object
    blib.assign(bpy.context.object, blib.pbr("T", (0.8, 0.3, 0.2), roughness=0.3))
    blib.three_point()
    cam = blib.camera(azimuth=40, elevation=20)
    center, radius = blib.bounds()
    d = (cam.location - center).length
    assert 1.5 * radius < d < 12 * radius, f"camera at odd distance: {d:.3f} (radius {radius:.3f})"
    return f"radius={radius:.3f} dist={d:.3f}"


@check("EEVEE render with real image")
def _():
    import blib
    p = blib.render(f"{TMP}/eevee.png", "EEVEE", resolution=(320, 240))
    assert os.path.getsize(p) > 2000, "PNG suspiciously small"
    mean, spread = brightness(p)
    assert mean > 0.02, f"render nearly black (mean luminance {mean:.3f}): missing lights or camera"
    assert mean < 0.97, f"render blown out (mean luminance {mean:.3f})"
    assert spread > 0.01, "flat image: a single color across the frame"
    return f"luminance={mean:.2f}"


@check("Cycles + GPU")
def _():
    import blib
    backend = blib.use_gpu()
    p = blib.render(f"{TMP}/cycles.png", "CYCLES", samples=16, resolution=(240, 180))
    mean, _ = brightness(p)
    assert mean > 0.02, "Cycles render is black"
    return f"backend={backend or 'CPU'}"


@check("geometry nodes (incl. 5.x gn_set)")
def _():
    import blib
    blib.reset()
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1)
    host = bpy.context.object
    ng, gin, gout = blib.gn_tree("V", inputs=[("Density", "NodeSocketFloat", 50.0)])
    dist = ng.nodes.new("GeometryNodeDistributePointsOnFaces")
    dist.distribute_method = "POISSON"
    inst = ng.nodes.new("GeometryNodeInstanceOnPoints")
    ico = ng.nodes.new("GeometryNodeMeshIcoSphere")
    ico.inputs["Radius"].default_value = 0.08
    L = ng.links.new
    L(gin.outputs["Geometry"], dist.inputs["Mesh"])
    L(gin.outputs["Density"], dist.inputs["Density Max"])
    L(dist.outputs["Points"], inst.inputs["Points"])
    L(ico.outputs["Mesh"], inst.inputs["Instance"])
    L(inst.outputs["Instances"], gout.inputs["Geometry"])
    mod = blib.gn_apply(host, ng, Density=200.0)
    dg = bpy.context.evaluated_depsgraph_get()
    n_inst = sum(1 for i in dg.object_instances if i.is_instance)
    assert n_inst > 10, f"the scatter produced {n_inst} instances, something did not evaluate"
    s = blib.sockets(dist)
    assert "Density" in s["in_disabled"], "disabled-socket behaviour changed"
    return f"{n_inst} instances"


@check("animation + FFMPEG video")
def _():
    import blib
    blib.reset()
    bpy.ops.mesh.primitive_cube_add(size=1)
    blib.three_point(); blib.camera()
    tt = blib.turntable(frames=4)
    assert len(blib.fcurves(tt)) > 0, "no fcurves: check the slotted Actions API"
    out = blib.render_video(f"{TMP}/v.mp4", fps=12, resolution=(160, 120),
                            engine="EEVEE", samples=8)
    assert os.path.getsize(out) > 1000, "the mp4 came out empty"
    return f"{os.path.getsize(out) // 1024} KB"


@check("glTF export with Draco")
def _():
    import blib
    p = blib.export_glb(f"{TMP}/m.glb")
    assert os.path.getsize(p) > 500, "empty glb"
    with open(p, "rb") as f:
        assert f.read(4) == b"glTF", "missing the glTF magic bytes"
    return f"{os.path.getsize(p)} bytes"


@check("skills present")
def _():
    root = pathlib.Path(__file__).resolve().parents[1]
    sk = root / ".claude" / "skills"
    found = sorted(p.name for p in sk.iterdir() if (p / "SKILL.md").exists())
    assert "blender" in found, "the blender skill is missing"
    return ", ".join(found)


# ---------------------------------------------------------------------------

print("\n" + "=" * 72)
fails = 0
for status, name, detail in RESULTS:
    if status == "FAIL":
        fails += 1
    print(f"  [{status}] {name:<40} {detail}")
print("=" * 72)
print(f"  {len(RESULTS) - fails}/{len(RESULTS)} OK" + ("  -> ENVIRONMENT READY" if not fails else "  -> FAILURES PRESENT"))
print("=" * 72 + "\n")
sys.exit(1 if fails else 0)
