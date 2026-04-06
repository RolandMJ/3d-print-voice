# 3DPrintVoice Command Cheat Sheet

Say or type these commands. Dimensions are always in millimeters.
The AI handles the conversion to Blender units automatically.

---

## Creating Objects

| Say this | What it does |
|----------|-------------|
| "create a 40mm cube" | Box, all sides 40mm |
| "create a box 50 by 30 by 20mm" | Rectangular box |
| "create a sphere with radius 20mm" | Sphere |
| "create a cylinder 10mm radius 50mm tall" | Solid cylinder |
| "create a cone 15mm radius 30mm tall" | Cone |
| "create a torus 20mm major radius 5mm minor radius" | Donut/ring shape |

## Moving and Transforming

| Say this | What it does |
|----------|-------------|
| "move it up by 30mm" | Shifts the object upward |
| "move it left 10mm" | Shifts along negative X |
| "rotate it 45 degrees around Z" | Spins on vertical axis |
| "scale it to double size" | Makes it 2x bigger |
| "set dimensions to 50 by 30 by 20mm" | Exact size |
| "center it at the origin" | Moves to (0,0,0) |

## Hollowing and Shell

| Say this | What it does |
|----------|-------------|
| "make it hollow with 1.5mm walls" | Hollows out the inside, keeps shell |
| "make it hollow with 2mm walls inward" | Shell goes inward (outside stays same) |
| "make it hollow with 2mm walls outward" | Shell goes outward (inside stays same) |

**How it works:** Adds a Solidify modifier. The object becomes a hollow shell
with the wall thickness you specify. Essential for 3D printing — solid objects
waste material.

## Boolean Operations (Adding, Subtracting, Intersecting)

| Say this | What it does |
|----------|-------------|
| "subtract the Cylinder from the Cube" | Cuts cylinder shape out of cube |
| "cut a hole through the middle" | Boolean difference with a cylinder |
| "join the Cube and Sphere into one" | Boolean union (merge two objects) |
| "keep only where they overlap" | Boolean intersection |

**How it works:** Boolean operations combine two objects. Think of it like
clay: you can stick two pieces together (union), stamp one out of the other
(difference), or keep only the part where they overlap (intersection).

## Rounding and Chamfering Edges

| Say this | What it does |
|----------|-------------|
| "round all edges with 1mm radius" | Smooth round on every edge |
| "round the sharp edges with 0.5mm radius" | Only edges > 30 degrees |
| "chamfer all edges 1mm" | Flat 45-degree cut on every edge |
| "fillet the edges with 2mm radius" | High-quality smooth round |

**Round vs Chamfer:** A round (fillet) is curved. A chamfer is a flat cut.
Both reduce sharp edges. For 3D printing, small fillets (0.5-1mm) improve
strength at corners.

## Patterns and Repetition

| Say this | What it does |
|----------|-------------|
| "repeat it 5 times along X with 10mm spacing" | Linear array |
| "repeat it 8 times in a circle" | Circular array |
| "mirror it along X" | Create symmetrical copy |
| "mirror it along X and Y" | Four-way symmetry |

## Common Shapes (Compound Commands)

| Say this | What it does |
|----------|-------------|
| "create a tube 10mm outer radius 8mm inner radius 30mm tall" | Hollow cylinder |
| "create a rounded box 30mm with 2mm radius edges" | Cube with smooth corners |
| "create a washer 10mm outer 5mm inner 2mm thick" | Flat ring |
| "create a slot 20mm long 3mm wide 2mm deep on top" | Groove cut into surface |
| "create a counterbore hole M5 with 10mm head 3mm deep" | Screw hole with pocket |

## Multi-Part Assemblies (Tolerance Fits)

When you create parts that fit together, the AI automatically applies
clearance offsets so they actually fit off the printer. These values are
tuned for the Prusa MK3 with a 0.4mm nozzle.

| Say this | Fit type | Clearance/side |
|----------|----------|---------------|
| "create a box with lid" | Sliding fit | 0.25mm |
| "create a snap-fit cap for it" | Snug fit | 0.15mm |
| "create a press-fit peg and hole" | Press fit | 0.05mm |
| "create a hinge pin and socket" | Loose fit | 0.40mm |
| "create a lid that fits this box" | Sliding fit | 0.25mm |

