# TitanForge Engine Project Map

## Identity

Name: TitanForge Engine

Category: external toolkit, procedural generation engine, development tool.

Short description: TitanForge Engine is a procedural toolkit for generating cinematic Minecraft maps.

Not a game. Not a Minecraft mod. Not a server plugin. The engine may export data that Minecraft tools can consume.

## Product Goal

Build a modular pipeline that can generate cinematic Minecraft maps from structured inputs: masks, layout rules, terrain passes, schematic placement, previews, and exporters.

Version priorities:

- Primary product target: Minecraft 1.21.11
- Secondary compatibility target: Minecraft 1.12.2

The primary product should serve our own long-term engine first. External client needs can shape compatibility work, but should not control the core architecture.

## Core Workflow

1. Read project configuration.
2. Load masks and source assets.
3. Resolve layout and region intent.
4. Run terrain passes.
5. Place structures, schematics, details, and cinematic anchors.
6. Generate previews for review.
7. Export Minecraft-compatible outputs.

## Main Systems

- Config and project format
- Mask processing
- Layout generation
- Terrain passes
- Schematic and structure placement
- Preview and diagnostics
- Exporters
- Version compatibility layer
- Asset library
- CLI or desktop control surface
- Test fixtures and example maps

## Repo Principles

- Keep code and knowledge close together.
- Treat large binary assets with Git LFS.
- Prefer small examples before large production maps.
- Preserve decisions in `DECISIONS.md`.
- Keep donor research documented in `DONORS.md`.

## Current State

GitHub repository exists. It may be public while the project is used as an open learning MVP and portfolio piece.

Repository URL: https://github.com/mio-openliven/titanforge-engine

Git, GitHub CLI, and Git LFS are configured on the PC.

The local repo is at:

```text
C:\Users\Li2Fox\Documents\ГИГАНТ
```
