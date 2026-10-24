# -*- coding: utf-8 -*-
"""Apply living-shore fixes THEN take one shot (no reload between). Hardcoded SHOT_* below."""
from __future__ import annotations
import pathlib, time, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v4d_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
SHOT_DIR = ROOT / "Saved" / "Screenshots" / "WindowsEditor"

# --- edit per invocation via companion writer, or defaults ---
SHOT_NAME = "TidebornCoveVerify"
SHOT_LOC = (1050.0, 1550.0, 200.0)
SHOT_ROT = (-5.0, -90.0, 0.0)

# override from active file if readable
cfgp = ROOT / "Tools" / "art" / "_shot_cfg_v4d.txt"
if cfgp.exists():
    try:
        raw = cfgp.read_text(encoding="utf-8-sig").strip().split("|")
        SHOT_NAME = raw[0].strip()
        SHOT_LOC = tuple(float(x) for x in raw[1].split(","))
        SHOT_ROT = tuple(float(x) for x in raw[2].split(","))
    except Exception:
        pass

lines = []
def log(m):
    t = str(m); unreal.log("[V4d] " + t); lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())

def label(a):
    try: return a.get_actor_label() or ""
    except Exception: return ""

def cname(a):
    try: return a.get_class().get_name() or ""
    except Exception: return ""

def make_solid(name, rgb, rough=0.92, emissive=(0.0, 0.0, 0.0)):
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
    em.set_editor_property("constant", unreal.LinearColor(emissive[0], emissive[1], emissive[2], 1.0))
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 160)
    m.set_editor_property("r", 0.0)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("mat %s rgb=%.2f/%.2f/%.2f em=%.3f" % (name, rgb[0], rgb[1], rgb[2], emissive[0]))
    return mat

def force_apply(a, mat):
    if not a or not mat: return 0
    n = 0
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        try: comp.modify()
        except Exception: pass
        try: comp.set_editor_property("overlay_material", None)
        except Exception: pass
        for i in range(16):
            try:
                comp.set_material(i, mat); n += 1
            except Exception:
                break
        try: comp.set_editor_property("override_materials", [mat] * 8)
        except Exception: pass
    return n

try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e:
    log("load " + str(e))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Aggressive warm sand — slight warm emissive fights blue wash
sand = make_solid("MI_Tideborn_SandWarm", (0.92, 0.72, 0.45), rough=0.96, emissive=(0.04, 0.028, 0.012))
make_solid("M_Tideborn_Sand", (0.92, 0.72, 0.45), rough=0.96, emissive=(0.04, 0.028, 0.012))
wood = make_solid("MI_Tideborn_WoodMuted", (0.38, 0.25, 0.14), rough=0.92)
creature = make_solid("MI_Tideborn_CreatureMuted", (0.45, 0.36, 0.22), rough=0.82)
gate = make_solid("M_Tideborn_GateSolid", (0.34, 0.23, 0.13), rough=0.9)
rock = make_solid("M_Tideborn_RockShore", (0.42, 0.40, 0.36), rough=0.78)
water = make_solid("M_Tideborn_WaterOpaque", (0.05, 0.12, 0.18), rough=0.3)
ground = make_solid("M_Tideborn_Ground", (0.30, 0.36, 0.18), rough=0.9)
bark = make_solid("M_Tideborn_Bark", (0.32, 0.18, 0.09), rough=0.9)

# Clear prior corridor waterline helpers from this pass
for a in list(actors()):
    lab = label(a)
    if lab.startswith("TidebornEnv_WLB_") or lab == "TidebornEnv_FillLight":
        try: eas.destroy_actor(a)
        except Exception: pass

for a in actors():
    lab = label(a)
    cn = cname(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_SandRamp") or "SandRamp" in lab:
        force_apply(a, sand); log("sand -> " + lab)
    elif lab == "TidebornEnv_Ground":
        force_apply(a, ground)
    elif lab in ("TidebornEnv_Ocean", "TidebornEnv_Shallows"):
        force_apply(a, water)
    elif "ShoreGate" in lab or "Gate" in lab:
        force_apply(a, gate)
        for c in a.get_components_by_class(unreal.LightComponent):
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.72, 0.4, 1.0))
            except Exception: pass
            try: c.set_editor_property("intensity", 250.0)
            except Exception: pass
            try: c.set_editor_property("cast_shadows", False)
            except Exception: pass
    elif "Kelp" in lab or "Burr" in lab or "Hound" in lab:
        force_apply(a, creature); log("creature -> " + lab)
    elif "Gather" in lab:
        force_apply(a, rock if "Stone" in lab else wood)
    elif lab.startswith("TidebornEnv_Boulder") or lab.startswith("TidebornEnv_Waterline"):
        force_apply(a, rock)
    elif "Trunk" in lab:
        force_apply(a, bark)

    if "DirectionalLight" in cn:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 2.0)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.92, 0.70, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 1.8)
            except Exception: pass
            try: c.set_editor_property("shadow_amount", 0.40)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-45, yaw=30, roll=0), False)
        log("DirLight warm 2.0")
    if "SkyLight" in cn:
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity", 1.8)
            except Exception: pass
            try: c.set_editor_property("real_time_capture", True)
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_is_black", False)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.95, 0.85, 1.0))
            except Exception: pass
        log("SkyLight 1.8 warm")
    if "ExponentialHeightFog" in cn:
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.10)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.75, 0.70, 0.60, 1.0))
            except Exception: pass
            try: c.set_editor_property("fog_max_opacity", 0.45)
            except Exception: pass
        log("Fog warm-grey dens~0.10")
    if "SkyAtmosphere" in cn or "AtmosphericFog" in cn:
        log("found atmosphere " + cn)
        try:
            for c in a.get_components_by_class(unreal.SkyAtmosphereComponent):
                try: c.set_editor_property("rayleigh_scattering", unreal.LinearColor(0.12, 0.18, 0.30, 1.0))  # less blue
                except Exception: pass
        except Exception:
            pass
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        try:
            try: a.set_editor_property("unbound", True)
            except Exception: pass
            s = a.get_editor_property("settings")
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 4800.0)  # warmer
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", 0.35)
                s.set_editor_property("override_auto_exposure_min_brightness", True)
                s.set_editor_property("auto_exposure_min_brightness", 0.6)
                s.set_editor_property("override_auto_exposure_max_brightness", True)
                s.set_editor_property("auto_exposure_max_brightness", 1.4)
            except Exception: pass
            try:
                s.set_editor_property("override_bloom_intensity", True)
                s.set_editor_property("bloom_intensity", 0.08)
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP temp4800 bias0.35")
        except Exception as e:
            log("PP " + str(e))

