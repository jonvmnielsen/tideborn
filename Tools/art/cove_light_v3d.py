# -*- coding: utf-8 -*-
"""Cove light v3 + living-shore pass:
- warmer/softer DirectionalLight, brighter SkyLight, denser bluish fog
- denser sand tiling (60-80)
- muted non-emissive ShoreGate wood
- shallows nudge for verify FOV
- import/spawn small SM_TidebornSandRamp at waterline (does NOT replace SandBase)
Hard floor locked: SandBase Z=106 Y[600..2400] sc=(45,18); Shallows Z=100; Ocean Z=99; water scY<=18
"""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_light_v3d_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
TEX = "/Game/Tideborn/Art/Textures"
MESH = "/Game/Tideborn/Art/Meshes"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
FBX = ROOT / "Tools" / "art" / "export" / "SM_TidebornSandRamp.fbx"

HARD = {
    "TidebornEnv_SandBase": dict(x=1000.0, y=1500.0, z=106.0, sx=45.0, sy=18.0),
    "TidebornEnv_Ground":   dict(x=1000.0, y=2800.0, z=105.0, sx=45.0, sy=16.0),
    "TidebornEnv_Ocean":    dict(x=1000.0, y=-900.0, z=99.0,  sx=70.0, sy=18.0),
}
SHALLOWS = dict(x=1000.0, y=450.0, z=100.0, sx=55.0, sy=6.0)
# Ramp sits on SandBase waterline edge (Y~600), mild overlap into shallows
RAMP = dict(x=1000.0, y=550.0, z=104.0, sx=1.0, sy=1.0, sz=1.0)

lines = []

def log(m):
    t = str(m)
    unreal.log("[LightV3d] " + t)
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

