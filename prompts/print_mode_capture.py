import bpy, json
s = bpy.context.scene
area = None
space = None
for a in bpy.context.screen.areas:
    if a.type == 'VIEW_3D':
        area = a
        for sp in a.spaces:
            if sp.type == 'VIEW_3D':
                space = sp
                break
        break
settings = {
    "unit_system": s.unit_settings.system,
    "length_unit": s.unit_settings.length_unit,
    "scale_length": s.unit_settings.scale_length,
}
if space:
    r3d = space.region_3d if hasattr(space, 'region_3d') else None
    settings["clip_start"] = space.clip_start
    settings["clip_end"] = space.clip_end
ts = s.tool_settings
settings["snap"] = ts.use_snap
settings["snap_elements"] = list(ts.snap_elements)
result = json.dumps(settings)
