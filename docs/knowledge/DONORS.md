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

## Vetted Shortlist

Checked on 2026-06-30. These are the first concrete donor candidates worth tracking.

| Project | Link | License | Why It Is Useful | TitanForge Decision |
| --- | --- | --- | --- | --- |
| `nbtlib` | <https://github.com/vberlier/nbtlib> | MIT | Clean Python NBT read/write layer for fixture tests, SNBT work, and binary payload inspection. | Safe candidate for optional dependency or reference implementation. Best first donor for NBT fixtures. |
| `anvil-parser2` | <https://github.com/0xTiger/anvil-parser2> | MIT | Python reader/parser for Anvil region data with 1.18+ support, which is much closer to the 1.21.11 target than the archived original fork. | Good candidate for an isolated exporter-adapter spike that validates chunk/region assumptions without touching core generation. |
| `mcschematic` | <https://github.com/Sloimayyy/mcschematic> | Apache-2.0 | Python-side schematic creation and transform helpers. Useful if TitanForge adds a first schematic handoff before full world writing. | Safe for experiments in a separate schematic adapter. Do not leak schematic-specific classes into core planning types. |
| `PrismarineJS/minecraft-data` | <https://github.com/PrismarineJS/minecraft-data> | Repo page says MIT, but provenance needs care | Huge versioned block/item/data snapshot set. Search results also show active 1.21.11 support discussion and releases in 2026. | Good as a version-data reference or pinned generated snapshot, but verify provenance before vendoring data directly into the repo. |
| `Querz/mcaselector` | <https://github.com/Querz/mcaselector> | MIT | Mature external world/chunk inspection tool. Useful to verify whether TitanForge-generated regions load cleanly, to inspect chunk boundaries, and to prune bad test outputs without opening Minecraft. | Strong external verifier and cleanup companion. Use it around TitanForge outputs, not as embedded Java code. |
| `Schem-at/Nucleation` | <https://github.com/schem-at/nucleation> | MIT | New high-performance schematic engine with Python bindings and multi-runtime focus. Interesting if TitanForge needs faster large schematic serialization than a pure Python path. | Worth a guarded spike in an isolated adapter only after the first simple schematic path exists. Too early to trust as a core dependency without local validation. |
| `Sponge Schematic Specification` | <https://github.com/SpongePowered/Schematic-Specification> | No clear root license file found during this pass | Canonical format reference for modern schematic storage, palette rules, entities, block entities, and `DataVersion`. | Use as a format/reference document only for now. Do not copy text or code into TitanForge without a clearer license trail. |
| `EngineHub/WorldEdit` | <https://github.com/EngineHub/WorldEdit> | GPL-3.0 | Defines strong builder expectations around clipboard/schematic workflows and practical UX around structure placement. | Learn from workflow and format expectations, but do not transplant code or couple TitanForge architecture to WorldEdit internals. |
| `MestreLion/mcworldlib` | <https://github.com/MestreLion/mcworldlib> | GPL-3.0 | Python library that explicitly reads and writes `.mca`, `.mcr`, and `.mcc` world data. It is one of the clearest references for what a real world-save layer must eventually handle. | Excellent reference and throwaway lab tool for region-writing experiments. Do not vendor or mix with TitanForge core while the repo stays permissive and modular. |
| `Captain-Chaos/WorldPainter` | <https://github.com/Captain-Chaos/WorldPainter> | GPL-3.0 | Battle-tested external terrain authoring workflow with huge-world ergonomics, import/export expectations, and builder-facing terminology. | Study workflow and optionally target it as an external handoff path. Do not embed code into TitanForge. |
| `Captain-Chaos/DemoWPPlugin` | <https://github.com/Captain-Chaos/DemoWPPlugin> | CC0-1.0 | Tiny skeleton showing how WorldPainter plugins are structured, including custom formats and map import/export extension points. | Safe reference if TitanForge ever tries a WorldPainter bridge or plugin-based handoff. Keep it in an adapter spike, not in core. |
| `Amulet-Core` | <https://github.com/Amulet-Team/Amulet-Core> | Paid/restricted license (`All rights reserved`, license purchase required) | Powerful world-format tooling and real exporter knowledge. | Useful as an external comparison target only. Do not vendor or depend on it inside TitanForge. |
| `PyMCTranslate` | <https://github.com/Amulet-Team/PyMCTranslate> | Paid/restricted license (`All rights reserved`, license purchase required) | Rich cross-version translation ideas for blocks, block entities, entities, and items. | Architecture inspiration only. Do not bundle into the repo. |
| `Amulet-NBT` | <https://github.com/Amulet-Team/Amulet-NBT> | Restrictive custom license with noncommercial/noncompete terms | Fast low-level NBT handling and serialization experience. | Local experiment only if needed; not suitable as a bundled core dependency for TitanForge. |

## Recommended Use Order

If the goal is to reach the first real 1.21.11 map creator faster without poisoning the architecture, use donors in this order:

1. Start with `nbtlib` for safe fixture/NBT tests and binary validation.
2. Add an isolated `anvil-parser2` spike to inspect chunk and region assumptions against `.mca` data.
3. Use `mcaselector` as an external verifier once TitanForge writes its first test world folders or region files.
4. Add a separate schematic-adapter spike with `mcschematic` only if schematic handoff becomes the fastest usable export path.
5. Consider `Nucleation` only if Python-side schematic writing becomes the bottleneck after a simpler path exists.
6. Use `minecraft-data` as a reference input for version-aware block/tag data after pinning exactly which generated snapshot TitanForge trusts.
7. Keep `WorldEdit`, `WorldPainter`, `Sponge`, `mcworldlib`, and the `Amulet` stack as reference material, external tooling, or lab-only adapters, not embedded engine code.

## Hard Boundaries

- Permissive licenses such as MIT and Apache-2.0 are the safest path for optional adapters, research spikes, and tests.
- GPL or restrictive/source-available donors are still useful for behavior study, file-format expectations, and manual experiments, but they should stay outside TitanForge core and outside copied source.
- Not selling the software does not cancel source-code license obligations once copied code or bundled dependencies are pushed to GitHub or redistributed.
- If TitanForge ever imports donor code, do it only in a narrow adapter module with explicit attribution, provenance notes, and a reason why a clean-room implementation would be slower or riskier.

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
