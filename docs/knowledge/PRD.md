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
PNG mask / structured layout
-> previews
-> validation report
-> terrain/location artifacts
-> later schematic/world export
```

## Current MVP

Location pack:

```text
mask.png
mask-preview.png
mask-cleanup-preview.png
layout.json
heightmap-preview.png
report.txt
manifest.json
```

## Must Have

- CLI workflow.
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

The user can run one command, get a useful location pack, inspect previews, read a report, and understand what the engine will generate next.
