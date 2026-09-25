# -*- coding: utf-8 -*-
"""v9e: hide peach SkyDome (use SkyAtmosphere), purge sand Y<600, rebuild foam+lip."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT/"Tools"/"art"/"cove_living_v9e_result.txt"
DUMP = ROOT/"Tools"/"art"/"cove_dump_v9e.txt"
MAT="/Game/Tideborn/Art/Materials"
MAP="/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V9e] "+t); lines.append(t)
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
    log("mat "+name); return mat

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log(str(e))
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

sand=load(MAT+"/MI_Tideborn_SandWarm")
wet_dark=load(MAT+"/MI_Tideborn_SandWet")
wet_mid=load(MAT+"/MI_Tideborn_SandWetMid")
water=load(MAT+"/M_Tideborn_WaterOpaque")
foam=make_lit("MI_Tideborn_Foam",(0.98,0.97,0.92),0.5,emissive=(0.35,0.33,0.28))
plane=load("/Engine/BasicShapes/Plane")

# Destroy helpers that bleed into water / bad lip
kill_prefix=("TidebornEnv_FoamSeg_","TidebornEnv_WetJag_","TidebornEnv_ShoreLip","TidebornEnv_BeachSlope","TidebornEnv_ShoreEdge")
for a in list(actors()):
    lab=label(a)
    if any(lab.startswith(p) or lab==p for p in kill_prefix) or lab in ("TidebornEnv_ShoreLip","TidebornEnv_ShoreLip2","TidebornEnv_BeachSlope","TidebornEnv_ShoreEdge"):
        try: eas.destroy_actor(a); log("x "+lab)
        except: pass
    if "SandRamp" in lab:
        hide(a); log("HIDE SandRamp")
    # Hide flat peach SkyDome — let SkyAtmosphere provide gradient
    if lab=="TidebornEnv_SkyDome" or "SkyDome" in lab or "SkySphere" in lab:
        hide(a); log("HIDE "+lab+" (was peach slab)")

# Core layout — hard rule: no sand-colored geo with Ymin < 600 and Zmax >= 99
for a in actors():
    lab=label(a); cn=cname(a)
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1))
        if sand: force_apply(a,sand); unhide(a); log("LOCK SandBase edgeY=600")
    elif lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(1000,-1000,99),False,True)
        a.set_actor_scale3d(unreal.Vector(90,15,1))
        if water: force_apply(a,water); unhide(a); log("Ocean")
    elif lab=="TidebornEnv_Shallows":
        # End before sand edge so blue is continuous up to wet band
        a.set_actor_location(unreal.Vector(1000,150,100),False,True)
        a.set_actor_scale3d(unreal.Vector(75,7.5,1))  # Y [-225..525]
        if water: force_apply(a,water); unhide(a); log("Shallows Ymax~525")
    elif lab=="TidebornEnv_WetSand_00":
        a.set_actor_location(unreal.Vector(1000,650,105.4),False,True)
        a.set_actor_scale3d(unreal.Vector(36,1.8,1))
        if wet_dark: force_apply(a,wet_dark); unhide(a)
    elif lab=="TidebornEnv_WetSand_01":
        a.set_actor_location(unreal.Vector(1000,720,105.8),False,True)
        a.set_actor_scale3d(unreal.Vector(34,1.6,1))
        if wet_mid: force_apply(a,wet_mid); unhide(a)
    elif lab=="TidebornEnv_Ground":
        a.set_actor_location(unreal.Vector(1000,2800,105),False,True)

# Shore lip: roll slope, STRICTLY Y>=620
if plane and sand:
    lip=eas.spawn_actor_from_object(plane, unreal.Vector(1000,710,105.0), unreal.Rotator(0,0,18))
    if lip:
        lip.set_actor_label("TidebornEnv_ShoreLip")
        lip.set_actor_scale3d(unreal.Vector(30,1.4,1))  # halfY=70 -> Y[640..780]
        force_apply(lip,sand); unhide(lip)
        o,e=lip.get_actor_bounds(False,False)
        if e.z>60:
            lip.set_actor_rotation(unreal.Rotator(0,0,-18),False)
            o,e=lip.get_actor_bounds(False,False)
        log("ShoreLip Y=[%.0f..%.0f] Z=[%.1f..%.1f]"%(o.y-e.y,o.y+e.y,o.z-e.z,o.z+e.z))
    # Slope-cam lip near X=700
    lip2=eas.spawn_actor_from_object(plane, unreal.Vector(700,700,105.0), unreal.Rotator(0,0,20))
    if lip2:
        lip2.set_actor_label("TidebornEnv_ShoreLip2")
        lip2.set_actor_scale3d(unreal.Vector(7,1.5,1))
        force_apply(lip2,sand); unhide(lip2)
        o,e=lip2.get_actor_bounds(False,False)
        if e.z>60: lip2.set_actor_rotation(unreal.Rotator(0,0,-20),False)
        log("ShoreLip2 ok")

# Foam: bright white, thick, staggered, Y~560-585 (between shallows end and wet sand)
if plane and foam:
    specs=[
        (740,565,9.0,1.1,-4),
        (900,575,10.0,1.2,3),
        (1060,560,11.0,1.0,-2),
        (1220,570,9.5,1.15,4),
        (1360,562,8.5,1.0,-3),
    ]
    for i,(x,y,sx,sy,yaw) in enumerate(specs):
        af=eas.spawn_actor_from_object(plane,unreal.Vector(x,y,104.6),unreal.Rotator(0,yaw,0))
        if af:
            af.set_actor_label("TidebornEnv_FoamSeg_%02d"%i)
            af.set_actor_scale3d(unreal.Vector(sx,sy,1))
            force_apply(af,foam); unhide(af)
    log("FoamSeg x5 bright")

# Lighting / sky atmosphere (NO skydome)
for a in actors():
    cn=cname(a); lab=label(a)
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        unhide(a); log("SHOW "+cn)
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("real_time_capture",True)
            except: pass
            try: c.set_editor_property("cubemap",None)
            except: pass
            try: c.set_editor_property("intensity",0.35)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0,0.92,0.78,1))
            except: pass
            try: c.recapture_sky()
            except: pass
        log("SkyLight 0.35")
    if "DirectionalLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity",3.8)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0,0.85,0.62,1))
            except: pass
            try: c.set_editor_property("atmosphere_sun_light",True)
            except: pass
        # Low sun for warm horizon + atmosphere gradient
        a.set_actor_rotation(unreal.Rotator(pitch=-18,yaw=-50,roll=0),False)
        log("DirLight low sun")
    if "ExponentialHeightFog" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density",0.032)
            except: pass
            try: c.set_editor_property("fog_height_falloff",0.2)
            except: pass
            # Warm peach-grey haze near horizon, not solid peach fill
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.70,0.62,0.55,1))
            except: pass
            try: c.set_editor_property("directional_inscattering_color", unreal.LinearColor(1.0,0.72,0.45,1))
            except: pass
            try: c.set_editor_property("directional_inscattering_exponent",4.0)
            except: pass
        log("Fog soft haze 0.032")
    if "PostProcess" in cn or lab=="TidebornEnv_PostProcess":
        unhide(a)
        try:
            try: a.set_editor_property("unbound",True)
            except: pass
            s=a.get_editor_property("settings")
            # Keep sand warm via mild temp; DO NOT crush blue channel
            try:
                s.set_editor_property("override_white_temp",True)
                s.set_editor_property("white_temp",4000.0)
            except: pass
            try:
                s.set_editor_property("override_color_gain",True)
                s.set_editor_property("color_gain", unreal.Vector4(1.15,1.02,0.88,1))
            except: pass
            try:
                s.set_editor_property("override_scene_color_tint",True)
                s.set_editor_property("scene_color_tint", unreal.LinearColor(1.06,0.98,0.90,1))
            except: pass
            try:
                s.set_editor_property("override_auto_exposure_method",True)
                s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
                s.set_editor_property("override_auto_exposure_bias",True)
                s.set_editor_property("auto_exposure_bias",-0.05)
            except: pass
            a.set_editor_property("settings",s)
            log("PP mild warm keep sky blue")
        except Exception as e: log("PP "+str(e))

for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1",
            "ShowFlag.Atmosphere 1","ShowFlag.Fog 1","ShowFlag.Cloud 1",
            "r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None,cmd)
    except: pass

for a in actors():
    if "SkyLight" in cname(a):
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.recapture_sky()
            except: pass

dump=[]
for a in actors():
    lab=label(a)
    if not any(k in lab for k in ("SandBase","Ocean","Shallows","WetSand","Foam","Shore","Ground","Ramp","Beach","Lip")): continue
    try:
        o,e=a.get_actor_bounds(False,False)
        line="%s Y=[%.0f..%.0f] Z=[%.1f..%.1f]"%(lab,o.y-e.y,o.y+e.y,o.z-e.z,o.z+e.z)
    except:
        loc=a.get_actor_location(); line="%s locY=%.0f locZ=%.1f"%(lab,loc.y,loc.z)
    dump.append(line); log("DUMP "+line)
    if lab in ("TidebornEnv_Ocean","TidebornEnv_Shallows"): continue
    if any(k in lab for k in ("Sand","Shore","Lip","Wet","Ramp","Ground","Beach")):
        try:
            if (o.y-e.y)<580 and (o.z+e.z)>=99:
                log("WARN_OVERLAP "+line)
        except: pass

DUMP.write_text("\n".join(dump)+"\n",encoding="utf-8")
try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
