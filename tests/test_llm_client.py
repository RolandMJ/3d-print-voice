"""Tests for llm_client — verifies code extraction and API call structure."""
from unittest.mock import patch
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

    def test_multiple_fences_takes_first(self):
        raw = "```python\nfirst_block()\n```\nsome text\n```python\nsecond_block()\n```"
        assert extract_code(raw) == "first_block()"


class TestGenerateBpyCode:
    """Test that generate_bpy_code calls Ollama correctly."""

    @patch("agent.llm_client._ollama_chat")
    def test_sends_user_message(self, mock_chat):
        mock_chat.return_value = "bpy.ops.mesh.primitive_cube_add(size=0.04)"
        result = generate_bpy_code("create a 40mm cube")
        assert result == "bpy.ops.mesh.primitive_cube_add(size=0.04)"
        mock_chat.assert_called_once()
        args = mock_chat.call_args
        assert "create a 40mm cube" in args[0][1]

    @patch("agent.llm_client._ollama_chat")
    def test_includes_scene_context(self, mock_chat):
        mock_chat.return_value = "bpy.ops.mesh.primitive_cube_add(size=0.04)"
        generate_bpy_code("make it bigger", scene_context="Cube at (0,0,0)")
        args = mock_chat.call_args
        assert "Cube at (0,0,0)" in args[0][1]

    @patch("agent.llm_client._ollama_chat")
    def test_strips_markdown_from_response(self, mock_chat):
        mock_chat.return_value = "```python\nbpy.ops.mesh.primitive_cube_add(size=0.04)\n```"
        result = generate_bpy_code("create a cube")
        assert result == "bpy.ops.mesh.primitive_cube_add(size=0.04)"
