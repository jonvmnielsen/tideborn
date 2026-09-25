# -*- coding: utf-8 -*-
"""v10d: same-Z water planes abut at Y=-450 to kill peach hairline."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_living_v10d_result.txt"
MAT="/Game/Tideborn/Art/Materials"
MAP="/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V10d] "+t); lines.append(t)
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if unreal.EditorAssetLibrary.does_asset_exist(p) else None
def force_apply(a,mat):
    if not a or not mat: return
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(16):
            try: c.set_material(i,mat)
            except: break
def unhide(a):
    try:
        a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False)
    except: pass

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log(str(e))
water=load(MAT+"/M_Tideborn_WaterOpaque")
sand=load(MAT+"/MI_Tideborn_SandWarm")
for a in list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()):
    lab=label(a)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1))
        if sand: force_apply(a,sand); unhide(a); log("LOCK SandBase")
    elif lab=="TidebornEnv_Ocean":
        # Y[-1900..-450] Z=99.5  center=-1175 half=725 scY=14.5
        a.set_actor_location(unreal.Vector(1000,-1175,99.5),False,True)
        a.set_actor_scale3d(unreal.Vector(95,14.5,1))
        if water: force_apply(a,water); unhide(a)
        log("Ocean Y[-1900..-450] Z=99.5")
    elif lab=="TidebornEnv_Shallows":
        # Y[-450..500] Z=99.5  center=25 half=475 scY=9.5
        a.set_actor_location(unreal.Vector(1000,25,99.5),False,True)
        a.set_actor_scale3d(unreal.Vector(80,9.5,1))
        if water: force_apply(a,water); unhide(a)
        log("Shallows Y[-450..500] Z=99.5")
    elif "SkyDome" in lab:
        try: a.set_actor_hidden_in_game(True); a.set_is_temporarily_hidden_in_editor(True)
        except: pass
for a in list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()):
    lab=label(a)
    if lab in ("TidebornEnv_Ocean","TidebornEnv_Shallows","TidebornEnv_SandBase"):
        o,e=a.get_actor_bounds(False,False)
        log("DUMP %s Y=[%.0f..%.0f] Z=%.1f"%(lab,o.y-e.y,o.y+e.y,a.get_actor_location().z))
try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")