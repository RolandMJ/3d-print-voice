bl_info = {
    "name": "AI Bridge",
    "blender": (4, 0, 0),
    "category": "Interface",
    "version": (0, 1, 0),
    "author": "BlenderAI",
    "description": "HTTP server that receives and executes bpy code from an external AI agent",
}

import bpy
import json
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from queue import Queue, Empty

# Queue for passing code from HTTP thread → main thread
_command_queue = Queue()
# Queue for passing results from main thread → HTTP thread
_result_queue = Queue()

HOST = "127.0.0.1"
PORT = 6789
TIMER_INTERVAL = 0.05  # 50ms polling


class CommandHandler(BaseHTTPRequestHandler):
    """Handles POST /execute requests with bpy code."""

    def do_POST(self):
        if self.path != "/execute":
            self._respond(404, {"status": "error", "error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError) as e:
            self._respond(400, {"status": "error", "error": f"Invalid JSON: {e}"})
            return

        bpy_code = data.get("bpy_code")
        if not bpy_code or not isinstance(bpy_code, str):
            self._respond(400, {"status": "error", "error": "Missing or invalid 'bpy_code' field"})
            return

        # Send code to main thread and wait for result
        _command_queue.put(bpy_code)
        try:
            result = _result_queue.get(timeout=30)
        except Empty:
            self._respond(504, {"status": "error", "error": "Execution timed out (30s)"})
            return

        status_code = 200 if result["status"] == "ok" else 500
        self._respond(status_code, result)

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok"})
            return
        self._respond(404, {"status": "error", "error": "Not found"})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress default stderr logging to keep Blender console clean."""
        pass


def _process_queue():
    """Timer callback — runs on Blender's main thread. Pulls code from the
    command queue, executes it, and pushes the result to the result queue."""
    try:
        bpy_code = _command_queue.get_nowait()
    except Empty:
        return TIMER_INTERVAL

    result = _execute_bpy(bpy_code)
    _result_queue.put(result)
    return TIMER_INTERVAL


def _execute_bpy(code):
    """Execute bpy code string and return a result dict."""
    exec_globals = {"bpy": bpy, "__builtins__": __builtins__}
    try:
        bpy.ops.ed.undo_push(message="AI Bridge command")
        exec(code, exec_globals)
        return {"status": "ok", "result": "executed"}
    except Exception:
        return {"status": "error", "error": traceback.format_exc()}


_server = None
_server_thread = None


def _start_server():
    global _server, _server_thread
    if _server is not None:
        return

    _server = HTTPServer((HOST, PORT), CommandHandler)
    _server_thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _server_thread.start()
    print(f"[AI Bridge] HTTP server listening on {HOST}:{PORT}")


def _stop_server():
    global _server, _server_thread
    if _server is not None:
        _server.shutdown()
        _server = None
        _server_thread = None
        print("[AI Bridge] HTTP server stopped")


def register():
    _start_server()
    bpy.app.timers.register(_process_queue, first_interval=TIMER_INTERVAL, persistent=True)
    print("[AI Bridge] Addon registered")


def unregister():
    if bpy.app.timers.is_registered(_process_queue):
        bpy.app.timers.unregister(_process_queue)
    _stop_server()
    print("[AI Bridge] Addon unregistered")


if __name__ == "__main__":
    register()
