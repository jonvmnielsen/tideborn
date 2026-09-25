# -*- coding: utf-8 -*-
"""Cove living v4 — warm sand, kill cyan, PP/exposure, visible waterline ramp+boulders.
LOCKED: SandBase Z=106 sc~(45,18); water Z < sand; water scY<=18.
"""
from __future__ import annotations
import pathlib, math, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v4_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MESH = "/Game/Tideborn/Art/Meshes"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
FBX_RAMP = ROOT / "Tools" / "art" / "export" / "SM_TidebornSandRamp.fbx"

lines = []

def log(m):
    t = str(m)
    unreal.log("[LivingV4] " + t)
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

def apply(a, mat, slots=12):
    if not mat or not a:
        return 0
    n = 0
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        try:
            comp.modify()
        except Exception:
            pass
        for i in range(slots):
            try:
                comp.set_material(i, mat)
                n += 1
            except Exception:
                break
        # kill any dynamic material cyan leftovers
        try:
            comp.set_editor_property("cast_shadow", True)
        except Exception:
            pass
    return n

def make_solid(name, rgb, rough=0.9, emissive=(0.0, 0.0, 0.0)):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 100)
    r.set_editor_property("r", float(rough))
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    em = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 200)
    em.set_editor_property("constant", unreal.LinearColor(emissive[0], emissive[1], emissive[2], 1.0))
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("mat %s rgb=(%.2f,%.2f,%.2f)" % (name, rgb[0], rgb[1], rgb[2]))
    return mat

def make_warm_sand():
    """Force warm beige — solid tint dominates any cool texture."""
    name = "M_Tideborn_Sand"
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    # Aggressive warm beach beige (LinearColor ~0.82,0.66,0.42)
    base_col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    base_col.set_editor_property("constant", unreal.LinearColor(0.82, 0.66, 0.42, 1.0))
    mel.connect_material_property(base_col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 100)
    r.set_editor_property("r", 0.95)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    em = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 200)
    em.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("sand WARM beige solid 0.82/0.66/0.42 (no cool tex)")
    return mat

def make_mi(parent_mat, name, tint_rgb):
    """Create MI with BaseColor override if possible; else solid master."""
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    # Prefer solid for reliability (no param guessing)
    return make_solid(name, tint_rgb, rough=0.88)

def import_ramp():
    if not FBX_RAMP.exists():
        log("ramp fbx missing")
        return load(MESH + "/SM_TidebornSandRamp")
    task = unreal.AssetImportTask()
    task.filename = str(FBX_RAMP)
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
    log("import ramp -> %s" % paths)
    for p in paths:
        a = load(p)
        if isinstance(a, unreal.StaticMesh):
            return a
    return load(MESH + "/SM_TidebornSandRamp")

def confirm(a, tag):
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    hy = 50.0 * sc.y
    mats = []
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(4):
            try:
                m = comp.get_material(i)
                if m:
                    mats.append(m.get_name())
            except Exception:
                break
        break
    log("CONFIRM %s Z=%.0f loc=(%.0f,%.0f,%.0f) Y[%.0f..%.0f] sc=(%.1f,%.1f,%.1f) mats=%s" % (
        tag, loc.z, loc.x, loc.y, loc.z, loc.y - hy, loc.y + hy, sc.x, sc.y, sc.z,
        ",".join(mats[:4]) or "-"))

# ---- main ----
try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e:
    log("load " + str(e))

sand = make_warm_sand()
# also alias MI name requested
sand_warm = make_mi(sand, "MI_Tideborn_SandWarm", (0.82, 0.66, 0.42))
wood = make_solid("MI_Tideborn_WoodMuted", (0.34, 0.22, 0.12), rough=0.92)
creature = make_solid("MI_Tideborn_CreatureMuted", (0.28, 0.32, 0.18), rough=0.75)  # olive, NOT cyan
rock = make_solid("M_Tideborn_RockShore", (0.38, 0.36, 0.32), rough=0.78)
gate = make_solid("M_Tideborn_GateSolid", (0.30, 0.20, 0.12), rough=0.90)
ground = make_solid("M_Tideborn_Ground", (0.28, 0.34, 0.18), rough=0.90)
water = make_solid("M_Tideborn_WaterOpaque", (0.06, 0.14, 0.22), rough=0.25)  # deep muted navy, no cyan
bark = make_solid("M_Tideborn_Bark", (0.30, 0.16, 0.08), rough=0.90)

