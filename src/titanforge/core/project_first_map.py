from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from titanforge.core.project_draft import DEFAULT_MAX_DRAFT_SIDE
from titanforge.core.project import load_project_config
from titanforge.core.project_location import ProjectLocationResult, write_project_location
from titanforge.core.project_first_map_review import write_project_first_map_review_page
from titanforge.core.project_template import (
    PROJECT_TEMPLATE_MAX_SIDE,
    PROJECT_TEMPLATE_MIN_SIDE,
    ProjectTemplateResult,
    describe_world_scale,
    rewrite_project_template_preset,
    rewrite_project_template_story,
    rewrite_project_template_regions,
    rewrite_project_template_world_size,
    write_project_template,
)
from titanforge.core.route_plan import build_route_plan
from titanforge.core.world_plan import build_world_plan
from titanforge.spikes.anvil_region import DEFAULT_SPIKE_MAX_SIDE, MAX_SPIKE_SIDE, count_sampled_region_files
from titanforge.spikes.anvil_test_world import (
    AnvilTestWorldGrowthResult,
    AnvilTestWorldResult,
    AnvilTestWorldStatusResult,
    format_test_world_status_result,
    grow_test_world,
    summarize_test_world_status,
    update_test_world_verification_report,
    write_anvil_test_world,
)


PROJECT_FIRST_MAP_SCHEMA = "titanforge.first-map"
PROJECT_FIRST_MAP_VERSION = 1
DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME = "minecraft-test-world"
DEFAULT_FIRST_MAP_START_FILE_NAME = "first-map-start.txt"
DEFAULT_FIRST_MAP_MINECRAFT_FIRST_PASS_FILE_NAME = "minecraft-first-pass.txt"
MIN_FIRST_MAP_TEST_WORLD_SIDE = 64


@dataclass(frozen=True)
class ProjectFirstMapResult:
    project_dir: Path
    manifest_path: Path
    review_page_path: Path
    max_draft_side: int
    template_result: ProjectTemplateResult
    location_result: ProjectLocationResult


@dataclass(frozen=True)
class ProjectFirstMapResizeResult:
    project_dir: Path
    config_path: Path
    old_width: int
    old_length: int
    new_width: int
    new_length: int
    refreshed_result: ProjectFirstMapResult


@dataclass(frozen=True)
class ProjectFirstMapRethemeResult:
    project_dir: Path
    config_path: Path
    old_preset_name: str
    new_preset_name: str
    refreshed_result: ProjectFirstMapResult


@dataclass(frozen=True)
class ProjectFirstMapStoryResult:
    project_dir: Path
    config_path: Path
    old_premise: str
    old_player_feeling: str
    new_premise: str
    new_player_feeling: str
    refreshed_result: ProjectFirstMapResult


@dataclass(frozen=True)
class ProjectFirstMapRegionsResult:
    project_dir: Path
    config_path: Path
    old_region_count: int
    new_region_count: int
    refreshed_result: ProjectFirstMapResult


@dataclass(frozen=True)
class ProjectFirstMapRouteHandoff:
    route_id: str
    kind: str
    summary: str
    start_command: str
    start_output_dir: str
    start_status_command: str
    end_command: str
    end_output_dir: str
    end_status_command: str


@dataclass(frozen=True)
class ProjectFirstMapWalkthroughStep:
    step_id: str
    title: str
    summary: str
    command: str
    output_dir: str
    status_command: str


@dataclass(frozen=True)
class ProjectFirstMapSizeOption:
    option_id: str
    label: str
    width: int
    length: int
    scale_label: str
    summary: str
    rerun_command: str


@dataclass(frozen=True)
class ProjectFirstMapRecommendedManualStart:
    summary: str
    install_extra_command: str
    build_command: str
    output_dir: str
    checklist_path: str
    status_command: str


@dataclass(frozen=True)
class ProjectFirstMapDatapackStart:
    summary: str
    datapack_zip_path: str
    reload_command: str
    place_command: str
    clear_command: str
    starter_verdict: str


@dataclass(frozen=True)
class ProjectFirstMapStatusResult:
    project_dir: Path
    manifest_path: Path
    first_map_start_path: Path
    minecraft_first_pass_path: Path
    config_path: Path
    review_page_path: Path
    location_review_path: Path
    draft_review_path: Path
    route_plan_path: Path
    route_preview_path: Path
    fixture_summary_path: Path
    fixture_commands_path: Path
    datapack_fixture_zip_path: Path
    starter_test_verdict: str
    starter_test_summary: str
    starter_test_world_advice: str
    test_world_recommended_max_side: int
    test_world_strategy_summary: str
    test_world_strategy_reason: str
    test_world_recommended_region_file_count: int
    test_world_region_file_summary: str
    test_world_first_multi_region_max_side: int | None
    test_world_first_multi_region_file_count: int | None
    test_world_multi_region_summary: str
    datapack_start: ProjectFirstMapDatapackStart
    recommended_manual_start: ProjectFirstMapRecommendedManualStart
    test_world_focus_commands: tuple[tuple[str, str, str, str], ...]
    test_world_focus_anchor_commands: tuple[tuple[str, str, str, str], ...]
    route_handoffs: tuple[ProjectFirstMapRouteHandoff, ...]
    recommended_walkthrough: tuple[ProjectFirstMapWalkthroughStep, ...]
    size_edit_config_path: Path
    size_edit_options: tuple[ProjectFirstMapSizeOption, ...]
    preset_name: str
    world_width: int
    world_length: int
    world_scale_label: str
    world_scale_summary: str
    world_scale_planning_note: str
    preset_story: str
    player_feeling: str
    key_regions: tuple[str, ...]
    open_sequence: tuple[tuple[str, str], ...]
    open_sequence_summaries: tuple[tuple[str, str], ...]
    next_actions: tuple[tuple[str, str, str], ...]
    minecraft_review_order: tuple[tuple[str, str, str], ...]
    test_world_requires_optional_extra: str
    test_world_build_command: str
    test_world_status_command: str
    test_world_output_dir: str
    commands: tuple[tuple[str, str], ...]


def build_first_map_test_world_output_dir(
    project_dir: Path,
    *,
    focus_region_title: str | None = None,
    focus_anchor_id: str | None = None,
) -> Path:
    if focus_region_title is None:
        return project_dir / DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME
    suffix_parts = [_slugify_focus_part(focus_region_title)]
    if focus_anchor_id is not None:
        suffix_parts.append(_slugify_focus_part(focus_anchor_id))
    suffix = "-".join(part for part in suffix_parts if part) or "focused"
    return project_dir / f"{DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME}-{suffix}"


def _build_first_map_shell_command(
    project_dir: Path,
    output_dir_name: str,
    recommended_max_side: int,
    *,
    focus_region_title: str,
    focus_anchor_id: str | None = None,
) -> str:
    command = (
        f'py -3.11 -m titanforge first-map-test-world "{project_dir.name}" '
        f'--output-dir "{output_dir_name}" --max-side {recommended_max_side} '
        f'--focus-region "{focus_region_title}"'
    )
    if focus_anchor_id is not None:
        command += f' --focus-anchor "{focus_anchor_id}"'
    return command


def _build_first_map_shell_status_command(project_dir: Path, output_dir_name: str) -> str:
    return (
        f'py -3.11 -m titanforge first-map-test-world-status "{project_dir.name}" '
        f'--sample-dir "{output_dir_name}"'
    )


def build_first_map_focus_region_commands(
    project_dir: Path,
    region_titles: tuple[str, ...],
    recommended_max_side: int,
) -> tuple[tuple[str, str, str, str], ...]:
    return tuple(
        (
            region_title,
            _build_first_map_shell_command(
                project_dir,
                build_first_map_test_world_output_dir(project_dir, focus_region_title=region_title).name,
                recommended_max_side,
                focus_region_title=region_title,
            ),
            build_first_map_test_world_output_dir(project_dir, focus_region_title=region_title).name,
            _build_first_map_shell_status_command(
                project_dir,
                build_first_map_test_world_output_dir(project_dir, focus_region_title=region_title).name
            ),
        )
        for region_title in region_titles
    )


def build_first_map_focus_anchor_commands(
    project_dir: Path,
    config,
    recommended_max_side: int,
) -> tuple[tuple[str, str, str, str], ...]:
    world_plan = build_world_plan(config)
    commands: list[tuple[str, str, str, str]] = []
    for region in world_plan.regions:
        for anchor in region.anchors:
            output_dir = build_first_map_test_world_output_dir(
                project_dir,
                focus_region_title=region.title,
                focus_anchor_id=anchor.id,
            ).name
            commands.append(
                (
                    f"{region.title} / {anchor.id}",
                    _build_first_map_shell_command(
                        project_dir,
                        output_dir,
                        recommended_max_side,
                        focus_region_title=region.title,
                        focus_anchor_id=anchor.id,
                    ),
                    output_dir,
                    _build_first_map_shell_status_command(project_dir, output_dir),
                )
            )
    return tuple(commands)


