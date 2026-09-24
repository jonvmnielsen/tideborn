# -*- coding: utf-8 -*-
"""HARD FIX: non-overlapping shore bands; sand ABOVE water; clear center corridor."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT=ROOT/"Tools"/"art"/"cove_shore_hardfix_result.txt"
MAT="/Game/Tideborn/Art/Materials"
MAP="/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[HardFix] "+t); lines.append(t)
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
        try: comp.modify()
        except Exception: pass
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break
def set_plane(a, x,y,z, sx,sy, mat, name):
    try: a.modify()
    except Exception: pass
    a.set_actor_location(unreal.Vector(float(x),float(y),float(z)), False, True)
    a.set_actor_scale3d(unreal.Vector(float(sx), float(sy), 1.0))
    a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0), False)
    # also force root component transform (sticks better on some UE builds)
    try:
        root=a.root_component
        if root:
            root.modify()
            root.set_world_location(unreal.Vector(float(x),float(y),float(z)), False, False, True)
            root.set_world_scale3d(unreal.Vector(float(sx), float(sy), 1.0))
            root.set_world_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0), False, False, True)
    except Exception as e:
        log("root xf warn %s: %s"%(name,e))
    apply(a, mat)
    try: a.mark_package_dirty()
    except Exception: pass
    loc=a.get_actor_location(); sc=a.get_actor_scale3d()
    hy=50.0*sc.y; hx=50.0*sc.x
    log("%s -> loc=(%.0f,%.0f,%.0f) sc=(%.1f,%.1f) X[%.0f..%.0f] Y[%.0f..%.0f]"%(
        name, loc.x,loc.y,loc.z, sc.x,sc.y, loc.x-hx,loc.x+hx, loc.y-hy,loc.y+hy))

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load "+str(e))

sand=load(MAT+"/M_Tideborn_Sand")
water=load(MAT+"/M_Tideborn_WaterOpaque") or load(MAT+"/M_Tideborn_WaterSimple")
ground=load(MAT+"/M_Tideborn_Ground") or sand
ox = 1000.0

# Plane half-extent = 50 * scale
# Sand ABOVE water (higher Z) so overlaps never paint blue under feet.
# Sand:   loc=(1000,1500,106) sc=(45,18) -> Y 600..2400
# Shallows: loc=(1000,250,100) sc=(55,7)  -> Y -100..600, Z BELOW sand
# Ocean:  loc=(1000,-900,99)  sc=(70,18) -> Y -1800..0
# Ground: loc=(1000,2800,105) sc=(45,16) -> Y 2000..3600

found={}
for a in actors():
    lab=label(a)
    if lab in ("TidebornEnv_SandBase","TidebornEnv_Shallows","TidebornEnv_Ocean","TidebornEnv_Ground"):
        found[lab]=a
log("found planes: "+",".join(sorted(found.keys())) or "NONE")

if "TidebornEnv_SandBase" in found:
    set_plane(found["TidebornEnv_SandBase"], ox, 1500, 106, 45, 18, sand, "SandBase")
else:
    log("MISSING SandBase")

if "TidebornEnv_Shallows" in found:
    set_plane(found["TidebornEnv_Shallows"], ox, 250, 100, 55, 7, water, "Shallows")
else:
    log("MISSING Shallows")

if "TidebornEnv_Ocean" in found:
    set_plane(found["TidebornEnv_Ocean"], ox, -900, 99, 70, 18, water, "Ocean")
else:
    log("MISSING Ocean")

if "TidebornEnv_Ground" in found:
    set_plane(found["TidebornEnv_Ground"], ox, 2800, 105, 45, 16, ground, "Ground")
else:
    log("MISSING Ground")

# Push Boulder/Trunk props out of center corridor
cleared=0
for a in actors():
    lab=label(a)
    if not lab.startswith("TidebornEnv_"): continue
    if "Boulder" not in lab and "Trunk" not in lab and "Rock" not in lab: continue
    loc=a.get_actor_location()
    if 820 <= loc.x <= 1180 and 400 <= loc.y <= 2000:
        try: a.modify()
        except Exception: pass
        nx = 650.0 if loc.x < 1000 else 1350.0
        a.set_actor_location(unreal.Vector(nx, loc.y, loc.z), False, True)
        try: a.mark_package_dirty()
        except Exception: pass
        cleared += 1
log("pushed %d props out of center corridor"%cleared)

# PlayerStart on sand facing ocean (-Y)
for a in actors():
    cn=a.get_class().get_name() if a.get_class() else ""
    if "PlayerStart" in cn or label(a)=="PlayerStart":
        try: a.modify()
        except Exception: pass
        a.set_actor_location(unreal.Vector(1050.0, 1600.0, 210.0), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0), False)
        try: a.mark_package_dirty()
        except Exception: pass
        log("PlayerStart @ (1050,1600,210) yaw=-90")

# Gameplay off beauty sightline
for a in actors():
    lab=label(a)
    try: a.modify()
    except Exception: pass
    if lab=="Tideborn_P2_ShoreGate":
        a.set_actor_location(unreal.Vector(1100, 2400, 190), False, True)
        log("ShoreGate -> (1100,2400,190)")
    elif lab=="Tideborn_P2_KelpBack":
        a.set_actor_location(unreal.Vector(480, 900, 140), False, True)
        log("KelpBack -> (480,900,140)")
    elif lab=="Tideborn_P2_BurrHound":
        a.set_actor_location(unreal.Vector(1600, 1800, 150), False, True)
        log("BurrHound -> (1600,1800,150)")
    elif "Gather" in lab:
        loc=a.get_actor_location()
        a.set_actor_location(unreal.Vector(max(loc.x, 1300), max(loc.y, 1700), 130), False, True)
        log("Gather %s nudged"%lab)
    try: a.mark_package_dirty()
    except Exception: pass

# Re-read and confirm BEFORE save
for a in actors():
    lab=label(a)
    if lab in ("TidebornEnv_SandBase","TidebornEnv_Shallows","TidebornEnv_Ocean","TidebornEnv_Ground"):
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        hy=50*sc.y
        log("CONFIRM %s Z=%.0f Y[%.0f..%.0f] scY=%.1f scX=%.1f"%(lab, loc.z, loc.y-hy, loc.y+hy, sc.y, sc.x))

# Save aggressively
saved=False
try:
    ok=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("LevelEditorSubsystem.save_current_level -> %s"%ok)
    saved=True
except Exception as e:
    log("LES save: "+str(e))
try:
    ok=unreal.EditorLevelLibrary.save_current_level()
    log("EditorLevelLibrary.save_current_level -> %s"%ok)
    saved=True
except Exception as e:
    log("ELL save: "+str(e))
try:
    n=unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("save_dirty_packages -> %s"%n)
except Exception as e:
    log("save pkg: "+str(e))
try:
    ok=unreal.EditorAssetLibrary.save_asset(MAP)
    log("save_asset map -> %s"%ok)
except Exception as e:
    log("save_asset: "+str(e))

RESULT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8")
log("DONE saved=%s"%saved)
