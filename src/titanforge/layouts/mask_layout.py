from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from titanforge.masks.analyzer import MaskAnalysis, analyze_png_mask


LAYOUT_SCHEMA = "titanforge.mask-layout"
LAYOUT_VERSION = 1


@dataclass(frozen=True)
class MaskLayoutResult:
    input_path: Path
    output_path: Path
    width: int
    height: int
    zone_count: int
    unknown_color_count: int


def build_mask_layout(input_path: Path) -> dict[str, Any]:
    analysis = analyze_png_mask(input_path)
    return _layout_from_analysis(analysis)


def write_mask_layout(input_path: Path, output_path: Path) -> MaskLayoutResult:
    layout = build_mask_layout(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(layout, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    world = layout["world"]
    return MaskLayoutResult(
        input_path=input_path,
        output_path=output_path,
        width=int(world["width"]),
        height=int(world["length"]),
        zone_count=len(layout["zones"]),
        unknown_color_count=len(layout["unknownColors"]),
    )


def format_mask_layout_result(result: MaskLayoutResult) -> str:
    return "\n".join(
        [
            f"Mask layout: {result.output_path}",
            f"Input: {result.input_path}",
            f"Size: {result.width} x {result.height}",
            f"Zones: {result.zone_count}",
            f"Unknown colors: {result.unknown_color_count}",
        ]
    )


def _layout_from_analysis(analysis: MaskAnalysis) -> dict[str, Any]:
    return {
        "schema": LAYOUT_SCHEMA,
        "version": LAYOUT_VERSION,
        "source": {
            "type": "png-mask",
            "path": str(analysis.path),
        },
        "world": {
            "width": analysis.width,
            "length": analysis.height,
        },
        "coverage": {
            "totalPixels": analysis.total_pixels,
            "knownPixels": analysis.known_pixels,
            "unknownPixels": analysis.unknown_pixels,
        },
        "zones": [
            {
                "id": stat.zone.zone_id,
                "label": stat.zone.label,
                "color": stat.zone.color.hex_rgb,
                "pixels": stat.pixels,
                "percent": round(stat.percent, 4),
            }
            for stat in analysis.zone_stats
        ],
        "unknownColors": [
            {
                "color": stat.color.hex_rgb,
                "alpha": stat.color.alpha,
                "pixels": stat.pixels,
                "percent": round(stat.percent, 4),
            }
            for stat in analysis.unknown_color_stats
        ],
    }
