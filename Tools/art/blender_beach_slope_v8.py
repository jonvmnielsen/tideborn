import bpy, math
from mathutils import Vector, noise

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Gentle beach slope wedge in centimeters for UE:
# ~50m wide (X) x 15m deep (Y), height drop ~100uu toward water (-Y)
sx, sy = 5000.0, 1500.0
res_x, res_y = 40, 24
drop = 100.0  # cm / uu

bpy.ops.mesh.primitive_grid_add(x_subdivisions=res_x, y_subdivisions=res_y, size=1)
slope = bpy.context.active_object
slope.name = "SM_TidebornBeachSlope"
slope.scale = (sx, sy, 1.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

for v in slope.data.vertices:
    x, y, z = v.co
    # t=0 at land (+Y), t=1 at water (-Y)
    t = 0.5 - (y / sy)
    t = max(0.0, min(1.0, t))
    # slight side scallop so waterline isn't a knife edge
    wave = 0.12 * math.sin(x * 0.004) + 0.08 * math.sin(x * 0.009 + 1.3)
    t2 = max(0.0, min(1.0, t + wave * t * 0.45))
    # smoothstep drop toward water
    h = -drop * (t2 * t2 * (3.0 - 2.0 * t2))
    n1 = noise.noise(Vector((x * 0.0025, y * 0.0025, 0.5))) * 5.0
    v.co.z = h + n1 * t2
    edge = abs(x) / (sx * 0.5)
    if edge > 0.90:
        v.co.z *= max(0.0, 1.0 - (edge - 0.90) / 0.10)

bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")

out = r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\export\SM_TidebornBeachSlope.fbx"
bpy.ops.object.select_all(action="DESELECT")
slope.select_set(True)
bpy.context.view_layer.objects.active = slope
bpy.ops.export_scene.fbx(
    filepath=out, use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
    mesh_smooth_type="FACE", global_scale=1.0,
)
print("exported", out, "cm", sx, sy, "drop", drop)
print("DONE beach slope 50x15 drop100")
