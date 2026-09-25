# -*- coding: utf-8 -*-
"""v9f: destroy broken ShoreLip; stepped Z lip; clamp wet/foam; keep SkyDome hidden."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_living_v9f_result.txt"
MAT="/Game/Tideborn/Art/Materials"
MAP="/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V9f] "+t); lines.append(t)
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

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log(str(e))
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sand=load(MAT+"/MI_Tideborn_SandWarm")
wet_dark=load(MAT+"/MI_Tideborn_SandWet")
wet_mid=load(MAT+"/MI_Tideborn_SandWetMid")
foam=load(MAT+"/MI_Tideborn_Foam")
plane=load("/Engine/BasicShapes/Plane")

for a in list(actors()):
    lab=label(a)
    if lab in ("TidebornEnv_ShoreLip","TidebornEnv_ShoreLip2") or lab.startswith("TidebornEnv_ShoreStep_"):
        try: eas.destroy_actor(a); log("x "+lab)
        except: pass
    if "SandRamp" in lab:
        try: eas.destroy_actor(a); log("x SandRamp")
        except: hide(a)
    if lab=="TidebornEnv_SkyDome" or "SkyDome" in lab:
        hide(a); log("HIDE SkyDome")
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1))
        if sand: force_apply(a,sand); log("LOCK SandBase")
    if lab=="TidebornEnv_WetSand_00":
        a.set_actor_location(unreal.Vector(1000,670,105.5),False,True)
        a.set_actor_scale3d(unreal.Vector(34,1.3,1))  # Y[605..735]
        if wet_dark: force_apply(a,wet_dark); log("WetSand_00 Y=670")
    if lab=="TidebornEnv_WetSand_01":
        a.set_actor_location(unreal.Vector(1000,730,105.9),False,True)
        a.set_actor_scale3d(unreal.Vector(32,1.2,1))
        if wet_mid: force_apply(a,wet_mid)
    if lab.startswith("TidebornEnv_FoamSeg_"):
        # nudge foam to sit just seaward of sand edge, discontinuous
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        a.set_actor_location(unreal.Vector(loc.x, 585.0 + (hash(lab)%7), 104.8),False,True)
        a.set_actor_scale3d(unreal.Vector(min(sc.x,10), max(sc.y,1.0), 1))
        if foam: force_apply(a,foam); unhide(a)
    if "SkyAtmosphere" in cname(a) or "VolumetricCloud" in cname(a) or "ExponentialHeightFog" in cname(a):
        unhide(a)

# Stepped lip: 3 flat sand planes at rising Z — readable height without rotation bugs
# All Ymin >= 620
if plane and sand:
    steps=[
        ("00", 1000.0, 640.0, 104.0, 28.0, 1.0),   # lowest near water Y[590..690] — wait keep >=620
        ("01", 1000.0, 680.0, 107.0, 28.0, 1.1),
        ("02", 1000.0, 720.0, 110.0, 26.0, 1.1),
        ("s0", 700.0, 660.0, 104.0, 6.0, 1.0),  # slope-cam side
        ("s1", 700.0, 700.0, 108.0, 6.0, 1.1),
        ("s2", 700.0, 740.0, 112.0, 5.5, 1.0),
    ]
    # Fix step 00 to Y=655 scY=1.0 -> [605..705]; actually use 660/1.0 -> [610..710]
    steps[0]=("00", 1000.0, 655.0, 104.0, 28.0, 0.9)  # half=45 -> Y[610..700]
    for name,x,y,z,sx,sy in steps:
        a=eas.spawn_actor_from_object(plane, unreal.Vector(x,y,z), unreal.Rotator(0,0,0))
        if a:
            a.set_actor_label("TidebornEnv_ShoreStep_"+name)
            a.set_actor_scale3d(unreal.Vector(sx,sy,1))
            force_apply(a,sand); unhide(a)
            o,e=a.get_actor_bounds(False,False)
            log("Step %s Y=[%.0f..%.0f] Z=%.1f"%(name,o.y-e.y,o.y+e.y,z))
            if (o.y-e.y)<600:
                # push inland
                new_y = 605 + e.y
                a.set_actor_location(unreal.Vector(x,new_y,z),False,True)
                log("Step %s pushed Y=%.0f"%(name,new_y))

for a in actors():
    if "DirectionalLight" in cname(a):
        a.set_actor_rotation(unreal.Rotator(pitch=-18,yaw=-45,roll=0),False)
    if "SkyLight" in cname(a):
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.recapture_sky()
            except: pass

# Final overlap check
for a in actors():
    lab=label(a)
    if not any(k in lab for k in ("Sand","Shore","Wet","Step","Ramp","Lip","Ground","Foam")): continue
    if "Ocean" in lab or "Shallows" in lab: continue
    try:
        o,e=a.get_actor_bounds(False,False)
        log("DUMP %s Y=[%.0f..%.0f] Z=[%.1f..%.1f]"%(lab,o.y-e.y,o.y+e.y,o.z-e.z,o.z+e.z))
        if (o.y-e.y)<580 and (o.z+e.z)>=99 and "Foam" not in lab:
            log("WARN "+lab)
    except Exception as ex:
        log("DUMP %s fail %s"%(lab,ex))

try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
