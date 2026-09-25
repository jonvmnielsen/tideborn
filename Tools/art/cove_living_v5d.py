# -*- coding: utf-8 -*-
"""v5d: darker sand/wet, nudge water for overview. NO shot."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v5d_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V5d] "+t); lines.append(t)
def label(a):
    try: return a.get_actor_label() or ""
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
    r.set_editor_property("r",float(rough))
    mel.connect_material_property(r,"",unreal.MaterialProperty.MP_ROUGHNESS)
    m=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-400,180)
    m.set_editor_property("r",0.0)
    mel.connect_material_property(m,"",unreal.MaterialProperty.MP_METALLIC)
    e=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-400,260)
    e.set_editor_property("constant", unreal.LinearColor(0,0,0,1))
    mel.connect_material_property(e,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path,True)
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
rock=make_lit("M_Tideborn_RockShore",(0.09,0.08,0.07),0.96)
sand=make_lit("MI_Tideborn_SandWarm",(0.62,0.48,0.30),0.97)
wet=make_lit("MI_Tideborn_SandWet",(0.16,0.13,0.10),0.45)
water=make_lit("M_Tideborn_WaterOpaque",(0.08,0.26,0.40),0.1)
for a in eas.get_all_level_actors():
    lab=label(a)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1)); apply(a,sand)
    elif lab.startswith("TidebornEnv_WetSand_") or lab=="TidebornEnv_ShoreEdge" or "SandRamp" in lab:
        apply(a,wet)
    elif lab in ("TidebornEnv_Ocean","TidebornEnv_Shallows"):
        apply(a,water)
        if lab=="TidebornEnv_Shallows":
            a.set_actor_location(unreal.Vector(1000,450,100),False,True)
            a.set_actor_scale3d(unreal.Vector(60,11,1))
        if lab=="TidebornEnv_Ocean":
            a.set_actor_location(unreal.Vector(1000,-350,99),False,True)
            a.set_actor_scale3d(unreal.Vector(70,18,1))
    elif "Boulder" in lab or lab.startswith("TidebornEnv_WLB_"):
        apply(a,rock)
    cn=a.get_class().get_name() if a.get_class() else ""
    if "SkyLight" in cn:
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity",0.85)
            except: pass
    if "DirectionalLight" in cn:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity",1.5)
            except: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-32,yaw=-90,roll=0),False)
    if "PostProcess" in cn:
        try:
            s=a.get_editor_property("settings")
            s.set_editor_property("override_auto_exposure_bias",True)
            s.set_editor_property("auto_exposure_bias",0.0)
            s.set_editor_property("override_white_temp",True)
            s.set_editor_property("white_temp",4300.0)
            a.set_editor_property("settings",s)
        except: pass
try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
