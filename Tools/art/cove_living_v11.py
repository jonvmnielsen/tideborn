#-*- coding: utf-8 -*-
"""v11 polish on v10 baseline (4bfbdf4).
Focus: kill peach hairline (Ocean/Shallows seam + specular), clean Waterline mid band,
mild warm fog. DO NOT regress warmth. LOCK SandBase. No BeachSlope/ShoreStep.
"""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v11_result.txt"
DUMP = ROOT / "Tools" / "art" / "cove_dump_v11.txt"
MAT = "/Game/Tideborn/Art/Materials"
TEX = "/Game/Tideborn/Art/Textures"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"

lines = []
def log(m):
    t = str(m); unreal.log("[V11] " + t); lines.append(t)
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
    if not a or not mat: return 0
    n = 0
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(16):
            try: comp.set_material(i, mat); n += 1
            except Exception: break
    return n
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

def make_sand_grain(name, tint, tile=9.0, rough=0.98):
    del_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    bc = load(TEX + "/Sand/sand_01_Diffuse")
    nrm = load(TEX + "/Sand/sand_01_nor_gl")
    rg_tex = load(TEX + "/Sand/sand_01_Rough")
    uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -800, 0)
    mul_uv = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -650, 0)
    sc = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -800, 80)
    sc.set_editor_property("r", float(tile))
    mel.connect_material_expressions(uv, "", mul_uv, "A")
    mel.connect_material_expressions(sc, "", mul_uv, "B")
    tint_n = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, -200)
    tint_n.set_editor_property("constant", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
    if bc:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -450, 0)
        ts.set_editor_property("texture", bc)
        mel.connect_material_expressions(mul_uv, "", ts, "UVs")
        mul_col = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -200, 0)
        mel.connect_material_expressions(ts, "RGB", mul_col, "A")
        mel.connect_material_expressions(tint_n, "", mul_col, "B")
        mel.connect_material_property(mul_col, "", unreal.MaterialProperty.MP_BASE_COLOR)
        log("sand_grain %s tile=%.1f tint=%s" % (name, tile, tint))
    else:
        mel.connect_material_property(tint_n, "", unreal.MaterialProperty.MP_BASE_COLOR)
        log("sand_grain %s FLAT tint=%s" % (name, tint))
    if nrm:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -450, 180)
        ts.set_editor_property("texture", nrm)
        try: ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        except Exception: pass
        mel.connect_material_expressions(mul_uv, "", ts, "UVs")
        mel.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_NORMAL)
    if rg_tex:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -450, 320)
        ts.set_editor_property("texture", rg_tex)
        try: ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        except Exception: pass
        mel.connect_material_expressions(mul_uv, "", ts, "UVs")
        mel.connect_material_property(ts, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    else:
        r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -200, 200)
        r.set_editor_property("r", float(rough))
        mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -200, 280)
    m.set_editor_property("r", 0.0)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -200, 360)
    e.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    sp = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -200, 440)
    sp.set_editor_property("r", 0.0)
    try: mel.connect_material_property(sp, "", unreal.MaterialProperty.MP_SPECULAR)
    except Exception: pass
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    return mat

def make_lit(name, rgb, rough=0.9, emissive=None, specular=0.0):
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
    sp = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 360)
    sp.set_editor_property("r", float(specular))
    try: mel.connect_material_property(sp, "", unreal.MaterialProperty.MP_SPECULAR)
    except Exception: pass
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("mat %s rgb=%s spec=%.2f" % (name, rgb, specular))
    return mat

def make_water(name, rgb=(0.03, 0.12, 0.40), rough=0.92):
    """Deep blue, high roughness, specular=0 to kill peach sky mirror hairline."""
    del_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    c = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)
    r.set_editor_property("r", float(rough))
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 280)
    m.set_editor_property("r", 0.0)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    sp = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 360)
    sp.set_editor_property("r", 0.0)
    try: mel.connect_material_property(sp, "", unreal.MaterialProperty.MP_SPECULAR)
    except Exception: pass
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("water %s rough=%.2f specular=0" % (name, rough))
    return mat

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load " + str(e))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# ========== DUMP BEFORE ==========
dump_before = []
KEYS = ("SandBase", "Ground", "WetSand", "Foam", "BeachSlope", "Shallows", "Ocean",
        "SandRamp", "ShoreEdge", "ShoreStep", "ShoreLip", "SkyBack", "SkyDome", "WetJag")
