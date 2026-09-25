import bpy, math
from mathutils import Vector, noise

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Flat strip ~50m wide (X) x ~12m deep (Y), cm units. Jagged +Y edge (water-facing in our layout is -Y / lower Y).
# Place so jagged edge faces water (toward -Y / ocean).
sx, sy = 5000.0, 1200.0
res_x, res_y = 64, 16

bpy.ops.mesh.primitive_grid_add(x_subdivisions=res_x, y_subdivisions=res_y, size=1)
edge = bpy.context.active_object
edge.name = "SM_TidebornShoreEdge"
edge.scale = (sx, sy, 1.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Water-facing edge is -Y (min Y). Displace that edge only with noise for irregular silhouette.
for v in edge.data.vertices:
    x, y, z = v.co
    # y in [-sy/2, +sy/2]; water edge at y ~ -sy/2
    t_water = max(0.0, min(1.0, (-y + sy * 0.15) / (sy * 0.35)))  # 1 near water edge
    n = noise.noise(Vector((x * 0.004, 0.2, 2.1)))
    n2 = noise.noise(Vector((x * 0.012, 1.7, 0.5)))
    jagged = (n * 180.0 + n2 * 70.0) * t_water
    # pull water-edge verts toward -Y irregularly
    v.co.y = y - jagged * 0.55
    # slight slope toward water
    slope = -35.0 * t_water
    micro = noise.noise(Vector((x * 0.006, y * 0.006, 3.3))) * 4.0 * t_water
    v.co.z = slope + micro
    # soft side falloff
    edge_x = abs(x) / (sx * 0.5)
    if edge_x > 0.92:
        v.co.z *= max(0.0, 1.0 - (edge_x - 0.92) / 0.08)

bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")

import os
out_dir = r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\export"
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, "SM_TidebornShoreEdge.fbx")
bpy.ops.object.select_all(action="DESELECT")
edge.select_set(True)
bpy.context.view_layer.objects.active = edge
bpy.ops.export_scene.fbx(
    filepath=out, use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
    mesh_smooth_type="FACE", global_scale=1.0,
)
print("exported", out, "cm", sx, sy)
print("DONE shore edge jagged")
