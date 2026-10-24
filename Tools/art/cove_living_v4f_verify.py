# -*- coding: utf-8 -*-
"""v4f: saturated UNLIT warm sand + kill blue PP/atmosphere + waterline. Hardcoded VERIFY."""
from __future__ import annotations
import pathlib, time, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v4f_verify_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
SHOT_DIR = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
SHOT_NAME = "TidebornCoveVerify"
SHOT_LOC = (1050.0, 1550.0, 200.0)
SHOT_ROT = (-5.0, -90.0, 0.0)

lines = []
def log(m):
    t = str(m); unreal.log("[V4f] " + t); lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except Exception: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except Exception: return ""

def make_unlit(name, rgb):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    except Exception: pass
    try: mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    except Exception: pass
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("UNLIT %s (%.2f,%.2f,%.2f)" % (name, rgb[0], rgb[1], rgb[2]))
    return mat

def make_lit(name, rgb, rough=0.88):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    except Exception: pass
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 100)
    r.set_editor_property("r", float(rough))
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    em = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 200)
    em.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("LIT %s" % name)
    return mat

def force_apply(a, mat):
    if not a or not mat: return 0
    n = 0
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        try: comp.modify()
        except Exception: pass
        for i in range(16):
            try: comp.set_material(i, mat); n += 1
            except Exception: break
        try: comp.set_editor_property("override_materials", [mat] * 8)
        except Exception: pass
    return n

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load " + str(e))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Saturated warm beach — unlit so lighting cannot cool it
sand = make_unlit("MI_Tideborn_SandWarm", (0.95, 0.78, 0.48))
make_unlit("M_Tideborn_Sand", (0.95, 0.78, 0.48))
wood = make_lit("MI_Tideborn_WoodMuted", (0.40, 0.26, 0.14))
creature = make_lit("MI_Tideborn_CreatureMuted", (0.48, 0.38, 0.24))  # brown, no teal
gate = make_lit("M_Tideborn_GateSolid", (0.36, 0.24, 0.14))
rock = make_lit("M_Tideborn_RockShore", (0.50, 0.46, 0.40))
water = make_lit("M_Tideborn_WaterOpaque", (0.12, 0.28, 0.38), rough=0.2)  # readable
ground = make_lit("M_Tideborn_Ground", (0.32, 0.38, 0.20))
bark = make_lit("M_Tideborn_Bark", (0.32, 0.18, 0.09))

for a in list(actors()):
    if label(a).startswith("TidebornEnv_WLB_"):
        try: eas.destroy_actor(a)
        except Exception: pass

for a in actors():
    lab = label(a); cn = cname(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_SandRamp") or "SandRamp" in lab:
        force_apply(a, sand); log("sand -> " + lab)
    elif lab == "TidebornEnv_Ground":
        force_apply(a, ground)
    elif lab in ("TidebornEnv_Ocean", "TidebornEnv_Shallows"):
        force_apply(a, water)
    elif "Gate" in lab:
        force_apply(a, gate)
        for c in a.get_components_by_class(unreal.LightComponent):
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.78, 0.5, 1.0))
            except Exception: pass
            try: c.set_editor_property("intensity", 180.0)
            except Exception: pass
            try: c.set_editor_property("cast_shadows", False)
            except Exception: pass
    elif "Kelp" in lab or "Burr" in lab or "Hound" in lab:
        force_apply(a, creature); log("creature -> " + lab)
    elif "Gather" in lab:
        force_apply(a, rock if "Stone" in lab else wood)
    elif "Boulder" in lab or "Waterline" in lab:
        force_apply(a, rock)
    elif "Trunk" in lab:
        force_apply(a, bark)

    if "DirectionalLight" in cn:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 2.5)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.94, 0.78, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 1.2)
            except Exception: pass
            try: c.set_editor_property("shadow_amount", 0.25)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-55, yaw=20, roll=0), False)
        log("DirLight high warm soft shadow")
    if "SkyLight" in cn:
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity", 0.9)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.97, 0.90, 1.0))
            except Exception: pass
            try: c.set_editor_property("real_time_capture", True)
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_is_black", False)
            except Exception: pass
        log("SkyLight low warm")
    if "ExponentialHeightFog" in cn:
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.06)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.80, 0.74, 0.62, 1.0))
            except Exception: pass
            try: c.set_editor_property("fog_max_opacity", 0.35)
            except Exception: pass
            try: c.set_editor_property("volumetric_fog", False)
            except Exception: pass
        log("Fog light warm")
    if "SkyAtmosphere" in cn:
        # Hide atmosphere actor — major blue wash source
        try:
            a.set_actor_hidden_in_game(True)
            a.set_is_temporarily_hidden_in_editor(True)
            log("SkyAtmosphere HIDDEN")
        except Exception as e:
            log("atm hide " + str(e))
            try:
                for c in a.get_components_by_class(unreal.SkyAtmosphereComponent):
                    try: c.set_editor_property("rayleigh_scattering_scale", 0.02)
                    except Exception: pass
                    try: c.set_editor_property("rayleigh_scattering", unreal.LinearColor(0.05, 0.08, 0.12, 1.0))
                    except Exception: pass
            except Exception: pass
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        try:
            try: a.set_editor_property("unbound", True)
            except Exception: pass
            s = a.get_editor_property("settings")
            # Warm white balance; disable cool grading
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 4200.0)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", 0.5)
            except Exception: pass
            try:
                s.set_editor_property("override_bloom_intensity", True)
                s.set_editor_property("bloom_intensity", 0.02)
            except Exception: pass
            # zero out color grade shadows/midtones/highlights cool cast if possible
            for prop in ("color_gamma", "color_gain", "color_saturation"):
                try:
                    s.set_editor_property("override_" + prop, False)
                except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP white_temp 4200 bias 0.5")
        except Exception as e:
            log("PP " + str(e))

