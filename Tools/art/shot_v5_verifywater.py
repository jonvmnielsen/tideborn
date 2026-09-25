# -*- coding: utf-8 -*-
"""Hardcoded one-shot. Atmosphere ON. Rotator kwargs."""
import time, pathlib, shutil, unreal
NAME = "TidebornCoveVerifyWater"
LOC = (1050.0, 900.0, 180.0)
ROT = (-8.0, -90.0, 0.0)
SHOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Screenshots\WindowsEditor")
SHOT2 = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Screenshots\Windows")
OUTDIR = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\shots_v5")
OUTDIR.mkdir(parents=True, exist_ok=True)
SHOT.mkdir(parents=True, exist_ok=True)
target = SHOT / (NAME + ".png")
alt = OUTDIR / (NAME + ".png")
auto = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\AutoScreenshot.png")
for p in (target, alt, auto):
    if p.exists():
        try: p.unlink()
        except Exception: pass
try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e:
    unreal.log("load "+str(e))
for cmd in (
    "r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1",
    "ShowFlag.Atmosphere 1","ShowFlag.Fog 1","ShowFlag.Cloud 1",
    "ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0",
    "ShowFlag.Bounds 0","ShowFlag.Collision 0","ShowFlag.LightRadius 0",
    "r.ScreenPercentage 100",
):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
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
        unreal.Vector(LOC[0], LOC[1], LOC[2]),
        unreal.Rotator(pitch=ROT[0], yaw=ROT[1], roll=ROT[2]),
    )
except Exception as e:
    unreal.log("cam "+str(e))
unreal.log("[ShotV5] begin "+NAME)
try:
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, NAME)
except Exception as e:
    unreal.log("auto fail "+str(e))
try:
    unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
except Exception as e:
    unreal.log("hrs fail "+str(e))
ok = False
def find_png():
    cands = []
    for d in (SHOT, SHOT2, OUTDIR, pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved")):
        if not d.exists(): continue
        for p in d.rglob("*.png"):
            try:
                if p.stat().st_size > 20000 and ".bak" not in p.name:
                    cands.append(p)
            except Exception: pass
    cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return cands
for i in range(120):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size > 20000:
        ok = True; break
    if auto.exists() and auto.stat().st_size > 20000:
        try:
            shutil.copy2(str(auto), str(target)); ok = True; break
        except Exception:
            try:
                shutil.copy2(str(auto), str(alt)); ok = True; break
            except Exception as e:
                unreal.log("copy auto "+str(e))
time.sleep(2.0)
# Always copy newest large png to OUTDIR alt path (Tools/art is writable)
src = None
if target.exists() and target.stat().st_size > 20000:
    src = target
elif auto.exists() and auto.stat().st_size > 20000:
    src = auto
else:
    cands = find_png()
    if cands: src = cands[0]
if src:
    try:
        shutil.copy2(str(src), str(alt))
        ok = True
        unreal.log("[ShotV5] wrote alt "+str(alt)+" from "+str(src))
    except Exception as e:
        unreal.log("alt copy fail "+str(e))
done = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_done.txt")
try:
    done.write_text("name=%s ok=%s target=%s alt=%s\n" % (
        NAME, ok,
        target.stat().st_size if target.exists() else 0,
        alt.stat().st_size if alt.exists() else 0,
    ), encoding="utf-8")
except Exception as e:
    unreal.log("done write "+str(e))
unreal.log("[ShotV5] end ok=%s" % ok)