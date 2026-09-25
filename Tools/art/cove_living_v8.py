# -*- coding: utf-8 -*-
"""v8: living-shore polish — sand grain, foam strip, beach slope, wet bands, soft sky.
LOCK: SandBase (1000,1500,106) sc(45,18); water Z<sand; warm PP/SkyLight; mouth open.
"""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v8_result.txt"
DUMP = ROOT / "Tools" / "art" / "cove_dump_v8_after.txt"
MAT = "/Game/Tideborn/Art/Materials"
TEX = "/Game/Tideborn/Art/Textures"
MESH = "/Game/Tideborn/Art/Meshes"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
FBX_SLOPE = ROOT / "Tools" / "art" / "export" / "SM_TidebornBeachSlope.fbx"

lines = []
def log(m):
    t = str(m); unreal.log("[V8] " + t); lines.append(t)
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

def force_apply(a, mat):
    if not a or not mat: return 0
    n = 0
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(16):
            try: comp.set_material(i, mat); n += 1
            except Exception: break
        try: comp.set_editor_property("override_materials", [mat] * 8)
        except Exception: pass
    return n

def del_mat(name):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)

def make_sand_grain(name, tint, tile=10.0, rough=0.96):
    """Warm sand with tiling diffuse grain (sand_01) multiplied by warm tint."""
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
        log("sand_grain %s textured tile=%.1f tint=%s" % (name, tile, tint))
    else:
        # Procedural noise fallback so sand isn't flat fill
        noise = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, -450, 0)
        try:
            noise.set_editor_property("scale", 28.0)
            noise.set_editor_property("levels", 4)
        except Exception: pass
        # Lerp tint dark/light via noise
        tint2 = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -450, -160)
        tint2.set_editor_property("constant", unreal.LinearColor(
            max(0.05, tint[0]*0.72), max(0.04, tint[1]*0.72), max(0.03, tint[2]*0.72), 1.0))
        lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -200, 0)
        mel.connect_material_expressions(tint2, "", lerp, "A")
        mel.connect_material_expressions(tint_n, "", lerp, "B")
        mel.connect_material_expressions(noise, "", lerp, "Alpha")
        mel.connect_material_property(lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
        log("sand_grain %s NOISE fallback tint=%s" % (name, tint))
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
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
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
    log("mat %s rgb=%s rough=%.2f" % (name, rgb, rough))
    return mat

def make_water_var(name, rgb=(0.02, 0.10, 0.38)):
    """Deeper blue water with slight roughness noise variation."""
    del_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    # Slight darken variation via noise multiply
    noise = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, -400, -160)
    try:
        noise.set_editor_property("scale", 12.0)
        noise.set_editor_property("levels", 3)
    except Exception: pass
    dark = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, -280)
    dark.set_editor_property("constant", unreal.LinearColor(rgb[0]*0.55, rgb[1]*0.55, rgb[2]*0.75, 1.0))
    lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -180, 0)
    mel.connect_material_expressions(dark, "", lerp, "A")
    mel.connect_material_expressions(col, "", lerp, "B")
    mel.connect_material_expressions(noise, "", lerp, "Alpha")
    mel.connect_material_property(lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    # Roughness variation
    r0 = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)
    r0.set_editor_property("r", 0.18)
    r1 = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 260)
    r1.set_editor_property("r", 0.55)
    noise2 = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, -400, 320)
    try:
        noise2.set_editor_property("scale", 22.0)
        noise2.set_editor_property("levels", 2)
    except Exception: pass
    lr = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -180, 220)
    mel.connect_material_expressions(r0, "", lr, "A")
    mel.connect_material_expressions(r1, "", lr, "B")
    mel.connect_material_expressions(noise2, "", lr, "Alpha")
    mel.connect_material_property(lr, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -180, 320)
    m.set_editor_property("r", 0.05)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("water_var %s rgb=%s" % (name, rgb))
    return mat

def import_fbx(path, dest):
    task = unreal.AssetImportTask()
    task.filename = str(path)
    task.destination_path = dest
    task.automated = True
    task.save = True
    task.replace_existing = True
    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = False
    options.import_materials = False
    options.import_textures = False
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.auto_generate_collision = True
    options.static_mesh_import_data.import_uniform_scale = 1.0
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.imported_object_paths) if task.imported_object_paths else []
    log("import %s -> %s" % (path.name, paths))
    return paths

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load " + str(e))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# --- Materials ---
# Warm beige tint over sand grain (parent v7 PASS palette)
sand = make_sand_grain("MI_Tideborn_SandWarm", (1.35, 0.95, 0.62), tile=9.0, rough=0.97)
make_sand_grain("M_Tideborn_Sand", (1.35, 0.95, 0.62), tile=9.0, rough=0.97)
wet_dark = make_lit("MI_Tideborn_SandWet", (0.09, 0.06, 0.04), rough=0.35)
wet_mid = make_lit("MI_Tideborn_SandWetMid", (0.16, 0.10, 0.06), rough=0.42)
water = make_water_var("M_Tideborn_WaterOpaque", (0.02, 0.10, 0.40))
rock = make_lit("M_Tideborn_RockShore", (0.20, 0.15, 0.11), rough=0.94)
make_lit("MI_Tideborn_RockDark", (0.20, 0.15, 0.11), rough=0.94)
foam = make_lit("MI_Tideborn_Foam", (0.92, 0.90, 0.82), rough=0.55,
                emissive=(0.08, 0.075, 0.06))

