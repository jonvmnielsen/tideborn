import unreal
import pathlib

RESULT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\import_meshes_result.txt")
lines = []
FBX_DIR = r"C:\Users\User\Desktop\AI\Grok\Tideborn\RawArt\Meshes"
DEST = "/Game/Tideborn/Meshes"

def log(m):
    unreal.log("[TidebornArt] " + str(m))
    lines.append(str(m))

def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)

def import_fbx(fbx_path, dest_path):
    task = unreal.AssetImportTask()
    task.filename = fbx_path
    task.destination_path = dest_path
    task.automated = True
    task.save = True
    task.replace_existing = True
    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = False
    options.import_materials = True
    options.import_textures = False
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.auto_generate_collision = True
    options.static_mesh_import_data.import_uniform_scale = 100.0  # Blender meters -> UE cm
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.imported_object_paths) if task.imported_object_paths else []

def main():
    ensure_dir(DEST)
    root = pathlib.Path(FBX_DIR)
    for fbx in sorted(root.glob("*.fbx")):
        paths = import_fbx(str(fbx), DEST)
        log(f"{fbx.name} -> {paths}")
    # list destination
    assets = unreal.EditorAssetLibrary.list_assets(DEST, recursive=False)
    log("assets=" + "; ".join(assets))
    RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("DONE")

if __name__ == "__main__":
    main()
