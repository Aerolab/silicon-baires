import bpy, json
out={}
out["build_ffmpeg"]=bpy.app.build_options.codec_ffmpeg
out["build_openimagedenoise"]=getattr(bpy.app.build_options,"openimagedenoise",None)
out["build_openvdb"]=bpy.app.build_options.openvdb
sc=bpy.context.scene
sc.render.image_settings.media_type = "VIDEO" if hasattr(sc.render.image_settings,"media_type") else None
out["has_media_type"]=hasattr(sc.render.image_settings,"media_type")
if out["has_media_type"]:
    out["media_types"]=[i.identifier for i in sc.render.image_settings.bl_rna.properties["media_type"].enum_items]
    try:
        sc.render.image_settings.media_type="VIDEO"
        sc.render.image_settings.file_format="FFMPEG"
        out["ffmpeg_after_video"]=True
    except Exception as e: out["ffmpeg_after_video"]=str(e)[:150]
def try_set(o,p,vals):
    ok=[]
    for v in vals:
        try: setattr(o,p,v); ok.append(v)
        except Exception: pass
    return ok
sc.view_settings.view_transform="AgX"
out["looks_agx_ok"]=try_set(sc.view_settings,"look",
  ["None","AgX - Punchy","AgX - Base Contrast","AgX - Medium High Contrast","AgX - High Contrast","AgX - Greyscale","Punchy","Base Contrast"])
print("###JSON###"); print(json.dumps(out,indent=1,default=str))