# Destroy previous v8 helpers if re-running
for a in list(actors()):
    lab = label(a)
    if lab in ("TidebornEnv_FoamStrip", "TidebornEnv_BeachSlope", "TidebornEnv_WetSand_01"):
        try:
            eas.destroy_actor(a); log("x old " + lab)
        except Exception as e:
            log("destroy " + lab + " " + str(e))

# --- Import / place beach slope ---
slope_mesh = None
slope_ok = False
if FBX_SLOPE.exists():
    paths = import_fbx(FBX_SLOPE, MESH)
    for p in paths:
        a = load(p)
        if isinstance(a, unreal.StaticMesh):
            slope_mesh = a; break
    if not slope_mesh:
        slope_mesh = load(MESH + "/SM_TidebornBeachSlope")
else:
    log("MISSING FBX " + str(FBX_SLOPE))

if slope_mesh:
    # Probe local bounds to choose scale so world ~50m x 15m
    try:
        box = slope_mesh.get_bounding_box()
        ext = box.max - box.min
        bx, by = abs(float(ext.x)), abs(float(ext.y))
        log("slope_bounds local=(%.1f,%.1f,%.1f)" % (bx, by, abs(float(ext.z))))
    except Exception as e:
        bx, by = 5000.0, 1500.0
        log("bounds_fail " + str(e))
    # Target world size ~5000 x 1500 uu
    sx = 5000.0 / bx if bx > 1.0 else 1.0
    sy = 1500.0 / by if by > 1.0 else 1.0
    # Clamp crazy scales
    if sx > 50 or sy > 50 or sx < 0.01 or sy < 0.01:
        log("slope_scale_REJECT sx=%.4f sy=%.4f — skip place" % (sx, sy))
        slope_mesh = None
    else:
        # Prefer uniform-ish; keep Z similar to X so drop stays ~100uu
        sz = (sx + sy) * 0.5
        a = eas.spawn_actor_from_object(
            slope_mesh, unreal.Vector(1000.0, 620.0, 106.0),
            unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
        if a:
            a.set_actor_label("TidebornEnv_BeachSlope")
            a.set_actor_scale3d(unreal.Vector(sx, sy, sz))
            force_apply(a, sand)
            unhide(a)
            # Validate extent after place
            loc = a.get_actor_location(); sc = a.get_actor_scale3d()
            # Rough world half extents from local * scale
            half_x = 0.5 * bx * sc.x
            half_y = 0.5 * by * sc.y
            bad = (half_x < 500 or half_x > 8000 or half_y < 200 or half_y > 4000)
            if bad:
                try:
                    eas.destroy_actor(a)
                    log("slope_void_or_wrong deleted half=(%.0f,%.0f)" % (half_x, half_y))
                except Exception as e:
                    log("slope_del_fail " + str(e))
            else:
                slope_ok = True
                log("PLACE BeachSlope sc=(%.3f,%.3f,%.3f) half=(%.0f,%.0f) OK" % (
                    sc.x, sc.y, sc.z, half_x, half_y))

# --- LOCK SandBase + water + wet bands + foam ---
wetsand0 = None
for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000.0, 1500.0, 106.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 18.0, 1.0))
        force_apply(a, sand); unhide(a)
        log("LOCK SandBase (1000,1500,106) sc(45,18)")
    elif lab == "TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000.0, -800.0, 99.0), False, True)
        a.set_actor_scale3d(unreal.Vector(80.0, 18.0, 1.0))
        force_apply(a, water); unhide(a)
        log("Ocean Z=99")
    elif lab == "TidebornEnv_Shallows":
        # Keep water inland edge near wet; Z < sand
        a.set_actor_location(unreal.Vector(1000.0, 420.0, 100.0), False, True)
        a.set_actor_scale3d(unreal.Vector(62.0, 12.0, 1.0))
        force_apply(a, water); unhide(a)
        log("Shallows Z=100 Y=420")
    elif lab == "TidebornEnv_WetSand_00" or (lab.startswith("TidebornEnv_WetSand_") and lab != "TidebornEnv_WetSand_01"):
        # Darker wet band nearer water, slight Z overlap
        a.set_actor_location(unreal.Vector(1000.0, 620.0, 105.3), False, True)
        a.set_actor_scale3d(unreal.Vector(50.0, 1.8, 1.0))
        force_apply(a, wet_dark); unhide(a)
        wetsand0 = a
        log("WetSand_00 dark Y=620 scY=1.8")
    elif "SandRamp" in lab:
        # Keep tiny existing ramp if present; wet mid
        force_apply(a, wet_mid)
        log("KEEP SandRamp wet_mid")
    elif "Boulder" in lab or lab.startswith("TidebornEnv_WLB_"):
        force_apply(a, rock)

