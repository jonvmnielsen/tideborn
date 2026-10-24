import unreal, pathlib
p = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\bp_api_probe.txt")
names = [n for n in dir(unreal) if "Blueprint" in n or "EdGraph" in n or "K2Node" in n or "Kismet" in n]
p.write_text("\n".join(sorted(names)[:200]), encoding="utf-8")
