# Roadmap

## Phase 0: Project Preparation

- Set up GitHub repository.
- Configure Git LFS.
- Create project knowledge base.
- Select 10 to 15 donors.
- Identify real source folder and import only useful files.

## Phase 1: Skeleton

- Create initial module structure.
- Define project config format.
- Add tiny example project.
- Add first pipeline command.
- Add basic preview output.

## Phase 2: Minecraft Data

- Decide primary Minecraft 1.21.11 schematic/world export support.
- Define secondary Minecraft 1.12.2 compatibility assumptions.
- Add NBT tests and fixtures.
- Export one minimal structure or region successfully.

## Phase 2.5: Version Layer

- Add explicit version target model.
- Keep block palettes and format details out of core generation logic.
- Add fixtures for 1.21.11 and 1.12.2 once formats are selected.
- Test downgrade/export compatibility from the neutral internal model to 1.12.2.
- Keep active candidate slots for 1.21.11, 1.20.1, and 1.12.2.
- Keep 1.19.2, 1.18.2, and 1.16.5 in the parking lot only.

## Phase 3: Generation

- Mask loading and region extraction.
- Layout rules.
- Terrain passes.
- Schematic placement.
- Preview diagnostics.

## Phase 4: Production Workflow

- Asset library conventions.
- Caching.
- Error reports.
- Batch generation.
- Larger cinematic map examples.
