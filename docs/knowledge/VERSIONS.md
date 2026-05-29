# Version Targets

## Product Targets

TitanForge Engine should support Minecraft versions in planned layers instead of treating all Minecraft data as one format.

## V1

Target: Minecraft 1.12.2

Purpose: first production target and compatibility baseline.

Reason: the original concept was built around Minecraft 1.12.2 cinematic map generation.

## V2

Target: Minecraft 1.21.11

Purpose: second version of the product.

Reason: the engine should be designed so modern Minecraft support can be added without rewriting the core pipeline.

## Architecture Rule

Core generation logic should describe intent: regions, masks, terrain operations, structures, materials, and export requests.

Minecraft-version-specific code should live in adapters:

- block and material mapping
- NBT/world format handling
- schematic format handling
- biome and palette behavior
- exporter compatibility

## Open Questions

- Which output formats are required for V1?
- Which output formats are required for V2?
- Should V2 support direct world export, schematic export, or both?
- How much block/material parity is required between V1 and V2?
