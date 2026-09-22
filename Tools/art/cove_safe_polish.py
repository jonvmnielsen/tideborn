# -*- coding: utf-8 -*-
"""Safer polish: bigger water in FOV, stronger skylight, more side dressing — keep sand floor."""
from __future__ import annotations
import pathlib, random, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_safe_polish_result.txt"
MAT="/Game/Tideborn/Art/Materials"; MESH="/Game/Tideborn/Art/Meshes"
lines=[]
def log(m):
    t=str(m); unreal.log("[Safe] "+t); lines.append(t)
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
def apply(a, mat):
    if not mat: return
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break
def spawn(mesh, loc, yaw, scale, lab, mat):
    a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_object(
        mesh, loc, unreal.Rotator(pitch=0,yaw=float(yaw),roll=0))
    if a:
        a.set_actor_scale3d(scale); a.set_actor_label(lab); apply(a, mat)
    return a

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log(str(e))

sand=load(MAT+"/M_Tideborn_Sand"); water=load(MAT+"/M_Tideborn_WaterSimple")
rock=load(MAT+"/M_Tideborn_RockShore") or load(MAT+"/M_Tideborn_RockBoulder")
bark=load(MAT+"/M_Tideborn_Bark")
boulder=load(MESH+"/boulder_01_1k"); stump=load(MESH+"/dead_tree_trunk_1k")
ox,oy,oz=1000.0,1000.0,100.0
rng=random.Random(17)

for a in actors():
    lab=label(a)
    if lab=="TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(ox, oy-650, oz-12), False, True)
        a.set_actor_scale3d(unreal.Vector(130, 70, 1)); apply(a, water); log("shallows big")
    if lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(ox, oy-1500, oz-22), False, True)
        a.set_actor_scale3d(unreal.Vector(180, 110, 1)); apply(a, water); log("ocean big")
    if lab=="TidebornEnv_SandBase":
        apply(a, sand)
    if "DirectionalLight" in cname(a):
        try:
            a.set_editor_property("intensity", 2.6)
            a.set_editor_property("light_color", unreal.LinearColor(1.0,0.92,0.8,1.0))
            a.set_actor_rotation(unreal.Rotator(pitch=-45, yaw=50, roll=0), False)
        except Exception: pass
    if "SkyLight" in cname(a):
        try:
            a.set_editor_property("intensity", 2.0)
            a.set_editor_property("real_time_capture", True)
        except Exception: pass
    if "ExponentialHeightFog" in cname(a):
        try:
            a.set_editor_property("fog_density", 0.04)
            a.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.45,0.6,0.8,1.0))
        except Exception: pass

# Extra mouth rocks + path pebbles (small boulders)
if boulder and rock:
    for i,(dx,dy,sc) in enumerate(((-620,-750,1.6),(720,-740,1.55),(-200,-50,0.7),(250,-80,0.65),(0,-280,0.55))):
        r=180.0
        try:
            box=boulder.get_bounding_box(); e=box.max-box.min; r=max(abs(e.x),abs(e.y),abs(e.z))
        except Exception: pass
        s=max(0.4, min(320.0/max(r,1.0), 2.4))*sc
        spawn(boulder, unreal.Vector(ox+dx, oy+dy, oz), rng.uniform(0,360), unreal.Vector(s,s,s),
              "TidebornEnv_Boulder_extra_%02d"%i, rock)

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8"); log("DONE")
