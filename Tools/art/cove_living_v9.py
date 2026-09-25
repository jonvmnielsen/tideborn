# -*- coding: utf-8 -*-
"""v9: fix sand-strip-in-water, soft sky gradient, multi foam, readable BeachSlope.
LOCK: SandBase (1000,1500,106) sc(45,18); water Z < sand Z; warm grain + mouth open.
"""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v9_result.txt"
DUMP = ROOT / "Tools" / "art" / "cove_dump_v9.txt"
MAT = "/Game/Tideborn/Art/Materials"
TEX = "/Game/Tideborn/Art/Textures"
MESH = "/Game/Tideborn/Art/Meshes"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
FBX_SLOPE = ROOT / "Tools" / "art" / "export" / "SM_TidebornBeachSlope.fbx"
FBX_EDGE = ROOT / "Tools" / "art" / "export" / "SM_TidebornShoreEdge.fbx"

lines = []
def log(m):
    t = str(m); unreal.log("[V9] " + t); lines.append(t)
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

def plane_y_range(a, default_half=50.0):
    """Approx world Y coverage for plane-like actors (Engine Plane half=50*scale)."""
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    half = default_half * abs(float(sc.y))
    # Prefer mesh bounds if available
    try:
        origin, extent = a.get_actor_bounds(False, False)
        if extent and float(extent.y) > 1.0:
            half = float(extent.y)
            return float(origin.y) - half, float(origin.y) + half, float(loc.z), half
    except Exception:
        pass
    return float(loc.y) - half, float(loc.y) + half, float(loc.z), half

def make_sand_grain(name, tint, tile=9.0, rough=0.97):
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
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    return mat

def make_lit(name, rgb, rough=0.9, emissive=None, opacity=None):
    del_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    if opacity is not None:
        try:
            mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            mat.set_editor_property("two_sided", True)
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
    if opacity is not None:
        o = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 360)
        o.set_editor_property("r", float(opacity))
        mel.connect_material_property(o, "", unreal.MaterialProperty.MP_OPACITY)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("mat %s rgb=%s" % (name, rgb))
    return mat

def make_water(name, rgb=(0.02, 0.10, 0.42)):
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
    r.set_editor_property("r", 0.28)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 280)
    m.set_editor_property("r", 0.05)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("water %s" % name)
    return mat

def make_sky_grad(name):
    """Unlit skydome: peach horizon -> soft blue/lavender zenith via PixelNormalWS.Z."""
    del_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try:
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        mat.set_editor_property("two_sided", True)
    except Exception: pass
    nrm = mel.create_material_expression(mat, unreal.MaterialExpressionPixelNormalWS, -700, 0)
    mask = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -520, 0)
    try:
        mask.set_editor_property("r", False); mask.set_editor_property("g", False)
        mask.set_editor_property("b", True); mask.set_editor_property("a", False)
    except Exception: pass
    mel.connect_material_expressions(nrm, "", mask, "")
    # Remap normal.Z (-1..1 or 0..1 on dome) — saturate + power for soft band
    sat = mel.create_material_expression(mat, unreal.MaterialExpressionSaturate, -360, 0)
    mel.connect_material_expressions(mask, "", sat, "")
    pow_n = mel.create_material_expression(mat, unreal.MaterialExpressionPower, -220, 0)
    exp = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -360, 80)
    exp.set_editor_property("r", 0.85)
    mel.connect_material_expressions(sat, "", pow_n, "Base")
    mel.connect_material_expressions(exp, "", pow_n, "Exp")
    bot = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -360, 160)
    # warm peach/amber horizon
    bot.set_editor_property("constant", unreal.LinearColor(1.05, 0.78, 0.52, 1.0))
    top = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -360, -140)
    # soft dusty blue-lavender zenith (mild — avoid washing sand)
    top.set_editor_property("constant", unreal.LinearColor(0.48, 0.52, 0.72, 1.0))
    lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -60, 0)
    mel.connect_material_expressions(bot, "", lerp, "A")
    mel.connect_material_expressions(top, "", lerp, "B")
    mel.connect_material_expressions(pow_n, "", lerp, "Alpha")
    # Slight emissive boost so gradient reads against fog
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, 80, 0)
    boost = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, 80, 80)
    boost.set_editor_property("r", 1.15)
    mel.connect_material_expressions(lerp, "", mul, "A")
    mel.connect_material_expressions(boost, "", mul, "B")
    mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("sky_grad %s" % name)
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

