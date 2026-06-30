from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from titanforge.core.project_draft import DEFAULT_MAX_DRAFT_SIDE
from titanforge.core.project import load_project_config
from titanforge.core.project_location import ProjectLocationResult, write_project_location
from titanforge.core.project_first_map_review import write_project_first_map_review_page
from titanforge.core.project_template import ProjectTemplateResult, describe_world_scale, write_project_template
from titanforge.spikes.anvil_region import DEFAULT_SPIKE_MAX_SIDE
from titanforge.spikes.anvil_test_world import AnvilTestWorldResult, write_anvil_test_world


PROJECT_FIRST_MAP_SCHEMA = "titanforge.first-map"
PROJECT_FIRST_MAP_VERSION = 1
DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME = "minecraft-test-world"


@dataclass(frozen=True)
class ProjectFirstMapResult:
    project_dir: Path
    manifest_path: Path
    review_page_path: Path
    template_result: ProjectTemplateResult
    location_result: ProjectLocationResult


@dataclass(frozen=True)
class ProjectFirstMapStatusResult:
    project_dir: Path
    manifest_path: Path
    config_path: Path
    review_page_path: Path
    location_review_path: Path
    draft_review_path: Path
    fixture_summary_path: Path
    fixture_commands_path: Path
    datapack_fixture_zip_path: Path
    preset_name: str
    world_width: int
    world_length: int
    world_scale_label: str
    open_sequence: tuple[tuple[str, str], ...]
    commands: tuple[tuple[str, str], ...]


def build_first_map_test_world_output_dir(project_dir: Path) -> Path:
    return project_dir / DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME


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
    scale = describe_world_scale(template_result.config.width, template_result.config.length)
    key_regions = tuple(region.title for region in template_result.config.regions)

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
        "guidance": {
            "worldScale": {
                "label": scale.label,
                "summary": scale.summary,
                "planningNote": scale.planning_note,
            },
            "preset": {
                "story": template_result.config.premise,
                "playerFeeling": template_result.config.player_experience,
                "keyRegions": list(key_regions),
            },
            "actionPlan": {
                "openSequence": [
                    {
                        "id": "root-review",
                        "path": review_page_path.name,
                        "summary": "Start here for the overview before opening draft or Minecraft handoff files.",
                    },
                    {
                        "id": "location-review",
                        "path": str(location_result.location_result.review_page_path.relative_to(project_dir)),
                        "summary": "Use this for the main non-technical review surface with previews and validation.",
                    },
                    {
                        "id": "draft-review",
                        "path": str(location_result.draft_result.review_page_path.relative_to(project_dir)),
                        "summary": "Use this when you need the earlier planning view and rough world shape.",
                    },
                    {
                        "id": "project-config",
                        "path": template_result.config_path.name,
                        "summary": "Edit this when world size, premise, or regions need another generation pass.",
                    },
                ],
                "nextActions": [
                    {
                        "id": "rerun-project-location",
                        "summary": "After editing the config, rerun project-location to refresh the first map outputs.",
                        "commandHint": (
                            f'py -3.11 -m titanforge project-location "{template_result.config_path.name}" '
                            f'"{location_result.output_dir.name}" --use-cleanup-for-heightmap'
                        ),
                    },
                    {
                        "id": "inspect-fixture-summary",
                        "summary": "Check fixture scope and warnings before any Minecraft-side testing.",
                        "path": str(location_result.draft_result.fixture_summary_path.relative_to(project_dir)),
                    },
                ],
            },
        },
        "commands": {
            "presetCatalog": "py -3.11 -m titanforge preset-catalog",
            "presetCatalogJson": "py -3.11 -m titanforge preset-catalog --json",
            "rerunFirstMap": (
                f'py -3.11 -m titanforge first-map "{project_dir.name}" '
                f'--name "{template_result.config.name}" --width {template_result.config.width} '
                f'--length {template_result.config.length} --preset {template_result.preset_name} '
                f'--max-draft-side {max_draft_side}'
            ),
            "rerunProjectLocation": (
                f'py -3.11 -m titanforge project-location "{template_result.config_path.name}" '
                f'"{location_result.output_dir.name}" --use-cleanup-for-heightmap'
            ),
            "buildTestWorld": (
                f'py -3.11 -m titanforge first-map-test-world "{project_dir.name}"'
            ),
            "testWorldStatus": (
                f'py -3.11 -m titanforge anvil-test-world-status "{DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME}"'
            ),
        },
        "minecraftHandoff": {
            "artifacts": {
                "fixtureSummary": str(location_result.draft_result.fixture_summary_path.relative_to(project_dir)),
                "fixtureCommands": str(location_result.draft_result.fixture_commands_path.relative_to(project_dir)),
                "datapackFixtureZip": str(location_result.draft_result.datapack_fixture_zip_path.relative_to(project_dir)),
            },
            "testWorld": {
                "requiresOptionalExtra": "py -3.11 -m pip install -e .[donor-spikes]",
                "buildCommand": f'py -3.11 -m titanforge first-map-test-world "{project_dir.name}"',
                "statusCommand": f'py -3.11 -m titanforge anvil-test-world-status "{DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME}"',
                "outputDir": DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME,
            },
            "reviewOrder": [
                {
                    "id": "fixture-summary",
                    "path": str(location_result.draft_result.fixture_summary_path.relative_to(project_dir)),
                    "summary": "Check footprint, fill-command count, and warnings before any world-side test.",
                },
                {
                    "id": "fixture-commands",
                    "path": str(location_result.draft_result.fixture_commands_path.relative_to(project_dir)),
                    "summary": "Use this when you need exact reload, place, and clear commands.",
                },
                {
                    "id": "datapack-fixture-zip",
                    "path": str(location_result.draft_result.datapack_fixture_zip_path.relative_to(project_dir)),
                    "summary": "Copy this only after the summary looks safe and the draft still matches the story.",
                },
            ],
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
            "Optional Minecraft shell: install donor-spikes, then run first-map-test-world from this project folder.",
            *[f"Warning: {warning}" for warning in result.location_result.warnings],
            f"Validation: {result.location_result.location_result.errors} errors, {result.location_result.location_result.warnings} warnings",
            f"Open first: {result.review_page_path.name}",
        )
    )


