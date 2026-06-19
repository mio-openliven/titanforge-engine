# Architecture Notes

## Initial Shape

The first implementation should be a modular pipeline, not one giant script.

```text
titanforge/
  core/
  masks/
  layouts/
  terrain/
  schematics/
  preview/
  exporters/
  pipeline/
examples/
assets/
tests/
docs/
```

The repository now starts as a Python package with a command-line interface. This keeps the early pipeline simple, testable, and friendly to image/mask processing. Java or Minecraft-native tools can be added later as adapters when a specific exporter needs them.

## Pipeline Contract

Each stage should receive explicit inputs and produce explicit outputs. Intermediate artifacts should be inspectable so broken generation can be debugged without rerunning the entire world.

`WorldPlan` should become the first spatial contract between scenario-writer intent and terrain/export logic. It should hold world size, region bounds, story roles, and future placement anchors before Minecraft-specific adapters enter the picture.

That anchor layer now exists in simple deterministic form. Regions can expose points such as `arrival`, `shoreline`, `forest-core`, `ridge-vista`, or `center` so later routing and placement layers have explicit targets instead of guessing from raw rectangles alone.

The first route layer can now connect those anchors into a neutral `route-plan.json` plus `route-preview.png`. This is still diagnostic, but it gives later road, path, and traversal passes a deterministic skeleton.

The next neutral layer can now promote anchors and route midpoints into `placement-plan.json` plus `placement-preview.png`. This is still not Minecraft placement, but it gives future roads, settlements, viewpoints, and POI passes named target sites instead of raw geometry alone.

On top of that, a first `road-plan.json` plus `road-preview.png` can classify route segments into simple road intent such as `main-road` and `local-path`, with width hints like `wide` and `narrow`. This is still neutral planning data, not Minecraft block placement.

On top of roads and named sites, a first `settlement-plan.json` plus `settlement-preview.png` can sketch gate, core, harbor, and junction blockouts. This is still neutral planning data, but it starts turning the scenario-writer brief into readable place footprints instead of only lines and points.

Between raw region strips and traversal, a first `transition-plan.json` plus `transition-preview.png` can describe neighboring seams such as coast transitions, treeline rises, and settled edges. This gives later terrain and composition passes a deterministic place to thicken borders instead of guessing only from rectangles.

The first version-specific adapter can now stay outside core generation as `material-profile.json`. For Minecraft `1.21.11`, it maps neutral region, transition, road, and settlement kinds into starter block palettes without pretending export geometry already exists.

The next exporter-facing artifact can stay inspectable too: `export-request.json`. It translates the 1.21.11 material profile plus neutral bounds into simple region bands, transition bands, road strips, and settlement pads before any schematic or NBT writer exists.

On top of that, `chunk-plan.json` can translate those export requests into compact 16x16 chunk coverages. This stays much smaller than enumerating every touched chunk while still matching the coordinate system a future Minecraft writer will need.

The next exporter fixture can stay explicit too: `block-fixture.json`. It turns export requests into simple block cuboids with starter Y levels, so the team can test fixture/NBT ideas without pretending terrain-aware world writing already exists.

On top of that, `block-fixture.nbt` can exercise binary NBT writing without claiming full Minecraft structure compatibility yet. This lets the exporter layer start handling real binary payloads before chunk serialization and full format rules arrive.

`place-fixture.mcfunction` is the first directly executable Minecraft-facing artifact. It converts block cuboids into striped `fill` commands so large surfaces stay practical without waiting for full structure or world writers.

`clear-fixture.mcfunction` is the first reversible companion for that artifact. It mirrors the same cuboids with `air` fills, so a tester can iterate on placement without manually cleaning the world between passes.

`fixture-commands.txt` is the first tiny operator-facing guide for that flow. It keeps the exact `/reload`, place, and clear calls next to the artifacts so a non-developer tester does not have to inspect datapack internals.

`datapack-fixture/` is the next practical wrapper around that command output. It adds `pack.mcmeta` plus the packaged function path so the exporter layer starts resembling a real Minecraft datapack before committing to heavier formats.

