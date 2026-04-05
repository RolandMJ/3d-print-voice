# Intellectual Property Notice

## Copyright

Copyright (c) 2026 Roland Preisach. All rights reserved.

This software and associated documentation files (the "Software") are the
proprietary intellectual property of Roland Preisach. Unauthorized copying,
modification, distribution, or use of this Software, via any medium, is
strictly prohibited without express written permission from the copyright holder.

## What This Covers

This IP notice applies to:

- The software architecture and system design
- All source code in this repository
- The prompt engineering (prompts/system.md and any derivatives)
- The integration method (external agent → HTTP bridge → Blender bpy execution)
- The launcher and desktop integration system
- Documentation, diagrams, and written materials

## What This Does NOT Cover

- The Blender application itself (GPL licensed by the Blender Foundation)
- The Blender Python API (bpy) — part of Blender
- Third-party libraries listed in requirements.txt (each has its own license)
- Ollama (MIT licensed)
- Qwen2.5-Coder model weights (Apache 2.0 licensed by Alibaba/Qwen team)
- faster-whisper (MIT licensed)

## AI-Assisted Development Disclosure

This software was developed with the assistance of AI tools:

**Development-time tools (used to write this software):**
- **Claude Code** (Anthropic) — used for code generation, architecture design,
  and documentation under the direction of the human author

**Runtime tools (used when this software runs):**
- **Ollama** — local LLM inference server (MIT license)
- **Qwen2.5-Coder 14B-Instruct** — local coding model that translates natural
  language to bpy code (Apache 2.0 license, Alibaba/Qwen team)
- **faster-whisper** — local speech-to-text model (MIT license)

The human author (Roland Preisach) provided:
- The original concept and product vision
- Architecture decisions and technical constraints
- All creative and strategic direction
- Review and approval of all generated code
- System prompt engineering (the "intelligence" of the bpy translation)
- Model selection research and hardware optimization decisions

Per Anthropic's Terms of Service, outputs generated using Claude are owned by
the user who generated them. The human author maintains full ownership of all
AI-assisted outputs in this repository.

The open-source models used at runtime (Qwen2.5-Coder, faster-whisper) are
licensed under permissive terms (Apache 2.0 / MIT) that allow commercial use
without restriction on the outputs they generate.

## Evidence of Authorship

Development history is maintained through:
- Git commit history with timestamps and descriptive messages
- Development log: [docs/DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)
- Architecture documentation: [docs/architecture.svg](architecture.svg)
- Implementation plans: [docs/plans/](plans/)
- Changelog: [docs/CHANGELOG.md](CHANGELOG.md)
- Dated session logs in the `logs/` directory (gitignored for privacy)

## Contact

Roland Preisach
roland@rmj-project.de
