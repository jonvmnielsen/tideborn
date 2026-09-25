# -*- coding: utf-8 -*-
"""Restore sky/ambient after v4i regression; fix water visibility + sand grain. NO shot."""
from __future__ import annotations
import pathlib, time, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_sky_restore_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
TEX = "/Game/Tideborn/Art/Textures"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"

lines = []
def log(m):
    t = str(m)
    unreal.log("[SkyRestore] " + t)
    lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())

def label(a):
    try: return a.get_actor_label() or ""
    except: return ""

def cname(a):
    try: return a.get_class().get_name() or ""
    except: return ""

def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if p and unreal.EditorAssetLibrary.does_asset_exist(p) else None

def unhide(a):
    try:
        a.set_actor_hidden_in_game(False)
        a.set_is_temporarily_hidden_in_editor(False)
        try:
            a.set_editor_property("b_hidden_ed", False)
        except Exception:
            pass
        try:
            a.set_editor_property("hidden", False)
        except Exception:
            pass
        root = a.root_component
        if root:
            try: root.set_editor_property("visible", True)
            except Exception: pass
            try: root.set_visibility(True, True)
            except Exception: pass
    except Exception as e:
        log("unhide warn " + str(e))

def force_apply(a, mat):
    if not a or not mat: return
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(16):
            try: comp.set_material(i, mat)
            except Exception: break
        try: comp.set_editor_property("override_materials", [mat] * 8)
        except Exception: pass

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

def make_sand_warm_grain(name="MI_Tideborn_SandWarm", tile=55.0):
    """Lit albedo * warm tint; texture if present; NO strong emissive."""
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    bc = load(find_tex("Sand", ["Diffuse", "Color"]))
    rough = load(find_tex("Sand", ["Rough", "roughness"]))
    uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 0)
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -550, 0)
    sc = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 60)
    sc.set_editor_property("r", float(tile))
    mel.connect_material_expressions(uv, "", mul, "A")
    mel.connect_material_expressions(sc, "", mul, "B")
    warm = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 40)
    warm.set_editor_property("constant", unreal.LinearColor(0.92, 0.78, 0.55, 1.0))
    if bc:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, -80)
        ts.set_editor_property("texture", bc)
        mel.connect_material_expressions(mul, "", ts, "UVs")
        m2 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -180, -40)
        mel.connect_material_expressions(ts, "RGB", m2, "A")
        mel.connect_material_expressions(warm, "", m2, "B")
        mel.connect_material_property(m2, "", unreal.MaterialProperty.MP_BASE_COLOR)
        log("sand grain TEX+warm tint " + name)
    else:
        mel.connect_material_property(warm, "", unreal.MaterialProperty.MP_BASE_COLOR)
        log("sand grain solid warm (no tex) " + name)
    if rough:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, 160)
        ts.set_editor_property("texture", rough)
        try: ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        except Exception: pass
        mel.connect_material_expressions(mul, "", ts, "UVs")
        mel.connect_material_property(ts, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    else:
        r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 160)
        r.set_editor_property("r", 0.92)
        mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    # Zero emissive — grain must come from lit albedo
    em = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 280)
    em.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path, True)
    return mat

def make_lit(name, rgb, rough=0.9):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 100)
    r.set_editor_property("r", float(rough))
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 200)
    e.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path, True)
    return mat

def mesh_y_range(a):
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    try:
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            sm = comp.get_editor_property("static_mesh")
            if sm:
                box = sm.get_bounding_box()
                dy = abs((box.max - box.min).y) * sc.y
                dx = abs((box.max - box.min).x) * sc.x
                return loc.y - dy * 0.5, loc.y + dy * 0.5, dx, dy
    except Exception:
        pass
    # plane fallback
    return loc.y - 50.0 * sc.y, loc.y + 50.0 * sc.y, 100.0 * sc.x, 100.0 * sc.y

def tune_dir_light(a):
    for c in a.get_components_by_class(unreal.DirectionalLightComponent):
        try: c.set_editor_property("intensity", 1.2)
        except Exception: pass
        try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.94, 0.80, 1.0))
        except Exception: pass
        try: c.set_editor_property("indirect_lighting_intensity", 1.2)
        except Exception: pass
        try: c.set_editor_property("volumetric_scattering_intensity", 0.8)
        except Exception: pass
        try: c.set_editor_property("shadow_amount", 0.55)
        except Exception: pass
        try: c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        except Exception: pass
    a.set_actor_rotation(unreal.Rotator(pitch=-45.0, yaw=25.0, roll=0.0), False)
    log("DirectionalLight warm intensity~1.2 pitch=-45")

