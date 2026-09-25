# -*- coding: utf-8 -*-
"""v8c: restore warm look after SkyDome hide; keep atmosphere gradient; foam; sand grain."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v8c_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V8c] "+t); lines.append(t)
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
def hide(a):
    try:
        a.set_actor_hidden_in_game(True); a.set_is_temporarily_hidden_in_editor(True)
        root=a.root_component
        if root:
            try: root.set_visibility(False,True)
            except: pass
    except: pass
def unhide(a):
    try:
        a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False)
        root=a.root_component
        if root:
            try: root.set_visibility(True,True)
            except: pass
    except: pass
def force_apply(a,mat):
    if not a or not mat: return
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(16):
            try: comp.set_material(i,mat)
            except: break

def del_mat(name):
    path=MAT+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)

def make_sky_grad(name):
    """Soft warm dusk gradient for SkyDome (not flat peach slab)."""
    del_mat(name)
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,MAT,unreal.Material,unreal.MaterialFactoryNew())
    mel=unreal.MaterialEditingLibrary
    try:
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        mat.set_editor_property("two_sided", True)
    except: pass
    # UV.Y -> lerp zenith cool peach-blue to horizon warm peach
    uv=mel.create_material_expression(mat,unreal.MaterialExpressionTextureCoordinate,-600,0)
    # ComponentMask G (V)
    mask=mel.create_material_expression(mat,unreal.MaterialExpressionComponentMask,-450,0)
    try:
        mask.set_editor_property("r", False); mask.set_editor_property("g", True)
        mask.set_editor_property("b", False); mask.set_editor_property("a", False)
    except: pass
    mel.connect_material_expressions(uv,"",mask,"")
    top=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-450,-120)
    # soft dusty blue-peach zenith
    top.set_editor_property("constant", unreal.LinearColor(0.55,0.48,0.62,1.0))
    bot=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-450,120)
    # warm horizon peach/amber
    bot.set_editor_property("constant", unreal.LinearColor(0.95,0.72,0.48,1.0))
    lerp=mel.create_material_expression(mat,unreal.MaterialExpressionLinearInterpolate,-200,0)
    mel.connect_material_expressions(bot,"",lerp,"A")
    mel.connect_material_expressions(top,"",lerp,"B")
    mel.connect_material_expressions(mask,"",lerp,"Alpha")
    mel.connect_material_property(lerp,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    # also base color
    mel.connect_material_property(lerp,"",unreal.MaterialProperty.MP_BASE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT+"/"+name, True)
    log("sky_grad "+name); return mat

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load "+str(e))

sky_mat = make_sky_grad("M_Tideborn_SkyDomeGrad")
sand = load(MAT+"/MI_Tideborn_SandWarm")
foam = load(MAT+"/MI_Tideborn_Foam")
water = load(MAT+"/M_Tideborn_WaterOpaque")
wet_dark = load(MAT+"/MI_Tideborn_SandWet")
wet_mid = load(MAT+"/MI_Tideborn_SandWetMid")

for a in list(actors()):
    lab=label(a); cn=cname(a)
    if lab=="TidebornEnv_SkyDome":
        # Re-enable but with soft gradient mat (not flat peach)
        unhide(a)
        if sky_mat: force_apply(a, sky_mat)
        log("SkyDome GRADIENT mat applied")
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        unhide(a)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1))
        if sand: force_apply(a,sand); log("LOCK SandBase")
    elif lab=="TidebornEnv_FoamStrip":
        a.set_actor_location(unreal.Vector(1000,545,103.8),False,True)
        a.set_actor_scale3d(unreal.Vector(48,0.55,1))
        if foam: force_apply(a,foam); unhide(a)
    elif lab=="TidebornEnv_BeachSlope":
        # Slight pitch so height change reads in Waterline
        a.set_actor_location(unreal.Vector(1000,600,108),False,True)
        a.set_actor_scale3d(unreal.Vector(1.0,1.0,1.5))
        try: a.set_actor_rotation(unreal.Rotator(pitch=4.0,yaw=0,roll=0),False)
        except: pass
        if sand: force_apply(a,sand); unhide(a); log("BeachSlope pitched+raised")
    elif lab=="TidebornEnv_Ocean":
        if water: force_apply(a,water)
    elif lab=="TidebornEnv_Shallows":
        if water: force_apply(a,water)
    elif lab=="TidebornEnv_WetSand_00":
        if wet_dark: force_apply(a,wet_dark)
    elif lab=="TidebornEnv_WetSand_01":
        if wet_mid: force_apply(a,wet_mid)
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("real_time_capture", True)
            except: pass
            try: c.set_editor_property("cubemap", None)
            except: pass
            try: c.set_editor_property("intensity", 0.45)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0,0.82,0.58,1.0))
            except: pass
            try: c.set_editor_property("lower_hemisphere_color", unreal.LinearColor(0.60,0.40,0.22,1.0))
            except: pass
            try: c.recapture_sky()
            except: pass
        log("SkyLight warm 0.45")
    if "DirectionalLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 3.5)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0,0.78,0.50,1.0))
            except: pass
            try: c.set_editor_property("atmosphere_sun_light", True)
            except: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-32,yaw=-90,roll=0),False)
        log("DirLight warm 3.5")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.02)
            except: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.90,0.70,0.48,1.0))
            except: pass
            try: c.set_editor_property("directional_inscattering_color", unreal.LinearColor(1.0,0.75,0.45,1.0))
            except: pass
        log("Fog warm")
    if "PostProcess" in cn or lab=="TidebornEnv_PostProcess":
        unhide(a)
        try:
            try: a.set_editor_property("unbound", True)
            except: pass
            s=a.get_editor_property("settings")
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 3600.0)
            except: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.40,0.95,0.52,1.0))
            except: pass
            try:
                s.set_editor_property("override_scene_color_tint", True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.20,0.92,0.70,1.0))
            except: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", -0.1)
            except: pass
            try: a.set_editor_property("settings",s)
            except: pass
            log("PP temp=3600 warm restore")
        except Exception as e: log("PP "+str(e))

for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1",
            "ShowFlag.Atmosphere 1","ShowFlag.Fog 1","ShowFlag.Cloud 1",
            "r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except: pass

try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