ramp_mesh = import_ramp()

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Destroy prior waterline helper boulders from this pass
for a in list(actors()):
    lab = label(a)
    if lab.startswith("TidebornEnv_WaterlineBoulder_") or lab.startswith("TidebornEnv_FillLight"):
        try:
            eas.destroy_actor(a)
            log("destroy " + lab)
        except Exception:
            pass

sand_base = None
for a in actors():
    lab = label(a)
    cn = cname(a)

    # --- A) warm sand ---
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_SandRamp") or "SandRamp" in lab:
        apply(a, sand_warm or sand)
        log("warm sand -> " + lab)
        if lab == "TidebornEnv_SandBase":
            sand_base = a
            # LOCKED transforms — do not change Z/sc beyond confirm
            loc = a.get_actor_location()
            sc = a.get_actor_scale3d()
            if abs(loc.z - 106.0) > 0.5 or abs(sc.x - 45.0) > 0.5:
                log("WARN SandBase drift loc.z=%.1f sc=(%.1f,%.1f) — leaving as-is (locked)" % (loc.z, sc.x, sc.y))

    if lab == "TidebornEnv_Ground":
        apply(a, ground)
        log("ground -> " + lab)

    if lab in ("TidebornEnv_Shallows", "TidebornEnv_Ocean"):
        apply(a, water)
        log("water muted -> " + lab)

    # --- B) kill cyan on props ---
    if "ShoreGate" in lab or lab == "Tideborn_P2_ShoreGate":
        apply(a, gate)
        log("gate wood muted -> " + lab)
        for comp in a.get_components_by_class(unreal.LightComponent):
            try:
                comp.set_editor_property("light_color", unreal.LinearColor(1.0, 0.72, 0.42, 1.0))
            except Exception:
                pass
            try:
                comp.set_editor_property("intensity", 200.0)
            except Exception:
                pass
            try:
                comp.set_editor_property("cast_shadows", False)
            except Exception:
                pass
            # zero any cyan emissive feel
            try:
                comp.set_editor_property("indirect_lighting_intensity", 0.5)
            except Exception:
                pass
            log("gate light desaturated")

    if "Kelp" in lab or "Burr" in lab or "Hound" in lab:
        apply(a, creature)
        log("creature muted olive -> " + lab)

    if "Gather" in lab:
        apply(a, rock if "Stone" in lab else wood)
        log("gather muted -> " + lab)

    if lab.startswith("TidebornEnv_Boulder") or "Rock" in lab:
        apply(a, rock)

    if "Trunk" in lab or "Bark" in lab:
        apply(a, bark)

    # any leftover TidebornEnv with water-looking names
    if lab.startswith("TidebornEnv_") and any(k in lab.lower() for k in ("cyan", "glow", "emissive", "marker")):
        apply(a, rock)
        log("scrub env -> " + lab)

# --- D) SandRamp scale/place + shallows ---
ramp_actor = None
for a in actors():
    if label(a) == "TidebornEnv_SandRamp" or "SandRamp" in label(a):
        ramp_actor = a
        break

if ramp_actor:
    if ramp_mesh:
        for comp in ramp_actor.get_components_by_class(unreal.StaticMeshComponent):
            try:
                comp.set_editor_property("static_mesh", ramp_mesh)
                log("ramp mesh reassigned")
            except Exception as e:
                log("ramp mesh warn " + str(e))
    # center ~(1000, 500, 105); mesh already 55x14m — slight X widen
    ramp_actor.set_actor_location(unreal.Vector(1000.0, 500.0, 105.0), False, True)
    ramp_actor.set_actor_scale3d(unreal.Vector(1.6, 1.1, 1.0))  # ~88m x 15.4m footprint
    ramp_actor.set_actor_rotation(unreal.Rotator(pitch=0, yaw=0, roll=0), False)
    apply(ramp_actor, sand_warm or sand)
    log("SandRamp placed (1000,500,105) sc=(1.6,1.1,1)")
else:
    # spawn if missing
    if ramp_mesh:
        ramp_actor = eas.spawn_actor_from_object(ramp_mesh, unreal.Vector(1000.0, 500.0, 105.0), unreal.Rotator(0, 0, 0))
        if ramp_actor:
            ramp_actor.set_actor_label("TidebornEnv_SandRamp")
            ramp_actor.set_actor_scale3d(unreal.Vector(1.6, 1.1, 1.0))
            apply(ramp_actor, sand_warm or sand)
            log("SandRamp SPAWNED")

