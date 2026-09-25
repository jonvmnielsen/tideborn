# -*- coding: utf-8 -*-
"""v9h: fix/remove bad SkyBackdrop; keep clean water; add upright sky wall."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_living_v9h_result.txt"
MAT="/Game/Tideborn/Art/Materials"
MAP="/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V9h] "+t); lines.append(t)
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
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sky_mat=load(MAT+"/M_Tideborn_SkyBackdrop")
plane=load("/Engine/BasicShapes/Plane")
sand=load(MAT+"/MI_Tideborn_SandWarm")

for a in list(actors()):
    lab=label(a)
    if lab=="TidebornEnv_SkyBackdrop":
        try: eas.destroy_actor(a); log("x bad SkyBackdrop")
        except: pass
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1))
        if sand: force_apply(a,sand); log("LOCK SandBase")
    if "SkyAtmosphere" in cname(a) or "VolumetricCloud" in cname(a):
        unhide(a)

# Upright sky wall: Cube stretched thin in Y, tall in Z, wide in X — more predictable than rotated plane
cube=load("/Engine/BasicShapes/Cube")
if cube and sky_mat:
    # Cube is 100uu; sc (250, 0.2, 80) -> 25000 x 20 x 8000
    bd=eas.spawn_actor_from_object(cube, unreal.Vector(1000,-2500,2000), unreal.Rotator(0,0,0))
    if bd:
        bd.set_actor_label("TidebornEnv_SkyBackdrop")
        bd.set_actor_scale3d(unreal.Vector(250,0.15,100))
        force_apply(bd,sky_mat); unhide(bd)
        o,e=bd.get_actor_bounds(False,False)
        log("SkyWall Y=[%.0f..%.0f] Z=[%.0f..%.0f]"%(o.y-e.y,o.y+e.y,o.z-e.z,o.z+e.z))
        # Must stay behind ocean (Y < -500)
        if (o.y+e.y) > -400:
            log("SkyWall too close — move further")
            bd.set_actor_location(unreal.Vector(1000,-3500,2000),False,True)

for a in actors():
    if "SkyLight" in cname(a):
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.recapture_sky()
            except: pass
    if "DirectionalLight" in cname(a):
        a.set_actor_rotation(unreal.Rotator(pitch=-30,yaw=-90,roll=0),False)

# Final sand-in-water audit
for a in actors():
    lab=label(a)
    if any(k in lab for k in ("SandBase","Step","WetSand","Ocean","Shallows","SkyBack","Foam")):
        try:
            o,e=a.get_actor_bounds(False,False)
            log("DUMP %s Y=[%.0f..%.0f] Z=[%.1f..%.1f]"%(lab,o.y-e.y,o.y+e.y,o.z-e.z,o.z+e.z))
        except: pass

try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