# ========== DUMP BEFORE ==========
dump_before = []
KEYS = ("SandBase", "Ground", "WetSand", "Foam", "BeachSlope", "Shallows", "Ocean",
        "SandRamp", "ShoreEdge")
for a in actors():
    lab = label(a)
    if not any(k in lab for k in KEYS):
        continue
    y0, y1, z, half = plane_y_range(a)
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    line = "%s loc=(%.0f,%.0f,%.1f) sc=(%.2f,%.2f,%.2f) Y=[%.0f..%.0f] halfY=%.0f Z=%.1f" % (
        lab, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z, y0, y1, half, z)
    dump_before.append(line); log("BEFORE " + line)

# ========== MATERIALS ==========
sand = make_sand_grain("MI_Tideborn_SandWarm", (1.38, 0.96, 0.60), tile=9.0)
make_sand_grain("M_Tideborn_Sand", (1.38, 0.96, 0.60), tile=9.0)
wet_dark = make_lit("MI_Tideborn_SandWet", (0.09, 0.06, 0.04), rough=0.35)
wet_mid = make_lit("MI_Tideborn_SandWetMid", (0.16, 0.10, 0.06), rough=0.42)
water = make_water("M_Tideborn_WaterOpaque", (0.02, 0.10, 0.42))
rock = make_lit("M_Tideborn_RockShore", (0.20, 0.15, 0.11), rough=0.94)
make_lit("MI_Tideborn_RockDark", (0.20, 0.15, 0.11), rough=0.94)
foam = make_lit("MI_Tideborn_Foam", (0.95, 0.93, 0.85), rough=0.65,
                emissive=(0.18, 0.16, 0.12))
foam_soft = make_lit("MI_Tideborn_FoamSoft", (0.93, 0.90, 0.80), rough=0.7,
                     emissive=(0.12, 0.11, 0.08), opacity=0.75)
sky_mat = make_sky_grad("M_Tideborn_SkyDomeGrad")

# ========== DESTROY old helpers that cause stripe / knife foam ==========
destroy_names = (
    "TidebornEnv_BeachSlope", "TidebornEnv_FoamStrip",
    "TidebornEnv_WetSand_01", "TidebornEnv_ShoreEdge",
)
# Also any Foam_* segments from prior runs
for a in list(actors()):
    lab = label(a)
    if lab in destroy_names or lab.startswith("TidebornEnv_FoamSeg_") or lab.startswith("TidebornEnv_WetJag_"):
        try:
            eas.destroy_actor(a); log("x " + lab)
        except Exception as e:
            log("destroy_fail %s %s" % (lab, e))

# Hide / shrink any sand-colored plane whose Y overlaps open ocean (Y < 400) at Z >= 99
OCEAN_Y_MAX = 400.0  # open water roughly Y < 400 in Overview
for a in list(actors()):
    lab = label(a)
    if lab in ("TidebornEnv_Ocean", "TidebornEnv_Shallows"):
        continue
    if not any(k in lab for k in ("Sand", "Ground", "Slope", "Ramp", "Beach", "Wet")):
        continue
    y0, y1, z, half = plane_y_range(a)
    # If sand cover extends into Y < 400 and Z >= water, shrink or move
    if y0 < OCEAN_Y_MAX and z >= 98.5:
        loc = a.get_actor_location(); sc = a.get_actor_scale3d()
        # Push inland: set min Y to >= 520 by moving center and/or shrinking scY
        target_min = 530.0
        if y1 <= target_min:
            hide(a); log("HIDE ocean-overlap %s Y=[%.0f..%.0f]" % (lab, y0, y1))
            continue
        # New center so min Y = target_min, keep max Y
        new_half = 0.5 * (y1 - target_min)
        new_y = target_min + new_half
        # Engine plane: half = 50 * scY
        new_scy = max(0.05, new_half / 50.0)
        # For custom meshes (BeachSlope etc already destroyed), scale proportionally
        if "SandBase" in lab:
            # LOCK — only ensure edge at Y=600 (scY=18 → half=900 → min=600). Do NOT shrink.
            log("KEEP SandBase edge OK minY=%.0f" % y0)
            continue
        if "Ground" in lab:
            # Ground is inland at Y=2800 — if somehow overlapping, skip
            if y0 >= 1500:
                log("KEEP Ground inland")
                continue
        try:
            a.set_actor_location(unreal.Vector(loc.x, new_y, loc.z), False, True)
            a.set_actor_scale3d(unreal.Vector(sc.x, new_scy, sc.z))
            log("SHRINK %s -> Y=%.0f scY=%.2f (was Y=[%.0f..%.0f])" % (lab, new_y, new_scy, y0, y1))
        except Exception as e:
            log("shrink_fail %s %s" % (lab, e))

