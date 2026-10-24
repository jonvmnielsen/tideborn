import unreal
import pathlib
out = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\key_probe.txt")
lines = []
lines.append("Keys attr: " + str(hasattr(unreal, "Keys")))
if hasattr(unreal, "Keys"):
    lines.append("dir Keys sample: " + ",".join([x for x in dir(unreal.Keys) if not x.startswith("_")][:40]))
    for cand in ["E", "E_Key", "Keyboard_E"]:
        if hasattr(unreal.Keys, cand):
            lines.append("Found Keys." + cand + "=" + str(getattr(unreal.Keys, cand)))
# inspect an existing mapping key
imc = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Input/IMC_Default")
mappings = list(imc.get_editor_property("mappings"))
lines.append("mapping count=" + str(len(mappings)))
for m in mappings[:8]:
    try:
        k = m.get_editor_property("key")
        lines.append("key type=" + str(type(k)) + " repr=" + repr(k) + " str=" + str(k))
        lines.append("key dir sample=" + ",".join([x for x in dir(k) if not x.startswith("_")][:30]))
        break
    except Exception as e:
        lines.append("err " + str(e))
# try construct
for expr in []:
    pass
try:
    k2 = unreal.Key()
    lines.append("Key() works: " + repr(k2))
    for prop in ["key_name", "KeyName"]:
        try:
            k2.set_editor_property(prop, "E")
            lines.append("set " + prop + " ok -> " + str(k2))
        except Exception as e:
            lines.append("set " + prop + " fail " + str(e))
except Exception as e:
    lines.append("Key() fail " + str(e))
out.write_text("\n".join(lines), encoding="utf-8")
unreal.log("[TidebornP0] probe written")