def make_sand(tile=72.0):
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
    base_col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 120)
    base_col.set_editor_property("constant", unreal.LinearColor(0.84, 0.72, 0.52, 1.0))
    if bc:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, -80)
        ts.set_editor_property("texture", bc)
        mel.connect_material_expressions(mul, "", ts, "UVs")
        lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -120, 0)
        mel.connect_material_expressions(base_col, "", lerp, "A")
        mel.connect_material_expressions(ts, "RGB", lerp, "B")
        alpha = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 40)
        alpha.set_editor_property("r", 0.18)
        mel.connect_material_expressions(alpha, "", lerp, "Alpha")
        mel.connect_material_property(lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    else:
        mel.connect_material_property(base_col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    if rough:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, 200)
        ts.set_editor_property("texture", rough)
        try:
            ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        except Exception:
            pass
        mel.connect_material_expressions(mul, "", ts, "UVs")
        mel.connect_material_property(ts, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    em = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 320)
    em.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("sand tile=%.0f soft_blend=0.18 warm" % tile)
    return mat

def make_gate_wood():
    """Darker weathered wood — replace teal/emissive GateSolid."""
    name = "M_Tideborn_GateSolid"
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    # Weathered brown wood, muted
    col.set_editor_property("constant", unreal.LinearColor(0.28, 0.18, 0.10, 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 100)
    r.set_editor_property("r", 0.88)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    em = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 200)
    em.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("gate wood mat recreated (muted brown, non-emissive)")
    return mat

def soften_atmosphere():
    has_dir = False
    has_sky = False
    has_fog = False
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors():
        cn = cname(a)
        if "DirectionalLight" in cn:
            has_dir = True
            try:
                comps = a.get_components_by_class(unreal.DirectionalLightComponent)
                for c in comps:
                    try:
                        c.set_editor_property("intensity", 1.3)
                    except Exception:
                        pass
                    try:
                        # warmer slight orange
                        c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.92, 0.78, 1.0))
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("indirect_lighting_intensity", 2.2)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("shadow_amount", 0.45)
                    except Exception:
                        pass
                a.set_actor_rotation(unreal.Rotator(pitch=-42, yaw=38, roll=0), False)
                try:
                    a.set_editor_property("intensity", 1.3)
                except Exception:
                    pass
                log("DirectionalLight intensity~1.3 warm orange pitch=-42 yaw=38")
            except Exception as e:
                log("DirectionalLight warn: %s" % e)
        if "SkyLight" in cn:
            has_sky = True
            try:
                comps = a.get_components_by_class(unreal.SkyLightComponent)
                for c in comps:
                    try:
                        c.set_editor_property("intensity", 8.0)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("real_time_capture", True)
                    except Exception:
                        pass
                try:
                    a.set_editor_property("intensity", 8.0)
                except Exception:
                    pass
                log("SkyLight intensity~8.0")
            except Exception as e:
                log("SkyLight warn: %s" % e)
        if "ExponentialHeightFog" in cn:
            has_fog = True
            try:
                comps = a.get_components_by_class(unreal.ExponentialHeightFogComponent)
                for c in comps:
                    try:
                        c.set_editor_property("fog_density", 0.12)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("fog_height_falloff", 0.18)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.50, 0.66, 0.88, 1.0))
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("volumetric_fog", True)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("volumetric_fog_extinction_scale", 0.7)
                    except Exception:
                        pass
                try:
                    a.set_editor_property("fog_density", 0.12)
                except Exception:
                    pass
                log("ExponentialHeightFog density~0.12 bluish inscatter")
            except Exception as e:
                log("Fog warn: %s" % e)

        if "PostProcess" in cn:
            try:
                comps = a.get_components_by_class(unreal.PostProcessComponent)
                for c in comps:
                    try:
                        settings = c.get_editor_property("settings")
                        settings.set_editor_property("override_auto_exposure_bias", True)
                        settings.set_editor_property("auto_exposure_bias", 1.0)
                        settings.set_editor_property("override_auto_exposure_min_brightness", True)
                        settings.set_editor_property("auto_exposure_min_brightness", 0.7)
                        c.set_editor_property("settings", settings)
                        log("PostProcess exposure_bias~1.0")
                    except Exception as e:
                        log("PP warn: %s" % e)
            except Exception as e:
                log("PostProcess warn: %s" % e)

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
                        c.set_editor_property("fog_density", 0.12)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("fog_height_falloff", 0.18)
                    except Exception:
                        pass
                    try:
                        c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.50, 0.66, 0.88, 1.0))
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

def import_ramp_fbx():
    if not FBX.exists():
        log("MISSING ramp fbx: %s" % FBX)
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
    log("import ramp -> %s" % paths)
    mesh = None
    for p in paths:
        a = load(p)
        if isinstance(a, unreal.StaticMesh):
            mesh = a
            break
    if not mesh:
        mesh = load(MESH + "/SM_TidebornSandRamp")
    return mesh

def place_ramp(mesh, sand_mat):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    # Remove prior SandRamp only (never touch SandBase)
    for a in list(actors()):
        lab = label(a)
        if lab == "TidebornEnv_SandRamp" or "SandRamp" in lab:
            try:
                eas.destroy_actor(a)
                log("x old " + lab)
            except Exception:
                pass
    if not mesh:
        log("no ramp mesh — skip spawn")
        return None
    # Bake sand onto mesh slots
    try:
        s = unreal.StaticMaterial()
        s.set_editor_property("material_interface", sand_mat)
        mesh.set_editor_property("static_materials", [s])
        unreal.EditorAssetLibrary.save_asset(MESH + "/SM_TidebornSandRamp")
    except Exception as e:
        log("bake ramp mat: %s" % e)
    r = RAMP
    act = eas.spawn_actor_from_object(
        mesh,
        unreal.Vector(r["x"], r["y"], r["z"]),
        unreal.Rotator(pitch=0, yaw=0, roll=0),
    )
    if not act:
        log("FAILED spawn SandRamp")
        return None
    try:
        act.set_actor_label("TidebornEnv_SandRamp")
    except Exception:
        pass
    act.set_actor_scale3d(unreal.Vector(r["sx"], r["sy"], r["sz"]))
    apply(act, sand_mat)
    # Sanity: bounding extent should be ~40m x 12m; if absurd, delete
    try:
        loc = act.get_actor_location()
        sc = act.get_actor_scale3d()
        box = mesh.get_bounding_box()
        dx = abs((box.max - box.min).x) * sc.x
        dy = abs((box.max - box.min).y) * sc.y
        dz = abs((box.max - box.min).z) * sc.z
        log("SandRamp bounds dx=%.0f dy=%.0f dz=%.0f loc=(%.0f,%.0f,%.0f)" % (
            dx, dy, dz, loc.x, loc.y, loc.z))
        if dx > 20000 or dy > 20000 or dz > 2000 or dx < 100:
            log("FAIL ramp scale absurd — deleting actor, keeping plane floor")
            eas.destroy_actor(act)
            return None
    except Exception as e:
        log("ramp bounds warn: %s" % e)
    log("placed TidebornEnv_SandRamp")
    return act

