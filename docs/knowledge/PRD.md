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

The next export-facing contract should become chunk-aware without exploding in size: a compact `chunk-plan.json` that records chunk coverages for those operations instead of pretending the writer can already stream real world files.

On top of that, the first block-facing fixture should stay inspectable: a `block-fixture.json` with cuboid operations and starter Y levels for 1.21.11, so the pipeline can approach real block output without committing to full world export too early.

The next safe step is a binary `block-fixture.nbt` artifact that round-trips through a small internal codec. This proves the exporter layer can handle real binary NBT payloads before it claims Minecraft-ready structure serialization.

The next user-meaningful export step is an executable `place-fixture.mcfunction`. It gives the pipeline a real Minecraft command artifact before the project commits to full schematic or world formats.

The next practical wrapper is a `datapack-fixture/` folder with `pack.mcmeta` and a packaged function path. This keeps the workflow inspectable while moving one step closer to something a tester can drop into a world.

That wrapper should also be emitted as `datapack-fixture.zip` so the first tester workflow is one file copy, not manual repackaging.

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
