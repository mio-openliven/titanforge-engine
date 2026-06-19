from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from titanforge.masks.classifier import MaskColorClassifier
from titanforge.masks.palette import DEFAULT_ZONE_PALETTE, ZoneDefinition
from titanforge.masks.png import PngImage, read_png
from titanforge.terrain.heightmap_preview import ZONE_HEIGHTS


TERRAIN_GRID_SCHEMA = "titanforge.terrain-grid"
TERRAIN_GRID_VERSION = 1


@dataclass(frozen=True)
class TerrainProfile:
    surface: str
    walkable: bool
    buildable: bool
    moisture: str


@dataclass(frozen=True)
class TerrainCell:
    x: int
    z: int
    zone_id: str
    elevation: int | None
    surface: str
    walkable: bool
    buildable: bool
    moisture: str


@dataclass(frozen=True)
class TerrainGrid:
    layout_path: Path
    mask_path: Path
    width: int
    length: int
    cells: tuple[TerrainCell, ...]
    unknown_cells: int


@dataclass(frozen=True)
class TerrainGridResult:
    layout_path: Path
    mask_path: Path
    output_path: Path
    width: int
    length: int
    cell_count: int
    unknown_cells: int


ZONE_TERRAIN_PROFILES = {
    "water": TerrainProfile(surface="water", walkable=False, buildable=False, moisture="wet"),
    "beach": TerrainProfile(surface="sand", walkable=True, buildable=True, moisture="coastal"),
    "port": TerrainProfile(surface="harbor", walkable=True, buildable=True, moisture="coastal"),
    "road": TerrainProfile(surface="road", walkable=True, buildable=False, moisture="dry"),
    "city": TerrainProfile(surface="urban", walkable=True, buildable=True, moisture="dry"),
    "forest": TerrainProfile(surface="forest-floor", walkable=True, buildable=False, moisture="humid"),
    "land": TerrainProfile(surface="grassland", walkable=True, buildable=True, moisture="normal"),
    "mountain": TerrainProfile(surface="rock", walkable=False, buildable=False, moisture="dry"),
    "void": TerrainProfile(surface="void", walkable=False, buildable=False, moisture="none"),
}

UNKNOWN_TERRAIN_PROFILE = TerrainProfile(
    surface="unknown",
    walkable=False,
    buildable=False,
    moisture="unknown",
)


def build_terrain_grid(
    layout_path: Path,
    mask_override_path: Path | None = None,
    palette: tuple[ZoneDefinition, ...] = DEFAULT_ZONE_PALETTE,
    *,
    mask_image: PngImage | None = None,
) -> TerrainGrid:
    layout = _load_layout(layout_path)
    mask_path = mask_override_path or _resolve_mask_path(layout_path, layout)
    image = mask_image if mask_image is not None else read_png(mask_path)
    classifier = MaskColorClassifier(palette)

    cells: list[TerrainCell] = []
    unknown_cells = 0

    for z, row in enumerate(image.pixels):
        for x, rgba in enumerate(row):
            zone = classifier.classify(rgba)
            if zone is None:
                unknown_cells += 1
                cells.append(
                    TerrainCell(
                        x=x,
                        z=z,
                        zone_id="unknown",
                        elevation=None,
                        surface=UNKNOWN_TERRAIN_PROFILE.surface,
                        walkable=UNKNOWN_TERRAIN_PROFILE.walkable,
                        buildable=UNKNOWN_TERRAIN_PROFILE.buildable,
                        moisture=UNKNOWN_TERRAIN_PROFILE.moisture,
                    )
                )
                continue

            profile = ZONE_TERRAIN_PROFILES.get(zone.zone_id, UNKNOWN_TERRAIN_PROFILE)
            cells.append(
                TerrainCell(
                    x=x,
                    z=z,
                    zone_id=zone.zone_id,
                    elevation=ZONE_HEIGHTS.get(zone.zone_id),
                    surface=profile.surface,
                    walkable=profile.walkable,
                    buildable=profile.buildable,
                    moisture=profile.moisture,
                )
            )

    return TerrainGrid(
        layout_path=layout_path,
        mask_path=mask_path,
        width=image.width,
        length=image.height,
        cells=tuple(cells),
        unknown_cells=unknown_cells,
    )


def write_terrain_grid(
    layout_path: Path,
    output_path: Path,
    mask_override_path: Path | None = None,
    palette: tuple[ZoneDefinition, ...] = DEFAULT_ZONE_PALETTE,
    *,
    mask_image: PngImage | None = None,
) -> TerrainGridResult:
    grid = build_terrain_grid(
        layout_path,
        mask_override_path=mask_override_path,
        palette=palette,
        mask_image=mask_image,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(terrain_grid_to_dict(grid), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return TerrainGridResult(
        layout_path=layout_path,
        mask_path=grid.mask_path,
        output_path=output_path,
        width=grid.width,
        length=grid.length,
        cell_count=len(grid.cells),
        unknown_cells=grid.unknown_cells,
    )


def terrain_grid_to_dict(grid: TerrainGrid) -> dict[str, Any]:
    return {
        "schema": TERRAIN_GRID_SCHEMA,
        "version": TERRAIN_GRID_VERSION,
        "source": {
            "layout": str(grid.layout_path),
            "mask": str(grid.mask_path),
        },
        "world": {
            "width": grid.width,
            "length": grid.length,
        },
        "summary": {
            "cells": len(grid.cells),
            "unknownCells": grid.unknown_cells,
        },
        "cells": [
            {
                "x": cell.x,
                "z": cell.z,
                "zone": cell.zone_id,
                "elevation": cell.elevation,
                "surface": cell.surface,
                "walkable": cell.walkable,
                "buildable": cell.buildable,
                "moisture": cell.moisture,
            }
            for cell in grid.cells
        ],
    }


def format_terrain_grid_result(result: TerrainGridResult) -> str:
    return "\n".join(
        [
            f"Terrain grid: {result.output_path}",
            f"Layout: {result.layout_path}",
            f"Mask: {result.mask_path}",
            f"Size: {result.width} x {result.length}",
            f"Cells: {result.cell_count}",
            f"Unknown cells: {result.unknown_cells}",
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
