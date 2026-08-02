import bpy, json
sc = bpy.context.scene
out = {}

def try_set(obj, prop, values):
    ok = []
    for v in values:
        try:
            setattr(obj, prop, v); ok.append(v)
        except Exception: pass
    return ok

out["engines_ok"] = try_set(sc.render, "engine", ["BLENDER_EEVEE","BLENDER_EEVEE_NEXT","BLENDER_WORKBENCH","CYCLES"])
out["view_transform_ok"] = try_set(sc.view_settings, "view_transform",
    ["Standard","Filmic","AgX","Khronos PBR Neutral","Raw","False Color"])
out["look_ok"] = try_set(sc.view_settings, "look",
    ["None","AgX - Punchy","AgX - Base Contrast","AgX - Medium High Contrast","Punchy","Medium High Contrast"])

# Cycles + GPU en Mac
sc.render.engine = "CYCLES"
cy = sc.cycles
out["cycles_device_ok"] = try_set(cy, "device", ["CPU","GPU"])
out["cycles_key_props"] = {p: getattr(cy, p, None) for p in
    ["samples","preview_samples","use_denoising","denoiser","use_adaptive_sampling","adaptive_threshold","max_bounces","time_limit"]}
prefs = bpy.context.preferences.addons.get("cycles")
if prefs:
    cp = prefs.preferences
    out["compute_device_types"] = [i.identifier for i in cp.bl_rna.properties["compute_device_type"].enum_items]
    try:
        cp.compute_device_type = "METAL"; cp.get_devices()
        out["metal_devices"] = [(d.name, d.type, d.use) for d in cp.devices]
    except Exception as e:
        out["metal_err"] = str(e)

# FFMPEG / video
try:
    sc.render.image_settings.file_format = "FFMPEG"
    out["ffmpeg_ok"] = True
except Exception as e:
    out["ffmpeg_ok"] = False; out["ffmpeg_err"] = str(e)[:120]
out["ffmpeg_containers"] = [i.identifier for i in sc.render.ffmpeg.bl_rna.properties["format"].enum_items]
out["ffmpeg_codecs"] = [i.identifier for i in sc.render.ffmpeg.bl_rna.properties["codec"].enum_items]

# glTF export: the operator's real parameters
out["gltf_params"] = sorted(p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties if p.identifier != "rna_type")
out["fbx_params_count"] = len([p for p in bpy.ops.export_scene.fbx.get_rna_type().properties])

# Modificadores y nodos utiles
out["modifier_types"] = [i.identifier for i in bpy.types.Modifier.bl_rna.properties["type"].enum_items]
print("###JSON###"); print(json.dumps(out, indent=1, default=str))
