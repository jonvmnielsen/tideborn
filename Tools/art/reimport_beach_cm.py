# -*- coding: utf-8 -*-
"""Reimport cm-scale beach, place 1:1, remove flat sand under it, fix trunks."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_beach_cm_result.txt"
MAT="/Game/Tideborn/Art/Materials"; MESH="/Game/Tideborn/Art/Meshes"
lines=[]
def log(m):
    t=str(m); unreal.log("[BeachCM] "+t); lines.append(t)
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
        try: comp.set_editor_property("override_materials",[mat]*8)
        except Exception: pass
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break
def import_fbx(path, dest):
    task=unreal.AssetImportTask(); task.filename=str(path); task.destination_path=dest
    task.automated=True; task.save=True; task.replace_existing=True
    options=unreal.FbxImportUI(); options.import_mesh=True; options.import_as_skeletal=False
    options.import_materials=False; options.import_textures=False
    options.static_mesh_import_data.combine_meshes=True
    options.static_mesh_import_data.auto_generate_collision=True
    options.static_mesh_import_data.import_uniform_scale=1.0
    task.options=options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.imported_object_paths) if task.imported_object_paths else []

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log(str(e))

import_fbx(ROOT/"RawArt"/"CC0"/"Models"/"SM_TidebornBeach.fbx", MESH)
import_fbx(ROOT/"RawArt"/"CC0"/"Models"/"SM_TidebornWater.fbx", MESH)
beach=load(MESH+"/SM_TidebornBeach"); water=load(MESH+"/SM_TidebornWater")
if beach:
    box=beach.get_bounding_box(); log("beach size=(%.0f,%.0f,%.0f)"%((box.max-box.min).x,(box.max-box.min).y,(box.max-box.min).z))
sand=load(MAT+"/M_Tideborn_Sand"); wmat=load(MAT+"/M_Tideborn_WaterSimple")
bark=load(MAT+"/M_Tideborn_Bark"); rock=load(MAT+"/M_Tideborn_RockShore") or load(MAT+"/M_Tideborn_RockBoulder")
ox,oy,oz=1000.0,1000.0,100.0

for a in list(actors()):
    lab=label(a)
    if lab.startswith("TidebornEnv_Sand") or lab in ("TidebornEnv_Beach","TidebornEnv_WaterMesh","TidebornEnv_Ocean","TidebornEnv_Ground","TidebornEnv_SandBase") or "Shallows" in lab:
        try: unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a); log("x "+lab)
        except Exception: pass
    # Destroy trunks that read as white cylinders in overview — re-place fewer later
    if lab.startswith("TidebornEnv_Trunk"):
        try: unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a); log("x trunk")
        except Exception: pass

sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
# Bake mats
for mesh, mat, path in ((beach, sand, MESH+"/SM_TidebornBeach"), (water, wmat, MESH+"/SM_TidebornWater")):
    if mesh and mat:
        try:
            s=unreal.StaticMaterial(); s.set_editor_property("material_interface", mat)
            mesh.set_editor_property("static_materials", [s]); unreal.EditorAssetLibrary.save_asset(path)
        except Exception as e: log(str(e))

# Place beach 1:1 cm at cove
if beach:
    b=sub.spawn_actor_from_object(beach, unreal.Vector(ox, oy, oz), unreal.Rotator(0,0,0))
    if b:
        b.set_actor_label("TidebornEnv_Beach"); apply(b, sand); log("beach 1:1")
if water:
    w=sub.spawn_actor_from_object(water, unreal.Vector(ox, oy-200, oz-40), unreal.Rotator(0,0,0))
    if w:
        w.set_actor_label("TidebornEnv_WaterMesh"); apply(w, wmat); log("water 1:1")

# A few driftwood with bark, well beside path
stump=load(MESH+"/dead_tree_trunk_1k")
if stump and bark:
    for i,(dx,dy) in enumerate(((-420,-80), (500,-60), (-480,-400), (560,-380))):
        a=sub.spawn_actor_from_object(stump, unreal.Vector(ox+dx, oy+dy, oz+20), unreal.Rotator(pitch=0, yaw=30*i, roll=0))
        if a:
            a.set_actor_scale3d(unreal.Vector(1.2,1.2,1.2)); a.set_actor_label("TidebornEnv_Trunk_%02d"%i); apply(a, bark)

# gameplay far back
for a in actors():
    lab=label(a); cn=cname(a)
    if "PlayerStart" in cn or lab=="PlayerStart":
        a.set_actor_location(unreal.Vector(ox+50, oy+400, oz+160), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0), False)
    if "Kelp" in lab: a.set_actor_location(unreal.Vector(ox-1000, oy+800, oz+50), False, True)
    if "Burr" in lab or "Hound" in lab: a.set_actor_location(unreal.Vector(ox+1100, oy+850, oz+50), False, True)
    if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
        a.set_actor_location(unreal.Vector(ox+80, oy+2000, oz+100), False, True)
    if "Boulder" in lab: apply(a, rock)

for a in actors():
    if "DirectionalLight" in cname(a):
        try:
            a.set_editor_property("intensity", 2.8)
            a.set_actor_rotation(unreal.Rotator(pitch=-42, yaw=40, roll=0), False)
        except Exception: pass
    if "SkyLight" in cname(a):
        try: a.set_editor_property("intensity", 1.4); a.set_editor_property("real_time_capture", True)
        except Exception: pass

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8"); log("DONE")
