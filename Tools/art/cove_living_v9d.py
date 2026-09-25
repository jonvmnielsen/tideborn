# -*- coding: utf-8 -*-
"""v9d: ShoreLip use Roll (slope in Y), not Pitch; clamp foam; keep sky."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v9d_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V9d] "+t); lines.append(t)
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
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sand = load(MAT+"/MI_Tideborn_SandWarm")
foam = load(MAT+"/MI_Tideborn_Foam")
plane = load("/Engine/BasicShapes/Plane")

for a in list(actors()):
    lab=label(a)
    if lab in ("TidebornEnv_ShoreLip","TidebornEnv_ShoreLip2") or lab.startswith("TidebornEnv_FoamSeg_"):
        try: eas.destroy_actor(a); log("x "+lab)
        except: pass
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1))
        if sand: force_apply(a,sand); log("LOCK SandBase")
    if lab=="TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000,180,100),False,True)
        a.set_actor_scale3d(unreal.Vector(72,8.0,1)); log("Shallows Y=180 scY=8")
    if "SkyAtmosphere" in cname(a) or "VolumetricCloud" in cname(a) or "ExponentialHeightFog" in cname(a):
        unhide(a)
    if lab=="TidebornEnv_SkyDome":
        unhide(a)

# Shore lip: ROLL so slope is along Y (toward water -Y lowers)
# roll=+15 => check bounds; want land(+Y) higher, water(-Y) lower
if plane and sand:
    lip = eas.spawn_actor_from_object(
        plane, unreal.Vector(1000.0, 700.0, 104.0),
        unreal.Rotator(pitch=0.0, yaw=0.0, roll=14.0))
    if lip:
        lip.set_actor_label("TidebornEnv_ShoreLip")
        # Narrow Y: scY=1.6 -> half=80; Y[620..780]; X mouth width
        lip.set_actor_scale3d(unreal.Vector(32.0, 1.6, 1.0))
        force_apply(lip, sand); unhide(lip)
        origin, extent = lip.get_actor_bounds(False, False)
        log("ShoreLip roll=14 Y=[%.0f..%.0f] Z=[%.1f..%.1f]" % (
            origin.y-extent.y, origin.y+extent.y, origin.z-extent.z, origin.z+extent.z))
        # If Z span still huge, destroy and use unrotated raised strip + second strip
        if (extent.z > 80):
            log("ShoreLip Z too big — retry opposite roll")
            lip.set_actor_rotation(unreal.Rotator(0,0,-14), False)
            origin, extent = lip.get_actor_bounds(False, False)
            log("ShoreLip roll=-14 Y=[%.0f..%.0f] Z=[%.1f..%.1f]" % (
                origin.y-extent.y, origin.y+extent.y, origin.z-extent.z, origin.z+extent.z))
    # Side lip for Slope cam at X=700
    lip2 = eas.spawn_actor_from_object(
        plane, unreal.Vector(700.0, 680.0, 104.0),
        unreal.Rotator(pitch=0.0, yaw=0.0, roll=16.0))
    if lip2:
        lip2.set_actor_label("TidebornEnv_ShoreLip2")
        lip2.set_actor_scale3d(unreal.Vector(8.0, 1.8, 1.0))
        force_apply(lip2, sand); unhide(lip2)
        origin, extent = lip2.get_actor_bounds(False, False)
        if extent.z > 80:
            lip2.set_actor_rotation(unreal.Rotator(0,0,-16), False)
            origin, extent = lip2.get_actor_bounds(False, False)
        log("ShoreLip2 Y=[%.0f..%.0f] Z=[%.1f..%.1f]" % (
            origin.y-extent.y, origin.y+extent.y, origin.z-extent.z, origin.z+extent.z))

# Foam segments — keep Y>=520, thick
if plane and foam:
    specs = [
        (720.0, 535.0, 10.0, 1.1, -3.0),
        (880.0, 548.0, 11.0, 1.2, 2.5),
        (1040.0, 532.0, 12.0, 1.05, -2.0),
        (1200.0, 542.0, 10.5, 1.15, 3.0),
        (1340.0, 538.0, 9.0, 1.0, -2.5),
    ]
    for i,(x,y,scx,scy,yaw) in enumerate(specs):
        af = eas.spawn_actor_from_object(plane, unreal.Vector(x,y,104.8), unreal.Rotator(0,yaw,0))
        if af:
            af.set_actor_label("TidebornEnv_FoamSeg_%02d"%i)
            af.set_actor_scale3d(unreal.Vector(scx,scy,1))
            force_apply(af,foam); unhide(af)
    log("FoamSeg x5")

# DirLight side
for a in actors():
    if "DirectionalLight" in cname(a):
        a.set_actor_rotation(unreal.Rotator(pitch=-24, yaw=-30, roll=0), False)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 3.5)
            except: pass
        log("DirLight")
    if "SkyLight" in cname(a):
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity", 0.25)
            except: pass
            try: c.recapture_sky()
            except: pass

# Final dump sand/water
for a in actors():
    lab=label(a)
    if not any(k in lab for k in ("SandBase","Ocean","Shallows","ShoreLip","FoamSeg","WetSand_00","BeachSlope")): continue
    loc=a.get_actor_location()
    try:
        o,e=a.get_actor_bounds(False,False)
        log("%s Y=[%.0f..%.0f] Z=[%.1f..%.1f] locZ=%.1f"%(lab,o.y-e.y,o.y+e.y,o.z-e.z,o.z+e.z,loc.z))
        if lab not in ("TidebornEnv_Ocean","TidebornEnv_Shallows") and (o.y-e.y)<400 and (o.z+e.z)>=99:
            log("WARN "+lab)
    except Exception as ex:
        log("%s bounds_fail %s"%(lab,ex))

try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
