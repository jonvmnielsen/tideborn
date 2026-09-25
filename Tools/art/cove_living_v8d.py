# -*- coding: utf-8 -*-
"""v8d: WorldPos sky gradient on SkyDome; keep warm; foam nudge."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v8d_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V8d] "+t); lines.append(t)
def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except: return ""
def force_apply(a,mat):
    if not a or not mat: return
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(16):
            try: comp.set_material(i,mat)
            except: break
def unhide(a):
    try:
        a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False)
        root=a.root_component
        if root:
            try: root.set_visibility(True,True)
            except: pass
    except: pass

def make_sky_wp(name):
    path=MAT+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,MAT,unreal.Material,unreal.MaterialFactoryNew())
    mel=unreal.MaterialEditingLibrary
    try:
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        mat.set_editor_property("two_sided", True)
    except: pass
    # World Z -> 0..1 soft gradient (horizon warm peach -> higher cooler)
    wp=mel.create_material_expression(mat,unreal.MaterialExpressionWorldPosition,-700,0)
    # ComponentMask Z
    mask=mel.create_material_expression(mat,unreal.MaterialExpressionComponentMask,-520,0)
    try:
        mask.set_editor_property("r", False); mask.set_editor_property("g", False)
        mask.set_editor_property("b", True); mask.set_editor_property("a", False)
    except: pass
    mel.connect_material_expressions(wp,"",mask,"")
    # (Z - 0) / 80000  -> saturate
    div=mel.create_material_expression(mat,unreal.MaterialExpressionDivide,-350,0)
    sc=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-520,80)
    sc.set_editor_property("r", 60000.0)
    mel.connect_material_expressions(mask,"",div,"A")
    mel.connect_material_expressions(sc,"",div,"B")
    sat=mel.create_material_expression(mat,unreal.MaterialExpressionSaturate,-200,0)
    mel.connect_material_expressions(div,"",sat,"")
    bot=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-350,160)
    bot.set_editor_property("constant", unreal.LinearColor(1.0,0.78,0.52,1.0))  # warm horizon
    top=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-350,-120)
    top.set_editor_property("constant", unreal.LinearColor(0.72,0.62,0.78,1.0))  # soft dusk zenith
    lerp=mel.create_material_expression(mat,unreal.MaterialExpressionLinearInterpolate,-50,0)
    mel.connect_material_expressions(bot,"",lerp,"A")
    mel.connect_material_expressions(top,"",lerp,"B")
    mel.connect_material_expressions(sat,"",lerp,"Alpha")
    mel.connect_material_property(lerp,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(lerp,"",unreal.MaterialProperty.MP_BASE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path, True)
    log("sky_wp "+name); return mat

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log(str(e))

sky=make_sky_wp("M_Tideborn_SkyDomeGrad")
for a in actors():
    lab=label(a); cn=cname(a)
    if lab=="TidebornEnv_SkyDome":
        unhide(a); force_apply(a,sky); log("SkyDome WP-grad")
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn or "ExponentialHeightFog" in cn:
        unhide(a)
    if lab=="TidebornEnv_FoamStrip":
        a.set_actor_location(unreal.Vector(1000,555,104.0),False,True)
        a.set_actor_scale3d(unreal.Vector(50,0.7,1)); unhide(a); log("Foam thicker")
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1)); log("LOCK SandBase")
    if "PostProcess" in cn or lab=="TidebornEnv_PostProcess":
        try:
            s=a.get_editor_property("settings")
            s.set_editor_property("override_white_temp", True)
            s.set_editor_property("white_temp", 3700.0)
            s.set_editor_property("override_color_gain", True)
            s.set_editor_property("color_gain", unreal.Vector4(1.35,0.96,0.55,1.0))
            a.set_editor_property("settings",s)
            log("PP warm keep")
        except Exception as e: log("PP "+str(e))

for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1","ShowFlag.Atmosphere 1","ShowFlag.Fog 1"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except: pass
try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
