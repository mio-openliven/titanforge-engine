# TitanForge Engine

TitanForge Engine is an early Python toolkit for turning simple map inputs into inspectable Minecraft map-planning artifacts.

It currently works with PNG masks and produces preview images, terrain color previews, layout JSON, heightmap previews, validation reports, and small location-pack folders. It does **not** yet export playable Minecraft worlds or schematics.

For a short handoff guide, see [START_HERE.md](START_HERE.md).

## Status

This repository is an MVP-stage tool, not a finished map generator.

Working now:

- project draft packs from `titanforge.toml`;
- bridged project-location packs from `titanforge.toml`;
- region-specific draft shapes for sea, forests, settlements, and mountains;
- world-plan story anchors for arrivals, shorelines, forest cores, ridge vistas, and village hearts;
- neutral transition-plan and transition-preview artifacts built from neighboring region seams;
- a first Minecraft 1.21.11 material-profile adapter built from neutral planning artifacts;
- a first Minecraft 1.21.11 export-request artifact built from neutral planning artifacts;
- neutral route-plan and route-preview artifacts built from world-plan anchors;
- neutral placement-plan and placement-preview artifacts built from anchors and routes;
- neutral road-plan and road-preview artifacts built from routes and placement sites;
- neutral settlement-plan and settlement-preview artifacts built from placement sites and roads;
- project config loading;
- human-readable world brief review pages from project config;
- inventory scans for source/donor folders;
- PNG mask read/write;
- demo mask generation;
- mask analysis, cleanup previews, and coastline smoothing previews;
- mask-to-layout JSON;
- terrain color previews;
- grayscale heightmap previews;
- validation reports;
- simple human-readable location summaries inside reports;
- static HTML review pages inside location packs;
- neutral terrain grid JSON artifacts for future generation/export layers;
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
python -m titanforge project-draft examples\tiny_project\titanforge.toml out\tiny-project-draft --max-draft-side 256
python -m titanforge project-location examples\tiny_project\titanforge.toml out\tiny-project-location --max-draft-side 256 --use-cleanup-for-heightmap
python -m titanforge plan examples\tiny_project\titanforge.toml --review-page out\project-review.html --world-plan out\world-plan.json
python -m titanforge demo-mask out\demo-mask.png
python -m titanforge build-location out\demo-location --width 128 --height 128 --use-cleanup-for-heightmap
python -m titanforge coastline-smoothing-preview out\demo-location\mask.png out\demo-location\coastline-smoothing-preview.png
python -m titanforge terrain-color-preview out\demo-location\layout.json out\demo-location\terrain-color-preview.png --mask out\demo-location\mask-cleanup-preview.png
python -m titanforge terrain-grid out\demo-location\layout.json out\demo-location\terrain-grid.json --mask out\demo-location\mask-cleanup-preview.png
```

Open `out\tiny-project-draft\review.html` first. That folder now also contains `world-plan.json`, `draft-mask.png`, and `draft-manifest.json`.
Large worlds are intentionally scaled into a manageable draft mask. The manifest records `blocksPerPixel` so a 32000-wide world can still be planned without generating a gigantic PNG too early. Draft and project-location commands now also emit human-readable warnings when that scale starts hiding fine detail, when a huge world brief defines too few regions, or when too many regions collapse into the same zone family.
`world-plan.json` now also includes deterministic anchors inside each region so later placement, roads, or export adapters have explicit story points to target.

The `build-location` command creates:

```text
mask.png
mask-preview.png
mask-cleanup-preview.png
coastline-smoothing-preview.png
layout.json
terrain-color-preview.png
heightmap-preview.png
report.txt
review.html
manifest.json
```

Open `review.html` in a browser to inspect the first local TitanForge review page for that pack. It now includes coastline smoothing and terrain color drafts before the grayscale heightmap.

The `project-draft` command creates:

```text
review.html
world-plan.json
material-profile.json
export-request.json
transition-plan.json
transition-preview.png
route-plan.json
route-preview.png
placement-plan.json
placement-preview.png
road-plan.json
road-preview.png
settlement-plan.json
settlement-preview.png
draft-mask.png
draft-manifest.json
```

Use it when you want the first map-planning artifact directly from `titanforge.toml` before hand-editing PNG masks. Regions now use simple deterministic shape hints instead of only full-height strips, neighboring regions expose a first neutral transition layer, anchors are connected into a first neutral route plan, key sites are promoted into a first neutral placement plan, those routes are promoted again into a first neutral road plan, placement hubs become a first neutral settlement blockout draft, and the primary 1.21.11 target now gets both a first material profile and a first export request artifact for future export adapters.

The `project-location` command creates:

```text
draft\
location\
project-location-manifest.json
```

Use it when you want one command from `titanforge.toml` to an inspectable location pack. The bridge manifest keeps `blocksPerPixel` visible so the draft raster is not confused with the logical world size, and it now points at the draft material, export-request, transition, route, placement, road, and settlement artifacts too.

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
