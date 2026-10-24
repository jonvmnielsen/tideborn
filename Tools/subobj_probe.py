import unreal, pathlib
out = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\subobj_api.txt")
lines = []
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lines.append("SubobjectDataSubsystem methods:")
for n in sorted(dir(sub)):
    if not n.startswith("_"):
        lines.append(n)
lines.append("---SubobjectDataBlueprintFunctionLibrary---")
for n in sorted(dir(unreal.SubobjectDataBlueprintFunctionLibrary)):
    if not n.startswith("_"):
        lines.append(n)
lines.append("---AddNewSubobjectParams---")
for n in sorted(dir(unreal.AddNewSubobjectParams)):
    if not n.startswith("_"):
        lines.append(n)
out.write_text("\n".join(lines), encoding="utf-8")
