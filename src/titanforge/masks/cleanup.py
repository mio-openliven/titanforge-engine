from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from titanforge.masks.classifier import MaskColorClassifier
from titanforge.masks.palette import DEFAULT_ZONE_PALETTE, ZoneDefinition
from titanforge.masks.png import read_png, write_rgba_png

WATERLIKE_ZONES = {"water"}
LANDLIKE_ZONES = {"land", "beach", "port", "road", "city", "forest", "mountain"}


@dataclass(frozen=True)
class MaskCleanupResult:
    input_path: Path
    output_path: Path
    width: int
    height: int
    changed_pixels: int
    unknown_pixels: int


def render_mask_cleanup_preview(
    input_path: Path,
    output_path: Path,
    *,
    threshold: int = 5,
    palette: tuple[ZoneDefinition, ...] = DEFAULT_ZONE_PALETTE,
) -> MaskCleanupResult:
    if threshold < 1 or threshold > 8:
        raise ValueError("Cleanup threshold must be between 1 and 8.")

    image = read_png(input_path)
    classifier = MaskColorClassifier(palette)
    zone_grid: list[list[ZoneDefinition | None]] = []
    unknown_pixels = 0

    for row in image.pixels:
        zone_row: list[ZoneDefinition | None] = []
        for rgba in row:
            zone = classifier.classify(rgba)
            if zone is None:
                unknown_pixels += 1
            zone_row.append(zone)
        zone_grid.append(zone_row)

    output_rows: list[tuple[tuple[int, int, int, int], ...]] = []
    changed_pixels = 0

    for y, row in enumerate(image.pixels):
        output_row: list[tuple[int, int, int, int]] = []
        for x, rgba in enumerate(row):
            zone = zone_grid[y][x]
            replacement = _replacement_zone(zone_grid, x, y, threshold)
            if zone is not None and replacement is not None and replacement.zone_id != zone.zone_id:
                changed_pixels += 1
                output_row.append(replacement.color.rgba)
            else:
                output_row.append(rgba)
        output_rows.append(tuple(output_row))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(output_path, image.width, image.height, tuple(output_rows))

    return MaskCleanupResult(
        input_path=input_path,
        output_path=output_path,
        width=image.width,
        height=image.height,
        changed_pixels=changed_pixels,
        unknown_pixels=unknown_pixels,
    )


def format_mask_cleanup_result(result: MaskCleanupResult) -> str:
    return "\n".join(
        [
            f"Mask cleanup preview: {result.output_path}",
            f"Input: {result.input_path}",
            f"Size: {result.width} x {result.height}",
            f"Changed pixels: {result.changed_pixels}",
            f"Unknown pixels: {result.unknown_pixels}",
        ]
    )


def _replacement_zone(
    grid: list[list[ZoneDefinition | None]],
    x: int,
    y: int,
    threshold: int,
) -> ZoneDefinition | None:
    current = grid[y][x]
    if current is None:
        return None

    current_family = _family(current.zone_id)
    if current_family is None:
        return None

    counts: dict[str, int] = {}
    candidates: dict[str, ZoneDefinition] = {}
    for neighbor in _neighbors(grid, x, y):
        family = _family(neighbor.zone_id)
        if family is None or family == current_family:
            continue
        counts[neighbor.zone_id] = counts.get(neighbor.zone_id, 0) + 1
        candidates[neighbor.zone_id] = neighbor

    if not counts:
        return None

    zone_id, count = max(counts.items(), key=lambda item: item[1])
    if count >= threshold:
        return candidates[zone_id]

    return None


def _neighbors(grid: list[list[ZoneDefinition | None]], x: int, y: int) -> tuple[ZoneDefinition, ...]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    neighbors: list[ZoneDefinition] = []

    for offset_y in (-1, 0, 1):
        for offset_x in (-1, 0, 1):
            if offset_x == 0 and offset_y == 0:
                continue
            nx = x + offset_x
            ny = y + offset_y
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            zone = grid[ny][nx]
            if zone is not None:
                neighbors.append(zone)

    return tuple(neighbors)


def _family(zone_id: str) -> str | None:
    if zone_id in WATERLIKE_ZONES:
        return "water"
    if zone_id in LANDLIKE_ZONES:
        return "land"
    return None
