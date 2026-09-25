# -*- coding: utf-8 -*-
"""v9c: kill remaining sand-over-shallows, readable shore lip, soft sky, multi foam."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v9c_result.txt"
DUMP = ROOT / "Tools" / "art" / "cove_dump_v9c.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines = []

def log(m):
    t = str(m); unreal.log("[V9c] " + t); lines.append(t)
def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except Exception: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except Exception: return ""
def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if p and unreal.EditorAssetLibrary.does_asset_exist(p) else None
def unhide(a):
    try:
        a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False)
        root = a.root_component
        if root:
            try: root.set_visibility(True, True)
            except Exception: pass
    except Exception: pass
def hide(a):
    try:
        a.set_actor_hidden_in_game(True); a.set_is_temporarily_hidden_in_editor(True)
        root = a.root_component
        if root:
            try: root.set_visibility(False, True)
            except Exception: pass
    except Exception: pass
def force_apply(a, mat):
    if not a or not mat: return
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(16):
            try: comp.set_material(i, mat)
            except Exception: break

def del_mat(name):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)

def make_sky_grad(name):
    del_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try:
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        mat.set_editor_property("two_sided", True)
    except Exception: pass
    # Use CameraVector for reliable view gradient
    cam = mel.create_material_expression(mat, unreal.MaterialExpressionCameraVectorWS, -700, 0)
    mask = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -520, 0)
    try:
        mask.set_editor_property("r", False); mask.set_editor_property("g", False)
        mask.set_editor_property("b", True); mask.set_editor_property("a", False)
    except Exception: pass
    mel.connect_material_expressions(cam, "", mask, "")
    # CameraVector.Z: look up positive. Remap: saturate((z+0.15)*1.2)
    add = mel.create_material_expression(mat, unreal.MaterialExpressionAdd, -360, 0)
    off = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -520, 80)
    off.set_editor_property("r", 0.20)
    mel.connect_material_expressions(mask, "", add, "A")
    mel.connect_material_expressions(off, "", add, "B")
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -220, 0)
    sc = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -360, 80)
    sc.set_editor_property("r", 1.35)
    mel.connect_material_expressions(add, "", mul, "A")
    mel.connect_material_expressions(sc, "", mul, "B")
    sat = mel.create_material_expression(mat, unreal.MaterialExpressionSaturate, -80, 0)
    mel.connect_material_expressions(mul, "", sat, "")
    bot = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -220, 160)
    bot.set_editor_property("constant", unreal.LinearColor(1.10, 0.72, 0.42, 1.0))  # warm horizon
    top = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -220, -140)
    top.set_editor_property("constant", unreal.LinearColor(0.35, 0.42, 0.68, 1.0))  # clear soft blue zenith
    lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, 80, 0)
    mel.connect_material_expressions(bot, "", lerp, "A")
    mel.connect_material_expressions(top, "", lerp, "B")
    mel.connect_material_expressions(sat, "", lerp, "Alpha")
    em = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, 220, 0)
    boost = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, 220, 80)
    boost.set_editor_property("r", 1.35)
    mel.connect_material_expressions(lerp, "", em, "A")
    mel.connect_material_expressions(boost, "", em, "B")
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("sky_grad " + name); return mat

def make_lit(name, rgb, rough=0.9, emissive=None):
    del_mat(name)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception: pass
    c = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 120)
    r.set_editor_property("r", float(rough))
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)
    m.set_editor_property("r", 0.0)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 280)
    if emissive:
        e.set_editor_property("constant", unreal.LinearColor(emissive[0], emissive[1], emissive[2], 1.0))
    else:
        e.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT + "/" + name, True)
    log("mat %s %s" % (name, rgb)); return mat

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load " + str(e))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

sand = load(MAT + "/MI_Tideborn_SandWarm")
wet_dark = load(MAT + "/MI_Tideborn_SandWet")
wet_mid = load(MAT + "/MI_Tideborn_SandWetMid")
water = load(MAT + "/M_Tideborn_WaterOpaque")
foam = make_lit("MI_Tideborn_Foam", (0.96, 0.94, 0.86), 0.55, emissive=(0.28, 0.25, 0.18))
sky_mat = make_sky_grad("M_Tideborn_SkyDomeGrad")
plane = load("/Engine/BasicShapes/Plane")

# Destroy oversized BeachSlope + old foam/shore that bleed into water
for a in list(actors()):
    lab = label(a)
    if lab in ("TidebornEnv_BeachSlope", "TidebornEnv_ShoreEdge", "TidebornEnv_ShoreLip"):
        try: eas.destroy_actor(a); log("x " + lab)
        except Exception as e: log("xfail " + str(e))
    if lab.startswith("TidebornEnv_FoamSeg_"):
        try: eas.destroy_actor(a); log("x " + lab)
        except Exception: pass

# LOCK core planes — ensure NO sand over open water (Y < 580 at Z>=99)
for a in actors():
    lab = label(a); cn = cname(a)
    if lab == "TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000, 1500, 106), False, True)
        a.set_actor_scale3d(unreal.Vector(45, 18, 1))
        if sand: force_apply(a, sand); unhide(a)
        log("LOCK SandBase")
    elif lab == "TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000, -900, 99), False, True)
        a.set_actor_scale3d(unreal.Vector(85, 16, 1))
        if water: force_apply(a, water); unhide(a)
        log("Ocean Y=-900")
    elif lab == "TidebornEnv_Shallows":
        # Pull shallows seaward so shore lip isn't buried under blue+sand stack
        a.set_actor_location(unreal.Vector(1000, 200, 100), False, True)
        a.set_actor_scale3d(unreal.Vector(72, 8.5, 1))  # Y[-225..625]
        if water: force_apply(a, water); unhide(a)
        log("Shallows Y=200 scY=8.5 -> ~[-225..625]")
    elif lab == "TidebornEnv_WetSand_00":
        a.set_actor_location(unreal.Vector(1000, 640, 105.3), False, True)
        a.set_actor_scale3d(unreal.Vector(38, 2.0, 1))
        if wet_dark: force_apply(a, wet_dark); unhide(a)
    elif lab == "TidebornEnv_WetSand_01":
        a.set_actor_location(unreal.Vector(1000, 710, 105.7), False, True)
        a.set_actor_scale3d(unreal.Vector(36, 1.8, 1))
        if wet_mid: force_apply(a, wet_mid); unhide(a)
    elif "SandRamp" in lab:
        loc = a.get_actor_location()
        if loc.y < 600:
            a.set_actor_location(unreal.Vector(loc.x, 660, 105.4), False, True)
        if wet_mid: force_apply(a, wet_mid)
    elif lab.startswith("TidebornEnv_WetJag_"):
        loc = a.get_actor_location()
        if loc.y < 600:
            a.set_actor_location(unreal.Vector(loc.x, max(610.0, loc.y), loc.z), False, True)

# Short readable shore lip: pitched sand plane at waterline (NOT spanning ocean)
if plane and sand:
    # Engine plane 100uu; scY=2.5 -> halfY=125; center Y=680 -> Y[555..805] — tight shore
    # Pitch so +Y (land) rises: Rotator pitch positive tilts
    lip = eas.spawn_actor_from_object(
        plane, unreal.Vector(1000.0, 680.0, 103.0),
        unreal.Rotator(pitch=12.0, yaw=0.0, roll=0.0))
    if lip:
        lip.set_actor_label("TidebornEnv_ShoreLip")
        lip.set_actor_scale3d(unreal.Vector(36.0, 2.8, 1.0))
        force_apply(lip, sand); unhide(lip)
        log("SPAWN ShoreLip pitched 12deg Y=680 scY=2.8")
    # Second steeper short lip for Slope cam readability
    lip2 = eas.spawn_actor_from_object(
        plane, unreal.Vector(720.0, 660.0, 102.0),
        unreal.Rotator(pitch=18.0, yaw=5.0, roll=0.0))
    if lip2:
        lip2.set_actor_label("TidebornEnv_ShoreLip2")
        lip2.set_actor_scale3d(unreal.Vector(10.0, 2.2, 1.0))
        force_apply(lip2, sand); unhide(lip2)
        log("SPAWN ShoreLip2 for Slope cam")

# Rebuild thicker staggered foam (scY 0.9-1.2), cream, Z above water
if plane and foam:
    specs = [
        (700.0, 545.0, 11.0, 1.1, -4.0),
        (860.0, 558.0, 12.0, 1.2, 2.0),
        (1020.0, 540.0, 13.0, 1.0, -2.0),
        (1180.0, 552.0, 11.5, 1.15, 3.0),
        (1340.0, 548.0, 10.0, 0.95, -3.0),
    ]
    for i, (x, y, scx, scy, yaw) in enumerate(specs):
        af = eas.spawn_actor_from_object(
            plane, unreal.Vector(x, y, 104.5),
            unreal.Rotator(0, yaw, 0))
        if af:
            af.set_actor_label("TidebornEnv_FoamSeg_%02d" % i)
            af.set_actor_scale3d(unreal.Vector(scx, scy, 1.0))
            force_apply(af, foam); unhide(af)
    log("SPAWN FoamSeg x5 thick cream")

# Sky / lighting — allow blue zenith while keeping sand warm via albedo+mild PP
for a in actors():
    lab = label(a); cn = cname(a)
    if lab == "TidebornEnv_SkyDome" or "SkyDome" in lab:
        unhide(a)
        if sky_mat: force_apply(a, sky_mat)
        try:
            a.set_actor_scale3d(unreal.Vector(500, 500, 500))
            a.set_actor_location(unreal.Vector(1000, 800, 0), False, True)
        except Exception: pass
        log("SkyDome cam-vector gradient")
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        unhide(a); log("SHOW " + cn)
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("real_time_capture", True)
            except Exception: pass
            try: c.set_editor_property("cubemap", None)
            except Exception: pass
            try: c.set_editor_property("intensity", 0.25)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.90, 0.75, 1.0))
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_color", unreal.LinearColor(0.50, 0.35, 0.20, 1.0))
            except Exception: pass
            try: c.recapture_sky()
            except Exception: pass
        log("SkyLight 0.25")
    if "DirectionalLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 3.4)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.82, 0.58, 1.0))
            except Exception: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-25, yaw=-35, roll=0), False)
        log("DirLight side for lip")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.045)
            except Exception: pass
            try: c.set_editor_property("fog_height_falloff", 0.18)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.78, 0.68, 0.58, 1.0))
            except Exception: pass
            try: c.set_editor_property("directional_inscattering_color", unreal.LinearColor(1.0, 0.75, 0.48, 1.0))
            except Exception: pass
        log("Fog 0.045 haze")
    if "PostProcess" in cn or lab == "TidebornEnv_PostProcess":
        unhide(a)
        try:
            try: a.set_editor_property("unbound", True)
            except Exception: pass
            s = a.get_editor_property("settings")
            # Milder warm — DO NOT crush blue sky to peach slab
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 3900.0)
            except Exception: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.18, 1.00, 0.82, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_scene_color_tint", True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.08, 0.96, 0.85, 1.0))
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", -0.1)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_method", True)
                s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP temp=3900 mild gain (sky blue kept)")
        except Exception as e:
            log("PP " + str(e))

for cmd in ("r.SkyAtmosphere 1", "r.VolumetricCloud 1", "r.Fog 1",
            "ShowFlag.Atmosphere 1", "ShowFlag.Fog 1", "ShowFlag.Cloud 1",
            "r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass

for a in actors():
    if "SkyLight" in cname(a):
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.recapture_sky()
            except Exception: pass

# Dump + warn
dump = []
KEYS = ("SandBase", "Ground", "WetSand", "Foam", "BeachSlope", "Shallows", "Ocean",
        "SandRamp", "ShoreEdge", "ShoreLip", "FoamSeg", "WetJag")
for a in actors():
    lab = label(a)
    if not any(k in lab for k in KEYS): continue
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    try:
        origin, extent = a.get_actor_bounds(False, False)
        y0, y1 = origin.y - extent.y, origin.y + extent.y
        z0, z1 = origin.z - extent.z, origin.z + extent.z
    except Exception:
        y0 = loc.y - 50 * abs(sc.y); y1 = loc.y + 50 * abs(sc.y)
        z0 = z1 = loc.z
    line = "%s loc=(%.0f,%.0f,%.1f) sc=(%.2f,%.2f,%.2f) Y=[%.0f..%.0f] Z=[%.1f..%.1f]" % (
        lab, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z, y0, y1, z0, z1)
    dump.append(line); log("DUMP " + line)
    if lab in ("TidebornEnv_Ocean", "TidebornEnv_Shallows"): continue
    if any(k in lab for k in ("Sand", "Slope", "Ramp", "Ground", "Wet", "Beach", "Shore", "Lip")):
        if y0 < 400 and z1 >= 98.5:
            log("WARN_SAND_IN_WATER " + line)

DUMP.write_text("\n".join(dump) + "\n", encoding="utf-8")
try: log("save %s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("DONE")
RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
