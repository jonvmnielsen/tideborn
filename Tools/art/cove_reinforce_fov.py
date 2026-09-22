# -*- coding: utf-8 -*-
"""Reinforce horseshoe so both arms read in player FOV; keep sand floor."""
from __future__ import annotations
import pathlib, random, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_reinforce_result.txt"
MAT="/Game/Tideborn/Art/Materials"; MESH="/Game/Tideborn/Art/Meshes"
lines=[]
def log(m):
    t=str(m); unreal.log("[Reinforce] "+t); lines.append(t)
def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if p and unreal.EditorAssetLibrary.does_asset_exist(p) else None
def apply(a, mat):
    if not mat: return
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break
def bounds_r(mesh):
    try:
        box=mesh.get_bounding_box(); e=box.max-box.min
        return max(abs(e.x),abs(e.y),abs(e.z))
    except Exception: return 100.0

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log(str(e))

rock=load(MAT+"/M_Tideborn_RockShore") or load(MAT+"/M_Tideborn_RockBoulder")
bark=load(MAT+"/M_Tideborn_Bark")
water=load(MAT+"/M_Tideborn_WaterSimple")
boulder=load(MESH+"/boulder_01_1k"); stump=load(MESH+"/dead_tree_trunk_1k")
ox,oy,oz=1000.0,1000.0,100.0
rng=random.Random(3)
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Ensure water exists and is large
has_shallow=False; has_ocean=False
for a in actors():
    lab=label(a)
    if "Shallows" in lab:
        a.set_actor_location(unreal.Vector(ox, oy-600, oz-10), False, True)
        a.set_actor_scale3d(unreal.Vector(140, 80, 1)); apply(a, water); has_shallow=True
    if lab.endswith("Ocean") or lab=="TidebornEnv_Ocean":
        a.set_actor_location(unreal.Vector(ox, oy-1400, oz-20), False, True)
        a.set_actor_scale3d(unreal.Vector(190, 120, 1)); apply(a, water); has_ocean=True
log("water shallow=%s ocean=%s"%(has_shallow, has_ocean))

# Add close framing rocks IN camera frustum (verify cam ~1080,1160 looking -Y)
# Left cluster x~700-850, right x~1250-1450, y~900..400
added=0
if boulder and rock:
    near=[
        (ox-280, oy+40, 1.4),(ox-320, oy-120, 1.3),(ox-360, oy-280, 1.35),(ox-400, oy-450, 1.5),
        (ox+360, oy+60, 1.4),(ox+400, oy-100, 1.3),(ox+440, oy-260, 1.35),(ox+480, oy-430, 1.5),
        (ox-220, oy-600, 1.2),(ox+300, oy-580, 1.2),
    ]
    for i,(x,y,scmul) in enumerate(near):
        r=bounds_r(boulder)
        sc=max(0.5, min(380.0/max(r,1.0), 2.5))*scmul
        a=sub.spawn_actor_from_object(boulder, unreal.Vector(x,y,oz), unreal.Rotator(pitch=0,yaw=rng.uniform(0,360),roll=0))
        if a:
            a.set_actor_scale3d(unreal.Vector(sc,sc,sc)); a.set_actor_label("TidebornEnv_Boulder_near_%02d"%i); apply(a, rock); added+=1
if stump and bark:
    for i,(x,y) in enumerate(((ox-260, oy-40),(ox+340, oy-20),(ox-300, oy-350),(ox+380, oy-330))):
        a=sub.spawn_actor_from_object(stump, unreal.Vector(x,y,oz+10), unreal.Rotator(pitch=0,yaw=rng.uniform(0,360),roll=0))
        if a:
            a.set_actor_scale3d(unreal.Vector(1.1,1.1,1.1)); a.set_actor_label("TidebornEnv_Trunk_near_%02d"%i); apply(a, bark); added+=1
log("added=%d"%added)

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8")
