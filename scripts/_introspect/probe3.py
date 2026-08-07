import bpy, json, time, math
out={}
sc=bpy.context.scene
# 1) FFMPEG before anything else
try:
    sc.render.image_settings.file_format="FFMPEG"; out["ffmpeg_first"]=True
except Exception as e: out["ffmpeg_first"]=str(e)[:100]
sc.render.image_settings.file_format="PNG"
# 2) looks bajo AgX
sc.view_settings.view_transform="AgX"
out["looks_agx"]=[i.identifier for i in sc.view_settings.bl_rna.properties["look"].enum_items]
sc.view_settings.view_transform="Khronos PBR Neutral"
out["looks_pbrneutral"]=[i.identifier for i in sc.view_settings.bl_rna.properties["look"].enum_items]

# 3) benchmark: misma escena, 3 configs
def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_monkey_add(location=(0,0,1)); bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_plane_add(size=20)
    bpy.ops.object.light_add(type='AREA', location=(4,-4,6)); bpy.context.object.data.energy=800
    bpy.ops.object.camera_add(location=(6,-6,4), rotation=(math.radians(63),0,math.radians(45)))
    bpy.context.scene.camera=bpy.context.object
    s=bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = 960, 540
    s.render.filepath="/tmp/bench.png"
    return s

def bench(name, cfg):
    s=build(); cfg(s); t=time.time(); bpy.ops.render.render(write_still=True)
    return round(time.time()-t,2)

def eevee(s):
    s.render.engine="BLENDER_EEVEE"; s.eevee.taa_render_samples=64
def cyc_gpu(s, n):
    s.render.engine="CYCLES"; s.cycles.device="GPU"; s.cycles.samples=n; s.cycles.use_denoising=True
    prefs=bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type="METAL"; prefs.get_devices()
    for d in prefs.devices: d.use = (d.type=="METAL")
def cyc_cpu(s, n):
    s.render.engine="CYCLES"; s.cycles.device="CPU"; s.cycles.samples=n; s.cycles.use_denoising=True

out["t_eevee_64spp_960x540"]=bench("eevee", eevee)
out["t_cycles_gpu_128spp"]=bench("cg", lambda s: cyc_gpu(s,128))
out["t_cycles_gpu_512spp"]=bench("cg5", lambda s: cyc_gpu(s,512))
out["t_cycles_cpu_128spp"]=bench("cc", lambda s: cyc_cpu(s,128))
print("###JSON###"); print(json.dumps(out, indent=1, default=str))
