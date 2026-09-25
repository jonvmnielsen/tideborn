# -*- coding: utf-8 -*-
"""Sky restore B: HDRI SkyLight (no broken realtime), brighter warm sun, exposure up. NO shot."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_sky_restore_b_result.txt"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
HDRI = "/Game/Tideborn/Art/HDRI/PH_industrial_sunset_puresky"

lines = []
def log(m):
    t = str(m); unreal.log("[SkyRestoreB] " + t); lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())

def cname(a):
    try: return a.get_class().get_name() or ""
    except: return ""

def label(a):
    try: return a.get_actor_label() or ""
    except: return ""

def unhide(a):
    try:
        a.set_actor_hidden_in_game(False)
        a.set_is_temporarily_hidden_in_editor(False)
        root = a.root_component
        if root:
            try: root.set_visibility(True, True)
            except Exception: pass
    except Exception as e:
        log("unhide " + str(e))

try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e:
    log("load " + str(e))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
hdri = None
if unreal.EditorAssetLibrary.does_asset_exist(HDRI):
    hdri = unreal.EditorAssetLibrary.load_asset(HDRI)
    log("HDRI loaded %s type=%s" % (HDRI, type(hdri).__name__ if hdri else "?"))
else:
    log("HDRI MISSING " + HDRI)

has_sl = False
has_atmo = False
has_fog = False
has_dir = False

for a in actors():
    cn = cname(a)
    lab = label(a)
    if "SkyAtmosphere" in cn:
        has_atmo = True
        unhide(a)
        log("SkyAtmosphere ok")
    if "VolumetricCloud" in cn:
        unhide(a)
    if "SkyLight" in cn:
        has_sl = True
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            except Exception: pass
            # Disable realtime — captures black under UE Cmd
            try: c.set_editor_property("real_time_capture", False)
            except Exception: pass
            try:
                # SourceType: SLS_SpecifiedCubemap = 1 in many builds
                c.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
            except Exception as e:
                log("source_type warn " + str(e))
                try: c.set_editor_property("source_type", 1)
                except Exception: pass
            if hdri:
                try:
                    c.set_editor_property("cubemap", hdri)
                    log("SkyLight cubemap <- HDRI sunset")
                except Exception as e:
                    log("cubemap set fail " + str(e))
            try: c.set_editor_property("intensity", 5.0)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.95, 0.85, 1.0))
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_is_black", False)
            except Exception: pass
            try: c.recapture_sky()
            except Exception: pass
        log("SkyLight HDRI intensity~5 warm")
    if "DirectionalLight" in cn:
        has_dir = True
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 2.5)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.92, 0.75, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 1.5)
            except Exception: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except Exception: pass
            try: c.set_editor_property("cast_shadows", True)
            except Exception: pass
            try: c.set_editor_property("dynamic_shadow_distance_movable_light", 20000.0)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-42.0, yaw=30.0, roll=0.0), False)
        log("DirectionalLight 2.5 warm atmosphere_sun pitch=-42")
    if "ExponentialHeightFog" in cn:
        has_fog = True
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.045)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.78, 0.72, 0.62, 1.0))
            except Exception: pass
            try: c.set_editor_property("fog_max_opacity", 0.5)
            except Exception: pass
            try: c.set_editor_property("start_distance", 500.0)
            except Exception: pass
        log("Fog mild warm-grey dens~0.045")
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        unhide(a)
        try:
            try: a.set_editor_property("unbound", True)
            except Exception: pass
            s = a.get_editor_property("settings")
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 5200.0)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_method", True)
                s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            except Exception as e:
                log("ae method warn " + str(e))
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", 1.2)
            except Exception: pass
            try:
                # Manual exposure brightness
                s.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
                s.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
            except Exception: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.18, 1.05, 0.88, 1.0))
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP manual-ish exposure bias 1.2 warm temp5200")
        except Exception as e:
            log("PP " + str(e))

if not has_sl:
    try:
        sl = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(1000, 1000, 500))
        if sl:
            sl.set_actor_label("TidebornEnv_SkyLight")
            for c in sl.get_components_by_class(unreal.SkyLightComponent):
                try: c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
                except Exception: pass
                try: c.set_editor_property("real_time_capture", False)
                except Exception: pass
                try: c.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
                except Exception: pass
                if hdri:
                    try: c.set_editor_property("cubemap", hdri)
                    except Exception: pass
                try: c.set_editor_property("intensity", 5.0)
                except Exception: pass
                try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.95, 0.85, 1.0))
                except Exception: pass
            has_sl = True
            log("SPAWNED SkyLight with HDRI")
    except Exception as e:
        log("spawn sl " + str(e))

# Soft sky dome fallback (large inverted sphere) for black-sky cmdlet shots
dome_mat_path = "/Game/Tideborn/Art/Materials/M_Tideborn_SkyDome"
if unreal.EditorAssetLibrary.does_asset_exist(dome_mat_path):
    unreal.EditorAssetLibrary.delete_asset(dome_mat_path)
dome_mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    "M_Tideborn_SkyDome", "/Game/Tideborn/Art/Materials", unreal.Material, unreal.MaterialFactoryNew())
mel = unreal.MaterialEditingLibrary
try: dome_mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
except Exception: pass
try: dome_mat.set_editor_property("two_sided", True)
except Exception: pass
col = mel.create_material_expression(dome_mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
# Soft dusk blue-ish sky (not black, not cyan)
col.set_editor_property("constant", unreal.LinearColor(0.35, 0.55, 0.85, 1.0))
mel.connect_material_property(col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
# also base
col2 = mel.create_material_expression(dome_mat, unreal.MaterialExpressionConstant3Vector, -300, 100)
col2.set_editor_property("constant", unreal.LinearColor(0.35, 0.55, 0.85, 1.0))
mel.connect_material_property(col2, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.recompile_material(dome_mat)
unreal.EditorAssetLibrary.save_asset(dome_mat_path, True)
log("sky dome mat soft dusk blue")

# Remove old dome
for a in list(actors()):
    if label(a) == "TidebornEnv_SkyDome":
        try: eas.destroy_actor(a)
        except Exception: pass

sphere = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere")
if sphere:
    dome = eas.spawn_actor_from_object(sphere, unreal.Vector(1000.0, 800.0, 0.0), unreal.Rotator(0, 0, 0))
    if dome:
        dome.set_actor_label("TidebornEnv_SkyDome")
        dome.set_actor_scale3d(unreal.Vector(400.0, 400.0, 400.0))
        for comp in dome.get_components_by_class(unreal.PrimitiveComponent):
            for i in range(4):
                try: comp.set_material(i, dome_mat)
                except Exception: break
            try: comp.set_editor_property("cast_shadow", False)
            except Exception: pass
            try: comp.set_editor_property("affect_distance_field_lighting", False)
            except Exception: pass
        log("SPAWNED SkyDome scale 400 soft dusk")
    else:
        log("FAILED spawn dome")
else:
    log("no Engine sphere")

for cmd in (
    "r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
    "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "ShowFlag.Cloud 1",
    "r.DefaultFeature.AutoExposure 0",
):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

# Confirm
log("=== CONFIRM ===")
log("SkyAtmosphere=%s SkyLight=%s Fog=%s Dir=%s HDRI=%s" % (has_atmo, has_sl, has_fog, has_dir, bool(hdri)))
for a in actors():
    cn = cname(a); lab = label(a)
    if "Sky" in cn or "Fog" in cn or "Directional" in cn or lab == "TidebornEnv_SkyDome" or lab == "TidebornEnv_SkyLight":
        loc = a.get_actor_location()
        log("ACT %s label=%s loc=(%.0f,%.0f,%.0f)" % (cn, lab, loc.x, loc.y, loc.z))
for a in actors():
    lab = label(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_SandRamp", "TidebornEnv_Ocean", "TidebornEnv_Shallows"):
        loc = a.get_actor_location(); sc = a.get_actor_scale3d()
        log("CONFIRM %s Z=%.0f loc=(%.0f,%.0f) sc=(%.2f,%.2f)" % (lab, loc.z, loc.x, loc.y, sc.x, sc.y))

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
