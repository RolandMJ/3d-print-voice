# Phase 3 — Scene Context, Parametric Awareness, Organic Geometry, Print Bed Safety

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable the LLM to see scene state for relative commands ("make it taller"), store part parameters for mating parts, warn on print bed exceedance, and add organic geometry recipes.

**Architecture:** After each successful bpy execution, a scene query script runs in Blender and returns JSON (object names, dimensions, locations, custom properties). This context is passed to the next LLM call. Print bed dimensions stored in config, checked after each command. Organic geometry via bezier curves and subdivision surface recipes in system prompt.

**Tech Stack:** Python 3.11+, bpy, tkinter, JSON scene serialization

---

### Task 1: Create scene query script

**Files:**
- Create: `prompts/scene_query.py`

The bpy code that runs after each command to capture scene state.

### Task 2: Add query_scene() to blender_client

**Files:**
- Modify: `agent/blender_client.py`

New method that POSTs scene_query.py code and returns parsed JSON.

### Task 3: Wire scene context into pipeline

**Files:**
- Modify: `agent/app.py` (_run_pipeline)

After successful execution, call query_scene(), store result. Pass to generate_bpy_code() on next call.

### Task 4: Add print bed config + warning

**Files:**
- Modify: `agent/config.py` (add print_bed to DEFAULT_CONFIG)
- Modify: `agent/app.py` (check dimensions after command, warn if exceeds)

### Task 5: Add parametric property instructions to system prompt

**Files:**
- Modify: `prompts/system.md`

Tell LLM to set custom properties on objects and how to use scene context.

### Task 6: Add organic geometry recipes to system prompt

**Files:**
- Modify: `prompts/system.md`

Bezier extrusion, subdivision base mesh, lofted surface, proportional smooth, shrinkwrap.

### Task 7: Update docs, poster, cheatsheet, verify, push

**Files:**
- Modify: `docs/command-reference.html`, `docs/COMMAND_CHEATSHEET.md`, `docs/CHANGELOG.md`
