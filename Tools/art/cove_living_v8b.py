# -*- coding: utf-8 -*-
"""v8b: kill purple noise water, hide flat SkyDome, thicken foam, readable slope."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v8b_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
TEX = "/Game/Tideborn/Art/Textures"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"

lines = []
def log(m):
    t = str(m); unreal.log("[V8b] " + t); lines.append(t)
def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except Exception: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except Exception: return ""
def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if p and unreal.EditorAssetLibrary.does_asset_exist(p) else None
def unhide(a):
    try:
        a.set_actor_hidden_in_game(False)
        a.set_is_temporarily_hidden_in_editor(False)
        root = a.root_component
        if root:
            try: root.set_visibility(True, True)
            except Exception: pass
    except Exception:
        pass
def hide(a):
    try:
        a.set_actor_hidden_in_game(True)
        a.set_is_temporarily_hidden_in_editor(True)
        root = a.root_component
        if root:
            try: root.set_visibility(False, True)
            except Exception: pass
    except Exception:
        pass
def force_apply(a, mat):
    if not a or not mat: return
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(16):
            try: comp.set_material(i, mat)
            except Exception: break
        try: comp.set_editor_property("override_materials", [mat] * 8)
        except Exception: pass

def del_mat(name):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)

def make_lit(name, rgb, rough=0.9, emissive=None):
    del_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    c = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 120)
    r.set_editor_property("r", float(rough))
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)
    m.set_editor_property("r", 0.0)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 280)
    if emissive:
        e.set_editor_property("constant", unreal.LinearColor(emissive[0], emissive[1], emissive[2], 1.0))
    else:
        e.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("mat %s %s" % (name, rgb))
    return mat

def make_water(name, rgb=(0.02, 0.10, 0.42)):
    """Deep blue + roughness from sand rough tile (NO Noise node)."""
    del_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    c = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rg_tex = load(TEX + "/Sand/sand_01_Rough") or load(TEX + "/Sand/sand_01_rough") or load("/Game/Tideborn/Art/Textures/Sand/sand_01_Rough")
    if rg_tex:
        uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 200)
        mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -550, 200)
        sc = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 260)
        sc.set_editor_property("r", 6.0)
        mel.connect_material_expressions(uv, "", mul, "A")
        mel.connect_material_expressions(sc, "", mul, "B")
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, 200)
        ts.set_editor_property("texture", rg_tex)
        try: ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        except Exception: pass
        mel.connect_material_expressions(mul, "", ts, "UVs")
        lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -150, 200)
        a = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 280)
        a.set_editor_property("r", 0.20)
        b = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 340)
        b.set_editor_property("r", 0.55)
        mel.connect_material_expressions(a, "", lerp, "A")
        mel.connect_material_expressions(b, "", lerp, "B")
        mel.connect_material_expressions(ts, "R", lerp, "Alpha")
        mel.connect_material_property(lerp, "", unreal.MaterialProperty.MP_ROUGHNESS)
    else:
        r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -200, 200)
        r.set_editor_property("r", 0.35)
        mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -200, 320)
    m.set_editor_property("r", 0.05)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("water %s" % name)
    return mat

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load " + str(e))

sand = load(MAT + "/MI_Tideborn_SandWarm")
wet_dark = make_lit("MI_Tideborn_SandWet", (0.09, 0.06, 0.04), 0.35)
wet_mid = make_lit("MI_Tideborn_SandWetMid", (0.16, 0.10, 0.06), 0.42)
water = make_water("M_Tideborn_WaterOpaque", (0.02, 0.10, 0.42))
foam = make_lit("MI_Tideborn_Foam", (0.95, 0.93, 0.85), 0.7, emissive=(0.22, 0.20, 0.16))
rock = load(MAT + "/M_Tideborn_RockShore")

for a in list(actors()):
    lab = label(a); cn = cname(a)
    # Hide flat peach sky sphere/dome so SkyAtmosphere can show gradient
    if ("Sky" in lab) or ("Sky" in cn) or ("Atmosphere" in cn) or ("Fog" in cn) or ("Cloud" in cn):
        log("SKYACTOR lab=%s cn=%s" % (lab, cn))
    if ("SkyDome" in lab) or ("SkySphere" in lab) or ("Sky_Sphere" in cn) or ("BP_Sky_Sphere" in cn) or (lab == "TidebornEnv_SkyDome") or ("SkyDome" in cn):
        hide(a); log("HIDE skydome " + lab + "/" + cn)
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        unhide(a); log("SHOW " + cn)
    if lab == "TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000.0, 1500.0, 106.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 18.0, 1.0))
        if sand: force_apply(a, sand)
        log("LOCK SandBase")
    elif lab == "TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000.0, -800.0, 99.0), False, True)
        a.set_actor_scale3d(unreal.Vector(80.0, 18.0, 1.0)); force_apply(a, water)
    elif lab == "TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000.0, 400.0, 100.0), False, True)
        a.set_actor_scale3d(unreal.Vector(62.0, 11.0, 1.0)); force_apply(a, water)
        log("Shallows Y=400")
    elif lab == "TidebornEnv_WetSand_00":
        a.set_actor_location(unreal.Vector(1000.0, 610.0, 105.2), False, True)
        a.set_actor_scale3d(unreal.Vector(50.0, 1.7, 1.0)); force_apply(a, wet_dark)
        log("WetSand_00")
    elif lab == "TidebornEnv_WetSand_01":
        a.set_actor_location(unreal.Vector(1000.0, 685.0, 105.6), False, True)
        a.set_actor_scale3d(unreal.Vector(48.0, 1.5, 1.0)); force_apply(a, wet_mid)
        log("WetSand_01")
    elif lab == "TidebornEnv_FoamStrip":
        a.set_actor_location(unreal.Vector(1000.0, 545.0, 103.8), False, True)
        a.set_actor_scale3d(unreal.Vector(48.0, 0.55, 1.0)); force_apply(a, foam); unhide(a)
        log("FoamStrip Y=545 scY=0.55")
    elif lab == "TidebornEnv_BeachSlope":
        a.set_actor_location(unreal.Vector(1000.0, 600.0, 107.5), False, True)
        a.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.35))
        if sand: force_apply(a, sand)
        unhide(a); log("BeachSlope Z=107.5 scZ=1.35")
    elif "SandRamp" in lab:
        force_apply(a, wet_mid)
    elif ("Boulder" in lab) or lab.startswith("TidebornEnv_WLB_"):
        if rock: force_apply(a, rock)
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("real_time_capture", True)
            except Exception: pass
            try: c.set_editor_property("cubemap", None)
            except Exception: pass
            try: c.set_editor_property("intensity", 0.65)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.90, 0.72, 1.0))
            except Exception: pass
            try: c.recapture_sky()
            except Exception: pass
        log("SkyLight 0.65")
    if "DirectionalLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 3.0)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.84, 0.60, 1.0))
            except Exception: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-35.0, yaw=-90.0, roll=0.0), False)
        log("DirLight 3.0")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.022)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.85, 0.72, 0.55, 1.0))
            except Exception: pass
            try: c.set_editor_property("directional_inscattering_color", unreal.LinearColor(1.0, 0.78, 0.50, 1.0))
            except Exception: pass
        log("Fog 0.022")
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        unhide(a)
        try:
            try: a.set_editor_property("unbound", True)
            except Exception: pass
            s = a.get_editor_property("settings")
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 4000.0)
            except Exception: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.30, 0.98, 0.60, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_scene_color_tint", True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.12, 0.95, 0.78, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", -0.15)
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP temp=4000")
        except Exception as e:
            log("PP " + str(e))

for cmd in ("r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
            "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "ShowFlag.Cloud 1",
            "r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

try: log("save %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")

