# -*- coding: utf-8 -*-
"""v6: clear waterline corridor, fill Overview water, dark wet band, warm rocks. NO shot."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v6_result.txt"
DUMP = ROOT / "Tools" / "art" / "cove_dump_v6_after.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
HDRI = "/Game/Tideborn/Art/HDRI/PH_industrial_sunset_puresky"

lines = []
def log(m):
    t = str(m); unreal.log("[V6] " + t); lines.append(t)
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

# Materials — DARK wet, mid beige sand, brown-grey rocks
rock = make_lit("M_Tideborn_RockShore", (0.12, 0.10, 0.08), rough=0.96)
make_lit("MI_Tideborn_RockDark", (0.12, 0.10, 0.08), rough=0.96)
sand_warm = make_lit("MI_Tideborn_SandWarm", (0.55, 0.45, 0.32), rough=0.97)
make_lit("M_Tideborn_Sand", (0.55, 0.45, 0.32), rough=0.97)
sand_wet = make_lit("MI_Tideborn_SandWet", (0.12, 0.10, 0.08), rough=0.40)
water = make_lit("M_Tideborn_WaterOpaque", (0.06, 0.22, 0.38), rough=0.10)
ground = make_lit("M_Tideborn_Ground", (0.28, 0.34, 0.18), rough=0.9)
bark = make_lit("M_Tideborn_Bark", (0.26, 0.15, 0.08), rough=0.9)

# A) Clear waterline sightline — move WLB/boulder/ShoreEdge out of center corridor
moved = 0
side_toggle = 0
for a in list(actors()):
    lab = label(a)
    loc = a.get_actor_location()
    is_blocker = (
        lab.startswith("TidebornEnv_WLB_")
        or ("Boulder" in lab and lab.startswith("TidebornEnv_"))
        or lab == "TidebornEnv_ShoreEdge"
    )
    if not is_blocker:
        continue
    if 850 <= loc.x <= 1150 and 450 <= loc.y <= 850:
        # Keep Y, push X to side as irregular rocks
        if lab == "TidebornEnv_ShoreEdge":
            try:
                eas.destroy_actor(a); log("x ShoreEdge (center corridor)")
            except Exception as e:
                log("destroy ShoreEdge " + str(e))
            continue
        new_x = 650.0 if (side_toggle % 2 == 0) else 1350.0
        # slight Y jitter so sides look irregular
        new_y = loc.y + ((side_toggle % 5) - 2) * 25.0
        a.set_actor_location(unreal.Vector(new_x, new_y, loc.z), False, True)
        force_apply(a, rock)
        log("MOVE %s (%.0f,%.0f) -> (%.0f,%.0f)" % (lab, loc.x, loc.y, new_x, new_y))
        side_toggle += 1
        moved += 1
log("moved_blockers=%d" % moved)

# Delete failed thin wet planes
for a in list(actors()):
    lab = label(a)
    if lab.startswith("TidebornEnv_WetSand_"):
        try:
            eas.destroy_actor(a); log("x " + lab)
        except Exception:
            pass

plane = load("/Engine/BasicShapes/Plane")

# LOCK SandBase forever
for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000.0, 1500.0, 106.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 18.0, 1.0))
        force_apply(a, sand_warm)
        log("LOCK SandBase Z=106 sc=(45,18) Y[600..2400]")
    elif lab == "TidebornEnv_SandRamp" or "SandRamp" in lab:
        # Keep ramp but push slightly inside sand edge, apply wet
        a.set_actor_location(unreal.Vector(1000.0, 640.0, 105.3), False, True)
        a.set_actor_scale3d(unreal.Vector(0.22, 0.14, 0.6))
        force_apply(a, sand_wet)
        log("SandRamp -> Y=640 wet")
    elif lab == "TidebornEnv_Ocean":
        # B) Ocean fills Overview — Z < sand, scY <= 18
        a.set_actor_location(unreal.Vector(1000.0, -800.0, 99.0), False, True)
        a.set_actor_scale3d(unreal.Vector(80.0, 18.0, 1.0))
        force_apply(a, water)
        log("Ocean loc=(1000,-800,99) sc=(80,18) Y[-1700..100]")
    elif lab == "TidebornEnv_Shallows":
        # B) Shallows: Y half=600 -> Y[-250..950], Z=100 < sand
        a.set_actor_location(unreal.Vector(1000.0, 350.0, 100.0), False, True)
        a.set_actor_scale3d(unreal.Vector(60.0, 12.0, 1.0))
        force_apply(a, water)
        log("Shallows loc=(1000,350,100) sc=(60,12) Y[-250..950]")
    elif lab == "TidebornEnv_Ground":
        force_apply(a, ground)
    elif "Boulder" in lab or lab.startswith("TidebornEnv_WLB_"):
        force_apply(a, rock)
    elif "Trunk" in lab:
        force_apply(a, bark)

# C) ONE wide WetSand band just inside sand edge at Y=600
# loc Y=650, scY=2 -> half=100 -> Y[550..750], Z=105.5
if plane:
    a = eas.spawn_actor_from_object(
        plane, unreal.Vector(1000.0, 650.0, 105.5), unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
    if a:
        a.set_actor_label("TidebornEnv_WetSand_00")
        a.set_actor_scale3d(unreal.Vector(50.0, 2.0, 1.0))
        force_apply(a, sand_wet)
        log("WetSand_00 loc=(1000,650,105.5) sc=(50,2) Y[550..750] DARK wet")

# D) Lighting — warmer dir, lower SkyLight (do NOT destroy SkyAtmosphere/SkyLight)
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
            try: c.set_editor_property("intensity", 0.70)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.88, 0.72, 1.0))
            except Exception: pass
            try: c.set_editor_property("source_cubemap_angle", 200.0)
            except Exception: pass
            try: c.recapture_sky()
            except Exception: pass
        log("SkyLight intensity=0.70 (kept)")
    if "DirectionalLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 1.6)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.85, 0.65, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 0.5)
            except Exception: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-32.0, yaw=-90.0, roll=0.0), False)
        log("DirLight warm 1.6")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.04)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.75, 0.65, 0.52, 1.0))
            except Exception: pass
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        unhide(a)
        try:
            try: a.set_editor_property("unbound", True)
            except Exception: pass
            s = a.get_editor_property("settings")
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 4200.0)
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
                s.set_editor_property("color_gain", unreal.Vector4(1.08, 1.00, 0.82, 1.0))
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP warm bias=-0.15")
        except Exception as e:
            log("PP " + str(e))
    if lab == "TidebornEnv_SkyDome":
        unhide(a)

for cmd in ("r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
            "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

# After-dump key actors
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
DUMP.write_text("\n".join(dump_lines) + "\n", encoding="utf-8")
log("dump_after %d" % len(dump_lines))

try: log("save %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
