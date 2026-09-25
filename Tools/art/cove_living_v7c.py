# -*- coding: utf-8 -*-
"""v7c: push remaining mid-cove rocks for Verify water band."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v7c_result.txt"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V7c] "+t); lines.append(t)
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load "+str(e))
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
side=0
for a in list(eas.get_all_level_actors()):
    lab=label(a)
    if not (("Boulder" in lab) or lab.startswith("TidebornEnv_WLB_")): continue
    loc=a.get_actor_location()
    # Broad verify+mouth clear
    if 550<=loc.x<=1450 and 300<=loc.y<=1500:
        nx=420.0 if (side%2==0) else 1580.0
        a.set_actor_location(unreal.Vector(nx,loc.y,loc.z),False,True)
        log("MOVE %s (%.0f,%.0f)->(%.0f,%.0f)"%(lab,loc.x,loc.y,nx,loc.y)); side+=1
# LOCK sand
for a in eas.get_all_level_actors():
    if label(a)=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1)); log("LOCK SandBase")
try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