# Second wet band (lighter dark) inland of first — softens hard join
plane = load("/Engine/BasicShapes/Plane")
if plane:
    a1 = eas.spawn_actor_from_object(
        plane, unreal.Vector(1000.0, 690.0, 105.7),
        unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
    if a1:
        a1.set_actor_label("TidebornEnv_WetSand_01")
        a1.set_actor_scale3d(unreal.Vector(48.0, 1.6, 1.0))
        force_apply(a1, wet_mid); unhide(a1)
        log("SPAWN WetSand_01 mid Y=690 scY=1.6")
    # Foam bright strip at water edge (thin Y)
    af = eas.spawn_actor_from_object(
        plane, unreal.Vector(1000.0, 560.0, 104.2),
        unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
    if af:
        af.set_actor_label("TidebornEnv_FoamStrip")
        af.set_actor_scale3d(unreal.Vector(46.0, 0.28, 1.0))
        force_apply(af, foam); unhide(af)
        log("SPAWN FoamStrip Y=560 scY=0.28 cream")

if not wetsand0 and plane:
    a = eas.spawn_actor_from_object(
        plane, unreal.Vector(1000.0, 620.0, 105.3),
        unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
    if a:
        a.set_actor_label("TidebornEnv_WetSand_00")
        a.set_actor_scale3d(unreal.Vector(50.0, 1.8, 1.0))
        force_apply(a, wet_dark); unhide(a)
        log("SPAWN WetSand_00")

# --- Sky / lighting: mild SkyAtmosphere + low fog, KEEP warm (no lavender) ---
for a in actors():
    cn = cname(a); lab = label(a)
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        unhide(a); log("KEEP " + cn)
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("real_time_capture", True)
            except Exception: pass
            try: c.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
            except Exception: pass
            try: c.set_editor_property("cubemap", None)
            except Exception: pass
            # Moderate warm — not crushed flat peach, not cool lavender
            try: c.set_editor_property("intensity", 0.55)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.88, 0.70, 1.0))
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_is_black", False)
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_color", unreal.LinearColor(0.55, 0.40, 0.26, 1.0))
            except Exception: pass
            try: c.recapture_sky()
            except Exception: pass
        log("SkyLight 0.55 warm realtime")
    if "DirectionalLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 2.8)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.82, 0.58, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 0.7)
            except Exception: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except Exception: pass
            try: c.set_editor_property("use_temperature", False)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-38.0, yaw=-90.0, roll=0.0), False)
        log("DirLight warm 2.8 pitch=-38")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.018)
            except Exception: pass
            try: c.set_editor_property("fog_height_falloff", 0.25)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.78, 0.68, 0.52, 1.0))
            except Exception: pass
            try: c.set_editor_property("directional_inscattering_color", unreal.LinearColor(1.0, 0.80, 0.55, 1.0))
            except Exception: pass
            try: c.set_editor_property("directional_inscattering_exponent", 8.0)
            except Exception: pass
        log("Fog density=0.018 warm soft")
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
            # Warm but allow sky gradient (not crushed 3400 peach slab)
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 4200.0)
            except Exception: pass
            try:
                s.set_editor_property("override_white_tint", True)
                s.set_editor_property("white_tint", 0.02)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", -0.2)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_method", True)
                s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            except Exception: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.28, 0.98, 0.62, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_color_gamma", True)
                s.set_editor_property("color_gamma", unreal.Vector4(1.02, 1.00, 0.96, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_scene_color_tint", True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.10, 0.94, 0.78, 1.0))
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP white_temp=4200 gain=(1.28,0.98,0.62)")
        except Exception as e:
            log("PP " + str(e))
    if lab == "TidebornEnv_SkyDome":
        unhide(a)

for cmd in ("r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
            "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

# Dump
dump_lines = []
for a in actors():
    lab = label(a)
    if not lab.startswith("Tideborn"): continue
    if not any(k in lab for k in ("SandBase","Ocean","Shallows","WetSand","ShoreEdge","WLB_",
                                   "Boulder","SandRamp","Ground","Foam","BeachSlope")):
        continue
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    mats = []
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(2):
            try:
                m = comp.get_material(i)
                if m: mats.append(m.get_name())
            except Exception: break
        break
    dump_lines.append("%s loc=(%.0f,%.0f,%.1f) sc=(%.2f,%.2f,%.2f) %s" % (
        lab, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z, ",".join(mats) or "-"))
DUMP.write_text("\n".join(dump_lines) + "\n", encoding="utf-8")
log("dump_after %d slope_ok=%s" % (len(dump_lines), slope_ok))

try: log("save %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")