def confirm(a, name):
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    hy = 50.0 * sc.y
    # Prefer mesh bounds for non-plane
    extra = ""
    try:
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            sm = comp.get_editor_property("static_mesh")
            if sm:
                box = sm.get_bounding_box()
                dx = abs((box.max - box.min).x) * sc.x
                dy = abs((box.max - box.min).y) * sc.y
                extra = " meshXY=(%.0f,%.0f)" % (dx, dy)
                hy = dy * 0.5
                break
    except Exception:
        pass
    log("CONFIRM %s Z=%.0f Y[%.0f..%.0f] sc=(%.1f,%.1f,%.1f)%s" % (
        name, loc.z, loc.y - hy, loc.y + hy, sc.x, sc.y, sc.z, extra))

# --- main ---
try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e:
    log("load " + str(e))

sand = make_sand(72.0)
gate_mat = make_gate_wood()
water = load(MAT + "/M_Tideborn_WaterOpaque") or load(MAT + "/M_Tideborn_WaterSimple")
ground = load(MAT + "/M_Tideborn_Ground") or sand

found = {}
for a in actors():
    lab = label(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_Shallows", "TidebornEnv_Ocean", "TidebornEnv_Ground"):
        found[lab] = a
    if "ShoreGate" in lab or lab == "Tideborn_P2_ShoreGate":
        apply(a, gate_mat)
        log("ShoreGate -> muted GateSolid wood")
        for comp in a.get_components_by_class(unreal.LightComponent):
            try: comp.modify()
            except Exception: pass
            try: comp.set_editor_property("light_color", unreal.LinearColor(1.0, 0.75, 0.45, 1.0))
            except Exception: pass
            try: comp.set_editor_property("intensity", 600.0)
            except Exception: pass
            try: comp.set_editor_property("cast_shadows", False)
            except Exception: pass
            log("ShoreGate VistaLight muted warm intensity~600")

log("found planes: " + (",".join(sorted(found.keys())) or "NONE"))

# Lock hard floor; only nudge shallows
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

# Keep sand ramp mat in sync with soft sand
for a in actors():
    lab = label(a)
    if lab == "TidebornEnv_SandRamp" or "SandRamp" in lab:
        apply(a, sand)
        log("SandRamp -> soft warm sand")

soften_atmosphere()

ramp_mesh = import_ramp_fbx()
ramp_actor = place_ramp(ramp_mesh, sand)

# Safety checks
ok = True
for name in ("TidebornEnv_SandBase", "TidebornEnv_Shallows", "TidebornEnv_Ocean", "TidebornEnv_Ground"):
    if name not in found:
        ok = False
        continue
    confirm(found[name], name)
if ramp_actor:
    confirm(ramp_actor, "TidebornEnv_SandRamp")

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
        if sy > 18.0:
            log("FAIL %s scY=%.1f > 18" % (wname, sy))
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

log("light_ok=%s" % ok)
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
