from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from titanforge.core.project import ProjectConfig
from titanforge.core.project_draft import DEFAULT_MAX_DRAFT_SIDE, ProjectDraftResult, write_project_draft
from titanforge.locations.builder import LocationBuildResult, build_location_pack


PROJECT_LOCATION_SCHEMA = "titanforge.project-location"
PROJECT_LOCATION_VERSION = 1


@dataclass(frozen=True)
class ProjectLocationResult:
    output_dir: Path
    draft_dir: Path
    location_dir: Path
    manifest_path: Path
    draft_result: ProjectDraftResult
    location_result: LocationBuildResult
    warnings: tuple[str, ...]


def write_project_location(
    config: ProjectConfig,
    output_dir: Path,
    *,
    max_draft_side: int = DEFAULT_MAX_DRAFT_SIDE,
    use_cleanup_for_heightmap: bool = False,
) -> ProjectLocationResult:
    output_dir.mkdir(parents=True, exist_ok=True)

    draft_dir = output_dir / "draft"
    location_dir = output_dir / "location"
    manifest_path = output_dir / "project-location-manifest.json"

    draft_result = write_project_draft(config, draft_dir, max_draft_side=max_draft_side)
    draft_review_links = (
        ("draft/review.html", "../draft/review.html"),
        ("draft/draft-mask.png", "../draft/draft-mask.png"),
        ("draft/fixture-summary.json", "../draft/fixture-summary.json"),
        ("draft/fixture-commands.txt", "../draft/fixture-commands.txt"),
        ("draft/datapack-fixture.zip", "../draft/datapack-fixture.zip"),
    )
    location_result = build_location_pack(
        location_dir,
        input_mask=draft_result.draft_mask_path,
        use_cleanup_for_heightmap=use_cleanup_for_heightmap,
        source_mode_override="project-draft",
        draft_artifacts=draft_review_links,
    )

    manifest = {
        "schema": PROJECT_LOCATION_SCHEMA,
        "version": PROJECT_LOCATION_VERSION,
        "project": {
            "name": config.name,
            "targetVersion": config.target_version,
        },
        "world": {
            "width": config.width,
            "length": config.length,
        },
        "raster": {
            "width": draft_result.raster_width,
            "length": draft_result.raster_length,
            "blocksPerPixel": draft_result.blocks_per_pixel,
        },
        "artifacts": {
            "draftDir": draft_dir.name,
            "locationDir": location_dir.name,
            "draftMask": str(draft_result.draft_mask_path.relative_to(output_dir)),
            "materialProfile": str(draft_result.material_profile_path.relative_to(output_dir)),
            "exportRequest": str(draft_result.export_request_path.relative_to(output_dir)),
            "chunkPlan": str(draft_result.chunk_plan_path.relative_to(output_dir)),
            "blockFixture": str(draft_result.block_fixture_path.relative_to(output_dir)),
            "nbtFixture": str(draft_result.nbt_fixture_path.relative_to(output_dir)),
            "mcfunctionFixture": str(draft_result.mcfunction_fixture_path.relative_to(output_dir)),
            "clearMcfunctionFixture": str(draft_result.clear_mcfunction_fixture_path.relative_to(output_dir)),
            "fixtureCommands": str(draft_result.fixture_commands_path.relative_to(output_dir)),
            "fixtureSummary": str(draft_result.fixture_summary_path.relative_to(output_dir)),
            "datapackFixture": str(draft_result.datapack_fixture_dir.relative_to(output_dir)),
            "datapackFixtureZip": str(draft_result.datapack_fixture_zip_path.relative_to(output_dir)),
            "transitionPlan": str(draft_result.transition_plan_path.relative_to(output_dir)),
            "transitionPreview": str(draft_result.transition_preview_path.relative_to(output_dir)),
            "routePlan": str(draft_result.route_plan_path.relative_to(output_dir)),
            "routePreview": str(draft_result.route_preview_path.relative_to(output_dir)),
            "placementPlan": str(draft_result.placement_plan_path.relative_to(output_dir)),
            "placementPreview": str(draft_result.placement_preview_path.relative_to(output_dir)),
            "roadPlan": str(draft_result.road_plan_path.relative_to(output_dir)),
            "roadPreview": str(draft_result.road_preview_path.relative_to(output_dir)),
            "settlementPlan": str(draft_result.settlement_plan_path.relative_to(output_dir)),
            "settlementPreview": str(draft_result.settlement_preview_path.relative_to(output_dir)),
            "locationReviewPage": str(location_result.review_page_path.relative_to(output_dir)),
            "locationManifest": str(location_result.manifest_path.relative_to(output_dir)),
        },
        "terrain": {
            "cleanupApplied": use_cleanup_for_heightmap,
            "heightmapSource": location_result.heightmap_source_path.name,
        },
        "warnings": list(draft_result.warnings),
        "validation": {
            "errors": location_result.errors,
            "warnings": location_result.warnings,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return ProjectLocationResult(
        output_dir=output_dir,
        draft_dir=draft_dir,
        location_dir=location_dir,
        manifest_path=manifest_path,
        draft_result=draft_result,
        location_result=location_result,
        warnings=draft_result.warnings,
    )


def format_project_location_result(result: ProjectLocationResult) -> str:
    return "\n".join(
        [
            f"Project location: {result.output_dir}",
            f"- draft dir: {result.draft_dir.name}",
            f"- location dir: {result.location_dir.name}",
            f"- bridge manifest: {result.manifest_path.name}",
            f"World size: {result.draft_result.world_width} x {result.draft_result.world_length}",
            f"Draft raster: {result.draft_result.raster_width} x {result.draft_result.raster_length}",
            f"Blocks per pixel: {result.draft_result.blocks_per_pixel}",
            *[f"Warning: {warning}" for warning in result.warnings],
            f"Validation: {result.location_result.errors} errors, {result.location_result.warnings} warnings",
        ]
    )
