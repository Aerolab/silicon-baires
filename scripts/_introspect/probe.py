import bpy, json, sys

out = {}
out["version"] = bpy.app.version_string
out["python"] = sys.version.split()[0]

def enum_of(struct, prop):
    try:
        return [i.identifier for i in struct.bl_rna.properties[prop].enum_items]
    except Exception as e:
        return f"ERR {e}"

sc = bpy.context.scene
out["render_engines"] = enum_of(sc.render, "engine")
out["image_formats"] = enum_of(sc.render.image_settings, "file_format")
out["view_transforms"] = enum_of(sc.view_settings, "view_transform")
out["looks"] = enum_of(sc.view_settings, "look")[:12]

# EEVEE props
out["eevee_props"] = sorted(p.identifier for p in sc.eevee.bl_rna.properties if not p.is_readonly)
# Cycles?
out["has_cycles"] = hasattr(sc, "cycles")
if hasattr(sc, "cycles"):
    out["cycles_props_sample"] = sorted(p.identifier for p in sc.cycles.bl_rna.properties if not p.is_readonly)

# Principled BSDF sockets (nombres exactos)
mat = bpy.data.materials.new("probe"); mat.use_nodes = True
n = mat.node_tree.nodes.get("Principled BSDF")
out["principled_inputs"] = [i.name for i in n.inputs] if n else "NOT FOUND"
out["shader_node_types"] = sorted(t for t in dir(bpy.types) if t.startswith("ShaderNode"))

# Geometry nodes
out["geo_node_types_count"] = len([t for t in dir(bpy.types) if t.startswith("GeometryNode")])
out["geo_node_types"] = sorted(t for t in dir(bpy.types) if t.startswith("GeometryNode"))

# Addons / exportadores disponibles
out["has_gltf_export"] = hasattr(bpy.ops.export_scene, "gltf")
out["export_scene_ops"] = [o for o in dir(bpy.ops.export_scene)]
out["import_scene_ops"] = [o for o in dir(bpy.ops.import_scene)]
out["wm_import_ops"] = [o for o in dir(bpy.ops.wm) if o.startswith(("obj_","stl_","ply_","usd_","alembic_","grease_"))]

print("###JSON###")
print(json.dumps(out, indent=1))
