# Local Architecture Rebuild — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the Anthropic cloud API with a fully local stack (Ollama + Qwen2.5-Coder 14B), add undo/auto-save support to the Blender addon, add output parsing for local model quirks, and create a one-click launcher.

**Architecture:** Ollama runs locally on GPU serving Qwen2.5-Coder 14B. The agent talks to Ollama's OpenAI-compatible API at localhost:11434. A code extractor strips markdown/explanation from model output before sending to Blender. The addon pushes undo points before each exec. A launcher script orchestrates startup/shutdown of all components.

**Tech Stack:** Ollama, Qwen2.5-Coder 14B (Q4_K_M), Python 3.12, stdlib HTTP, Blender 5.1 bpy

---

## Task 1: Install System Dependencies

**Files:** None (system-level installs)

**Step 1: Install Ollama**

Run:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
Expected: Ollama installed, `ollama --version` returns version string.

**Step 2: Start Ollama service and pull model**

Run:
```bash
ollama serve &  # if not auto-started by systemd
ollama pull qwen2.5-coder:14b-instruct
```
Expected: Model downloaded (~9GB), `ollama list` shows `qwen2.5-coder:14b-instruct`.

**Step 3: Verify Ollama API responds**

Run:
```bash
curl -s http://localhost:11434/v1/models | python3 -m json.tool
```
Expected: JSON with model listed.

**Step 4: Install Python dependencies**

Run:
```bash
pip install sounddevice faster-whisper --break-system-packages
```
Expected: Both install without error.

**Step 5: Verify CUDA works with faster-whisper**

Run:
```bash
python3 -c "from faster_whisper import WhisperModel; m = WhisperModel('tiny', device='cuda', compute_type='float16'); print('CUDA whisper OK')"
```
Expected: Prints "CUDA whisper OK". If CUDA fails, fall back to `device='cpu'`.

**Step 6: Commit — no code changes, just verify environment**

---

## Task 2: Replace claude_client.py with llm_client.py

**Files:**
- Delete: `agent/claude_client.py`
- Create: `agent/llm_client.py`
- Create: `tests/test_llm_client.py`

**Step 1: Write the test**

```python
# tests/test_llm_client.py
"""Tests for llm_client — verifies code extraction and API call structure."""
import json
from unittest.mock import patch, MagicMock
from agent.llm_client import generate_bpy_code, extract_code


class TestExtractCode:
    """Test the code extractor that strips markdown from model output."""

    def test_clean_code_passes_through(self):
        raw = "bpy.ops.mesh.primitive_cube_add(size=0.04)"
        assert extract_code(raw) == raw

    def test_strips_python_fence(self):
        raw = "```python\nbpy.ops.mesh.primitive_cube_add(size=0.04)\n```"
        assert extract_code(raw) == "bpy.ops.mesh.primitive_cube_add(size=0.04)"

    def test_strips_plain_fence(self):
        raw = "```\nbpy.ops.mesh.primitive_cube_add(size=0.04)\n```"
        assert extract_code(raw) == "bpy.ops.mesh.primitive_cube_add(size=0.04)"

    def test_strips_preamble_text(self):
        raw = "Here is the code:\n```python\nbpy.ops.mesh.primitive_cube_add(size=0.04)\n```"
        assert extract_code(raw) == "bpy.ops.mesh.primitive_cube_add(size=0.04)"

    def test_strips_trailing_explanation(self):
        raw = "```python\nbpy.ops.mesh.primitive_cube_add(size=0.04)\n```\nThis creates a cube."
        assert extract_code(raw) == "bpy.ops.mesh.primitive_cube_add(size=0.04)"

    def test_multiline_code(self):
        raw = "```python\nimport bpy\nbpy.ops.mesh.primitive_cube_add(size=0.04)\nobj = bpy.context.active_object\nobj.name = 'MyCube'\n```"
        expected = "import bpy\nbpy.ops.mesh.primitive_cube_add(size=0.04)\nobj = bpy.context.active_object\nobj.name = 'MyCube'"
        assert extract_code(raw) == expected

    def test_cannot_execute_passes_through(self):
        raw = "# CANNOT_EXECUTE: cannot delete system objects"
        assert extract_code(raw) == raw

    def test_no_code_found_returns_original(self):
        raw = "I cannot help with that request."
        assert extract_code(raw) == raw


class TestGenerateBpyCode:
    """Test that generate_bpy_code calls Ollama correctly."""

    @patch("agent.llm_client._ollama_chat")
    def test_sends_system_and_user_message(self, mock_chat):
        mock_chat.return_value = "bpy.ops.mesh.primitive_cube_add(size=0.04)"
        result = generate_bpy_code("create a 40mm cube")
        assert result == "bpy.ops.mesh.primitive_cube_add(size=0.04)"
        mock_chat.assert_called_once()
        args = mock_chat.call_args
        assert "create a 40mm cube" in args[0][1]  # user message

    @patch("agent.llm_client._ollama_chat")
    def test_includes_scene_context(self, mock_chat):
        mock_chat.return_value = "bpy.ops.mesh.primitive_cube_add(size=0.04)"
        generate_bpy_code("make it bigger", scene_context="Cube at (0,0,0)")
        args = mock_chat.call_args
        assert "Cube at (0,0,0)" in args[0][1]
```

