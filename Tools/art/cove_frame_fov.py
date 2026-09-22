# -*- coding: utf-8 -*-
"""Frame the cove in camera: rocks in FOV, darker rock mat from RockShore, denser beach."""
from __future__ import annotations
import math, pathlib, random, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_frame_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
TEX = "/Game/Tideborn/Art/Textures"
MESH = "/Game/Tideborn/Art/Meshes"
lines=[]
C={"props":0,"destroyed":0}

def log(m):
    t=str(m); unreal.log("[Frame] "+t); lines.append(t)

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

def find_tex(folder, keys):
    base=TEX+"/"+folder
    if not unreal.EditorAssetLibrary.does_directory_exist(base): return None
    for ap in unreal.EditorAssetLibrary.list_assets(base, recursive=False):
        name=ap.split(".")[-1].lower()
        for k in keys:
            if k.lower() in name: return ap
    return None

def make_dark_rock():
    """Diffuse-only rock from RockShore / RockACG — darker coastal look."""
    name="M_Tideborn_RockShore"
    path=MAT+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel=unreal.MaterialEditingLibrary
    folder="RockShore"
    bc=load(find_tex(folder, ["Diffuse","Color"]))
    if not bc:
        folder="RockACG"; bc=load(find_tex(folder, ["Diffuse","Color"]))
    rough=load(find_tex(folder, ["Rough","roughness"]))
    uv=mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 0)
    mul=mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -550, 0)
    sc=mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 60)
    sc.set_editor_property("r", 2.0)
    mel.connect_material_expressions(uv, "", mul, "A")
    mel.connect_material_expressions(sc, "", mul, "B")
    if bc:
        ts=mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, -80)
        ts.set_editor_property("texture", bc)
        mel.connect_material_expressions(mul, "", ts, "UVs")
        # darken via multiply
        dark=mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 40)
        dark.set_editor_property("constant", unreal.LinearColor(0.55, 0.55, 0.55, 1.0))
        m2=mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -200, -40)
        mel.connect_material_expressions(ts, "RGB", m2, "A")
        mel.connect_material_expressions(dark, "", m2, "B")
        mel.connect_material_property(m2, "", unreal.MaterialProperty.MP_BASE_COLOR)
    if rough:
        ts=mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, 160)
        ts.set_editor_property("texture", rough)
        try: ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        except Exception: pass
        mel.connect_material_expressions(mul, "", ts, "UVs")
        mel.connect_material_property(ts, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("dark rock mat")
    return mat

def apply(a, mat):
    if not mat: return
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        try: comp.set_editor_property("override_materials", [mat]*8)
        except Exception: pass
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break

def bake(path, mat):
    mesh=load(path)
    if not mesh or not mat: return
    try:
        existing=list(mesh.get_editor_property("static_materials") or [])
        n=max(1,len(existing))
        slots=[]
        for _ in range(n):
            s=unreal.StaticMaterial(); s.set_editor_property("material_interface", mat); slots.append(s)
        mesh.set_editor_property("static_materials", slots)
        unreal.EditorAssetLibrary.save_asset(path)
        log("bake "+path)
    except Exception as e:
        log("bake fail "+str(e))

def bounds_r(mesh):
    try:
        box=mesh.get_bounding_box(); e=box.max-box.min
        return max(abs(e.x),abs(e.y),abs(e.z))
    except Exception: return 100.0

def spawn(mesh, loc, yaw, scale, lab, mat):
    a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_object(
        mesh, loc, unreal.Rotator(pitch=0.0, yaw=float(yaw), roll=0.0))
    if not a: return None
    a.set_actor_scale3d(scale); a.set_actor_label(lab); apply(a, mat); return a

try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log("load "+str(e))

# wipe existing env props (keep sand/ground/water planes)
for a in list(actors()):
    lab=label(a)
    if lab.startswith("TidebornEnv_Boulder") or lab.startswith("TidebornEnv_Trunk") or lab.startswith("TidebornEnv_Stone"):
        try:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
            C["destroyed"]+=1
        except Exception: pass

rock=make_dark_rock()
bark=load(MAT+"/M_Tideborn_Bark")
sand=load(MAT+"/M_Tideborn_Sand")
ground=load(MAT+"/M_Tideborn_Ground")
water=load(MAT+"/M_Tideborn_WaterSimple")
creature=load(MAT+"/M_Tideborn_CreatureSolid")
gate=load(MAT+"/M_Tideborn_GateSolid")

boulder=load(MESH+"/boulder_01_1k")
stump=load(MESH+"/dead_tree_trunk_1k")
bake(MESH+"/boulder_01_1k", rock)
boulder=load(MESH+"/boulder_01_1k")

ox,oy,oz=1000.0,1000.0,100.0
# Camera will be ~ (1100, 1070, 250) looking -Y.
# Place rocks IN frustum: x 500-900 left, 1200-1700 right, y 200-950 ahead
rng=random.Random(99)
spots=[]
# left arm (in view)
for i in range(6):
    spots.append((ox-350+i*35, oy-50-i*120, "Boulder", 1.1))
# right arm
for i in range(6):
    spots.append((ox+450+i*40, oy-30-i*115, "Boulder", 1.1))
# near foreground framing
spots.append((ox-280, oy+20, "Boulder", 1.3))
spots.append((ox+400, oy+40, "Boulder", 1.25))
spots.append((ox-180, oy-200, "Boulder", 0.95))
spots.append((ox+320, oy-220, "Boulder", 1.0))
# mid distance clusters
spots.append((ox-420, oy-400, "Boulder", 1.4))
spots.append((ox+520, oy-380, "Boulder", 1.35))
spots.append((ox+50, oy-550, "Boulder", 1.2))
# driftwood on sand corridor
for i in range(5):
    spots.append((ox-80+i*90, oy-180-i*40, "Trunk", 0.85))

for i,(x,y,kind,scmul) in enumerate(spots):
    mesh = boulder if kind=="Boulder" else stump
    mat = rock if kind=="Boulder" else bark
    if not mesh: continue
    r=bounds_r(mesh)
    sc=max(0.45, min(380.0/max(r,1.0), 2.4))*scmul*rng.uniform(0.9,1.08)
    if spawn(mesh, unreal.Vector(x+rng.uniform(-20,20), y+rng.uniform(-20,20), oz),
             rng.uniform(0,360), unreal.Vector(sc,sc,sc), "TidebornEnv_%s_%02d"%(kind,i), mat):
        C["props"]+=1

# gameplay off center corridor but still in world
for a in actors():
    lab=label(a); cn=cname(a)
    if "PlayerStart" in cn or lab=="PlayerStart":
        a.set_actor_location(unreal.Vector(ox+100, oy+80, oz+95), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0.0,yaw=-90.0,roll=0.0), False)
    if "Kelp" in lab:
        a.set_actor_location(unreal.Vector(ox-500, oy-100, oz+40), False, True); apply(a, creature)
    if "Burr" in lab or "Hound" in lab:
        a.set_actor_location(unreal.Vector(ox+700, oy+50, oz+50), False, True); apply(a, creature)
    if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
        a.set_actor_location(unreal.Vector(ox+80, oy+1200, oz+90), False, True); apply(a, gate)
    if "Gather" in lab and "Stone" in lab:
        a.set_actor_location(unreal.Vector(ox+380, oy+50, oz+30), False, True); apply(a, rock)
    if lab.startswith("TidebornEnv_Sand"): apply(a, sand)
    elif lab.startswith("TidebornEnv_Ground"): apply(a, ground)
    elif "Ocean" in lab or "Shallows" in lab: apply(a, water)
for i,a in enumerate([a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]):
    a.set_actor_location(unreal.Vector(ox+300+i*120, oy+30, oz+30), False, True)
    apply(a, bark)

for a in actors():
    if "DirectionalLight" in cname(a):
        try:
            a.set_editor_property("intensity", 3.8)
            a.set_editor_property("light_color", unreal.LinearColor(1.0, 0.9, 0.75, 1.0))
            a.set_actor_rotation(unreal.Rotator(pitch=-40.0, yaw=30.0, roll=0.0), False)
        except Exception: pass
    if "SkyLight" in cname(a):
        try: a.set_editor_property("intensity", 0.9)
        except Exception: pass
    if "ExponentialHeightFog" in cname(a):
        try: a.set_editor_property("fog_density", 0.025)
        except Exception: pass

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception: pass

lines.append("props=%d destroyed=%d DONE"% (C["props"], C["destroyed"]))
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
log("DONE")