def build_first_map_route_handoffs(
    project_dir: Path,
    config,
    recommended_max_side: int,
) -> tuple[ProjectFirstMapRouteHandoff, ...]:
    world_plan = build_world_plan(config)
    route_plan = build_route_plan(world_plan)
    handoffs: list[ProjectFirstMapRouteHandoff] = []
    for route in route_plan.routes:
        start_output_dir = build_first_map_test_world_output_dir(
            project_dir,
            focus_region_title=route.from_point.region_title,
            focus_anchor_id=route.from_point.anchor_id,
        ).name
        end_output_dir = build_first_map_test_world_output_dir(
            project_dir,
            focus_region_title=route.to_point.region_title,
            focus_anchor_id=route.to_point.anchor_id,
        ).name
        handoffs.append(
            ProjectFirstMapRouteHandoff(
                route_id=route.id,
                kind=route.kind,
                summary=(
                    f"{route.from_point.region_title} / {route.from_point.anchor_id} -> "
                    f"{route.to_point.region_title} / {route.to_point.anchor_id}"
                ),
                start_command=_build_first_map_shell_command(
                    project_dir,
                    start_output_dir,
                    recommended_max_side,
                    focus_region_title=route.from_point.region_title,
                    focus_anchor_id=route.from_point.anchor_id,
                ),
                start_output_dir=start_output_dir,
                start_status_command=_build_first_map_shell_status_command(project_dir, start_output_dir),
                end_command=_build_first_map_shell_command(
                    project_dir,
                    end_output_dir,
                    recommended_max_side,
                    focus_region_title=route.to_point.region_title,
                    focus_anchor_id=route.to_point.anchor_id,
                ),
                end_output_dir=end_output_dir,
                end_status_command=_build_first_map_shell_status_command(project_dir, end_output_dir),
            )
        )
    return tuple(handoffs)


def build_first_map_story_walkthrough(
    project_dir: Path,
    config,
    recommended_max_side: int,
) -> tuple[ProjectFirstMapWalkthroughStep, ...]:
    world_plan = build_world_plan(config)
    route_plan = build_route_plan(world_plan)
    steps: list[ProjectFirstMapWalkthroughStep] = []
    seen_points: set[tuple[str, str]] = set()

    def append_step(
        *,
        region_title: str,
        anchor_id: str,
        title: str,
        summary: str,
    ) -> None:
        key = (region_title, anchor_id)
        if key in seen_points:
            return
        seen_points.add(key)
        output_dir = build_first_map_test_world_output_dir(
            project_dir,
            focus_region_title=region_title,
            focus_anchor_id=anchor_id,
        ).name
        step_index = len(steps) + 1
        steps.append(
            ProjectFirstMapWalkthroughStep(
                step_id=f"step-{step_index:02d}",
                title=title,
                summary=summary,
                command=_build_first_map_shell_command(
                    project_dir,
                    output_dir,
                    recommended_max_side,
                    focus_region_title=region_title,
                    focus_anchor_id=anchor_id,
                ),
                output_dir=output_dir,
                status_command=_build_first_map_shell_status_command(project_dir, output_dir),
            )
        )

    intra_routes = tuple(route for route in route_plan.routes if route.kind == "intra-region")
    transition_routes = tuple(route for route in route_plan.routes if route.kind == "transition")

    if intra_routes:
        first_local = intra_routes[0]
        append_step(
            region_title=first_local.from_point.region_title,
            anchor_id=first_local.from_point.anchor_id,
            title="Start here",
            summary=f'Open the first story entry point in {first_local.from_point.region_title}.',
        )
        append_step(
            region_title=first_local.to_point.region_title,
            anchor_id=first_local.to_point.anchor_id,
            title="First local payoff",
            summary=f'Move to the main focal point in {first_local.to_point.region_title}.',
        )

    for index, route in enumerate(transition_routes, start=1):
        title = "Final reveal" if index == len(transition_routes) else f"Travel beat {index}"
        append_step(
            region_title=route.to_point.region_title,
            anchor_id=route.to_point.anchor_id,
            title=title,
            summary=f'Continue into {route.to_point.region_title} through {route.to_point.anchor_id}.',
        )

    return tuple(steps)


def build_first_map_size_options(
    project_dir: Path,
    width: int,
    length: int,
) -> tuple[ProjectFirstMapSizeOption, ...]:
    options: list[ProjectFirstMapSizeOption] = []
    seen_sizes: set[tuple[int, int]] = set()
    for option_id, label, target_max_side in (
        ("pocket-scene", "Smaller test map", 256),
        ("local-district", "Town-sized map", 2048),
        ("regional-journey", "Regional map", 8192),
        ("long-travel-world", "Large cinematic map", 16000),
    ):
        option_width, option_length = _scale_dimensions_to_max_side(width, length, target_max_side)
        size_key = (option_width, option_length)
        if size_key in seen_sizes:
            continue
        seen_sizes.add(size_key)
        scale = describe_world_scale(option_width, option_length)
        options.append(
            ProjectFirstMapSizeOption(
                option_id=option_id,
                label=label,
                width=option_width,
                length=option_length,
                scale_label=scale.label,
                summary=scale.summary,
                rerun_command=(
                    f'py -3.11 -m titanforge first-map-resize "{project_dir.name}" '
                    f'--width {option_width} --length {option_length}'
                ),
            )
        )
    return tuple(options)


def build_first_map_recommended_manual_start(
    project_dir: Path,
    *,
    recommended_max_side: int,
) -> ProjectFirstMapRecommendedManualStart:
    output_dir = DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME
    return ProjectFirstMapRecommendedManualStart(
        summary=(
            "Start with one disposable centered sample before trying focused regions or larger manual-open passes."
        ),
        install_extra_command="py -3.11 -m pip install -e .[donor-spikes]",
        build_command=(
            f'py -3.11 -m titanforge first-map-test-world "{project_dir.name}" '
            f'--max-side {recommended_max_side}'
        ),
        output_dir=output_dir,
        checklist_path=f"{output_dir}\\verification-checklist.txt",
        status_command=(
            f'py -3.11 -m titanforge first-map-test-world-status "{project_dir.name}" '
            f'--sample-dir "{output_dir}"'
        ),
    )


def build_first_map_datapack_start(
    project_dir: Path,
    *,
    datapack_zip_path: Path,
    fixture_summary_path: Path,
) -> ProjectFirstMapDatapackStart:
    summary = json.loads(fixture_summary_path.read_text(encoding="utf-8"))
    function_ids = dict(summary.get("functionIds", {}))
    starter_test = dict(summary.get("starterTest", {}))
    place_function_id = str(function_ids.get("place", "titanforge:place_fixture"))
    clear_function_id = str(function_ids.get("clear", "titanforge:clear_fixture"))
    starter_verdict = str(starter_test.get("verdict", "unknown"))
    datapack_relative_path = str(datapack_zip_path.relative_to(project_dir))
    return ProjectFirstMapDatapackStart(
        summary=(
            "For the first world-side Minecraft 1.21.11 pass, copy the datapack zip into a backed-up throwaway "
            "world datapacks folder, run /reload, then place the fixture once."
        ),
        datapack_zip_path=datapack_relative_path,
        reload_command="/reload",
        place_command=f"/function {place_function_id}",
        clear_command=f"/function {clear_function_id}",
        starter_verdict=starter_verdict,
    )


def format_project_first_map_datapack_start_text(
    project_dir: Path,
    datapack_start: ProjectFirstMapDatapackStart,
    *,
    starter_test_summary: str,
    starter_test_world_advice: str,
) -> str:
    lines = [
        f"First in-world Minecraft 1.21.11 pass for: {project_dir.name}",
        "",
        datapack_start.summary,
        f"Starter verdict: {datapack_start.starter_verdict}",
    ]
    if starter_test_summary:
        lines.append(f"Why: {starter_test_summary}")
    if starter_test_world_advice:
        lines.append(f"Advice: {starter_test_world_advice}")
    lines.extend(
        (
            "",
            "Do this in order:",
            f"1. Copy {datapack_start.datapack_zip_path} into a backed-up throwaway world datapacks folder.",
            f"2. Open that world and run {datapack_start.reload_command}.",
            f"3. Place the first fixture with {datapack_start.place_command}.",
            f"4. Remove the same fixture later with {datapack_start.clear_command}.",
            "",
            "If the draft no longer matches the story, go back to review.html before continuing.",
        )
    )
    return "\n".join(lines)


