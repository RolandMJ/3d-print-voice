import bpy
import json

scene_data = {"objects": [], "active": None, "selected": []}

# Unit info
us = bpy.context.scene.unit_settings
scale = bpy.context.scene.unit_settings.scale_length
to_mm = 1000.0  # Blender units to mm (when scale_length=0.001, multiply by 1000)

for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    d = obj.dimensions
    l = obj.location
    r = obj.rotation_euler
    entry = {
        "name": obj.name,
        "dimensions_mm": [round(d.x * to_mm, 1), round(d.y * to_mm, 1), round(d.z * to_mm, 1)],
        "location_mm": [round(l.x * to_mm, 1), round(l.y * to_mm, 1), round(l.z * to_mm, 1)],
        "rotation_deg": [round(r.x * 57.2958, 1), round(r.y * 57.2958, 1), round(r.z * 57.2958, 1)],
    }
    # Custom properties (parametric data set by previous commands)
    props = {}
    for key in obj.keys():
        if key.startswith("_"):
            continue
        val = obj[key]
        if isinstance(val, (int, float, str, bool)):
            props[key] = val
    if props:
        entry["properties"] = props
    scene_data["objects"].append(entry)

if bpy.context.active_object:
    scene_data["active"] = bpy.context.active_object.name

for obj in bpy.context.selected_objects:
    scene_data["selected"].append(obj.name)

# Limit to 30 objects to avoid context overflow
if len(scene_data["objects"]) > 30:
    scene_data["objects"] = scene_data["objects"][:30]
    scene_data["truncated"] = True

result = json.dumps(scene_data)
