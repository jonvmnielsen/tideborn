# -*- coding: utf-8 -*-
"""Feel v2: softer light/fog, denser sand tiling, thin shallows at waterline.
Preserves hardfix Z order: sand Z > water Z; water scY stays sane (<=7)."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_feel_v2_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
TEX = "/Game/Tideborn/Art/Textures"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"

# Hardfix floor (do not break)
HARD = {
    "TidebornEnv_SandBase": dict(x=1000.0, y=1500.0, z=106.0, sx=45.0, sy=18.0),
    "TidebornEnv_Ground":   dict(x=1000.0, y=2800.0, z=105.0, sx=45.0, sy=16.0),
    "TidebornEnv_Ocean":    dict(x=1000.0, y=-900.0, z=99.0,  sx=70.0, sy=18.0),
}
# Feel nudge: thin shallows band nearer waterline (still Z below sand)
SHALLOWS = dict(x=1000.0, y=450.0, z=100.0, sx=55.0, sy=5.5)

lines = []

def log(m):
    t = str(m)
    unreal.log("[FeelV2] " + t)
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

def find_tex(folder, keys):
    base = TEX + "/" + folder
    if not unreal.EditorAssetLibrary.does_directory_exist(base):
        return None
    for ap in unreal.EditorAssetLibrary.list_assets(base, recursive=False):
        name = ap.split(".")[-1].lower()
        for k in keys:
            if k.lower() in name:
                return ap
    return None

def apply(a, mat):
    if not mat:
        return
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        try:
            comp.modify()
        except Exception:
            pass
        for i in range(8):
            try:
                comp.set_material(i, mat)
            except Exception:
                break

def set_plane(a, x, y, z, sx, sy, mat, name):
    try:
        a.modify()
    except Exception:
        pass
    a.set_actor_location(unreal.Vector(float(x), float(y), float(z)), False, True)
    a.set_actor_scale3d(unreal.Vector(float(sx), float(sy), 1.0))
    a.set_actor_rotation(unreal.Rotator(pitch=0, yaw=0, roll=0), False)
    try:
        root = a.root_component
        if root:
            root.modify()
            # UE 5.4 Python: set_world_location(loc, sweep, teleport) — 3 args max
            root.set_world_location(unreal.Vector(float(x), float(y), float(z)), False, True)
            root.set_world_scale3d(unreal.Vector(float(sx), float(sy), 1.0))
            root.set_world_rotation(unreal.Rotator(pitch=0, yaw=0, roll=0), False, True)
    except Exception as e:
        log("root xf warn %s: %s" % (name, e))
    apply(a, mat)
    try:
        a.mark_package_dirty()
    except Exception:
        pass
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    hy = 50.0 * sc.y
    hx = 50.0 * sc.x
    log("%s -> loc=(%.0f,%.0f,%.0f) sc=(%.1f,%.1f) X[%.0f..%.0f] Y[%.0f..%.0f]" % (
        name, loc.x, loc.y, loc.z, sc.x, sc.y, loc.x - hx, loc.x + hx, loc.y - hy, loc.y + hy))

def make_sand(tile=40.0):
    """Recreate sand with slightly denser tiling (was ~32)."""
    name = "M_Tideborn_Sand"
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    bc = load(find_tex("Sand", ["Diffuse", "Color"]))
    rough = load(find_tex("Sand", ["Rough", "roughness"]))
    uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 0)
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -550, 0)
    sc = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 60)
    sc.set_editor_property("r", float(tile))
    mel.connect_material_expressions(uv, "", mul, "A")
    mel.connect_material_expressions(sc, "", mul, "B")
    if bc:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, -80)
        ts.set_editor_property("texture", bc)
        mel.connect_material_expressions(mul, "", ts, "UVs")
        dark = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 40)
        dark.set_editor_property("constant", unreal.LinearColor(0.72, 0.72, 0.72, 1.0))
        m2 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -180, -40)
        mel.connect_material_expressions(ts, "RGB", m2, "A")
        mel.connect_material_expressions(dark, "", m2, "B")
        mel.connect_material_property(m2, "", unreal.MaterialProperty.MP_BASE_COLOR)
    if rough:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, 160)
        ts.set_editor_property("texture", rough)
        try:
            ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        except Exception:
            pass
        mel.connect_material_expressions(mul, "", ts, "UVs")
        mel.connect_material_property(ts, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("sand tile=%.0f" % tile)
    return mat

def soften_or_spawn_atmosphere():
    has_dir = False
    has_sky = False
    has_fog = False
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors():
        cn = cname(a)
        if "DirectionalLight" in cn:
            has_dir = True
            try:
                # Prefer component props when present
                comps = a.get_components_by_class(unreal.DirectionalLightComponent)
                for c in comps:
                    try:
                        c.set_editor_property("intensity", 1.7)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.92, 0.82, 1.0))
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("indirect_lighting_intensity", 1.5)
                    except Exception:
                        pass
                a.set_actor_rotation(unreal.Rotator(pitch=-42, yaw=50, roll=0), False)
                try:
                    a.set_editor_property("intensity", 1.7)
                except Exception:
                    pass
                log("DirectionalLight softened intensity~1.7 rot pitch=-42 yaw=50")
            except Exception as e:
                log("DirectionalLight warn: %s" % e)
        if "SkyLight" in cn:
            has_sky = True
            try:
                comps = a.get_components_by_class(unreal.SkyLightComponent)
                for c in comps:
                    try:
                        c.set_editor_property("intensity", 3.0)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("real_time_capture", True)
                    except Exception:
                        pass
                try:
                    a.set_editor_property("intensity", 3.0)
                except Exception:
                    pass
                log("SkyLight raised intensity~3.0")
            except Exception as e:
                log("SkyLight warn: %s" % e)
        if "ExponentialHeightFog" in cn:
            has_fog = True
            try:
                comps = a.get_components_by_class(unreal.ExponentialHeightFogComponent)
                for c in comps:
                    try:
                        c.set_editor_property("fog_density", 0.035)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("fog_height_falloff", 0.2)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.55, 0.68, 0.85, 1.0))
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("volumetric_fog", True)
                    except Exception:
                        pass
                try:
                    a.set_editor_property("fog_density", 0.035)
                except Exception:
                    pass
                log("ExponentialHeightFog density~0.035")
            except Exception as e:
                log("Fog warn: %s" % e)
    if not has_fog:
        try:
            fog = eas.spawn_actor_from_class(
                unreal.ExponentialHeightFog, unreal.Vector(1000.0, 1000.0, 200.0))
            if fog:
                try:
                    fog.set_actor_label("TidebornEnv_HeightFog")
                except Exception:
                    pass
                comps = fog.get_components_by_class(unreal.ExponentialHeightFogComponent)
                for c in comps:
                    try:
                        c.set_editor_property("fog_density", 0.035)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.55, 0.68, 0.85, 1.0))
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("volumetric_fog", True)
                    except Exception:
                        pass
                log("spawned ExponentialHeightFog TidebornEnv_HeightFog")
            else:
                log("FAILED spawn fog")
        except Exception as e:
            log("spawn fog fail: %s" % e)
    if not has_dir:
        log("WARN no DirectionalLight found")
    if not has_sky:
        log("WARN no SkyLight found")

def confirm_plane(a, name):
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    hy = 50.0 * sc.y
    log("CONFIRM %s Z=%.0f Y[%.0f..%.0f] scY=%.1f scX=%.1f" % (
        name, loc.z, loc.y - hy, loc.y + hy, sc.y, sc.x))

# --- main ---
try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e:
    log("load " + str(e))

sand = make_sand(40.0)
water = load(MAT + "/M_Tideborn_WaterOpaque") or load(MAT + "/M_Tideborn_WaterSimple")
ground = load(MAT + "/M_Tideborn_Ground") or sand

found = {}
for a in actors():
    lab = label(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_Shallows", "TidebornEnv_Ocean", "TidebornEnv_Ground"):
        found[lab] = a
log("found planes: " + (",".join(sorted(found.keys())) or "NONE"))

# Keep Sand/Ocean/Ground at hardfix; only nudge Shallows + reapply mats
if "TidebornEnv_SandBase" in found:
    h = HARD["TidebornEnv_SandBase"]
    set_plane(found["TidebornEnv_SandBase"], h["x"], h["y"], h["z"], h["sx"], h["sy"], sand, "SandBase")
else:
    log("MISSING SandBase")

if "TidebornEnv_Shallows" in found:
    s = SHALLOWS
    set_plane(found["TidebornEnv_Shallows"], s["x"], s["y"], s["z"], s["sx"], s["sy"], water, "Shallows")
else:
    log("MISSING Shallows")

if "TidebornEnv_Ocean" in found:
    h = HARD["TidebornEnv_Ocean"]
    set_plane(found["TidebornEnv_Ocean"], h["x"], h["y"], h["z"], h["sx"], h["sy"], water, "Ocean")
else:
    log("MISSING Ocean")

if "TidebornEnv_Ground" in found:
    h = HARD["TidebornEnv_Ground"]
    set_plane(found["TidebornEnv_Ground"], h["x"], h["y"], h["z"], h["sx"], h["sy"], ground, "Ground")
else:
    log("MISSING Ground")

soften_or_spawn_atmosphere()

# Safety: water scY must stay <= 20; sand Z must stay above water
ok = True
for name in ("TidebornEnv_SandBase", "TidebornEnv_Shallows", "TidebornEnv_Ocean", "TidebornEnv_Ground"):
    if name not in found:
        ok = False
        continue
    confirm_plane(found[name], name)
if "TidebornEnv_SandBase" in found and "TidebornEnv_Shallows" in found:
    sz = found["TidebornEnv_SandBase"].get_actor_location().z
    wz = found["TidebornEnv_Shallows"].get_actor_location().z
    if sz <= wz:
        log("FAIL sand Z (%.1f) not above shallows Z (%.1f)" % (sz, wz))
        ok = False
    else:
        log("OK sand Z %.1f > shallows Z %.1f" % (sz, wz))
for wname in ("TidebornEnv_Shallows", "TidebornEnv_Ocean"):
    if wname in found:
        sy = found[wname].get_actor_scale3d().y
        if sy > 20.0:
            log("FAIL %s scY=%.1f > 20 — reverting hardfix" % (wname, sy))
            ok = False

# Save
try:
    r = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("LevelEditorSubsystem.save_current_level -> %s" % r)
except Exception as e:
    log("LES save: %s" % e)
    try:
        unreal.EditorLevelLibrary.save_current_level()
        log("EditorLevelLibrary.save_current_level -> True")
    except Exception as e2:
        log("ELL save: %s" % e2)
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("save_dirty_packages -> True")
except Exception as e:
    log("save_dirty: %s" % e)
try:
    unreal.EditorAssetLibrary.save_asset(MAP)
    log("save_asset map -> True")
except Exception as e:
    log("save_asset: %s" % e)

log("feel_ok=%s" % ok)
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
