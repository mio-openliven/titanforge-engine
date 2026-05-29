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

## Pipeline Contract

Each stage should receive explicit inputs and produce explicit outputs. Intermediate artifacts should be inspectable so broken generation can be debugged without rerunning the entire world.

## Suggested Early Modules

- `core`: project loading, paths, logging, shared types.
- `masks`: image masks, regions, weights, transforms.
- `layouts`: high-level map composition and cinematic routing.
- `terrain`: heightmaps, biome/material passes, erosion-style operations.
- `schematics`: schematic metadata, placement rules, collision checks.
- `preview`: fast visual diagnostics before Minecraft export.
- `exporters`: Minecraft 1.12.2-compatible outputs.
- `pipeline`: orchestration, cache, stage execution.

## Design Bias

Start with a clear command-line workflow. Add a desktop UI only after the file formats and pipeline are stable enough.
