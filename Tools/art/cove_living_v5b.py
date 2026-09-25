# -*- coding: utf-8 -*-
"""v5b: shrink SandRamp so wet band/shore edge read. NO shot."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v5b_result.txt"
lines = []
def log(m):
    t=str(m); unreal.log("[V5b] "+t); lines.append(t)
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log("load "+str(e))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    lab = label(a)
    if lab == "TidebornEnv_SandRamp" or "SandRamp" in lab:
        a.set_actor_location(unreal.Vector(1000.0, 580.0, 105.0), False, True)
        # mesh is ~55x14m; tiny scale so it doesn't bury wet strips
        a.set_actor_scale3d(unreal.Vector(0.22, 0.14, 0.6))
        try:
            o,e = a.get_actor_bounds(False)
            log("SandRamp sc=(0.22,0.14) extent=(%.0f,%.0f,%.0f) Y[%.0f..%.0f]" % (e.x,e.y,e.z, o.y-e.y, o.y+e.y))
        except Exception as ex:
            log("bounds "+str(ex))
    if lab == "TidebornEnv_SandBase":
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        log("LOCK check SandBase Z=%.0f sc=(%.1f,%.1f)" % (loc.z, sc.x, sc.y))
    if lab.startswith("TidebornEnv_WetSand_") or lab=="TidebornEnv_ShoreEdge":
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        log("keep %s loc=(%.0f,%.0f,%.0f) sc=(%.2f,%.2f)" % (lab, loc.x, loc.y, loc.z, sc.x, sc.y))
try: log("save -> %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log("save "+str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except: pass
log("DONE")
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
