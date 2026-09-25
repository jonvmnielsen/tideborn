# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib, unreal
OUT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\cove_dump_v7_final.txt")
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m): lines.append(str(m))
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except: return ""
def sg(o,p):
    try: return o.get_editor_property(p)
    except: return "<err>"
try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log(str(e))
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    cn=cname(a); lab=label(a)
    if "PostProcess" in cn:
        s=a.get_editor_property("settings")
        log("PP white_temp=%s gain=%s bias=%s lut=%s"%(sg(s,"white_temp"),sg(s,"color_gain"),sg(s,"auto_exposure_bias"),sg(s,"color_grading_lut")))
    if "SkyLight" in cn:
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            cm=sg(c,"cubemap")
            try: cm=cm.get_path_name() if cm and cm!="<err>" else cm
            except: pass
            log("SkyLight int=%s color=%s type=%s cubemap=%s"%(sg(c,"intensity"),sg(c,"light_color"),sg(c,"source_type"),cm))
    if "DirectionalLight" in cn:
        rot=a.get_actor_rotation()
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            log("DirLight int=%s color=%s use_temp=%s temp=%s rot=(%.1f,%.1f,%.1f)"%(sg(c,"intensity"),sg(c,"light_color"),sg(c,"use_temperature"),sg(c,"temperature"),rot.pitch,rot.yaw,rot.roll))
    if "ExponentialHeightFog" in cn:
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            log("Fog density=%s"%(sg(c,"fog_density"),))
    if lab in ("TidebornEnv_SandBase","TidebornEnv_WetSand_00","TidebornEnv_Ocean","TidebornEnv_Shallows"):
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        mats=[]
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            for i in range(2):
                try:
                    m=comp.get_material(i)
                    if m: mats.append(m.get_name())
                except: break
            break
        log("%s loc=(%.0f,%.0f,%.1f) sc=(%.2f,%.2f) %s"%(lab,loc.x,loc.y,loc.z,sc.x,sc.y,",".join(mats) or "-"))
OUT.write_text("\n".join(lines)+"\n",encoding="utf-8")
log("wrote")
