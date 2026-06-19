from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from titanforge.core.route_plan import RoutePlan, RouteSegment
from titanforge.core.world_plan import WorldPlan, WorldPlanAnchor, WorldPlanRegion
from titanforge.masks.png import write_rgba_png


PLACEMENT_PLAN_SCHEMA = "titanforge.placement-plan"
PLACEMENT_PLAN_VERSION = 1
PLACEMENT_PREVIEW_BACKGROUND = (239, 233, 220, 255)
PLACEMENT_PREVIEW_ROUTE = (157, 137, 117, 255)
PLACEMENT_PREVIEW_SITE = (184, 82, 52, 255)
PLACEMENT_PREVIEW_JUNCTION = (55, 92, 122, 255)


@dataclass(frozen=True)
class PlacementSite:
    id: str
    kind: str
    region_title: str
    source: str
    x: int
    z: int


@dataclass(frozen=True)
class PlacementPlan:
    width: int
    length: int
    sites: tuple[PlacementSite, ...]


def build_placement_plan(world_plan: WorldPlan, route_plan: RoutePlan) -> PlacementPlan:
    sites: list[PlacementSite] = []

    for region in world_plan.regions:
        for anchor in region.anchors:
            sites.append(_site_from_anchor(region, anchor))

    for route in route_plan.routes:
        if route.kind == "transition":
            sites.append(_site_from_route(route))

    return PlacementPlan(width=world_plan.width, length=world_plan.length, sites=tuple(sites))


def write_placement_plan(world_plan: WorldPlan, route_plan: RoutePlan, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plan = build_placement_plan(world_plan, route_plan)
    output_path.write_text(json.dumps(placement_plan_to_dict(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def render_placement_preview(
    route_plan: RoutePlan,
    placement_plan: PlacementPlan,
    output_path: Path,
    *,
    raster_width: int,
    raster_length: int,
    blocks_per_pixel: int,
) -> Path:
    pixels = [[PLACEMENT_PREVIEW_BACKGROUND for _x in range(raster_width)] for _z in range(raster_length)]

    for route in route_plan.routes:
        from_x = min(raster_width - 1, max(0, route.from_point.x // blocks_per_pixel))
        from_z = min(raster_length - 1, max(0, route.from_point.z // blocks_per_pixel))
        to_x = min(raster_width - 1, max(0, route.to_point.x // blocks_per_pixel))
        to_z = min(raster_length - 1, max(0, route.to_point.z // blocks_per_pixel))
        for x, z in _bresenham(from_x, from_z, to_x, to_z):
            pixels[z][x] = PLACEMENT_PREVIEW_ROUTE

    for site in placement_plan.sites:
        x = min(raster_width - 1, max(0, site.x // blocks_per_pixel))
        z = min(raster_length - 1, max(0, site.z // blocks_per_pixel))
        color = PLACEMENT_PREVIEW_JUNCTION if site.source == "route" else PLACEMENT_PREVIEW_SITE
        _mark_site(pixels, x, z, color)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(output_path, raster_width, raster_length, tuple(tuple(row) for row in pixels))
    return output_path


def placement_plan_to_dict(plan: PlacementPlan) -> dict[str, Any]:
    return {
        "schema": PLACEMENT_PLAN_SCHEMA,
        "version": PLACEMENT_PLAN_VERSION,
        "world": {
            "width": plan.width,
            "length": plan.length,
        },
        "sites": [
            {
                "id": site.id,
                "kind": site.kind,
                "region": site.region_title,
                "source": site.source,
                "point": {"x": site.x, "z": site.z},
            }
            for site in plan.sites
        ],
    }


def _site_from_anchor(region: WorldPlanRegion, anchor: WorldPlanAnchor) -> PlacementSite:
    kind_by_anchor = {
        "arrival": "entry-plaza",
        "center": "settlement-heart",
        "shoreline": "dock-edge",
        "far-water": "vista-point",
        "forest-core": "mystery-cluster",
        "forest-edge": "trail-gate",
        "ridge-vista": "overlook",
        "approach": "approach-gate",
        "entry": "entry-plaza",
        "focus": "story-focus",
    }
    kind = kind_by_anchor.get(anchor.id, "story-focus")
    return PlacementSite(
        id=f"{region.title.lower().replace(' ', '-')}-{anchor.id}",
        kind=kind,
        region_title=region.title,
        source="anchor",
        x=anchor.x,
        z=anchor.z,
    )


def _site_from_route(route: RouteSegment) -> PlacementSite:
    midpoint_x = (route.from_point.x + route.to_point.x) // 2
    midpoint_z = (route.from_point.z + route.to_point.z) // 2
    return PlacementSite(
        id=f"{route.id}-junction",
        kind="route-junction",
        region_title=f"{route.from_point.region_title} -> {route.to_point.region_title}",
        source="route",
        x=midpoint_x,
        z=midpoint_z,
    )


def _mark_site(
    pixels: list[list[tuple[int, int, int, int]]],
    x: int,
    z: int,
    color: tuple[int, int, int, int],
) -> None:
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    for offset_z in (-1, 0, 1):
        for offset_x in (-1, 0, 1):
            nx = x + offset_x
            nz = z + offset_z
            if 0 <= nx < width and 0 <= nz < height:
                pixels[nz][nx] = color


def _bresenham(x0: int, y0: int, x1: int, y1: int) -> tuple[tuple[int, int], ...]:
    points: list[tuple[int, int]] = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x = x0
    y = y0

    while True:
        points.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy

    return tuple(points)
