import json
import urllib.request
import urllib.error

BLENDER_URL = "http://127.0.0.1:6789"


def execute(bpy_code: str) -> dict:
    """POST bpy code to the Blender addon and return the response dict."""
    payload = json.dumps({"bpy_code": bpy_code}).encode("utf-8")
    req = urllib.request.Request(
        f"{BLENDER_URL}/execute",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"status": "error", "error": f"HTTP {e.code}: {body}"}
    except urllib.error.URLError as e:
        return {"status": "error", "error": f"Connection failed: {e.reason}. Is Blender running with the AI Bridge addon enabled?"}


def health_check() -> bool:
    """Check if the Blender addon HTTP server is reachable."""
    req = urllib.request.Request(f"{BLENDER_URL}/health", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            return data.get("status") == "ok"
    except Exception:
        return False
