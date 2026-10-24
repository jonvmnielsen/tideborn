# -*- coding: utf-8 -*-
"""DIAG: paint SandBase hot pink UNLIT, shot verify — proves mat reaches screenshot."""
from __future__ import annotations
import pathlib, time, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_diag_pink_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
SHOT_DIR = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
lines = []
def log(m):
    t=str(m); unreal.log("[DiagPink] "+t); lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load "+str(e))

path = MAT + "/MI_Tideborn_SandWarm"
if unreal.EditorAssetLibrary.does_asset_exist(path):
    unreal.EditorAssetLibrary.delete_asset(path)
mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    "MI_Tideborn_SandWarm", MAT, unreal.Material, unreal.MaterialFactoryNew())
mel = unreal.MaterialEditingLibrary
try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
except Exception as e: log("shading "+str(e))
col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
# HOT PINK diagnostic
col.set_editor_property("constant", unreal.LinearColor(1.0, 0.0, 0.8, 1.0))
mel.connect_material_property(col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(path)
log("created HOT PINK unlit sand")

for a in actors():
    lab = label(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_SandRamp") or "SandRamp" in lab:
        for comp in a.get_components_by_class(unreal.PrimitiveComponent):
            for i in range(8):
                try: comp.set_material(i, mat)
                except Exception: break
            try: comp.set_editor_property("override_materials", [mat]*8)
            except Exception: pass
        # also log actual material after
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            m0 = comp.get_material(0)
            sm = comp.get_editor_property("static_mesh")
            log("apply %s mesh=%s mat0=%s" % (lab, sm.get_name() if sm else "?", m0.get_name() if m0 else "?"))

# soften PP that might remap
for a in actors():
    cn = a.get_class().get_name() if a.get_class() else ""
    if "PostProcess" in cn:
        try:
            s = a.get_editor_property("settings")
            s.set_editor_property("override_white_temp", False)
            s.set_editor_property("override_auto_exposure_bias", True)
            s.set_editor_property("auto_exposure_bias", 0.0)
            a.set_editor_property("settings", s)
            log("PP neutralized")
        except Exception as e: log("PP "+str(e))

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception: pass

log("wait 20s shaders")
time.sleep(20)

SHOT_DIR.mkdir(parents=True, exist_ok=True)
target = SHOT_DIR / "TidebornCoveVerify.png"
if target.exists():
    try: target.unlink()
    except Exception: pass
for cmd in ("ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
unreal.EditorLevelLibrary.set_level_viewport_camera_info(
    unreal.Vector(1050,1550,200), unreal.Rotator(pitch=-5, yaw=-90, roll=0))
log("SHOT begin")
unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, "TidebornCoveVerify")
ok=False
for i in range(90):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size>20000:
        ok=True; break
time.sleep(3)
if target.exists() and target.stat().st_size>20000: ok=True
log("SHOT ok=%s size=%s" % (ok, target.stat().st_size if target.exists() else 0))
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
log("DONE")