def tune_sky_light(a):
    unhide(a)
    for c in a.get_components_by_class(unreal.SkyLightComponent):
        try: c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        except Exception: pass
        try: c.set_editor_property("real_time_capture", True)
        except Exception: pass
        try: c.set_editor_property("intensity", 4.0)
        except Exception: pass
        try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.96, 0.88, 1.0))
        except Exception: pass
        try: c.set_editor_property("lower_hemisphere_is_black", False)
        except Exception: pass
        try: c.recapture_sky()
        except Exception: pass
    log("SkyLight movable realtime intensity~4 warm tint")

def tune_fog(a):
    unhide(a)
    for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
        try: c.set_editor_property("fog_density", 0.055)
        except Exception: pass
        try: c.set_editor_property("fog_height_falloff", 0.2)
        except Exception: pass
        # Warm grey — mild, must NOT blue-wash sand
        try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.72, 0.68, 0.60, 1.0))
        except Exception: pass
        try: c.set_editor_property("fog_max_opacity", 0.65)
        except Exception: pass
        try: c.set_editor_property("start_distance", 800.0)
        except Exception: pass
        try: c.set_editor_property("volumetric_fog", False)
        except Exception: pass
    log("ExponentialHeightFog density~0.055 warm-grey inscatter")

def tune_pp(a):
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
            s.set_editor_property("auto_exposure_bias", 0.35)
        except Exception: pass
        # Mild warm gain — keep enough blue so water reads
        try:
            s.set_editor_property("override_color_gain", True)
            s.set_editor_property("color_gain", unreal.Vector4(1.12, 1.02, 0.92, 1.0))
        except Exception: pass
        try:
            s.set_editor_property("override_color_gamma", True)
            s.set_editor_property("color_gamma", unreal.Vector4(1.02, 1.0, 0.98, 1.0))
        except Exception: pass
        try:
            s.set_editor_property("override_bloom_intensity", True)
            s.set_editor_property("bloom_intensity", 0.15)
        except Exception: pass
        try: a.set_editor_property("settings", s)
        except Exception: pass
        log("PP mild warm temp4800 gain R1.12 B0.92 (water-safe)")
    except Exception as e:
        log("PP warn " + str(e))

# --- main ---
try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e:
    log("load " + str(e))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

sand = make_sand_warm_grain("MI_Tideborn_SandWarm", 55.0)
make_sand_warm_grain("M_Tideborn_Sand", 55.0)
# Darker blue water (not cyan) for contrast vs sand
water = make_lit("M_Tideborn_WaterOpaque", (0.04, 0.10, 0.26), rough=0.25)
make_lit("M_Tideborn_WaterSimple", (0.05, 0.12, 0.28), rough=0.3)
rock = make_lit("M_Tideborn_RockShore", (0.48, 0.42, 0.36), rough=0.85)
wood = make_lit("MI_Tideborn_WoodMuted", (0.38, 0.24, 0.13))
creature = make_lit("MI_Tideborn_CreatureMuted", (0.42, 0.34, 0.20))
gate = make_lit("M_Tideborn_GateSolid", (0.34, 0.22, 0.12))
ground = make_lit("M_Tideborn_Ground", (0.32, 0.38, 0.20))
bark = make_lit("M_Tideborn_Bark", (0.30, 0.17, 0.09))

# Purge prior WLB (will respawn)
for a in list(actors()):
    lab = label(a)
    if lab.startswith("TidebornEnv_WLB_") or lab.startswith("TidebornEnv_WaterlineBoulder_"):
        try:
            eas.destroy_actor(a)
            log("x old " + lab)
        except Exception:
            pass

has_sky_atmo = False
has_sky_light = False
has_fog = False
has_dir = False
has_pp = False

for a in actors():
    cn = cname(a)
    lab = label(a)
    if "SkyAtmosphere" in cn:
        has_sky_atmo = True
        unhide(a)
        log("SkyAtmosphere UNHID/present")
    if "VolumetricCloud" in cn:
        unhide(a)
        log("VolumetricCloud UNHID")
    if "SkyLight" in cn:
        has_sky_light = True
        tune_sky_light(a)
    if "ExponentialHeightFog" in cn:
        has_fog = True
        tune_fog(a)
    if "DirectionalLight" in cn:
        has_dir = True
        tune_dir_light(a)
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        has_pp = True
        tune_pp(a)

