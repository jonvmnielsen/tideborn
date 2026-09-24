# -*- coding: utf-8 -*-
"""One-off Overview shot; avoids locked _shot_cfg.txt."""
import time, pathlib, unreal
name = "TidebornCoveOverview"
loc = [1100.0, 2500.0, 900.0]
rot = [-35.0, -90.0, 0.0]
SHOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Screenshots\WindowsEditor")
SHOT.mkdir(parents=True, exist_ok=True)
target = SHOT / (name + ".png")
# write to alternate if locked
alt = SHOT / (name + "_feel.png")
for p in (target, alt):
    try:
        if p.exists():
            p.unlink()
    except Exception as e:
        unreal.log("unlink %s: %s" % (p, e))
try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e:
    unreal.log("load "+str(e))
for cmd in ("ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0","ShowFlag.Bounds 0","ShowFlag.Collision 0","ShowFlag.LightRadius 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(loc[0], loc[1], loc[2]),
        unreal.Rotator(pitch=rot[0], yaw=rot[1], roll=rot[2]),
    )
except Exception as e:
    unreal.log("cam "+str(e))
unreal.log("[Shot] begin "+name)
try:
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, name + "_feel")
except Exception as e:
    unreal.log("auto fail "+str(e))
try:
    unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
except Exception as e:
    unreal.log("hrs fail "+str(e))
ok = False
auto = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\AutoScreenshot.png")
for i in range(60):
    time.sleep(0.5)
    for cand in (alt, target, auto):
        if cand.exists() and cand.stat().st_size > 20000:
            if cand != alt:
                try:
                    import shutil
                    shutil.copy2(str(cand), str(alt))
                except Exception as e:
                    unreal.log("copy %s: %s" % (cand, e))
            ok = True
            break
    if ok:
        break
done = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_done.txt")
try:
    done.write_text("name=%s ok=%s alt=%s\n" % (name, ok, alt.stat().st_size if alt.exists() else 0), encoding="utf-8")
except Exception as e:
    unreal.log("done write %s" % e)
unreal.log("[Shot] end ok=%s" % ok)
