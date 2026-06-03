from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LayoutIssue:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class LayoutValidationResult:
    layout_path: Path
    schema: str
    version: int
    width: int
    length: int
    zones: tuple[str, ...]
    total_pixels: int
    known_pixels: int
    unknown_pixels: int
    issues: tuple[LayoutIssue, ...]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")


def validate_layout_file(layout_path: Path) -> LayoutValidationResult:
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    return validate_layout(layout_path, layout)


def validate_layout(layout_path: Path, layout: dict[str, Any]) -> LayoutValidationResult:
    world = layout.get("world", {})
    coverage = layout.get("coverage", {})
    zones_data = layout.get("zones", [])

    schema = str(layout.get("schema", ""))
    version = int(layout.get("version", 0))
    width = int(world.get("width", 0))
    length = int(world.get("length", 0))
    total_pixels = int(coverage.get("totalPixels", 0))
    known_pixels = int(coverage.get("knownPixels", 0))
    unknown_pixels = int(coverage.get("unknownPixels", 0))
    zones = tuple(str(zone.get("id", "")) for zone in zones_data if zone.get("id"))

    issues: list[LayoutIssue] = []

    if schema != "titanforge.mask-layout":
        issues.append(LayoutIssue("error", "layout.schema", "Unsupported or missing layout schema."))
    if version != 1:
        issues.append(LayoutIssue("error", "layout.version", "Unsupported or missing layout version."))
    if width <= 0 or length <= 0:
        issues.append(LayoutIssue("error", "world.size", "World width and length must be positive."))
    if total_pixels != width * length:
        issues.append(LayoutIssue("error", "coverage.total", "Coverage total does not match world size."))
    if known_pixels + unknown_pixels != total_pixels:
        issues.append(LayoutIssue("error", "coverage.sum", "Known and unknown pixel counts do not match total."))
    if not zones:
        issues.append(LayoutIssue("error", "zones.empty", "Layout contains no known zones."))
    if unknown_pixels > 0:
        issues.append(LayoutIssue("warning", "mask.unknown-colors", f"Mask has {unknown_pixels} unknown pixels."))
    if "water" not in zones:
        issues.append(LayoutIssue("warning", "zones.no-water", "Layout has no water zone."))
    if "land" not in zones:
        issues.append(LayoutIssue("warning", "zones.no-land", "Layout has no land zone."))
    if _coverage_percent(layout, "water") > 95.0:
        issues.append(LayoutIssue("warning", "zones.too-much-water", "Water covers more than 95% of the mask."))
    if _coverage_percent(layout, "land") > 95.0:
        issues.append(LayoutIssue("warning", "zones.too-much-land", "Land covers more than 95% of the mask."))

    return LayoutValidationResult(
        layout_path=layout_path,
        schema=schema,
        version=version,
        width=width,
        length=length,
        zones=zones,
        total_pixels=total_pixels,
        known_pixels=known_pixels,
        unknown_pixels=unknown_pixels,
        issues=tuple(issues),
    )


def write_layout_validation_report(layout_path: Path, report_path: Path) -> LayoutValidationResult:
    result = validate_layout_file(layout_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(format_layout_validation_report(result) + "\n", encoding="utf-8")
    return result


def format_layout_validation_report(result: LayoutValidationResult) -> str:
    lines = [
        "TitanForge Layout Report",
        f"Layout: {result.layout_path}",
        f"Schema: {result.schema}",
        f"Version: {result.version}",
        f"World: {result.width} x {result.length}",
        f"Coverage: {result.known_pixels}/{result.total_pixels} known, {result.unknown_pixels} unknown",
        f"Zones: {', '.join(result.zones) if result.zones else '<none>'}",
        f"Status: {'ERROR' if result.has_errors else 'OK'}",
        f"Errors: {result.error_count}",
        f"Warnings: {result.warning_count}",
    ]

    if result.issues:
        lines.append("")
        lines.append("Issues:")
        for issue in result.issues:
            lines.append(f"- [{issue.severity.upper()}] {issue.code}: {issue.message}")

    return "\n".join(lines)


def _coverage_percent(layout: dict[str, Any], zone_id: str) -> float:
    for zone in layout.get("zones", []):
        if zone.get("id") == zone_id:
            return float(zone.get("percent", 0.0))
    return 0.0
