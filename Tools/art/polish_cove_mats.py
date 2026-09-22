# -*- coding: utf-8 -*-
"""Polish pass: force solid mats on all env + gameplay meshes; darker sand; clean shot flags."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "polish_result.txt"
MAT_DIR = "/Game/Tideborn/Art/Materials"
lines = []

def log(m):
    t = str(m); unreal.log("[Polish] "+t); lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())

def label(a):
    try: return a.get_actor_label() or ""
    except: return ""

def cname(a):
    try: return a.get_class().get_name() or ""
    except: return ""

def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if unreal.EditorAssetLibrary.does_asset_exist(p) else None

def ensure_solid(name, rgb, translucent=False, rough=0.85):
    path = MAT_DIR + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not mat:
        return None
    if translucent:
        try:
            mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            mat.set_editor_property("two_sided", True)
        except Exception:
            pass
    node = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -350, 0
    )
    node.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    if translucent:
        op = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -350, 120
        )
        op.set_editor_property("r", 0.45)
        unreal.MaterialEditingLibrary.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
    else:
        r = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -350, 120
        )
        r.set_editor_property("r", rough)
        unreal.MaterialEditingLibrary.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("mat "+name)
    return mat

def apply_mat(actor, mat):
    n = 0
    try:
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            # override all slots
            try:
                mats = comp.get_editor_property("override_materials") or []
                slots = max(1, len(mats) if mats else 1)
                try:
                    sm = comp.get_editor_property("static_mesh")
                    if sm:
                        slots = max(slots, sm.get_num_sections(0) if hasattr(sm, "get_num_sections") else slots)
                except Exception:
                    pass
                for i in range(max(slots, 4)):
                    try:
                        comp.set_material(i, mat)
                        n += 1
                    except Exception:
                        break
            except Exception as e:
                log("apply fail "+str(e))
    except Exception:
        pass
    return n

def main():
    try:
        unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
    except Exception as e:
        log("load "+str(e))

    # Darker, more readable beach colors under strong sun
    sand = ensure_solid("M_Tideborn_SandSolid", (0.62, 0.48, 0.28), rough=0.92)
    ground = ensure_solid("M_Tideborn_GroundSolid", (0.22, 0.28, 0.14), rough=0.9)
    water = ensure_solid("M_Tideborn_WaterSolid", (0.08, 0.28, 0.45), translucent=True)
    rock = ensure_solid("M_Tideborn_RockSolid", (0.42, 0.40, 0.36), rough=0.75)
    bark = ensure_solid("M_Tideborn_BarkSolid", (0.32, 0.18, 0.09), rough=0.88)
    creature = ensure_solid("M_Tideborn_CreatureSolid", (0.25, 0.45, 0.30), rough=0.7)
    gate = ensure_solid("M_Tideborn_GateSolid", (0.45, 0.35, 0.22), rough=0.8)

    applied = 0
    for a in actors():
        lab = label(a)
        low = lab.lower()
        if lab.startswith("TidebornEnv_Sand") or lab.startswith("TidebornEnv_Ground"):
            applied += apply_mat(a, sand if "Sand" in lab else ground)
        elif lab.startswith("TidebornEnv_Ocean"):
            applied += apply_mat(a, water)
        elif "Trunk" in lab or "Bark" in lab:
            applied += apply_mat(a, bark)
        elif lab.startswith("TidebornEnv_"):
            applied += apply_mat(a, rock)
        elif "Kelp" in lab or "Burr" in lab or "Hound" in lab:
            applied += apply_mat(a, creature)
        elif "Gate" in lab:
            applied += apply_mat(a, gate)
        elif "Gather" in lab:
            applied += apply_mat(a, rock if "Stone" in lab else bark)
        elif "Beacon" in lab or "Landmark" in lab or "PathPost" in lab or "Post" in lab:
            applied += apply_mat(a, gate)
    log("material_slots_applied=%d" % applied)

    # Soften directional light so sand isn't blown white
    for a in actors():
        if "DirectionalLight" in cname(a):
            try:
                a.set_editor_property("intensity", 8.0)
                a.set_editor_property("light_color", unreal.LinearColor(1.0, 0.85, 0.65, 1.0))
                a.set_actor_rotation(unreal.Rotator(pitch=-32.0, yaw=50.0, roll=0.0), False)
            except Exception:
                pass
        if "SkyLight" in cname(a):
            try:
                a.set_editor_property("intensity", 1.2)
            except Exception:
                pass

    # Hide editor clutter in viewport shot
    for cmd in (
        "ShowFlag.ModeWidgets 0",
        "ShowFlag.Selection 0",
        "ShowFlag.SelectionOutline 0",
        "ShowFlag.Bounds 0",
        "ShowFlag.Collision 0",
        "ShowFlag.Navigation 0",
    ):
        try:
            unreal.SystemLibrary.execute_console_command(None, cmd)
        except Exception:
            pass

    cam_loc = unreal.Vector(1150, 900, 200)
    cam_rot = unreal.Rotator(pitch=-6.0, yaw=-90.0, roll=0.0)
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(cam_loc, cam_rot)
    except Exception:
        pass
    try:
        unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, "TidebornCoveVerify")
        log("shot verify")
    except Exception as e:
        log("shot fail "+str(e))
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(
            unreal.Vector(1000, 1800, 900),
            unreal.Rotator(pitch=-30.0, yaw=-90.0, roll=0.0),
        )
        unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, "TidebornCoveOverview")
        log("shot overview")
    except Exception as e:
        log("overview fail "+str(e))

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception:
        try: unreal.EditorLevelLibrary.save_current_level()
        except Exception: pass
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass

    lines.append("DONE")
    RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")

if __name__ == "__main__":
    main()
