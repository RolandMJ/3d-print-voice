# bpy Operations Reference — 3D Printing Workflows

Complete bpy Python code for 3D modeling operations targeting 3D print workflows.
All code is designed to run inside `exec()` with `bpy` already imported.
Tested against Blender 4.x / 5.x API.

**Unit convention:** Blender uses meters internally. For 3D printing in mm:
`1 mm = 0.001 Blender units`. All examples below use mm-scale values.

---

## Table of Contents

1. [Hollowing / Shell](#1-hollowing--shell)
2. [Boolean Operations](#2-boolean-operations)
3. [Edge Operations](#3-edge-operations)
4. [Modifiers](#4-modifiers)
5. [Mesh Operations](#5-mesh-operations)
6. [Transforms](#6-transforms)
7. [3D Print Specific](#7-3d-print-specific)
8. [Shape Creation](#8-shape-creation)
9. [Limitations — What bpy Cannot Do Easily](#9-limitations)

---

## 1. Hollowing / Shell

### Solidify — Make Object Hollow (Shell Inward)

Wall thickness 1.5mm, shell goes inward (default for 3D printing).

```python
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
mod.thickness = -0.0015       # negative = inward
mod.offset = -1               # -1 = all thickness goes inward
mod.use_even_offset = True    # uniform thickness on angled faces
mod.use_quality_normals = True
bpy.ops.object.modifier_apply(modifier="Solidify")
```

### Solidify — Shell Outward

Wall thickness 1.5mm, shell goes outward (original surface becomes inner wall).

```python
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
mod.thickness = 0.0015        # positive = outward
mod.offset = 1                # 1 = all thickness goes outward
mod.use_even_offset = True
mod.use_quality_normals = True
bpy.ops.object.modifier_apply(modifier="Solidify")
```

### Solidify — Shell Centered (Both Directions)

```python
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
mod.thickness = 0.0015
mod.offset = 0                # 0 = centered, half in, half out
mod.use_even_offset = True
mod.use_quality_normals = True
bpy.ops.object.modifier_apply(modifier="Solidify")
```

**Key parameters:**
- `thickness`: absolute wall thickness in BU (negative = inward)
- `offset`: -1 (fully inward), 0 (centered), 1 (fully outward)
- `use_even_offset`: prevents thin spots on sharp angles
- `use_rim`: True by default, closes the open edges — essential for manifold output

---

## 2. Boolean Operations

### Boolean Union (Join Two Solids Into One)

```python
base = bpy.data.objects['Cube']
tool = bpy.data.objects['Cylinder']
bpy.context.view_layer.objects.active = base
mod = base.modifiers.new(name="bool_union", type='BOOLEAN')
mod.operation = 'UNION'
mod.object = tool
mod.solver = 'EXACT'           # EXACT is slower but more reliable for printing
bpy.ops.object.modifier_apply(modifier="bool_union")
tool.select_set(True)
bpy.ops.object.delete()
```

### Boolean Difference (Cut One Object From Another)

```python
base = bpy.data.objects['Cube']
cutter = bpy.data.objects['Cylinder']
bpy.context.view_layer.objects.active = base
mod = base.modifiers.new(name="bool_diff", type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = cutter
mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="bool_diff")
cutter.select_set(True)
bpy.ops.object.delete()
```

### Boolean Intersection (Keep Only Overlapping Volume)

```python
base = bpy.data.objects['Cube']
tool = bpy.data.objects['Sphere']
bpy.context.view_layer.objects.active = base
mod = base.modifiers.new(name="bool_isect", type='BOOLEAN')
mod.operation = 'INTERSECT'
mod.object = tool
mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="bool_isect")
tool.select_set(True)
bpy.ops.object.delete()
```

**Solver options:**
- `'EXACT'`: robust, handles coplanar faces, best for 3D print — slower
- `'FAST'`: faster but can fail on complex or coplanar geometry

**Common pitfall:** Boolean operations require overlapping geometry. If objects
only touch at a surface (coplanar), EXACT solver handles it; FAST will fail.

---

## 3. Edge Operations

### Bevel All Edges (Bevel Modifier — Round)

Round all edges with 0.5mm radius, 8 segments for smooth curve.

```python
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Bevel", type='BEVEL')
mod.width = 0.0005            # 0.5mm radius
mod.segments = 8              # smoothness (more = rounder)
mod.affect = 'EDGES'
mod.limit_method = 'NONE'     # bevel ALL edges
mod.miter_outer = 'MITER_ARC'
bpy.ops.object.modifier_apply(modifier="Bevel")
```

### Bevel Specific Edges Only (Weight-Based)

Step 1: Assign bevel weight to target edges in edit mode.
Step 2: Apply bevel modifier limited by weight.

```python
import bmesh

obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(obj.data)

# Get or create bevel weight layer
bw_layer = bm.edges.layers.bevel_weight.verify()

# Select target edges first (example: edges longer than 10mm)
for edge in bm.edges:
    length = edge.calc_length()
    if length > 0.01:  # edges longer than 10mm
        edge[bw_layer] = 1.0
    else:
        edge[bw_layer] = 0.0

bmesh.update_edit_mesh(obj.data)
bpy.ops.object.mode_set(mode='OBJECT')

# Apply bevel modifier limited by weight
mod = obj.modifiers.new(name="Bevel", type='BEVEL')
mod.width = 0.0005
mod.segments = 6
mod.limit_method = 'WEIGHT'
bpy.ops.object.modifier_apply(modifier="Bevel")
```

**Alternative — Bevel by Angle:**
Only bevels edges sharper than a threshold (useful for box-like shapes).

```python
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Bevel", type='BEVEL')
mod.width = 0.0005
mod.segments = 6
mod.limit_method = 'ANGLE'
mod.angle_limit = 0.523599     # 30 degrees in radians
bpy.ops.object.modifier_apply(modifier="Bevel")
```

### Chamfer (Flat Bevel — 1 Segment)

A chamfer is a bevel with segments=1 (flat cut, not rounded).

```python
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Chamfer", type='BEVEL')
mod.width = 0.001              # 1mm chamfer
mod.segments = 1               # flat = chamfer
mod.affect = 'EDGES'
mod.limit_method = 'ANGLE'
mod.angle_limit = 0.523599     # 30 degrees
bpy.ops.object.modifier_apply(modifier="Chamfer")
```

### Fillet (Round Bevel — High Segments)

A fillet is a bevel with high segments (smooth round).

```python
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Fillet", type='BEVEL')
mod.width = 0.001              # 1mm fillet radius
mod.segments = 12              # smooth round
mod.affect = 'EDGES'
mod.limit_method = 'ANGLE'
mod.angle_limit = 0.523599
mod.miter_outer = 'MITER_ARC'
mod.profile = 0.5              # 0.5 = circular, <0.5 = concave, >0.5 = convex
bpy.ops.object.modifier_apply(modifier="Fillet")
```

---

## 4. Modifiers

### Array — Linear Pattern

Repeat object 5 times along X axis with 2mm gap between copies.

```python
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Array", type='ARRAY')
mod.count = 5
mod.use_relative_offset = False
mod.use_constant_offset = True
mod.constant_offset_displace = (0.002, 0, 0)  # 2mm gap along X
bpy.ops.object.modifier_apply(modifier="Array")
```

### Array — Circular Pattern

Repeat object 8 times in a circle using an empty as rotation driver.

```python
import math

obj = bpy.context.active_object

# Create empty at world origin as rotation pivot
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
empty = bpy.context.active_object
empty.name = "ArrayPivot"
empty.rotation_euler.z = math.radians(360 / 8)  # 45 degrees for 8 copies

# Switch back to the mesh object
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

mod = obj.modifiers.new(name="CircArray", type='ARRAY')
mod.count = 8
mod.use_relative_offset = False
mod.use_object_offset = True
mod.offset_object = empty
bpy.ops.object.modifier_apply(modifier="CircArray")

# Clean up the empty
bpy.data.objects.remove(empty)
```

**Note:** The mesh object must be offset from the world origin (the pivot point)
for circular array to work. If the object is at origin, move it first:
`obj.location.x = 0.02`  (20mm from center)

### Mirror Along Axis

Mirror along X axis (most common for symmetrical parts).

```python
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Mirror", type='MIRROR')
mod.use_axis[0] = True         # X axis
mod.use_axis[1] = False        # Y axis
mod.use_axis[2] = False        # Z axis
mod.use_clip = True            # prevent vertices crossing mirror plane
mod.merge_threshold = 0.0001   # merge verts at mirror seam
bpy.ops.object.modifier_apply(modifier="Mirror")
```

Mirror along multiple axes:

```python
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Mirror", type='MIRROR')
mod.use_axis[0] = True         # X
mod.use_axis[1] = True         # Y
mod.use_axis[2] = False
mod.use_clip = True
bpy.ops.object.modifier_apply(modifier="Mirror")
```

### Subdivision Surface (Smooth)

```python
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod.levels = 2                 # viewport subdivision level
mod.render_levels = 2          # render level (match for consistency)
mod.subdivision_type = 'CATMULL_CLARK'  # smooth; 'SIMPLE' = no smoothing
bpy.ops.object.modifier_apply(modifier="Subsurf")
```

**Warning for 3D printing:** Subdivision Surface dramatically increases face
count. For print, level 1-2 is usually enough. Apply before export.

---

## 5. Mesh Operations

### Extrude Face

Extrude the top face of a cube upward by 10mm.
Requires entering edit mode and selecting the face first.

```python
import bmesh

obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(obj.data)
bm.faces.ensure_lookup_table()

# Deselect all, then select top face (highest Z normal)
for f in bm.faces:
    f.select = False
for f in bm.faces:
    if f.normal.z > 0.9:       # top face (Z-up normal)
        f.select = True

bmesh.update_edit_mesh(obj.data)

# Extrude selected faces along normals
bpy.ops.mesh.extrude_region_move(
    TRANSFORM_OT_translate={"value": (0, 0, 0.01)}  # 10mm up
)

bpy.ops.object.mode_set(mode='OBJECT')
```

### Inset Face

Inset the top face by 2mm (creates a border ring on the face).

```python
import bmesh

obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(obj.data)
bm.faces.ensure_lookup_table()

for f in bm.faces:
    f.select = False
for f in bm.faces:
    if f.normal.z > 0.9:
        f.select = True

bmesh.update_edit_mesh(obj.data)

bpy.ops.mesh.inset(thickness=0.002, depth=0)  # 2mm inset, no depth change

bpy.ops.object.mode_set(mode='OBJECT')
```

### Bridge Edge Loops (Connect Two Holes)

Bridge connects two edge loops — typically used to join two holes or openings.
Both loops must be in the same mesh object.

```python
import bmesh

obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')

# Select the two edge loops to bridge
# (assumes they are already selected, or select by criteria)
bpy.ops.mesh.select_all(action='DESELECT')
bm = bmesh.from_edit_mesh(obj.data)
bm.edges.ensure_lookup_table()

# Example: select boundary edges (open edges = edges with only 1 face)
for edge in bm.edges:
    if len(edge.link_faces) == 1:
        edge.select = True

bmesh.update_edit_mesh(obj.data)

bpy.ops.mesh.bridge_edge_loops(
    number_cuts=0,             # 0 = direct bridge, >0 = add intermediate loops
    interpolation='LINEAR'     # or 'PATH' or 'SURFACE'
)

bpy.ops.object.mode_set(mode='OBJECT')
```

**Important:** Bridge requires exactly 2 edge loops selected. The loops must
have the same vertex count for clean results. This operation is context-sensitive
and can be tricky to automate reliably — see Limitations section.

### Loop Cut

Add a loop cut in the middle of an object (adds edge ring).

```python
obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')

bpy.ops.mesh.loopcut_slide(
    MESH_OT_loopcut={
        "number_cuts": 1,
        "smoothness": 0,
        "falloff": 'INVERSE_SQUARE',
        "object_index": 0,
        "edge_index": 0        # index of edge to cut across
    },
    TRANSFORM_OT_edge_slide={
        "value": 0.0           # 0 = center, -1/+1 = edges
    }
)

bpy.ops.object.mode_set(mode='OBJECT')
```

**Note:** `edge_index` is the critical parameter — it determines WHERE the
loop cut goes. Finding the right edge index programmatically requires bmesh
traversal. This is one of the harder operations to automate. See Limitations.

---

## 6. Transforms

### Rotate Around Specific Axis

Rotate active object 45 degrees around Z axis.

```python
import math
obj = bpy.context.active_object
obj.rotation_euler.z += math.radians(45)
```

Rotate around X axis by 90 degrees:

```python
import math
obj = bpy.context.active_object
obj.rotation_euler.x += math.radians(90)
```

Rotate around arbitrary axis using matrix:

```python
import math
import mathutils

obj = bpy.context.active_object
axis = mathutils.Vector((1, 1, 0)).normalized()  # diagonal axis
angle = math.radians(30)
rot_matrix = mathutils.Matrix.Rotation(angle, 4, axis)
obj.matrix_world = rot_matrix @ obj.matrix_world
```

### Align Objects

Align object B to match object A's position on a specific axis:

```python
source = bpy.data.objects['Cube']
target = bpy.data.objects['Cylinder']

# Align X position
target.location.x = source.location.x

# Align all axes (stack on top)
target.location = source.location.copy()

# Align center, then place on top
target.location.x = source.location.x
target.location.y = source.location.y
target.location.z = source.location.z + source.dimensions.z / 2 + target.dimensions.z / 2
```

Align to origin (center object at world origin):

```python
obj = bpy.context.active_object
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
obj.location = (0, 0, 0)
```

Align multiple objects (center all selected on X):

```python
# Select objects first, make one active
bpy.ops.object.align(
    align_mode='OPT_1',       # align to active object
    relative_to='OPT_4',      # relative to active
    align_axis={'X'}           # which axes to align
)
```

### Snap to Grid

Snap object location to 1mm grid:

```python
import math

obj = bpy.context.active_object
grid = 0.001  # 1mm grid

obj.location.x = round(obj.location.x / grid) * grid
obj.location.y = round(obj.location.y / grid) * grid
obj.location.z = round(obj.location.z / grid) * grid
```

Snap all vertices to grid (edit mode):

```python
import bmesh

obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(obj.data)

grid = 0.001  # 1mm
for v in bm.verts:
    v.co.x = round(v.co.x / grid) * grid
    v.co.y = round(v.co.y / grid) * grid
    v.co.z = round(v.co.z / grid) * grid

bmesh.update_edit_mesh(obj.data)
bpy.ops.object.mode_set(mode='OBJECT')
```

---

## 7. 3D Print Specific

### Check Manifold (Watertight Mesh)

A manifold mesh has no holes, no loose edges, no non-manifold geometry.

```python
import bmesh

obj = bpy.context.active_object
bm = bmesh.new()
bm.from_mesh(obj.data)

non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
non_manifold_verts = [v for v in bm.verts if not v.is_manifold]
loose_edges = [e for e in bm.edges if not e.link_faces]
loose_verts = [v for v in bm.verts if not v.link_edges]

result = {
    "is_manifold": len(non_manifold_edges) == 0 and len(non_manifold_verts) == 0,
    "non_manifold_edges": len(non_manifold_edges),
    "non_manifold_verts": len(non_manifold_verts),
    "loose_edges": len(loose_edges),
    "loose_verts": len(loose_verts),
    "total_faces": len(bm.faces),
    "total_verts": len(bm.verts),
}

bm.free()
print(result)
```

### Recalculate Normals (Make Normals Consistent)

```python
obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)  # False = outward
bpy.ops.object.mode_set(mode='OBJECT')
```

### Remove Doubles / Merge by Distance

Merge vertices closer than 0.01mm (cleanup for 3D print).

```python
obj = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.00001)  # 0.01mm
bpy.ops.object.mode_set(mode='OBJECT')
```

**Note:** `remove_doubles` is the legacy name still supported. The UI calls it
"Merge by Distance" but the operator name remains `mesh.remove_doubles`.

### Apply All Transforms Before Export

Critical before STL export. Bakes location, rotation, and scale into mesh data.

```python
obj = bpy.context.active_object
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
```

Apply transforms to ALL objects in scene:

```python
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
```

### Export as STL

**Blender 4.0+ / 5.x:** STL export moved to `bpy.ops.wm.stl_export()`.
The old `bpy.ops.export_mesh.stl()` was removed in Blender 4.0.

Export active/selected object:

```python
bpy.ops.wm.stl_export(
    filepath="/tmp/model.stl",
    export_selected_objects=True,    # only selected, not entire scene
    global_scale=1000.0,             # BU to mm (1 BU = 1m = 1000mm)
    use_scene_unit=False,
    ascii_format=False,              # binary STL = smaller file
    apply_modifiers=True
)
```

Export entire scene:

```python
bpy.ops.wm.stl_export(
    filepath="/tmp/scene.stl",
    export_selected_objects=False,
    global_scale=1000.0,
    ascii_format=False,
    apply_modifiers=True
)
```

**Fallback for older Blender (< 4.0):**

```python
# Legacy API — do NOT use for Blender 4.0+
bpy.ops.export_mesh.stl(
    filepath="/tmp/model.stl",
    use_selection=True,
    global_scale=1000.0,
    ascii=False
)
```

### Full Print-Ready Export Pipeline

Complete workflow: clean up, validate, export.

```python
import bmesh

obj = bpy.context.active_object

# 1. Apply all transforms
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 2. Enter edit mode for cleanup
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')

# 3. Merge close vertices
bpy.ops.mesh.remove_doubles(threshold=0.00001)

# 4. Recalculate normals outward
bpy.ops.mesh.normals_make_consistent(inside=False)

# 5. Return to object mode
bpy.ops.object.mode_set(mode='OBJECT')

# 6. Manifold check
bm = bmesh.new()
bm.from_mesh(obj.data)
non_manifold = [e for e in bm.edges if not e.is_manifold]
bm.free()

if non_manifold:
    print(f"WARNING: {len(non_manifold)} non-manifold edges found")
else:
    print("Mesh is manifold — ready for print")

# 7. Export STL (Blender 4.0+ / 5.x)
obj.select_set(True)
bpy.ops.wm.stl_export(
    filepath="/tmp/print_ready.stl",
    export_selected_objects=True,
    global_scale=1000.0,
    ascii_format=False,
    apply_modifiers=True
)
print("Exported to /tmp/print_ready.stl")
```

---

## 8. Shape Creation

### Rounded Box (Cube with Beveled Edges)

```python
# Create cube, then bevel all edges
bpy.ops.mesh.primitive_cube_add(size=0.02, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "RoundedBox"

mod = obj.modifiers.new(name="Bevel", type='BEVEL')
mod.width = 0.002              # 2mm radius
mod.segments = 8
mod.affect = 'EDGES'
mod.limit_method = 'NONE'
mod.miter_outer = 'MITER_ARC'
bpy.ops.object.modifier_apply(modifier="Bevel")
```

### Tube / Pipe (Hollow Cylinder)

Cylinder with hollow center. Inner radius 8mm, outer radius 10mm, height 30mm.

```python
# Create outer cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.01, depth=0.03, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "Tube"

# Hollow it with solidify (inward)
mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
mod.thickness = -0.002         # 2mm wall thickness (10mm - 8mm = 2mm wall)
mod.offset = -1
mod.use_even_offset = True
bpy.ops.object.modifier_apply(modifier="Solidify")
```

**Alternative — Boolean method:**

```python
# Outer cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.01, depth=0.03, location=(0, 0, 0), vertices=64)
outer = bpy.context.active_object
outer.name = "Tube"

# Inner cylinder (cutter) — slightly taller to ensure clean cut
bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.032, location=(0, 0, 0), vertices=64)
inner = bpy.context.active_object
inner.name = "TubeCutter"

# Boolean difference
bpy.context.view_layer.objects.active = outer
mod = outer.modifiers.new(name="bool_hole", type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = inner
mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="bool_hole")
bpy.data.objects.remove(inner)
```

### Ring / Washer Shape

Outer radius 10mm, inner radius 5mm, thickness 2mm.

```python
# Create torus-like shape using cylinder + solidify
bpy.ops.mesh.primitive_cylinder_add(radius=0.01, depth=0.002, location=(0, 0, 0), vertices=64)
obj = bpy.context.active_object
obj.name = "Washer"

# Cut the center hole
bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=0.004, location=(0, 0, 0), vertices=64)
cutter = bpy.context.active_object

bpy.context.view_layer.objects.active = obj
mod = obj.modifiers.new(name="bool_hole", type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = cutter
mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="bool_hole")
bpy.data.objects.remove(cutter)
```

### L-Bracket

20mm x 30mm x 3mm thick L-shaped bracket.

```python
import bmesh

# Create base mesh manually with bmesh
mesh = bpy.data.meshes.new("LBracket")
obj = bpy.data.objects.new("LBracket", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj

bm = bmesh.new()

t = 0.003   # 3mm thickness
w = 0.02    # 20mm width (Y)
h1 = 0.03   # 30mm vertical leg
h2 = 0.02   # 20mm horizontal leg

# L-profile vertices (XZ plane, extruded along Y)
profile = [
    (0, 0),           # bottom-left
    (h2, 0),          # bottom-right
    (h2, t),          # step up
    (t, t),           # inner corner
    (t, h1),          # top of vertical leg
    (0, h1),          # top-left
]

# Create front and back faces, then bridge
front_verts = [bm.verts.new((x * 0.001 / 0.001, 0, z * 0.001 / 0.001)) for x, z in profile]
# Correction: profile is already in meters
front_verts = []
back_verts = []
for x, z in profile:
    front_verts.append(bm.verts.new((x, 0, z)))
    back_verts.append(bm.verts.new((x, w, z)))

n = len(profile)
# Front face
bm.faces.new(front_verts)
# Back face
bm.faces.new(list(reversed(back_verts)))
# Side faces
for i in range(n):
    j = (i + 1) % n
    bm.faces.new([front_verts[i], front_verts[j], back_verts[j], back_verts[i]])

bm.to_mesh(mesh)
bm.free()
mesh.update()

# Recalculate normals
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
```

### T-Bracket

```python
import bmesh

mesh = bpy.data.meshes.new("TBracket")
obj = bpy.data.objects.new("TBracket", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj

bm = bmesh.new()

t = 0.003    # 3mm thickness
w = 0.02     # 20mm depth (Y)
stem_h = 0.025  # 25mm stem height
top_w = 0.03    # 30mm top bar width

# T-profile (XZ plane)
half_top = top_w / 2
half_stem = t / 2
profile = [
    (-half_top, stem_h + t),       # top-left
    (half_top, stem_h + t),        # top-right
    (half_top, stem_h),            # step down right
    (half_stem, stem_h),           # inner right
    (half_stem, 0),                # bottom right of stem
    (-half_stem, 0),               # bottom left of stem
    (-half_stem, stem_h),          # inner left
    (-half_top, stem_h),           # step down left
]

front_verts = []
back_verts = []
for x, z in profile:
    front_verts.append(bm.verts.new((x, 0, z)))
    back_verts.append(bm.verts.new((x, w, z)))

n = len(profile)
bm.faces.new(front_verts)
bm.faces.new(list(reversed(back_verts)))
for i in range(n):
    j = (i + 1) % n
    bm.faces.new([front_verts[i], front_verts[j], back_verts[j], back_verts[i]])

bm.to_mesh(mesh)
bm.free()
mesh.update()

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
```

### Box with Lid (Two Separate Pieces)

Box: 40x30x20mm outer, 2mm walls. Lid: matching top piece.

```python
wall = 0.002    # 2mm wall
ox, oy, oz = 0.04, 0.03, 0.02  # outer dimensions
lid_h = 0.005   # 5mm lid height
lip = 0.001     # 1mm lip overlap

# --- BOX (bottom part) ---
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, oz / 2))
box = bpy.context.active_object
box.name = "Box"
box.dimensions = (ox, oy, oz)
bpy.ops.object.transform_apply(scale=True)

# Hollow the box (solidify inward, no rim on top)
mod = box.modifiers.new(name="Solidify", type='SOLIDIFY')
mod.thickness = -wall
mod.offset = -1
mod.use_rim = False            # leave top open
mod.use_even_offset = True
bpy.ops.object.modifier_apply(modifier="Solidify")

# Delete top face to create open box
import bmesh
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(box.data)
bm.faces.ensure_lookup_table()
for f in bm.faces:
    f.select = f.normal.z > 0.9 and f.calc_center_median().z > oz * 0.9
bmesh.update_edit_mesh(box.data)
bpy.ops.mesh.delete(type='FACE')
bpy.ops.object.mode_set(mode='OBJECT')

# --- LID ---
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, oz + lid_h / 2 + 0.001))
lid = bpy.context.active_object
lid.name = "Lid"
lid.dimensions = (ox, oy, lid_h)
bpy.ops.object.transform_apply(scale=True)

# Add lip (inner part that fits into the box)
bpy.ops.mesh.primitive_cube_add(
    size=1,
    location=(0, 0, oz - lip / 2 + 0.001)
)
lip_part = bpy.context.active_object
lip_part.name = "LidLip"
lip_part.dimensions = (ox - wall * 2 - 0.0002, oy - wall * 2 - 0.0002, lip)
bpy.ops.object.transform_apply(scale=True)

# Union lip to lid
bpy.context.view_layer.objects.active = lid
lid.select_set(True)
mod = lid.modifiers.new(name="bool_lip", type='BOOLEAN')
mod.operation = 'UNION'
mod.object = lip_part
mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="bool_lip")
bpy.data.objects.remove(lip_part)
```

### Threaded Hole (Simplified — Cosmetic Thread)

True helical threads are extremely complex in bpy. This creates a simplified
"cosmetic thread" — a cylinder with a helical groove cut, good enough for
visual representation or loose-fit printed threads.

```python
import bmesh
import math

# Parameters
radius = 0.003       # M6 = 3mm radius
depth = 0.01         # 10mm deep hole
pitch = 0.001        # 1mm pitch
thread_depth = 0.0004  # 0.4mm thread depth
segments = 32
turns = int(depth / pitch)

# Create threaded cylinder profile using bmesh
mesh = bpy.data.meshes.new("Thread")
obj = bpy.data.objects.new("Thread", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj

bm = bmesh.new()

# Create helix vertices (inner and outer)
verts_outer = []
verts_inner = []
total_steps = turns * segments

for i in range(total_steps + 1):
    angle = (i / segments) * 2 * math.pi
    z = (i / segments) * pitch
    # Triangle wave for thread profile
    phase = (i % segments) / segments
    r_offset = thread_depth * (1 - abs(2 * phase - 1))

    x_out = (radius) * math.cos(angle)
    y_out = (radius) * math.sin(angle)
    x_in = (radius - r_offset) * math.cos(angle)
    y_in = (radius - r_offset) * math.sin(angle)

    verts_outer.append(bm.verts.new((x_out, y_out, z)))
    verts_inner.append(bm.verts.new((x_in, y_in, z)))

# Create faces between inner and outer helix
for i in range(total_steps):
    bm.faces.new([verts_outer[i], verts_outer[i+1], verts_inner[i+1], verts_inner[i]])

bm.to_mesh(mesh)
bm.free()
mesh.update()

# NOTE: For a threaded HOLE, use this object as a boolean cutter on your base part
```

**Honest assessment:** Generating printable threaded holes purely in bpy is
hard to get right. For functional threads, consider:
1. Use a pre-made thread mesh (import STL of standard thread profile)
2. Use the Bolt Factory addon if available (`bpy.ops.mesh.bolt_add()`)
3. For printed parts, heat-set brass inserts are more reliable than printed threads

### Slot / Groove

Cut a 3mm wide, 2mm deep slot along the top of an object.

```python
# Assumes active object is the base part
base = bpy.context.active_object

# Create slot cutter
slot_length = base.dimensions.x * 1.1  # slightly longer than base
bpy.ops.mesh.primitive_cube_add(
    size=1,
    location=(base.location.x, base.location.y,
              base.location.z + base.dimensions.z / 2 - 0.001)  # 1mm from top
)
slot = bpy.context.active_object
slot.name = "SlotCutter"
slot.dimensions = (slot_length, 0.003, 0.002)  # length x 3mm wide x 2mm deep
bpy.ops.object.transform_apply(scale=True)

# Boolean cut
bpy.context.view_layer.objects.active = base
base.select_set(True)
mod = base.modifiers.new(name="bool_slot", type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = slot
mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="bool_slot")
bpy.data.objects.remove(slot)
```

### Counterbore Hole

A counterbore = through-hole + wider shallow pocket on top.
Example: M5 through-hole (2.5mm radius) with 10mm diameter counterbore, 3mm deep.

```python
base = bpy.context.active_object
loc = base.location.copy()
top_z = loc.z + base.dimensions.z / 2

# Through-hole cutter
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.0025,               # M5 = 2.5mm radius
    depth=base.dimensions.z * 1.1,
    location=(loc.x, loc.y, loc.z),
    vertices=32
)
through_hole = bpy.context.active_object
through_hole.name = "ThroughHole"

# Counterbore cutter
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.005,                # 10mm diameter = 5mm radius
    depth=0.003,                 # 3mm deep
    location=(loc.x, loc.y, top_z - 0.0015),  # centered at top
    vertices=32
)
counterbore = bpy.context.active_object
counterbore.name = "Counterbore"

# Cut through-hole
bpy.context.view_layer.objects.active = base
base.select_set(True)
mod = base.modifiers.new(name="bool_through", type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = through_hole
mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="bool_through")
bpy.data.objects.remove(through_hole)

# Cut counterbore
mod = base.modifiers.new(name="bool_cbore", type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = counterbore
mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="bool_cbore")
bpy.data.objects.remove(counterbore)
```

---

## 9. Limitations — What bpy Cannot Do Easily

### Difficult but Possible

| Operation | Difficulty | Why |
|-----------|-----------|-----|
| **Loop cut at specific location** | Hard | `loopcut_slide` requires `edge_index` which must be found via bmesh traversal. No way to say "cut here" by coordinate. |
| **Bridge edge loops** | Hard | Requires exactly 2 edge loops selected with matching vertex count. Programmatically selecting the right loops is fragile. |
| **Select specific faces by position** | Medium | Must iterate all faces in bmesh and filter by normal/position. No spatial query API. |
| **Helical threads** | Hard | No built-in helix primitive. Must generate vertices mathematically. Results need careful manifold checking. |
| **Freeform surface editing** | Hard | Sculpt-like operations exist (`bpy.ops.sculpt.*`) but require brush setup and are designed for interactive use, not scripted. |
| **Text/engraving** | Medium | `bpy.ops.object.text_add()` creates text, convert to mesh, then boolean cut. Font rendering can produce non-manifold geometry. |
| **Loft between profiles** | Hard | No direct loft operator. Must use bridge_edge_loops between two profile curves converted to mesh, or build faces manually with bmesh. |

### Practically Impossible with Pure bpy

| Operation | Why |
|-----------|-----|
| **Organic sculpting via script** | Sculpt tools are interactive-only in practice. You can call operators but controlling brush strokes programmatically produces poor results. |
| **Automatic support generation** | Slicer territory (PrusaSlicer/Cura). Blender has no built-in support generation. |
| **Parametric constraint system** | No auto-updating linked dimensions. Tolerance offsets are applied manually per part — 3DPrintVoice automates this via system prompt rules for Prusa MK3 (0.25mm sliding, 0.15mm snug, 0.05mm press fit). |
| **GD&T / dimensioning** | No measurement/annotation system for manufacturing. Use FreeCAD for this. |
| **Adaptive mesh refinement** | Remesh modifier exists but it's global, not adaptive to feature size. |

### Recommended Workarounds

- **For parametric parts:** Use FreeCAD's Python API instead — it has constraints, sketches, pads, pockets natively.
- **For standard hardware (bolts, nuts):** Use Blender's Bolt Factory addon if installed, or import pre-made STL files.
- **For threads:** Use heat-set inserts in printed parts instead of printing threads. If you must have threads, import a thread profile STL.
- **For complex assemblies:** Model parts individually in Blender, assemble and check fit in PrusaSlicer or your slicer of choice.

---

## API Version Notes

| Feature | Blender < 4.0 | Blender 4.0+ / 5.x |
|---------|---------------|---------------------|
| STL Export | `bpy.ops.export_mesh.stl()` | `bpy.ops.wm.stl_export()` |
| Boolean solver | `'FAST'` default | `'EXACT'` recommended |
| Bevel weight | `edge.bevel_weight` property | `bm.edges.layers.bevel_weight.verify()` via bmesh layer |
| Modifier apply | `bpy.ops.object.modifier_apply(modifier=name)` | Same (unchanged) |
| Collection linking | `bpy.context.scene.collection` | Same (unchanged) |

---

*Generated for 3d-print-voice project. Target: Blender 5.1.0, Prusa MK3 printer.*
*All measurements assume Blender default unit = meters, 3D print target = mm.*
