# -*- coding: utf-8 -*-
"""Show beach relief, enlarge water in FOV, hide silhouette gameplay from beauty corridor."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_polish2_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
lines = []

def log(m):
    t=str(m); unreal.log("[Polish2] "+t); lines.append(t)
def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
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

sand=load(MAT+"/M_Tideborn_Sand"); water_mat=load(MAT+"/M_Tideborn_WaterSimple")
ox,oy,oz=1000.0,1000.0,100.0

for a in actors():
    lab=label(a)
    # Drop flat sand base under sculpted beach so relief reads; keep ground inland
    if lab == "TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(ox, oy+800, oz-8), False, True)
        a.set_actor_scale3d(unreal.Vector(80, 60, 1))
        log("sandbase moved inland under spawn only")
    if lab == "TidebornEnv_Beach":
        # Raise and ensure sand mat
        a.set_actor_location(unreal.Vector(ox, oy-150, oz+5), False, True)
        apply(a, sand)
        log("beach raised")
    if lab == "TidebornEnv_WaterMesh":
        a.set_actor_location(unreal.Vector(ox, oy-900, oz-25), False, True)
        # bigger
        a.set_actor_scale3d(unreal.Vector(180, 200, 1))
        apply(a, water_mat)
        log("water mesh larger")
    if lab == "TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(ox, oy-1600, oz-30), False, True)
        a.set_actor_scale3d(unreal.Vector(160, 100, 1))
        apply(a, water_mat)
        log("ocean plane")
    # Hide silhouette gameplay far behind spawn (still in level for PIE)
    if "Kelp" in lab:
        a.set_actor_location(unreal.Vector(ox-900, oy+600, oz+40), False, True)
    if "Burr" in lab or "Hound" in lab:
        a.set_actor_location(unreal.Vector(ox+950, oy+650, oz+50), False, True)
    if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
        a.set_actor_location(unreal.Vector(ox+100, oy+1800, oz+90), False, True)
    if "Gather" in lab:
        # keep near spawn but beside path
        if "Stone" in lab:
            a.set_actor_location(unreal.Vector(ox+320, oy+200, oz+40), False, True)
    if "PlayerStart" in cname(a) or lab=="PlayerStart":
        a.set_actor_location(unreal.Vector(ox+60, oy+150, oz+130), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0, yaw=-90, roll=0), False)

woods=[a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]
for i,a in enumerate(woods):
    a.set_actor_location(unreal.Vector(ox+250+i*120, oy+220, oz+40), False, True)

for a in actors():
    if "DirectionalLight" in cname(a):
        try:
            a.set_editor_property("intensity", 3.0)
            a.set_actor_rotation(unreal.Rotator(pitch=-38.0, yaw=35.0, roll=0.0), False)
        except Exception: pass
    if "ExponentialHeightFog" in cname(a):
        try:
            a.set_editor_property("fog_density", 0.035)
            a.set_editor_property("fog_height_falloff", 0.2)
        except Exception: pass

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8")
log("DONE")