for a in actors():
    lab = label(a)
    if not any(k in lab for k in KEYS):
        continue
    y0, y1, z, half = plane_y_range(a)
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
    dump_before.append(line); log("BEFORE " + line)

# ========== DESTROY regressors + WetSand_01 mid + geometric foam extras ==========
kill_exact = (
    "TidebornEnv_BeachSlope", "TidebornEnv_FoamStrip", "TidebornEnv_ShoreEdge",
    "TidebornEnv_ShoreLip", "TidebornEnv_ShoreLip2", "TidebornEnv_SkyBackdrop",
    "TidebornEnv_SandRamp", "TidebornEnv_WetSand_01",
)
kill_prefix = (
    "TidebornEnv_ShoreStep_", "TidebornEnv_FoamSeg_", "TidebornEnv_WetJag_",
    "TidebornEnv_ShoreLip",
)
for a in list(actors()):
    lab = label(a)
    do_kill = lab in kill_exact or any(lab.startswith(p) for p in kill_prefix)
    if lab == "TidebornEnv_SkyDome" or "SkyDome" in lab:
        hide(a); log("HIDE SkyDome " + lab)
        continue
    if do_kill:
        try:
            eas.destroy_actor(a); log("x " + lab)
        except Exception as e:
            hide(a); log("hide_fail_x %s %s" % (lab, e))

# ========== MATERIALS ==========
sand = make_sand_grain("MI_Tideborn_SandWarm", (0.85, 0.38, 0.16), tile=9.0)
make_sand_grain("M_Tideborn_Sand", (0.85, 0.38, 0.16), tile=9.0)
wet_dark = make_lit("MI_Tideborn_SandWet", (0.14, 0.08, 0.04), rough=0.40, specular=0.05)
# Keep mid mat asset warm but unused (no actor) so we don't leave cool remnant
make_lit("MI_Tideborn_SandWetMid", (0.18, 0.10, 0.05), rough=0.45, specular=0.05)
water = make_water("M_Tideborn_WaterOpaque", (0.03, 0.12, 0.40), rough=0.92)
rock = make_lit("M_Tideborn_RockShore", (0.42, 0.28, 0.16), rough=0.90)
make_lit("MI_Tideborn_RockDark", (0.42, 0.28, 0.16), rough=0.90)
foam = make_lit("MI_Tideborn_Foam", (0.92, 0.88, 0.78), rough=0.85, specular=0.0)
foam_soft = make_lit("MI_Tideborn_FoamSoft", (0.88, 0.84, 0.74), rough=0.88, specular=0.0)

plane = load("/Engine/BasicShapes/Plane")

# ========== LOCK SandBase + water: OVERLAP seam, extend Ocean -Y, Z~99.5 ==========
# Hairline was sky peeking at Ocean/Shallows abut. Overlap ~200uu; Ocean under Shallows.
# Ocean Y[-2400..-250] center=-1325 half=1075 -> scY=21.5  Z=99.5
# Shallows Y[-450..520] center=35 half=485 -> scY=9.7  Z=99.8  (overlap -450..-250)
for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000.0, 1500.0, 106.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 18.0, 1.0))
        force_apply(a, sand); unhide(a)
        log("LOCK SandBase (1000,1500,106) sc(45,18)")
    elif lab == "TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000.0, -1325.0, 99.5), False, True)
        a.set_actor_scale3d(unreal.Vector(100.0, 21.5, 1.0))
        force_apply(a, water); unhide(a)
        log("Ocean Y~[-2400..-250] Z=99.5 (extend -Y + overlap)")
    elif lab == "TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000.0, 35.0, 99.8), False, True)
        a.set_actor_scale3d(unreal.Vector(85.0, 9.7, 1.0))
        force_apply(a, water); unhide(a)
        log("Shallows Y~[-450..520] Z=99.8 (over Ocean)")
    elif lab == "TidebornEnv_Ground":
        a.set_actor_location(unreal.Vector(1000.0, 2800.0, 105.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 16.0, 1.0))
        unhide(a)
    elif "Boulder" in lab or lab.startswith("TidebornEnv_WLB_"):
        force_apply(a, rock)
        loc = a.get_actor_location()
        if 800.0 <= loc.x <= 1200.0 and 200.0 <= loc.y <= 900.0:
            new_x = 520.0 if loc.x < 1000.0 else 1480.0
            a.set_actor_location(unreal.Vector(new_x, loc.y, loc.z), False, True)
            log("MOUTH aside %s -> X=%.0f" % (lab, new_x))

