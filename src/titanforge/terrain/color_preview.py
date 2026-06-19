from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from titanforge.masks.classifier import MaskColorClassifier
from titanforge.masks.palette import DEFAULT_ZONE_PALETTE, ZoneDefinition
from titanforge.masks.png import PngImage, read_png, write_rgba_png


UNKNOWN_TERRAIN_COLOR = (255, 0, 255, 255)

ZONE_TERRAIN_COLORS = {
    "void": (0, 0, 0, 0),
    "water": (46, 102, 173, 255),
    "beach": (212, 196, 144, 255),
    "port": (180, 132, 72, 255),
    "road": (104, 100, 94, 255),
    "city": (176, 126, 102, 255),
    "forest": (56, 101, 58, 255),
    "land": (126, 172, 96, 255),
    "mountain": (146, 146, 154, 255),
}


@dataclass(frozen=True)
class TerrainColorPreviewResult:
    layout_path: Path
    mask_path: Path
    output_path: Path
    width: int
    height: int
    known_pixels: int
    unknown_pixels: int


def render_terrain_color_preview(
    layout_path: Path,
    output_path: Path,
    mask_override_path: Path | None = None,
    palette: tuple[ZoneDefinition, ...] = DEFAULT_ZONE_PALETTE,
    *,
    mask_image: PngImage | None = None,
) -> TerrainColorPreviewResult:
    layout = _load_layout(layout_path)
    mask_path = mask_override_path or _resolve_mask_path(layout_path, layout)
    image = mask_image if mask_image is not None else read_png(mask_path)
    classifier = MaskColorClassifier(palette)

    known_pixels = 0
    unknown_pixels = 0
    output_rows: list[tuple[tuple[int, int, int, int], ...]] = []

    for row in image.pixels:
        output_row: list[tuple[int, int, int, int]] = []
        for rgba in row:
            zone = classifier.classify(rgba)
            if zone is None:
                unknown_pixels += 1
                output_row.append(UNKNOWN_TERRAIN_COLOR)
                continue

            known_pixels += 1
            output_row.append(ZONE_TERRAIN_COLORS.get(zone.zone_id, UNKNOWN_TERRAIN_COLOR))

        output_rows.append(tuple(output_row))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(output_path, image.width, image.height, tuple(output_rows))

    return TerrainColorPreviewResult(
        layout_path=layout_path,
        mask_path=mask_path,
        output_path=output_path,
        width=image.width,
        height=image.height,
        known_pixels=known_pixels,
        unknown_pixels=unknown_pixels,
    )


def format_terrain_color_preview_result(result: TerrainColorPreviewResult) -> str:
    return "\n".join(
        [
            f"Terrain color preview: {result.output_path}",
            f"Layout: {result.layout_path}",
            f"Mask: {result.mask_path}",
            f"Size: {result.width} x {result.height}",
            f"Known pixels: {result.known_pixels}",
            f"Unknown pixels: {result.unknown_pixels}",
        ]
    )


def _load_layout(layout_path: Path) -> dict[str, Any]:
    return json.loads(layout_path.read_text(encoding="utf-8"))


def _resolve_mask_path(layout_path: Path, layout: dict[str, Any]) -> Path:
    source_path = Path(str(layout.get("source", {}).get("path", "")))
    if source_path.is_absolute():
        return source_path

    layout_relative = layout_path.parent / source_path
    if layout_relative.exists():
        return layout_relative

    cwd_relative = Path.cwd() / source_path
    if cwd_relative.exists():
        return cwd_relative

    return layout_relative
