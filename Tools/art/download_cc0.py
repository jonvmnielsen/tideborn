import json, urllib.request, zipfile, pathlib, ssl
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\RawArt\CC0")
tex = ROOT / "textures"
hdri = ROOT / "hdri"
models = ROOT / "models"
man = ROOT / "manifest"
for p in (tex, hdri, models, man):
    p.mkdir(parents=True, exist_ok=True)
ctx = ssl.create_default_context()
UA = {"User-Agent": "TidebornArtBot/1.0"}

def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        return json.load(r)

def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        print("skip exists", dest)
        return dest.stat().st_size
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=ctx, timeout=600) as r, open(dest, "wb") as f:
        while True:
            c = r.read(262144)
            if not c: break
            f.write(c)
    print("got", dest.name, dest.stat().st_size)
    return dest.stat().st_size

# Poly Haven textures
ph = ["rock_boulder_dry","rock_face","sand_01","bark_brown_02","wood_table_001","coast_sand_rocks_02","aerial_grass_rock"]
for tid in ph:
    files = get_json(f"https://api.polyhaven.com/files/{tid}")
    out = tex / f"PH_{tid}"
    out.mkdir(exist_ok=True)
    for map_name, res_dict in files.items():
        if map_name in ("Blend","gltf","Arm") or not isinstance(res_dict, dict):
            continue
        url = None
        for res in ("2k","1k"):
            formats = res_dict.get(res)
            if not isinstance(formats, dict):
                continue
            for fmt in ("jpg","png"):
                info = formats.get(fmt)
                if isinstance(info, dict) and "url" in info:
                    url = info["url"]; break
            if url: break
        if not url: continue
        ext = url.split(".")[-1].split("?")[0]
        download(url, out / f"{tid}_{map_name}.{ext}")

# HDRI
hdris = get_json("https://api.polyhaven.com/assets?t=hdris")
hid = None
for p in ["industrial_sunset_puresky","kloppenheim_06_puresky","syferfontein"]:
    m = [k for k in hdris if p in k.lower()]
    if m: hid = m[0]; break
files = get_json(f"https://api.polyhaven.com/files/{hid}")
node = files.get("hdri", files)
url = node["2k"]["hdr"]["url"]
download(url, hdri / f"PH_{hid}.hdr")

# ambientCG
for aid in ["Rock023","Wood062","Ground037","Bark001"]:
    meta = get_json(f"https://ambientcg.com/api/v2/full_json?id={aid}&include=downloadData")
    assets = meta.get("foundAssets") or []
    if not assets:
        print("empty", aid); continue
    url = None
    for folder in (assets[0].get("downloadFolders") or {}).values():
        zips = (folder.get("downloadFiletypeCategories") or {}).get("zip", {}).get("downloads") or []
        zips = sorted(zips, key=lambda d: (0 if "2K-JPG" in str(d.get("attribute","")) else 1))
        for d in zips:
            url = d.get("downloadLink") or d.get("fullDownloadPath")
            if url: break
        if url: break
    if not url:
        url = f"https://ambientcg.com/get?file={aid}_2K-JPG.zip"
    zpath = tex / f"ACG_{aid}.zip"
    download(url, zpath)
    out = tex / f"ACG_{aid}"
    out.mkdir(exist_ok=True)
    with zipfile.ZipFile(zpath) as zf:
        zf.extractall(out)

# Models FBX
for mid in ["coast_land_rocks_02","coast_land_rocks_03","boulder_01","dead_tree_trunk"]:
    files = get_json(f"https://api.polyhaven.com/files/{mid}")
    if "fbx" in files and "1k" in files["fbx"]:
        url = files["fbx"]["1k"]["fbx"]["url"]
        download(url, models / f"{mid}_1k.fbx")
    if "gltf" in files and "1k" in files["gltf"]:
        url = files["gltf"]["1k"]["gltf"]["url"]
        dest = models / f"{mid}_1k.gltf.zip"
        download(url, dest)
        try:
            with zipfile.ZipFile(dest) as zf:
                zf.extractall(models / mid)
        except Exception as e:
            print("gltf unzip", mid, e)

(man / "FREE_ASSETS.md").write_text("CC0 shore pack downloaded on Jon PC.\n", encoding="utf-8")
print("ALL DONE")