# ========== ONE dark WetSand only ==========
has_w0 = False
for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_WetSand_00":
        a.set_actor_location(unreal.Vector(1000.0, 680.0, 105.4), False, True)
        a.set_actor_scale3d(unreal.Vector(48.0, 2.2, 1.0))
        force_apply(a, wet_dark); unhide(a)
        has_w0 = True; log("WetSand_00 Y=680 Z=105.4 sc(48,2.2) dark-only")
    elif lab.startswith("TidebornEnv_WetSand_") and lab != "TidebornEnv_WetSand_00":
        try:
            eas.destroy_actor(a); log("x extra wet " + lab)
        except Exception:
            hide(a); log("hide extra wet " + lab)

if not has_w0 and plane:
    a = eas.spawn_actor_from_object(
        plane, unreal.Vector(1000.0, 680.0, 105.4), unreal.Rotator(0, 0, 0))
    if a:
        a.set_actor_label("TidebornEnv_WetSand_00")
        a.set_actor_scale3d(unreal.Vector(48.0, 2.2, 1.0))
        force_apply(a, wet_dark); unhide(a)
        log("SPAWN WetSand_00")

# ========== Soft cream foam segs only (thin, inland Y>=620) ==========
if plane and foam:
    foam_specs = [
        (800.0, 640.0, 7.0, 0.45, -1.5),
        (1000.0, 648.0, 8.0, 0.50, 2.0),
        (1200.0, 642.0, 7.0, 0.45, -1.0),
    ]
    for i, (x, y, scx, scy, yaw) in enumerate(foam_specs):
        af = eas.spawn_actor_from_object(
            plane, unreal.Vector(x, y, 104.4 + 0.05 * (i % 2)),
            unreal.Rotator(0, yaw, 0))
        if af:
            af.set_actor_label("TidebornEnv_FoamSeg_%02d" % i)
            af.set_actor_scale3d(unreal.Vector(scx, scy, 1.0))
            force_apply(af, foam if i % 2 == 0 else foam_soft); unhide(af)
            y0, y1, z, _ = plane_y_range(af)
            if y0 < 610.0:
                af.set_actor_location(unreal.Vector(x, 640.0, 104.4), False, True)
                log("FoamSeg_%02d nudged inland" % i)
            log("FoamSeg_%02d Y=[%.0f..%.0f]" % (i, y0, y1))
    log("SPAWN FoamSeg x3 cream soft")

