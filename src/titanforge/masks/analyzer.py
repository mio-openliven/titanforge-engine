from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from titanforge.masks.classifier import MaskColorClassifier
from titanforge.masks.palette import DEFAULT_ZONE_PALETTE, MaskColor, ZoneDefinition
from titanforge.masks.png import read_png


@dataclass(frozen=True)
class ZoneStats:
    zone: ZoneDefinition
    pixels: int
    percent: float


@dataclass(frozen=True)
class UnknownColorStats:
    color: MaskColor
    pixels: int
    percent: float


@dataclass(frozen=True)
class MaskAnalysis:
    path: Path
    width: int
    height: int
    total_pixels: int
    zone_stats: tuple[ZoneStats, ...]
    unknown_color_stats: tuple[UnknownColorStats, ...]

    @property
    def known_pixels(self) -> int:
        return sum(stat.pixels for stat in self.zone_stats)

    @property
    def unknown_pixels(self) -> int:
        return sum(stat.pixels for stat in self.unknown_color_stats)


def analyze_png_mask(
    path: Path,
    palette: tuple[ZoneDefinition, ...] = DEFAULT_ZONE_PALETTE,
) -> MaskAnalysis:
    image = read_png(path)
    classifier = MaskColorClassifier(palette)

    zone_counts: Counter[str] = Counter()
    unknown_counts: Counter[tuple[int, int, int, int]] = Counter()
    zones_by_id = {zone.zone_id: zone for zone in palette}

    for row in image.pixels:
        for rgba in row:
            zone = classifier.classify(rgba)
            if zone is None:
                unknown_counts[rgba] += 1
            else:
                zone_counts[zone.zone_id] += 1

    total = image.width * image.height
    zone_stats = tuple(
        ZoneStats(
            zone=zones_by_id[zone_id],
            pixels=count,
            percent=(count / total) * 100 if total else 0.0,
        )
        for zone_id, count in zone_counts.most_common()
    )
    unknown_stats = tuple(
        UnknownColorStats(
            color=MaskColor.from_rgba(rgba),
            pixels=count,
            percent=(count / total) * 100 if total else 0.0,
        )
        for rgba, count in unknown_counts.most_common(20)
    )

    return MaskAnalysis(
        path=path,
        width=image.width,
        height=image.height,
        total_pixels=total,
        zone_stats=zone_stats,
        unknown_color_stats=unknown_stats,
    )


def format_mask_analysis(analysis: MaskAnalysis) -> str:
    lines = [
        f"Mask: {analysis.path}",
        f"Size: {analysis.width} x {analysis.height}",
        f"Pixels: {analysis.total_pixels}",
        f"Known pixels: {analysis.known_pixels}",
        f"Unknown pixels: {analysis.unknown_pixels}",
        "",
        "Zones:",
    ]

    if analysis.zone_stats:
        for stat in analysis.zone_stats:
            lines.append(
                f"- {stat.zone.zone_id} {stat.zone.color.hex_rgb}: {stat.pixels} ({stat.percent:.1f}%)"
            )
    else:
        lines.append("- <none>")

    if analysis.unknown_color_stats:
        lines.append("")
        lines.append("Unknown colors:")
        for stat in analysis.unknown_color_stats:
            alpha = f" alpha={stat.color.alpha}" if stat.color.alpha != 255 else ""
            lines.append(f"- {stat.color.hex_rgb}{alpha}: {stat.pixels} ({stat.percent:.1f}%)")

    return "\n".join(lines)
