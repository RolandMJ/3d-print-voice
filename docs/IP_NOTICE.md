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
- Documentation, diagrams, and written materials

## What This Does NOT Cover

- The Blender application itself (GPL licensed by the Blender Foundation)
- The Blender Python API (bpy) — part of Blender
- Third-party libraries listed in requirements.txt (each has its own license)
- The Claude API — operated by Anthropic under their terms of service

## AI-Assisted Development Disclosure

This software was developed with the assistance of AI tools, specifically:

- **Claude Code** (Anthropic) — used for code generation, architecture design,
  and documentation under the direction of the human author
- **Claude API** (Anthropic, claude-sonnet-4-20250514) — used at runtime as the
  natural language to bpy code translation engine

The human author (Roland Preisach) provided:
- The original concept and product vision
- Architecture decisions and technical constraints
- All creative and strategic direction
- Review and approval of all generated code
- System prompt engineering (the "intelligence" of the bpy translation)

Per Anthropic's Terms of Service, outputs generated using Claude are owned by
the user who generated them. The human author maintains full ownership of all
AI-assisted outputs in this repository.

## Evidence of Authorship

Development history is maintained through:
- Git commit history with timestamps (this repository)
- Development log: [docs/DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)
- Architecture documentation: [docs/architecture.svg](architecture.svg)
- Dated session logs in the `logs/` directory

## Contact

Roland Preisach
roland@rmj-project.de
