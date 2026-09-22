# -*- coding: utf-8 -*-
"""EMERGENCY: restore playable sand+rock+water cove (no broken beach mesh)."""
from __future__ import annotations
import math, pathlib, random, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_restore_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MESH = "/Game/Tideborn/Art/Meshes"
lines=[]; C={"props":0}

def log(m):
    t=str(m); unreal.log("[Restore] "+t); lines.append(t)
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
        try: comp.set_editor_property("override_materials",[mat]*8)
        except Exception: pass
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break
def bounds_r(mesh):
    try:
        box=mesh.get_bounding_box(); e=box.max-box.min
        return max(abs(e.x),abs(e.y),abs(e.z))
    except Exception: return 100.0
def spawn(mesh, loc, yaw, scale, lab, mat):
    a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_object(
        mesh, loc, unreal.Rotator(pitch=0, yaw=float(yaw), roll=0))
    if not a: return None
    a.set_actor_scale3d(scale); a.set_actor_label(lab); apply(a, mat); return a
def plane(loc, sx, sy, mat, lab):
    p=load("/Engine/BasicShapes/Plane")
    return spawn(p, loc, 0, unreal.Vector(sx,sy,1), lab, mat)

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log(str(e))

# Wipe ALL TidebornEnv
for a in list(actors()):
    lab=label(a)
    if lab.startswith("TidebornEnv_"):
        try:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
            log("x "+lab)
        except Exception: pass

sand=load(MAT+"/M_Tideborn_Sand"); ground=load(MAT+"/M_Tideborn_Ground")
water=load(MAT+"/M_Tideborn_WaterSimple")
rock=load(MAT+"/M_Tideborn_RockShore") or load(MAT+"/M_Tideborn_RockBoulder")
bark=load(MAT+"/M_Tideborn_Bark")
creature=load(MAT+"/M_Tideborn_CreatureSolid"); gate=load(MAT+"/M_Tideborn_GateSolid")
boulder=load(MESH+"/boulder_01_1k"); stump=load(MESH+"/dead_tree_trunk_1k")
ox,oy,oz=1000.0,1000.0,100.0
rng=random.Random(5)

# Continuous floors first — NEVER void
plane(unreal.Vector(ox, oy, oz-2), 140, 140, sand, "TidebornEnv_SandBase")
plane(unreal.Vector(ox, oy+1600, oz-3), 120, 100, ground, "TidebornEnv_Ground")
plane(unreal.Vector(ox, oy-800, oz-15), 120, 55, water, "TidebornEnv_Shallows")
plane(unreal.Vector(ox, oy-1700, oz-28), 160, 100, water, "TidebornEnv_Ocean")
log("floors ok")

# Wide horseshoe rocks
spots=[]
for i in range(8):
    spots.append((ox-500-i*18, oy+120-i*115, "Boulder", 1.25))
for i in range(8):
    spots.append((ox+580+i*20, oy+100-i*115, "Boulder", 1.25))
spots += [(ox-580, oy-700, "Boulder", 1.5),(ox+700, oy-680, "Boulder", 1.5),
          (ox-450, oy+400, "Boulder", 1.2),(ox+550, oy+380, "Boulder", 1.2)]
# driftwood sides
spots += [(ox-340, oy-40, "Trunk", 0.95),(ox+460, oy-20, "Trunk", 0.95),
          (ox-380, oy-320, "Trunk", 0.9),(ox+500, oy-300, "Trunk", 0.9)]

for i,(x,y,kind,scmul) in enumerate(spots):
    mesh=boulder if kind=="Boulder" else stump
    mat=rock if kind=="Boulder" else bark
    if not mesh: continue
    r=bounds_r(mesh)
    sc=max(0.55, min(400.0/max(r,1.0), 2.5))*scmul*rng.uniform(0.94,1.05)
    if spawn(mesh, unreal.Vector(x,y,oz), rng.uniform(0,360), unreal.Vector(sc,sc,sc),
             "TidebornEnv_%s_%02d"%(kind,i), mat):
        C["props"]+=1

for a in actors():
    lab=label(a); cn=cname(a)
    if "PlayerStart" in cn or lab=="PlayerStart":
        a.set_actor_location(unreal.Vector(ox+80, oy+160, oz+110), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0), False)
    if "Kelp" in lab:
        a.set_actor_location(unreal.Vector(ox-850, oy+500, oz+40), False, True); apply(a, creature)
    if "Burr" in lab or "Hound" in lab:
        a.set_actor_location(unreal.Vector(ox+900, oy+550, oz+50), False, True); apply(a, creature)
    if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
        a.set_actor_location(unreal.Vector(ox+100, oy+1700, oz+90), False, True); apply(a, gate)
    if "Gather" in lab and "Stone" in lab:
        a.set_actor_location(unreal.Vector(ox+300, oy+200, oz+35), False, True); apply(a, rock)
for i,a in enumerate([a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]):
    a.set_actor_location(unreal.Vector(ox+240+i*130, oy+220, oz+35), False, True); apply(a, bark)

for a in actors():
    if "DirectionalLight" in cname(a):
        try:
            a.set_editor_property("intensity", 3.2)
            a.set_actor_rotation(unreal.Rotator(pitch=-40, yaw=35, roll=0), False)
        except Exception: pass
    if "SkyLight" in cname(a):
        try: a.set_editor_property("intensity", 1.3); a.set_editor_property("real_time_capture", True)
        except Exception: pass
    if "ExponentialHeightFog" in cname(a):
        try: a.set_editor_property("fog_density", 0.03)
        except Exception: pass

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("props=%d DONE"%C["props"])
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