def format_project_first_map_start_text(
    project_dir: Path,
    *,
    world_width: int,
    world_length: int,
    world_scale_label: str,
) -> str:
    lines = [
        f"First-map starter for: {project_dir.name}",
        f"Logical world size: {world_width} x {world_length}",
        f"World scale: {world_scale_label}",
        "",
        "Do this in order:",
        "1. Open review.html first for the main scenario-writer overview.",
        f'2. If the size is wrong, run: py -3.11 -m titanforge first-map-resize "{project_dir.name}" --width <blocks> --length <blocks>',
        f'3. If the starter theme is wrong, run: py -3.11 -m titanforge first-map-retheme "{project_dir.name}" --preset <preset-name>',
        (
            f'4. If the premise or player feeling is wrong, run: py -3.11 -m titanforge first-map-set-story "{project_dir.name}" '
            '--premise "<story text>" --player-feeling "<player feeling>"'
        ),
        f'5. If the region lineup is wrong, run: py -3.11 -m titanforge first-map-set-regions "{project_dir.name}" --region "<title>|<kind>|<story role>|<mood>|<coverage>"',
        f'6. After any manual config edits, run: py -3.11 -m titanforge first-map-refresh "{project_dir.name}"',
        "7. If the overview already looks right and you want the shortest Minecraft datapack path, open minecraft-first-pass.txt.",
        f'8. If you need the terminal handoff again later, run: py -3.11 -m titanforge first-map-status "{project_dir.name}"',
    ]
    return "\n".join(lines)


def suggest_first_map_test_world_max_side(width: int, length: int) -> int:
    logical_max_side = max(width, length)
    if logical_max_side <= 256:
        return max(16, logical_max_side - (logical_max_side % 16))
    if logical_max_side <= 1024:
        return 256
    if logical_max_side <= 4096:
        return 128
    return MIN_FIRST_MAP_TEST_WORLD_SIDE


def _align_chunk_side(side: int) -> int:
    aligned = side - (side % 16)
    return aligned if aligned >= 16 else 16


def _format_sampled_region_file_count(region_file_count: int) -> str:
    unit = "file" if region_file_count == 1 else "files"
    return f"{region_file_count} sampled .mca {unit}"


def _build_first_map_test_world_growth_sides(
    width: int,
    length: int,
    recommended_max_side: int,
) -> tuple[int, ...]:
    logical_limit = min(MAX_SPIKE_SIDE, max(width, length))
    logical_limit = _align_chunk_side(logical_limit)
    sides = [_align_chunk_side(recommended_max_side)]
    while True:
        next_side = min(MAX_SPIKE_SIDE, sides[-1] * 2, logical_limit)
        next_side = _align_chunk_side(next_side)
        if next_side <= sides[-1]:
            break
        sides.append(next_side)
    return tuple(sides)


def build_first_map_test_world_strategy(width: int, length: int) -> dict[str, object]:
    recommended_max_side = suggest_first_map_test_world_max_side(width, length)
    logical_max_side = max(width, length)
    if logical_max_side <= 256:
        summary = "The first sampled Minecraft test can stay close to the real footprint."
        reason = "This world is already small enough that a near-full sampled window stays manageable."
    elif logical_max_side <= 1024:
        summary = "Start with a 256 x 256 sampled window before trying larger manual Minecraft passes."
        reason = "This keeps the first throwaway test readable while still covering a meaningful slice of the map."
    elif logical_max_side <= 4096:
        summary = "Start with a 128 x 128 sampled window before trying larger manual Minecraft passes."
        reason = "The logical world is large enough that a smaller first sample is safer for command load, cleanup, and visual inspection."
    else:
        summary = "Start with a 64 x 64 sampled window before trying larger manual Minecraft passes."
        reason = "This world is too large for a comfortable first manual Minecraft pass, so begin with a very small disposable slice."
    sampled_width = min(width, recommended_max_side)
    sampled_length = min(length, recommended_max_side)
    recommended_region_file_count = count_sampled_region_files(sampled_width, sampled_length)
    growth_sides = _build_first_map_test_world_growth_sides(width, length, recommended_max_side)
    first_multi_region_max_side = next(
        (
            side
            for side in growth_sides
            if count_sampled_region_files(min(width, side), min(length, side)) > 1
        ),
        None,
    )
    first_multi_region_file_count = (
        count_sampled_region_files(min(width, first_multi_region_max_side), min(length, first_multi_region_max_side))
        if first_multi_region_max_side is not None
        else None
    )
    region_file_summary = (
        f"The starter sample should write {_format_sampled_region_file_count(recommended_region_file_count)} under test-world\\region\\."
    )
    if first_multi_region_max_side is None:
        multi_region_summary = "Even the largest safe sampled growth here should stay inside one sampled .mca file."
    elif first_multi_region_max_side == recommended_max_side:
        multi_region_summary = (
            f"This starter sample already spans {_format_sampled_region_file_count(recommended_region_file_count)}."
        )
    else:
        multi_region_summary = (
            f"The first multi-file growth is --max-side {first_multi_region_max_side}, which should write "
            f"{_format_sampled_region_file_count(first_multi_region_file_count or 1)}."
        )
    return {
        "recommendedMaxSide": recommended_max_side,
        "summary": summary,
        "reason": reason,
        "recommendedRegionFileCount": recommended_region_file_count,
        "regionFileSummary": region_file_summary,
        "firstMultiRegionMaxSide": first_multi_region_max_side,
        "firstMultiRegionRegionFileCount": first_multi_region_file_count,
        "multiRegionSummary": multi_region_summary,
    }


def _read_first_map_refresh_settings(project_dir: Path) -> tuple[str, int, bool]:
    manifest_path = project_dir / "first-map-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing first-map manifest: {manifest_path}")

    manifest = read_project_first_map_manifest(manifest_path)
    project = dict(manifest.get("project", {}))
    terrain = dict(manifest.get("terrain", {}))
    draft_manifest_path = project_dir / "first-map" / "draft" / "draft-manifest.json"
    max_draft_side = DEFAULT_MAX_DRAFT_SIDE
    if draft_manifest_path.exists():
        draft_manifest = json.loads(draft_manifest_path.read_text(encoding="utf-8"))
        max_draft_side = int(dict(draft_manifest.get("raster", {})).get("maxDraftSide", DEFAULT_MAX_DRAFT_SIDE))
    return (
        str(project.get("preset", "unknown")),
        max_draft_side,
        bool(terrain.get("cleanupApplied", True)),
    )


