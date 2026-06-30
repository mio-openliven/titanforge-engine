from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tomllib

from titanforge import __version__
from titanforge.core.project_first_map import (
    format_project_first_map_result,
    format_project_first_map_status_result,
    summarize_project_first_map_status,
    write_project_first_map,
)
from titanforge.core.project_location import format_project_location_result, write_project_location
from titanforge.core.project_draft import format_project_draft_result, write_project_draft
from titanforge.core.project import ProjectConfig, load_project_config
from titanforge.core.project_template import (
    build_project_template_preset_catalog_data,
    build_project_template_preset_catalog_payload,
    ProjectTemplateError,
    format_project_template_preset_catalog,
    format_project_template_result,
    list_project_template_presets,
    write_project_template,
)
from titanforge.core.project_review import write_project_review_page
from titanforge.core.world_plan import build_world_plan, format_world_plan, write_world_plan
from titanforge.inventory.scanner import format_inventory_report, scan_inventory
from titanforge.layouts.mask_layout import format_mask_layout_result, write_mask_layout
from titanforge.locations.builder import build_location_pack, format_location_build_result
from titanforge.masks.analyzer import analyze_png_mask, format_mask_analysis
from titanforge.masks.coastline import format_coastline_smoothing_result, render_coastline_smoothing_preview
from titanforge.masks.cleanup import format_mask_cleanup_result, render_mask_cleanup_preview
from titanforge.masks.png import PngError
from titanforge.masks.demo import format_demo_mask_result, generate_demo_mask
from titanforge.operations.night_run import format_night_run_result, run_night_run
from titanforge.preview.mask_preview import format_mask_preview_result, render_mask_preview
from titanforge.spikes.anvil_region import (
    AnvilRegionSpikeError,
    DEFAULT_SPIKE_MAX_SIDE,
    format_anvil_region_spike_result,
    write_anvil_region_spike,
)
from titanforge.spikes.anvil_save_shell import format_anvil_save_shell_result, write_anvil_save_shell
from titanforge.spikes.anvil_test_world import (
    AnvilTestWorldVerificationError,
    format_anvil_test_world_result,
    format_test_world_status_result,
    format_test_world_verification_update_result,
    summarize_test_world_status,
    update_test_world_verification_report,
    write_anvil_test_world,
)
from titanforge.terrain.color_preview import format_terrain_color_preview_result, render_terrain_color_preview
from titanforge.terrain.heightmap_preview import format_heightmap_preview_result, render_heightmap_preview
from titanforge.terrain.model import format_terrain_grid_result, write_terrain_grid
from titanforge.validation.layout_report import format_layout_validation_report, validate_layout_file, write_layout_validation_report
from titanforge.versions.targets import ACTIVE_TARGETS, PARKING_LOT_TARGETS, PRIMARY_TARGET


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="titanforge",
        description="TitanForge Engine command-line tools.",
    )
    parser.add_argument("--version", action="store_true", help="Show TitanForge Engine version.")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("info", help="Show current engine strategy and version targets.")
    subparsers.add_parser(
        "preset-catalog",
        help="Show plain-language starter preset guidance for scenario writers.",
    )
    preset_catalog_parser = subparsers.choices["preset-catalog"]
    preset_catalog_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the starter preset catalog as JSON for tooling or future UI layers.",
    )

    init_project_parser = subparsers.add_parser(
        "init-project",
        help="Write a starter titanforge.toml from a cinematic preset.",
    )
    init_project_parser.add_argument("project_dir", type=Path, help="Folder that will receive titanforge.toml.")
    init_project_parser.add_argument("--name", help="Project name shown in review pages and manifests.")
    init_project_parser.add_argument("--width", type=int, default=2048, help="Logical world width in blocks.")
    init_project_parser.add_argument("--length", type=int, default=2048, help="Logical world length in blocks.")
    init_project_parser.add_argument(
        "--preset",
        choices=list_project_template_presets(),
        default="coastal-valley",
        help="Starter region/story preset.",
    )
    init_project_parser.add_argument(
        "--target-version",
        default=PRIMARY_TARGET.minecraft_version,
        help="Minecraft target version written into the starter config.",
    )

    first_map_parser = subparsers.add_parser(
        "first-map",
        help="Create a starter titanforge.toml and immediately build the first project-location pack.",
    )
    first_map_parser.add_argument("project_dir", type=Path, help="Folder that will receive the starter project and first map.")
    first_map_parser.add_argument("--name", help="Project name shown in review pages and manifests.")
    first_map_parser.add_argument("--width", type=int, default=2048, help="Logical world width in blocks.")
    first_map_parser.add_argument("--length", type=int, default=2048, help="Logical world length in blocks.")
    first_map_parser.add_argument(
        "--preset",
        choices=list_project_template_presets(),
        default="coastal-valley",
        help="Starter region/story preset.",
    )
    first_map_parser.add_argument(
        "--target-version",
        default=PRIMARY_TARGET.minecraft_version,
        help="Minecraft target version written into the starter config.",
    )
    first_map_parser.add_argument(
        "--max-draft-side",
        type=int,
        default=1024,
        help="Maximum raster side for the generated draft mask.",
    )
    first_map_parser.add_argument(
        "--no-cleanup-for-heightmap",
        action="store_true",
        help="Keep the first location heightmap on the raw draft mask instead of the cleanup preview.",
    )
    first_map_status_parser = subparsers.add_parser(
        "first-map-status",
        help="Read the current handoff status of an existing first-map project without rebuilding it.",
    )
    first_map_status_parser.add_argument("project_dir", type=Path, help="Existing first-map project folder.")

    plan_parser = subparsers.add_parser("plan", help="Read and summarize a TitanForge project config.")
    plan_parser.add_argument("config", type=Path, help="Path to titanforge.toml.")
    plan_parser.add_argument(
        "--review-page",
        type=Path,
        help="Optional HTML output path for a human-friendly world brief review page.",
    )
    plan_parser.add_argument(
        "--world-plan",
        type=Path,
        help="Optional JSON output path for a neutral spatial world-plan artifact.",
    )

    project_draft_parser = subparsers.add_parser(
        "project-draft",
        help="Build a first human-friendly draft pack from titanforge.toml.",
    )
    project_draft_parser.add_argument("config", type=Path, help="Path to titanforge.toml.")
    project_draft_parser.add_argument("output_dir", type=Path, help="Output folder for the project draft pack.")
    project_draft_parser.add_argument(
        "--max-draft-side",
        type=int,
        default=1024,
        help="Maximum raster side for the generated draft mask.",
    )

    project_location_parser = subparsers.add_parser(
        "project-location",
        help="Build a project draft and location pack directly from titanforge.toml.",
    )
    project_location_parser.add_argument("config", type=Path, help="Path to titanforge.toml.")
    project_location_parser.add_argument("output_dir", type=Path, help="Output folder for the bridged project pack.")
    project_location_parser.add_argument(
        "--max-draft-side",
        type=int,
        default=1024,
        help="Maximum raster side for the generated draft mask.",
    )
    project_location_parser.add_argument(
        "--use-cleanup-for-heightmap",
        action="store_true",
        help="Render location heightmap-preview.png from mask-cleanup-preview.png.",
    )

    anvil_region_spike_parser = subparsers.add_parser(
        "anvil-region-spike",
        help="Write one experimental donor-backed .mca region from a TitanForge project config.",
    )
    anvil_region_spike_parser.add_argument("config", type=Path, help="Path to titanforge.toml.")
    anvil_region_spike_parser.add_argument("output_dir", type=Path, help="Output folder for the donor-backed region spike.")
    anvil_region_spike_parser.add_argument(
        "--max-side",
        type=int,
        default=DEFAULT_SPIKE_MAX_SIDE,
        help="Chunk-aligned sampled side in blocks. Must stay within one region file.",
    )

    anvil_save_shell_parser = subparsers.add_parser(
        "anvil-save-shell",
        help="Write one experimental save-like folder around a sampled donor-backed .mca region.",
    )
    anvil_save_shell_parser.add_argument("config", type=Path, help="Path to titanforge.toml.")
    anvil_save_shell_parser.add_argument("output_dir", type=Path, help="Output folder for the sampled save-shell handoff.")
    anvil_save_shell_parser.add_argument(
        "--max-side",
        type=int,
        default=DEFAULT_SPIKE_MAX_SIDE,
        help="Chunk-aligned sampled side in blocks. Must stay within one region file.",
    )

    anvil_test_world_parser = subparsers.add_parser(
        "anvil-test-world",
        help="Write one experimental minimal test-world shell around a sampled donor-backed .mca region.",
    )
    anvil_test_world_parser.add_argument("config", type=Path, help="Path to titanforge.toml.")
    anvil_test_world_parser.add_argument("output_dir", type=Path, help="Output folder for the minimal test-world candidate.")
    anvil_test_world_parser.add_argument(
        "--max-side",
        type=int,
        default=DEFAULT_SPIKE_MAX_SIDE,
        help="Chunk-aligned sampled side in blocks. Must stay within one region file.",
    )

    anvil_test_world_verify_parser = subparsers.add_parser(
        "anvil-test-world-verify",
        help="Update a test-world verification-report.json without hand-editing JSON.",
    )
    anvil_test_world_verify_parser.add_argument("report", type=Path, help="Path to verification-report.json.")
    anvil_test_world_verify_parser.add_argument(
        "--status",
        choices=("pending", "in_progress", "failed", "passed"),
        help="Top-level verification status.",
    )
    anvil_test_world_verify_parser.add_argument("--check", help="Check id inside verification-report.json.")
    anvil_test_world_verify_parser.add_argument(
        "--check-status",
        choices=("pending", "in_progress", "failed", "passed"),
        help="New status for the selected check.",
    )
    anvil_test_world_verify_parser.add_argument("--check-note", help="Note to append to the selected check.")
    anvil_test_world_verify_parser.add_argument("--report-note", help="Note to append to the report note list.")

    anvil_test_world_status_parser = subparsers.add_parser(
        "anvil-test-world-status",
        help="Read the current status of an existing test-world candidate without rebuilding it.",
    )
    anvil_test_world_status_parser.add_argument("output_dir", type=Path, help="Existing anvil-test-world output folder.")

    inventory_parser = subparsers.add_parser(
        "inventory",
        help="Scan a source or donor folder before importing it.",
    )
    inventory_parser.add_argument("path", type=Path, help="Folder to scan.")

    mask_parser = subparsers.add_parser(
        "mask-info",
        help="Inspect a PNG mask and report known TitanForge zone colors.",
    )
    mask_parser.add_argument("path", type=Path, help="PNG mask to inspect.")

    demo_mask_parser = subparsers.add_parser(
        "demo-mask",
        help="Create a small deterministic demo PNG mask for pipeline testing.",
    )
    demo_mask_parser.add_argument("output", type=Path, help="Demo mask PNG output path.")
    demo_mask_parser.add_argument("--width", type=int, default=128, help="Demo mask width.")
    demo_mask_parser.add_argument("--height", type=int, default=128, help="Demo mask height.")

    mask_preview_parser = subparsers.add_parser(
        "mask-preview",
        help="Render a normalized preview PNG from a TitanForge mask.",
    )
    mask_preview_parser.add_argument("input", type=Path, help="PNG mask to preview.")
    mask_preview_parser.add_argument("output", type=Path, help="Preview PNG output path.")

    mask_cleanup_parser = subparsers.add_parser(
        "mask-cleanup-preview",
        help="Render a cleanup preview that removes tiny water/land mask noise.",
    )
    mask_cleanup_parser.add_argument("input", type=Path, help="PNG mask to clean up.")
    mask_cleanup_parser.add_argument("output", type=Path, help="Cleanup preview PNG output path.")
    mask_cleanup_parser.add_argument("--threshold", type=int, default=5, help="Neighbor threshold from 1 to 8.")

    coastline_smoothing_parser = subparsers.add_parser(
        "coastline-smoothing-preview",
        help="Render a coastline smoothing preview that softens stair-step coast edges.",
    )
    coastline_smoothing_parser.add_argument("input", type=Path, help="PNG mask to smooth.")
    coastline_smoothing_parser.add_argument("output", type=Path, help="Coastline smoothing preview PNG output path.")

    mask_layout_parser = subparsers.add_parser(
        "mask-layout",
        help="Write a neutral layout JSON artifact from a TitanForge PNG mask.",
    )
    mask_layout_parser.add_argument("input", type=Path, help="PNG mask to convert.")
    mask_layout_parser.add_argument("output", type=Path, help="Layout JSON output path.")

    heightmap_preview_parser = subparsers.add_parser(
        "heightmap-preview",
        help="Render a first grayscale heightmap preview from a mask layout JSON.",
    )
    heightmap_preview_parser.add_argument("layout", type=Path, help="Mask layout JSON input path.")
    heightmap_preview_parser.add_argument("output", type=Path, help="Heightmap preview PNG output path.")
    heightmap_preview_parser.add_argument(
        "--mask",
        type=Path,
        help="Optional mask PNG override, useful for cleaned terrain inputs.",
    )

    terrain_color_preview_parser = subparsers.add_parser(
        "terrain-color-preview",
        help="Render a first color terrain preview from a mask layout JSON.",
    )
    terrain_color_preview_parser.add_argument("layout", type=Path, help="Mask layout JSON input path.")
    terrain_color_preview_parser.add_argument("output", type=Path, help="Terrain color preview PNG output path.")
    terrain_color_preview_parser.add_argument(
        "--mask",
        type=Path,
        help="Optional mask PNG override, useful for cleaned terrain inputs.",
    )

    terrain_grid_parser = subparsers.add_parser(
        "terrain-grid",
        help="Write a neutral terrain grid JSON artifact from a mask layout JSON.",
    )
    terrain_grid_parser.add_argument("layout", type=Path, help="Mask layout JSON input path.")
    terrain_grid_parser.add_argument("output", type=Path, help="Terrain grid JSON output path.")
    terrain_grid_parser.add_argument(
        "--mask",
        type=Path,
        help="Optional mask PNG override, useful for cleaned terrain inputs.",
    )

    validate_layout_parser = subparsers.add_parser(
        "validate-layout",
        help="Validate a mask layout JSON and optionally write a human-readable report.",
    )
    validate_layout_parser.add_argument("layout", type=Path, help="Mask layout JSON input path.")
    validate_layout_parser.add_argument("--report", type=Path, help="Optional report TXT output path.")

    build_location_parser = subparsers.add_parser(
        "build-location",
        help="Build a first TitanForge location pack folder from a mask or deterministic demo input.",
    )
    build_location_parser.add_argument("output_dir", type=Path, help="Location pack output folder.")
    source_group = build_location_parser.add_mutually_exclusive_group()
    source_group.add_argument("--input", type=Path, help="PNG mask to use as the location source.")
    source_group.add_argument("--demo", action="store_true", help="Generate a deterministic demo mask.")
    build_location_parser.add_argument("--width", type=int, default=128, help="Demo mask width.")
    build_location_parser.add_argument("--height", type=int, default=128, help="Demo mask height.")
    build_location_parser.add_argument(
        "--use-cleanup-for-heightmap",
        action="store_true",
        help="Render heightmap-preview.png from mask-cleanup-preview.png instead of mask.png.",
    )

    night_run_parser = subparsers.add_parser(
        "night-run",
        help="Run a resilient overnight batch of demo location-pack generations.",
    )
    night_run_parser.add_argument("output_dir", type=Path, help="Night run output folder.")
    night_run_parser.add_argument("--count", type=int, default=24, help="How many cases to attempt.")
    night_run_parser.add_argument("--width", type=int, default=128, help="Base demo mask width.")
    night_run_parser.add_argument("--height", type=int, default=128, help="Base demo mask height.")
    night_run_parser.add_argument("--size-step", type=int, default=32, help="Size increase for variant cases.")
    night_run_parser.add_argument("--max-minutes", type=float, help="Stop after this many minutes.")
    night_run_parser.add_argument(
        "--use-cleanup-for-heightmap",
        action="store_true",
        help="Use cleanup previews as heightmap source for every case.",
    )
    night_run_parser.add_argument(
        "--no-alternate-cleanup",
        action="store_true",
        help="Do not alternate cleanup/raw heightmap cases.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    try:
        return _dispatch(args, parser)
    except (
        AnvilRegionSpikeError,
        AnvilTestWorldVerificationError,
        PngError,
        ProjectTemplateError,
        FileExistsError,
        FileNotFoundError,
        NotADirectoryError,
        tomllib.TOMLDecodeError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _dispatch(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    if args.command == "info":
        print_info()
        return 0

    if args.command == "preset-catalog":
        if args.json:
            print(json.dumps(build_project_template_preset_catalog_payload(), indent=2))
        else:
            print(format_project_template_preset_catalog())
        return 0

    if args.command == "init-project":
        result = write_project_template(
            args.project_dir,
            args.name,
            args.width,
            args.length,
            args.preset,
            target_version=args.target_version,
        )
        print(format_project_template_result(result))
        return 0

    if args.command == "first-map":
        result = write_project_first_map(
            args.project_dir,
            args.name,
            args.width,
            args.length,
            args.preset,
            target_version=args.target_version,
            max_draft_side=args.max_draft_side,
            use_cleanup_for_heightmap=not args.no_cleanup_for_heightmap,
        )
        print(format_project_first_map_result(result))
        return 0

    if args.command == "first-map-status":
        result = summarize_project_first_map_status(args.project_dir)
        print(format_project_first_map_status_result(result))
        return 0

    if args.command == "plan":
        config = load_project_config(args.config)
        if args.review_page:
            review_page = write_project_review_page(config, args.review_page)
            print(f"Project review page: {review_page}")
        if args.world_plan:
            world_plan_path = write_world_plan(config, args.world_plan)
            print(f"World plan: {world_plan_path}")
            print(format_world_plan(build_world_plan(config), world_plan_path))
        print_project_plan(config)
        return 0

    if args.command == "project-draft":
        config = load_project_config(args.config)
        result = write_project_draft(config, args.output_dir, max_draft_side=args.max_draft_side)
        print(format_project_draft_result(result))
        return 0

    if args.command == "project-location":
        config = load_project_config(args.config)
        result = write_project_location(
            config,
            args.output_dir,
            max_draft_side=args.max_draft_side,
            use_cleanup_for_heightmap=args.use_cleanup_for_heightmap,
        )
        print(format_project_location_result(result))
        return 1 if result.location_result.errors else 0

    if args.command == "anvil-region-spike":
        if not 16 <= args.max_side <= 512:
            print(f"error: --max-side must be between 16 and 512, got {args.max_side}", file=sys.stderr)
            return 2
        if args.max_side % 16 != 0:
            print(f"error: --max-side must be divisible by 16, got {args.max_side}", file=sys.stderr)
            return 2
        config = load_project_config(args.config)
        result = write_anvil_region_spike(config, args.output_dir, max_side=args.max_side)
        print(format_anvil_region_spike_result(result))
        return 0

    if args.command == "anvil-save-shell":
        if not 16 <= args.max_side <= 512:
            print(f"error: --max-side must be between 16 and 512, got {args.max_side}", file=sys.stderr)
            return 2
        if args.max_side % 16 != 0:
            print(f"error: --max-side must be divisible by 16, got {args.max_side}", file=sys.stderr)
            return 2
        config = load_project_config(args.config)
        result = write_anvil_save_shell(config, args.output_dir, max_side=args.max_side)
        print(format_anvil_save_shell_result(result))
        return 0

    if args.command == "anvil-test-world":
        if not 16 <= args.max_side <= 512:
            print(f"error: --max-side must be between 16 and 512, got {args.max_side}", file=sys.stderr)
            return 2
        if args.max_side % 16 != 0:
            print(f"error: --max-side must be divisible by 16, got {args.max_side}", file=sys.stderr)
            return 2
        config = load_project_config(args.config)
        result = write_anvil_test_world(config, args.output_dir, max_side=args.max_side)
        print(format_anvil_test_world_result(result))
        return 0

    if args.command == "anvil-test-world-verify":
        result = update_test_world_verification_report(
            args.report,
            status=args.status,
            check_id=args.check,
            check_status=args.check_status,
            check_note=args.check_note,
            report_note=args.report_note,
        )
        print(format_test_world_verification_update_result(result))
        return 0

    if args.command == "anvil-test-world-status":
        result = summarize_test_world_status(args.output_dir)
        print(format_test_world_status_result(result))
        return 0

    if args.command == "inventory":
        report = scan_inventory(args.path)
        print(format_inventory_report(report))
        return 0

    if args.command == "mask-info":
        analysis = analyze_png_mask(args.path)
        print(format_mask_analysis(analysis))
        return 0

    if args.command == "demo-mask":
        result = generate_demo_mask(args.output, width=args.width, height=args.height)
        print(format_demo_mask_result(result))
        return 0

    if args.command == "mask-preview":
        result = render_mask_preview(args.input, args.output)
        print(format_mask_preview_result(result))
        return 0

    if args.command == "mask-cleanup-preview":
        if not 1 <= args.threshold <= 8:
            print(f"error: --threshold must be between 1 and 8, got {args.threshold}", file=sys.stderr)
            return 2
        result = render_mask_cleanup_preview(args.input, args.output, threshold=args.threshold)
        print(format_mask_cleanup_result(result))
        return 0

    if args.command == "coastline-smoothing-preview":
        result = render_coastline_smoothing_preview(args.input, args.output)
        print(format_coastline_smoothing_result(result))
        return 0

    if args.command == "mask-layout":
        result = write_mask_layout(args.input, args.output)
        print(format_mask_layout_result(result))
        return 0

    if args.command == "heightmap-preview":
        result = render_heightmap_preview(args.layout, args.output, mask_override_path=args.mask)
        print(format_heightmap_preview_result(result))
        return 0

    if args.command == "terrain-color-preview":
        result = render_terrain_color_preview(args.layout, args.output, mask_override_path=args.mask)
        print(format_terrain_color_preview_result(result))
        return 0

    if args.command == "terrain-grid":
        result = write_terrain_grid(args.layout, args.output, mask_override_path=args.mask)
        print(format_terrain_grid_result(result))
        return 0

    if args.command == "validate-layout":
        if args.report:
            result = write_layout_validation_report(args.layout, args.report)
        else:
            result = validate_layout_file(args.layout)
        print(format_layout_validation_report(result))
        return 1 if result.has_errors else 0

    if args.command == "build-location":
        result = build_location_pack(
            args.output_dir,
            input_mask=args.input,
            demo=args.demo,
            width=args.width,
            height=args.height,
            use_cleanup_for_heightmap=args.use_cleanup_for_heightmap,
        )
        print(format_location_build_result(result))
        return 1 if result.errors else 0

    if args.command == "night-run":
        result = run_night_run(
            args.output_dir,
            count=args.count,
            width=args.width,
            height=args.height,
            size_step=args.size_step,
            max_minutes=args.max_minutes,
            use_cleanup_for_heightmap=args.use_cleanup_for_heightmap,
            alternate_cleanup=not args.no_alternate_cleanup,
        )
        print(format_night_run_result(result))
        return 1 if result.failed_cases else 0

    parser.print_help()
    return 0


def print_info() -> None:
    print("TitanForge Engine")
    print(f"Primary target: {PRIMARY_TARGET.minecraft_version}")
    print("Active targets:")
    for target in ACTIVE_TARGETS:
        print(f"- {target.minecraft_version}: {target.role}")
    print("Parking lot:")
    for target in PARKING_LOT_TARGETS:
        print(f"- {target.minecraft_version}: {target.role}")


def print_project_plan(config: ProjectConfig) -> None:
    print(f"Project: {config.name}")
    print(f"Target: {config.target_version}")
    print(f"World size: {config.width} x {config.length}")
    print(f"Premise: {config.premise}")
    print(f"Player feeling: {config.player_experience}")
    if config.regions:
        print("Regions:")
        for region in config.regions:
            print(
                f"- {region.title} [{region.kind}] | role: {region.story_role} | "
                f"mood: {region.mood} | coverage: {region.coverage_hint}"
            )
    print("Pipeline:")
    for stage in config.pipeline:
        print(f"- {stage}")
