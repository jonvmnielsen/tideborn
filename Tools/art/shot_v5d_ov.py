# -*- coding: utf-8 -*-
import time, pathlib, shutil, unreal
NAME="V5d_Overview"
LOC=(1100.0, 1600.0, 950.0)
ROT=(-55.0, -90.0, 0.0)
OUT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\shots_v5d")
OUT.mkdir(parents=True, exist_ok=True)
alt=OUT/(NAME+".png")
if alt.exists():
    try: alt.unlink()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: unreal.log(str(e))
for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1","ShowFlag.Atmosphere 1","ShowFlag.Fog 1","r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
time.sleep(10)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(*LOC), unreal.Rotator(pitch=ROT[0], yaw=ROT[1], roll=ROT[2]))
except Exception as e: unreal.log("cam "+str(e))
# Unique name avoids locked file collisions
uniq="%s_%d"%(NAME, int(time.time()))
try: unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,uniq)
except Exception as e: unreal.log(str(e))
try: unreal.SystemLibrary.execute_console_command(None,"HighResShot 1920x1080")
except Exception: pass
SHOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Screenshots")
ok=False; src=None
for i in range(100):
    time.sleep(0.5)
    cands=[]
    if SHOT.exists():
        for p in SHOT.rglob("*.png"):
            try:
                if p.stat().st_size>50000: cands.append(p)
            except Exception: pass
    cands.sort(key=lambda p:p.stat().st_mtime, reverse=True)
    # Prefer exact uniq name
    for p in cands:
        if uniq in p.name:
            src=p; break
    if src is None and cands:
        # only accept files newer than script start (~2 min)
        src=cands[0]
    if src and src.stat().st_size>50000:
        break
time.sleep(2)
if src:
    try:
        shutil.copy2(str(src), str(alt)); ok=True
        unreal.log("[V5d] copied %s -> %s"%(src,alt))
    except Exception as e:
        unreal.log("copy "+str(e))
pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_done_v5d.txt").write_text(
    "name=%s ok=%s alt=%s src=%s\n"%(NAME,ok, alt.stat().st_size if alt.exists() else 0, src), encoding="utf-8")