# -*- coding: utf-8 -*-
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_purge_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
lines = []
def log(m):
    t=str(m); unreal.log("[Purge] "+t); lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except: return ""
def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if unreal.EditorAssetLibrary.does_asset_exist(p) else None

def apply(a, mat):
    if not mat: return
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        try:
            comp.set_editor_property("override_materials", [mat]*8)
        except Exception: pass
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log("load "+str(e))

rock=load(MAT+"/M_Tideborn_RockBoulder"); bark=load(MAT+"/M_Tideborn_Bark")
sand=load(MAT+"/M_Tideborn_Sand"); ground=load(MAT+"/M_Tideborn_Ground")
water=load(MAT+"/M_Tideborn_WaterSimple"); creature=load(MAT+"/M_Tideborn_CreatureSolid")
gate=load(MAT+"/M_Tideborn_GateSolid"); wood=load(MAT+"/M_Tideborn_Wood")

destroyed=0
for a in list(actors()):
    lab = label(a)
    mesh_names=[]
    try:
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            sm=comp.get_editor_property("static_mesh")
            if sm: mesh_names.append(sm.get_name().lower())
    except Exception: pass
    mn=" ".join(mesh_names)
    kill=False
    why=""
    if lab.startswith("TidebornArt_"):
        kill=True; why="old art place"
    if "coast_land_rocks" in mn:
        kill=True; why="coast_land_rocks"
    if kill:
        try:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
            destroyed+=1; log("destroy %s (%s %s)"%(lab, why, mn))
        except Exception as e:
            log("fail "+str(e))

ox,oy,oz=1000.0,1000.0,100.0
for a in actors():
    lab=label(a); cn=cname(a)
    if "PlayerStart" in cn or lab=="PlayerStart":
        a.set_actor_location(unreal.Vector(ox+100, oy+20, oz+95), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0.0,yaw=-90.0,roll=0.0), False)
    if "Kelp" in lab:
        a.set_actor_location(unreal.Vector(ox-560, oy-260, oz+40), False, True); apply(a, creature)
    if "Burr" in lab or "Hound" in lab:
        a.set_actor_location(unreal.Vector(ox+820, oy+180, oz+50), False, True); apply(a, creature)
    if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
        a.set_actor_location(unreal.Vector(ox+80, oy+1300, oz+90), False, True); apply(a, gate)
    if "Gather" in lab and "Stone" in lab:
        a.set_actor_location(unreal.Vector(ox+500, oy+180, oz+30), False, True); apply(a, rock)
    if "Gather" in lab and "Wood" in lab:
        apply(a, bark)
    if lab.startswith("TidebornEnv_Sand"): apply(a, sand)
    elif lab.startswith("TidebornEnv_Ground"): apply(a, ground)
    elif "Ocean" in lab or "Shallows" in lab: apply(a, water)
    elif "Trunk" in lab: apply(a, bark)
    elif "Boulder" in lab: apply(a, rock)

woods=[a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]
for i,a in enumerate(woods):
    a.set_actor_location(unreal.Vector(ox+430+i*140, oy+100, oz+30), False, True)
    apply(a, bark)

# verify dump
log("=== AFTER ===")
for a in actors():
    lab=label(a)
    if not (lab.startswith("Tideborn") or "Player" in cname(a)): continue
    mats=[]
    try:
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            sm=comp.get_editor_property("static_mesh")
            m0=comp.get_material(0)
            mats.append("%s->%s"%(sm.get_name() if sm else "?", m0.get_name() if m0 else "None"))
    except Exception: pass
    log("%s %s"%(lab, mats))

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass
log("destroyed=%d DONE"%destroyed)
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
