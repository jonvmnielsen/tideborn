# -*- coding: utf-8 -*-
"""Pull water closer, densify cove arms for overview, keep wide playable corridor."""
from __future__ import annotations
import pathlib, random, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_water_result.txt"
MAT="/Game/Tideborn/Art/Materials"; MESH="/Game/Tideborn/Art/Meshes"
lines=[]; C={"props":0,"destroyed":0,"planes":0}

def log(m):
    t=str(m); unreal.log("[WaterIn] "+t); lines.append(t)
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
        try: comp.set_editor_property("override_materials", [mat]*8)
        except Exception: pass
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break
def destroy(a, why):
    try:
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a); C["destroyed"]+=1; log("x "+label(a)+" "+why)
    except Exception as e: log(str(e))
def bounds_r(mesh):
    try:
        box=mesh.get_bounding_box(); e=box.max-box.min
        return max(abs(e.x),abs(e.y),abs(e.z))
    except Exception: return 100.0
def spawn(mesh, loc, yaw, scale, lab, mat):
    a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_object(
        mesh, loc, unreal.Rotator(pitch=0.0,yaw=float(yaw),roll=0.0))
    if not a: return None
    a.set_actor_scale3d(scale); a.set_actor_label(lab); apply(a, mat); return a
def plane(loc, sx, sy, mat, lab):
    p=load("/Engine/BasicShapes/Plane")
    return spawn(p, loc, 0.0, unreal.Vector(sx,sy,1.0), lab, mat)

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log(str(e))

# clear env only
for a in list(actors()):
    lab=label(a)
    if lab.startswith("TidebornEnv_"):
        destroy(a, "rebuild")

rock=load(MAT+"/M_Tideborn_RockShore") or load(MAT+"/M_Tideborn_RockBoulder")
bark=load(MAT+"/M_Tideborn_Bark")
sand=load(MAT+"/M_Tideborn_Sand"); ground=load(MAT+"/M_Tideborn_Ground"); water=load(MAT+"/M_Tideborn_WaterSimple")
creature=load(MAT+"/M_Tideborn_CreatureSolid"); gate=load(MAT+"/M_Tideborn_GateSolid")
boulder=load(MESH+"/boulder_01_1k"); stump=load(MESH+"/dead_tree_trunk_1k")
ox,oy,oz=1000.0,1000.0,100.0
rng=random.Random(13)

# Ground behind spawn
if plane(unreal.Vector(ox+200, oy+1600, oz-4), 130, 130, ground, "TidebornEnv_Ground"): C["planes"]+=1
# Beach — large continuous sand toward ocean
if plane(unreal.Vector(ox+100, oy-200, oz-1), 90, 70, sand, "TidebornEnv_Sand_0"): C["planes"]+=1
if plane(unreal.Vector(ox-500, oy-150, oz-1), 50, 55, sand, "TidebornEnv_Sand_1"): C["planes"]+=1
if plane(unreal.Vector(ox+700, oy-150, oz-1), 50, 55, sand, "TidebornEnv_Sand_2"): C["planes"]+=1
if plane(unreal.Vector(ox+100, oy+500, oz-1), 60, 50, sand, "TidebornEnv_Sand_3"): C["planes"]+=1
# Water CLOSE — shallows just ahead of beach, ocean beyond
if plane(unreal.Vector(ox+100, oy-900, oz-18), 110, 50, water, "TidebornEnv_Shallows"): C["planes"]+=1
if plane(unreal.Vector(ox+100, oy-1800, oz-40), 150, 90, water, "TidebornEnv_Ocean"): C["planes"]+=1

# Dense but WIDE horseshoe (corridor ~900uu)
spots=[]
for i in range(8):
    spots.append((ox-480-i*20, oy+100-i*110, "Boulder", 1.2))
for i in range(8):
    spots.append((ox+560+i*22, oy+80-i*110, "Boulder", 1.2))
# mouth toward water
spots += [(ox-560, oy-650, "Boulder", 1.5),(ox-480, oy-800, "Boulder", 1.3),
          (ox+680, oy-640, "Boulder", 1.5),(ox+620, oy-790, "Boulder", 1.3)]
# back corners
spots += [(ox-400, oy+350, "Boulder", 1.25),(ox+520, oy+330, "Boulder", 1.25)]
# driftwood sides only
spots += [(ox-320, oy-40, "Trunk", 0.9),(ox-360, oy-300, "Trunk", 0.85),
          (ox+440, oy-20, "Trunk", 0.9),(ox+480, oy-280, "Trunk", 0.85),
          (ox-250, oy-520, "Trunk", 0.8),(ox+400, oy-540, "Trunk", 0.8)]

for i,(x,y,kind,scmul) in enumerate(spots):
    mesh=boulder if kind=="Boulder" else stump
    mat=rock if kind=="Boulder" else bark
    if not mesh: continue
    r=bounds_r(mesh)
    sc=max(0.5, min(420.0/max(r,1.0), 2.6))*scmul*rng.uniform(0.93,1.05)
    if spawn(mesh, unreal.Vector(x,y,oz), rng.uniform(0,360), unreal.Vector(sc,sc,sc),
             "TidebornEnv_%s_%02d"%(kind,i), mat):
        C["props"]+=1

for a in actors():
    lab=label(a); cn=cname(a)
    if "PlayerStart" in cn or lab=="PlayerStart":
        a.set_actor_location(unreal.Vector(ox+100, oy+150, oz+95), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0.0,yaw=-90.0,roll=0.0), False)
    if "Kelp" in lab:
        a.set_actor_location(unreal.Vector(ox-500, oy+60, oz+40), False, True); apply(a, creature)
    if "Burr" in lab or "Hound" in lab:
        a.set_actor_location(unreal.Vector(ox+640, oy+100, oz+50), False, True); apply(a, creature)
    if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
        a.set_actor_location(unreal.Vector(ox+100, oy+1400, oz+90), False, True); apply(a, gate)
    if "Gather" in lab and "Stone" in lab:
        a.set_actor_location(unreal.Vector(ox+340, oy+80, oz+30), False, True); apply(a, rock)
for i,a in enumerate([a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]):
    a.set_actor_location(unreal.Vector(ox+260+i*130, oy+50, oz+30), False, True); apply(a, bark)

for a in actors():
    if "DirectionalLight" in cname(a):
        try:
            a.set_editor_property("intensity", 3.5)
            a.set_actor_rotation(unreal.Rotator(pitch=-42.0, yaw=25.0, roll=0.0), False)
        except Exception: pass
    if "ExponentialHeightFog" in cname(a):
        try:
            a.set_editor_property("fog_density", 0.03)
            a.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.4,0.55,0.75,1.0))
        except Exception: pass

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("planes=%d props=%d destroyed=%d DONE"%(C["planes"],C["props"],C["destroyed"]))
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