for a in actors():
    if label(a) == "TidebornEnv_SandRamp" or "SandRamp" in label(a):
        a.set_actor_location(unreal.Vector(1000.0, 560.0, 105.0), False, True)
        a.set_actor_scale3d(unreal.Vector(2.4, 1.6, 1.4))
        force_apply(a, sand)
        log("SandRamp big")
    if label(a) == "TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000.0, 420.0, 100.0), False, True)
        sc = a.get_actor_scale3d()
        a.set_actor_scale3d(unreal.Vector(max(sc.x, 55.0), 6.5, sc.z))
        force_apply(a, water)

boulder_mesh = None
for a in actors():
    if label(a).startswith("TidebornEnv_Boulder") and "WLB" not in label(a):
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            try: boulder_mesh = comp.get_editor_property("static_mesh")
            except Exception: pass
        if boulder_mesh: break
if boulder_mesh:
    for i, (x, y, z, s, yaw) in enumerate([
        (880, 605, 101, 2.2, -30), (855, 650, 100, 1.9, 40),
        (1125, 608, 101, 2.3, 20), (1150, 660, 100, 2.0, -55),
        (900, 685, 100, 1.7, 10), (1100, 635, 100, 1.8, -20),
    ]):
        a = eas.spawn_actor_from_object(boulder_mesh, unreal.Vector(float(x), float(y), float(z)), unreal.Rotator(0, float(yaw), 0))
        if a:
            a.set_actor_label("TidebornEnv_WLB_%02d" % i)
            a.set_actor_scale3d(unreal.Vector(s, s, s * 0.85))
            force_apply(a, rock)
            log("WLB %02d" % i)

for a in actors():
    lab = label(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_SandRamp", "TidebornEnv_Shallows", "TidebornEnv_Ocean",
               "Tideborn_P2_BurrHound", "Tideborn_P2_ShoreGate"):
        loc = a.get_actor_location(); sc = a.get_actor_scale3d()
        mats = []
        for comp in a.get_components_by_class(unreal.PrimitiveComponent):
            for i in range(3):
                try:
                    m = comp.get_material(i)
                    if m: mats.append(m.get_name())
                except Exception: break
        log("CONFIRM %s Z=%.0f loc=(%.0f,%.0f) sc=(%.1f,%.1f) mats=%s" % (
            lab, loc.z, loc.x, loc.y, sc.x, sc.y, ",".join(mats[:4]) or "-"))

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass

log("wait shaders 22s")
time.sleep(22)

SHOT_DIR.mkdir(parents=True, exist_ok=True)
target = SHOT_DIR / (SHOT_NAME + ".png")
if target.exists():
    try: target.unlink()
    except Exception: pass
for cmd in ("ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0","ShowFlag.Bounds 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
unreal.EditorLevelLibrary.set_level_viewport_camera_info(
    unreal.Vector(*SHOT_LOC), unreal.Rotator(pitch=SHOT_ROT[0], yaw=SHOT_ROT[1], roll=SHOT_ROT[2]))
log("SHOT begin " + SHOT_NAME)
unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, SHOT_NAME)
ok = False
for i in range(100):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size > 20000:
        ok = True; break
time.sleep(3)
if target.exists() and target.stat().st_size > 20000: ok = True
log("SHOT end ok=%s size=%s" % (ok, target.stat().st_size if target.exists() else 0))
(ROOT / "Tools" / "art" / "_shot_done.txt").write_text(
    "name=%s ok=%s size=%s\n" % (SHOT_NAME, ok, target.stat().st_size if target.exists() else 0), encoding="utf-8")
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
