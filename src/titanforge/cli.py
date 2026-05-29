from __future__ import annotations

import argparse
from pathlib import Path

from titanforge import __version__
from titanforge.core.project import ProjectConfig, load_project_config
from titanforge.inventory.scanner import format_inventory_report, scan_inventory
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
