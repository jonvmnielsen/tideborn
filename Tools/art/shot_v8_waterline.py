# -*- coding: utf-8 -*-
import time, pathlib, shutil, unreal
NAME='V8_Waterline_20260925_205705'
LOC=(1050, 750, 160)
ROT=(-12, -90, 0)
ROOT = pathlib.Path(r'C:\Users\User\Desktop\AI\Grok\Tideborn')
SHOT = ROOT / 'Saved' / 'Screenshots' / 'WindowsEditor'
SHOT.mkdir(parents=True, exist_ok=True)
target = SHOT / (NAME + '.png')
if target.exists():
    try: target.unlink()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.load_map('/Game/ThirdPerson/Maps/ThirdPersonMap')
except Exception as e: unreal.log(str(e))
for cmd in ('r.SkyAtmosphere 1','r.VolumetricCloud 1','r.Fog 1','ShowFlag.Atmosphere 1','ShowFlag.Fog 1','ShowFlag.Cloud 1','ShowFlag.ModeWidgets 0','ShowFlag.Selection 0','r.DefaultFeature.AutoExposure 0','r.ScreenPercentage 100'):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
try:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        cn = a.get_class().get_name() if a.get_class() else ''
        if 'SkyLight' in cn:
            for c in a.get_components_by_class(unreal.SkyLightComponent):
                try: c.recapture_sky()
                except Exception: pass
except Exception: pass
time.sleep(14)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(*LOC), unreal.Rotator(pitch=ROT[0], yaw=ROT[1], roll=ROT[2]))
except Exception as e: unreal.log('cam '+str(e))
time.sleep(5)
try: unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,NAME)
except Exception as e: unreal.log('auto '+str(e))
try: unreal.SystemLibrary.execute_console_command(None,'HighResShot 1920x1080')
except Exception: pass
ok=False
for i in range(150):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size > 50000:
        ok=True; break
time.sleep(3)
dst = ROOT/'Tools'/'art'/'shots_v8'/(NAME+'.png')
dst.parent.mkdir(parents=True, exist_ok=True)
if target.exists():
    try:
        shutil.copy2(str(target), str(dst))
        shutil.copy2(str(target), str(dst.parent/('V8_Waterline.png')))
    except Exception as e: unreal.log('copy '+str(e))
pathlib.Path(str(ROOT/'Tools'/'art'/('_shot_done_v8_Waterline.txt'))).write_text(
    'name=%s ok=%s size=%s\n'%(NAME, ok, target.stat().st_size if target.exists() else 0), encoding='utf-8')
unreal.log('[V8Shot] end %s ok=%s'%(NAME,ok))


