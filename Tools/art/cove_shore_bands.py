# -*- coding: utf-8 -*-
"""Non-overlapping shoreline bands: sand / shallows / ocean."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_shore_bands_result.txt"
MAT="/Game/Tideborn/Art/Materials"
lines=[]
def log(m):
    t=str(m); unreal.log("[Bands] "+t); lines.append(t)
def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if p and unreal.EditorAssetLibrary.does_asset_exist(p) else None
def apply(a, mat):
    if not mat: return
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log(str(e))

sand=load(MAT+"/M_Tideborn_Sand")
water=load(MAT+"/M_Tideborn_WaterOpaque") or load(MAT+"/M_Tideborn_WaterSimple")
ox,oy,oz=1000.0,1000.0,100.0

# Plane extent half = 50 * scale
# Sand: under spawn/camera (~y 1200-1600). center=1500, scaleY=16 => ±800 => 700..2300
# Shallows: ahead of sand. center=300, scaleY=10 => ±500 => -200..800  (meets sand ~700-800)
# Ocean: further. center=-800, scaleY=20 => ±1000 => -1800..200

for a in actors():
    lab=label(a)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(ox, 1500, oz-2), False, True)
        a.set_actor_scale3d(unreal.Vector(80, 16, 1)); apply(a, sand)
        log("sand 700..2300")
    if "Shallows" in lab:
        a.set_actor_location(unreal.Vector(ox, 300, oz+2), False, True)
        a.set_actor_scale3d(unreal.Vector(90, 10, 1)); apply(a, water)
        log("shallows -200..800")
    if lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(ox, -900, oz+1), False, True)
        a.set_actor_scale3d(unreal.Vector(120, 22, 1)); apply(a, water)
        log("ocean -2000..200")
    if lab=="TidebornEnv_Ground":
        a.set_actor_location(unreal.Vector(ox, 2800, oz-3), False, True)
        a.set_actor_scale3d(unreal.Vector(80, 30, 1))

for a in actors():
    cn=a.get_class().get_name() if a.get_class() else ""
    if "PlayerStart" in cn or label(a)=="PlayerStart":
        a.set_actor_location(unreal.Vector(ox+50, 1400, oz+110), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0), False)

for a in actors():
    lab=label(a)
    if any(k in lab for k in ("SandBase","Shallows","Ocean")):
        loc=a.get_actor_location(); sc=a.get_actor_scale3d(); hy=50*sc.y
        log("%s cover Y [%.0f..%.0f] z=%.0f"%(lab, loc.y-hy, loc.y+hy, loc.z))

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8")