def read_project_first_map_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_project_first_map_config(project_dir: Path):
    manifest = read_project_first_map_manifest(project_dir / "first-map-manifest.json")
    project = manifest.get("project", {})
    config_path = project_dir / str(project.get("configPath", "titanforge.toml"))
    return load_project_config(config_path)


def write_project_first_map_test_world(
    project_dir: Path,
    *,
    output_dir: Path | None = None,
    max_side: int = DEFAULT_SPIKE_MAX_SIDE,
    anvil_module: Any | None = None,
) -> AnvilTestWorldResult:
    config = load_project_first_map_config(project_dir)
    resolved_output_dir = output_dir if output_dir is not None else build_first_map_test_world_output_dir(project_dir)
    return write_anvil_test_world(config, resolved_output_dir, max_side=max_side, anvil_module=anvil_module)


def summarize_project_first_map_status(project_dir: Path) -> ProjectFirstMapStatusResult:
    manifest_path = project_dir / "first-map-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing first-map manifest: {manifest_path}")

    manifest = read_project_first_map_manifest(manifest_path)
    project = manifest.get("project", {})
    world = manifest.get("world", {})
    guidance = manifest.get("guidance", {})
    action_plan = dict(guidance.get("actionPlan", {}))
    commands = dict(manifest.get("commands", {}))
    artifacts = dict(manifest.get("artifacts", {}))
    minecraft_handoff = dict(manifest.get("minecraftHandoff", {}))
    handoff_artifacts = dict(minecraft_handoff.get("artifacts", {}))

    open_sequence = tuple(
        (str(item.get("id", "unknown")), str(item.get("path", "")))
        for item in action_plan.get("openSequence", [])
    )
    command_items = tuple((str(key), str(value)) for key, value in commands.items())

    return ProjectFirstMapStatusResult(
        project_dir=project_dir,
        manifest_path=manifest_path,
        config_path=project_dir / str(project.get("configPath", "titanforge.toml")),
        review_page_path=project_dir / str(artifacts.get("rootReviewPage", "review.html")),
        location_review_path=project_dir / str(artifacts.get("locationReviewPage", Path("first-map") / "location" / "review.html")),
        draft_review_path=project_dir / str(next((path for item_id, path in open_sequence if item_id == "draft-review"), Path("first-map") / "draft" / "review.html")),
        fixture_summary_path=project_dir / str(handoff_artifacts.get("fixtureSummary", Path("first-map") / "draft" / "fixture-summary.json")),
        fixture_commands_path=project_dir / str(handoff_artifacts.get("fixtureCommands", Path("first-map") / "draft" / "fixture-commands.txt")),
        datapack_fixture_zip_path=project_dir / str(handoff_artifacts.get("datapackFixtureZip", Path("first-map") / "draft" / "datapack-fixture.zip")),
        preset_name=str(project.get("preset", "unknown")),
        world_width=int(world.get("width", 0)),
        world_length=int(world.get("length", 0)),
        world_scale_label=str(dict(guidance.get("worldScale", {})).get("label", "unknown")),
        open_sequence=open_sequence,
        commands=command_items,
    )


def format_project_first_map_status_result(result: ProjectFirstMapStatusResult) -> str:
    lines = [
        f"First-map status: {result.project_dir}",
        f"- manifest: {result.manifest_path.name}",
        f"- config: {result.config_path.name}",
        f"- preset: {result.preset_name}",
        f"- logical world size: {result.world_width} x {result.world_length}",
        f"- world scale: {result.world_scale_label}",
        f"- root review: {result.review_page_path.relative_to(result.project_dir)}",
        f"- location review: {result.location_review_path.relative_to(result.project_dir)}",
        f"- draft review: {result.draft_review_path.relative_to(result.project_dir)}",
        f"- fixture summary: {result.fixture_summary_path.relative_to(result.project_dir)}",
        f"- fixture commands: {result.fixture_commands_path.relative_to(result.project_dir)}",
        f"- datapack zip: {result.datapack_fixture_zip_path.relative_to(result.project_dir)}",
    ]
    if result.open_sequence:
        lines.append("Open order:")
        for item_id, item_path in result.open_sequence:
            lines.append(f"- {item_id}: {item_path}")
    if result.commands:
        lines.append("Command hints:")
        for command_id, command_value in result.commands:
            lines.append(f"- {command_id}: {command_value}")
    lines.append(f"Open first: {result.review_page_path.name}")
    return "\n".join(lines)
