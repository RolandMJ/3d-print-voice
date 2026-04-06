import bpy
import json

scene_data = {"objects": [], "active": None, "selected": [], "total_objects": 0}

to_mm = 1000.0  # Blender units to mm

# Collect all mesh objects
all_objects = []
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
    props = {}
    for key in obj.keys():
        if key.startswith("_"):
            continue
        val = obj[key]
        if isinstance(val, (int, float, str, bool)):
            props[key] = val
    if props:
        entry["properties"] = props
    all_objects.append((obj, entry))

scene_data["total_objects"] = len(all_objects)

# Smart truncation: prioritize active + selected, then include the rest
active_name = bpy.context.active_object.name if bpy.context.active_object else None
selected_names = {o.name for o in bpy.context.selected_objects}
scene_data["active"] = active_name
scene_data["selected"] = list(selected_names)

# Priority: 1) active object, 2) selected objects, 3) rest (alphabetical)
priority = []
rest = []
for obj, entry in all_objects:
    if obj.name == active_name or obj.name in selected_names:
        priority.append(entry)
    else:
        rest.append(entry)

# Always include priority objects, fill remaining slots with rest
max_objects = 50
scene_data["objects"] = priority + rest[:max_objects - len(priority)]
if len(all_objects) > max_objects:
    scene_data["truncated"] = True
    # Add a name-only summary of remaining objects
    remaining = [e["name"] for _, e in all_objects if e not in scene_data["objects"]]
    scene_data["other_objects"] = remaining[:100]

result = json.dumps(scene_data)
