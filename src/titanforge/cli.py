from __future__ import annotations

import argparse
from pathlib import Path

from titanforge import __version__
from titanforge.core.project import ProjectConfig, load_project_config
from titanforge.inventory.scanner import format_inventory_report, scan_inventory
from titanforge.layouts.mask_layout import format_mask_layout_result, write_mask_layout
from titanforge.masks.analyzer import analyze_png_mask, format_mask_analysis
from titanforge.preview.mask_preview import format_mask_preview_result, render_mask_preview
from titanforge.terrain.heightmap_preview import format_heightmap_preview_result, render_heightmap_preview
from titanforge.versions.targets import ACTIVE_TARGETS, PARKING_LOT_TARGETS, PRIMARY_TARGET


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="titanforge",
        description="TitanForge Engine command-line tools.",
    )
    parser.add_argument("--version", action="store_true", help="Show TitanForge Engine version.")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("info", help="Show current engine strategy and version targets.")

    plan_parser = subparsers.add_parser("plan", help="Read and summarize a TitanForge project config.")
    plan_parser.add_argument("config", type=Path, help="Path to titanforge.toml.")

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

    mask_preview_parser = subparsers.add_parser(
        "mask-preview",
        help="Render a normalized preview PNG from a TitanForge mask.",
    )
    mask_preview_parser.add_argument("input", type=Path, help="PNG mask to preview.")
    mask_preview_parser.add_argument("output", type=Path, help="Preview PNG output path.")

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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command == "info":
        print_info()
        return 0

    if args.command == "plan":
        config = load_project_config(args.config)
        print_project_plan(config)
        return 0

    if args.command == "inventory":
        report = scan_inventory(args.path)
        print(format_inventory_report(report))
        return 0

    if args.command == "mask-info":
        analysis = analyze_png_mask(args.path)
        print(format_mask_analysis(analysis))
        return 0

    if args.command == "mask-preview":
        result = render_mask_preview(args.input, args.output)
        print(format_mask_preview_result(result))
        return 0

    if args.command == "mask-layout":
        result = write_mask_layout(args.input, args.output)
        print(format_mask_layout_result(result))
        return 0

    if args.command == "heightmap-preview":
        result = render_heightmap_preview(args.layout, args.output)
        print(format_heightmap_preview_result(result))
        return 0

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
    print("Pipeline:")
    for stage in config.pipeline:
        print(f"- {stage}")
