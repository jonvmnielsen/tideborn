# -*- coding: utf-8 -*-
"""v7: warm sand/rocks, kill cool HDRI cast, widen mouth, keep WetSand/SkyAtmosphere."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v7_result.txt"
DUMP = ROOT / "Tools" / "art" / "cove_dump_v7_after.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"

lines = []
def log(m):
    t = str(m); unreal.log("[V7] " + t); lines.append(t)
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
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    col.set_editor_property("constant", unreal.LinearColor(float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 120)
    r.set_editor_property("r", float(rough))
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)
    m.set_editor_property("r", 0.0)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 280)
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

# A) Materials — warm sand, brown-grey rocks, deep blue water, dark wet
rock = make_lit("M_Tideborn_RockShore", (0.18, 0.14, 0.10), rough=0.96)
make_lit("MI_Tideborn_RockDark", (0.18, 0.14, 0.10), rough=0.96)
sand_warm = make_lit("MI_Tideborn_SandWarm", (0.55, 0.42, 0.28), rough=0.97)
make_lit("M_Tideborn_Sand", (0.55, 0.42, 0.28), rough=0.97)
sand_wet = make_lit("MI_Tideborn_SandWet", (0.10, 0.07, 0.05), rough=0.38)
water = make_lit("M_Tideborn_WaterOpaque", (0.05, 0.15, 0.35), rough=0.10)
ground = make_lit("M_Tideborn_Ground", (0.30, 0.32, 0.16), rough=0.9)
bark = make_lit("M_Tideborn_Bark", (0.28, 0.16, 0.08), rough=0.9)

# B) Widen mouth: Boulder/WLB with X in [800,1200] AND Y in [200,900] -> X<=550 or >=1450
moved = 0
side = 0
for a in list(actors()):
    lab = label(a)
    loc = a.get_actor_location()
    if not (("Boulder" in lab) or lab.startswith("TidebornEnv_WLB_")):
        continue
    if 600 <= loc.x <= 1400 and 200 <= loc.y <= 1000:
        new_x = 480.0 if (side % 2 == 0) else 1520.0
        new_y = loc.y + ((side % 5) - 2) * 28.0
        # Lower tallest near-mouth rocks slightly for Verify sightline
        new_z = loc.z
        sc = a.get_actor_scale3d()
        if sc.z >= 2.8 or sc.x >= 2.8:
            a.set_actor_scale3d(unreal.Vector(sc.x * 0.85, sc.y * 0.85, sc.z * 0.75))
            log("LOWER %s sc was (%.2f,%.2f,%.2f)" % (lab, sc.x, sc.y, sc.z))
        a.set_actor_location(unreal.Vector(new_x, new_y, new_z), False, True)
        force_apply(a, rock)
        log("MOVE mouth %s (%.0f,%.0f)->(%.0f,%.0f)" % (lab, loc.x, loc.y, new_x, new_y))
        side += 1
        moved += 1
log("moved_mouth=%d" % moved)

# Also push any remaining corridor blockers X[850,1150] Y[400,850]
extra = 0
for a in list(actors()):
    lab = label(a)
    loc = a.get_actor_location()
    if not (("Boulder" in lab) or lab.startswith("TidebornEnv_WLB_") or lab == "TidebornEnv_ShoreEdge"):
        continue
    if 850 <= loc.x <= 1150 and 400 <= loc.y <= 850:
        if lab == "TidebornEnv_ShoreEdge":
            try:
                eas.destroy_actor(a); log("x ShoreEdge corridor"); extra += 1
            except Exception as e:
                log("destroy ShoreEdge " + str(e))
            continue
        new_x = 500.0 if (extra % 2 == 0) else 1500.0
        a.set_actor_location(unreal.Vector(new_x, loc.y, loc.z), False, True)
        force_apply(a, rock)
        log("MOVE extra %s -> X=%.0f" % (lab, new_x)); extra += 1
log("extra_moved=%d" % extra)

# LOCK SandBase + water Z < sand + WetSand dark band (keep pattern that worked)
wetsand_ok = False
for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000.0, 1500.0, 106.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 18.0, 1.0))
        force_apply(a, sand_warm)
        log("LOCK SandBase Z=106 sc=(45,18) Y[600..2400]")
    elif lab == "TidebornEnv_SandRamp" or "SandRamp" in lab:
        a.set_actor_location(unreal.Vector(1000.0, 640.0, 105.3), False, True)
        a.set_actor_scale3d(unreal.Vector(0.22, 0.14, 0.6))
        force_apply(a, sand_wet)
        log("SandRamp Y=640 wet")
    elif lab == "TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000.0, -800.0, 99.0), False, True)
        a.set_actor_scale3d(unreal.Vector(80.0, 18.0, 1.0))
        force_apply(a, water)
        log("Ocean Z=99 scY=18")
    elif lab == "TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000.0, 350.0, 100.0), False, True)
        a.set_actor_scale3d(unreal.Vector(60.0, 12.0, 1.0))
        force_apply(a, water)
        log("Shallows Z=100 scY=12")
    elif lab == "TidebornEnv_WetSand_00" or lab.startswith("TidebornEnv_WetSand_"):
        # Keep dark wet band pattern from Waterline PASS (scY~2–2.5)
        a.set_actor_location(unreal.Vector(1000.0, 650.0, 105.5), False, True)
        a.set_actor_scale3d(unreal.Vector(50.0, 2.5, 1.0))
        force_apply(a, sand_wet)
        wetsand_ok = True
        log("KEEP WetSand_00 dark sc=(50,2.5) Y[525..775]")
    elif lab == "TidebornEnv_Ground":
        force_apply(a, ground)
    elif "Boulder" in lab or lab.startswith("TidebornEnv_WLB_"):
        force_apply(a, rock)
    elif "Trunk" in lab:
        force_apply(a, bark)

if not wetsand_ok:
    plane = load("/Engine/BasicShapes/Plane")
    if plane:
        a = eas.spawn_actor_from_object(
            plane, unreal.Vector(1000.0, 650.0, 105.5), unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
        if a:
            a.set_actor_label("TidebornEnv_WetSand_00")
            a.set_actor_scale3d(unreal.Vector(50.0, 2.5, 1.0))
            force_apply(a, sand_wet)
            log("SPAWN WetSand_00 dark sc=(50,2.5)")

# A) Lighting — clear cool HDRI cubemap, warm SkyLight color, warm Dir, warm fog, warm PP
for a in actors():
    cn = cname(a); lab = label(a)
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        unhide(a)
        log("KEEP " + cn)
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            # Clear cool industrial HDRI — use capturable sky / none + warm color
            try: c.set_editor_property("real_time_capture", True)
            except Exception: pass
            try: c.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
            except Exception:
                try: c.set_editor_property("source_type", 0)
                except Exception: pass
            try: c.set_editor_property("cubemap", None)
            except Exception: pass
            try: c.set_editor_property("intensity", 1.0)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.90, 0.75, 1.0))
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_is_black", False)
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_color", unreal.LinearColor(0.55, 0.42, 0.28, 1.0))
            except Exception: pass
            try: c.recapture_sky()
            except Exception: pass
        log("SkyLight intensity=1.0 warm color, cubemap CLEARED (realtime capture)")
    if "DirectionalLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 2.2)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.85, 0.65, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 0.55)
            except Exception: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except Exception: pass
            try:
                c.set_editor_property("use_temperature", False)
                c.set_editor_property("temperature", 4500.0)
            except Exception: pass
        # Pitch -40 from ocean side (yaw -90 looks toward +Y / shore)
        a.set_actor_rotation(unreal.Rotator(pitch=-40.0, yaw=-90.0, roll=0.0), False)
        log("DirLight warm (1,0.85,0.65) int=2.2 pitch=-40")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.025)
            except Exception: pass
            # Warm-grey inscattering (NOT purple)
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.72, 0.62, 0.48, 1.0))
            except Exception: pass
            try: c.set_editor_property("directional_inscattering_color", unreal.LinearColor(1.0, 0.82, 0.55, 1.0))
            except Exception: pass
        log("Fog density=0.025 warm-grey")
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        unhide(a)
        try:
            try: a.set_editor_property("unbound", True)
            except Exception: pass
            s = a.get_editor_property("settings")
            # Neutralize cool LUT / look
            for lut_prop in ("color_grading_lut", "look_up_table"):
                try: s.set_editor_property(lut_prop, None)
                except Exception: pass
            for ov in ("override_color_grading_lut", "override_color_grading_intensity"):
                try: s.set_editor_property(ov, False)
                except Exception: pass
            try:
                s.set_editor_property("override_color_grading_intensity", True)
                s.set_editor_property("color_grading_intensity", 0.0)
            except Exception: pass
            # WhiteTemp warm ~5600K (parent), strong warm gain
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 5600.0)
            except Exception: pass
            try:
                s.set_editor_property("override_white_tint", True)
                s.set_editor_property("white_tint", 0.05)  # slight magenta cancel / warm
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", -0.25)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_method", True)
                s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            except Exception: pass
            # Global saturation mild + color gain R↑ G mid B↓
            try:
                s.set_editor_property("override_color_saturation", True)
                s.set_editor_property("color_saturation", unreal.Vector4(1.05, 1.05, 1.05, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.18, 1.00, 0.72, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_color_gamma", True)
                s.set_editor_property("color_gamma", unreal.Vector4(1.02, 1.00, 0.95, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_scene_color_tint", True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.05, 0.95, 0.82, 1.0))
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP white_temp=5600 gain=(1.18,1.00,0.72) LUT cleared")
        except Exception as e:
            log("PP " + str(e))
    if lab == "TidebornEnv_SkyDome":
        unhide(a)

for cmd in ("r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
            "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

# After-dump
dump_lines = []
for a in actors():
    lab = label(a)
    if not lab.startswith("Tideborn"):
        continue
    if not any(k in lab for k in ("SandBase","Ocean","Shallows","WetSand","ShoreEdge","WLB_","Boulder","SandRamp","Ground")):
        continue
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    hy = 50.0 * sc.y
    mats = []
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(2):
            try:
                m = comp.get_material(i)
                if m: mats.append(m.get_name())
            except Exception: break
        break
    dump_lines.append("%s loc=(%.0f,%.0f,%.1f) sc=(%.2f,%.2f) Y[%.0f..%.0f] %s" % (
        lab, loc.x, loc.y, loc.z, sc.x, sc.y, loc.y - hy, loc.y + hy, ",".join(mats) or "-"))
# Mouth remaining
mouth_left = 0
for a in actors():
    lab = label(a)
    if not (("Boulder" in lab) or lab.startswith("TidebornEnv_WLB_")): continue
    loc = a.get_actor_location()
    if 800 <= loc.x <= 1200 and 200 <= loc.y <= 900:
        dump_lines.append("STILL_MOUTH %s (%.0f,%.0f)" % (lab, loc.x, loc.y))
        mouth_left += 1
dump_lines.append("mouth_remaining=%d" % mouth_left)
DUMP.write_text("\n".join(dump_lines) + "\n", encoding="utf-8")
log("dump_after %d mouth_remaining=%d" % (len(dump_lines), mouth_left))

try: log("save %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")

