#-*- coding: utf-8 -*-
"""v10: restore v7 warmth + keep v9 Ocean/Shallows clamps. Delete ShoreStep/sky-wall.
LOCK forever: SandBase (1000,1500,106) sc(45,18); Ocean Y~[-1900..-500] Z=99;
Shallows Y~[-400..500] Z=100; no sand plane over Ocean Y at Z>=99; mouth open.
"""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v10_result.txt"
DUMP = ROOT / "Tools" / "art" / "cove_dump_v10.txt"
MAT = "/Game/Tideborn/Art/Materials"
TEX = "/Game/Tideborn/Art/Textures"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"

lines = []
def log(m):
    t = str(m); unreal.log("[V10] " + t); lines.append(t)
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
    """Orange-warm albedo WITH sand texture grain, emissive=0."""
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
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    return mat

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
    log("mat %s rgb=%s" % (name, rgb))
    return mat

def make_water(name, rgb=(0.03, 0.12, 0.40), rough=0.55):
    """Deep blue, roughness up (v7 warmth + readable water)."""
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
    m.set_editor_property("r", 0.02)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("water %s rough=%.2f" % (name, rough))
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

# ========== DESTROY regressors ==========
kill_exact = (
    "TidebornEnv_BeachSlope", "TidebornEnv_FoamStrip", "TidebornEnv_ShoreEdge",
    "TidebornEnv_ShoreLip", "TidebornEnv_ShoreLip2", "TidebornEnv_SkyBackdrop",
    "TidebornEnv_SandRamp",
)
kill_prefix = (
    "TidebornEnv_ShoreStep_", "TidebornEnv_FoamSeg_", "TidebornEnv_WetJag_",
    "TidebornEnv_ShoreLip",
)
for a in list(actors()):
    lab = label(a)
    do_kill = lab in kill_exact or any(lab.startswith(p) for p in kill_prefix)
    # Also hide SkyDome (prefer SkyAtmosphere)
    if lab == "TidebornEnv_SkyDome" or "SkyDome" in lab:
        hide(a); log("HIDE SkyDome " + lab)
        continue
    if do_kill:
        try:
            eas.destroy_actor(a); log("x " + lab)
        except Exception as e:
            hide(a); log("hide_fail_x %s %s" % (lab, e))

# ========== MATERIALS (v7 warmth + grain) ==========
# Orange-warm (0.85,0.38,0.16) WITH grain — tint multiplies diffuse so keep strong orange
sand = make_sand_grain("MI_Tideborn_SandWarm", (0.85, 0.38, 0.16), tile=9.0)
make_sand_grain("M_Tideborn_Sand", (0.85, 0.38, 0.16), tile=9.0)
wet_dark = make_lit("MI_Tideborn_SandWet", (0.14, 0.08, 0.04), rough=0.40)
wet_mid = make_lit("MI_Tideborn_SandWetMid", (0.22, 0.12, 0.06), rough=0.48)
water = make_water("M_Tideborn_WaterOpaque", (0.03, 0.12, 0.40), rough=0.55)
rock = make_lit("M_Tideborn_RockShore", (0.42, 0.28, 0.16), rough=0.90)
make_lit("MI_Tideborn_RockDark", (0.42, 0.28, 0.16), rough=0.90)
# Cream foam — NOT cyan, NOT bright emissive
foam = make_lit("MI_Tideborn_Foam", (0.92, 0.88, 0.78), rough=0.70, emissive=None)
foam_soft = make_lit("MI_Tideborn_FoamSoft", (0.88, 0.84, 0.74), rough=0.75, emissive=None)

plane = load("/Engine/BasicShapes/Plane")

# ========== LOCK SandBase + water clamps (v9) ==========
for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000.0, 1500.0, 106.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 18.0, 1.0))
        force_apply(a, sand); unhide(a)
        log("LOCK SandBase (1000,1500,106) sc(45,18)")
    elif lab == "TidebornEnv_Ocean":
        # Y roughly [-1900..-500] Z=99  (center -1200, halfY=700 -> scY=14)
        a.set_actor_location(unreal.Vector(1000.0, -1200.0, 99.0), False, True)
        a.set_actor_scale3d(unreal.Vector(95.0, 14.0, 1.0))
        force_apply(a, water); unhide(a)
        log("Ocean Y~[-1900..-500] Z=99")
    elif lab == "TidebornEnv_Shallows":
        # Y roughly [-400..500] Z=100  (center 50, halfY=450 -> scY=9)
        a.set_actor_location(unreal.Vector(1000.0, 50.0, 100.0), False, True)
        a.set_actor_scale3d(unreal.Vector(80.0, 9.0, 1.0))
        force_apply(a, water); unhide(a)
        log("Shallows Y~[-400..500] Z=100")
    elif lab == "TidebornEnv_Ground":
        a.set_actor_location(unreal.Vector(1000.0, 2800.0, 105.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 16.0, 1.0))
        unhide(a)
    elif "Boulder" in lab or lab.startswith("TidebornEnv_WLB_"):
        force_apply(a, rock)
        # Keep mouth open: push mid-X blockers aside
        loc = a.get_actor_location()
        if 800.0 <= loc.x <= 1200.0 and 200.0 <= loc.y <= 900.0:
            new_x = 520.0 if loc.x < 1000.0 else 1480.0
            a.set_actor_location(unreal.Vector(new_x, loc.y, loc.z), False, True)
            log("MOUTH aside %s -> X=%.0f" % (lab, new_x))

