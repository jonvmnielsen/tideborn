# -*- coding: utf-8 -*-
"""Widen cove corridor, move trunks off path, open playable sand to water."""
from __future__ import annotations
import pathlib, random, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_widen_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MESH = "/Game/Tideborn/Art/Meshes"
lines=[]; C={"props":0,"destroyed":0}

def log(m):
    t=str(m); unreal.log("[Widen] "+t); lines.append(t)
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
def bounds_r(mesh):
    try:
        box=mesh.get_bounding_box(); e=box.max-box.min
        return max(abs(e.x), abs(e.y), abs(e.z))
    except Exception: return 100.0
def spawn(mesh, loc, yaw, scale, lab, mat):
    a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_object(
        mesh, loc, unreal.Rotator(pitch=0.0, yaw=float(yaw), roll=0.0))
    if not a: return None
    a.set_actor_scale3d(scale); a.set_actor_label(lab); apply(a, mat); return a

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log(str(e))

for a in list(actors()):
    lab=label(a)
    if lab.startswith("TidebornEnv_Boulder") or lab.startswith("TidebornEnv_Trunk"):
        try:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a); C["destroyed"]+=1
        except Exception: pass

rock=load(MAT+"/M_Tideborn_RockShore") or load(MAT+"/M_Tideborn_RockBoulder")
bark=load(MAT+"/M_Tideborn_Bark")
sand=load(MAT+"/M_Tideborn_Sand"); ground=load(MAT+"/M_Tideborn_Ground"); water=load(MAT+"/M_Tideborn_WaterSimple")
creature=load(MAT+"/M_Tideborn_CreatureSolid"); gate=load(MAT+"/M_Tideborn_GateSolid")
boulder=load(MESH+"/boulder_01_1k"); stump=load(MESH+"/dead_tree_trunk_1k")

ox,oy,oz=1000.0,1000.0,100.0
rng=random.Random(7)
# Wide playable corridor ~800uu: left rocks x<=ox-280, right x>=ox+380
spots=[]
for i in range(7):  # left ridge
    spots.append((ox-420-i*25, oy+80-i*130, "Boulder", 1.15+0.05*(i%3)))
for i in range(7):  # right ridge
    spots.append((ox+500+i*30, oy+60-i*125, "Boulder", 1.15+0.05*(i%3)))
# outer shoulders farther out
spots.append((ox-650, oy-200, "Boulder", 1.5))
spots.append((ox-600, oy-450, "Boulder", 1.35))
spots.append((ox+750, oy-180, "Boulder", 1.45))
spots.append((ox+720, oy-430, "Boulder", 1.3))
# near water mouth — still open center
spots.append((ox-500, oy-700, "Boulder", 1.4))
spots.append((ox+620, oy-680, "Boulder", 1.4))
# driftwood OFF path — left and right beach edges only
spots.append((ox-300, oy-50, "Trunk", 0.9))
spots.append((ox-340, oy-280, "Trunk", 0.85))
spots.append((ox+420, oy-40, "Trunk", 0.9))
spots.append((ox+460, oy-260, "Trunk", 0.85))
spots.append((ox-200, oy-500, "Trunk", 0.8))
spots.append((ox+350, oy-520, "Trunk", 0.8))

for i,(x,y,kind,scmul) in enumerate(spots):
    mesh=boulder if kind=="Boulder" else stump
    mat=rock if kind=="Boulder" else bark
    if not mesh: continue
    r=bounds_r(mesh)
    sc=max(0.5, min(400.0/max(r,1.0), 2.5))*scmul*rng.uniform(0.92,1.06)
    if spawn(mesh, unreal.Vector(x,y,oz), rng.uniform(0,360), unreal.Vector(sc,sc,sc*rng.uniform(0.9,1.05)),
             "TidebornEnv_%s_%02d"%(kind,i), mat):
        C["props"]+=1

for a in actors():
    lab=label(a); cn=cname(a)
    if "PlayerStart" in cn or lab=="PlayerStart":
        a.set_actor_location(unreal.Vector(ox+100, oy+120, oz+95), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0.0,yaw=-90.0,roll=0.0), False)
    if "Kelp" in lab:
        a.set_actor_location(unreal.Vector(ox-480, oy+40, oz+40), False, True); apply(a, creature)
    if "Burr" in lab or "Hound" in lab:
        a.set_actor_location(unreal.Vector(ox+620, oy+80, oz+50), False, True); apply(a, creature)
    if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
        a.set_actor_location(unreal.Vector(ox+100, oy+1350, oz+90), False, True); apply(a, gate)
    if "Gather" in lab and "Stone" in lab:
        a.set_actor_location(unreal.Vector(ox+360, oy+60, oz+30), False, True); apply(a, rock)
    if lab.startswith("TidebornEnv_Sand"): apply(a, sand)
    elif lab.startswith("TidebornEnv_Ground"): apply(a, ground)
    elif "Ocean" in lab or "Shallows" in lab: apply(a, water)
for i,a in enumerate([a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]):
    a.set_actor_location(unreal.Vector(ox+280+i*130, oy+40, oz+30), False, True); apply(a, bark)

for a in actors():
    if "DirectionalLight" in cname(a):
        try:
            a.set_editor_property("intensity", 3.6)
            a.set_actor_rotation(unreal.Rotator(pitch=-42.0, yaw=28.0, roll=0.0), False)
        except Exception: pass

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("props=%d destroyed=%d DONE"%(C["props"],C["destroyed"]))
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