if not has_sky_atmo:
    try:
        atmo = eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))
        if atmo:
            try: atmo.set_actor_label("TidebornEnv_SkyAtmosphere")
            except Exception: pass
            unhide(atmo)
            has_sky_atmo = True
            log("SPAWNED SkyAtmosphere")
        else:
            log("FAILED spawn SkyAtmosphere")
    except Exception as e:
        log("spawn SkyAtmosphere fail " + str(e))

if not has_sky_light:
    try:
        sl = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(1000, 1000, 500))
        if sl:
            try: sl.set_actor_label("TidebornEnv_SkyLight")
            except Exception: pass
            tune_sky_light(sl)
            has_sky_light = True
            log("SPAWNED SkyLight")
        else:
            log("FAILED spawn SkyLight")
    except Exception as e:
        log("spawn SkyLight fail " + str(e))

if not has_fog:
    try:
        fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(1000, 1000, 200))
        if fog:
            try: fog.set_actor_label("TidebornEnv_HeightFog")
            except Exception: pass
            tune_fog(fog)
            has_fog = True
            log("SPAWNED ExponentialHeightFog")
        else:
            log("FAILED spawn fog")
    except Exception as e:
        log("spawn fog fail " + str(e))

if not has_dir:
    try:
        dl = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(1000, 1000, 800))
        if dl:
            try: dl.set_actor_label("TidebornEnv_DirectionalLight")
            except Exception: pass
            tune_dir_light(dl)
            has_dir = True
            log("SPAWNED DirectionalLight")
    except Exception as e:
        log("spawn DirLight fail " + str(e))

# Re-enable atmosphere console (session)
for cmd in (
    "r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
    "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "ShowFlag.Cloud 1",
):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

# Apply mats + hard floor lock + water fix
sand_base = None
sand_ramp = None
ocean = None
shallows = None
boulder_mesh = None

for a in actors():
    lab = label(a)
    cn = cname(a)
    if lab == "TidebornEnv_SandBase":
        sand_base = a
        # HARD LOCK
        a.set_actor_location(unreal.Vector(1000.0, 1500.0, 106.0), False, True)
        a.set_actor_scale3d(unreal.Vector(45.0, 18.0, 1.0))
        force_apply(a, sand)
    elif lab == "TidebornEnv_SandRamp" or ("SandRamp" in lab):
        sand_ramp = a
    elif lab == "TidebornEnv_Ocean":
        ocean = a
        a.set_actor_location(unreal.Vector(1000.0, -900.0, 99.0), False, True)
        a.set_actor_scale3d(unreal.Vector(70.0, 18.0, 1.0))
        force_apply(a, water)
    elif lab == "TidebornEnv_Shallows":
        shallows = a
        # Keep below sand; extend toward waterline so Verify FOV can see it past Y=600
        a.set_actor_location(unreal.Vector(1000.0, 350.0, 100.0), False, True)
        a.set_actor_scale3d(unreal.Vector(55.0, 8.0, 1.0))  # Y[ -50 .. 750 ] approx plane
        # clamp scY <= 18 hard floor
        force_apply(a, water)
    elif lab == "TidebornEnv_Ground":
        force_apply(a, ground)
    elif "Gate" in lab:
        force_apply(a, gate)
    elif "Kelp" in lab or "Burr" in lab or "Hound" in lab:
        force_apply(a, creature)
    elif "Gather" in lab:
        force_apply(a, rock if "Stone" in lab else wood)
    elif "Boulder" in lab or "Waterline" in lab:
        force_apply(a, rock)
    elif "Trunk" in lab:
        force_apply(a, bark)

    if lab.startswith("TidebornEnv_Boulder") and "WLB" not in lab and "Waterline" not in lab:
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            try:
                sm = comp.get_editor_property("static_mesh")
                if sm: boulder_mesh = sm
            except Exception: pass

# Shrink SandRamp so it does NOT cover ocean (mesh ~4000x1200 at scale 1)
if sand_ramp:
    # Target Y cover ~[520..650] only
    sand_ramp.set_actor_location(unreal.Vector(1000.0, 580.0, 105.0), False, True)
    sand_ramp.set_actor_scale3d(unreal.Vector(0.18, 0.11, 0.7))
    force_apply(sand_ramp, sand)
    y0, y1, dx, dy = mesh_y_range(sand_ramp)
    log("SandRamp cover Y[%.0f..%.0f] meshXY=(%.0f,%.0f) loc=(1000,580,105) sc=(0.18,0.11,0.7)" % (y0, y1, dx, dy))
    if y1 > 700 or y0 < 200:
        # Still too big — shrink further
        sand_ramp.set_actor_scale3d(unreal.Vector(0.12, 0.08, 0.6))
        y0, y1, dx, dy = mesh_y_range(sand_ramp)
        log("SandRamp RESHRINK Y[%.0f..%.0f] meshXY=(%.0f,%.0f)" % (y0, y1, dx, dy))
