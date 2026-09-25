import bpy, math
from mathutils import Vector, noise

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Wider/deeper ramp: ~55m x 14m in cm; ~1.0m drop land(+Y)->water(-Y)
sx, sy = 5500.0, 1400.0
res_x, res_y = 48, 20

bpy.ops.mesh.primitive_grid_add(x_subdivisions=res_x, y_subdivisions=res_y, size=1)
ramp = bpy.context.active_object
ramp.name = "SM_TidebornSandRamp"
ramp.scale = (sx, sy, 1.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

for v in ramp.data.vertices:
    x, y, z = v.co
    t = 0.5 - (y / sy)  # 0 land (+Y), 1 water (-Y)
    t = max(0.0, min(1.0, t))
    wave = 0.15 * math.sin(x * 0.0035) + 0.10 * math.sin(x * 0.008 + 1.7)
    t2 = max(0.0, min(1.0, t + wave * t * 0.5))
    # ~100cm drop (stronger readable slope)
    h = -100.0 * (t2 * t2 * (3.0 - 2.0 * t2))  # smoothstep-ish
    n1 = noise.noise(Vector((x * 0.0025, y * 0.0025, 0.4))) * 6.0
    v.co.z = h + n1 * t2
    edge = abs(x) / (sx * 0.5)
    if edge > 0.90:
        v.co.z *= max(0.0, 1.0 - (edge - 0.90) / 0.10)

bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")

out = r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\export\SM_TidebornSandRamp.fbx"
bpy.ops.object.select_all(action="DESELECT")
ramp.select_set(True)
bpy.context.view_layer.objects.active = ramp
bpy.ops.export_scene.fbx(
    filepath=out, use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
    mesh_smooth_type="FACE", global_scale=1.0,
)
print("exported", out, "cm", sx, sy, "drop~100cm")
print("DONE sand ramp 55x14 strong slope")
