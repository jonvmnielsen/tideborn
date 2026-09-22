# -*- coding: utf-8 -*-
"""Force water into player FOV — big shallows + ocean planes close ahead."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_water_fov_result.txt"
MAT="/Game/Tideborn/Art/Materials"
lines=[]
def log(m):
    t=str(m); unreal.log("[WaterFOV] "+t); lines.append(t)
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

water=load(MAT+"/M_Tideborn_WaterSimple")
sand=load(MAT+"/M_Tideborn_Sand")
ox,oy,oz=1000.0,1000.0,100.0

# Remove old water/dune planes and rebuild closer
for a in list(actors()):
    lab=label(a)
    if any(k in lab for k in ("Ocean","Shallows","Dune")):
        try:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
            log("x "+lab)
        except Exception: pass

plane=load("/Engine/BasicShapes/Plane")
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def spawn_plane(loc, sx, sy, mat, lab, zoff=0):
    a=sub.spawn_actor_from_object(plane, unreal.Vector(loc[0],loc[1],loc[2]+zoff), unreal.Rotator(pitch=0,yaw=0,roll=0))
    if a:
        a.set_actor_scale3d(unreal.Vector(sx,sy,1))
        a.set_actor_label(lab)
        apply(a, mat)
        log("plane "+lab)
    return a

# Beach lip
spawn_plane((ox+100, oy-350, oz-1), 85, 40, sand, "TidebornEnv_Sand_Lip")
# Shallows VERY close — fills mid FOV
spawn_plane((ox+100, oy-700, oz-12), 100, 45, water, "TidebornEnv_Shallows")
# Ocean fills far FOV
spawn_plane((ox+100, oy-1400, oz-28), 140, 80, water, "TidebornEnv_Ocean")

# Lower light a bit so sand/water contrast
for a in actors():
    if "DirectionalLight" in (a.get_class().get_name() if a.get_class() else ""):
        try: a.set_editor_property("intensity", 3.2)
        except Exception: pass

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8")
log("DONE")
