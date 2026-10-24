# -*- coding: utf-8 -*-
"""Safe fake dunes (tilted sand shelves) + pull water into lower FOV hard."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_dunes_safe_result.txt"
MAT="/Game/Tideborn/Art/Materials"
lines=[]
def log(m):
    t=str(m); unreal.log("[DunesSafe] "+t); lines.append(t)
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

sand=load(MAT+"/M_Tideborn_Sand"); water=load(MAT+"/M_Tideborn_WaterSimple")
ox,oy,oz=1000.0,1000.0,100.0
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
plane=load("/Engine/BasicShapes/Plane")

# remove prior dunes
for a in list(actors()):
    if label(a).startswith("TidebornEnv_Dune"):
        try: sub.destroy_actor(a)
        except Exception: pass

def dune(x,y,z, sx,sy, pitch, yaw, name):
    a=sub.spawn_actor_from_object(plane, unreal.Vector(x,y,z), unreal.Rotator(pitch=pitch, yaw=yaw, roll=0))
    if a:
        a.set_actor_scale3d(unreal.Vector(sx,sy,1)); a.set_actor_label(name); apply(a, sand); log(name)

# Berms along rock arms (do not cover center path)
dune(ox-380, oy-50, oz+6, 22, 50, 6.0, 8.0, "TidebornEnv_Dune_L0")
dune(ox-420, oy-280, oz+10, 20, 40, 7.0, 5.0, "TidebornEnv_Dune_L1")
dune(ox+460, oy-30, oz+6, 22, 50, 6.0, -8.0, "TidebornEnv_Dune_R0")
dune(ox+500, oy-260, oz+10, 20, 40, 7.0, -5.0, "TidebornEnv_Dune_R1")
# Low lip before water across full width (slight pitch toward ocean)
dune(ox, oy-420, oz+2, 90, 18, 4.0, 0.0, "TidebornEnv_Dune_Lip")

for a in actors():
    lab=label(a)
    if "Shallows" in lab:
        # Fill mid FOV with water
        a.set_actor_location(unreal.Vector(ox, oy-480, oz-6), False, True)
        a.set_actor_scale3d(unreal.Vector(160, 100, 1)); apply(a, water); log("shallows FOV")
    if lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(ox, oy-1100, oz-14), False, True)
        a.set_actor_scale3d(unreal.Vector(220, 140, 1)); apply(a, water); log("ocean FOV")

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8")
