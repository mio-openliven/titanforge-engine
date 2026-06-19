from __future__ import annotations

from dataclasses import dataclass
import json
from math import ceil
from pathlib import Path
from typing import Any

from titanforge.core.world_plan import WorldPlan, WorldPlanAnchor
from titanforge.masks.png import write_rgba_png


ROUTE_PLAN_SCHEMA = "titanforge.route-plan"
ROUTE_PLAN_VERSION = 1
ROUTE_PREVIEW_BACKGROUND = (243, 236, 221, 255)
ROUTE_PREVIEW_LINE = (93, 54, 25, 255)
ROUTE_PREVIEW_POINT = (201, 92, 36, 255)


@dataclass(frozen=True)
class RouteEndpoint:
    region_title: str
    anchor_id: str
    x: int
    z: int


@dataclass(frozen=True)
class RouteSegment:
    id: str
    kind: str
    from_point: RouteEndpoint
    to_point: RouteEndpoint


@dataclass(frozen=True)
class RoutePlan:
    width: int
    length: int
    routes: tuple[RouteSegment, ...]


def build_route_plan(world_plan: WorldPlan) -> RoutePlan:
    routes: list[RouteSegment] = []

    for index, region in enumerate(world_plan.regions):
        if len(region.anchors) >= 2:
            routes.append(
                RouteSegment(
                    id=f"region-{index:02d}",
                    kind="intra-region",
                    from_point=_endpoint(region.title, region.anchors[0]),
                    to_point=_endpoint(region.title, region.anchors[-1]),
                )
            )

    for index in range(len(world_plan.regions) - 1):
        current = world_plan.regions[index]
        nxt = world_plan.regions[index + 1]
        routes.append(
            RouteSegment(
                id=f"transition-{index:02d}",
                kind="transition",
                from_point=_endpoint(current.title, current.anchors[-1]),
                to_point=_endpoint(nxt.title, nxt.anchors[0]),
            )
        )

    return RoutePlan(width=world_plan.width, length=world_plan.length, routes=tuple(routes))


def write_route_plan(world_plan: WorldPlan, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(route_plan_to_dict(build_route_plan(world_plan)), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def render_route_preview(
    route_plan: RoutePlan,
    output_path: Path,
    *,
    raster_width: int,
    raster_length: int,
    blocks_per_pixel: int,
) -> Path:
    pixels = [[ROUTE_PREVIEW_BACKGROUND for _x in range(raster_width)] for _z in range(raster_length)]

    for route in route_plan.routes:
        from_x = min(raster_width - 1, max(0, route.from_point.x // blocks_per_pixel))
        from_z = min(raster_length - 1, max(0, route.from_point.z // blocks_per_pixel))
        to_x = min(raster_width - 1, max(0, route.to_point.x // blocks_per_pixel))
        to_z = min(raster_length - 1, max(0, route.to_point.z // blocks_per_pixel))

        for x, z in _bresenham(from_x, from_z, to_x, to_z):
            pixels[z][x] = ROUTE_PREVIEW_LINE
        _mark_point(pixels, from_x, from_z)
        _mark_point(pixels, to_x, to_z)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(output_path, raster_width, raster_length, tuple(tuple(row) for row in pixels))
    return output_path


def route_plan_to_dict(plan: RoutePlan) -> dict[str, Any]:
    return {
        "schema": ROUTE_PLAN_SCHEMA,
        "version": ROUTE_PLAN_VERSION,
        "world": {
            "width": plan.width,
            "length": plan.length,
        },
        "routes": [
            {
                "id": route.id,
                "kind": route.kind,
                "from": {
                    "region": route.from_point.region_title,
                    "anchor": route.from_point.anchor_id,
                    "point": {"x": route.from_point.x, "z": route.from_point.z},
                },
                "to": {
                    "region": route.to_point.region_title,
                    "anchor": route.to_point.anchor_id,
                    "point": {"x": route.to_point.x, "z": route.to_point.z},
                },
            }
            for route in plan.routes
        ],
    }


def _endpoint(region_title: str, anchor: WorldPlanAnchor) -> RouteEndpoint:
    return RouteEndpoint(region_title=region_title, anchor_id=anchor.id, x=anchor.x, z=anchor.z)


def _mark_point(
    pixels: list[list[tuple[int, int, int, int]]],
    x: int,
    z: int,
) -> None:
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    for offset_z in (-1, 0, 1):
        for offset_x in (-1, 0, 1):
            nx = x + offset_x
            nz = z + offset_z
            if 0 <= nx < width and 0 <= nz < height:
                pixels[nz][nx] = ROUTE_PREVIEW_POINT


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
