from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from titanforge.masks.palette import DEFAULT_ZONE_PALETTE, MaskColor, ZoneDefinition
from titanforge.masks.png import read_png, write_rgba_png


UNKNOWN_COLOR = MaskColor(255, 0, 255)


@dataclass(frozen=True)
class MaskPreviewResult:
    input_path: Path
    output_path: Path
    width: int
    height: int
    known_pixels: int
    unknown_pixels: int


def render_mask_preview(
    input_path: Path,
    output_path: Path,
    palette: tuple[ZoneDefinition, ...] = DEFAULT_ZONE_PALETTE,
) -> MaskPreviewResult:
    image = read_png(input_path)
    zone_by_rgba = {zone.color.rgba: zone for zone in palette}
    zone_by_rgb = {zone.color.rgb: zone for zone in palette if zone.color.alpha == 255}
    void_zone = next((zone for zone in palette if zone.zone_id == "void"), None)

    known_pixels = 0
    unknown_pixels = 0
    output_rows: list[tuple[tuple[int, int, int, int], ...]] = []

    for row in image.pixels:
        output_row: list[tuple[int, int, int, int]] = []
        for rgba in row:
            zone = zone_by_rgba.get(rgba)
            if zone is None and rgba[3] == 0:
                zone = void_zone
            if zone is None and rgba[3] == 255:
                zone = zone_by_rgb.get(rgba[:3])

            if zone is None:
                unknown_pixels += 1
                output_row.append(UNKNOWN_COLOR.rgba)
            else:
                known_pixels += 1
                output_row.append(zone.color.rgba)

        output_rows.append(tuple(output_row))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(output_path, image.width, image.height, tuple(output_rows))

    return MaskPreviewResult(
        input_path=input_path,
        output_path=output_path,
        width=image.width,
        height=image.height,
        known_pixels=known_pixels,
        unknown_pixels=unknown_pixels,
    )


def format_mask_preview_result(result: MaskPreviewResult) -> str:
    return "\n".join(
        [
            f"Mask preview: {result.output_path}",
            f"Input: {result.input_path}",
            f"Size: {result.width} x {result.height}",
            f"Known pixels: {result.known_pixels}",
            f"Unknown pixels: {result.unknown_pixels}",
        ]
    )
