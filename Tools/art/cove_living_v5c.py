# -*- coding: utf-8 -*-
"""v5c: fix wet-under-sand, shoreedge covering water, dark rocks, kill washout. NO shot."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v5c_result.txt"
DUMP = ROOT / "Tools" / "art" / "cove_dump.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
HDRI = "/Game/Tideborn/Art/HDRI/PH_industrial_sunset_puresky"

lines = []
def log(m):
    t = str(m); unreal.log("[V5c] " + t); lines.append(t)
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

def make_lit(name, rgb, rough=0.9):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    # Base color
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    col.set_editor_property("constant", unreal.LinearColor(float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    # Roughness
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 120)
    r.set_editor_property("r", float(rough))
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    # Explicit zero metallic
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)
    m.set_editor_property("r", 0.0)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    # Explicit zero specular-ish (specular)
    try:
        s = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 280)
        s.set_editor_property("r", 0.15)
        mel.connect_material_property(s, "", unreal.MaterialProperty.MP_SPECULAR)
    except Exception:
        pass
    # Zero emissive
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 360)
    e.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path, True)
    log("mat %s rgb=(%.3f,%.3f,%.3f)" % (name, rgb[0], rgb[1], rgb[2]))
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

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load " + str(e))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# DARK rocks — much darker than before so SkyLight cannot bleach them
rock = make_lit("M_Tideborn_RockShore", (0.10, 0.09, 0.08), rough=0.95)
make_lit("MI_Tideborn_RockDark", (0.12, 0.10, 0.09), rough=0.95)
# Warm sand NO emissive (emissive was washing out)
sand_warm = make_lit("MI_Tideborn_SandWarm", (0.72, 0.58, 0.38), rough=0.96)
make_lit("M_Tideborn_Sand", (0.72, 0.58, 0.38), rough=0.96)
# Wet sand darker; readable band
sand_wet = make_lit("MI_Tideborn_SandWet", (0.28, 0.24, 0.18), rough=0.55)
water = make_lit("M_Tideborn_WaterOpaque", (0.10, 0.28, 0.40), rough=0.12)
ground = make_lit("M_Tideborn_Ground", (0.30, 0.36, 0.20), rough=0.9)
bark = make_lit("M_Tideborn_Bark", (0.28, 0.16, 0.08), rough=0.9)
gate = make_lit("M_Tideborn_GateSolid", (0.32, 0.22, 0.12), rough=0.85)
creature = make_lit("MI_Tideborn_CreatureMuted", (0.42, 0.34, 0.22), rough=0.85)
wood = make_lit("MI_Tideborn_WoodMuted", (0.36, 0.24, 0.12), rough=0.88)

# Remove broken ShoreEdge (was covering water) and old wet strips
for a in list(actors()):
    lab = label(a)
    if lab.startswith("TidebornEnv_WetSand_") or lab == "TidebornEnv_ShoreEdge":
        try:
            eas.destroy_actor(a); log("x " + lab)
        except Exception:
            pass

plane = load("/Engine/BasicShapes/Plane")

# LOCK SandBase; re-apply warm sand
for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000.0, 1500.0, 106.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 18.0, 1.0))
        force_apply(a, sand_warm)
        log("LOCK SandBase Z=106 sc=(45,18)")
    elif lab == "TidebornEnv_SandRamp" or "SandRamp" in lab:
        a.set_actor_location(unreal.Vector(1000.0, 580.0, 105.0), False, True)
        a.set_actor_scale3d(unreal.Vector(0.22, 0.14, 0.6))
        force_apply(a, sand_wet)
    elif lab == "TidebornEnv_Ocean":
        # Push water band toward Overview (+Y) still Z < sand, scY<=18
        a.set_actor_location(unreal.Vector(1000.0, -400.0, 99.0), False, True)
        a.set_actor_scale3d(unreal.Vector(70.0, 18.0, 1.0))
        force_apply(a, water)
        log("Ocean Y=-400")
    elif lab == "TidebornEnv_Shallows":
        # Wider visible band toward sand edge (SandBase starts Y=600)
        a.set_actor_location(unreal.Vector(1000.0, 420.0, 100.0), False, True)
        a.set_actor_scale3d(unreal.Vector(60.0, 10.0, 1.0))  # Y[ -80 .. 920 ] wait: 420+/-500 = -80..920
        force_apply(a, water)
        log("Shallows Y=420 scY=10 -> water up to ~920")
    elif lab == "TidebornEnv_Ground":
        force_apply(a, ground)
    elif "Boulder" in lab or lab.startswith("TidebornEnv_WLB_"):
        force_apply(a, rock)
    elif "Trunk" in lab:
        force_apply(a, bark)
    elif "Gate" in lab:
        force_apply(a, gate)
    elif "Kelp" in lab or "Burr" in lab or "Hound" in lab:
        force_apply(a, creature)
    elif "Gather" in lab:
        force_apply(a, rock if "Stone" in lab else wood)

# Wet sand strips BETWEEN water and SandBase front (Y < 600), Z slightly above water, below/at sand
# SandBase covers Y>=600; place wet at Y=560..595 so Overview/VerifyWater see dark band
if plane:
    for i, (y, z, sx, sy) in enumerate([
        (560.0, 105.8, 50.0, 2.5),
        (580.0, 105.9, 48.0, 2.0),
        (595.0, 106.1, 46.0, 1.5),
    ]):
        a = eas.spawn_actor_from_object(
            plane, unreal.Vector(1000.0, y, z), unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
        if a:
            a.set_actor_label("TidebornEnv_WetSand_%02d" % i)
            a.set_actor_scale3d(unreal.Vector(sx, sy, 1.0))
            force_apply(a, sand_wet)
            log("WetSand_%02d Y=%.0f Z=%.1f (in front of SandBase)" % (i, y, z))

# Thin ShoreEdge strip ON the waterline only (do not cover ocean)
shore = load("/Game/Tideborn/Art/Meshes/SM_TidebornShoreEdge")
if shore:
    a = eas.spawn_actor_from_object(
        shore, unreal.Vector(1000.0, 555.0, 105.2), unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
    if a:
        a.set_actor_label("TidebornEnv_ShoreEdge")
        # mesh ~50x12m; squash Y so it is a thin coastal ribbon
        a.set_actor_scale3d(unreal.Vector(1.0, 0.18, 1.0))
        force_apply(a, sand_wet)
        try:
            o, e = a.get_actor_bounds(False)
            log("ShoreEdge thin extent=(%.0f,%.0f,%.0f) Y[%.0f..%.0f]" % (e.x, e.y, e.z, o.y - e.y, o.y + e.y))
            # If still covering too much water (ymin < 200), shrink more
            if (o.y - e.y) < 200:
                a.set_actor_scale3d(unreal.Vector(1.0, 0.10, 1.0))
                a.set_actor_location(unreal.Vector(1000.0, 570.0, 105.2), False, True)
                o, e = a.get_actor_bounds(False)
                log("ShoreEdge shrink2 Y[%.0f..%.0f]" % (o.y - e.y, o.y + e.y))
        except Exception as ex:
            log("shore bounds " + str(ex))

# Lighting: stop blowout; keep atmosphere/skylight
hdri = load(HDRI)
for a in actors():
    cn = cname(a); lab = label(a)
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        unhide(a)
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("real_time_capture", False)
            except Exception: pass
            try: c.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
            except Exception:
                try: c.set_editor_property("source_type", 1)
                except Exception: pass
            if hdri:
                try: c.set_editor_property("cubemap", hdri)
                except Exception: pass
            try: c.set_editor_property("intensity", 1.0)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.90, 0.75, 1.0))
            except Exception: pass
            try: c.set_editor_property("source_cubemap_angle", 200.0)
            except Exception: pass
            try: c.recapture_sky()
            except Exception: pass
        log("SkyLight intensity=1.0")
    if "DirectionalLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 1.8)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.88, 0.70, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 0.6)
            except Exception: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-35.0, yaw=-90.0, roll=0.0), False)
        log("DirLight 1.8 ocean-side")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.05)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.78, 0.68, 0.55, 1.0))
            except Exception: pass
        log("Fog dens=0.05")
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        unhide(a)
        try:
            try: a.set_editor_property("unbound", True)
            except Exception: pass
            s = a.get_editor_property("settings")
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 4500.0)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", 0.2)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_method", True)
                s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            except Exception: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.10, 1.00, 0.85, 1.0))
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP exposureBias=0.2 manual warm")
        except Exception as e:
            log("PP " + str(e))
    if lab == "TidebornEnv_SkyDome":
        unhide(a)
        # warmer dusk dome, dimmer so not wash
        dome_path = MAT + "/M_Tideborn_SkyDome"
        if unreal.EditorAssetLibrary.does_asset_exist(dome_path):
            unreal.EditorAssetLibrary.delete_asset(dome_path)
        dome = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_Tideborn_SkyDome", MAT, unreal.Material, unreal.MaterialFactoryNew())
        mel = unreal.MaterialEditingLibrary
        try: dome.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        except Exception: pass
        try: dome.set_editor_property("two_sided", True)
        except Exception: pass
        c = mel.create_material_expression(dome, unreal.MaterialExpressionConstant3Vector, -300, 0)
        c.set_editor_property("constant", unreal.LinearColor(0.40, 0.32, 0.35, 1.0))
        mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        mel.recompile_material(dome)
        unreal.EditorAssetLibrary.save_asset(dome_path, True)
        force_apply(a, dome)
        log("SkyDome dim warm dusk")

for cmd in ("r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
            "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

# Dump key actors
dump_lines = []
for a in actors():
    lab = label(a)
    keep = (lab.startswith("Tideborn") or lab in ("PlayerStart", "DirectionalLight", "SkyAtmosphere", "ExponentialHeightFog")
            or "SkyLight" in cname(a) or "PostProcess" in cname(a))
    if not keep: continue
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    mats = []
    try:
        for comp in a.get_components_by_class(unreal.PrimitiveComponent):
            smn = "-"
            try:
                sm = comp.get_editor_property("static_mesh")
                if sm: smn = sm.get_name()
            except Exception: pass
            for i in range(2):
                try:
                    m = comp.get_material(i)
                    if m: mats.append("%s[%d]=%s" % (smn, i, m.get_name()))
                except Exception: break
    except Exception: pass
    try:
        origin, extent = a.get_actor_bounds(False)
        yr = "[%.0f..%.0f]" % (origin.y - extent.y, origin.y + extent.y)
    except Exception:
        yr = "?"
    line = "%s | loc=(%.0f,%.0f,%.0f) sc=(%.2f,%.2f) Y%s | %s" % (
        lab, loc.x, loc.y, loc.z, sc.x, sc.y, yr, ";".join(mats[:3]) or "-")
    dump_lines.append(line)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_Ocean", "TidebornEnv_Shallows", "TidebornEnv_ShoreEdge") or lab.startswith("TidebornEnv_WetSand_"):
        log("CONFIRM " + line)
DUMP.write_text("\n".join(dump_lines) + "\nDONE\n", encoding="utf-8")

try: log("save -> %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log("save " + str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