# ========== WetSand dark band (v7 composition) ==========
has_w0 = False
for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_WetSand_00":
        a.set_actor_location(unreal.Vector(1000.0, 650.0, 105.5), False, True)
        a.set_actor_scale3d(unreal.Vector(50.0, 2.5, 1.0))
        force_apply(a, wet_dark); unhide(a)
        has_w0 = True; log("WetSand_00 Y=650 Z=105.5 sc(50,2.5)")
    elif lab == "TidebornEnv_WetSand_01":
        # Keep a soft mid band inland of wet00, still on sand side
        a.set_actor_location(unreal.Vector(1000.0, 740.0, 105.9), False, True)
        a.set_actor_scale3d(unreal.Vector(40.0, 1.6, 1.0))
        force_apply(a, wet_mid); unhide(a)
        log("WetSand_01 mid Y=740")

if not has_w0 and plane:
    a = eas.spawn_actor_from_object(
        plane, unreal.Vector(1000.0, 650.0, 105.5), unreal.Rotator(0, 0, 0))
    if a:
        a.set_actor_label("TidebornEnv_WetSand_00")
        a.set_actor_scale3d(unreal.Vector(50.0, 2.5, 1.0))
        force_apply(a, wet_dark); unhide(a)
        log("SPAWN WetSand_00")

# ========== Foam: 4 short cream segments, staggered Y 620-640, scY~0.6 ==========
if plane and foam:
    foam_specs = [
        (780.0, 625.0, 8.0, 0.55, -2.0),
        (960.0, 635.0, 9.0, 0.60, 2.5),
        (1140.0, 622.0, 8.5, 0.55, -1.5),
        (1300.0, 638.0, 7.5, 0.60, 3.0),
    ]
    for i, (x, y, scx, scy, yaw) in enumerate(foam_specs):
        af = eas.spawn_actor_from_object(
            plane, unreal.Vector(x, y, 104.2 + 0.1 * (i % 2)),
            unreal.Rotator(0, yaw, 0))
        if af:
            af.set_actor_label("TidebornEnv_FoamSeg_%02d" % i)
            af.set_actor_scale3d(unreal.Vector(scx, scy, 1.0))
            force_apply(af, foam if i % 2 == 0 else foam_soft); unhide(af)
            y0, y1, z, _ = plane_y_range(af)
            # Guard: must stay on sand side (Y >= 600)
            if y0 < 600.0:
                af.set_actor_location(unreal.Vector(x, 630.0, 104.3), False, True)
                log("FoamSeg_%02d nudged inland" % i)
            log("FoamSeg_%02d Y=[%.0f..%.0f]" % (i, y0, y1))
    log("SPAWN FoamSeg x4 cream scY~0.6")

# ========== LIGHTING / PP (v7 warmth) — prefer SkyAtmosphere, NO sky-wall ==========
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
        log("SkyLight intensity=0.15 cubemap=None")
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
            try: c.set_editor_property("fog_density", 0.015)
            except Exception: pass
            try: c.set_editor_property("fog_height_falloff", 0.25)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.90, 0.72, 0.50, 1.0))
            except Exception: pass
            try: c.set_editor_property("directional_inscattering_color", unreal.LinearColor(1.0, 0.78, 0.48, 1.0))
            except Exception: pass
            try: c.set_editor_property("volumetric_fog", True)
            except Exception: pass
        log("Fog dens=0.015 warm")
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

# ========== DUMP AFTER + sand-in-water audit ==========
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
    # NO sand-colored plane may cover Ocean Y at Z>=99
    if lab in ("TidebornEnv_Ocean", "TidebornEnv_Shallows"):
        continue
    if any(k in lab for k in ("Sand", "Slope", "Ramp", "Ground", "Wet", "Beach", "Step", "Lip")):
        # Ocean Y roughly < -500; also flag any Ymin < 550 at Z>=99 as risky
        if y0 < 550.0 and z >= 98.5:
            bad.append(line)
            log("WARN_SAND_NEAR_WATER " + line)

if bad:
    for b in bad:
        log("FAIL sand/near-water " + b)
else:
    log("OK no sand plane with Ymin<550 at Z>=98.5")

# Explicit regressor check
left = [label(a) for a in actors() if any(k in label(a) for k in ("ShoreStep", "ShoreLip", "BeachSlope", "SkyBackdrop"))]
if left:
    log("FAIL regressors remain: " + ",".join(left))
else:
    log("OK no ShoreStep/ShoreLip/BeachSlope/SkyBackdrop")

DUMP.write_text(
    "BEFORE\n" + "\n".join(dump_before) + "\n\nAFTER\n" + "\n".join(dump_after) + "\n",
    encoding="utf-8")

try: log("save %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
