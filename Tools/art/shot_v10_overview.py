# -*- coding: utf-8 -*-
import time, pathlib, unreal
NAME='V10_Overview_20260925_225418'
ROOT = pathlib.Path(r'C:\Users\User\Desktop\AI\Grok\Tideborn')
SHOT = ROOT / 'Saved' / 'Screenshots' / 'WindowsEditor'
target = SHOT / (NAME + '.png')
if target.exists():
    try: target.unlink()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.load_map('/Game/ThirdPerson/Maps/ThirdPersonMap')
except Exception as e: unreal.log(str(e))
for cmd in ('r.SkyAtmosphere 1','r.Fog 1','ShowFlag.Atmosphere 1','ShowFlag.Fog 1','ShowFlag.ModeWidgets 0','r.DefaultFeature.AutoExposure 0'):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
time.sleep(12)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(1000,1200,400), unreal.Rotator(pitch=-25,yaw=-90,roll=0))
except Exception as e: unreal.log(str(e))
time.sleep(5)
try: unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,NAME)
except Exception: pass
try: unreal.SystemLibrary.execute_console_command(None,'HighResShot 1920x1080')
except Exception: pass
time.sleep(15)
for i in range(360):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size>50000: break
time.sleep(5)
cands=sorted(SHOT.glob('V10_Overview_*.png'), key=lambda p:p.stat().st_mtime, reverse=True)
final=cands[0] if cands else None
ok=bool(final and final.stat().st_size>50000)
pathlib.Path(str(ROOT/'Tools'/'art'/'_overview_latest.txt')).write_text(str(final)+'\n'+str(final.stat().st_size if final else 0), encoding='utf-8')
pathlib.Path(str(ROOT/'Tools'/'art'/'_shot_done_v10_Overview.txt')).write_text('name=%s ok=%s path=%s\n'%(NAME,ok,final), encoding='utf-8')
unreal.log('[V10Shot] %s ok=%s final=%s'%(NAME,ok,final))