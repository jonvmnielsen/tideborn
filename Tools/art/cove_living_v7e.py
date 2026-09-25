# -*- coding: utf-8 -*-
"""v7e: crush cool skylight fill, orange sand albedo, rocks brown; SandBase LOCK kept."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v7e_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V7e] "+t); lines.append(t)
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
# Strong orange sand (low G), brown rocks, deep blue water
rock=make_lit("M_Tideborn_RockShore",(0.42,0.28,0.16),0.9)
make_lit("MI_Tideborn_RockDark",(0.42,0.28,0.16),0.9)
sand=make_lit("MI_Tideborn_SandWarm",(0.85,0.38,0.16),0.98)
make_lit("M_Tideborn_Sand",(0.85,0.38,0.16),0.98)
wet=make_lit("MI_Tideborn_SandWet",(0.14,0.08,0.04),0.4)
water=make_lit("M_Tideborn_WaterOpaque",(0.03,0.12,0.40),0.5)
for a in list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()):
    lab=label(a); cn=cname(a)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1)); apply(a,sand); log("LOCK SandBase")
    elif lab.startswith("TidebornEnv_WetSand_"):
        a.set_actor_location(unreal.Vector(1000,650,105.5),False,True)
        a.set_actor_scale3d(unreal.Vector(50,2.5,1)); apply(a,wet)
    elif "SandRamp" in lab: apply(a,wet)
    elif lab=="TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000,700,100),False,True)
        a.set_actor_scale3d(unreal.Vector(70,14,1)); apply(a,water)
    elif lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000,-600,99),False,True)
        a.set_actor_scale3d(unreal.Vector(90,18,1)); apply(a,water)
    elif "Boulder" in lab or lab.startswith("TidebornEnv_WLB_"):
        apply(a,rock)
    if "SkyLight" in cn:
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity", 0.15)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0,0.80,0.55,1.0))
            except: pass
            try: c.set_editor_property("real_time_capture", True)
            except: pass
            try: c.set_editor_property("cubemap", None)
            except: pass
            try: c.recapture_sky()
            except: pass
        log("SkyLight 0.15 (crush cool fill)")
    if "DirectionalLight" in cn:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("use_temperature", False)
            except: pass
            try: c.set_editor_property("intensity", 4.0)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0,0.75,0.45,1.0))
            except: pass
            try: c.set_editor_property("indirect_lighting_intensity", 1.0)
            except: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-40,yaw=-90,roll=0),False)
        log("DirLight 4.0 warm")
    if "PostProcess" in cn:
        try:
            s=a.get_editor_property("settings")
            s.set_editor_property("override_white_temp", True)
            s.set_editor_property("white_temp", 3400.0)
            s.set_editor_property("override_auto_exposure_bias", True)
            s.set_editor_property("auto_exposure_bias", -0.1)
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.45,0.92,0.48,1.0))
            except: pass
            try:
                s.set_editor_property("override_scene_color_tint", True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.25,0.90,0.60,1.0))
            except: pass
            a.set_editor_property("settings",s)
            log("PP temp=3400 gain R1.45 G0.92 B0.48")
        except Exception as e: log("PP "+str(e))
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        try: a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False)
        except: pass
try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
