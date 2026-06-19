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

The next neutral artifact is a route plan that connects those anchors into a first traversal skeleton. It is not yet a block path or Minecraft road, but it gives the engine a deterministic map of likely movement and reveal lines.

Before traversal alone carries too much burden, the draft should also expose simple transition seams between neighboring regions so terrain, roads, and later exporters can read where coast joins town, forest climbs into ridge, or settlement gives way to wilderness.

The first Minecraft-specific layer should remain inspectable: a simple `material-profile.json` for `1.21.11` that maps neutral planning intent into starter block palettes before any real world or schematic export is attempted.

On top of that, the first exporter-facing contract should still stay readable: an `export-request.json` that tells a future 1.21.11 exporter which region bands, seam bands, road strips, and settlement pads to materialize.

On top of that, a placement plan can promote anchor roles and route junctions into named neutral sites such as entry plazas, dock edges, mystery clusters, overlooks, and route junctions before any Minecraft-specific exporter starts.

The next neutral layer can promote traversal lines plus named sites into a first road plan so the engine starts distinguishing main roads from local paths before block or schematic export exists.

On top of that, the engine can now turn selected placement sites plus road access into a first settlement blockout plan so a creator sees rough gates, harbor pads, village cores, and junction hubs before any Minecraft exporter exists.

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
