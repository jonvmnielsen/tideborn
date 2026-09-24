# -*- coding: utf-8 -*-
"""CRITICAL: sand was covering water. Trim sand, opaque water in FOV."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_water_visible_result.txt"
MAT="/Game/Tideborn/Art/Materials"
lines=[]
def log(m):
    t=str(m); unreal.log("[WaterVis] "+t); lines.append(t)
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

def make_opaque_water():
    name="M_Tideborn_WaterOpaque"; path=MAT+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel=unreal.MaterialEditingLibrary
    col=mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
    col.set_editor_property("constant", unreal.LinearColor(0.05, 0.28, 0.48, 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rg=mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 100)
    rg.set_editor_property("r", 0.08)
    mel.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat); unreal.EditorAssetLibrary.save_asset(path)
    log("opaque water mat"); return mat

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log(str(e))

sand=load(MAT+"/M_Tideborn_Sand")
water=make_opaque_water()
ox,oy,oz=1000.0,1000.0,100.0

for a in actors():
    lab=label(a)
    # Sand only covers inland+beach, NOT ocean region (stop before y~oy-350)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(ox, oy+200, oz-2), False, True)
        a.set_actor_scale3d(unreal.Vector(130, 70, 1))  # extends roughly +/-3500 in Y from center -> ends ~ oy-3300? 
        # Plane default 100uu; scale 70 => 7000uu extent in Y, center at oy+200 => covers oy-3300..oy+3700 — STILL too far
        # Need smaller Y scale: 28 => 2800uu half = 1400; center oy+100 => ends oy-1300
        a.set_actor_location(unreal.Vector(ox, oy+50, oz-2), False, True)
        a.set_actor_scale3d(unreal.Vector(120, 28, 1))
        apply(a, sand); log("sand trimmed")
    if lab.startswith("TidebornEnv_Dune"):
        # keep berms but not over water
        loc=a.get_actor_location()
        if loc.y < oy-400:
            try: unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a); log("x deep dune")
            except Exception: pass
        else:
            apply(a, sand)
    if "Shallows" in lab:
        # JUST past sand edge, SLIGHTLY above sand Z so always visible
        a.set_actor_location(unreal.Vector(ox, oy-450, oz+1), False, True)
        a.set_actor_scale3d(unreal.Vector(140, 55, 1)); apply(a, water); log("shallows visible")
    if lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(ox, oy-1100, oz+0), False, True)
        a.set_actor_scale3d(unreal.Vector(200, 100, 1)); apply(a, water); log("ocean visible")

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8")
