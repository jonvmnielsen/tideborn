import bpy, math
from mathutils import Vector, noise

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Build directly in centimeters for UE (no ambiguous FBX scale)
# Beach ~ 9000 x 11000 cm
sx, sy = 9000.0, 11000.0
res_x, res_y = 180, 220

bpy.ops.mesh.primitive_grid_add(x_subdivisions=res_x, y_subdivisions=res_y, size=1)
beach = bpy.context.active_object
beach.name = "SM_TidebornBeach"
beach.scale = (sx, sy, 1)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

for v in beach.data.vertices:
    x, y, z = v.co
    nx = x / sx
    ny = y / sy
    # Stronger relief (cm)
    h = (ny + 0.5) * 280.0  # inland rise
    cove = -180.0 * math.exp(-(nx * nx) * 10.0) * max(0.0, 0.6 - ny)
    dunes = 220.0 * math.exp(-((abs(nx) - 0.30) ** 2) * 40) * (0.35 + 0.65 * (ny + 0.5))
    n1 = noise.noise(Vector((x * 0.0015, y * 0.0015, 0.0))) * 55.0
    n2 = noise.noise(Vector((x * 0.004, y * 0.004, 2.2))) * 25.0
    v.co.z = h + cove + dunes + n1 + n2

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')

# Water plane in cm
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -4500, -80))
water = bpy.context.active_object
water.name = "SM_TidebornWater"
water.scale = (12000, 9000, 1)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)

out_beach = r"C:\Users\User\Desktop\AI\Grok\Tideborn\RawArt\CC0\Models\SM_TidebornBeach.fbx"
out_water = r"C:\Users\User\Desktop\AI\Grok\Tideborn\RawArt\CC0\Models\SM_TidebornWater.fbx"

def export(obj, path):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL', axis_forward='-Y', axis_up='Z',
        mesh_smooth_type='FACE', global_scale=1.0,
    )
    print("exported", path)

export(beach, out_beach)
export(water, out_water)
print("DONE cm beach")