# ========== LOCK water + SandBase ==========
plane = load("/Engine/BasicShapes/Plane")
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
        log("Ocean Z=99 Y=-800 scY=18 -> Y[-1700..100]")
    elif lab == "TidebornEnv_Shallows":
        # Keep shallows from covering past wet band; Z < sand
        a.set_actor_location(unreal.Vector(1000.0, 300.0, 100.0), False, True)
        a.set_actor_scale3d(unreal.Vector(70.0, 10.0, 1.0))
        force_apply(a, water); unhide(a)
        log("Shallows Z=100 Y=300 scY=10 -> Y[-200..800]")
    elif lab == "TidebornEnv_Ground":
        # Ensure inland only
        a.set_actor_location(unreal.Vector(1000.0, 2800.0, 105.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 16.0, 1.0))
        unhide(a); log("Ground inland Y=2800")
    elif lab == "TidebornEnv_WetSand_00":
        a.set_actor_location(unreal.Vector(1000.0, 630.0, 105.2), False, True)
        a.set_actor_scale3d(unreal.Vector(42.0, 1.9, 1.0))
        force_apply(a, wet_dark); unhide(a)
        log("WetSand_00 dark Y=630")
    elif "SandRamp" in lab:
        # Tiny — keep but ensure not over ocean
        loc = a.get_actor_location()
        if loc.y < 500:
            a.set_actor_location(unreal.Vector(loc.x, 640.0, 105.3), False, True)
        force_apply(a, wet_mid)
        log("SandRamp keep")
    elif "Boulder" in lab or lab.startswith("TidebornEnv_WLB_"):
        force_apply(a, rock)

