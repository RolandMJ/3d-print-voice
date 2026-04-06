import bpy
s = bpy.context.scene
s.unit_settings.system = 'METRIC'
s.unit_settings.length_unit = 'MILLIMETERS'
s.unit_settings.scale_length = 0.001
for a in bpy.context.screen.areas:
    if a.type == 'VIEW_3D':
        for sp in a.spaces:
            if sp.type == 'VIEW_3D':
                sp.clip_start = 0.1
                sp.clip_end = 100000
                break
        break
ts = s.tool_settings
ts.use_snap = True
ts.snap_elements = {'INCREMENT'}
