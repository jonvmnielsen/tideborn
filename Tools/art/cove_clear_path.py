# -*- coding: utf-8 -*-
"""Clear center-path blockers; keep side framing only."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_clear_path_result.txt"
lines=[]
def log(m):
    t=str(m); unreal.log("[ClearPath] "+t); lines.append(t)
def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log(str(e))

ox, oy = 1000.0, 1000.0
# Playable corridor: |x-ox| < 220 roughly must stay clear of large props
removed=0
for a in list(actors()):
    lab=label(a)
    if not (lab.startswith("TidebornEnv_Boulder") or lab.startswith("TidebornEnv_Trunk")):
        continue
    loc=a.get_actor_location()
    # remove anything near center corridor in front of spawn
    if abs(loc.x - ox) < 220 and (oy-700) < loc.y < (oy+200):
        try:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
            removed+=1; log("removed center %s at %.0f,%.0f"%(lab, loc.x, loc.y))
        except Exception as e: log(str(e))
    # also remove named extras that were mouth-center
    if "extra_04" in lab or "extra_03" in lab or "extra_02" in lab:
        try:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
            removed+=1; log("removed "+lab)
        except Exception: pass

log("removed=%d"%removed)
try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8")