# ========== BeachSlope: import + place shore-only ==========
slope_mesh = None
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
    try:
        box = slope_mesh.get_bounding_box()
        ext = box.max - box.min
        bx, by, bz = abs(float(ext.x)), abs(float(ext.y)), abs(float(ext.z))
        log("slope_bounds local=(%.1f,%.1f,%.1f) minZ=%.1f maxZ=%.1f" % (
            bx, by, bz, float(box.min.z), float(box.max.z)))
    except Exception as e:
        bx, by, bz = 5000.0, 1200.0, 240.0
        log("bounds_fail " + str(e))
    # Place: water edge at Y~560, land toward +Y. Center = 560 + half_y
    # Use scale 1 if mesh already ~50x12m
    sx = 5000.0 / bx if bx > 1 else 1.0
    sy = 1200.0 / by if by > 1 else 1.0
    sz = 1.0
    if sx > 20 or sy > 20:
        log("slope_scale_clamp sx=%.3f sy=%.3f" % (sx, sy))
        sx, sy = min(sx, 2.0), min(sy, 2.0)
    half_y = 0.5 * by * sy
    # CRITICAL: min world Y = center_y - half_y >= 530
    center_y = 530.0 + half_y
    # Land surface at Z~108; if mesh maxZ~0 and minZ~-240, place Z=108
    # If UE recentered (minZ=0, maxZ=240), place Z = 108 - maxZ = -132  ... detect:
    try:
        zmin = float(box.min.z); zmax = float(box.max.z)
    except Exception:
        zmin, zmax = -240.0, 0.0
    if zmin >= -1.0 and zmax > 10.0:
        # recentered: land at +zmax, water at 0 → place so water at Z=100
        place_z = 100.0 - zmin  # =100
        # but then land at 100+zmax — too high. Better: place_z so land ~108
        place_z = 108.0 - zmax
        log("slope_recentered place_z=%.1f (land~108, water~%.1f)" % (place_z, place_z + zmin))
    else:
        # origin at land Z=0: place_z = 108 → land 108, water 108+zmin
        place_z = 108.0
        log("slope_land_origin place_z=108 water_z=%.1f" % (place_z + zmin * sz))
    a = eas.spawn_actor_from_object(
        slope_mesh, unreal.Vector(1000.0, center_y, place_z),
        unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
    if a:
        a.set_actor_label("TidebornEnv_BeachSlope")
        a.set_actor_scale3d(unreal.Vector(sx, sy, sz))
        force_apply(a, sand); unhide(a)
        # Validate Y coverage
        y0, y1, z, half = plane_y_range(a)
        if y0 < 500.0:
            # Emergency shrink/move
            new_half = 0.5 * (y1 - 530.0) if y1 > 530 else 50.0
            new_y = 530.0 + new_half
            # scale Y down
            cur = a.get_actor_scale3d()
            ratio = max(0.05, new_half / max(1.0, half))
            a.set_actor_location(unreal.Vector(1000.0, new_y, place_z), False, True)
            a.set_actor_scale3d(unreal.Vector(cur.x, cur.y * ratio, cur.z))
            y0, y1, z, half = plane_y_range(a)
            log("slope_EMERGENCY_SHRINK Y=[%.0f..%.0f]" % (y0, y1))
        log("PLACE BeachSlope centerY=%.0f Z=%.1f sc=(%.2f,%.2f,%.2f) Y=[%.0f..%.0f]" % (
            center_y, place_z, sx, sy, sz, y0, y1))

# Optional ShoreEdge irregular wet mesh
edge_mesh = load(MESH + "/SM_TidebornShoreEdge")
if not edge_mesh and FBX_EDGE.exists():
    paths = import_fbx(FBX_EDGE, MESH)
    for p in paths:
        a = load(p)
        if isinstance(a, unreal.StaticMesh):
            edge_mesh = a; break
if edge_mesh:
    try:
        box = edge_mesh.get_bounding_box()
        ext = box.max - box.min
        ebx, eby = abs(float(ext.x)), abs(float(ext.y))
    except Exception:
        ebx, eby = 5000.0, 1200.0
    esx = min(2.0, 4500.0 / ebx if ebx > 1 else 1.0)
    esy = min(2.0, 400.0 / eby if eby > 1 else 0.3)  # thin Y band
    half_e = 0.5 * eby * esy
    cy = 560.0 + half_e
    if cy - half_e < 520:
        cy = 520.0 + half_e
    ae = eas.spawn_actor_from_object(
        edge_mesh, unreal.Vector(1000.0, cy, 104.5),
        unreal.Rotator(0, 0, 0))
    if ae:
        ae.set_actor_label("TidebornEnv_ShoreEdge")
        ae.set_actor_scale3d(unreal.Vector(esx, esy, 1.2))
        force_apply(ae, wet_dark); unhide(ae)
        log("PLACE ShoreEdge Y=%.0f scY=%.2f" % (cy, esy))

# ========== WetSand bands (2) + staggered foam segments ==========
if plane:
    # Wet mid inland
    a1 = eas.spawn_actor_from_object(
        plane, unreal.Vector(1000.0, 700.0, 105.6),
        unreal.Rotator(0, 0, 0))
    if a1:
        a1.set_actor_label("TidebornEnv_WetSand_01")
        a1.set_actor_scale3d(unreal.Vector(40.0, 1.7, 1.0))
        force_apply(a1, wet_mid); unhide(a1)
        log("SPAWN WetSand_01 mid Y=700")
    # Jagged wet extras — short offset planes
    for i, (x, y, scx, scy) in enumerate((
        (780.0, 645.0, 12.0, 1.4),
        (1220.0, 655.0, 11.0, 1.5),
        (950.0, 615.0, 10.0, 1.2),
    )):
        aj = eas.spawn_actor_from_object(
            plane, unreal.Vector(x, y, 105.15), unreal.Rotator(0, (i - 1) * 3.0, 0))
        if aj:
            aj.set_actor_label("TidebornEnv_WetJag_%02d" % i)
            aj.set_actor_scale3d(unreal.Vector(scx, scy, 1.0))
            force_apply(aj, wet_dark if i != 1 else wet_mid); unhide(aj)
    # Foam: 5 staggered short cream segments (not one infinite knife line)
    foam_specs = [
        (720.0, 548.0, 9.0, 1.0),
        (880.0, 560.0, 10.0, 1.15),
        (1050.0, 542.0, 11.0, 0.95),
        (1200.0, 555.0, 9.5, 1.1),
        (1360.0, 545.0, 8.5, 0.9),
    ]
    for i, (x, y, scx, scy) in enumerate(foam_specs):
        af = eas.spawn_actor_from_object(
            plane, unreal.Vector(x, y, 103.6 + 0.15 * (i % 3)),
            unreal.Rotator(0, (i - 2) * 2.5, 0))
        if af:
            af.set_actor_label("TidebornEnv_FoamSeg_%02d" % i)
            af.set_actor_scale3d(unreal.Vector(scx, scy, 1.0))
            force_apply(af, foam if i % 2 == 0 else foam_soft); unhide(af)
    log("SPAWN FoamSeg x5 scY~0.9-1.15")

# Ensure WetSand_00 exists
has_w0 = any(label(a) == "TidebornEnv_WetSand_00" for a in actors())
if not has_w0 and plane:
    a = eas.spawn_actor_from_object(
        plane, unreal.Vector(1000.0, 630.0, 105.2), unreal.Rotator(0, 0, 0))
    if a:
        a.set_actor_label("TidebornEnv_WetSand_00")
        a.set_actor_scale3d(unreal.Vector(42.0, 1.9, 1.0))
        force_apply(a, wet_dark); unhide(a)
        log("SPAWN WetSand_00")

# ========== SKY / LIGHTING ==========
for a in actors():
    cn = cname(a); lab = label(a)
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        unhide(a); log("SHOW " + cn)
    if lab == "TidebornEnv_SkyDome" or "SkyDome" in lab:
        unhide(a)
        if sky_mat: force_apply(a, sky_mat)
        # Ensure large enough
        try:
            sc = a.get_actor_scale3d()
            if max(abs(sc.x), abs(sc.y), abs(sc.z)) < 50:
                a.set_actor_scale3d(unreal.Vector(400.0, 400.0, 400.0))
        except Exception: pass
        log("SkyDome gradient mat")
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("real_time_capture", True)
            except Exception: pass
            try: c.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
            except Exception: pass
            try: c.set_editor_property("cubemap", None)
            except Exception: pass
            try: c.set_editor_property("intensity", 0.30)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.86, 0.68, 1.0))
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_is_black", False)
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_color", unreal.LinearColor(0.55, 0.38, 0.22, 1.0))
            except Exception: pass
            try: c.recapture_sky()
            except Exception: pass
        log("SkyLight 0.30 warm")
    if "DirectionalLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 3.2)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.80, 0.55, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 0.65)
            except Exception: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except Exception: pass
            try: c.set_editor_property("use_temperature", False)
            except Exception: pass
        # Side-ish light so BeachSlope lip reads
        a.set_actor_rotation(unreal.Rotator(pitch=-28.0, yaw=-55.0, roll=0.0), False)
        log("DirLight warm 3.2 pitch=-28 yaw=-55")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.040)
            except Exception: pass
            try: c.set_editor_property("fog_height_falloff", 0.22)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.82, 0.70, 0.58, 1.0))
            except Exception: pass
            try: c.set_editor_property("directional_inscattering_color", unreal.LinearColor(1.0, 0.78, 0.52, 1.0))
            except Exception: pass
            try: c.set_editor_property("directional_inscattering_exponent", 6.0)
            except Exception: pass
            try: c.set_editor_property("volumetric_fog", True)
            except Exception: pass
        log("Fog dens=0.040 warm peach-grey")
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
                s.set_editor_property("white_temp", 3700.0)
            except Exception: pass
            try:
                s.set_editor_property("override_white_tint", True)
                s.set_editor_property("white_tint", 0.0)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", -0.15)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_method", True)
                s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            except Exception: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.32, 0.97, 0.58, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_scene_color_tint", True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.14, 0.94, 0.76, 1.0))
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP white_temp=3700 warm")
        except Exception as e:
            log("PP " + str(e))

