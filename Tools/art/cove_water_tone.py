# -*- coding: utf-8 -*-
"""Mute bright cyan water -> darker natural ocean; keep hard floor transforms."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_water_tone_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines = []

def log(m):
    t = str(m); unreal.log("[WaterTone] " + t); lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())

def label(a):
    try: return a.get_actor_label() or ""
    except Exception: return ""

def apply(a, mat):
    if not mat: return
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        try: comp.modify()
        except Exception: pass
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break

def make_water(name, rgb, rough=0.15):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 100)
    r.set_editor_property("r", float(rough))
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    # slight specular water look via metallic low
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 160)
    m.set_editor_property("r", 0.05)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    em = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 220)
    em.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("water mat %s rgb=(%.2f,%.2f,%.2f)" % (name, rgb[0], rgb[1], rgb[2]))
    return mat

try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e:
    log("load " + str(e))

# Shallows: muted sea-green; Ocean: deeper navy — no bright cyan
shallows = make_water("M_Tideborn_WaterOpaque", (0.08, 0.18, 0.28), rough=0.22)
ocean = shallows  # same opaque base; depth read via lighting
# also refresh simple alias if used
try:
    make_water("M_Tideborn_WaterSimple", (0.08, 0.18, 0.28), rough=0.22)
except Exception as e:
    log("simple water warn: %s" % e)

for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_Shallows":
        apply(a, shallows); log("Shallows -> muted sea")
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        log("CONFIRM Shallows Z=%.0f Y[%.0f..%.0f] scY=%.1f" % (loc.z, loc.y-50*sc.y, loc.y+50*sc.y, sc.y))
    if lab == "TidebornEnv_Ocean":
        apply(a, ocean); log("Ocean -> muted sea")
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        log("CONFIRM Ocean Z=%.0f scY=%.1f" % (loc.z, sc.y))
    if lab == "TidebornEnv_SandBase":
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        log("CONFIRM SandBase Z=%.0f Y[%.0f..%.0f] sc=(%.1f,%.1f) LOCKED" % (
            loc.z, loc.y-50*sc.y, loc.y+50*sc.y, sc.x, sc.y))

try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("save_current_level -> True")
except Exception as e:
    log("save: %s" % e)
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("save_dirty -> True")
except Exception as e:
    log("save_dirty: %s" % e)

log("DONE")
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