**What are these numbers?** When you 3D print two parts that should fit
together, the printer is not perfectly precise. A 10mm peg into a 10mm hole
won't fit — you need the hole to be slightly bigger (or the peg slightly
smaller). The clearance is that extra space:

- **Sliding fit (0.25mm):** Parts slide smoothly. Lids, drawers, sleeves.
- **Snug fit (0.15mm):** Parts click together with light pressure. Caps, covers.
- **Press fit (0.05mm):** Parts require force to assemble. Permanent joins.
- **Loose fit (0.40mm):** Parts move freely. Hinges, pivots, bearings.

The AI applies the right clearance automatically based on your words. If you
say "lid" or "cover," it uses sliding fit. If you say "snap" or "click," it
uses snug fit. You can also be explicit: "use 0.3mm clearance per side."

## 3D Print Preparation

| Say this | What it does |
|----------|-------------|
| "fix the normals" | Makes all faces point outward |
| "clean up the mesh" | Removes duplicate vertices |
| "apply all transforms" | Bakes position/rotation/scale |
| "check if it's manifold" | Verifies mesh is watertight |
| "export as STL" | Saves to /tmp/model.stl for slicer |
| "prepare for printing and export" | Full cleanup + manifold check + export |

## Articulation Joints (Poseable Assemblies)

| Say this | What it does |
|----------|-------------|
| "create medium ball-and-socket joint" | 10mm ball + socket (shoulders, hips, neck) |
| "create small ball joint" | 6mm ball (wrists, ankles, fingers) |
| "create large ball joint" | 14mm ball (torso-hip, shoulder base) |
| "create ratchet joint with 12 stops" | Click-stop joint (holds poses under gravity) |
| "create double-hinge knee joint" | 2-axis articulation (knees, elbows) |
| "create swivel joint for waist" | Single-axis rotation (waist, forearm twist) |
| "create friction peg joint 4mm" | D-shape tight-fit rotation (wrists, ankles) |

## Hardware Integration (Metal Parts)

| Say this | What it does |
|----------|-------------|
| "add 6mm steel rod sleeve" | Channel for 6mm metal rod (3/4/6/8mm available) |
| "add M3 heat-set insert pocket" | Tapered pocket for brass threaded insert |
| "add M3 screw boss with ribs" | Reinforced mounting post with gussets |
| "add countersunk M3 hole" | Flush bolt head recess |
| "add magnet pocket 6x3mm" | Recessed pocket for disc magnet |
| "add spring clip detent" | Flexible clip for removable panel retention |
| "add zip-tie anchor point" | Loop/bridge for cable management |

## DIN Metric Hardware (German Baumarkt)

Holes use exact DIN clearance dimensions. Say the screw size and the AI
uses the correct H13 tolerance hole.

| Say this | DIN Standard | Key dimensions |
|----------|-------------|---------------|
| "add M4 DIN 912 counterbore" | Socket head cap | 4.5mm shaft, 7mm head, 4mm deep |
| "add M4 hex nut pocket" | DIN 934 | 7mm hex, 3.2mm deep |
| "add M6 threaded rod channel" | DIN 975 | 6.6mm clearance (thread OD > nominal) |
| "add 3mm spring pin hole" | DIN 1481 | Exact 3mm — pin compresses to fit |
| "add 4mm dowel pin hole" | DIN 7 | 4.05mm (0.05mm press fit clearance) |
| "add M3 countersunk hole" | DIN 7991 | 3.4mm shaft, 6mm head recess |

**Available sizes at Baumarkt:** M3, M4, M5, M6, M8 screws. Smooth rods: 3-10mm.
Threaded rods: M4-M10. Spring pins: 2-5mm. Dowel pins: 3-6mm.

## Curved Panels (Armor / Shell Geometry)

| Say this | What it does |
|----------|-------------|
| "create curved panel 60mm wide 90 degrees" | Swept arc panel (bmesh spin) |
| "create shoulder pauldron 120 degrees" | Wide curved panel, r=35mm |
| "create tapered armor panel" | Wider top, narrower bottom, curved |
| "create curved tube 90 degrees radius 30mm" | Structural arc, handle, frame |
| "add overlap lip to panel edge" | 2mm inward lip for layered armor |

**How it works:** Curved panels use bmesh spin — a 2D profile is swept along
an arc to create a curved 3D surface. You specify width, arc angle, radius,
and thickness. The AI handles the geometry.

