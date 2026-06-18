# TitanForge Engine

TitanForge Engine is an early Python toolkit for turning simple map inputs into inspectable Minecraft map-planning artifacts.

It currently works with PNG masks and produces preview images, layout JSON, heightmap previews, validation reports, and small location-pack folders. It does **not** yet export playable Minecraft worlds or schematics.

For a short handoff guide, see [START_HERE.md](START_HERE.md).

## Status

This repository is an MVP-stage tool, not a finished map generator.

Working now:

- project config loading;
- inventory scans for source/donor folders;
- PNG mask read/write;
- demo mask generation;
- mask analysis and cleanup previews;
- mask-to-layout JSON;
- grayscale heightmap previews;
- validation reports;
- simple human-readable location summaries inside reports;
- location-pack folder output;
- resilient batch generation with `night-run`;
- unit tests for the current pipeline.

Not implemented yet:

- Minecraft world export;
- schematic export;
- structure placement;
- asset library;
- GUI/editor;
- production-quality terrain generation.

## Quick Start

Use Python 3.11 or newer.

```powershell
$env:PYTHONPATH = "src"
python -m titanforge info
python -m titanforge demo-mask out\demo-mask.png
python -m titanforge build-location out\demo-location --width 128 --height 128 --use-cleanup-for-heightmap
```

The `build-location` command creates:

```text
mask.png
mask-preview.png
mask-cleanup-preview.png
layout.json
heightmap-preview.png
report.txt
manifest.json
```

## Tests

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
python -m compileall -q src tests
```

## Night Runs

`night-run` generates a batch of location packs and writes progress after every case. It is useful for unattended local experiments.

```powershell
$env:PYTHONPATH = "src"
python -m titanforge night-run night_runs\first --count 200 --width 128 --height 128 --size-step 32 --max-minutes 480
```

Outputs are written under `night_runs/`, which is intentionally ignored by Git.

Details: [docs/operations/NIGHT_RUNS.md](docs/operations/NIGHT_RUNS.md)

## Design Direction

The project keeps the core pipeline Minecraft-version-neutral. Version-specific behavior should live behind exporters/adapters.

Current planning targets:

- primary: Minecraft `1.21.11`;
- compatibility target: Minecraft `1.12.2`.

The near-term goal is to make the preview and location-pack workflow reliable before starting GUI work or Minecraft export.

## Documentation

- [START_HERE.md](START_HERE.md) - short handoff for humans and new Codex/GPT chats.
- [AGENTS.md](AGENTS.md) - working rules for coding agents.
- [docs/knowledge/PROJECT_MAP.md](docs/knowledge/PROJECT_MAP.md) - project structure and goals.
- [docs/knowledge/ARCHITECTURE.md](docs/knowledge/ARCHITECTURE.md) - architecture notes.
- [docs/knowledge/ROADMAP.md](docs/knowledge/ROADMAP.md) - phased roadmap.
- [docs/knowledge/DONORS.md](docs/knowledge/DONORS.md) - donor/research notes.
- [docs/knowledge/RISKS.md](docs/knowledge/RISKS.md) - current risks.

## Development Rules

- Keep changes small and testable.
- Do not mix GUI, exporter, terrain, AI prompt logic, and asset management in one pass.
- Do not import donor code without checking the license.
- Keep generated outputs out of Git unless they are intentional fixtures.

## License

MIT License. See [LICENSE](LICENSE).
