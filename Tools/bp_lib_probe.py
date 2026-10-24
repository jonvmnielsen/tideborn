import unreal, pathlib, inspect
out = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\bp_lib_methods.txt")
lines = []
for name in sorted(dir(unreal.BlueprintEditorLibrary)):
    if name.startswith("_"):
        continue
    lines.append(name)
# Also SubobjectDataSubsystem
lines.append("---SubobjectDataSubsystem---")
try:
    for name in sorted(dir(unreal.SubobjectDataSubsystem)):
        if not name.startswith("_"):
            lines.append(name)
except Exception as e:
    lines.append(str(e))
lines.append("---K2Node sample---")
for name in sorted(dir(unreal)):
    if name.startswith("K2Node") and ("Input" in name or "Enhanced" in name or "Event" in name or "CallFunction" in name or "Print" in name):
        lines.append(name)
out.write_text("\n".join(lines), encoding="utf-8")