for cmd in ("r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
            "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "ShowFlag.Cloud 1",
            "r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

# Recapture skylight after sky changes
for a in actors():
    if "SkyLight" in cname(a):
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.recapture_sky()
            except Exception: pass

# ========== DUMP AFTER ==========
dump_after = []
for a in actors():
    lab = label(a)
    if not any(k in lab for k in KEYS + ("FoamSeg", "WetJag")):
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

# Flag any sand still over open water
bad = []
for line in dump_after:
    if any(k in line for k in ("Ocean", "Shallows")):
        continue
    if not any(k in line for k in ("Sand", "Slope", "Ramp", "Ground", "Wet", "Beach", "Foam")):
        continue
    # parse Y=[a..b]
    try:
        ys = line.split("Y=[")[1].split("]")[0]
        y0 = float(ys.split("..")[0]); y1 = float(ys.split("..")[1])
        zs = float(line.split("Z=")[1].split(" ")[0])
        if y0 < 400 and zs >= 98.5:
            bad.append(line)
    except Exception:
        pass
if bad:
    for b in bad:
        log("WARN_SAND_IN_WATER " + b)
else:
    log("OK no sand plane with Ymin<400 at Z>=98.5")

DUMP.write_text("BEFORE\n" + "\n".join(dump_before) + "\n\nAFTER\n" + "\n".join(dump_after) + "\n", encoding="utf-8")

try: log("save %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
