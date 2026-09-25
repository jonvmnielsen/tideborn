# -*- coding: utf-8 -*-
"""v7b: fix lavender (UE white_temp lower=warmer), brown rocks, clear Verify corridor."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v7b_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V7b] "+t); lines.append(t)
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except: return ""
def make_lit(name, rgb, rough=0.9):
    path=MAT+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,MAT,unreal.Material,unreal.MaterialFactoryNew())
    mel=unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except: pass
    c=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-400,0)
    c.set_editor_property("constant", unreal.LinearColor(rgb[0],rgb[1],rgb[2],1.0))
    mel.connect_material_property(c,"",unreal.MaterialProperty.MP_BASE_COLOR)
    r=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-400,100)
    r.set_editor_property("r",float(rough)); mel.connect_material_property(r,"",unreal.MaterialProperty.MP_ROUGHNESS)
    m=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-400,180)
    m.set_editor_property("r",0.0); mel.connect_material_property(m,"",unreal.MaterialProperty.MP_METALLIC)
    e=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-400,260)
    e.set_editor_property("constant", unreal.LinearColor(0,0,0,1))
    mel.connect_material_property(e,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat); unreal.EditorAssetLibrary.save_asset(path,True)
    log("mat %s %s"%(name,rgb)); return mat
def apply(a,mat):
    if not a or not mat: return
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(12):
            try: comp.set_material(i,mat)
            except: break
try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load "+str(e))
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Warmer sand (more orange), readable brown rocks, deep blue water, dark wet
rock=make_lit("M_Tideborn_RockShore",(0.28,0.20,0.14),0.95)
make_lit("MI_Tideborn_RockDark",(0.28,0.20,0.14),0.95)
sand=make_lit("MI_Tideborn_SandWarm",(0.62,0.44,0.26),0.97)
make_lit("M_Tideborn_Sand",(0.62,0.44,0.26),0.97)
wet=make_lit("MI_Tideborn_SandWet",(0.10,0.07,0.05),0.35)
water=make_lit("M_Tideborn_WaterOpaque",(0.05,0.15,0.35),0.08)

# Clear Verify corridor: rocks X[650,1350] Y[850,1550] block water from (1050,1600)
side=0
for a in list(eas.get_all_level_actors()):
    lab=label(a); loc=a.get_actor_location()
    if (("Boulder" in lab) or lab.startswith("TidebornEnv_WLB_")) and 650<=loc.x<=1350 and 850<=loc.y<=1550:
        nx=450.0 if (side%2==0) else 1550.0
        ny=loc.y
        a.set_actor_location(unreal.Vector(nx,ny,loc.z),False,True)
        apply(a,rock)
        log("MOVE verify-corridor %s (%.0f,%.0f)->(%.0f,%.0f)"%(lab,loc.x,loc.y,nx,ny)); side+=1
    elif (("Boulder" in lab) or lab.startswith("TidebornEnv_WLB_")) and 700<=loc.x<=1300 and 200<=loc.y<=900:
        nx=450.0 if (side%2==0) else 1550.0
        a.set_actor_location(unreal.Vector(nx,loc.y,loc.z),False,True)
        apply(a,rock)
        log("MOVE mouth2 %s ->X=%.0f"%(lab,nx)); side+=1
    elif lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1)); apply(a,sand)
        log("LOCK SandBase")
    elif lab=="TidebornEnv_WetSand_00" or lab.startswith("TidebornEnv_WetSand_"):
        a.set_actor_location(unreal.Vector(1000,650,105.5),False,True)
        a.set_actor_scale3d(unreal.Vector(50,2.5,1)); apply(a,wet)
        log("KEEP WetSand dark")
    elif lab=="TidebornEnv_SandRamp" or "SandRamp" in lab:
        apply(a,wet)
    elif lab=="TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000,350,100),False,True)
        a.set_actor_scale3d(unreal.Vector(60,12,1)); apply(a,water)
    elif lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000,-800,99),False,True)
        a.set_actor_scale3d(unreal.Vector(80,18,1)); apply(a,water)
    elif "Boulder" in lab or lab.startswith("TidebornEnv_WLB_"):
        apply(a,rock)
    cn=cname(a)
    if "SkyLight" in cn:
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("real_time_capture", True)
            except: pass
            try: c.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
            except:
                try: c.set_editor_property("source_type", 0)
                except: pass
            try: c.set_editor_property("cubemap", None)
            except: pass
            try: c.set_editor_property("intensity", 0.85)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0,0.88,0.70,1.0))
            except: pass
            try: c.set_editor_property("lower_hemisphere_is_black", False)
            except: pass
            try: c.set_editor_property("lower_hemisphere_color", unreal.LinearColor(0.70,0.48,0.28,1.0))
            except: pass
            try: c.recapture_sky()
            except: pass
        log("SkyLight 0.85 warm no-HDRI")
    if "DirectionalLight" in cn:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("use_temperature", False)
            except: pass
            try: c.set_editor_property("intensity", 2.8)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0,0.82,0.58,1.0))
            except: pass
            try: c.set_editor_property("indirect_lighting_intensity", 0.7)
            except: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-38,yaw=-90,roll=0),False)
        log("DirLight warm 2.8 no-temp pitch=-38")
    if "ExponentialHeightFog" in cn:
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.02)
            except: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.80,0.65,0.45,1.0))
            except: pass
    if "PostProcess" in cn:
        try:
            try: a.set_editor_property("unbound", True)
            except: pass
            s=a.get_editor_property("settings")
            # UE: LOWER white_temp = WARMER image. 5600 cooled the scene.
            s.set_editor_property("override_white_temp", True)
            s.set_editor_property("white_temp", 3900.0)
            try:
                s.set_editor_property("override_white_tint", True)
                s.set_editor_property("white_tint", -0.05)
            except: pass
            s.set_editor_property("override_auto_exposure_bias", True)
            s.set_editor_property("auto_exposure_bias", -0.20)
            try:
                s.set_editor_property("override_auto_exposure_method", True)
                s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            except: pass
            try:
                s.set_editor_property("override_color_saturation", True)
                s.set_editor_property("color_saturation", unreal.Vector4(1.08,1.05,0.95,1.0))
            except: pass
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.28,1.02,0.62,1.0))
            except: pass
            try:
                s.set_editor_property("override_color_gamma", True)
                s.set_editor_property("color_gamma", unreal.Vector4(1.04,1.00,0.92,1.0))
            except: pass
            try:
                s.set_editor_property("override_scene_color_tint", True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.12,0.95,0.75,1.0))
            except: pass
            try:
                s.set_editor_property("override_color_grading_intensity", True)
                s.set_editor_property("color_grading_intensity", 0.0)
            except: pass
            a.set_editor_property("settings",s)
            log("PP white_temp=3900 gain=(1.28,1.02,0.62) tint warm")
        except Exception as e:
            log("PP "+str(e))
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        try:
            a.set_actor_hidden_in_game(False)
            a.set_is_temporarily_hidden_in_editor(False)
        except: pass

for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1","ShowFlag.Atmosphere 1","ShowFlag.Fog 1","r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except: pass

try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
