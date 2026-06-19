from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from titanforge.core.placement_plan import PlacementPlan, PlacementSite
from titanforge.core.route_plan import RoutePlan, RouteSegment
from titanforge.masks.png import write_rgba_png


ROAD_PLAN_SCHEMA = "titanforge.road-plan"
ROAD_PLAN_VERSION = 1
ROAD_PREVIEW_BACKGROUND = (233, 227, 214, 255)
ROAD_PREVIEW_LINE = (88, 82, 74, 255)
ROAD_PREVIEW_HUB = (173, 104, 56, 255)


@dataclass(frozen=True)
class RoadEndpoint:
    site_id: str
    kind: str
    x: int
    z: int


@dataclass(frozen=True)
class RoadSegment:
    id: str
    kind: str
    width_hint: str
    from_point: RoadEndpoint
    to_point: RoadEndpoint


@dataclass(frozen=True)
class RoadPlan:
    width: int
    length: int
    roads: tuple[RoadSegment, ...]


def build_road_plan(route_plan: RoutePlan, placement_plan: PlacementPlan) -> RoadPlan:
    sites_by_position = {(site.x, site.z): site for site in placement_plan.sites}
    roads: list[RoadSegment] = []

    for route in route_plan.routes:
        from_site = _site_for_point(sites_by_position, route.from_point.x, route.from_point.z, route.from_point.anchor_id)
        to_site = _site_for_point(sites_by_position, route.to_point.x, route.to_point.z, route.to_point.anchor_id)
        roads.append(
            RoadSegment(
                id=route.id,
                kind=_road_kind(route),
                width_hint=_width_hint(route),
                from_point=RoadEndpoint(site_id=from_site.id, kind=from_site.kind, x=from_site.x, z=from_site.z),
                to_point=RoadEndpoint(site_id=to_site.id, kind=to_site.kind, x=to_site.x, z=to_site.z),
            )
        )

    return RoadPlan(width=route_plan.width, length=route_plan.length, roads=tuple(roads))


def write_road_plan(route_plan: RoutePlan, placement_plan: PlacementPlan, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plan = build_road_plan(route_plan, placement_plan)
    output_path.write_text(json.dumps(road_plan_to_dict(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def render_road_preview(
    road_plan: RoadPlan,
    placement_plan: PlacementPlan,
    output_path: Path,
    *,
    raster_width: int,
    raster_length: int,
    blocks_per_pixel: int,
) -> Path:
    pixels = [[ROAD_PREVIEW_BACKGROUND for _x in range(raster_width)] for _z in range(raster_length)]

    for road in road_plan.roads:
        from_x = min(raster_width - 1, max(0, road.from_point.x // blocks_per_pixel))
        from_z = min(raster_length - 1, max(0, road.from_point.z // blocks_per_pixel))
        to_x = min(raster_width - 1, max(0, road.to_point.x // blocks_per_pixel))
        to_z = min(raster_length - 1, max(0, road.to_point.z // blocks_per_pixel))
        radius = 1 if road.width_hint == "narrow" else 2
        for x, z in _bresenham(from_x, from_z, to_x, to_z):
            _paint_radius(pixels, x, z, ROAD_PREVIEW_LINE, radius)

    for site in placement_plan.sites:
        x = min(raster_width - 1, max(0, site.x // blocks_per_pixel))
        z = min(raster_length - 1, max(0, site.z // blocks_per_pixel))
        _paint_radius(pixels, x, z, ROAD_PREVIEW_HUB, 1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(output_path, raster_width, raster_length, tuple(tuple(row) for row in pixels))
    return output_path


def road_plan_to_dict(plan: RoadPlan) -> dict[str, Any]:
    return {
        "schema": ROAD_PLAN_SCHEMA,
        "version": ROAD_PLAN_VERSION,
        "world": {
            "width": plan.width,
            "length": plan.length,
        },
        "roads": [
            {
                "id": road.id,
                "kind": road.kind,
                "widthHint": road.width_hint,
                "from": {
                    "site": road.from_point.site_id,
                    "kind": road.from_point.kind,
                    "point": {"x": road.from_point.x, "z": road.from_point.z},
                },
                "to": {
                    "site": road.to_point.site_id,
                    "kind": road.to_point.kind,
                    "point": {"x": road.to_point.x, "z": road.to_point.z},
                },
            }
            for road in plan.roads
        ],
    }


def _site_for_point(
    sites_by_position: dict[tuple[int, int], PlacementSite],
    x: int,
    z: int,
    fallback_id: str,
) -> PlacementSite:
    return sites_by_position.get(
        (x, z),
        PlacementSite(id=fallback_id, kind="story-focus", region_title="unknown", source="route", x=x, z=z),
    )


def _road_kind(route: RouteSegment) -> str:
    if route.kind == "transition":
        return "main-road"
    return "local-path"


def _width_hint(route: RouteSegment) -> str:
    if route.kind == "transition":
        return "wide"
    return "narrow"


def _paint_radius(
    pixels: list[list[tuple[int, int, int, int]]],
    x: int,
    z: int,
    color: tuple[int, int, int, int],
    radius: int,
) -> None:
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    for offset_z in range(-radius, radius + 1):
        for offset_x in range(-radius, radius + 1):
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
