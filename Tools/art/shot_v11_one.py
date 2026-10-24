# -*- coding: utf-8 -*-
import time, pathlib, shutil, unreal, sys
LABEL = sys.argv[1] if len(sys.argv)>1 else 'Verify'
# Unreal ExecutePythonScript does not pass argv; read from cfg file instead
CFG = pathlib.Path(r'C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_cfg_active.txt')
line = CFG.read_text(encoding='utf-8').strip().splitlines()[0]
# format: Name|x,y,z|pitch,yaw,roll
parts = line.split('|')
short = parts[0]
xyz = [float(v) for v in parts[1].split(',')]
pyr = [float(v) for v in parts[2].split(',')]
TS = pathlib.Path(r'C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_v11_ts.txt').read_text(encoding='utf-8').strip()
NAME = short + '_' + TS
ROOT = pathlib.Path(r'C:\Users\User\Desktop\AI\Grok\Tideborn')
SHOT = ROOT / 'Saved' / 'Screenshots' / 'WindowsEditor'
SHOT.mkdir(parents=True, exist_ok=True)
# clear old
for p in SHOT.glob(short + '*.png'):
    try: p.unlink()
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
time.sleep(12)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(xyz[0], xyz[1], xyz[2]),
        unreal.Rotator(pitch=pyr[0], yaw=pyr[1], roll=pyr[2]))
except Exception as e: unreal.log('cam '+str(e))
time.sleep(6)
try: unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,NAME)
except Exception as e: unreal.log('auto '+str(e))
try: unreal.SystemLibrary.execute_console_command(None,'HighResShot 1920x1080')
except Exception: pass
time.sleep(20)
ok=False
final=None
deadline = time.time() + 200
while time.time() < deadline:
    cands = sorted(SHOT.glob(short+'*.png'), key=lambda p: p.stat().st_mtime, reverse=True)
    for c in cands:
        if c.stat().st_size > 50000:
            final=c; ok=True; break
    if ok: break
    # also accept HighResShot generic names written recently
    generics = sorted(SHOT.glob('*.png'), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    for c in generics:
        age = time.time() - c.stat().st_mtime
        if age < 120 and c.stat().st_size > 50000 and short.split('_')[0] in c.name:
            final=c; ok=True; break
    if ok: break
    time.sleep(1)
time.sleep(3)
dst_dir = ROOT/'Tools'/'art'/'shots_v11'
dst_dir.mkdir(parents=True, exist_ok=True)
if final and final.exists():
    try:
        shutil.copy2(str(final), str(dst_dir/(NAME+'.png')))
        shutil.copy2(str(final), str(dst_dir/(short+'.png')))
    except Exception as e: unreal.log('copy '+str(e))
tag = short.replace('V11_','')
pathlib.Path(str(ROOT/'Tools'/'art'/('_shot_done_v11_'+tag+'.txt'))).write_text(
    'name=%s ok=%s size=%s path=%s\n'%(NAME, ok, final.stat().st_size if final and final.exists() else 0, final), encoding='utf-8')
unreal.log('[V11Shot] end %s ok=%s path=%s'%(NAME,ok,final))
