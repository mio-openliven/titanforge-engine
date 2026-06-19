from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from titanforge.masks.classifier import MaskColorClassifier
from titanforge.masks.palette import DEFAULT_ZONE_PALETTE, ZoneDefinition
from titanforge.masks.png import PngImage, read_png, write_rgba_png


WATERLIKE_ZONES = {"water"}
LANDLIKE_ZONES = {"land", "beach", "port", "road", "city", "forest", "mountain"}


@dataclass(frozen=True)
class CoastlineSmoothingResult:
    input_path: Path
    output_path: Path
    width: int
    height: int
    changed_pixels: int
    unknown_pixels: int


def render_coastline_smoothing_preview(
    input_path: Path,
    output_path: Path,
    *,
    palette: tuple[ZoneDefinition, ...] = DEFAULT_ZONE_PALETTE,
    image: PngImage | None = None,
) -> CoastlineSmoothingResult:
    if image is None:
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
            replacement = _replacement_zone(zone_grid, x, y)
            if zone is not None and replacement is not None and replacement.zone_id != zone.zone_id:
                changed_pixels += 1
                output_row.append(replacement.color.rgba)
            else:
                output_row.append(rgba)
        output_rows.append(tuple(output_row))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(output_path, image.width, image.height, tuple(output_rows))

    return CoastlineSmoothingResult(
        input_path=input_path,
        output_path=output_path,
        width=image.width,
        height=image.height,
        changed_pixels=changed_pixels,
        unknown_pixels=unknown_pixels,
    )


def format_coastline_smoothing_result(result: CoastlineSmoothingResult) -> str:
    return "\n".join(
        [
            f"Coastline smoothing preview: {result.output_path}",
            f"Input: {result.input_path}",
            f"Size: {result.width} x {result.height}",
            f"Changed pixels: {result.changed_pixels}",
            f"Unknown pixels: {result.unknown_pixels}",
        ]
    )


def _replacement_zone(grid: list[list[ZoneDefinition | None]], x: int, y: int) -> ZoneDefinition | None:
    current = grid[y][x]
    if current is None:
        return None

    current_family = _family(current.zone_id)
    if current_family is None:
        return None

    orthogonal_same = 0
    orthogonal_other = 0
    same_counts: dict[str, int] = {}
    other_counts: dict[str, int] = {}
    same_candidates: dict[str, ZoneDefinition] = {}
    other_candidates: dict[str, ZoneDefinition] = {}
    diagonal_other = 0

    for offset_x, offset_y, neighbor in _neighbors(grid, x, y):
        family = _family(neighbor.zone_id)
        if family is None:
            continue

        is_orthogonal = offset_x == 0 or offset_y == 0
        if family == current_family:
            same_counts[neighbor.zone_id] = same_counts.get(neighbor.zone_id, 0) + 1
            same_candidates[neighbor.zone_id] = neighbor
            if is_orthogonal:
                orthogonal_same += 1
        else:
            other_counts[neighbor.zone_id] = other_counts.get(neighbor.zone_id, 0) + 1
            other_candidates[neighbor.zone_id] = neighbor
            if is_orthogonal:
                orthogonal_other += 1
            else:
                diagonal_other += 1

    if orthogonal_other == 0 or orthogonal_same == 0:
        return None

    if orthogonal_other >= 2 and (orthogonal_other + diagonal_other) >= 5:
        zone_id = max(other_counts.items(), key=lambda item: item[1])[0]
        return other_candidates[zone_id]

    return None


def _neighbors(
    grid: list[list[ZoneDefinition | None]],
    x: int,
    y: int,
) -> tuple[tuple[int, int, ZoneDefinition], ...]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    neighbors: list[tuple[int, int, ZoneDefinition]] = []

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
                neighbors.append((offset_x, offset_y, zone))

    return tuple(neighbors)


def _family(zone_id: str) -> str | None:
    if zone_id in WATERLIKE_ZONES:
        return "water"
    if zone_id in LANDLIKE_ZONES:
        return "land"
    return None
