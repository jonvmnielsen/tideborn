# -*- coding: utf-8 -*-
"""Feel pass: retile sand denser, softer light/fog, larger near-water band. Keep floor."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_feel_result.txt"
MAT="/Game/Tideborn/Art/Materials"; TEX="/Game/Tideborn/Art/Textures"
lines=[]
def log(m):
    t=str(m); unreal.log("[Feel] "+t); lines.append(t)
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
def find_tex(folder, keys):
    base=TEX+"/"+folder
    if not unreal.EditorAssetLibrary.does_directory_exist(base): return None
    for ap in unreal.EditorAssetLibrary.list_assets(base, recursive=False):
        name=ap.split(".")[-1].lower()
        for k in keys:
            if k.lower() in name: return ap
    return None
def apply(a, mat):
    if not mat: return
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break

def make_sand(tile=28.0):
    name="M_Tideborn_Sand"; path=MAT+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel=unreal.MaterialEditingLibrary
    bc=load(find_tex("Sand", ["Diffuse","Color"]))
    rough=load(find_tex("Sand", ["Rough","roughness"]))
    uv=mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 0)
    mul=mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -550, 0)
    sc=mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 60)
    sc.set_editor_property("r", float(tile))
    mel.connect_material_expressions(uv, "", mul, "A")
    mel.connect_material_expressions(sc, "", mul, "B")
    if bc:
        ts=mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, -80)
        ts.set_editor_property("texture", bc)
        mel.connect_material_expressions(mul, "", ts, "UVs")
        # slight darken so sand isn't blown white
        dark=mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 40)
        dark.set_editor_property("constant", unreal.LinearColor(0.72, 0.72, 0.72, 1.0))
        m2=mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -180, -40)
        mel.connect_material_expressions(ts, "RGB", m2, "A")
        mel.connect_material_expressions(dark, "", m2, "B")
        mel.connect_material_property(m2, "", unreal.MaterialProperty.MP_BASE_COLOR)
    if rough:
        ts=mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, 160)
        ts.set_editor_property("texture", rough)
        try: ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        except Exception: pass
        mel.connect_material_expressions(mul, "", ts, "UVs")
        mel.connect_material_property(ts, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat); unreal.EditorAssetLibrary.save_asset(path)
    log("sand tile=%.0f"%tile); return mat

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log(str(e))

sand=make_sand(32.0)
water=load(MAT+"/M_Tideborn_WaterSimple")
ox,oy,oz=1000.0,1000.0,100.0

for a in actors():
    lab=label(a)
    if lab.startswith("TidebornEnv_Sand") or lab=="TidebornEnv_SandBase":
        apply(a, sand)
    if "Shallows" in lab:
        a.set_actor_location(unreal.Vector(ox, oy-550, oz-8), False, True)
        a.set_actor_scale3d(unreal.Vector(150, 90, 1)); apply(a, water)
    if lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(ox, oy-1300, oz-18), False, True)
        a.set_actor_scale3d(unreal.Vector(200, 130, 1)); apply(a, water)
    if "DirectionalLight" in cname(a):
        try:
            a.set_editor_property("intensity", 2.2)
            a.set_editor_property("light_color", unreal.LinearColor(1.0,0.9,0.78,1.0))
            a.set_actor_rotation(unreal.Rotator(pitch=-48, yaw=55, roll=0), False)
            try: a.set_editor_property("indirect_lighting_intensity", 1.4)
            except Exception: pass
        except Exception: pass
    if "SkyLight" in cname(a):
        try:
            a.set_editor_property("intensity", 2.4)
            a.set_editor_property("real_time_capture", True)
        except Exception: pass
    if "ExponentialHeightFog" in cname(a):
        try:
            a.set_editor_property("fog_density", 0.045)
            a.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.5,0.65,0.85,1.0))
            try: a.set_editor_property("volumetric_fog", True)
            except Exception: pass
        except Exception: pass

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8"); log("DONE")
