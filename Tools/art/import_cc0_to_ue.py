"""Import CC0 textures/models into Tideborn and build master materials + shore lighting."""
import unreal
import pathlib

RESULT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\import_cc0_result.txt")
lines = []

def log(m):
    unreal.log("[TidebornCC0] " + str(m))
    lines.append(str(m))

SRC = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\RawArt\CC0")
TEX_DST = "/Game/Tideborn/Art/Textures"
MAT_DST = "/Game/Tideborn/Art/Materials"
MESH_DST = "/Game/Tideborn/Art/Meshes"
HDRI_DST = "/Game/Tideborn/Art/HDRI"

def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)

def import_texture(path: pathlib.Path, dest_path: str, srgb: bool):
    task = unreal.AssetImportTask()
    task.filename = str(path)
    task.destination_path = dest_path
    task.automated = True
    task.save = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.imported_object_paths) if task.imported_object_paths else []
    if not imported:
        return None
    asset = unreal.EditorAssetLibrary.load_asset(imported[0])
    if isinstance(asset, unreal.Texture2D):
        asset.set_editor_property("srgb", srgb)
        if not srgb:
            # normal/rough/ao
            try:
                asset.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
            except Exception:
                pass
        unreal.EditorAssetLibrary.save_asset(imported[0])
    return imported[0]

def find_map(folder: pathlib.Path, keywords):
    files = list(folder.rglob("*"))
    for kw in keywords:
        for f in files:
            if f.is_file() and kw.lower() in f.name.lower() and f.suffix.lower() in (".jpg", ".png", ".jpeg", ".tga"):
                return f
    return None

def create_mi(name, base_color, normal, roughness, ao=None):
    """Create a material instance from engine default lit and assign textures via material params.
    Fallback: create a simple Material with TextureSample nodes is heavy in Python —
    use MaterialEditingLibrary on a created material.
    """
    ensure_dir(MAT_DST)
    mat_path = f"{MAT_DST}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
        unreal.EditorAssetLibrary.delete_asset(mat_path)

    # Create material
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFactoryNew()
    mat = asset_tools.create_asset(name, MAT_DST, unreal.Material, factory)
    if not mat:
        log(f"failed create material {name}")
        return None

    # Load textures
    def load_tex(path):
        return unreal.EditorAssetLibrary.load_asset(path) if path else None

    bc = load_tex(base_color)
    nrm = load_tex(normal)
    rough = load_tex(roughness)
    ao_tex = load_tex(ao) if ao else None

    # Use MaterialEditingLibrary
    mel = unreal.MaterialEditingLibrary
    # Create texture samples and connect
    if bc:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, -200)
        ts.texture = bc
        mel.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    if nrm:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, 0)
        ts.texture = nrm
        try:
            ts.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
        except Exception:
            pass
        mel.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_NORMAL)
    if rough:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, 200)
        ts.texture = rough
        try:
            ts.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
        except Exception:
            pass
        # Rough often in R or from ARM G channel — use R
        mel.connect_material_property(ts, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(mat_path)
    log(f"material {mat_path}")
    return mat_path

def import_fbx_static(path: pathlib.Path, dest_path: str):
    task = unreal.AssetImportTask()
    task.filename = str(path)
    task.destination_path = dest_path
    task.automated = True
    task.save = True
    task.replace_existing = True
    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = False
    options.import_materials = True
    options.import_textures = True
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.auto_generate_collision = True
    options.static_mesh_import_data.import_uniform_scale = 1.0
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.imported_object_paths) if task.imported_object_paths else []

def apply_sky_hdri(hdri_asset_path: str):
    # Place or update HDRI backdrop if plugin available; else set on SkyLight cubemap if texture cube
    # Import HDR as texture; for true HDRI sky use HDRIBackdrop actor
    try:
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        # Find DirectionalLight and bump intensity for outdoor feel
        for actor in subsystem.get_all_level_actors():
            name = actor.get_class().get_name()
            if "DirectionalLight" in name:
                # warmer sunset
                try:
                    actor.set_editor_property("intensity", 8.0)
                except Exception:
                    pass
            if "SkyLight" in name:
                try:
                    actor.set_editor_property("intensity", 1.2)
                    actor.set_editor_property("real_time_capture", True)
                except Exception:
                    pass
            if "ExponentialHeightFog" in name:
                try:
                    actor.set_editor_property("fog_density", 0.015)
                except Exception:
                    pass
        log("lighting tweaked (directional/skylight/fog)")
    except Exception as e:
        log(f"lighting tweak fail: {e}")

def place_mesh(asset_path: str, location, scale=(1,1,1), label=""):
    sm = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not sm:
        return None
    loc = unreal.Vector(*location)
    rot = unreal.Rotator(0, 0, 0)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(sm, loc, rot)
    if actor:
        actor.set_actor_scale3d(unreal.Vector(*scale))
        if label:
            actor.set_actor_label(label)
        log(f"placed {label or asset_path} at {location}")
    return actor

