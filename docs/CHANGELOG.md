# Changelog

All notable changes to BlenderAI are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-04-05

### Added
- Blender addon (ai_bridge.py) with HTTP server on port 6789
- POST /execute endpoint for receiving and executing bpy code
- GET /health endpoint for connection verification
- Thread-safe command queue with bpy.app.timers for main thread execution
- Claude API client (claude_client.py) using claude-sonnet-4-20250514
- System prompt (prompts/system.md) with bpy expertise and output contract
- Blender HTTP client (blender_client.py) with health check and error handling
- Terminal input loop (main.py) for text-based interaction
- Session logging to logs/ directory (every command and generated code)
- .env-based API key management
- Project documentation (setup guide, architecture diagram, IP notice)