# ========== LIGHTING / fog dens 0.025 warm peach-grey ==========
for a in actors():
    cn = cname(a); lab = label(a)
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        unhide(a); log("SHOW " + cn)
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity", 0.15)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.80, 0.55, 1.0))
            except Exception: pass
            try: c.set_editor_property("real_time_capture", True)
            except Exception: pass
            try: c.set_editor_property("cubemap", None)
            except Exception: pass
            try: c.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_is_black", False)
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_color", unreal.LinearColor(0.55, 0.35, 0.18, 1.0))
            except Exception: pass
            try: c.recapture_sky()
            except Exception: pass
        log("SkyLight intensity=0.15")
    if "DirectionalLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("use_temperature", False)
            except Exception: pass
            try: c.set_editor_property("intensity", 4.0)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.75, 0.45, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 1.0)
            except Exception: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-40.0, yaw=-90.0, roll=0.0), False)
        log("DirLight 4.0 warm pitch=-40 yaw=-90")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.025)
            except Exception: pass
            try: c.set_editor_property("fog_height_falloff", 0.22)
            except Exception: pass
            # warm peach-grey — soft horizon, don't cool sand
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.92, 0.78, 0.62, 1.0))
            except Exception: pass
            try: c.set_editor_property("directional_inscattering_color", unreal.LinearColor(1.0, 0.82, 0.58, 1.0))
            except Exception: pass
            try: c.set_editor_property("volumetric_fog", True)
            except Exception: pass
            try: c.set_editor_property("start_distance", 800.0)
            except Exception: pass
        log("Fog dens=0.025 warm peach-grey")
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        unhide(a)
        try:
            try: a.set_editor_property("unbound", True)
            except Exception: pass
            s = a.get_editor_property("settings")
            for lut_prop in ("color_grading_lut", "look_up_table"):
                try: s.set_editor_property(lut_prop, None)
                except Exception: pass
            try:
                s.set_editor_property("override_color_grading_intensity", True)
                s.set_editor_property("color_grading_intensity", 0.0)
            except Exception: pass
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 3400.0)
            except Exception: pass
            try:
                s.set_editor_property("override_white_tint", True)
                s.set_editor_property("white_tint", 0.0)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", -0.1)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_method", True)
                s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            except Exception: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.45, 0.92, 0.48, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_scene_color_tint", True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.25, 0.90, 0.60, 1.0))
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP white_temp=3400 gain=(1.45,0.92,0.48)")
        except Exception as e:
            log("PP " + str(e))

for cmd in ("r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
            "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "ShowFlag.Cloud 1",
            "r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

for a in actors():
    if "SkyLight" in cname(a):
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.recapture_sky()
            except Exception: pass

# ========== DUMP AFTER + audit ==========
dump_after = []
bad = []
for a in actors():
    lab = label(a)
    if not any(k in lab for k in KEYS + ("FoamSeg",)):
        continue
    y0, y1, z, half = plane_y_range(a)
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
    dump_after.append(line); log("AFTER " + line)
    if lab in ("TidebornEnv_Ocean", "TidebornEnv_Shallows"):
        continue
    if any(k in lab for k in ("Sand", "Slope", "Ramp", "Ground", "Wet", "Beach", "Step", "Lip")):
        if y0 < 550.0 and z >= 98.5:
            bad.append(line)
            log("WARN_SAND_NEAR_WATER " + line)

# Seam check: Ocean maxY should be >= Shallows minY (overlap)
ocean_y1 = shallows_y0 = None
for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_Ocean":
        y0, y1, z, _ = plane_y_range(a); ocean_y1 = y1
        log("SEAM Ocean Y1=%.0f Z=%.1f" % (y1, z))
    elif lab == "TidebornEnv_Shallows":
        y0, y1, z, _ = plane_y_range(a); shallows_y0 = y0
        log("SEAM Shallows Y0=%.0f Z=%.1f" % (y0, z))
if ocean_y1 is not None and shallows_y0 is not None:
    if ocean_y1 >= shallows_y0 - 1.0:
        log("OK water overlap Ocean.Y1=%.0f >= Shallows.Y0=%.0f" % (ocean_y1, shallows_y0))
    else:
        log("FAIL water GAP Ocean.Y1=%.0f < Shallows.Y0=%.0f" % (ocean_y1, shallows_y0))

if bad:
    for b in bad:
        log("FAIL sand/near-water " + b)
else:
    log("OK no sand plane with Ymin<550 at Z>=98.5")

left = [label(a) for a in actors() if any(k in label(a) for k in ("ShoreStep", "ShoreLip", "BeachSlope", "SkyBackdrop"))]
if left:
    log("FAIL regressors remain: " + ",".join(left))
else:
    log("OK no ShoreStep/ShoreLip/BeachSlope/SkyBackdrop")

wet_left = [label(a) for a in actors() if "WetSand" in label(a)]
log("WetSand actors: " + ",".join(wet_left) if wet_left else "WetSand actors: NONE")

DUMP.write_text(
    "BEFORE\n" + "\n".join(dump_before) + "\n\nAFTER\n" + "\n".join(dump_after) + "\n",
    encoding="utf-8")

try: log("save %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
