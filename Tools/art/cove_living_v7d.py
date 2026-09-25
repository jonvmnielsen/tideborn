# -*- coding: utf-8 -*-
"""v7d: water less specular (kill sky-lavender), sand/rock warmer albedos, water further inland, open Verify."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v7d_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V7d] "+t); lines.append(t)
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
    # NO emissive (parent lock)
    e=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-400,260)
    e.set_editor_property("constant", unreal.LinearColor(0,0,0,1))
    mel.connect_material_property(e,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    # Specular low on water via roughness; also lower specular if property exists
    mel.recompile_material(mat); unreal.EditorAssetLibrary.save_asset(path,True)
    log("mat %s rgb=%s rough=%.2f"%(name,rgb,rough)); return mat
def apply(a,mat):
    if not a or not mat: return
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(12):
            try: comp.set_material(i,mat)
            except: break
        try: comp.set_editor_property("override_materials", [mat]*8)
        except: pass
try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load "+str(e))
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Extreme warm sand (orange-beige), brown rocks, deep blue water with HIGH roughness so albedo reads
rock=make_lit("M_Tideborn_RockShore",(0.36,0.26,0.18),0.92)
make_lit("MI_Tideborn_RockDark",(0.36,0.26,0.18),0.92)
sand=make_lit("MI_Tideborn_SandWarm",(0.72,0.48,0.28),0.98)
make_lit("M_Tideborn_Sand",(0.72,0.48,0.28),0.98)
wet=make_lit("MI_Tideborn_SandWet",(0.12,0.08,0.05),0.45)
# rough 0.55 so peach sky doesn't mirror as lavender
water=make_lit("M_Tideborn_WaterOpaque",(0.04,0.14,0.38),0.55)

side=0
for a in list(eas.get_all_level_actors()):
    lab=label(a); loc=a.get_actor_location(); cn=cname(a)
    # Flatten/side any boulder whose mesh likely intrudes X mid from scale
    if ("Boulder" in lab) or lab.startswith("TidebornEnv_WLB_"):
        sc=a.get_actor_scale3d()
        # approx half-extent; if overlaps X[700,1300] in verify/mouth Y
        half = 80.0 * max(sc.x, sc.y)
        x0,x1 = loc.x-half, loc.x+half
        if x0 < 1300 and x1 > 700 and 250 <= loc.y <= 1550:
            nx=380.0 if (side%2==0) else 1620.0
            a.set_actor_location(unreal.Vector(nx,loc.y,loc.z),False,True)
            # shrink tall mouth rocks
            if sc.x >= 2.4:
                a.set_actor_scale3d(unreal.Vector(sc.x*0.7, sc.y*0.7, sc.z*0.55))
                log("SHRINK %s"%lab)
            apply(a,rock)
            log("MOVE %s (%.0f,%.0f)->(%.0f,%.0f)"%(lab,loc.x,loc.y,nx,loc.y)); side+=1
        else:
            apply(a,rock)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1)); apply(a,sand)
        log("LOCK SandBase")
    elif lab.startswith("TidebornEnv_WetSand_"):
        a.set_actor_location(unreal.Vector(1000,650,105.5),False,True)
        a.set_actor_scale3d(unreal.Vector(50,2.5,1)); apply(a,wet)
        log("KEEP WetSand")
    elif "SandRamp" in lab:
        apply(a,wet)
    elif lab=="TidebornEnv_Shallows":
        # Push water further inland so Verify sees substantial band: Y half=700 -> [0..1400]
        a.set_actor_location(unreal.Vector(1000,700,100),False,True)
        a.set_actor_scale3d(unreal.Vector(70,14,1)); apply(a,water)
        log("Shallows inland locY=700 scY=14 Y[0..1400]")
    elif lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000,-600,99),False,True)
        a.set_actor_scale3d(unreal.Vector(90,18,1)); apply(a,water)
        log("Ocean Z=99")
    if "SkyLight" in cn:
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("real_time_capture", True)
            except: pass
            try: c.set_editor_property("source_type", 0)
            except: pass
            try: c.set_editor_property("cubemap", None)
            except: pass
            try: c.set_editor_property("intensity", 0.55)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0,0.85,0.65,1.0))
            except: pass
            try: c.set_editor_property("lower_hemisphere_color", unreal.LinearColor(0.75,0.50,0.28,1.0))
            except: pass
            try: c.recapture_sky()
            except: pass
        log("SkyLight 0.55 warm")
    if "DirectionalLight" in cn:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("use_temperature", False)
            except: pass
            try: c.set_editor_property("intensity", 3.2)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0,0.78,0.52,1.0))
            except: pass
            try: c.set_editor_property("indirect_lighting_intensity", 0.9)
            except: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-42,yaw=-90,roll=0),False)
        log("DirLight 3.2 warm pitch=-42")
    if "ExponentialHeightFog" in cn:
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.015)
            except: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.85,0.68,0.45,1.0))
            except: pass
    if "PostProcess" in cn:
        try:
            s=a.get_editor_property("settings")
            s.set_editor_property("override_white_temp", True)
            s.set_editor_property("white_temp", 3600.0)  # strongly warm in UE
            s.set_editor_property("override_auto_exposure_bias", True)
            s.set_editor_property("auto_exposure_bias", -0.15)
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.35,1.00,0.55,1.0))
            except: pass
            try:
                s.set_editor_property("override_color_saturation", True)
                s.set_editor_property("color_saturation", unreal.Vector4(1.10,1.05,0.90,1.0))
            except: pass
            try:
                s.set_editor_property("override_scene_color_tint", True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.20,0.95,0.70,1.0))
            except: pass
            a.set_editor_property("settings",s)
            log("PP white_temp=3600 gain R1.35 B0.55")
        except Exception as e: log("PP "+str(e))
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        try:
            a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False)
        except: pass

for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1","ShowFlag.Atmosphere 1","ShowFlag.Fog 1","r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except: pass
try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
