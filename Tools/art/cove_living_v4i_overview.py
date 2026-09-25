# -*- coding: utf-8 -*-
"""v4i: PP color_gain warm + destroy SkyLight + sand emissive max. VERIFY."""
from __future__ import annotations
import pathlib, time, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v4i_overview_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
SHOT_DIR = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
SHOT_NAME = "TidebornCoveOverview"
SHOT_LOC = (1100.0, 2500.0, 900.0)
SHOT_ROT = (-35.0, -90.0, 0.0)

lines = []
def log(m):
    t=str(m); unreal.log("[V4i] "+t); lines.append(t)
def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except: return ""

def make_sand(name):
    path = MAT+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    try: mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except: pass
    base = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    base.set_editor_property("constant", unreal.LinearColor(0.95, 0.78, 0.48, 1.0))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    em = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 120)
    em.set_editor_property("constant", unreal.LinearColor(0.85, 0.62, 0.28, 1.0))  # near-glow warm
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 220)
    r.set_editor_property("r", 0.98)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path, True)
    log("sand glow "+name)
    return mat

def make_lit(name, rgb):
    path = MAT+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 100)
    r.set_editor_property("r", 0.9)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 200)
    e.set_editor_property("constant", unreal.LinearColor(0,0,0,1))
    mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path, True)
    return mat

def force_apply(a, mat):
    if not a or not mat: return
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(16):
            try: comp.set_material(i, mat)
            except: break
        try: comp.set_editor_property("override_materials", [mat]*8)
        except: pass

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load "+str(e))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

sand = make_sand("MI_Tideborn_SandWarm"); make_sand("M_Tideborn_Sand")
wood = make_lit("MI_Tideborn_WoodMuted", (0.40,0.26,0.14))
creature = make_lit("MI_Tideborn_CreatureMuted", (0.48,0.38,0.24))
gate = make_lit("M_Tideborn_GateSolid", (0.36,0.24,0.14))
rock = make_lit("M_Tideborn_RockShore", (0.55,0.50,0.44))
water = make_lit("M_Tideborn_WaterOpaque", (0.18,0.34,0.44))
ground = make_lit("M_Tideborn_Ground", (0.34,0.40,0.22))
bark = make_lit("M_Tideborn_Bark", (0.32,0.18,0.09))

for a in list(actors()):
    lab=label(a); cn=cname(a)
    if lab.startswith("TidebornEnv_WLB_"):
        try: eas.destroy_actor(a)
        except: pass
    # DESTROY SkyLight — major cool ambient
    if "SkyLight" in cn:
        try:
            eas.destroy_actor(a); log("DESTROYED SkyLight")
        except Exception as e:
            log("skylight destroy fail "+str(e))

for a in actors():
    lab=label(a); cn=cname(a)
    if lab in ("TidebornEnv_SandBase","TidebornEnv_SandRamp") or "SandRamp" in lab:
        force_apply(a, sand)
    elif lab=="TidebornEnv_Ground": force_apply(a, ground)
    elif lab in ("TidebornEnv_Ocean","TidebornEnv_Shallows"): force_apply(a, water)
    elif "Gate" in lab: force_apply(a, gate)
    elif "Kelp" in lab or "Burr" in lab or "Hound" in lab: force_apply(a, creature)
    elif "Gather" in lab: force_apply(a, rock if "Stone" in lab else wood)
    elif "Boulder" in lab or "Waterline" in lab: force_apply(a, rock)
    elif "Trunk" in lab: force_apply(a, bark)

    if "DirectionalLight" in cn:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 4.0)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.96, 0.82, 1.0))
            except: pass
            try: c.set_editor_property("indirect_lighting_intensity", 0.5)
            except: pass
            try: c.set_editor_property("shadow_amount", 0.15)
            except: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-50, yaw=10, roll=0), False)
        log("DirLight strong warm")
    if "ExponentialHeightFog" in cn or "SkyAtmosphere" in cn or "VolumetricCloud" in cn:
        try:
            a.set_actor_hidden_in_game(True)
            a.set_is_temporarily_hidden_in_editor(True)
            log("hide "+cn)
        except: pass
    if "PostProcess" in cn or lab=="TidebornEnv_PostProcess":
        try:
            try: a.set_editor_property("unbound", True)
            except: pass
            s = a.get_editor_property("settings")
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 3500.0)
            except: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", 0.8)
            except: pass
            # Force warm color gain (boost R, cut B)
            try:
                s.set_editor_property("override_color_gain", True)
                s.set_editor_property("color_gain", unreal.Vector4(1.55, 1.05, 0.55, 1.0))
            except Exception as e:
                log("gain warn "+str(e))
            try:
                s.set_editor_property("override_color_gamma", True)
                s.set_editor_property("color_gamma", unreal.Vector4(1.05, 1.0, 0.9, 1.0))
            except: pass
            try:
                s.set_editor_property("override_bloom_intensity", True)
                s.set_editor_property("bloom_intensity", 0.0)
            except: pass
            try: a.set_editor_property("settings", s)
            except: pass
            log("PP gain warm R1.55 B0.55 temp3500")
        except Exception as e:
            log("PP "+str(e))