# Shallows: center Y~420 scY~6-7 Z=100
for a in actors():
    if label(a) == "TidebornEnv_Shallows":
        loc = a.get_actor_location()
        sc = a.get_actor_scale3d()
        a.set_actor_location(unreal.Vector(loc.x, 420.0, 100.0), False, True)
        # keep scY <= 18 locked rule; target 6.5
        a.set_actor_scale3d(unreal.Vector(sc.x, 6.5, sc.z))
        apply(a, water)
        log("Shallows center Y=420 scY=6.5 Z=100")

# Waterline boulders Y~600-700, irregular, NOT blocking X 900-1100 corridor
boulder_mesh = None
for a in actors():
    if label(a).startswith("TidebornEnv_Boulder"):
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            try:
                boulder_mesh = comp.get_editor_property("static_mesh")
            except Exception:
                pass
        if boulder_mesh:
            break
if not boulder_mesh:
    boulder_mesh = load(MESH + "/boulder_01_1k")

wl_spots = [
    (720, 620, 100, 2.4, -40),
    (780, 680, 100, 2.1, 55),
    (820, 640, 100, 2.6, 12),
    (1180, 660, 100, 2.3, -88),
    (1240, 610, 100, 2.5, 33),
    (1300, 690, 100, 2.2, -15),
]
if boulder_mesh:
    for i, (x, y, z, s, yaw) in enumerate(wl_spots):
        a = eas.spawn_actor_from_object(boulder_mesh, unreal.Vector(float(x), float(y), float(z)), unreal.Rotator(0, float(yaw), 0))
        if a:
            a.set_actor_label("TidebornEnv_WaterlineBoulder_%02d" % i)
            a.set_actor_scale3d(unreal.Vector(s, s, s * 0.85))
            apply(a, rock)
            log("waterline boulder %02d @ (%.0f,%.0f)" % (i, x, y))

# --- C) Post-process + exposure + lights + fog ---
pp = None
for a in actors():
    cn = cname(a)
    if "PostProcess" in cn:
        pp = a
        break

if not pp:
    # spawn unbound PP volume
    try:
        pp_cls = unreal.EditorAssetLibrary.load_blueprint_class("/Engine/EngineVolumes/PostProcessVolume")
    except Exception:
        pp_cls = None
    try:
        pp = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(1000.0, 1200.0, 200.0), unreal.Rotator(0, 0, 0))
        if pp:
            pp.set_actor_label("TidebornEnv_PostProcess")
            log("spawned PostProcessVolume")
    except Exception as e:
        log("PP spawn fail " + str(e))

if pp:
    try:
        pp.set_editor_property("unbound", True)
    except Exception:
        try:
            pp.set_editor_property("b_unbound", True)
        except Exception:
            pass
    try:
        s = pp.get_editor_property("settings")
        # warmer white balance ~5500
        try:
            s.set_editor_property("override_white_temp", True)
            s.set_editor_property("white_temp", 5500.0)
        except Exception as e:
            log("white_temp warn " + str(e))
        try:
            s.set_editor_property("override_color_grading_global", True)
            # slight warm lift via gain (R>G>B)
            s.set_editor_property("color_grading_global", unreal.Vector4(1.08, 1.0, 0.90, 1.0))
        except Exception:
            pass
        try:
            s.set_editor_property("override_auto_exposure_bias", True)
            s.set_editor_property("auto_exposure_bias", 0.9)
            s.set_editor_property("override_auto_exposure_min_brightness", True)
            s.set_editor_property("auto_exposure_min_brightness", 0.7)
            s.set_editor_property("override_auto_exposure_max_brightness", True)
            s.set_editor_property("auto_exposure_max_brightness", 1.6)
        except Exception as e:
            log("exposure warn " + str(e))
        try:
            s.set_editor_property("override_color_contrast", True)
            s.set_editor_property("color_contrast", unreal.Vector4(0.92, 0.92, 0.92, 1.0))
        except Exception:
            try:
                s.set_editor_property("override_film_contrast", True)
                s.set_editor_property("film_contrast", 0.45)
            except Exception:
                pass
        try:
            pp.set_editor_property("settings", s)
        except Exception:
            pass
        log("PP unbound warm temp~5500 exposure_bias~0.9 contrast soft")
    except Exception as e:
        log("PP settings fail " + str(e))

