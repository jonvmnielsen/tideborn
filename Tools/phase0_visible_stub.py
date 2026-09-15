import unreal
import pathlib

RESULT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\phase0_visible_stub.txt")

def log(m):
    unreal.log("[TidebornP0] " + str(m))

def main():
    map_path = "/Game/ThirdPerson/Maps/ThirdPersonMap"
    try:
        unreal.EditorLoadingAndSavingUtils.load_map(map_path)
    except Exception as e:
        log("load_map: " + str(e))

    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        label = a.get_actor_label()
        if label in ("Tideborn_InteractStub", "Tideborn_InteractMarker"):
            unreal.EditorLevelLibrary.destroy_actor(a)

    loc = unreal.Vector(350.0, 0.0, 50.0)

    cube = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, loc, unreal.Rotator()
    )
    if not cube:
        raise RuntimeError("Failed to spawn StaticMeshActor")

    cube.set_actor_label("Tideborn_InteractMarker")
    cube.set_actor_scale3d(unreal.Vector(0.6, 0.6, 1.2))

    mesh_comp = cube.static_mesh_component
    cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    if cube_mesh:
        mesh_comp.set_static_mesh(cube_mesh)

    mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
    if mat:
        mesh_comp.set_material(0, mat)

    trigger = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.TriggerBox, loc + unreal.Vector(0, 0, 60), unreal.Rotator()
    )
    if trigger:
        trigger.set_actor_label("Tideborn_InteractStub")
        trigger.set_actor_scale3d(unreal.Vector(1.2, 1.2, 1.5))
        try:
            tags = list(trigger.tags)
            tags.append("TidebornInteract")
            trigger.tags = tags
        except Exception as e:
            log("tags: " + str(e))

    unreal.EditorLevelLibrary.save_current_level()
    log("Visible marker placed at " + str(loc))
    RESULT.write_text("OK visible cube Tideborn_InteractMarker + TriggerBox at ~350,0,50\n", encoding="utf-8")
    log("DONE visible stub")

if __name__ == "__main__":
    main()
