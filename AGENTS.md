# TitanForge Agent Protocol

## Identity

TitanForge Engine is an external toolkit for generating cinematic Minecraft map/location artifacts. It is not a Minecraft mod, plugin, or game.

## Start Every Task

Run:

```powershell
git status --short --branch
git pull origin main
```

Read these files before changing behavior:

- `README.md`
- `docs/knowledge/PRD.md`
- `docs/knowledge/PROJECT_MAP.md`
- `docs/knowledge/DECISIONS.md`
- `docs/knowledge/ROADMAP.md`
- `docs/knowledge/LOCATION_PACKS.md`
- `tasks.md`

## Work Loop

1. Pick one task only.
2. Move it to `In Progress` in `tasks.md` if it is a planned backlog task.
3. Implement the smallest complete pass.
4. Run tests and smoke checks.
5. Update docs if commands or behavior changed.
6. Move the task to `Done` only when verified.
7. Commit and push to `main` when clean.

## Test Commands

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
python -m compileall -q src tests
```

Main smoke:

```powershell
$env:PYTHONPATH='src'
python -m titanforge build-location previews\demo-location --width 128 --height 128 --use-cleanup-for-heightmap
```

Night smoke:

```powershell
$env:PYTHONPATH='src'
python -m titanforge night-run night_runs\smoke --count 4 --width 64 --height 64 --size-step 16 --max-minutes 5
```

## Scope Rules

- Keep core generation neutral.
- Keep Minecraft-version logic in adapters.
- Primary target: Minecraft `1.21.11`.
- Compatibility target: Minecraft `1.12.2`.
- Prefer CLI and file artifacts before GUI.
- Prefer location packs before Minecraft export.
- Prefer overnight deterministic runs over unattended AI coding.
- Do not import donor code without inventory and license review.

## New PC Protocol

When this repo is opened from another PC or a new Codex chat:

1. Read `README.md`.
2. Read this file.
3. Run `git status --short --branch`.
4. Run `git pull origin main`.
5. Run tests.
6. Continue one task only.

If the user asks for unattended work, use `night-run` and reports. Do not keep editing code forever without human review.

## User Interaction

When unsure, offer 3 micro-options and recommend one.

If the user says any letter or "continue", choose the safest next high-value pass.

Explain status simply. Avoid jargon walls.

If this chat has a declared role, do not do work outside that role. Redirect with the correct mini-prompt from `docs/operations/WINDOW_SYSTEM.md`.
