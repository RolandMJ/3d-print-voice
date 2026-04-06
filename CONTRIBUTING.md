# Contributing to 3DPrintVoice

Thanks for your interest in contributing. Here's how to get started.

## Reporting Bugs

[Open an issue](https://github.com/RolandMJ/3d-print-voice/issues) with:

- What you did (the command you typed or said)
- What you expected to happen
- What actually happened (error message, wrong result, nothing)
- Your system info: GPU model, VRAM, Blender version, model tier (Full/Medium)

## Suggesting Features

Open an issue with the `enhancement` label. Describe:

- What problem it solves
- How you'd expect it to work (example commands)
- Whether it fits an existing category or needs a new one

## Code Contributions

### Setup

1. Fork the repo and clone your fork
2. Follow the [Setup Guide](docs/SETUP_GUIDE.md) to get a working installation
3. Create a feature branch: `git checkout -b my-feature`

### Guidelines

- **Keep it local.** No cloud APIs, no external services at runtime. Everything must work offline after initial setup.
- **Blender addon restrictions.** `addon/ai_bridge.py` can only use Python stdlib + `bpy`. No third-party imports inside the addon.
- **Test your changes.** Run `pytest tests/ -v` before submitting.
- **One thing per PR.** Bug fix? One PR. New command category? One PR. Don't bundle unrelated changes.
- **System prompt changes.** If you add commands to `prompts/system.md`, test them with both the 14B (Full) and 7B (Medium) models. Commands that only work on 14B should be noted.

### Commit Messages

Use conventional commits:

```
feat: add spiral staircase recipe
fix: boolean union fails on non-manifold meshes
docs: update cheat sheet with new DIN hardware commands
```

### Pull Requests

1. Push your branch to your fork
2. Open a PR against `main`
3. Describe what the change does and why
4. Include test output or a screenshot/recording if it's a visual change

## Code of Conduct

Be respectful. This is a hobby project built in spare time. Constructive feedback is welcome. Demands and entitlement are not.

## Questions?

Open a [discussion](https://github.com/RolandMJ/3d-print-voice/issues) or reach out via the issue tracker.
