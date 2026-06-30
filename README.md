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
- a first Minecraft 1.21.11 chunk-plan artifact aligned to 16x16 chunk bounds;
- a first Minecraft 1.21.11 block-fixture artifact with cuboid block operations;
- a first Minecraft 1.21.11 NBT-oriented fixture artifact for binary export experiments;
- a first Minecraft 1.21.11 mcfunction fixture exporter with real `fill` commands;
- a first Minecraft 1.21.11 clear-fixture mcfunction companion for reversible test placement;
- a first fixture-commands guide artifact with exact `/function` commands for testing and explicit unsupported-target warnings;
- a first fixture-summary artifact with rough bounds, fill-command counts, and safety warnings before world testing;
- a first Minecraft 1.21.11 datapack fixture package with `pack.mcmeta` and packaged function file;
- a first zipped Minecraft 1.21.11 datapack fixture package for easy handoff into a test world;
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
python -m titanforge preset-catalog
python -m titanforge preset-catalog --json
python -m titanforge first-map out\my-first-world --name "My First World" --width 2048 --length 1536 --preset coastal-valley --max-draft-side 256
python -m titanforge first-map-status out\my-first-world
python -m titanforge first-map-test-world out\my-first-world --max-side 128
python -m titanforge init-project out\my-first-world --name "My First World" --width 2048 --length 1536 --preset coastal-valley
python -m titanforge project-draft examples\tiny_project\titanforge.toml out\tiny-project-draft --max-draft-side 256
python -m titanforge project-location examples\tiny_project\titanforge.toml out\tiny-project-location --max-draft-side 256 --use-cleanup-for-heightmap
python -m titanforge plan examples\tiny_project\titanforge.toml --review-page out\project-review.html --world-plan out\world-plan.json
python -m titanforge demo-mask out\demo-mask.png
python -m titanforge build-location out\demo-location --width 128 --height 128 --use-cleanup-for-heightmap
python -m titanforge coastline-smoothing-preview out\demo-location\mask.png out\demo-location\coastline-smoothing-preview.png
python -m titanforge terrain-color-preview out\demo-location\layout.json out\demo-location\terrain-color-preview.png --mask out\demo-location\mask-cleanup-preview.png
python -m titanforge terrain-grid out\demo-location\layout.json out\demo-location\terrain-grid.json --mask out\demo-location\mask-cleanup-preview.png
```

Use `first-map` when you want the fastest path from idea to the first reviewable map pack. It now writes a starter `titanforge.toml`, builds the first `project-location` output, writes a small root manifest, writes a root `review.html`, labels the requested world scale in plain language, surfaces the preset story intent and key regions, and tells you to open that root page first.

Use `first-map-status` when the pack already exists and you only need the current handoff summary again. It reads `first-map-manifest.json` and now reprints the preset intent, world-scale guidance, review order, next actions, Minecraft caution notes, and saved command hints without rebuilding anything.

Use `first-map-test-world` when you already have a `first-map` project and want the shortest path to one experimental Minecraft manual-open candidate without hunting for `titanforge.toml` yourself. It resolves the config from `first-map-manifest.json`, writes a donor-backed `minecraft-test-world` folder, and prints the same checklist/report handoff used by `anvil-test-world`. Install the optional extra first with `py -3.11 -m pip install -e .[donor-spikes]`.

`fixture-summary.json` now also carries a plain `starterTest` verdict: `safe`, `caution`, or `blocked`. The same verdict is surfaced in `location/review.html` and `first-map-status`, so a scenario writer does not need to infer first-test risk from raw warning strings alone.

Use `init-project` when you want a starter `titanforge.toml` without hand-writing the first world brief. The command writes a preset-backed config for a safe `64 .. 32000` block range, gives a plain-language world-scale label for the chosen size, surfaces the preset story intent and starter regions, reminds you that `width` and `length` can be changed later inside `titanforge.toml`, and prints the exact next `project-location` command to run.

Use `preset-catalog` first when you do not yet know whether you want the coast, frontier, or island starter. It prints the story intent, player feeling, and key starter regions for every preset in one short CLI report. Use `preset-catalog --json` when a future UI or helper script needs the same data in a schema-tagged payload instead of text parsing.

Open `out\tiny-project-draft\review.html` first. That folder now also contains `world-plan.json`, `draft-mask.png`, and `draft-manifest.json`.
The review page now also explains which draft artifacts to open next, including `fixture-summary.json`, `fixture-commands.txt`, and `datapack-fixture.zip`.
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
chunk-plan.json
block-fixture.json
block-fixture.nbt
structure-template.nbt
place-fixture.mcfunction
clear-fixture.mcfunction
fixture-commands.txt
fixture-summary.json
datapack-fixture\
datapack-fixture.zip
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

Use it when you want the first map-planning artifact directly from `titanforge.toml` before hand-editing PNG masks. Regions now use simple deterministic shape hints instead of only full-height strips, neighboring regions expose a first neutral transition layer, anchors are connected into a first neutral route plan, key sites are promoted into a first neutral placement plan, those routes are promoted again into a first neutral road plan, placement hubs become a first neutral settlement blockout draft, and the primary 1.21.11 target now gets a first material profile, export request, chunk plan, block fixture, binary NBT-oriented fixture, vanilla `structure-template.nbt`, executable `mcfunction`, a reversible `clear-fixture.mcfunction`, a local `fixture-commands.txt` guide that warns on unsupported or oversized structure-template cases, a `fixture-summary.json` safety snapshot with warnings for overly large runs, a packaged datapack fixture, and a ready-to-copy `datapack-fixture.zip`. Very large worlds still emit the structure-template artifact, but it falls back to a safe placeholder and tells you to use the `mcfunction` or datapack path instead of `/place template`.

The `project-location` command creates:

```text
draft\
location\
project-location-manifest.json
```

Use it when you want one command from `titanforge.toml` to an inspectable location pack. The bridge manifest keeps `blocksPerPixel` visible so the draft raster is not confused with the logical world size, and it now points at the draft material, export-request, datapack zip, transition, route, placement, road, and settlement artifacts too.
When the location pack came from `project-location`, its `location/review.html` now also links back to the key draft-side files like `fixture-summary.json`, `fixture-commands.txt`, and `datapack-fixture.zip`.
That same location review page now also shows the draft fixture command count and footprint inline, so a tester can judge scope without opening the JSON separately.
It now also shows the exact next Minecraft test commands inline, so the tester does not need to leave the review page to find `/reload` or `/function` calls.

The `first-map` command creates:

```text
review.html
first-map-manifest.json
titanforge.toml
first-map\
```

Use it when you want the quickest scenario-writer flow. Open the root `review.html` first; it now explains the preset story intent, the key starter regions, the logical world size, the plain-language world scale, the smaller draft raster, and the `blocksPerPixel` bridge before you jump into `first-map\location\review.html`, `first-map\draft\review.html`, or the Minecraft handoff files. The root `first-map-manifest.json` now also records that same guidance plus a machine-readable open order, next-action plan, command hints, and Minecraft handoff artifact order for future UI layers. If you revisit the folder later, `python -m titanforge first-map-status out\my-first-world` prints that handoff summary again without rerunning generation, and `python -m titanforge first-map-test-world out\my-first-world --max-side 128` gives the shortest donor-backed path to a throwaway Minecraft manual-open candidate.

## Optional Donor Spike

If you want one narrow experiment toward real world-region output, install the optional donor spike dependency:

```powershell
py -3.11 -m pip install -e .[donor-spikes]
python -m titanforge anvil-region-spike examples\tiny_project\titanforge.toml out\tiny-anvil-spike --max-side 128
python -m titanforge anvil-save-shell examples\tiny_project\titanforge.toml out\tiny-save-shell --max-side 128
python -m titanforge anvil-test-world examples\tiny_project\titanforge.toml out\tiny-test-world --max-side 128
```

This writes one sampled `region\r.0.0.mca`, a manifest, and a short README. It is intentionally clipped to one chunk-aligned window inside one safe region file. It proves a donor-backed `.mca` write/read path without claiming that TitanForge already exports full playable worlds.
The `anvil-save-shell` wrapper goes one step further: it creates a save-like folder under `save-shell\`, keeps the sampled region inside `save-shell\region\`, and tells you the next manual test step for MCA Selector or for copying that one region into a backed-up throwaway world.
`anvil-test-world` is the next honest candidate: it writes `test-world\level.dat`, `test-world\session.lock`, and `test-world\region\r.0.0.mca`, but it still labels the result as an experimental throwaway manual-open shell rather than claiming verified world export.
That same `anvil-test-world` output now also writes `verification-checklist.txt` and `verification-report.json` at the root so the manual open test can be recorded instead of guessed later.
The intended handoff order is explicit: open `verification-checklist.txt` first, then record the outcome in `verification-report.json`.
When the manual test starts or finishes, update the report through CLI instead of hand-editing JSON, for example:

```powershell
python -m titanforge anvil-test-world-verify out\tiny-test-world\verification-report.json --check minecraft-world-list --check-status in_progress --check-note "World copied into a throwaway saves folder."
python -m titanforge anvil-test-world-status out\tiny-test-world
```

The status command now shows both the top-level verification state and each per-check state from `verification-report.json`, and it highlights failed checks in one compact line so a broken manual step does not get buried in the longer list.

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