`datapack-fixture.zip` is the first handoff-oriented wrapper around that folder. It keeps the same inspectable contents, but gives testers one copyable artifact for quick datapack import checks.

`project-draft` is now the first user-facing bridge on top of that contract. It writes a review page, `world-plan.json`, and a `draft-mask.png` that may be smaller than the logical world. The manifest records `blocksPerPixel` so large worlds stay planable without pretending the early PNG is already block-accurate export data.

The draft mask no longer needs to render every region as a full-height strip. Deterministic shape hints such as `coast-band`, `ridge-cap`, `oval-core`, and `settlement-core` make the draft easier to read while keeping generation logic simple and testable.

`project-location` is the next orchestration layer above that. It does not add new terrain logic; it simply wires `project-draft` into the existing location-pack pipeline and records the bridge metadata in one top-level manifest.

## Suggested Early Modules

- `core`: project loading, paths, logging, shared types.
- `masks`: image masks, regions, weights, transforms.
- `layouts`: high-level map composition and cinematic routing.
- `terrain`: heightmaps, biome/material passes, erosion-style operations.
- `schematics`: schematic metadata, placement rules, collision checks.
- `preview`: fast visual diagnostics before Minecraft export.
- `exporters`: Minecraft-compatible outputs.
- `versions`: version-specific rules, formats, palettes, and compatibility adapters.
- `pipeline`: orchestration, cache, stage execution.

## First Mask Pass

The initial `masks` module reads simple PNG masks without external dependencies and reports exact-color zone statistics. It does not generate terrain yet. This keeps the first image-input layer deterministic and easy to test.

The initial `preview` module can render a normalized mask preview PNG. It preserves known colors and marks unknown colors with a visible error color. Preview output should stay cheap and deterministic so it can run before expensive terrain or exporter work.

The initial `layouts` module writes a neutral JSON artifact from a PNG mask. It should describe intent and coverage, not Minecraft-specific blocks. Terrain, schematic, and exporter passes should consume this type of artifact instead of reparsing the original image.

The initial `terrain` module can render a grayscale heightmap preview from a mask layout. It is a diagnostic terrain artifact, not the final terrain algorithm. This lets us inspect height intent before adding coastline smoothing, erosion-style noise, or Minecraft exporters.

The next terrain layer should be a neutral terrain grid artifact. It should describe cells, elevations, surfaces, walkability, and buildability without leaking Minecraft block IDs or version rules into core generation.

`demo-mask` belongs to the mask tooling, not generation. Its job is to provide stable smoke-test input for the current pipeline.

`mask-cleanup-preview` is the first cleanup pass. It should stay conservative and inspectable: produce a preview artifact first, then later decide whether terrain generation should consume cleaned masks.

Terrain preview can optionally consume `mask-cleanup-preview.png`, but the layout/report path stays tied to the original mask. This separates "what the user drew" from "what a terrain pass may safely clean."

## First Location Pack

The first user-facing output is a location pack folder:

```text
mask.png
mask-preview.png
mask-cleanup-preview.png
layout.json
heightmap-preview.png
report.txt
manifest.json
```

This is intentionally not a Minecraft world yet. It gives the user something inspectable while keeping exporter work behind later adapters.

## First Project Draft Pack

The first scenario-writer output is a project draft pack:

```text
review.html
world-plan.json
draft-mask.png
draft-manifest.json
```

This pack sits one step earlier than a location pack. It exists so a non-technical user can define world size, premise, and regions in `titanforge.toml`, then immediately inspect a first spatial draft before touching raw PNG work.

## Design Bias

Start with a clear command-line workflow. Add a desktop UI only after the file formats and pipeline are stable enough.

## Version Strategy

Avoid scattering Minecraft-version checks through the engine. Keep version-specific behavior behind explicit adapters.

Priority target:

- Primary product target: Minecraft 1.21.11
- Secondary compatibility target: Minecraft 1.12.2

The safest path is to build a neutral internal map model first, then write version adapters from that model. That makes it possible to export downward to 1.12.2 without letting old-format constraints infect the whole engine.