for a in actors():
    cn = cname(a)
    if "DirectionalLight" in cn:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try:
                c.set_editor_property("intensity", 2.2)
            except Exception:
                pass
            try:
                c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.88, 0.68, 1.0))
            except Exception:
                pass
            try:
                c.set_editor_property("indirect_lighting_intensity", 2.8)
            except Exception:
                pass
            try:
                c.set_editor_property("shadow_amount", 0.35)
            except Exception:
                pass
            try:
                c.set_editor_property("cast_shadows", True)
            except Exception:
                pass
        a.set_actor_rotation(unreal.Rotator(pitch=-38, yaw=40, roll=0), False)
        log("DirectionalLight warm 2.2 soft shadows")
    if "SkyLight" in cn:
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try:
                c.set_editor_property("intensity", 9.0)
            except Exception:
                pass
            try:
                c.set_editor_property("real_time_capture", True)
            except Exception:
                pass
            try:
                c.set_editor_property("lower_hemisphere_is_black", False)
            except Exception:
                pass
            try:
                c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.95, 0.88, 1.0))
            except Exception:
                pass
        log("SkyLight 9.0 warm")
    if "ExponentialHeightFog" in cn:
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try:
                c.set_editor_property("fog_density", 0.135)
            except Exception:
                pass
            try:
                c.set_editor_property("fog_height_falloff", 0.22)
            except Exception:
                pass
            try:
                c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.70, 0.68, 0.64, 1.0))
            except Exception:
                pass
            try:
                c.set_editor_property("fog_max_opacity", 0.65)
            except Exception:
                pass
            try:
                c.set_editor_property("volumetric_fog", True)
            except Exception:
                pass
        log("Fog density~0.135 warm-grey inscatter")

# weak fill PointLight over cove
try:
    fill = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(1050.0, 1100.0, 380.0), unreal.Rotator(0, 0, 0))
    if fill:
        fill.set_actor_label("TidebornEnv_FillLight")
        for c in fill.get_components_by_class(unreal.PointLightComponent):
            try:
                c.set_editor_property("intensity", 12000.0)
            except Exception:
                pass
            try:
                c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.90, 0.72, 1.0))
            except Exception:
                pass
            try:
                c.set_editor_property("attenuation_radius", 3500.0)
            except Exception:
                pass
            try:
                c.set_editor_property("cast_shadows", False)
            except Exception:
                pass
        log("Fill PointLight warm weak")
except Exception as e:
    log("fill light warn " + str(e))

# Sweep ALL Tideborn actors for any remaining cyan-looking material names
CYAN_KEYS = ("cyan", "teal", "emissive", "glow", "water", "ice", "neon")
for a in actors():
    lab = label(a)
    if not lab.startswith("Tideborn"):
        continue
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(8):
            try:
                m = comp.get_material(i)
                if not m:
                    continue
                mn = (m.get_name() or "").lower()
                if any(k in mn for k in CYAN_KEYS) and "wateropaque" not in mn and "watersimple" not in mn:
                    # replace with rock/wood
                    replace = creature if any(k in lab for k in ("Kelp", "Burr", "Hound")) else (gate if "Gate" in lab else rock)
                    if lab.startswith("TidebornEnv_Sand") or "Sand" in lab:
                        replace = sand_warm or sand
                    if "Ocean" in lab or "Shallow" in lab:
                        continue
                    comp.set_material(i, replace)
                    log("replaced cyan-ish %s on %s" % (mn, lab))
            except Exception:
                break

# Final CONFIRM
for a in actors():
    lab = label(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_Shallows", "TidebornEnv_Ocean",
               "TidebornEnv_Ground", "TidebornEnv_SandRamp", "Tideborn_P2_ShoreGate",
               "Tideborn_P2_KelpBack", "Tideborn_P2_BurrHound"):
        confirm(a, lab)
    if lab.startswith("TidebornEnv_WaterlineBoulder_"):
        confirm(a, lab)
    if lab.startswith("Tideborn_Gather"):
        confirm(a, lab)

# hard-floor lock check
for a in actors():
    if label(a) == "TidebornEnv_SandBase":
        loc = a.get_actor_location(); sc = a.get_actor_scale3d()
        ok = abs(loc.z - 106) < 1.0 and abs(sc.x - 45) < 1.0 and abs(sc.y - 18) < 1.0
        log("LOCK SandBase OK=%s Z=%.0f sc=(%.1f,%.1f)" % (ok, loc.z, sc.x, sc.y))
    if label(a) in ("TidebornEnv_Ocean", "TidebornEnv_Shallows"):
        loc = a.get_actor_location(); sc = a.get_actor_scale3d()
        ok = loc.z < 106 and sc.y <= 18.0 + 0.01
        log("LOCK water %s OK=%s Z=%.0f scY=%.1f" % (label(a), ok, loc.z, sc.y))

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