**Step 2: Run test to verify it fails**

Run: `cd ~/Documents/Claude\ Projects/blender-ai && python3 -m pytest tests/test_llm_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agent.llm_client'`

**Step 3: Write llm_client.py**

```python
# agent/llm_client.py
"""Local LLM client — talks to Ollama API at localhost:11434."""
import json
import re
import urllib.request
import urllib.error
from pathlib import Path

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system.md"
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5-coder:14b-instruct"


def _load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text()


def _ollama_chat(system: str, user_message: str) -> str:
    """Send a chat request to Ollama and return the response text."""
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 1024},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["message"]["content"]


def extract_code(raw: str) -> str:
    """Extract executable Python from model output.

    Local models often wrap code in markdown fences or add explanations.
    This strips everything except the actual code.
    """
    # Try to find code inside ```python ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:python)?\s*\n(.*?)```", raw, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    # If no fences, return as-is (might be clean code or CANNOT_EXECUTE)
    return raw.strip()


def generate_bpy_code(user_text: str, scene_context: str = "") -> str:
    """Generate bpy code from natural language via local Ollama model."""
    system = _load_system_prompt()

    user_message = user_text
    if scene_context:
        user_message = f"Current scene state:\n{scene_context}\n\nUser request: {user_text}"

    raw = _ollama_chat(system, user_message)
    return extract_code(raw)
```

**Step 4: Run tests to verify they pass**

Run: `cd ~/Documents/Claude\ Projects/blender-ai && python3 -m pytest tests/test_llm_client.py -v`
Expected: All 10 tests PASS.

**Step 5: Delete old claude_client.py**

Run: `rm agent/claude_client.py`

**Step 6: Commit**

```bash
git add agent/llm_client.py tests/test_llm_client.py
git rm agent/claude_client.py
git commit -m "feat: replace Claude API with local Ollama LLM client

- New llm_client.py talks to Ollama at localhost:11434
- Code extractor strips markdown fences from model output
- Uses qwen2.5-coder:14b-instruct model
- Tests for code extraction and API call structure"
```

---

## Task 3: Harden the System Prompt for Local Models

**Files:**
- Modify: `prompts/system.md`

**Step 1: Rewrite system.md with stricter output rules and more examples**

The local model needs more explicit instruction than Claude. Add repeated
output format enforcement and more bpy examples.

**Step 2: Commit**

```bash
git add prompts/system.md
git commit -m "feat: harden system prompt for local model reliability"
```

---

## Task 4: Add Undo Support to Blender Addon

**Files:**
- Modify: `addon/ai_bridge.py`

**Step 1: Add undo_push before exec in _execute_bpy**

Wrap each execution with `bpy.ops.ed.undo_push(message="AI Bridge")` so
Ctrl+Z in Blender reverts AI commands.

**Step 2: Test manually in Blender** (addon runs in Blender's Python, can't unit test bpy)

