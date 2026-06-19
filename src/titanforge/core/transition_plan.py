from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from titanforge.core.world_plan import WorldPlan, WorldPlanAnchor, WorldPlanRegion
from titanforge.masks.png import write_rgba_png


TRANSITION_PLAN_SCHEMA = "titanforge.transition-plan"
TRANSITION_PLAN_VERSION = 1
TRANSITION_PREVIEW_BACKGROUND = (240, 236, 226, 255)
TRANSITION_PREVIEW_COAST = (86, 129, 166, 255)
TRANSITION_PREVIEW_TREE = (97, 124, 84, 255)
TRANSITION_PREVIEW_SETTLED = (160, 116, 79, 255)
TRANSITION_PREVIEW_SOFT = (171, 153, 133, 255)
TRANSITION_PREVIEW_LINE = (67, 60, 52, 255)

_ZONE_KEYWORDS = (
    ("port", ("port", "harbor", "dock")),
    ("mountain", ("mountain", "mountains", "ridge", "peak", "cliff", "highland")),
    ("forest", ("forest", "woods", "pine", "jungle", "grove")),
    ("road", ("road", "path", "bridge", "route")),
    ("city", ("city", "town", "village", "settlement", "ruins", "fort", "castle")),
    ("beach", ("beach", "dune", "sand")),
    ("water", ("sea", "ocean", "water", "bay", "coast", "shore", "lake", "river")),
    ("land", ("land", "field", "farm", "plains", "meadow", "valley")),
)


@dataclass(frozen=True)
class TransitionPoint:
    region_title: str
    anchor_id: str
    x: int
    z: int


@dataclass(frozen=True)
class TransitionSpan:
    id: str
    kind: str
    from_point: TransitionPoint
    to_point: TransitionPoint
    x: int
    z: int
    width: int
    length: int


@dataclass(frozen=True)
class TransitionPlan:
    width: int
    length: int
    transitions: tuple[TransitionSpan, ...]


def build_transition_plan(world_plan: WorldPlan) -> TransitionPlan:
    transitions: list[TransitionSpan] = []

    for index in range(len(world_plan.regions) - 1):
        current = world_plan.regions[index]
        nxt = world_plan.regions[index + 1]
        from_anchor = current.anchors[-1]
        to_anchor = nxt.anchors[0]
        span_width = min(
            max(24, min(current.width, nxt.width) // 6),
            max(24, world_plan.width // 4),
        )
        span_length = min(
            world_plan.length,
            max(world_plan.length // 3, abs(from_anchor.z - to_anchor.z) + 48),
        )
        center_x = nxt.x
        center_z = (from_anchor.z + to_anchor.z) // 2
        origin_x = min(max(0, center_x - span_width // 2), max(0, world_plan.width - span_width))
        origin_z = min(max(0, center_z - span_length // 2), max(0, world_plan.length - span_length))

        transitions.append(
            TransitionSpan(
                id=f"transition-zone-{index:02d}",
                kind=_transition_kind(current, nxt),
                from_point=_transition_point(current, from_anchor),
                to_point=_transition_point(nxt, to_anchor),
                x=origin_x,
                z=origin_z,
                width=span_width,
                length=span_length,
            )
        )

    return TransitionPlan(width=world_plan.width, length=world_plan.length, transitions=tuple(transitions))


def write_transition_plan(world_plan: WorldPlan, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plan = build_transition_plan(world_plan)
    output_path.write_text(json.dumps(transition_plan_to_dict(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def render_transition_preview(
    transition_plan: TransitionPlan,
    output_path: Path,
    *,
    raster_width: int,
    raster_length: int,
    blocks_per_pixel: int,
) -> Path:
    pixels = [[TRANSITION_PREVIEW_BACKGROUND for _x in range(raster_width)] for _z in range(raster_length)]

    for transition in transition_plan.transitions:
        start_x = min(raster_width - 1, max(0, transition.x // blocks_per_pixel))
        start_z = min(raster_length - 1, max(0, transition.z // blocks_per_pixel))
        end_x = min(raster_width - 1, max(start_x, (transition.x + transition.width - 1) // blocks_per_pixel))
        end_z = min(raster_length - 1, max(start_z, (transition.z + transition.length - 1) // blocks_per_pixel))
        color = _preview_color(transition.kind)

        for raster_z in range(start_z, end_z + 1):
            for raster_x in range(start_x, end_x + 1):
                pixels[raster_z][raster_x] = color

        from_x = min(raster_width - 1, max(0, transition.from_point.x // blocks_per_pixel))
        from_z = min(raster_length - 1, max(0, transition.from_point.z // blocks_per_pixel))
        to_x = min(raster_width - 1, max(0, transition.to_point.x // blocks_per_pixel))
        to_z = min(raster_length - 1, max(0, transition.to_point.z // blocks_per_pixel))
        for raster_x, raster_z in _bresenham(from_x, from_z, to_x, to_z):
            pixels[raster_z][raster_x] = TRANSITION_PREVIEW_LINE

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rgba_png(output_path, raster_width, raster_length, tuple(tuple(row) for row in pixels))
    return output_path


def transition_plan_to_dict(plan: TransitionPlan) -> dict[str, Any]:
    return {
        "schema": TRANSITION_PLAN_SCHEMA,
        "version": TRANSITION_PLAN_VERSION,
        "world": {
            "width": plan.width,
            "length": plan.length,
        },
        "transitions": [
            {
                "id": transition.id,
                "kind": transition.kind,
                "from": {
                    "region": transition.from_point.region_title,
                    "anchor": transition.from_point.anchor_id,
                    "point": {"x": transition.from_point.x, "z": transition.from_point.z},
                },
                "to": {
                    "region": transition.to_point.region_title,
                    "anchor": transition.to_point.anchor_id,
                    "point": {"x": transition.to_point.x, "z": transition.to_point.z},
                },
                "bounds": {
                    "x": transition.x,
                    "z": transition.z,
                    "width": transition.width,
                    "length": transition.length,
                },
            }
            for transition in plan.transitions
        ],
    }


def _transition_point(region: WorldPlanRegion, anchor: WorldPlanAnchor) -> TransitionPoint:
    return TransitionPoint(region_title=region.title, anchor_id=anchor.id, x=anchor.x, z=anchor.z)


def _transition_kind(current: WorldPlanRegion, nxt: WorldPlanRegion) -> str:
    current_zone = _zone_family(current)
    next_zone = _zone_family(nxt)
    pair = {current_zone, next_zone}

    if "water" in pair and len(pair) > 1:
        return "coast-transition"
    if pair == {"forest", "mountain"}:
        return "treeline-rise"
    if "city" in pair or "port" in pair:
        return "settled-edge"
    return "soft-boundary"


def _zone_family(region: WorldPlanRegion) -> str:
    text = " ".join((region.kind, region.title, region.story_role, region.notes)).lower()
    tokens = set(re.findall(r"[a-z]+", text))
    for zone_id, keywords in _ZONE_KEYWORDS:
        if any(keyword in tokens for keyword in keywords):
            return zone_id
    return "land"


def _preview_color(kind: str) -> tuple[int, int, int, int]:
    if kind == "coast-transition":
        return TRANSITION_PREVIEW_COAST
    if kind == "treeline-rise":
        return TRANSITION_PREVIEW_TREE
    if kind == "settled-edge":
        return TRANSITION_PREVIEW_SETTLED
    return TRANSITION_PREVIEW_SOFT


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
