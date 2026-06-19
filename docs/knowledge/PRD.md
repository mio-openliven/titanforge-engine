# TitanForge Engine PRD

## Product

TitanForge Engine is a CLI-first toolkit for generating cinematic Minecraft map/location artifacts from visual plans and structured rules.

## User

Primary user: one creator/developer using Codex to build tools for Minecraft cinematic location production.

Future users: builders, server owners, video teams, modders, and creators who need large map drafts faster than manual building.

## Problem

Large Minecraft locations take too long to plan and block out by hand. Existing real-world map generators can produce broken water, floating structures, missing roofs, and ugly noisy terrain.

## Goal

Create a controlled deterministic pipeline:

```text
world brief / project draft / world plan / PNG mask / structured layout
-> previews
-> validation report
-> terrain/location artifacts
-> later schematic/world export
```

## Current MVP

Project draft pack:

```text
review.html
world-plan.json
draft-mask.png
draft-manifest.json
```

Location pack:

```text
mask.png
mask-preview.png
mask-cleanup-preview.png
layout.json
heightmap-preview.png
report.txt
review.html
manifest.json
```

The current bridge from story idea to generation is a project draft pack. It keeps the world brief readable, gives regions deterministic spatial bounds through `WorldPlan`, and auto-scales large worlds into a manageable `draft-mask.png` with `blocksPerPixel` metadata and human-readable scale warnings.

`WorldPlan` should also carry simple story anchors so the engine can later place routes, settlements, viewpoints, and reveals against named points instead of only against region rectangles.

The next user-facing bridge is `project-location`: one command from `titanforge.toml` to `draft/` plus `location/`, with a bridge manifest that keeps logical world size and raster scale explicit.

Draft artifacts should feel like rough places, not spreadsheet stripes. Simple deterministic region shapes are acceptable before full composition rules or Minecraft export exist.

## Must Have

- CLI workflow.
- Human-readable planning surface before raw artifact overload.
- Inspectable intermediate files.
- Tests for each pass.
- Git-backed small commits.
- Neutral internal model before Minecraft-specific export.
- Simple reports understandable by a non-engineer.

## Not Doing Yet

- GUI.
- AI-generated worlds.
- Full Minecraft world export.
- Complex buildings.
- Real-time preview.
- Importing huge donor code.

## Success For First Week

The user can run one command, get a useful project draft or location pack, inspect previews, read a report, and understand what the engine will generate next.
