from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from titanforge.core.project_draft import DEFAULT_MAX_DRAFT_SIDE
from titanforge.core.project_location import ProjectLocationResult, write_project_location
from titanforge.core.project_first_map_review import write_project_first_map_review_page
from titanforge.core.project_template import ProjectTemplateResult, describe_world_scale, write_project_template


PROJECT_FIRST_MAP_SCHEMA = "titanforge.first-map"
PROJECT_FIRST_MAP_VERSION = 1


@dataclass(frozen=True)
class ProjectFirstMapResult:
    project_dir: Path
    manifest_path: Path
    review_page_path: Path
    template_result: ProjectTemplateResult
    location_result: ProjectLocationResult


def write_project_first_map(
    project_dir: Path,
    project_name: str | None,
    width: int,
    length: int,
    preset_name: str,
    *,
    target_version: str = "1.21.11",
    max_draft_side: int = DEFAULT_MAX_DRAFT_SIDE,
    use_cleanup_for_heightmap: bool = True,
) -> ProjectFirstMapResult:
    manifest_path = project_dir / "first-map-manifest.json"
    review_page_path = project_dir / "review.html"
    suggested_output_dir = project_dir / "first-map"
    if manifest_path.exists():
        raise FileExistsError(f"First-map manifest already exists: {manifest_path}")
    if review_page_path.exists():
        raise FileExistsError(f"First-map review page already exists: {review_page_path}")
    if suggested_output_dir.exists():
        raise FileExistsError(f"First map output already exists: {suggested_output_dir}")

    template_result = write_project_template(
        project_dir,
        project_name,
        width,
        length,
        preset_name,
        target_version=target_version,
    )

    location_result = write_project_location(
        template_result.config,
        template_result.suggested_output_dir,
        max_draft_side=max_draft_side,
        use_cleanup_for_heightmap=use_cleanup_for_heightmap,
    )

    provisional_result = ProjectFirstMapResult(
        project_dir=project_dir,
        manifest_path=manifest_path,
        review_page_path=review_page_path,
        template_result=template_result,
        location_result=location_result,
    )
    write_project_first_map_review_page(provisional_result, review_page_path)

    manifest = {
        "schema": PROJECT_FIRST_MAP_SCHEMA,
        "version": PROJECT_FIRST_MAP_VERSION,
        "project": {
            "name": template_result.config.name,
            "targetVersion": template_result.config.target_version,
            "preset": template_result.preset_name,
            "configPath": template_result.config_path.name,
        },
        "world": {
            "width": template_result.config.width,
            "length": template_result.config.length,
        },
        "artifacts": {
            "rootReviewPage": review_page_path.name,
            "projectLocationDir": location_result.output_dir.name,
            "locationReviewPage": str(location_result.location_result.review_page_path.relative_to(project_dir)),
            "bridgeManifest": str(location_result.manifest_path.relative_to(project_dir)),
            "draftMask": str(location_result.draft_result.draft_mask_path.relative_to(project_dir)),
            "fixtureCommands": str(location_result.draft_result.fixture_commands_path.relative_to(project_dir)),
            "fixtureSummary": str(location_result.draft_result.fixture_summary_path.relative_to(project_dir)),
            "datapackFixtureZip": str(location_result.draft_result.datapack_fixture_zip_path.relative_to(project_dir)),
        },
        "raster": {
            "width": location_result.draft_result.raster_width,
            "length": location_result.draft_result.raster_length,
            "blocksPerPixel": location_result.draft_result.blocks_per_pixel,
        },
        "terrain": {
            "cleanupApplied": use_cleanup_for_heightmap,
            "heightmapSource": location_result.location_result.heightmap_source_path.name,
        },
        "warnings": list(location_result.warnings),
        "validation": {
            "errors": location_result.location_result.errors,
            "warnings": location_result.location_result.warnings,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return ProjectFirstMapResult(
        project_dir=project_dir,
        manifest_path=manifest_path,
        review_page_path=review_page_path,
        template_result=template_result,
        location_result=location_result,
    )


def format_project_first_map_result(result: ProjectFirstMapResult) -> str:
    scale = describe_world_scale(result.template_result.config.width, result.template_result.config.length)
    region_lineup = ", ".join(region.title for region in result.template_result.config.regions[:3])
    if len(result.template_result.config.regions) > 3:
        region_lineup = f"{region_lineup}, +{len(result.template_result.config.regions) - 3} more"
    return "\n".join(
        (
            f"First map: {result.project_dir}",
            f"- config: {result.template_result.config_path.name}",
            f"- preset: {result.template_result.preset_name}",
            f"- project-location dir: {result.location_result.output_dir.name}",
            f"- root manifest: {result.manifest_path.name}",
            f"- root review: {result.review_page_path.name}",
            f"Logical world size: {result.template_result.config.width} x {result.template_result.config.length}",
            f"World scale: {scale.label}",
            f"Scale use: {scale.summary}",
            f"Preset story: {result.template_result.config.premise}",
            f"Player feeling: {result.template_result.config.player_experience}",
            f"Key regions: {region_lineup}",
            f"Draft raster: {result.location_result.draft_result.raster_width} x {result.location_result.draft_result.raster_length}",
            f"Scale bridge: 1 px = {result.location_result.draft_result.blocks_per_pixel} blocks",
            "Change world size later: edit width and length in titanforge.toml, then rerun generation.",
            scale.planning_note,
            *[f"Warning: {warning}" for warning in result.location_result.warnings],
            f"Validation: {result.location_result.location_result.errors} errors, {result.location_result.location_result.warnings} warnings",
            f"Open first: {result.review_page_path.name}",
        )
    )
