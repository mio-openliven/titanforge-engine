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

## Architecture Rule

Core generation logic should describe intent: regions, masks, terrain operations, structures, materials, and export requests.

Minecraft-version-specific code should live in adapters:

- block and material mapping
- NBT/world format handling
- schematic format handling
- biome and palette behavior
- exporter compatibility

## Open Questions

- Which output formats are required for primary 1.21.11?
- Which output formats are required for secondary 1.12.2?
- Should 1.21.11 support direct world export, schematic export, or both?
- How much block/material parity is required between 1.21.11 and 1.12.2?
- Which modern features can be downgraded, approximated, or forbidden for 1.12.2?
