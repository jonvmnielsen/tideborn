# -*- coding: utf-8 -*-
"""v9i: re-clamp Ocean/Shallows/WetSand after stale bounds; keep sky wall."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_living_v9i_result.txt"
MAT="/Game/Tideborn/Art/Materials"
MAP="/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V9i] "+t); lines.append(t)
def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except: return ""
def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if p and unreal.EditorAssetLibrary.does_asset_exist(p) else None
def force_apply(a,mat):
    if not a or not mat: return
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(16):
            try: comp.set_material(i,mat)
            except: break
def unhide(a):
    try:
        a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False)
        root=a.root_component
        if root:
            try: root.set_visibility(True,True)
            except: pass
    except: pass
def hide(a):
    try:
        a.set_actor_hidden_in_game(True); a.set_is_temporarily_hidden_in_editor(True)
        root=a.root_component
        if root:
            try: root.set_visibility(False,True)
            except: pass
    except: pass

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log(str(e))
sand=load(MAT+"/MI_Tideborn_SandWarm")
wet_dark=load(MAT+"/MI_Tideborn_SandWet")
wet_mid=load(MAT+"/MI_Tideborn_SandWetMid")
water=load(MAT+"/M_Tideborn_WaterOpaque")

for a in actors():
    lab=label(a); cn=cname(a)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1))
        if sand: force_apply(a,sand); log("LOCK SandBase")
    elif lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000,-1200,99),False,True)
        a.set_actor_scale3d(unreal.Vector(95,14,1)); force_apply(a,water); unhide(a)
        log("Ocean Y~[-1900..-500]")
    elif lab=="TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000,50,100),False,True)
        a.set_actor_scale3d(unreal.Vector(80,9,1)); force_apply(a,water); unhide(a)
        log("Shallows Y~[-400..500]")
    elif lab=="TidebornEnv_WetSand_00":
        a.set_actor_location(unreal.Vector(1000,680,105.5),False,True)
        a.set_actor_scale3d(unreal.Vector(34,1.4,1)); force_apply(a,wet_dark)
        log("Wet00")
    elif lab=="TidebornEnv_WetSand_01":
        a.set_actor_location(unreal.Vector(1000,740,105.9),False,True)
        a.set_actor_scale3d(unreal.Vector(32,1.3,1)); force_apply(a,wet_mid)
    elif lab=="TidebornEnv_SkyDome" or "SkyDome" in lab:
        hide(a)
    elif "SkyAtmosphere" in cn or "VolumetricCloud" in cn or "ExponentialHeightFog" in cn:
        unhide(a)
    elif "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.recapture_sky()
            except: pass
    elif "DirectionalLight" in cn:
        a.set_actor_rotation(unreal.Rotator(pitch=-30,yaw=-90,roll=0),False)

for a in actors():
    lab=label(a)
    if any(k in lab for k in ("SandBase","Ocean","Shallows","WetSand","Step","SkyBack","Foam")):
        try:
            o,e=a.get_actor_bounds(False,False)
            log("DUMP %s Y=[%.0f..%.0f] Z=[%.1f..%.1f]"%(lab,o.y-e.y,o.y+e.y,o.z-e.z,o.z+e.z))
            if lab not in ("TidebornEnv_Ocean","TidebornEnv_Shallows","TidebornEnv_SkyBackdrop") and "Foam" not in lab:
                if (o.y-e.y)<550 and (o.z+e.z)>=99: log("WARN "+lab)
        except: pass

try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
