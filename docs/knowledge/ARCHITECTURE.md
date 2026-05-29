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

## Design Bias

Start with a clear command-line workflow. Add a desktop UI only after the file formats and pipeline are stable enough.

## Version Strategy

Avoid scattering Minecraft-version checks through the engine. Keep version-specific behavior behind explicit adapters.

Priority target:

- Primary product target: Minecraft 1.21.11
- Secondary compatibility target: Minecraft 1.12.2

The safest path is to build a neutral internal map model first, then write version adapters from that model. That makes it possible to export downward to 1.12.2 without letting old-format constraints infect the whole engine.