def main():
    ensure_dir(TEX_DST)
    ensure_dir(MAT_DST)
    ensure_dir(MESH_DST)
    ensure_dir(HDRI_DST)

    # Import texture sets
    sets = {
        "RockShore": SRC / "textures" / "PH_coast_sand_rocks_02",
        "RockBoulder": SRC / "textures" / "PH_rock_boulder_dry",
        "Sand": SRC / "textures" / "PH_sand_01",
        "Bark": SRC / "textures" / "PH_bark_brown_02",
        "Wood": SRC / "textures" / "PH_wood_table_001",
        "Ground": SRC / "textures" / "ACG_Ground037",
        "WoodACG": SRC / "textures" / "ACG_Wood062",
        "BarkACG": SRC / "textures" / "ACG_Bark001",
        "RockACG": SRC / "textures" / "ACG_Rock023",
    }

    mat_paths = {}
    for set_name, folder in sets.items():
        if not folder.exists():
            log(f"missing set {folder}")
            continue
        dest = f"{TEX_DST}/{set_name}"
        ensure_dir(dest)
        bc = find_map(folder, ["Diffuse", "diff", "Color", "albedo", "BaseColor", "_col"])
        nrm = find_map(folder, ["nor_gl", "NormalGL", "normal", "Nor"])
        rough = find_map(folder, ["Rough", "roughness"])
        ao = find_map(folder, ["AO", "ao", "AmbientOcclusion"])
        # ambientCG naming: Rock023_Color.jpg etc
        if not bc:
            bc = find_map(folder, ["Color", "color"])
        if not nrm:
            nrm = find_map(folder, ["Normal", "normal"])
        log(f"{set_name}: bc={bc} nrm={nrm} rough={rough}")
        bc_p = import_texture(bc, dest, True) if bc else None
        nrm_p = import_texture(nrm, dest, False) if nrm else None
        rough_p = import_texture(rough, dest, False) if rough else None
        ao_p = import_texture(ao, dest, False) if ao else None
        if bc_p:
            mat_paths[set_name] = create_mi(f"M_Tideborn_{set_name}", bc_p, nrm_p, rough_p, ao_p)

    # HDRI texture
    hdri_files = list((SRC / "hdri").rglob("*.hdr")) + list((SRC / "hdri").rglob("*.exr"))
    hdri_files.sort(key=lambda p: ("secluded_beach" not in p.name.lower(), str(p)))
    hdri_path = None
    if hdri_files:
        hdri_path = import_texture(hdri_files[0], HDRI_DST, False)
        log(f"HDRI imported {hdri_path}")
    apply_sky_hdri(hdri_path)

    # Import models
    for fbx in sorted((SRC / "models").rglob("*.fbx")):
        paths = import_fbx_static(fbx, MESH_DST)
        log(f"fbx {fbx.name} -> {paths}")

    # Place a few rocks / stump near PlayerStart for readability
    # Find PlayerStart
    spawn = unreal.Vector(0, 0, 100)
    try:
        for a in unreal.EditorLevelLibrary.get_all_level_actors():
            if "PlayerStart" in a.get_class().get_name() or "PlayerStart" in a.get_actor_label():
                spawn = a.get_actor_location()
                break
    except Exception:
        pass

    # place imported static meshes offset from spawn
    assets = unreal.EditorAssetLibrary.list_assets(MESH_DST, recursive=True)
    offsets = [(400, 200, 0), (600, -100, 0), (800, 150, 0), (500, 400, 0)]
    i = 0
    for ap in assets:
        if not ap.lower().endswith(tuple(x.lower() for x in ["coast_land", "boulder", "dead_tree", "rock"])):
            # place all static meshes we imported
            pass
        if i >= len(offsets):
            break
        # only static mesh assets
        asset = unreal.EditorAssetLibrary.load_asset(ap)
        if not isinstance(asset, unreal.StaticMesh):
            continue
        o = offsets[i]
        loc = (spawn.x + o[0], spawn.y + o[1], spawn.z + o[2])
        place_mesh(ap, loc, (1, 1, 1), f"TidebornArt_{i}")
        i += 1

    # Apply wood material to existing Tideborn foundation meshes in level if possible
    wood = mat_paths.get("Wood") or mat_paths.get("WoodACG") or mat_paths.get("Bark")
    rock = mat_paths.get("RockShore") or mat_paths.get("RockBoulder") or mat_paths.get("RockACG")
    if wood or rock:
        for a in unreal.EditorLevelLibrary.get_all_level_actors():
            label = a.get_actor_label().lower()
            mats = None
            if "foundation" in label or "build" in label:
                mats = wood
            if "gather" in label or "wood" in label or "stump" in label:
                mats = wood
            if "stone" in label or "gate" in label or "rock" in label:
                mats = rock
            if not mats:
                continue
            mat_obj = unreal.EditorAssetLibrary.load_asset(mats)
            for comp in a.get_components_by_class(unreal.StaticMeshComponent):
                try:
                    comp.set_material(0, mat_obj)
                except Exception:
                    pass
            log(f"applied mat to {a.get_actor_label()}")

    unreal.EditorLevelLibrary.save_current_level()
    log("DONE")
    RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
