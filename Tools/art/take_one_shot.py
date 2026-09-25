# -*- coding: utf-8 -*-
"""Take one high-res shot from _shot_cfg_v5.txt. Atmosphere ON. Rotator kwargs."""
import time, pathlib, shutil, unreal
cfg = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_cfg_v5.txt")
raw = cfg.read_text(encoding="utf-8-sig").strip().split("|")
name, loc_s, rot_s = raw[0].strip(), raw[1].strip(), raw[2].strip()
loc = [float(x) for x in loc_s.split(",")]
rot = [float(x) for x in rot_s.split(",")]
SHOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Screenshots\WindowsEditor")
SHOT2 = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Screenshots\Windows")
SHOT.mkdir(parents=True, exist_ok=True)
target = SHOT / (name + ".png")
if target.exists():
    try: target.unlink()
    except Exception: pass
auto = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\AutoScreenshot.png")
if auto.exists():
    try: auto.unlink()
    except Exception: pass
try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e:
    unreal.log("load "+str(e))
# Ensure sky/fog visible for this shot session
for cmd in (
    "r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1",
    "ShowFlag.Atmosphere 1","ShowFlag.Fog 1","ShowFlag.Cloud 1",
    "ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0",
    "ShowFlag.Bounds 0","ShowFlag.Collision 0","ShowFlag.LightRadius 0",
    "r.ScreenPercentage 100",
):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
# Recapture skylight if present
try:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        cn = a.get_class().get_name() if a.get_class() else ""
        if "SkyLight" in cn:
            for c in a.get_components_by_class(unreal.SkyLightComponent):
                try: c.recapture_sky()
                except Exception: pass
except Exception:
    pass
time.sleep(8)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(loc[0], loc[1], loc[2]),
        unreal.Rotator(pitch=rot[0], yaw=rot[1], roll=rot[2]),
    )
except Exception as e:
    unreal.log("cam "+str(e))
unreal.log("[Shot] begin "+name)
try:
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, name)
except Exception as e:
    unreal.log("auto fail "+str(e))
try:
    unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
except Exception as e:
    unreal.log("hrs fail "+str(e))
ok = False
def find_png():
    cands = []
    for d in (SHOT, SHOT2, pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved")):
        if not d.exists(): continue
        for p in d.rglob("*.png"):
            try:
                if p.stat().st_size > 20000:
                    cands.append(p)
            except Exception:
                pass
    cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return cands
for i in range(120):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size > 20000:
        ok = True
        break
    if auto.exists() and auto.stat().st_size > 20000:
        try:
            shutil.copy2(str(auto), str(target))
            ok = True
            break
        except Exception as e:
            unreal.log("copy auto "+str(e))
time.sleep(3.0)
if not ok:
    for p in find_png():
        try:
            shutil.copy2(str(p), str(target))
            if target.exists() and target.stat().st_size > 20000:
                ok = True
                unreal.log("[Shot] rescued from "+str(p))
                break
        except Exception:
            pass
done = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_done.txt")
done.write_text("name=%s ok=%s target=%s auto=%s\n" % (
    name, ok,
    target.stat().st_size if target.exists() else 0,
    auto.stat().st_size if auto.exists() else 0,
), encoding="utf-8")
unreal.log("[Shot] end ok=%s size=%s" % (ok, target.stat().st_size if target.exists() else 0))

