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

`project-draft` is now the first user-facing bridge on top of that contract. It writes a review page, `world-plan.json`, and a `draft-mask.png` that may be smaller than the logical world. The manifest records `blocksPerPixel` so large worlds stay planable without pretending the early PNG is already block-accurate export data.

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