- Install updated addon
- Send a command via curl
- Press Ctrl+Z in Blender
- Verify the object disappears

**Step 3: Commit**

```bash
git add addon/ai_bridge.py
git commit -m "feat: add undo support — each AI command is undoable via Ctrl+Z"
```

---

## Task 5: Update main.py for Local Architecture

**Files:**
- Modify: `agent/main.py`

**Step 1: Replace claude_client import with llm_client**

- Change import from `agent.claude_client` to `agent.llm_client`
- Remove dotenv dependency (no API key needed)
- Add error retry: if Blender returns an error, feed it back to the model once
- Update print messages (no more "Claude" references)

**Step 2: Verify the text input loop works end-to-end**

Run: `python3 -m agent.main`
- Ollama must be running with model loaded
- Blender must be running with addon enabled
- Type "create a 40mm cube"
- Expected: cube appears in Blender

**Step 3: Commit**

```bash
git add agent/main.py
git commit -m "feat: wire main.py to local Ollama backend with error retry"
```

---

## Task 6: Update requirements.txt and Remove .env Dependency

**Files:**
- Modify: `requirements.txt`
- Delete: `.env.example`

**Step 1: Update requirements.txt**

```
sounddevice>=0.4.6
faster-whisper>=1.0.0
```

No anthropic SDK. No python-dotenv. These are the only pip dependencies
for the agent. Ollama is a system install, not a pip package.

**Step 2: Commit**

```bash
git add requirements.txt
git rm .env.example
git commit -m "feat: update deps for local stack, remove API key dependency"
```

---

## Task 7: Build the Launcher Script

**Files:**
- Create: `launcher.sh`
- Create: `blender-ai.desktop`

**Step 1: Write launcher.sh**

Bash script that:
1. Starts Ollama if not already running
2. Preloads the model (warm-up request)
3. Launches Blender with the addon
4. Launches the agent (in a terminal window)
5. On exit (Ctrl+C or terminal close), kills Blender and Ollama gracefully

**Step 2: Write blender-ai.desktop**

Standard .desktop file for Linux that runs launcher.sh. User copies it to
`~/.local/share/applications/` for app menu, or Desktop for double-click.

**Step 3: Test the launcher**

Run: `bash launcher.sh`
Expected: Ollama starts, Blender opens, agent terminal appears, typing
a command creates objects in Blender.

**Step 4: Commit**

```bash
git add launcher.sh blender-ai.desktop
git commit -m "feat: add one-click launcher with desktop integration"
```

---

## Task 8: Update All Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/SETUP_GUIDE.md`
- Modify: `docs/PROJECT_OVERVIEW.md`
- Modify: `docs/DEVELOPMENT_LOG.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/architecture.svg`
- Modify: `docs/IP_NOTICE.md`

**Step 1: Update all docs to reflect local architecture**

- Remove all Anthropic/Claude API references
- Add Ollama setup instructions
- Update architecture diagram for local flow
- Add new development log entry
- Update changelog with v0.2.0
- Update IP notice (AI tools disclosure: Ollama + Qwen2.5-Coder)

**Step 2: Commit**

```bash
git add README.md docs/
git commit -m "docs: update all documentation for fully local architecture"
```

---

## Task 9: Integration Test and Final Audit

**Step 1: Full pipeline test**

1. Run `bash launcher.sh`
2. Wait for everything to start
3. Type "create a 40mm cube" → verify cube appears
4. Type "move it up by 20mm" → verify it moves (may fail without scene context)
5. Press Ctrl+Z in Blender → verify undo works
6. Type "quit" → verify agent exits
7. Close launcher → verify Blender and Ollama stop

**Step 2: Audit checklist**

- [ ] No Anthropic API references remain in code
- [ ] No .env file required
- [ ] All tests pass
- [ ] Launcher starts/stops all components
- [ ] Desktop file works
- [ ] Documentation matches code
- [ ] Git history is clean with descriptive commits

**Step 3: Tag release**

```bash
git tag -a v0.2.0 -m "v0.2.0: fully local architecture — Ollama + Qwen2.5-Coder 14B"
```
