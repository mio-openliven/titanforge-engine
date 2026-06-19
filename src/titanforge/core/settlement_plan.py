from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from titanforge.core.placement_plan import PlacementPlan, PlacementSite
from titanforge.core.road_plan import RoadPlan
from titanforge.masks.png import write_rgba_png


SETTLEMENT_PLAN_SCHEMA = "titanforge.settlement-plan"
SETTLEMENT_PLAN_VERSION = 1
SETTLEMENT_PREVIEW_BACKGROUND = (236, 230, 219, 255)
SETTLEMENT_PREVIEW_BLOCKOUT = (161, 112, 86, 255)
SETTLEMENT_PREVIEW_GATE = (115, 79, 55, 255)
SETTLEMENT_PREVIEW_HARBOR = (88, 118, 135, 255)


@dataclass(frozen=True)
class SettlementBlockout:
    id: str
    kind: str
    region_title: str
    site_id: str
    site_kind: str
    x: int
    z: int
    width: int
    length: int
    access_roads: tuple[str, ...]


@dataclass(frozen=True)
class SettlementPlan:
    width: int
    length: int
    blockouts: tuple[SettlementBlockout, ...]


def build_settlement_plan(placement_plan: PlacementPlan, road_plan: RoadPlan) -> SettlementPlan:
    roads_by_site = _roads_by_site(road_plan)
    blockouts: list[SettlementBlockout] = []

    for site in placement_plan.sites:
        blockout_kind = _blockout_kind(site)
        if blockout_kind is None:
            continue

        size_width, size_length = _blockout_size(blockout_kind)
        origin_x = max(0, site.x - size_width // 2)
        origin_z = max(0, site.z - size_length // 2)
        width = min(size_width, max(1, placement_plan.width - origin_x))
        length = min(size_length, max(1, placement_plan.length - origin_z))
        blockouts.append(
            SettlementBlockout(
                id=f"{site.id}-{blockout_kind}",
                kind=blockout_kind,
                region_title=site.region_title,
                site_id=site.id,
                site_kind=site.kind,
                x=origin_x,
                z=origin_z,
                width=width,
                length=length,
                access_roads=tuple(sorted(roads_by_site.get(site.id, ()))),
            )
        )

    return SettlementPlan(width=placement_plan.width, length=placement_plan.length, blockouts=tuple(blockouts))


def write_settlement_plan(placement_plan: PlacementPlan, road_plan: RoadPlan, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plan = build_settlement_plan(placement_plan, road_plan)
    output_path.write_text(json.dumps(settlement_plan_to_dict(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def render_settlement_preview(
    settlement_plan: SettlementPlan,
    output_path: Path,
    *,
    raster_width: int,
    raster_length: int,
    blocks_per_pixel: int,
) -> Path:
    pixels = [[SETTLEMENT_PREVIEW_BACKGROUND for _x in range(raster_width)] for _z in range(raster_length)]

    for blockout in settlement_plan.blockouts:
        start_x = min(raster_width - 1, max(0, blockout.x // blocks_per_pixel))
        start_z = min(raster_length - 1, max(0, blockout.z // blocks_per_pixel))
        end_x = min(raster_width - 1, max(start_x, (blockout.x + blockout.width - 1) // blocks_per_pixel))
        end_z = min(raster_length - 1, max(start_z, (blockout.z + blockout.length - 1) // blocks_per_pixel))
        color = _preview_color(blockout.kind)
        for raster_z in range(start_z, end_z + 1):
            for raster_x in range(start_x, end_x + 1):
                pixels[raster_z][raster_x] = color

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(output_path, raster_width, raster_length, tuple(tuple(row) for row in pixels))
    return output_path


def settlement_plan_to_dict(plan: SettlementPlan) -> dict[str, Any]:
    return {
        "schema": SETTLEMENT_PLAN_SCHEMA,
        "version": SETTLEMENT_PLAN_VERSION,
        "world": {
            "width": plan.width,
            "length": plan.length,
        },
        "blockouts": [
            {
                "id": blockout.id,
                "kind": blockout.kind,
                "region": blockout.region_title,
                "site": {
                    "id": blockout.site_id,
                    "kind": blockout.site_kind,
                },
                "origin": {
                    "x": blockout.x,
                    "z": blockout.z,
                },
                "size": {
                    "width": blockout.width,
                    "length": blockout.length,
                },
                "accessRoads": list(blockout.access_roads),
            }
            for blockout in plan.blockouts
        ],
    }


def _roads_by_site(road_plan: RoadPlan) -> dict[str, set[str]]:
    roads_by_site: dict[str, set[str]] = {}

    for road in road_plan.roads:
        roads_by_site.setdefault(road.from_point.site_id, set()).add(road.id)
        roads_by_site.setdefault(road.to_point.site_id, set()).add(road.id)

    return roads_by_site


def _blockout_kind(site: PlacementSite) -> str | None:
    if site.kind in {"entry-plaza", "approach-gate", "trail-gate"}:
        return "gate"
    if site.kind == "settlement-heart":
        return "core"
    if site.kind == "dock-edge":
        return "harbor"
    if site.kind == "route-junction":
        return "junction"
    return None


def _blockout_size(kind: str) -> tuple[int, int]:
    if kind == "core":
        return (32, 28)
    if kind == "harbor":
        return (22, 16)
    if kind == "junction":
        return (14, 14)
    return (18, 18)


def _preview_color(kind: str) -> tuple[int, int, int, int]:
    if kind == "gate":
        return SETTLEMENT_PREVIEW_GATE
    if kind == "harbor":
        return SETTLEMENT_PREVIEW_HARBOR
    return SETTLEMENT_PREVIEW_BLOCKOUT
