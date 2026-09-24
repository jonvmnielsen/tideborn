# -*- coding: utf-8 -*-
"""Fix water plane scales so they don't cover the whole map; sand under feet, water ahead."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_water_scale_result.txt"
MAT="/Game/Tideborn/Art/Materials"
lines=[]
def log(m):
    t=str(m); unreal.log("[WaterScale] "+t); lines.append(t)
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
# Soften water color a bit
if water:
    try:
        # leave opaque but we'll use as-is
        pass
    except Exception: pass

ox,oy,oz=1000.0,1000.0,100.0
# Engine Plane is 100x100 uu. scale S => extent = 50*S each direction from center.
# Want sand under camera y=1100: center oy+200=1200, scaleY=20 => covers 1200±1000 = 200..2200
# Want shallows starting ~y=300 ending ~y=-500: center y=-100, scaleY=16 => ±800 => -900..700
# Ocean further: center y=-1200, scaleY=30 => ±1500 => -2700..300

for a in actors():
    lab=label(a)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(ox, oy+200, oz-2), False, True)
        a.set_actor_rotation(unreal.Rotator(0,0,0), False)
        a.set_actor_scale3d(unreal.Vector(90, 20, 1))
        apply(a, sand); log("sand ok")
    if "Shallows" in lab:
        a.set_actor_location(unreal.Vector(ox, oy-200, oz+1), False, True)
        a.set_actor_scale3d(unreal.Vector(100, 14, 1))  # ±700 in Y
        apply(a, water); log("shallows scale14")
    if lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(ox, oy-1400, oz+0), False, True)
        a.set_actor_scale3d(unreal.Vector(140, 28, 1))
        apply(a, water); log("ocean scale28")
    if lab=="TidebornEnv_Ground":
        a.set_actor_location(unreal.Vector(ox, oy+1800, oz-3), False, True)
        a.set_actor_scale3d(unreal.Vector(90, 40, 1))

# PlayerStart on sand
for a in actors():
    cn=a.get_class().get_name() if a.get_class() else ""
    if "PlayerStart" in cn or label(a)=="PlayerStart":
        a.set_actor_location(unreal.Vector(ox+60, oy+350, oz+110), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0), False)

log("=== LAYOUT ===")
for a in actors():
    lab=label(a)
    if any(k in lab for k in ("SandBase","Shallows","Ocean","Ground")):
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        half_y=50.0*sc.y
        log("%s y=%.0f cover=[%.0f..%.0f] z=%.0f"%(lab, loc.y, loc.y-half_y, loc.y+half_y, loc.z))

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8")
