# -*- coding: utf-8 -*-
"""Generate timestamped v9 shot scripts on disk."""
from pathlib import Path
from datetime import datetime

ROOT = Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
ART = ROOT / "Tools" / "art"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
(ART / "_v9_ts.txt").write_text(TS + "\n", encoding="utf-8")

SHOTS = [
    ("Waterline", (1050, 750, 160), (-12, -90, 0)),
    ("Verify", (1050, 1600, 200), (-5, -90, 0)),
    ("Overview", (1000, 1200, 400), (-25, -90, 0)),
    ("Slope", (700, 650, 140), (0, -20, 0)),
]

TEMPLATE = r'''# -*- coding: utf-8 -*-
import time, pathlib, shutil, unreal
NAME={name!r}
LOC={loc}
ROT={rot}
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
SHOT = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
SHOT.mkdir(parents=True, exist_ok=True)
target = SHOT / (NAME + ".png")
if target.exists():
    try: target.unlink()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: unreal.log(str(e))
for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1","ShowFlag.Atmosphere 1","ShowFlag.Fog 1","ShowFlag.Cloud 1","ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","r.DefaultFeature.AutoExposure 0","r.ScreenPercentage 100"):
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
except Exception: pass
time.sleep(14)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(*LOC), unreal.Rotator(pitch=ROT[0], yaw=ROT[1], roll=ROT[2]))
except Exception as e: unreal.log("cam "+str(e))
time.sleep(5)
try: unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,NAME)
except Exception as e: unreal.log("auto "+str(e))
try: unreal.SystemLibrary.execute_console_command(None,"HighResShot 1920x1080")
except Exception: pass
ok=False
for i in range(150):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size > 50000:
        ok=True; break
time.sleep(3)
dst_dir = ROOT/"Tools"/"art"/"shots_v9"
dst_dir.mkdir(parents=True, exist_ok=True)
dst = dst_dir/(NAME+".png")
if target.exists():
    try:
        shutil.copy2(str(target), str(dst))
        short = NAME.split("_20")[0]  # V9_Waterline
        shutil.copy2(str(target), str(dst_dir/(short+".png")))
    except Exception as e: unreal.log("copy "+str(e))
done = "Waterline" if "Waterline" in NAME else ("Verify" if "Verify" in NAME else ("Overview" if "Overview" in NAME else "Slope"))
pathlib.Path(str(ROOT/"Tools"/"art"/("_shot_done_v9_"+done+".txt"))).write_text(
    "name=%s ok=%s size=%s\n"%(NAME, ok, target.stat().st_size if target.exists() else 0), encoding="utf-8")
unreal.log("[V9Shot] end %s ok=%s"%(NAME,ok))
'''

for key, loc, rot in SHOTS:
    name = "V9_%s_%s" % (key, TS)
    script = TEMPLATE.format(name=name, loc=loc, rot=rot)
    path = ART / ("shot_v9_%s.py" % key.lower())
    path.write_text(script, encoding="utf-8")
    print("wrote", path, name)
print("TS", TS)