def _finalize_project_first_map(
    project_dir: Path,
    *,
    template_result: ProjectTemplateResult,
    location_result: ProjectLocationResult,
    max_draft_side: int,
    use_cleanup_for_heightmap: bool,
) -> ProjectFirstMapResult:
    manifest_path = project_dir / "first-map-manifest.json"
    first_map_start_path = project_dir / DEFAULT_FIRST_MAP_START_FILE_NAME
    review_page_path = project_dir / "review.html"
    provisional_result = ProjectFirstMapResult(
        project_dir=project_dir,
        manifest_path=manifest_path,
        review_page_path=review_page_path,
        max_draft_side=max_draft_side,
        template_result=template_result,
        location_result=location_result,
    )
    write_project_first_map_review_page(provisional_result, review_page_path)
    scale = describe_world_scale(template_result.config.width, template_result.config.length)
    test_world_strategy = build_first_map_test_world_strategy(template_result.config.width, template_result.config.length)
    key_regions = tuple(region.title for region in template_result.config.regions)
    focus_region_commands = build_first_map_focus_region_commands(
        project_dir,
        key_regions,
        int(test_world_strategy["recommendedMaxSide"]),
    )
    focus_anchor_commands = build_first_map_focus_anchor_commands(
        project_dir,
        template_result.config,
        int(test_world_strategy["recommendedMaxSide"]),
    )
    route_handoffs = build_first_map_route_handoffs(
        project_dir,
        template_result.config,
        int(test_world_strategy["recommendedMaxSide"]),
    )
    recommended_walkthrough = build_first_map_story_walkthrough(
        project_dir,
        template_result.config,
        int(test_world_strategy["recommendedMaxSide"]),
    )
    recommended_manual_start = build_first_map_recommended_manual_start(
        project_dir,
        recommended_max_side=int(test_world_strategy["recommendedMaxSide"]),
    )
    datapack_start = build_first_map_datapack_start(
        project_dir,
        datapack_zip_path=location_result.draft_result.datapack_fixture_zip_path,
        fixture_summary_path=location_result.draft_result.fixture_summary_path,
    )
    first_map_start_path.write_text(
        format_project_first_map_start_text(
            project_dir,
            world_width=template_result.config.width,
            world_length=template_result.config.length,
            world_scale_label=scale.label,
        )
        + "\n",
        encoding="utf-8",
    )
    fixture_summary = json.loads(location_result.draft_result.fixture_summary_path.read_text(encoding="utf-8"))
    starter_test = dict(fixture_summary.get("starterTest", {}))
    minecraft_first_pass_path = project_dir / DEFAULT_FIRST_MAP_MINECRAFT_FIRST_PASS_FILE_NAME
    minecraft_first_pass_path.write_text(
        format_project_first_map_datapack_start_text(
            project_dir,
            datapack_start,
            starter_test_summary=str(starter_test.get("summary", "")),
            starter_test_world_advice=str(starter_test.get("worldAdvice", "")),
        )
        + "\n",
        encoding="utf-8",
    )
    size_options = build_first_map_size_options(
        project_dir,
        template_result.config.width,
        template_result.config.length,
    )

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
            "worldSizeEdits": {
                "editFile": template_result.config_path.name,
                "editFields": ["width", "length"],
                "allowedRange": {
                    "minBlocks": PROJECT_TEMPLATE_MIN_SIDE,
                    "maxBlocks": PROJECT_TEMPLATE_MAX_SIDE,
                },
                "recommendedCommand": f'py -3.11 -m titanforge first-map-resize "{project_dir.name}" --width <blocks> --length <blocks>',
                "examples": [
                    {
                        "id": option.option_id,
                        "label": option.label,
                        "width": option.width,
                        "length": option.length,
                        "scaleLabel": option.scale_label,
                        "summary": option.summary,
                        "rerunCommand": option.rerun_command,
                    }
                    for option in size_options
                ],
            },
            "storyRoutes": {
                "routePlan": str(location_result.draft_result.route_plan_path.relative_to(project_dir)),
                "routePreview": str(location_result.draft_result.route_preview_path.relative_to(project_dir)),
                "recommendedWalkthrough": [
                    {
                        "stepId": step.step_id,
                        "title": step.title,
                        "summary": step.summary,
                        "command": step.command,
                        "outputDir": step.output_dir,
                        "statusCommand": step.status_command,
                    }
                    for step in recommended_walkthrough
                ],
                "routeSamples": [
                    {
                        "routeId": route.route_id,
                        "kind": route.kind,
                        "summary": route.summary,
                        "startCommand": route.start_command,
                        "startOutputDir": route.start_output_dir,
                        "startStatusCommand": route.start_status_command,
                        "endCommand": route.end_command,
                        "endOutputDir": route.end_output_dir,
                        "endStatusCommand": route.end_status_command,
                    }
                    for route in route_handoffs
                ],
            },
            "actionPlan": {
                "openSequence": [
                    {
                        "id": "first-map-start",
                        "path": first_map_start_path.name,
                        "summary": "Open this first from the project folder when you want a short text handoff before the HTML review.",
                    },
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
                        "summary": "Edit this when premise, regions, or other story settings need another generation pass.",
                    },
                    {
                        "id": "minecraft-first-pass",
                        "path": minecraft_first_pass_path.name,
                        "summary": "Use this when the visual review already looks right and you want the shortest in-world datapack path.",
                    },
                ],
                "nextActions": [
                    {
                        "id": "refresh-first-map",
                        "summary": "After editing the config, rerun first-map-refresh so the root handoff and first-map outputs stay in sync.",
                        "commandHint": f'py -3.11 -m titanforge first-map-refresh "{project_dir.name}"',
                    },
                    {
                        "id": "resize-first-map",
                        "summary": "Use first-map-resize when only width or length should change without hand-editing titanforge.toml.",
                        "commandHint": f'py -3.11 -m titanforge first-map-resize "{project_dir.name}" --width <blocks> --length <blocks>',
                    },
                    {
                        "id": "retheme-first-map",
                        "summary": "Use first-map-retheme when the starter story and region lineup should switch to another preset without hand-editing TOML.",
                        "commandHint": f'py -3.11 -m titanforge first-map-retheme "{project_dir.name}" --preset <preset-name>',
                    },
                    {
                        "id": "set-story-first-map",
                        "summary": "Use first-map-set-story when the premise or player feeling should change without hand-editing [creative] in TOML.",
                        "commandHint": (
                            f'py -3.11 -m titanforge first-map-set-story "{project_dir.name}" '
                            '--premise "<story text>" --player-feeling "<player feeling>"'
                        ),
                    },
                    {
                        "id": "set-regions-first-map",
                        "summary": "Use first-map-set-regions when the map needs a custom region lineup without hand-editing [[regions]] in TOML.",
                        "commandHint": f'py -3.11 -m titanforge first-map-set-regions "{project_dir.name}" --region "<title>|<kind>|<story role>|<mood>|<coverage>"',
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
            "refreshFirstMap": f'py -3.11 -m titanforge first-map-refresh "{project_dir.name}"',
            "resizeFirstMap": f'py -3.11 -m titanforge first-map-resize "{project_dir.name}" --width <blocks> --length <blocks>',
            "rethemeFirstMap": f'py -3.11 -m titanforge first-map-retheme "{project_dir.name}" --preset <preset-name>',
            "setStoryFirstMap": (
                f'py -3.11 -m titanforge first-map-set-story "{project_dir.name}" '
                '--premise "<story text>" --player-feeling "<player feeling>"'
            ),
            "setRegionsFirstMap": f'py -3.11 -m titanforge first-map-set-regions "{project_dir.name}" --region "<title>|<kind>|<story role>|<mood>|<coverage>"',
            "rerunProjectLocation": (
                f'py -3.11 -m titanforge project-location "{template_result.config_path.name}" '
                f'"{location_result.output_dir.name}" --use-cleanup-for-heightmap'
            ),
            "buildTestWorld": (
                f'py -3.11 -m titanforge first-map-test-world "{project_dir.name}" '
                f'--max-side {test_world_strategy["recommendedMaxSide"]}'
            ),
            "growTestWorld": (
                f'py -3.11 -m titanforge first-map-test-world-grow "{project_dir.name}"'
            ),
            "verifyTestWorld": (
                f'py -3.11 -m titanforge first-map-test-world-verify "{project_dir.name}" '
                '--check <check-id> --check-status <status>'
            ),
            "testWorldStatus": (
                f'py -3.11 -m titanforge first-map-test-world-status "{project_dir.name}"'
            ),
        },
        "minecraftHandoff": {
            "artifacts": {
                "fixtureSummary": str(location_result.draft_result.fixture_summary_path.relative_to(project_dir)),
                "fixtureCommands": str(location_result.draft_result.fixture_commands_path.relative_to(project_dir)),
                "datapackFixtureZip": str(location_result.draft_result.datapack_fixture_zip_path.relative_to(project_dir)),
                "minecraftFirstPass": minecraft_first_pass_path.name,
            },
            "datapackStart": {
                "summary": datapack_start.summary,
                "datapackZipPath": datapack_start.datapack_zip_path,
                "reloadCommand": datapack_start.reload_command,
                "placeCommand": datapack_start.place_command,
                "clearCommand": datapack_start.clear_command,
                "starterVerdict": datapack_start.starter_verdict,
            },
            "testWorld": {
                "requiresOptionalExtra": "py -3.11 -m pip install -e .[donor-spikes]",
                "buildCommand": (
                    f'py -3.11 -m titanforge first-map-test-world "{project_dir.name}" '
                    f'--max-side {test_world_strategy["recommendedMaxSide"]}'
                ),
                "growCommand": f'py -3.11 -m titanforge first-map-test-world-grow "{project_dir.name}"',
                "statusCommand": f'py -3.11 -m titanforge first-map-test-world-status "{project_dir.name}"',
                "verifyCommand": (
                    f'py -3.11 -m titanforge first-map-test-world-verify "{project_dir.name}" '
                    '--check <check-id> --check-status <status>'
                ),
                "outputDir": DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME,
                "recommendedStart": {
                    "summary": recommended_manual_start.summary,
                    "installExtraCommand": recommended_manual_start.install_extra_command,
                    "buildCommand": recommended_manual_start.build_command,
                    "outputDir": recommended_manual_start.output_dir,
                    "checklistPath": recommended_manual_start.checklist_path,
                    "statusCommand": recommended_manual_start.status_command,
                },
                "strategy": test_world_strategy,
                "focusRegionCommands": [
                    {
                        "regionTitle": region_title,
                        "command": command,
                        "outputDir": output_dir,
                        "statusCommand": status_command,
                    }
                    for region_title, command, output_dir, status_command in focus_region_commands
                ],
                "focusAnchorCommands": [
                    {
                        "anchorLabel": anchor_label,
                        "command": command,
                        "outputDir": output_dir,
                        "statusCommand": status_command,
                    }
                    for anchor_label, command, output_dir, status_command in focus_anchor_commands
                ],
            },
            "reviewOrder": [
                {
                    "id": "minecraft-first-pass",
                    "path": minecraft_first_pass_path.name,
                    "summary": "Open this first for the shortest in-world datapack path before the longer shell workflow.",
                },
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
            "firstMapStart": first_map_start_path.name,
            "rootReviewPage": review_page_path.name,
            "minecraftFirstPass": minecraft_first_pass_path.name,
            "projectLocationDir": location_result.output_dir.name,
            "locationReviewPage": str(location_result.location_result.review_page_path.relative_to(project_dir)),
            "bridgeManifest": str(location_result.manifest_path.relative_to(project_dir)),
            "draftMask": str(location_result.draft_result.draft_mask_path.relative_to(project_dir)),
            "routePlan": str(location_result.draft_result.route_plan_path.relative_to(project_dir)),
            "routePreview": str(location_result.draft_result.route_preview_path.relative_to(project_dir)),
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
    return provisional_result


def refresh_project_first_map(
    project_dir: Path,
    *,
    max_draft_side: int | None = None,
    use_cleanup_for_heightmap: bool | None = None,
    preset_name: str | None = None,
) -> ProjectFirstMapResult:
    stored_preset_name, stored_max_draft_side, stored_cleanup_flag = _read_first_map_refresh_settings(project_dir)
    config_path = project_dir / "titanforge.toml"
    config = load_project_config(config_path)
    resolved_max_draft_side = stored_max_draft_side if max_draft_side is None else max_draft_side
    resolved_cleanup = stored_cleanup_flag if use_cleanup_for_heightmap is None else use_cleanup_for_heightmap
    resolved_preset_name = stored_preset_name if preset_name is None else preset_name
    location_result = write_project_location(
        config,
        project_dir / "first-map",
        max_draft_side=resolved_max_draft_side,
        use_cleanup_for_heightmap=resolved_cleanup,
        project_root_artifacts=(
            (DEFAULT_FIRST_MAP_START_FILE_NAME, f"../{DEFAULT_FIRST_MAP_START_FILE_NAME}"),
            ("review.html", "../review.html"),
            (DEFAULT_FIRST_MAP_MINECRAFT_FIRST_PASS_FILE_NAME, f"../{DEFAULT_FIRST_MAP_MINECRAFT_FIRST_PASS_FILE_NAME}"),
        ),
    )
    template_result = ProjectTemplateResult(
        project_dir=project_dir,
        config_path=config_path,
        suggested_output_dir=project_dir / "first-map",
        preset_name=resolved_preset_name,
        config=config,
    )
    return _finalize_project_first_map(
        project_dir,
        template_result=template_result,
        location_result=location_result,
        max_draft_side=resolved_max_draft_side,
        use_cleanup_for_heightmap=resolved_cleanup,
    )


def resize_project_first_map(project_dir: Path, *, width: int, length: int) -> ProjectFirstMapResizeResult:
    config_path = project_dir / "titanforge.toml"
    current_config = load_project_config(config_path)
    updated_config = rewrite_project_template_world_size(config_path, width, length)
    refreshed_result = refresh_project_first_map(project_dir)
    return ProjectFirstMapResizeResult(
        project_dir=project_dir,
        config_path=config_path,
        old_width=current_config.width,
        old_length=current_config.length,
        new_width=updated_config.width,
        new_length=updated_config.length,
        refreshed_result=refreshed_result,
    )


def retheme_project_first_map(project_dir: Path, *, preset_name: str) -> ProjectFirstMapRethemeResult:
    config_path = project_dir / "titanforge.toml"
    old_preset_name, _, _ = _read_first_map_refresh_settings(project_dir)
    rewrite_project_template_preset(config_path, preset_name)
    refreshed_result = refresh_project_first_map(project_dir, preset_name=preset_name)
    return ProjectFirstMapRethemeResult(
        project_dir=project_dir,
        config_path=config_path,
        old_preset_name=old_preset_name,
        new_preset_name=preset_name,
        refreshed_result=refreshed_result,
    )


def set_project_first_map_story(
    project_dir: Path,
    *,
    premise: str,
    player_feeling: str,
) -> ProjectFirstMapStoryResult:
    config_path = project_dir / "titanforge.toml"
    current_config = load_project_config(config_path)
    updated_config = rewrite_project_template_story(
        config_path,
        premise=premise,
        player_experience=player_feeling,
    )
    refreshed_result = refresh_project_first_map(project_dir)
    return ProjectFirstMapStoryResult(
        project_dir=project_dir,
        config_path=config_path,
        old_premise=current_config.premise,
        old_player_feeling=current_config.player_experience,
        new_premise=updated_config.premise,
        new_player_feeling=updated_config.player_experience,
        refreshed_result=refreshed_result,
    )


def replace_project_first_map_regions(project_dir: Path, *, region_specs: tuple[str, ...]) -> ProjectFirstMapRegionsResult:
    config_path = project_dir / "titanforge.toml"
    current_config = load_project_config(config_path)
    updated_config = rewrite_project_template_regions(config_path, region_specs)
    refreshed_result = refresh_project_first_map(project_dir)
    return ProjectFirstMapRegionsResult(
        project_dir=project_dir,
        config_path=config_path,
        old_region_count=len(current_config.regions),
        new_region_count=len(updated_config.regions),
        refreshed_result=refreshed_result,
    )


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
        project_root_artifacts=(
            (DEFAULT_FIRST_MAP_START_FILE_NAME, f"../{DEFAULT_FIRST_MAP_START_FILE_NAME}"),
            ("review.html", "../review.html"),
            (DEFAULT_FIRST_MAP_MINECRAFT_FIRST_PASS_FILE_NAME, f"../{DEFAULT_FIRST_MAP_MINECRAFT_FIRST_PASS_FILE_NAME}"),
        ),
    )
    return _finalize_project_first_map(
        project_dir,
        template_result=template_result,
        location_result=location_result,
        max_draft_side=max_draft_side,
        use_cleanup_for_heightmap=use_cleanup_for_heightmap,
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
            f"- first-map start: {DEFAULT_FIRST_MAP_START_FILE_NAME}",
            f"- root review: {result.review_page_path.name}",
            f"- minecraft first pass: {DEFAULT_FIRST_MAP_MINECRAFT_FIRST_PASS_FILE_NAME}",
            f"Logical world size: {result.template_result.config.width} x {result.template_result.config.length}",
            f"World scale: {scale.label}",
            f"Scale use: {scale.summary}",
            f"Preset story: {result.template_result.config.premise}",
            f"Player feeling: {result.template_result.config.player_experience}",
            f"Key regions: {region_lineup}",
            f"Draft raster: {result.location_result.draft_result.raster_width} x {result.location_result.draft_result.raster_length}",
            f"Scale bridge: 1 px = {result.location_result.draft_result.blocks_per_pixel} blocks",
            f'Change world size later: py -3.11 -m titanforge first-map-resize "{result.project_dir.name}" --width <blocks> --length <blocks>',
            f'Switch starter preset later: py -3.11 -m titanforge first-map-retheme "{result.project_dir.name}" --preset <preset-name>',
            (
                f'Change story later: py -3.11 -m titanforge first-map-set-story "{result.project_dir.name}" '
                '--premise "<story text>" --player-feeling "<player feeling>"'
            ),
            f'Set custom regions later: py -3.11 -m titanforge first-map-set-regions "{result.project_dir.name}" --region "<title>|<kind>|<story role>|<mood>|<coverage>"',
            scale.planning_note,
            f'After other config edits: py -3.11 -m titanforge first-map-refresh "{result.project_dir.name}"',
            "If the overview already looks right: open minecraft-first-pass.txt for the shortest in-world datapack path.",
            "Optional Minecraft shell: install donor-spikes, then run first-map-test-world from this project folder.",
            f'If a sample passes manual checks: py -3.11 -m titanforge first-map-test-world-grow "{result.project_dir.name}"',
            f'If you need to record manual checks: py -3.11 -m titanforge first-map-test-world-verify "{result.project_dir.name}" --check <check-id> --check-status <status>',
            *[f"Warning: {warning}" for warning in result.location_result.warnings],
            f"Validation: {result.location_result.location_result.errors} errors, {result.location_result.location_result.warnings} warnings",
            f"Open first: {DEFAULT_FIRST_MAP_START_FILE_NAME}",
        )
    )


def format_project_first_map_resize_result(result: ProjectFirstMapResizeResult) -> str:
    return "\n".join(
        (
            f"First-map resize: {result.project_dir}",
            f"- config: {result.config_path.name}",
            f"- old size: {result.old_width} x {result.old_length}",
            f"- new size: {result.new_width} x {result.new_length}",
            f"- refreshed review: {result.refreshed_result.review_page_path.name}",
            f"- refreshed project-location dir: {result.refreshed_result.location_result.output_dir.name}",
            f"Validation: {result.refreshed_result.location_result.location_result.errors} errors, {result.refreshed_result.location_result.location_result.warnings} warnings",
            f"Open first: {result.refreshed_result.review_page_path.name}",
        )
    )


def format_project_first_map_retheme_result(result: ProjectFirstMapRethemeResult) -> str:
    return "\n".join(
        (
            f"First-map retheme: {result.project_dir}",
            f"- config: {result.config_path.name}",
            f"- old preset: {result.old_preset_name}",
            f"- new preset: {result.new_preset_name}",
            f"- refreshed review: {result.refreshed_result.review_page_path.name}",
            f"- refreshed project-location dir: {result.refreshed_result.location_result.output_dir.name}",
            f"Validation: {result.refreshed_result.location_result.location_result.errors} errors, {result.refreshed_result.location_result.location_result.warnings} warnings",
            f"Open first: {result.refreshed_result.review_page_path.name}",
        )
    )


def format_project_first_map_story_result(result: ProjectFirstMapStoryResult) -> str:
    return "\n".join(
        (
            f"First-map story: {result.project_dir}",
            f"- config: {result.config_path.name}",
            f"- old premise: {result.old_premise}",
            f"- new premise: {result.new_premise}",
            f"- old player feeling: {result.old_player_feeling}",
            f"- new player feeling: {result.new_player_feeling}",
            f"- refreshed review: {result.refreshed_result.review_page_path.name}",
            f"- refreshed project-location dir: {result.refreshed_result.location_result.output_dir.name}",
            f"Validation: {result.refreshed_result.location_result.location_result.errors} errors, {result.refreshed_result.location_result.location_result.warnings} warnings",
            f"Open first: {result.refreshed_result.review_page_path.name}",
        )
    )


def format_project_first_map_regions_result(result: ProjectFirstMapRegionsResult) -> str:
    return "\n".join(
        (
            f"First-map regions: {result.project_dir}",
            f"- config: {result.config_path.name}",
            f"- old region count: {result.old_region_count}",
            f"- new region count: {result.new_region_count}",
            f"- refreshed review: {result.refreshed_result.review_page_path.name}",
            f"- refreshed project-location dir: {result.refreshed_result.location_result.output_dir.name}",
            f"Validation: {result.refreshed_result.location_result.location_result.errors} errors, {result.refreshed_result.location_result.location_result.warnings} warnings",
            f"Open first: {result.refreshed_result.review_page_path.name}",
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
    max_side: int | None = None,
    focus_region_title: str | None = None,
    focus_anchor_id: str | None = None,
    anvil_module: Any | None = None,
) -> AnvilTestWorldResult:
    config = load_project_first_map_config(project_dir)
    resolved_output_dir = (
        output_dir
        if output_dir is not None
        else build_first_map_test_world_output_dir(
            project_dir,
            focus_region_title=focus_region_title,
            focus_anchor_id=focus_anchor_id,
        )
    )
    resolved_max_side = max_side if max_side is not None else suggest_first_map_test_world_max_side(config.width, config.length)
    command = f'py -3.11 -m titanforge first-map-test-world "{project_dir}"'
    if output_dir is not None:
        command += f' --output-dir "{output_dir}"'
    command += " --max-side {max_side}"
    if focus_region_title is not None:
        command += f' --focus-region "{focus_region_title}"'
    if focus_anchor_id is not None:
        command += f' --focus-anchor "{focus_anchor_id}"'
    return write_anvil_test_world(
        config,
        resolved_output_dir,
        max_side=resolved_max_side,
        focus_region_title=focus_region_title,
        focus_anchor_id=focus_anchor_id,
        anvil_module=anvil_module,
        rerun_command_template=command,
        project_status_command=f'py -3.11 -m titanforge first-map-status "{project_dir}"',
    )


def grow_project_first_map_test_world(
    project_dir: Path,
    *,
    sample_dir_name: str = DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME,
    output_dir_name: str | None = None,
) -> AnvilTestWorldGrowthResult:
    source_output_dir = project_dir / sample_dir_name
    target_output_dir = project_dir / output_dir_name if output_dir_name is not None else None
    return grow_test_world(source_output_dir, target_output_dir=target_output_dir)


def summarize_project_first_map_test_world(
    project_dir: Path,
    *,
    sample_dir_name: str = DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME,
) -> AnvilTestWorldStatusResult:
    return summarize_test_world_status(project_dir / sample_dir_name)


def verify_project_first_map_test_world(
    project_dir: Path,
    *,
    sample_dir_name: str = DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME,
    status: str | None = None,
    check_id: str | None = None,
    check_status: str | None = None,
    check_note: str | None = None,
    report_note: str | None = None,
):
    return update_test_world_verification_report(
        project_dir / sample_dir_name / "verification-report.json",
        status=status,
        check_id=check_id,
        check_status=check_status,
        check_note=check_note,
        report_note=report_note,
    )


def format_project_first_map_test_world_status_result(
    project_dir: Path,
    sample_dir_name: str,
    result: AnvilTestWorldStatusResult,
) -> str:
    status_text = format_test_world_status_result(result)
    filtered_lines = [
        line
        for line in status_text.splitlines()
        if not line.startswith("- grow wrapper:")
    ]
    lines = ["\n".join(filtered_lines)]
    status_command = f'py -3.11 -m titanforge first-map-test-world-status "{project_dir}"'
    grow_command = f'py -3.11 -m titanforge first-map-test-world-grow "{project_dir}"'
    verify_command = (
        f'py -3.11 -m titanforge first-map-test-world-verify "{project_dir}" '
        '--check <check-id> --check-status <status>'
    )
    if sample_dir_name != DEFAULT_FIRST_MAP_TEST_WORLD_DIR_NAME:
        status_command += f' --sample-dir "{sample_dir_name}"'
        grow_command += f' --sample-dir "{sample_dir_name}"'
        verify_command += f' --sample-dir "{sample_dir_name}"'
    lines.extend(
        (
            "First-map wrappers:",
            f"- status: {status_command}",
            f"- grow: {grow_command}",
            f"- verify: {verify_command}",
        )
    )
    return "\n".join(lines)


def summarize_project_first_map_status(project_dir: Path) -> ProjectFirstMapStatusResult:
    manifest_path = project_dir / "first-map-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing first-map manifest: {manifest_path}")

    manifest = read_project_first_map_manifest(manifest_path)
    project = manifest.get("project", {})
    world = manifest.get("world", {})
    guidance = manifest.get("guidance", {})
    action_plan = dict(guidance.get("actionPlan", {}))
    world_scale = dict(guidance.get("worldScale", {}))
    preset = dict(guidance.get("preset", {}))
    world_size_edits = dict(guidance.get("worldSizeEdits", {}))
    story_routes = dict(guidance.get("storyRoutes", {}))
    commands = dict(manifest.get("commands", {}))
    artifacts = dict(manifest.get("artifacts", {}))
    minecraft_handoff = dict(manifest.get("minecraftHandoff", {}))
    handoff_artifacts = dict(minecraft_handoff.get("artifacts", {}))
    test_world = dict(minecraft_handoff.get("testWorld", {}))
    datapack_start_data = dict(minecraft_handoff.get("datapackStart", {}))
    test_world_strategy = dict(test_world.get("strategy", {}))
    recommended_manual_start_data = dict(test_world.get("recommendedStart", {}))
    test_world_focus_commands = tuple(
        (
            str(item.get("regionTitle", "")),
            str(item.get("command", "")),
            str(item.get("outputDir", "")),
            str(item.get("statusCommand", "")),
        )
        for item in test_world.get("focusRegionCommands", [])
    )
    test_world_focus_anchor_commands = tuple(
        (
            str(item.get("anchorLabel", "")),
            str(item.get("command", "")),
            str(item.get("outputDir", "")),
            str(item.get("statusCommand", "")),
        )
        for item in test_world.get("focusAnchorCommands", [])
    )
    route_handoffs = tuple(
        ProjectFirstMapRouteHandoff(
            route_id=str(item.get("routeId", "")),
            kind=str(item.get("kind", "")),
            summary=str(item.get("summary", "")),
            start_command=str(item.get("startCommand", "")),
            start_output_dir=str(item.get("startOutputDir", "")),
            start_status_command=str(item.get("startStatusCommand", "")),
            end_command=str(item.get("endCommand", "")),
            end_output_dir=str(item.get("endOutputDir", "")),
            end_status_command=str(item.get("endStatusCommand", "")),
        )
        for item in story_routes.get("routeSamples", [])
    )
    recommended_walkthrough = tuple(
        ProjectFirstMapWalkthroughStep(
            step_id=str(item.get("stepId", "")),
            title=str(item.get("title", "")),
            summary=str(item.get("summary", "")),
            command=str(item.get("command", "")),
            output_dir=str(item.get("outputDir", "")),
            status_command=str(item.get("statusCommand", "")),
        )
        for item in story_routes.get("recommendedWalkthrough", [])
    )
    size_edit_options = tuple(
        ProjectFirstMapSizeOption(
            option_id=str(item.get("id", "")),
            label=str(item.get("label", "")),
            width=int(item.get("width", 0)),
            length=int(item.get("length", 0)),
            scale_label=str(item.get("scaleLabel", "")),
            summary=str(item.get("summary", "")),
            rerun_command=str(item.get("rerunCommand", "")),
        )
        for item in world_size_edits.get("examples", [])
    )

    open_sequence = tuple(
        (str(item.get("id", "unknown")), str(item.get("path", "")))
        for item in action_plan.get("openSequence", [])
    )
    open_sequence_summaries = tuple(
        (str(item.get("id", "unknown")), str(item.get("summary", "")))
        for item in action_plan.get("openSequence", [])
    )
    next_actions = tuple(
        (
            str(item.get("id", "unknown")),
            str(item.get("summary", "")),
            str(item.get("commandHint") or item.get("path") or ""),
        )
        for item in action_plan.get("nextActions", [])
    )
    minecraft_review_order = tuple(
        (
            str(item.get("id", "unknown")),
            str(item.get("path", "")),
            str(item.get("summary", "")),
        )
        for item in minecraft_handoff.get("reviewOrder", [])
    )
    command_items = tuple((str(key), str(value)) for key, value in commands.items())
    fixture_summary_path = project_dir / str(handoff_artifacts.get("fixtureSummary", Path("first-map") / "draft" / "fixture-summary.json"))
    starter_test: dict[str, object] = {}
    if fixture_summary_path.exists():
        fixture_summary = json.loads(fixture_summary_path.read_text(encoding="utf-8"))
        starter_test = dict(fixture_summary.get("starterTest", {}))

    return ProjectFirstMapStatusResult(
        project_dir=project_dir,
        manifest_path=manifest_path,
        first_map_start_path=project_dir / str(artifacts.get("firstMapStart", DEFAULT_FIRST_MAP_START_FILE_NAME)),
        minecraft_first_pass_path=project_dir / str(artifacts.get("minecraftFirstPass", handoff_artifacts.get("minecraftFirstPass", DEFAULT_FIRST_MAP_MINECRAFT_FIRST_PASS_FILE_NAME))),
        config_path=project_dir / str(project.get("configPath", "titanforge.toml")),
        review_page_path=project_dir / str(artifacts.get("rootReviewPage", "review.html")),
        location_review_path=project_dir / str(artifacts.get("locationReviewPage", Path("first-map") / "location" / "review.html")),
        draft_review_path=project_dir / str(next((path for item_id, path in open_sequence if item_id == "draft-review"), Path("first-map") / "draft" / "review.html")),
        route_plan_path=project_dir / str(story_routes.get("routePlan", artifacts.get("routePlan", Path("first-map") / "draft" / "route-plan.json"))),
        route_preview_path=project_dir / str(story_routes.get("routePreview", artifacts.get("routePreview", Path("first-map") / "draft" / "route-preview.png"))),
        fixture_summary_path=fixture_summary_path,
        fixture_commands_path=project_dir / str(handoff_artifacts.get("fixtureCommands", Path("first-map") / "draft" / "fixture-commands.txt")),
        datapack_fixture_zip_path=project_dir / str(handoff_artifacts.get("datapackFixtureZip", Path("first-map") / "draft" / "datapack-fixture.zip")),
        starter_test_verdict=str(starter_test.get("verdict", "unknown")),
        starter_test_summary=str(starter_test.get("summary", "")),
        starter_test_world_advice=str(starter_test.get("worldAdvice", "")),
        test_world_recommended_max_side=int(test_world_strategy.get("recommendedMaxSide", DEFAULT_SPIKE_MAX_SIDE)),
        test_world_strategy_summary=str(test_world_strategy.get("summary", "")),
        test_world_strategy_reason=str(test_world_strategy.get("reason", "")),
        test_world_recommended_region_file_count=int(test_world_strategy.get("recommendedRegionFileCount", 1)),
        test_world_region_file_summary=str(test_world_strategy.get("regionFileSummary", "")),
        test_world_first_multi_region_max_side=(
            int(test_world_strategy["firstMultiRegionMaxSide"])
            if test_world_strategy.get("firstMultiRegionMaxSide") is not None
            else None
        ),
        test_world_first_multi_region_file_count=(
            int(test_world_strategy["firstMultiRegionRegionFileCount"])
            if test_world_strategy.get("firstMultiRegionRegionFileCount") is not None
            else None
        ),
        test_world_multi_region_summary=str(test_world_strategy.get("multiRegionSummary", "")),
        datapack_start=ProjectFirstMapDatapackStart(
            summary=str(datapack_start_data.get("summary", "")),
            datapack_zip_path=str(datapack_start_data.get("datapackZipPath", handoff_artifacts.get("datapackFixtureZip", Path("first-map") / "draft" / "datapack-fixture.zip"))),
            reload_command=str(datapack_start_data.get("reloadCommand", "/reload")),
            place_command=str(datapack_start_data.get("placeCommand", "/function titanforge:place_fixture")),
            clear_command=str(datapack_start_data.get("clearCommand", "/function titanforge:clear_fixture")),
            starter_verdict=str(datapack_start_data.get("starterVerdict", starter_test.get("verdict", "unknown"))),
        ),
        recommended_manual_start=ProjectFirstMapRecommendedManualStart(
            summary=str(recommended_manual_start_data.get("summary", "")),
            install_extra_command=str(recommended_manual_start_data.get("installExtraCommand", "")),
            build_command=str(recommended_manual_start_data.get("buildCommand", "")),
            output_dir=str(recommended_manual_start_data.get("outputDir", "")),
            checklist_path=str(recommended_manual_start_data.get("checklistPath", "")),
            status_command=str(recommended_manual_start_data.get("statusCommand", "")),
        ),
        test_world_focus_commands=test_world_focus_commands,
        test_world_focus_anchor_commands=test_world_focus_anchor_commands,
        route_handoffs=route_handoffs,
        recommended_walkthrough=recommended_walkthrough,
        size_edit_config_path=project_dir / str(world_size_edits.get("editFile", project.get("configPath", "titanforge.toml"))),
        size_edit_options=size_edit_options,
        preset_name=str(project.get("preset", "unknown")),
        world_width=int(world.get("width", 0)),
        world_length=int(world.get("length", 0)),
        world_scale_label=str(world_scale.get("label", "unknown")),
        world_scale_summary=str(world_scale.get("summary", "")),
        world_scale_planning_note=str(world_scale.get("planningNote", "")),
        preset_story=str(preset.get("story", "")),
        player_feeling=str(preset.get("playerFeeling", "")),
        key_regions=tuple(str(item) for item in preset.get("keyRegions", [])),
        open_sequence=open_sequence,
        open_sequence_summaries=open_sequence_summaries,
        next_actions=next_actions,
        minecraft_review_order=minecraft_review_order,
        test_world_requires_optional_extra=str(test_world.get("requiresOptionalExtra", "")),
        test_world_build_command=str(test_world.get("buildCommand", "")),
        test_world_status_command=str(test_world.get("statusCommand", "")),
        test_world_output_dir=str(test_world.get("outputDir", "")),
        commands=command_items,
    )


def format_project_first_map_status_result(result: ProjectFirstMapStatusResult) -> str:
    key_regions_line = ", ".join(result.key_regions[:3])
    if len(result.key_regions) > 3:
        key_regions_line = f"{key_regions_line}, +{len(result.key_regions) - 3} more"
    lines = [
        f"First-map status: {result.project_dir}",
        f"- manifest: {result.manifest_path.name}",
        f"- first-map start: {result.first_map_start_path.name}",
        f"- minecraft first pass: {result.minecraft_first_pass_path.name}",
        f"- config: {result.config_path.name}",
        f"- preset: {result.preset_name}",
        f"- logical world size: {result.world_width} x {result.world_length}",
        f"- world scale: {result.world_scale_label}",
        f"- root review: {result.review_page_path.relative_to(result.project_dir)}",
        f"- location review: {result.location_review_path.relative_to(result.project_dir)}",
        f"- draft review: {result.draft_review_path.relative_to(result.project_dir)}",
        f"- route preview: {result.route_preview_path.relative_to(result.project_dir)}",
        f"- route plan: {result.route_plan_path.relative_to(result.project_dir)}",
        f"- fixture summary: {result.fixture_summary_path.relative_to(result.project_dir)}",
        f"- fixture commands: {result.fixture_commands_path.relative_to(result.project_dir)}",
        f"- datapack zip: {result.datapack_fixture_zip_path.relative_to(result.project_dir)}",
    ]
    if result.preset_story or result.player_feeling or key_regions_line:
        lines.append("Preset intent:")
        if result.preset_story:
            lines.append(f"- story: {result.preset_story}")
        if result.player_feeling:
            lines.append(f"- player feeling: {result.player_feeling}")
        if key_regions_line:
            lines.append(f"- key regions: {key_regions_line}")
    if result.world_scale_summary or result.world_scale_planning_note:
        lines.append("Size guidance:")
        if result.world_scale_summary:
            lines.append(f"- use: {result.world_scale_summary}")
        if result.world_scale_planning_note:
            lines.append(f"- planning note: {result.world_scale_planning_note}")
    if result.size_edit_options:
        lines.append("Change world size:")
        lines.append(
            f"- edit {result.size_edit_config_path.name}: width and length must stay between {PROJECT_TEMPLATE_MIN_SIDE} and {PROJECT_TEMPLATE_MAX_SIDE} blocks."
        )
        for option in result.size_edit_options:
            lines.append(
                f"- {option.label}: {option.width} x {option.length} ({option.scale_label}; {option.summary})"
            )
            lines.append(f"- rerun example: {option.rerun_command}")
    if result.open_sequence:
        lines.append("Review now:")
        open_summaries = dict(result.open_sequence_summaries)
        for item_id, item_path in result.open_sequence:
            summary = open_summaries.get(item_id, "")
            if summary:
                lines.append(f"- {item_id}: {summary} ({item_path})")
            else:
                lines.append(f"- {item_id}: {item_path}")
    if result.route_handoffs:
        lines.append("Story routes:")
        lines.append(f"- route-preview: {result.route_preview_path.relative_to(result.project_dir)}")
        lines.append(f"- route-plan: {result.route_plan_path.relative_to(result.project_dir)}")
        if result.recommended_walkthrough:
            lines.append("- recommended walkthrough:")
            for step in result.recommended_walkthrough:
                lines.append(f"- {step.step_id}: {step.title} ({step.summary})")
                lines.append(
                    f"- walkthrough shell: {step.command} (folder: {step.output_dir}; status: {step.status_command})"
                )
        lines.append(
            f"- full route sample pairs: {len(result.route_handoffs)} saved in first-map-manifest.json under guidance.storyRoutes.routeSamples."
        )
    if result.next_actions:
        lines.append("If you need changes:")
        for item_id, summary, detail in result.next_actions:
            if detail:
                lines.append(f"- {item_id}: {summary} ({detail})")
            else:
                lines.append(f"- {item_id}: {summary}")
    if result.minecraft_review_order or result.test_world_build_command:
        lines.append("Minecraft later:")
        if result.starter_test_verdict != "unknown":
            lines.append(
                f"- starter-test-verdict: {result.starter_test_verdict} ({result.starter_test_summary})"
            )
            if result.starter_test_world_advice:
                lines.append(f"- world advice: {result.starter_test_world_advice}")
        if result.datapack_start.summary:
            lines.append("- first in-world datapack pass:")
            lines.append(f"- summary: {result.datapack_start.summary}")
            lines.append(f"- starter verdict: {result.datapack_start.starter_verdict}")
            lines.append(f"- copy zip into world datapacks: {result.datapack_start.datapack_zip_path}")
            lines.append(f"- then run in Minecraft: {result.datapack_start.reload_command}")
            lines.append(f"- place fixture: {result.datapack_start.place_command}")
            lines.append(f"- clear fixture: {result.datapack_start.clear_command}")
        if result.recommended_manual_start.summary:
            lines.append("- recommended first manual-open:")
            lines.append(f"- summary: {result.recommended_manual_start.summary}")
            if result.recommended_manual_start.install_extra_command:
                lines.append(f"- install extra first: {result.recommended_manual_start.install_extra_command}")
            if result.recommended_manual_start.build_command:
                lines.append(f"- build shell: {result.recommended_manual_start.build_command}")
            if result.recommended_manual_start.output_dir:
                lines.append(f"- shell folder: {result.recommended_manual_start.output_dir}")
            if result.recommended_manual_start.checklist_path:
                lines.append(f"- open next: {result.recommended_manual_start.checklist_path}")
            if result.recommended_manual_start.status_command:
                lines.append(f"- reread shell status: {result.recommended_manual_start.status_command}")
        if result.test_world_strategy_summary:
            lines.append(
                f"- sampled-test-strategy: start with --max-side {result.test_world_recommended_max_side} ({result.test_world_strategy_summary})"
            )
        if result.test_world_strategy_reason:
            lines.append(f"- strategy reason: {result.test_world_strategy_reason}")
        if result.test_world_region_file_summary:
            lines.append(f"- starter sample scope: {result.test_world_region_file_summary}")
        if result.test_world_multi_region_summary:
            lines.append(f"- growth scope: {result.test_world_multi_region_summary}")
        if result.test_world_focus_commands:
            lines.append("- focus samples:")
            for region_title, command, output_dir, status_command in result.test_world_focus_commands:
                if output_dir and status_command:
                    lines.append(f"- {region_title}: {command} (folder: {output_dir}; status: {status_command})")
                else:
                    lines.append(f"- {region_title}: {command}")
        if result.test_world_focus_anchor_commands:
            lines.append("- focus anchors:")
            for anchor_label, command, output_dir, status_command in result.test_world_focus_anchor_commands:
                if output_dir and status_command:
                    lines.append(f"- {anchor_label}: {command} (folder: {output_dir}; status: {status_command})")
                else:
                    lines.append(f"- {anchor_label}: {command}")
        for item_id, item_path, summary in result.minecraft_review_order:
            if summary:
                lines.append(f"- {item_id}: {summary} ({item_path})")
            else:
                lines.append(f"- {item_id}: {item_path}")
        if result.test_world_build_command:
            lines.append("- optional-test-world: Experimental manual-open shell only, not full world export.")
    if result.commands:
        lines.append("Command hints:")
        for command_id, command_value in result.commands:
            lines.append(f"- {command_id}: {command_value}")
    lines.append(f"Open first: {result.first_map_start_path.name}")
    return "\n".join(lines)


def _slugify_focus_part(value: str) -> str:
    lowered = value.strip().lower()
    cleaned = "".join(character if character.isalnum() else "-" for character in lowered)
    parts = [part for part in cleaned.split("-") if part]
    return "-".join(parts)


def _scale_dimensions_to_max_side(width: int, length: int, target_max_side: int) -> tuple[int, int]:
    if width <= 0 or length <= 0:
        return PROJECT_TEMPLATE_MIN_SIDE, PROJECT_TEMPLATE_MIN_SIDE

    current_max_side = max(width, length)
    scale = target_max_side / current_max_side
    scaled_width = max(PROJECT_TEMPLATE_MIN_SIDE, min(PROJECT_TEMPLATE_MAX_SIDE, round(width * scale)))
    scaled_length = max(PROJECT_TEMPLATE_MIN_SIDE, min(PROJECT_TEMPLATE_MAX_SIDE, round(length * scale)))

    if max(scaled_width, scaled_length) > target_max_side:
        if scaled_width >= scaled_length:
            scaled_width = target_max_side
            scaled_length = max(PROJECT_TEMPLATE_MIN_SIDE, round(target_max_side * length / width))
        else:
            scaled_length = target_max_side
            scaled_width = max(PROJECT_TEMPLATE_MIN_SIDE, round(target_max_side * width / length))

    return scaled_width, scaled_length
