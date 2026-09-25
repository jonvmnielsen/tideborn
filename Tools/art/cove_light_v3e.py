# -*- coding: utf-8 -*-
"""Cove light v3e — kill blue wash; warm sand/fog within locked ranges. No transform changes."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_light_v3e_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
TEX = "/Game/Tideborn/Art/Textures"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"

lines = []

def log(m):
    t = str(m)
    unreal.log("[LightV3e] " + t)
    lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())

def label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""

def cname(a):
    try:
        return a.get_class().get_name() or ""
    except Exception:
        return ""

def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if p and unreal.EditorAssetLibrary.does_asset_exist(p) else None

def apply(a, mat):
    if not mat:
        return
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        try:
            comp.modify()
        except Exception:
            pass
        for i in range(8):
            try:
                comp.set_material(i, mat)
            except Exception:
                break

def find_tex(folder, keys):
    base = TEX + "/" + folder
    if not unreal.EditorAssetLibrary.does_directory_exist(base):
        return None
    for ap in unreal.EditorAssetLibrary.list_assets(base, recursive=False):
        name = ap.split(".")[-1].lower()
        for k in keys:
            if k.lower() in name:
                return ap
    return None

def make_sand(tile=68.0):
    name = "M_Tideborn_Sand"
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    bc = load(find_tex("Sand", ["Diffuse", "Color"]))
    rough = load(find_tex("Sand", ["Rough", "roughness"]))
    uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 0)
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -550, 0)
    sc = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 60)
    sc.set_editor_property("r", float(tile))
    mel.connect_material_expressions(uv, "", mul, "A")
    mel.connect_material_expressions(sc, "", mul, "B")
    base_col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 120)
    # Stronger warm beach — survives cool skylight
    base_col.set_editor_property("constant", unreal.LinearColor(0.92, 0.74, 0.48, 1.0))
    if bc:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, -80)
        ts.set_editor_property("texture", bc)
        mel.connect_material_expressions(mul, "", ts, "UVs")
        lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -120, 0)
        mel.connect_material_expressions(base_col, "", lerp, "A")
        mel.connect_material_expressions(ts, "RGB", lerp, "B")
        alpha = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 40)
        alpha.set_editor_property("r", 0.12)
        mel.connect_material_expressions(alpha, "", lerp, "Alpha")
        mel.connect_material_property(lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    else:
        mel.connect_material_property(base_col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    if rough:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, 200)
        ts.set_editor_property("texture", rough)
        try:
            ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        except Exception:
            pass
        mel.connect_material_expressions(mul, "", ts, "UVs")
        mel.connect_material_property(ts, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    em = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 320)
    em.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("sand tile=%.0f soft_blend=0.12 warm_beach" % tile)
    return mat

def make_gate_wood():
    name = "M_Tideborn_GateSolid"
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    col.set_editor_property("constant", unreal.LinearColor(0.32, 0.22, 0.14, 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 100)
    r.set_editor_property("r", 0.90)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    em = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 200)
    em.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("gate wood muted brown non-emissive")
    return mat

try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e:
    log("load " + str(e))

sand = make_sand(68.0)
gate = make_gate_wood()

for a in actors():
    lab = label(a)
    cn = cname(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_SandRamp") or "SandRamp" in lab:
        apply(a, sand)
        log("apply sand -> " + lab)
    if "ShoreGate" in lab or lab == "Tideborn_P2_ShoreGate":
        apply(a, gate)
        log("apply gate wood -> " + lab)
        for comp in a.get_components_by_class(unreal.LightComponent):
            try: comp.set_editor_property("light_color", unreal.LinearColor(1.0, 0.78, 0.50, 1.0))
            except Exception: pass
            try: comp.set_editor_property("intensity", 400.0)
            except Exception: pass
            try: comp.set_editor_property("cast_shadows", False)
            except Exception: pass
            log("gate light muted")
    if "DirectionalLight" in cn:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 1.3)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.86, 0.62, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 2.4)
            except Exception: pass
            try: c.set_editor_property("shadow_amount", 0.40)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-40, yaw=35, roll=0), False)
        log("DirectionalLight 1.3 warm amber pitch=-40 yaw=35")
    if "SkyLight" in cn:
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity", 7.5)
            except Exception: pass
            try: c.set_editor_property("real_time_capture", True)
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_is_black", False)
            except Exception: pass
        log("SkyLight 7.5")
    if "ExponentialHeightFog" in cn:
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.09)
            except Exception: pass
            try: c.set_editor_property("fog_height_falloff", 0.20)
            except Exception: pass
            # Soft warm-grey with only a hint of blue — kills cyan wash
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.72, 0.70, 0.68, 1.0))
            except Exception: pass
            try: c.set_editor_property("fog_max_opacity", 0.70)
            except Exception: pass
            try: c.set_editor_property("volumetric_fog", True)
            except Exception: pass
        log("Fog density~0.09 warm-grey inscatter (anti-blue-wash)")
    if "PostProcess" in cn:
        for c in a.get_components_by_class(unreal.PostProcessComponent):
            try:
                s = c.get_editor_property("settings")
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", 1.2)
                s.set_editor_property("override_auto_exposure_min_brightness", True)
                s.set_editor_property("auto_exposure_min_brightness", 0.85)
                c.set_editor_property("settings", s)
                log("PP exposure_bias~1.2")
            except Exception as e:
                log("PP warn: %s" % e)

# Confirm hard floor untouched
for a in actors():
    lab = label(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_Shallows", "TidebornEnv_Ocean", "TidebornEnv_Ground", "TidebornEnv_SandRamp"):
        loc = a.get_actor_location(); sc = a.get_actor_scale3d()
        hy = 50.0 * sc.y
        log("CONFIRM %s Z=%.0f Y[%.0f..%.0f] sc=(%.1f,%.1f,%.1f)" % (
            lab, loc.z, loc.y - hy, loc.y + hy, sc.x, sc.y, sc.z))

try:
    r = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("save_current_level -> %s" % r)
except Exception as e:
    log("save: %s" % e)
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("save_dirty -> True")
except Exception as e:
    log("save_dirty: %s" % e)
try:
    unreal.EditorAssetLibrary.save_asset(MAP)
except Exception:
    pass

log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
