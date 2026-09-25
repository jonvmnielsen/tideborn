# -*- coding: utf-8 -*-
"""v10b: brighten sand to v7 beige reading; kill cool waterline band; keep clamps."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v10b_result.txt"
DUMP = ROOT / "Tools" / "art" / "cove_dump_v10b.txt"
MAT = "/Game/Tideborn/Art/Materials"
TEX = "/Game/Tideborn/Art/Textures"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"

lines = []
def log(m):
    t = str(m); unreal.log("[V10b] " + t); lines.append(t)
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
def hide(a):
    try:
        a.set_actor_hidden_in_game(True); a.set_is_temporarily_hidden_in_editor(True)
        root = a.root_component
        if root:
            try: root.set_visibility(False, True)
            except Exception: pass
    except Exception: pass
def unhide(a):
    try:
        a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False)
        root = a.root_component
        if root:
            try: root.set_visibility(True, True)
            except Exception: pass
    except Exception: pass
def force_apply(a, mat):
    if not a or not mat: return
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(16):
            try: comp.set_material(i, mat)
            except Exception: break
def del_mat(name):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
def plane_y_range(a, default_half=50.0):
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    half = default_half * abs(float(sc.y))
    try:
        origin, extent = a.get_actor_bounds(False, False)
        if extent and float(extent.y) > 1.0:
            half = float(extent.y)
            return float(origin.y) - half, float(origin.y) + half, float(loc.z), half
    except Exception: pass
    return float(loc.y) - half, float(loc.y) + half, float(loc.z), half

def make_sand_grain(name, tint, tile=8.0, grain_mix=0.40):
    del_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    bc = load(TEX + "/Sand/sand_01_Diffuse")
    nrm = load(TEX + "/Sand/sand_01_nor_gl")
    uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    mul_uv = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -750, 0)
    sc = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -900, 80)
    sc.set_editor_property("r", float(tile))
    mel.connect_material_expressions(uv, "", mul_uv, "A")
    mel.connect_material_expressions(sc, "", mul_uv, "B")
    flat = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -500, -220)
    flat.set_editor_property("constant", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
    if bc:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, 0)
        ts.set_editor_property("texture", bc)
        mel.connect_material_expressions(mul_uv, "", ts, "UVs")
        boost = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -320, 40)
        bamt = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, 100)
        bamt.set_editor_property("r", 1.45)
        mel.connect_material_expressions(ts, "RGB", boost, "A")
        mel.connect_material_expressions(bamt, "", boost, "B")
        grain = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -180, 0)
        mel.connect_material_expressions(boost, "", grain, "A")
        mel.connect_material_expressions(flat, "", grain, "B")
        lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, 0, 0)
        mel.connect_material_expressions(flat, "", lerp, "A")
        mel.connect_material_expressions(grain, "", lerp, "B")
        alpha = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -180, 120)
        alpha.set_editor_property("r", float(grain_mix))
        mel.connect_material_expressions(alpha, "", lerp, "Alpha")
        mel.connect_material_property(lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
        log("sand_grain %s tint=%s mix=%.2f" % (name, tint, grain_mix))
    else:
        mel.connect_material_property(flat, "", unreal.MaterialProperty.MP_BASE_COLOR)
        log("sand_grain %s FLAT" % name)
    if nrm:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, 220)
        ts.set_editor_property("texture", nrm)
        try: ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        except Exception: pass
        mel.connect_material_expressions(mul_uv, "", ts, "UVs")
        mel.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_NORMAL)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, 0, 200)
    r.set_editor_property("r", 0.92)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, 0, 280)
    m.set_editor_property("r", 0.0)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, 0, 360)
    e.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    return mat

def make_lit(name, rgb, rough=0.9):
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
    e.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("mat %s rgb=%s" % (name, rgb))
    return mat

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load " + str(e))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in list(actors()):
    lab = label(a)
    if any(lab.startswith(p) for p in (
        "TidebornEnv_ShoreStep_", "TidebornEnv_FoamSeg_", "TidebornEnv_WetJag_", "TidebornEnv_ShoreLip"
    )) or lab in (
        "TidebornEnv_BeachSlope", "TidebornEnv_FoamStrip", "TidebornEnv_ShoreEdge",
        "TidebornEnv_ShoreLip", "TidebornEnv_ShoreLip2", "TidebornEnv_SkyBackdrop",
        "TidebornEnv_SandRamp", "TidebornEnv_WetSand_01"
    ):
        try: eas.destroy_actor(a); log("x " + lab)
        except Exception: hide(a)
    if "SkyDome" in lab:
        hide(a); log("HIDE " + lab)

sand = make_sand_grain("MI_Tideborn_SandWarm", (0.95, 0.58, 0.30), tile=8.0, grain_mix=0.40)
make_sand_grain("M_Tideborn_Sand", (0.95, 0.58, 0.30), tile=8.0, grain_mix=0.40)
wet_dark = make_lit("MI_Tideborn_SandWet", (0.16, 0.09, 0.045), rough=0.55)
water = make_lit("M_Tideborn_WaterOpaque", (0.03, 0.12, 0.40), rough=0.60)
rock = make_lit("M_Tideborn_RockShore", (0.42, 0.28, 0.16), rough=0.92)
make_lit("MI_Tideborn_RockDark", (0.42, 0.28, 0.16), rough=0.92)
foam = make_lit("MI_Tideborn_Foam", (0.78, 0.62, 0.42), rough=0.85)
foam_soft = make_lit("MI_Tideborn_FoamSoft", (0.70, 0.52, 0.34), rough=0.88)

plane = load("/Engine/BasicShapes/Plane")

for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000.0, 1500.0, 106.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 18.0, 1.0))
        force_apply(a, sand); unhide(a); log("LOCK SandBase")
    elif lab == "TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000.0, -1200.0, 99.0), False, True)
        a.set_actor_scale3d(unreal.Vector(95.0, 14.0, 1.0))
        force_apply(a, water); unhide(a); log("Ocean clamp")
    elif lab == "TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000.0, 50.0, 100.0), False, True)
        a.set_actor_scale3d(unreal.Vector(80.0, 9.0, 1.0))
        force_apply(a, water); unhide(a); log("Shallows clamp")
    elif lab == "TidebornEnv_WetSand_00":
        a.set_actor_location(unreal.Vector(1000.0, 700.0, 105.5), False, True)
        a.set_actor_scale3d(unreal.Vector(48.0, 2.0, 1.0))
        force_apply(a, wet_dark); unhide(a); log("WetSand_00 Y=700 scY=2 -> Y[600..800]")
    elif "Boulder" in lab or lab.startswith("TidebornEnv_WLB_"):
        force_apply(a, rock)

if plane and foam:
    for i, (x, y, scx, scy, yaw) in enumerate([
        (800.0, 628.0, 7.5, 0.50, -2.0),
        (980.0, 636.0, 8.0, 0.55, 2.0),
        (1160.0, 624.0, 7.5, 0.50, -1.5),
        (1320.0, 634.0, 7.0, 0.55, 2.5),
    ]):
        af = eas.spawn_actor_from_object(plane, unreal.Vector(x, y, 105.2), unreal.Rotator(0, yaw, 0))
        if af:
            af.set_actor_label("TidebornEnv_FoamSeg_%02d" % i)
            af.set_actor_scale3d(unreal.Vector(scx, scy, 1.0))
            force_apply(af, foam if i % 2 == 0 else foam_soft); unhide(af)
    log("FoamSeg x4 warm-sand tone")

for a in actors():
    cn = cname(a); lab = label(a)
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        unhide(a)
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity", 0.18)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.78, 0.50, 1.0))
            except Exception: pass
            try: c.set_editor_property("cubemap", None)
            except Exception: pass
            try: c.set_editor_property("real_time_capture", True)
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_color", unreal.LinearColor(0.70, 0.42, 0.20, 1.0))
            except Exception: pass
            try: c.recapture_sky()
            except Exception: pass
        log("SkyLight 0.18 warm")
    if "DirectionalLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 4.5)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.72, 0.42, 1.0))
            except Exception: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except Exception: pass
            try: c.set_editor_property("use_temperature", False)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-40.0, yaw=-90.0, roll=0.0), False)
        log("DirLight 4.5 warm")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.015)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.95, 0.72, 0.48, 1.0))
            except Exception: pass
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        unhide(a)
        try:
            try: a.set_editor_property("unbound", True)
            except Exception: pass
            s = a.get_editor_property("settings")
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 3400.0)
            except Exception: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.50, 0.95, 0.48, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_scene_color_tint", True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.28, 0.92, 0.58, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", 0.05)
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP temp=3400 gain lift")
        except Exception as e:
            log("PP " + str(e))

for cmd in ("r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
            "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

for a in actors():
    if "SkyLight" in cname(a):
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.recapture_sky()
            except Exception: pass

dump = []
for a in actors():
    lab = label(a)
    if not lab.startswith("TidebornEnv_"):
        continue
    if not any(k in lab for k in ("Sand", "Wet", "Foam", "Ocean", "Shallows", "Ground", "Step", "Lip", "Sky", "Slope", "Ramp")):
        continue
    y0, y1, z, _ = plane_y_range(a)
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    mats = []
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(2):
            try:
                m = comp.get_material(i)
                if m: mats.append(m.get_name())
            except Exception: break
        break
    line = "%s loc=(%.0f,%.0f,%.1f) sc=(%.2f,%.2f,%.2f) Y=[%.0f..%.0f] Z=%.1f %s" % (
        lab, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z, y0, y1, z, ",".join(mats) or "-")
    dump.append(line); log("DUMP " + line)

DUMP.write_text("\n".join(dump) + "\n", encoding="utf-8")
try: log("save %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")