for a in actors():
    if label(a)=="TidebornEnv_SandRamp" or "SandRamp" in label(a):
        a.set_actor_location(unreal.Vector(1000,560,105), False, True)
        a.set_actor_scale3d(unreal.Vector(2.4,1.6,1.4))
        force_apply(a, sand)
    if label(a)=="TidebornEnv_Shallows":
        a.set_actor_location(unreal.Vector(1000,420,100), False, True)
        sc=a.get_actor_scale3d()
        a.set_actor_scale3d(unreal.Vector(max(sc.x,55), 6.5, sc.z))
        force_apply(a, water)

boulder_mesh=None
for a in actors():
    if label(a).startswith("TidebornEnv_Boulder") and "WLB" not in label(a):
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            try: boulder_mesh=comp.get_editor_property("static_mesh")
            except: pass
        if boulder_mesh: break
if boulder_mesh:
    for i,(x,y,z,s,yaw) in enumerate([
        (880,605,101,2.2,-30),(855,650,100,1.9,40),
        (1125,608,101,2.3,20),(1150,660,100,2.0,-55),
        (900,685,100,1.7,10),(1100,635,100,1.8,-20)]):
        a=eas.spawn_actor_from_object(boulder_mesh, unreal.Vector(float(x),float(y),float(z)), unreal.Rotator(0,float(yaw),0))
        if a:
            a.set_actor_label("TidebornEnv_WLB_%02d"%i)
            a.set_actor_scale3d(unreal.Vector(s,s,s*0.85))
            force_apply(a, rock)

for a in actors():
    lab=label(a)
    if lab in ("TidebornEnv_SandBase","TidebornEnv_SandRamp","TidebornEnv_Shallows","TidebornEnv_Ocean","Tideborn_P2_BurrHound","Tideborn_P2_ShoreGate"):
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        mats=[]
        for comp in a.get_components_by_class(unreal.PrimitiveComponent):
            for i in range(2):
                try:
                    m=comp.get_material(i)
                    if m: mats.append(m.get_name())
                except: break
        log("CONFIRM %s Z=%.0f loc=(%.0f,%.0f) sc=(%.1f,%.1f) mats=%s"%(lab,loc.z,loc.x,loc.y,sc.x,sc.y,",".join(mats[:3]) or "-"))

try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except: pass
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except: pass
time.sleep(25)
for cmd in ("r.SkyAtmosphere 0","r.VolumetricCloud 0","r.Fog 0","ShowFlag.Atmosphere 0","ShowFlag.Fog 0","ShowFlag.Cloud 0","ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except: pass
SHOT_DIR.mkdir(parents=True, exist_ok=True)
target=SHOT_DIR/(SHOT_NAME+".png")
if target.exists():
    try: target.unlink()
    except: pass
unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(*SHOT_LOC), unreal.Rotator(pitch=SHOT_ROT[0], yaw=SHOT_ROT[1], roll=SHOT_ROT[2]))
log("SHOT begin "+SHOT_NAME)
unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,SHOT_NAME)
ok=False
for i in range(100):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size>20000:
        ok=True; break
time.sleep(3)
if target.exists() and target.stat().st_size>20000: ok=True
log("SHOT end ok=%s size=%s"%(ok, target.stat().st_size if target.exists() else 0))
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
log("DONE")

