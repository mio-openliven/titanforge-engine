# Donor Research

Donors are reference projects, libraries, formats, tools, or creative workflows that can teach TitanForge. They are not code to blindly copy.

The honest reason this project exists is that Minecraft creation already has many strong ideas scattered across different tools and communities. TitanForge is an attempt to learn from those ideas and combine the useful patterns into a small, testable pipeline for cinematic map generation.

## Donor Rules

- Check the license before using code, assets, schemas, or generated examples.
- Prefer learning from public documentation and behavior over copying implementation.
- Attribute projects that materially influence the design.
- Keep donor-specific adapters separate from TitanForge core logic.
- Do not import a large source tree just because one function looks useful.

## Current Donor Categories

| Category | Why It Matters | What TitanForge Can Learn |
| --- | --- | --- |
| WorldEdit and schematic ecosystems | Builders already rely on schematic workflows. | Structure placement concepts, clipboard formats, and builder-friendly export expectations. |
| Sponge schematic format references | Modern schematic workflows need stable data formats. | Palette handling, NBT structure, version compatibility, and metadata conventions. |
| Minecraft NBT / Anvil tooling | Any real exporter must understand Minecraft data safely. | Region/chunk boundaries, block data, version-specific risks, and test fixtures. |
| Heightmap and mask workflows | Artists can communicate terrain intent visually. | Color-coded regions, biome/zone masks, cleanup passes, and preview-first iteration. |
| Procedural terrain examples | Generation needs repeatable rules, not only manual building. | Pipeline stages, deterministic inputs, seed handling, and terrain pass composition. |
| Preview renderers | Creators need fast feedback before opening Minecraft. | Lightweight previews, diagnostics, and image outputs for review. |
| Asset pipeline examples | Large maps need reusable structures and conventions. | Naming, manifests, Git LFS discipline, and asset indexing. |
| Existing map-generation tools | The field already has many solved pieces. | User expectations, feature boundaries, and mistakes to avoid. |
| Git LFS / large-repo workflows | Map assets can destroy Git history if handled badly. | Separation of code, fixtures, generated output, and heavy binary assets. |

## Useful Questions For Every Donor

```text
Name:
Link or local path:
Domain:
License:
Useful ideas:
Do not copy:
Risks:
Decision:
```

## Open Attribution List

This list should grow as real sources are selected. For now, TitanForge names donor categories instead of claiming code from specific projects.

- WorldEdit ecosystem - schematic/building workflow inspiration.
- Sponge schematic ecosystem - modern schematic format inspiration.
- Minecraft NBT/Anvil ecosystem - data-format research direction.
- Image-mask and heightmap workflows - visual planning direction.
- Procedural terrain/toolchain projects - pipeline architecture inspiration.

## Why Combining These Ideas Is Useful

Server owners, builders, and creators usually do not need a perfect academic terrain engine. They need a workflow that can move from idea to preview to usable world faster.

If masks, previews, terrain passes, schematics, and version-aware export are connected cleanly, TitanForge could help with:

- server spawns;
- event maps;
- cinematic roleplay locations;
- YouTube scenes;
- seasonal worlds;
- quick layout experiments before manual detailing.

The project should stay humble: learn from the donor ecosystem, give credit, and publish only the parts that are safe and genuinely useful.