## Surface Detail

| Say this | What it does |
|----------|-------------|
| "engrave panel line 30mm long" | 0.3mm deep recessed line on surface |
| "add raised rivet detail" | 2mm hex bolt head decoration |
| "add 4 reinforcement ribs" | Structural gussets at wall-base junction |
| "fillet inside corners 2mm" | Stress-relief radius on internal edges |
| "chamfer bottom edges 0.5mm" | Elephant foot compensation for printing |

## Organic Geometry (Smooth / Curved Forms)

| Say this | What it does |
|----------|-------------|
| "create organic tube along a curve" | Bezier curve extrusion (cables, handles) |
| "create smooth dome with subdivision" | Low-poly cage + subsurf = smooth organic |
| "loft between circle and square" | Bridge two cross-sections into smooth surface |
| "smooth the mesh" | Smooth modifier to soften boolean artifacts |
| "shrinkwrap detail onto curved panel" | Project flat detail onto curved surface |

**How it works:** Organic shapes use bezier curves (extruded profiles along paths),
subdivision surfaces (smooth from low-poly cage), and shrinkwrap (flat-to-curved
projection). These bridge the gap between box-and-boolean and freeform sculpting.

## Scene Context (Relative Commands)

The AI knows what's already in your scene. After each command, it reads all
object names, dimensions, locations, and custom properties. This enables:

| Say this | What happens |
|----------|-------------|
| "make it taller" | Reads current height, increases it |
| "create a matching socket" | Reads ball joint radius, adds clearance |
| "create the left version" | Mirrors right-side part from scene |
| "move it next to the arm" | Reads arm position, places adjacent |

**Print bed warning:** If any part exceeds your print bed (default Prusa MK3:
250x210x210mm), a yellow warning appears suggesting you split the part.

## Assembly & Production

| Say this | What it does |
|----------|-------------|
| "add keyed alignment pin 6mm" | D-shape pin (prevents rotation) |
| "split part at 50mm with zigzag" | Interlocking seam for oversize parts |
| "add dovetail rail 80mm long" | Linear slide channel |
| "add T-slot channel for M4" | Adjustable bolt channel |
| "export all parts as STL" | Batch export (individual file per object) |

## Part Naming Convention

When building multi-part assemblies, the AI follows this naming pattern:
`REGION_PART_SIDE_NUMBER` — e.g., ARM_UPPER_L_01, TORSO_PANEL_FRONT_01

| Word you say | Naming result |
|-------------|---------------|
| "left upper arm" | ARM_UPPER_L_01 |
| "right knee joint" | JOINT_KNEE_R_01 |
| "chest front panel" | TORSO_PANEL_FRONT_01 |
| "head" | HEAD_MAIN_C_01 |
| "foot sole" | FOOT_SOLE_R_01 |

## Scene Management

| Say this | What it does |
|----------|-------------|
| "delete everything" | Clears the scene |
| "delete the Cylinder" | Removes specific object |
| "rename it to Base" | Names the active object |
| "select the Cube" | Makes Cube the active object |

---

## Tips for Best Results

1. **Be specific with dimensions.** "Create a 40mm cube" works better than
   "create a small cube."

2. **Name your objects.** After creating an object, say "rename it to Base."
   Then you can refer to it by name: "subtract the Hole from the Base."

3. **One operation at a time.** "Create a cube and make it hollow" might work,
   but "create a cube" then "make it hollow with 2mm walls" is more reliable.

4. **Use Ctrl+Z in Blender** if something goes wrong. Every AI command is
   an undo step.

5. **Check the terminal output.** The generated code is shown before execution.
   If it looks wrong, you can Ctrl+C before it runs (in future versions).

---

## What the AI Can NOT Do Well

These operations are very hard to automate and may produce unreliable results:

- Organic sculpting (freeform clay-like modeling)
- Precise threading (use heat-set inserts for printed parts instead)
- Auto-updating parametric constraints (changing one dimension won't auto-update linked parts)
- Lofting between arbitrary profiles
- Selecting specific individual faces by visual appearance

For fully parametric engineering CAD, consider FreeCAD. 3DPrintVoice excels at
quick shape creation, boolean-based part building, multi-part assemblies
with print-ready tolerances, and 3D print preparation.
