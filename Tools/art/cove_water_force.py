# -*- coding: utf-8 -*-
"""Diagnose water/sand actors; force unmistakable water band in front of camera."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_water_force_result.txt"
MAT="/Game/Tideborn/Art/Materials"
lines=[]
def log(m):
    t=str(m); unreal.log("[WaterForce] "+t); lines.append(t)
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
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
plane=load("/Engine/BasicShapes/Plane")

log("=== ENV ACTORS ===")
for a in actors():
    lab=label(a)
    if lab.startswith("TidebornEnv_"):
        loc=a.get_actor_location(); sc=a.get_actor_scale3d(); rot=a.get_actor_rotation()
        log("%s loc=(%.0f,%.0f,%.0f) sc=(%.1f,%.1f,%.1f) rot=(%.1f,%.1f,%.1f)"%(lab,loc.x,loc.y,loc.z,sc.x,sc.y,sc.z,rot.pitch,rot.yaw,rot.roll))

# Destroy ALL dunes (cause tilt/confusion)
for a in list(actors()):
    if label(a).startswith("TidebornEnv_Dune") or "Shallows" in label(a) or label(a)=="TidebornEnv_Ocean":
        try: sub.destroy_actor(a); log("x "+label(a))
        except Exception: pass

# Flatten sand base clearly under camera looking -Y from ~y=1100
for a in actors():
    if label(a)=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(ox, oy+100, oz-2), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0), False)
        a.set_actor_scale3d(unreal.Vector(100, 25, 1))  # half-extent Y=1250; from oy+100 covers oy-1150..oy+1350
        apply(a, sand); log("sand flat")

# Water STARTS where sand ends: sand ends ~ oy-1150 if scale 25*100/2=1250 and center oy+100 -> oy-1150
# Camera at y=1100 looking -Y sees decreasing y. Water should start around y=200..-400 in view.
# Place water covering y from ~oy-200 to oy-2000, z slightly above sand
w1=sub.spawn_actor_from_object(plane, unreal.Vector(ox, oy-400, oz+3), unreal.Rotator(0,0,0))
if w1:
    w1.set_actor_scale3d(unreal.Vector(160, 80, 1)); w1.set_actor_label("TidebornEnv_Shallows"); apply(w1, water); log("shallows forced")
w2=sub.spawn_actor_from_object(plane, unreal.Vector(ox, oy-1400, oz+2), unreal.Rotator(0,0,0))
if w2:
    w2.set_actor_scale3d(unreal.Vector(220, 120, 1)); w2.set_actor_label("TidebornEnv_Ocean"); apply(w2, water); log("ocean forced")

# Shrink sand so it DOES NOT cover water: sand only to ~oy-150
for a in actors():
    if label(a)=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(ox, oy+250, oz-2), False, True)
        a.set_actor_scale3d(unreal.Vector(100, 18, 1))  # half Y=900; center 1250 => covers 350..2150
        # Wait camera at 1100, sand from 350 to 2150 - water at -400 is OUTSIDE sand. Good.
        log("sand final")

log("=== AFTER ===")
for a in actors():
    lab=label(a)
    if lab.startswith("TidebornEnv_") and any(k in lab for k in ("Sand","Ocean","Shallows","Dune")):
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        log("%s loc=(%.0f,%.0f,%.0f) sc=(%.1f,%.1f)"%(lab,loc.x,loc.y,loc.z,sc.x,sc.y))

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8")
