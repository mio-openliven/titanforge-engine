# Version Targets

## Product Targets

TitanForge Engine should support Minecraft versions in planned layers instead of treating all Minecraft data as one format.

## Primary Product Target

Target: Minecraft 1.21.11

Purpose: personal and long-term product target.

Reason: TitanForge Engine should be valuable as our own tool first, independent of unreliable external demand.

## Secondary Compatibility Target

Target: Minecraft 1.12.2

Purpose: compatibility target for a YouTuber/client workflow.

Reason: useful opportunity, but not guaranteed enough to control product architecture.

## Strategic Direction

Build the engine around a neutral internal map model and the primary 1.21.11 product target. Add 1.12.2 as a compatibility adapter where feasible.

This is preferable to building the entire engine around 1.12.2 and later trying to modernize it, because older Minecraft constraints can leak into terrain, block palettes, biome handling, and export assumptions.

The 1.12.2 path should be treated as a downgrade/export problem:

1. Generate intent in the neutral model.
2. Map modern materials and structures to older equivalents.
3. Report unsupported features explicitly.
4. Keep compatibility decisions visible and testable.

## Popular Version Candidates

This is a planning matrix, not a promise that every version will be fully supported.

The engine should keep the version adapter system flexible enough to add popular versions inside the 1.12.2 to 1.21.11 range when there is a real product reason.

| Tier | Version | Role | Why it matters |
| --- | --- | --- | --- |
| P0 | 1.21.11 | Primary product target | Current modern target for our own product direction. |
| P1 | 1.20.1 | Modern modded ecosystem candidate | Frequently treated as a strong modern modded baseline. |
| P1 | 1.12.2 | Legacy/client compatibility target | Important older ecosystem and YouTuber/client compatibility target. |
| Parking lot | 1.19.2 | Deferred compatibility candidate | Keep in mind only if a real workflow or donor requires it. |
| Parking lot | 1.18.2 | Deferred worldgen-era candidate | Not active for early server/product work. |
| Parking lot | 1.16.5 | Deferred legacy-modern bridge | Not active for early server/product work. |

Recommended early adapter order:

1. `1.21.11`: primary modern exporter.
2. `1.20.1`: modern fallback if ecosystem tooling is stronger there.
3. `1.12.2`: downgrade/export path for the YouTuber/client case.
4. Add `1.19.2`, `1.18.2`, or `1.16.5` only when a donor, library, or real workflow requires it.

## Architecture Rule

Core generation logic should describe intent: regions, masks, terrain operations, structures, materials, and export requests.

Minecraft-version-specific code should live in adapters:

- block and material mapping
- NBT/world format handling
- schematic format handling
- biome and palette behavior
- exporter compatibility

The first concrete adapter artifact is now a `material-profile.json` for Minecraft `1.21.11`. It is intentionally small: it maps neutral regions, transitions, roads, and settlements into starter block palettes. It is not yet a world exporter, but it proves the version layer can stay explicit and testable.

The next concrete exporter artifact is `export-request.json` for Minecraft `1.21.11`. It turns those palettes plus neutral geometry into a first fixture-oriented export contract without pretending that NBT, chunks, or schematic serialization are already solved.

`chunk-plan.json` is the next companion artifact for Minecraft `1.21.11`. It projects export requests onto 16x16 chunk space using compact coverages, so large worlds stay inspectable without materializing millions of chunk entries too early.

`block-fixture.json` is the next fixture-oriented companion for Minecraft `1.21.11`. It turns those requests into simple cuboid block operations with starter Y levels, which is closer to real output while still stopping short of full schematic or NBT serialization.

`block-fixture.nbt` is the first binary companion for Minecraft `1.21.11`. It currently carries TitanForge fixture data through a small internal NBT codec, proving binary export plumbing before full Minecraft structure rules are locked down.

`place-fixture.mcfunction` is the first directly runnable companion for Minecraft `1.21.11`. It expresses fixture cuboids as striped `fill` commands, which is primitive but genuinely usable inside the game before full structure serialization exists.

## Open Questions

- Which output formats are required for primary 1.21.11?
- Which output formats are required for secondary 1.12.2?
- Should 1.21.11 support direct world export, schematic export, or both?
- How much block/material parity is required between 1.21.11 and 1.12.2?
- Which modern features can be downgraded, approximated, or forbidden for 1.12.2?
- Is 1.20.1 worth supporting before 1.12.2 if tooling is better?
- Which version gives the best first preview/export donor set?
