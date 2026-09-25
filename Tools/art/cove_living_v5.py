# -*- coding: utf-8 -*-
"""v5 living shore: dark rocks, wet sand band, jagged shore edge, water band, mild sky. NO shot."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v5_result.txt"
DUMP = ROOT / "Tools" / "art" / "cove_dump.txt"
MAT = "/Game/Tideborn/Art/Materials"
MESH = "/Game/Tideborn/Art/Meshes"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
HDRI = "/Game/Tideborn/Art/HDRI/PH_industrial_sunset_puresky"
FBX = ROOT / "Tools" / "art" / "export" / "SM_TidebornShoreEdge.fbx"

lines = []
def log(m):
    t = str(m); unreal.log("[V5] " + t); lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except Exception: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except Exception: return ""
def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if unreal.EditorAssetLibrary.does_asset_exist(p) else None

def make_lit(name, rgb, rough=0.88, emissive=None):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    try: mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    except Exception: pass
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 100)
    r.set_editor_property("r", float(rough))
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 200)
    if emissive:
        e.set_editor_property("constant", unreal.LinearColor(emissive[0], emissive[1], emissive[2], 1.0))
    else:
        e.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path, True)
    log("mat %s rgb=(%.2f,%.2f,%.2f) rough=%.2f" % (name, rgb[0], rgb[1], rgb[2], rough))
    return mat

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

def import_shore_fbx():
    if not FBX.exists():
        log("MISSING shore fbx: %s" % FBX)
        return None
    task = unreal.AssetImportTask()
    task.filename = str(FBX)
    task.destination_path = MESH
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
    log("import shore -> %s" % paths)
    mesh = None
    for p in paths:
        a = load(p)
        if isinstance(a, unreal.StaticMesh):
            mesh = a
            break
    if not mesh:
        mesh = load(MESH + "/SM_TidebornShoreEdge")
    return mesh

try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e:
    log("load " + str(e))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# --- A) Materials: dark rock, wet sand, keep warm sand ---
# Dark shore rock albedo ~0.18-0.22 grey-brown (was 0.55 -> white under SkyLight)
rock = make_lit("M_Tideborn_RockShore", (0.18, 0.16, 0.14), rough=0.92)
rock_dark = make_lit("MI_Tideborn_RockDark", (0.20, 0.17, 0.14), rough=0.93)
# Wet sand: darker wet beige, slightly cooler not cyan
sand_wet = make_lit("MI_Tideborn_SandWet", (0.35, 0.30, 0.22), rough=0.72)
# Warm dry sand (keep readable warm; mild emissive so not blue-washed)
sand_warm = make_lit("MI_Tideborn_SandWarm", (0.82, 0.66, 0.42), rough=0.95,
                     emissive=(0.12, 0.08, 0.03))
make_lit("M_Tideborn_Sand", (0.82, 0.66, 0.42), rough=0.95, emissive=(0.12, 0.08, 0.03))
water = make_lit("M_Tideborn_WaterOpaque", (0.14, 0.30, 0.40), rough=0.18)
ground = make_lit("M_Tideborn_Ground", (0.34, 0.40, 0.22), rough=0.9)
bark = make_lit("M_Tideborn_Bark", (0.32, 0.18, 0.09), rough=0.9)
wood = make_lit("MI_Tideborn_WoodMuted", (0.40, 0.26, 0.14), rough=0.88)
creature = make_lit("MI_Tideborn_CreatureMuted", (0.48, 0.38, 0.24), rough=0.85)
gate = make_lit("M_Tideborn_GateSolid", (0.36, 0.24, 0.14), rough=0.85)

# Destroy prior wet strips / shore edge / WLB clutter we will rebuild
for a in list(actors()):
    lab = label(a)
    if lab.startswith("TidebornEnv_WetSand_") or lab.startswith("TidebornEnv_ShoreEdge") or lab.startswith("TidebornEnv_WLB_"):
        try:
            eas.destroy_actor(a)
            log("x " + lab)
        except Exception:
            pass

# Apply dark rock + warm sand + water
for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_SandBase":
        force_apply(a, sand_warm)
        # LOCK: SandBase Z=106 sc~(45,18)
        a.set_actor_location(unreal.Vector(1000.0, 1500.0, 106.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 18.0, 1.0))
        log("LOCK SandBase Z=106 sc=(45,18) SandWarm")
    elif lab == "TidebornEnv_SandRamp" or "SandRamp" in lab:
        # Shrink ramp so wet band reads; place near water edge
        a.set_actor_location(unreal.Vector(1000.0, 560.0, 105.0), False, True)
        a.set_actor_scale3d(unreal.Vector(0.85, 0.55, 0.7))
        force_apply(a, sand_wet)
        log("SandRamp shrunk + SandWet")
    elif lab == "TidebornEnv_Ground":
        force_apply(a, ground)
    elif lab == "TidebornEnv_Ocean":
        # Ocean center Y~-600 scY~18, Z below sand
        a.set_actor_location(unreal.Vector(1000.0, -600.0, 99.0), False, True)
        a.set_actor_scale3d(unreal.Vector(70.0, 18.0, 1.0))
        force_apply(a, water)
        log("Ocean Y=-600 scY=18 Z=99")
    elif lab == "TidebornEnv_Shallows":
        # Shallows Y~500 scY~8-10 so Overview sees wider water band
        a.set_actor_location(unreal.Vector(1000.0, 500.0, 100.0), False, True)
        a.set_actor_scale3d(unreal.Vector(60.0, 9.0, 1.0))
        force_apply(a, water)
        log("Shallows Y=500 scY=9 Z=100")
    elif "Boulder" in lab or "Waterline" in lab:
        force_apply(a, rock)
    elif "Trunk" in lab:
        force_apply(a, bark)
    elif "Gate" in lab:
        force_apply(a, gate)
    elif "Kelp" in lab or "Burr" in lab or "Hound" in lab:
        force_apply(a, creature)
    elif "Gather" in lab:
        force_apply(a, rock if "Stone" in lab else wood)

# Spawn WLB rocks along waterline with DARK rock
boulder_mesh = None
for a in actors():
    if label(a).startswith("TidebornEnv_Boulder") and "WLB" not in label(a) and "Wet" not in label(a):
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            try:
                boulder_mesh = comp.get_editor_property("static_mesh")
            except Exception:
                pass
        if boulder_mesh:
            break
if boulder_mesh:
    for i, (x, y, z, s, yaw) in enumerate([
        (880, 605, 101, 2.0, -30), (855, 650, 100, 1.7, 40),
        (1125, 608, 101, 2.1, 20), (1150, 660, 100, 1.8, -55),
        (920, 690, 100, 1.5, 10), (1080, 640, 100, 1.6, -20),
        (1000, 620, 100.5, 1.4, 55),
    ]):
        a = eas.spawn_actor_from_object(
            boulder_mesh,
            unreal.Vector(float(x), float(y), float(z)),
            unreal.Rotator(pitch=0.0, yaw=float(yaw), roll=0.0),
        )
        if a:
            a.set_actor_label("TidebornEnv_WLB_%02d" % i)
            a.set_actor_scale3d(unreal.Vector(s, s, s * 0.85))
            force_apply(a, rock)
    log("spawned WLB dark rocks")

# --- B) Wet sand strips + jagged shore edge ---
plane = load("/Engine/BasicShapes/Plane")
if plane:
    for i, (x, y, z, sx, sy) in enumerate([
        (1000.0, 640.0, 105.5, 45.0, 2.2),
        (1000.0, 600.0, 105.4, 48.0, 1.8),
        (1000.0, 670.0, 105.6, 42.0, 1.6),
    ]):
        a = eas.spawn_actor_from_object(
            plane,
            unreal.Vector(x, y, z),
            unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0),
        )
        if a:
            a.set_actor_label("TidebornEnv_WetSand_%02d" % i)
            a.set_actor_scale3d(unreal.Vector(sx, sy, 1.0))
            force_apply(a, sand_wet)
            log("WetSand_%02d Y=%.0f sc=(%.1f,%.1f)" % (i, y, sx, sy))
else:
    log("NO Engine Plane for wet sand")

shore_mesh = import_shore_fbx()
if shore_mesh:
    a = eas.spawn_actor_from_object(
        shore_mesh,
        unreal.Vector(1000.0, 560.0, 104.5),
        unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0),
    )
    if a:
        a.set_actor_label("TidebornEnv_ShoreEdge")
        # mesh already ~50x12m in cm; scale ~1
        a.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
        force_apply(a, sand_wet)
        # Sanity: if bounds insane, delete
        try:
            origin, extent = a.get_actor_bounds(False)
            if extent.x > 8000 or extent.y > 4000 or extent.z > 800:
                eas.destroy_actor(a)
                log("ShoreEdge DELETED bad bounds extent=(%.0f,%.0f,%.0f)" % (extent.x, extent.y, extent.z))
            else:
                log("ShoreEdge ok bounds extent=(%.0f,%.0f,%.0f)" % (extent.x, extent.y, extent.z))
        except Exception as e:
            log("ShoreEdge bounds warn " + str(e))
else:
    log("NO shore mesh imported")

# --- C) Mild sky polish: keep SkyAtmosphere/SkyLight, HDRI, fog dens~0.05 ---
hdri = load(HDRI)
has_sl = has_atmo = has_fog = has_dir = False
for a in actors():
    cn = cname(a); lab = label(a)
    if "SkyAtmosphere" in cn:
        has_atmo = True
        unhide(a)
        log("SkyAtmosphere keep")
    if "VolumetricCloud" in cn:
        unhide(a)
    if "SkyLight" in cn:
        has_sl = True
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            except Exception: pass
            try: c.set_editor_property("real_time_capture", False)
            except Exception: pass
            try: c.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
            except Exception:
                try: c.set_editor_property("source_type", 1)
                except Exception: pass
            if hdri:
                try:
                    c.set_editor_property("cubemap", hdri)
                    log("SkyLight HDRI sunset")
                except Exception as e:
                    log("cubemap " + str(e))
            # Lower intensity so dark rocks stay dark (was 5 -> white rocks)
            try: c.set_editor_property("intensity", 2.2)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.92, 0.78, 1.0))
            except Exception: pass
            # Rotate cubemap so warm sun from ocean (-Y) side
            try: c.set_editor_property("source_cubemap_angle", 200.0)
            except Exception as e:
                log("cubemap_angle warn " + str(e))
            try: c.set_editor_property("lower_hemisphere_is_black", False)
            except Exception: pass
            try: c.recapture_sky()
            except Exception: pass
        log("SkyLight intensity~2.2 warm angle~200")
    if "DirectionalLight" in cn:
        has_dir = True
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 2.8)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.90, 0.72, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 1.0)
            except Exception: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except Exception: pass
        # Warm sun from ocean side (looking toward -Y water from beach)
        a.set_actor_rotation(unreal.Rotator(pitch=-38.0, yaw=-90.0, roll=0.0), False)
        log("DirLight warm from ocean yaw=-90")
    if "ExponentialHeightFog" in cn:
        has_fog = True
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.05)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.80, 0.72, 0.60, 1.0))
            except Exception: pass
            try: c.set_editor_property("fog_max_opacity", 0.55)
            except Exception: pass
            try: c.set_editor_property("start_distance", 400.0)
            except Exception: pass
        log("Fog dens~0.05 warm-grey")
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        unhide(a)
        try:
            try: a.set_editor_property("unbound", True)
            except Exception: pass
            s = a.get_editor_property("settings")
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 4800.0)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", 0.9)
            except Exception: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.15, 1.05, 0.90, 1.0))
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP warm temp4800 gain mild")
        except Exception as e:
            log("PP " + str(e))
    # Soften sky dome so not flat cyan-ish; keep dusk
    if lab == "TidebornEnv_SkyDome":
        unhide(a)

# Soft sky dome material refresh (warm dusk, not black)
dome_mat_path = MAT + "/M_Tideborn_SkyDome"
if unreal.EditorAssetLibrary.does_asset_exist(dome_mat_path):
    unreal.EditorAssetLibrary.delete_asset(dome_mat_path)
dome_mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    "M_Tideborn_SkyDome", MAT, unreal.Material, unreal.MaterialFactoryNew())
mel = unreal.MaterialEditingLibrary
try: dome_mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
except Exception: pass
try: dome_mat.set_editor_property("two_sided", True)
except Exception: pass
col = mel.create_material_expression(dome_mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
col.set_editor_property("constant", unreal.LinearColor(0.55, 0.42, 0.38, 1.0))  # warm dusk
mel.connect_material_property(col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
col2 = mel.create_material_expression(dome_mat, unreal.MaterialExpressionConstant3Vector, -300, 100)
col2.set_editor_property("constant", unreal.LinearColor(0.45, 0.50, 0.70, 1.0))
mel.connect_material_property(col2, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.recompile_material(dome_mat)
unreal.EditorAssetLibrary.save_asset(dome_mat_path, True)
for a in actors():
    if label(a) == "TidebornEnv_SkyDome":
        force_apply(a, dome_mat)
        log("SkyDome warm dusk")

for cmd in (
    "r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
    "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "ShowFlag.Cloud 1",
):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

# --- Dump ---
dump_lines = []
for a in actors():
    lab = label(a)
    if not lab.startswith("Tideborn") and lab not in ("PlayerStart", "DirectionalLight", "SkyAtmosphere", "ExponentialHeightFog"):
        cn = cname(a)
        if "SkyLight" not in cn and "PostProcess" not in cn:
            continue
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    mats = []
    try:
        for comp in a.get_components_by_class(unreal.PrimitiveComponent):
            smn = "-"
            try:
                sm = comp.get_editor_property("static_mesh")
                if sm: smn = sm.get_name()
            except Exception: pass
            for i in range(4):
                try:
                    m = comp.get_material(i)
                    if m: mats.append("%s[%d]=%s" % (smn, i, m.get_name()))
                except Exception: break
    except Exception:
        pass
    try:
        origin, extent = a.get_actor_bounds(False)
        yr = "[%.0f..%.0f]" % (origin.y - extent.y, origin.y + extent.y)
        xr = "[%.0f..%.0f]" % (origin.x - extent.x, origin.x + extent.x)
    except Exception:
        yr = xr = "?"
    line = "%s | %s | loc=(%.0f,%.0f,%.0f) sc=(%.2f,%.2f,%.2f) | Y%s X%s | %s" % (
        lab, cname(a), loc.x, loc.y, loc.z, sc.x, sc.y, sc.z, yr, xr, ";".join(mats[:4]) or "-")
    dump_lines.append(line)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_SandRamp", "TidebornEnv_Ocean",
               "TidebornEnv_Shallows", "TidebornEnv_ShoreEdge") or lab.startswith("TidebornEnv_WetSand_"):
        log("CONFIRM " + line)

DUMP.write_text("\n".join(dump_lines) + "\nDONE\n", encoding="utf-8")
log("dump lines=%d" % len(dump_lines))
log("sky atmo=%s sl=%s fog=%s dir=%s hdri=%s" % (has_atmo, has_sl, has_fog, has_dir, bool(hdri)))

try:
    log("save_level -> %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e:
    log("save " + str(e))
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("save_dirty ok")
except Exception as e:
    log("dirty " + str(e))
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
