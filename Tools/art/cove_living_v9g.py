# -*- coding: utf-8 -*-
"""v9g: nuke shore steps; sky backdrop gradient plane; even light; clean water gap."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_living_v9g_result.txt"
MAT="/Game/Tideborn/Art/Materials"
MAP="/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V9g] "+t); lines.append(t)
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

def make_sky_back(name):
    """Vertical UV gradient for a large backdrop plane (peach horizon -> blue zenith)."""
    del_mat(name)
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,MAT,unreal.Material,unreal.MaterialFactoryNew())
    mel=unreal.MaterialEditingLibrary
    try:
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        mat.set_editor_property("two_sided", True)
    except: pass
    uv=mel.create_material_expression(mat,unreal.MaterialExpressionTextureCoordinate,-600,0)
    mask=mel.create_material_expression(mat,unreal.MaterialExpressionComponentMask,-450,0)
    try:
        mask.set_editor_property("r",False); mask.set_editor_property("g",True)
        mask.set_editor_property("b",False); mask.set_editor_property("a",False)
    except: pass
    mel.connect_material_expressions(uv,"",mask,"")
    bot=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-450,120)
    bot.set_editor_property("constant", unreal.LinearColor(1.05,0.78,0.50,1))
    top=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-450,-120)
    top.set_editor_property("constant", unreal.LinearColor(0.40,0.52,0.78,1))
    lerp=mel.create_material_expression(mat,unreal.MaterialExpressionLinearInterpolate,-200,0)
    mel.connect_material_expressions(bot,"",lerp,"A")
    mel.connect_material_expressions(top,"",lerp,"B")
    mel.connect_material_expressions(mask,"",lerp,"Alpha")
    em=mel.create_material_expression(mat,unreal.MaterialExpressionMultiply,0,0)
    b=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,0,80)
    b.set_editor_property("r",1.4)
    mel.connect_material_expressions(lerp,"",em,"A")
    mel.connect_material_expressions(b,"",em,"B")
    mel.connect_material_property(em,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(lerp,"",unreal.MaterialProperty.MP_BASE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT+"/"+name,True)
    log("sky_back "+name); return mat

def make_lit(name,rgb,rough=0.9,emissive=None):
    del_mat(name)
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,MAT,unreal.Material,unreal.MaterialFactoryNew())
    mel=unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except: pass
    c=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-400,0)
    c.set_editor_property("constant", unreal.LinearColor(rgb[0],rgb[1],rgb[2],1))
    mel.connect_material_property(c,"",unreal.MaterialProperty.MP_BASE_COLOR)
    r=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-400,120)
    r.set_editor_property("r",float(rough))
    mel.connect_material_property(r,"",unreal.MaterialProperty.MP_ROUGHNESS)
    m=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-400,200)
    m.set_editor_property("r",0.0)
    mel.connect_material_property(m,"",unreal.MaterialProperty.MP_METALLIC)
    e=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-400,280)
    if emissive:
        e.set_editor_property("constant", unreal.LinearColor(emissive[0],emissive[1],emissive[2],1))
    else:
        e.set_editor_property("constant", unreal.LinearColor(0,0,0,1))
    mel.connect_material_property(e,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(MAT+"/"+name,True)
    return mat

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log(str(e))
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sand=load(MAT+"/MI_Tideborn_SandWarm")
wet_dark=load(MAT+"/MI_Tideborn_SandWet")
wet_mid=load(MAT+"/MI_Tideborn_SandWetMid")
water=load(MAT+"/M_Tideborn_WaterOpaque")
foam=make_lit("MI_Tideborn_Foam",(0.98,0.96,0.90),0.45,emissive=(0.45,0.42,0.35))
sky_back=make_sky_back("M_Tideborn_SkyBackdrop")
plane=load("/Engine/BasicShapes/Plane")

for a in list(actors()):
    lab=label(a)
    if lab.startswith("TidebornEnv_ShoreStep_") or lab.startswith("TidebornEnv_FoamSeg_") or lab.startswith("TidebornEnv_ShoreLip") or lab=="TidebornEnv_SkyBackdrop":
        try: eas.destroy_actor(a); log("x "+lab)
        except: pass
    if lab=="TidebornEnv_SkyDome" or "SkyDome" in lab:
        hide(a)
    if "SandRamp" in lab or "BeachSlope" in lab:
        try: eas.destroy_actor(a); log("x "+lab)
        except: hide(a)

for a in actors():
    lab=label(a); cn=cname(a)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1))
        if sand: force_apply(a,sand); unhide(a); log("LOCK SandBase")
    elif lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000,-1200,99),False,True)
        a.set_actor_scale3d(unreal.Vector(95,14,1))  # Y[-1900..-500]
        if water: force_apply(a,water); unhide(a)
    elif lab=="TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000,50,100),False,True)
        a.set_actor_scale3d(unreal.Vector(80,9,1))  # Y[-400..500]
        if water: force_apply(a,water); unhide(a); log("Shallows Ymax~500")
    elif lab=="TidebornEnv_WetSand_00":
        a.set_actor_location(unreal.Vector(1000,680,105.5),False,True)
        a.set_actor_scale3d(unreal.Vector(34,1.4,1))  # Y[610..750]
        if wet_dark: force_apply(a,wet_dark)
    elif lab=="TidebornEnv_WetSand_01":
        a.set_actor_location(unreal.Vector(1000,740,105.9),False,True)
        a.set_actor_scale3d(unreal.Vector(32,1.3,1))
        if wet_mid: force_apply(a,wet_mid)

# Sky backdrop: huge vertical plane far past ocean, facing camera (+Y normal roughly)
# Plane is XY; rotate pitch=90 to stand vertical in XZ, then place at Y=-2200
if plane and sky_back:
    bd=eas.spawn_actor_from_object(plane, unreal.Vector(1000,-2200,800), unreal.Rotator(pitch=90,yaw=0,roll=0))
    if bd:
        bd.set_actor_label("TidebornEnv_SkyBackdrop")
        bd.set_actor_scale3d(unreal.Vector(200,80,1))  # wide x tall
        force_apply(bd,sky_back); unhide(bd)
        log("SkyBackdrop gradient @ Y=-2200")

# Foam segments between shallows(~500) and wet(~610)
if plane and foam:
    for i,(x,y,sx,sy,yaw) in enumerate([
        (760,560,9,1.15,-3),(940,570,10,1.2,2),(1120,555,11,1.1,-2),(1300,565,9,1.15,3)
    ]):
        af=eas.spawn_actor_from_object(plane,unreal.Vector(x,y,104.5),unreal.Rotator(0,yaw,0))
        if af:
            af.set_actor_label("TidebornEnv_FoamSeg_%02d"%i)
            af.set_actor_scale3d(unreal.Vector(sx,sy,1))
            force_apply(af,foam); unhide(af)
    log("Foam x4")

# Visible step lip ONLY inland of Y=620 — 3 Z levels
if plane and sand:
    for i,(y,z) in enumerate([(650,104.5),(690,108.0),(735,111.5)]):
        a=eas.spawn_actor_from_object(plane,unreal.Vector(1000,y,z),unreal.Rotator(0,0,0))
        if a:
            a.set_actor_label("TidebornEnv_ShoreStep_%02d"%i)
            a.set_actor_scale3d(unreal.Vector(30,0.9,1))  # halfY=45 -> stays >=605
            force_apply(a,sand); unhide(a)
            o,e=a.get_actor_bounds(False,False)
            log("Step%d Y=[%.0f..%.0f] Z=%.1f"%(i,o.y-e.y,o.y+e.y,z))
    # slope-cam local steps
    for i,(y,z) in enumerate([(660,104.5),(700,109.0),(745,113.0)]):
        a=eas.spawn_actor_from_object(plane,unreal.Vector(700,y,z),unreal.Rotator(0,0,0))
        if a:
            a.set_actor_label("TidebornEnv_ShoreStep_s%d"%i)
            a.set_actor_scale3d(unreal.Vector(6,0.9,1))
            force_apply(a,sand); unhide(a)

for a in actors():
    cn=cname(a); lab=label(a)
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn: unhide(a)
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity",0.4)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1,0.93,0.8,1))
            except: pass
            try: c.recapture_sky()
            except: pass
    if "DirectionalLight" in cn:
        unhide(a)
        a.set_actor_rotation(unreal.Rotator(pitch=-30,yaw=-90,roll=0),False)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity",3.2)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1,0.88,0.65,1))
            except: pass
            try: c.set_editor_property("atmosphere_sun_light",True)
            except: pass
        log("DirLight yaw=-90 even warm")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density",0.025)
            except: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.65,0.60,0.58,1))
            except: pass
    if "PostProcess" in cn or lab=="TidebornEnv_PostProcess":
        try:
            s=a.get_editor_property("settings")
            s.set_editor_property("override_white_temp",True)
            s.set_editor_property("white_temp",3950.0)
            s.set_editor_property("override_color_gain",True)
            s.set_editor_property("color_gain", unreal.Vector4(1.12,1.02,0.90,1))
            a.set_editor_property("settings",s)
            log("PP mild")
        except Exception as e: log(str(e))

for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1","ShowFlag.Atmosphere 1","ShowFlag.Fog 1","ShowFlag.Cloud 1"):
    try: unreal.SystemLibrary.execute_console_command(None,cmd)
    except: pass

# Overlap audit
for a in actors():
    lab=label(a)
    if not any(k in lab for k in ("Sand","Shore","Wet","Step","Foam","Ocean","Shallows","SkyBack","Ground")): continue
    try:
        o,e=a.get_actor_bounds(False,False)
        log("DUMP %s Y=[%.0f..%.0f] Z=[%.1f..%.1f]"%(lab,o.y-e.y,o.y+e.y,o.z-e.z,o.z+e.z))
        if lab not in ("TidebornEnv_Ocean","TidebornEnv_Shallows","TidebornEnv_SkyBackdrop") and "Foam" not in lab:
            if (o.y-e.y)<550 and (o.z+e.z)>=99:
                log("WARN "+lab)
    except: pass

try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
