# TitanForge Engine

TitanForge Engine is an early procedural toolkit for planning and generating cinematic Minecraft map workflows.

It is not a game, not a Minecraft mod, and not a server plugin. It is an external development tool for map makers and server owners who want to turn visual ideas into repeatable steps: masks, layouts, previews, terrain passes, location packs, and future exporters.

## Why This Exists

Minecraft server owners, builders, event teams, and YouTube creators often need the same thing in different words:

- a spawn that feels intentional;
- a themed world for a season, event, or story;
- a cinematic location that can be reviewed before hours are spent building;
- a workflow that is less "start from nothing" and more "draw the idea, preview it, then iterate".

TitanForge is an experiment around that idea. The goal is to combine map-planning concepts, mask/heightmap workflows, schematic thinking, preview generation, and version-aware export logic into one understandable pipeline.

## Project Status

- **Useful now:** yes, as a tested CLI prototype for masks, previews, layout reports, and tiny location-pack experiments.
- **Finished product:** no. This is an idea-stage MVP, not a production world generator yet.
- **Main risks:** Minecraft format complexity, version compatibility, schematic/export correctness, and large asset handling.
- **If needed:** I can continue it into a practical map-building pipeline with real exporters, richer terrain passes, and a friendlier UI.

## Current Working Pieces

- project config loading;
- inventory scanning;
- PNG mask reading/writing;
- demo mask generation;
- mask analysis;
- mask cleanup previews;
- mask-to-layout output;
- simple heightmap previews;
- layout validation reports;
- tiny location-pack output;
- unit tests around the current pipeline pieces.

## Who It Could Help

- **Minecraft server owners** who need repeatable spawns, hubs, event maps, or seasonal worlds.
- **Creative builders** who want a planning pipeline before doing manual detail work.
- **YouTubers and roleplay teams** who need cinematic locations quickly, with previews before production.
- **Toolmakers** who want small readable examples of mask/layout/preview workflows.

## Inspiration and Donor Research

TitanForge is openly inspired by existing map-making and Minecraft tooling ecosystems. The project keeps donor research in:

- [docs/knowledge/DONORS.md](docs/knowledge/DONORS.md)
- [docs/knowledge/SOURCE_IMPORT_PLAN.md](docs/knowledge/SOURCE_IMPORT_PLAN.md)
- [docs/knowledge/DECISIONS.md](docs/knowledge/DECISIONS.md)

Donors are not code to blindly copy. They are references that teach formats, workflows, risks, and design choices. If this project ever uses code, assets, schemas, or behavior from another project, the license and attribution must be checked first.

## Version Direction

- Primary target: modern Minecraft, currently tracked as `1.21.11` in the planning docs.
- Secondary compatibility target: `1.12.2`, because older creative/server ecosystems still matter.

The goal is to keep version-specific behavior behind adapters instead of mixing every Minecraft version into core generation logic.

## Quick Start

Use Python 3.11 or newer.

```powershell
$env:PYTHONPATH = "src"
python -m titanforge info
python -m titanforge plan examples/tiny_project/titanforge.toml
python -m titanforge inventory examples
python -m titanforge demo-mask out\demo-mask.png
python -m titanforge mask-info out\demo-mask.png
python -m titanforge mask-preview out\demo-mask.png out\mask-preview.png
python -m titanforge mask-cleanup-preview out\demo-mask.png out\mask-cleanup-preview.png
python -m titanforge mask-layout out\demo-mask.png out\layout.json
python -m titanforge heightmap-preview out\layout.json out\heightmap-preview.png
python -m titanforge validate-layout out\layout.json --report out\report.txt
python -m titanforge build-location out\demo-location --width 128 --height 128 --use-cleanup-for-heightmap
```

## Tests

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

## Project Knowledge

Start here:

- [PRD](docs/knowledge/PRD.md)
- [Project map](docs/knowledge/PROJECT_MAP.md)
- [Architecture](docs/knowledge/ARCHITECTURE.md)
- [Roadmap](docs/knowledge/ROADMAP.md)
- [Risks](docs/knowledge/RISKS.md)
- [Terms](docs/knowledge/TERMS.md)
- [Agent protocol](AGENTS.md)
- [Chat roles](docs/operations/CHAT_ROLES.md)
- [Simple next steps](docs/operations/SIMPLE_NEXT_STEPS.md)

## Author Note

This project is made in the spirit of learning, practice, and building useful tools for Minecraft communities. It is an honest MVP-plus experiment, not a polished commercial product.

The idea is simple: learn by shipping, keep the reusable parts public, document the rough edges, and slowly turn scattered creative workflows into something other people can understand and improve.

## License

MIT License. See [LICENSE](LICENSE).
