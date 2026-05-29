# Decisions

## 2026-05-29: Product Identity

TitanForge Engine is an external procedural toolkit and generation engine for cinematic Minecraft maps.

It should not be described as a game, mod, or plugin.

Version priorities:

- Primary product target: Minecraft 1.21.11
- Secondary compatibility target: Minecraft 1.12.2

The product should prioritize our own long-term direction. A YouTuber/client target can justify compatibility work, but should not become the architectural center because that relationship may not be reliable.

Implementation bias: build from a neutral internal representation toward version-specific exporters. Prefer modern-first design with a downgrade adapter for 1.12.2 where feasible.

Popular versions inside the supported planning range should be represented as candidate adapters, not hard requirements.

Active version focus:

- 1.21.11: primary product target.
- 1.20.1: modern ecosystem fallback candidate.
- 1.12.2: legacy/client downgrade target.

Parking lot versions such as 1.19.2, 1.18.2, and 1.16.5 should not affect early architecture unless a real donor, library, or workflow requires them.

## 2026-05-29: Naming

Use `TitanForge Engine` as the display name.

Use `titanforge-engine` as the repository and package-style slug.

## 2026-05-29: Git and Assets

Use GitHub private repository with Git LFS enabled for heavy binary assets such as schematics, region files, images, videos, archives, and 3D files.

## 2026-05-29: Knowledge Base

Project memory should live in repo docs instead of relying only on chat history.

## 2026-05-29: First Mask Pass

The first image input pass uses exact-color PNG masks and reports zone statistics through `titanforge mask-info`.

Do not add fuzzy color matching or AI interpretation before the deterministic mask contract exists. Unknown colors should be reported visibly so bad plans can be cleaned up before terrain generation.

## 2026-05-29: First Preview Pass

The first preview pass renders a normalized PNG through `titanforge mask-preview`. It should be fast, deterministic, and independent of Minecraft export.

Unknown mask colors are rendered as `#ff00ff` to make bad inputs visible instead of silently guessing intent.

## 2026-05-29: First Layout Artifact

`titanforge mask-layout` writes a neutral JSON summary from a PNG mask. The artifact records source, dimensions, coverage, zones, and unknown colors.

Keep this artifact Minecraft-version-neutral. Minecraft block IDs, biome IDs, schematic formats, and exporter rules belong in later adapters.

## 2026-05-29: First Heightmap Preview

`titanforge heightmap-preview` renders a simple grayscale preview from a `mask-layout` JSON artifact.

This is diagnostic only. It deliberately avoids smoothing, erosion-style filtering, and water-depth logic until the mask and layout contracts are stable.

## 2026-05-29: Demo Mask Generator

`titanforge demo-mask` creates a deterministic toy island mask for smoke testing the input-preview-layout-heightmap pipeline.

It is not a production map generator. Keep it small and predictable so tests can catch pipeline regressions.

## 2026-05-29: First Location Pack

`titanforge build-location` creates the first tangible product folder: mask, mask preview, layout JSON, heightmap preview, report, and manifest.

This is the first "touch it" output. It deliberately stops before Minecraft world or schematic export so early validation and preview remain stable.