else:
    log("WARN no SandRamp actor")

# WLB boulders Y 550-700, X outside corridor 900-1100
if boulder_mesh:
    for i, (x, y, z, s, yaw) in enumerate([
        (780, 560, 101, 2.0, -25),
        (820, 620, 100, 1.8, 35),
        (760, 680, 100, 2.2, 10),
        (1220, 555, 101, 2.1, 20),
        (1260, 640, 100, 1.9, -40),
        (1300, 700, 100, 2.0, -15),
        (740, 700, 100, 1.6, 50),
        (1280, 590, 100, 1.7, -60),
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
            log("WLB %02d @ (%.0f,%.0f)" % (i, x, y))
else:
    log("WARN no boulder mesh for WLB")

# Dump CONFIRM
log("=== DUMP CONFIRM ===")
log("SkyAtmosphere present=%s" % has_sky_atmo)
log("SkyLight present=%s" % has_sky_light)
log("ExponentialHeightFog present=%s" % has_fog)
log("DirectionalLight present=%s" % has_dir)

# Re-scan for sky actors after spawn
for a in actors():
    cn = cname(a)
    lab = label(a)
    if "SkyAtmosphere" in cn or "SkyLight" in cn or "ExponentialHeightFog" in cn or "DirectionalLight" in cn:
        loc = a.get_actor_location()
        hid = False
        try: hid = a.is_hidden_ed() if hasattr(a, "is_hidden_ed") else False
        except Exception: pass
        try:
            hg = a.get_editor_property("hidden")
        except Exception:
            hg = "?"
        log("SKYACTOR %s label=%s loc=(%.0f,%.0f,%.0f) hidden=%s" % (cn, lab, loc.x, loc.y, loc.z, hg))

for a in actors():
    lab = label(a)
    if lab in (
        "TidebornEnv_SandBase", "TidebornEnv_SandRamp", "TidebornEnv_Shallows",
        "TidebornEnv_Ocean", "TidebornEnv_Ground", "Tideborn_P2_BurrHound",
        "Tideborn_P2_ShoreGate",
    ) or lab.startswith("TidebornEnv_WLB_"):
        loc = a.get_actor_location()
        sc = a.get_actor_scale3d()
        y0, y1, dx, dy = mesh_y_range(a)
        mats = []
        for comp in a.get_components_by_class(unreal.PrimitiveComponent):
            for i in range(2):
                try:
                    m = comp.get_material(i)
                    if m: mats.append(m.get_name())
                except Exception: break
        log("CONFIRM %s Z=%.0f loc=(%.0f,%.0f) sc=(%.2f,%.2f,%.2f) Y[%.0f..%.0f] mats=%s" % (
            lab, loc.z, loc.x, loc.y, sc.x, sc.y, sc.z, y0, y1, ",".join(mats[:3]) or "-"))

# Hard floor asserts
ok = True
if sand_base:
    loc = sand_base.get_actor_location(); sc = sand_base.get_actor_scale3d()
    lock_ok = abs(loc.z - 106) < 0.5 and abs(sc.x - 45) < 0.1 and abs(sc.y - 18) < 0.1
    log("LOCK SandBase OK=%s Z=%.0f sc=(%.1f,%.1f)" % (lock_ok, loc.z, sc.x, sc.y))
    if not lock_ok: ok = False
for a, name in ((ocean, "Ocean"), (shallows, "Shallows")):
    if not a: continue
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    wok = loc.z < 106 and sc.y <= 18.01
    log("LOCK water %s OK=%s Z=%.0f scY=%.1f" % (name, wok, loc.z, sc.y))
    if not wok: ok = False

if sand_ramp:
    y0, y1, dx, dy = mesh_y_range(sand_ramp)
    covers_all = y1 > 900 or (y0 < 0 and y1 > 700)
    log("SandRamp MUST NOT cover ocean: Y[%.0f..%.0f] covers_all_water=%s" % (y0, y1, covers_all))
    if covers_all:
        log("FAIL SandRamp still covering water")
        ok = False

try:
    ok_save = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("save_current_level -> %s" % ok_save)
except Exception as e:
    log("save level " + str(e))
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("save_dirty -> True")
except Exception as e:
    log("save dirty " + str(e))

log("PASS_ASSERTS=%s" % ok)
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
