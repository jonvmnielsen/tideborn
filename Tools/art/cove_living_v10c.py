# -*- coding: utf-8 -*-
"""v10c: close Ocean/Shallows Y gap (-500..-400) that showed peach sky stripe."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v10c_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V10c] "+t); lines.append(t)
def label(a):
    try: return a.get_actor_label() or ""
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

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log(str(e))
water=load(MAT+"/M_Tideborn_WaterOpaque")
sand=load(MAT+"/MI_Tideborn_SandWarm")
wet=load(MAT+"/MI_Tideborn_SandWet")
for a in list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()):
    lab=label(a)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1))
        if sand: force_apply(a,sand); unhide(a); log("LOCK SandBase")
    elif lab=="TidebornEnv_Ocean":
        # Extend to abut shallows: Y[-1900..-400] center=-1150 half=750 scY=15
        a.set_actor_location(unreal.Vector(1000,-1150,99),False,True)
        a.set_actor_scale3d(unreal.Vector(95,15,1))
        if water: force_apply(a,water); unhide(a)
        log("Ocean Y[-1900..-400]")
    elif lab=="TidebornEnv_Shallows":
        # Y[-500..500] center=0 half=500 scY=10 — slight overlap with Ocean at -400..-500
        a.set_actor_location(unreal.Vector(1000,0,100),False,True)
        a.set_actor_scale3d(unreal.Vector(80,10,1))
        if water: force_apply(a,water); unhide(a)
        log("Shallows Y[-500..500]")
    elif lab=="TidebornEnv_WetSand_00":
        a.set_actor_location(unreal.Vector(1000,700,105.5),False,True)
        a.set_actor_scale3d(unreal.Vector(48,2.0,1))
        if wet: force_apply(a,wet); unhide(a)
    elif "SkyDome" in lab:
        try:
            a.set_actor_hidden_in_game(True); a.set_is_temporarily_hidden_in_editor(True)
        except: pass

for a in list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()):
    lab=label(a)
    if any(k in lab for k in ("Ocean","Shallows","SandBase","WetSand","Foam")):
        try:
            o,e=a.get_actor_bounds(False,False)
            log("DUMP %s Y=[%.0f..%.0f] Z=%.1f"%(lab,o.y-e.y,o.y+e.y,o.z))
        except: pass

try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")