# Ensure SandRamp placement
for a in actors():
    if label(a) == "TidebornEnv_SandRamp" or "SandRamp" in label(a):
        a.set_actor_location(unreal.Vector(1000.0, 520.0, 105.5), False, True)
        a.set_actor_scale3d(unreal.Vector(2.0, 1.3, 1.15))  # wider + slightly taller slope
        force_apply(a, sand)
        log("SandRamp (1000,520,105.5) sc=(2.0,1.3,1.15)")

# Shallows
for a in actors():
    if label(a) == "TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000.0, 420.0, 100.0), False, True)
        sc = a.get_actor_scale3d()
        a.set_actor_scale3d(unreal.Vector(sc.x, 6.5, sc.z))
        force_apply(a, water)

# Corridor waterline boulders — IN view through gap (X near 900/1100 edges, Y~600-680)
boulder_mesh = None
for a in actors():
    if label(a).startswith("TidebornEnv_Boulder") and "Waterline" not in label(a) and "WLB" not in label(a):
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            try:
                boulder_mesh = comp.get_editor_property("static_mesh")
            except Exception: pass
        if boulder_mesh: break
if boulder_mesh:
    spots = [
        (880, 610, 101, 2.0, -30),
        (860, 670, 100, 1.7, 40),
        (1120, 620, 101, 2.1, 20),
        (1140, 680, 100, 1.8, -55),
        (900, 700, 100, 1.5, 10),
        (1100, 650, 100, 1.6, -20),
    ]
    for i, (x, y, z, s, yaw) in enumerate(spots):
        a = eas.spawn_actor_from_object(boulder_mesh, unreal.Vector(float(x), float(y), float(z)), unreal.Rotator(0, float(yaw), 0))
        if a:
            a.set_actor_label("TidebornEnv_WLB_%02d" % i)
            a.set_actor_scale3d(unreal.Vector(s, s, s * 0.8))
            force_apply(a, rock)
            log("WLB %02d (%.0f,%.0f)" % (i, x, y))

# CONFIRM
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

try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("saved level")
except Exception as e:
    log("save " + str(e))
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception:
    pass

# ---- SHOT (same session, materials live) ----
SHOT_DIR.mkdir(parents=True, exist_ok=True)
target = SHOT_DIR / (SHOT_NAME + ".png")
if target.exists():
    try: target.unlink()
    except Exception: pass
auto = ROOT / "Saved" / "AutoScreenshot.png"
for cmd in ("ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0","ShowFlag.Bounds 0","ShowFlag.Collision 0","ShowFlag.LightRadius 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(SHOT_LOC[0], SHOT_LOC[1], SHOT_LOC[2]),
        unreal.Rotator(pitch=SHOT_ROT[0], yaw=SHOT_ROT[1], roll=SHOT_ROT[2]),
    )
except Exception as e:
    log("cam " + str(e))
log("SHOT begin " + SHOT_NAME)
try:
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, SHOT_NAME)
except Exception as e:
    log("auto " + str(e))
try:
    unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
except Exception:
    pass
ok = False
for i in range(100):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size > 20000:
        ok = True; break
    if auto.exists() and auto.stat().st_size > 20000:
        try:
            import shutil
            shutil.copy2(str(auto), str(target)); ok = True; break
        except Exception:
            pass
time.sleep(2.0)
if not ok and target.exists() and target.stat().st_size > 20000:
    ok = True
log("SHOT end ok=%s size=%s" % (ok, target.stat().st_size if target.exists() else 0))
(ROOT / "Tools" / "art" / "_shot_done.txt").write_text(
    "name=%s ok=%s size=%s\n" % (SHOT_NAME, ok, target.stat().st_size if target.exists() else 0), encoding="utf-8")

log("DONE")
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
