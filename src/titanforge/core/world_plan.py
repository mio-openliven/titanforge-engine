from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from titanforge.core.project import ProjectConfig, ProjectRegion


WORLD_PLAN_SCHEMA = "titanforge.world-plan"
WORLD_PLAN_VERSION = 1


@dataclass(frozen=True)
class WorldPlanRegion:
    title: str
    kind: str
    story_role: str
    mood: str
    notes: str
    coverage_percent: float
    x: int
    z: int
    width: int
    length: int


@dataclass(frozen=True)
class WorldPlan:
    name: str
    target_version: str
    width: int
    length: int
    premise: str
    player_experience: str
    regions: tuple[WorldPlanRegion, ...]


def build_world_plan(config: ProjectConfig) -> WorldPlan:
    if not config.regions:
        return WorldPlan(
            name=config.name,
            target_version=config.target_version,
            width=config.width,
            length=config.length,
            premise=config.premise,
            player_experience=config.player_experience,
            regions=(),
        )

    requested = [_parse_coverage_percent(region.coverage_hint) for region in config.regions]
    total_requested = sum(requested)
    if total_requested <= 0:
        requested = [100.0 / len(config.regions)] * len(config.regions)
        total_requested = 100.0

    widths: list[int] = []
    consumed = 0
    for index, requested_percent in enumerate(requested):
        if index == len(requested) - 1:
            region_width = config.width - consumed
        else:
            share = requested_percent / total_requested
            region_width = max(1, round(config.width * share))
            remaining_slots = len(config.regions) - index - 1
            max_width_here = config.width - consumed - remaining_slots
            region_width = min(region_width, max_width_here)

        widths.append(region_width)
        consumed += region_width

    regions: list[WorldPlanRegion] = []
    cursor_x = 0
    for region, requested_percent, region_width in zip(config.regions, requested, widths):
        regions.append(
            WorldPlanRegion(
                title=region.title,
                kind=region.kind,
                story_role=region.story_role,
                mood=region.mood,
                notes=region.notes,
                coverage_percent=round(requested_percent, 2),
                x=cursor_x,
                z=0,
                width=region_width,
                length=config.length,
            )
        )
        cursor_x += region_width

    return WorldPlan(
        name=config.name,
        target_version=config.target_version,
        width=config.width,
        length=config.length,
        premise=config.premise,
        player_experience=config.player_experience,
        regions=tuple(regions),
    )


def write_world_plan(config: ProjectConfig, output_path: Path) -> Path:
    plan = build_world_plan(config)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(world_plan_to_dict(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def world_plan_to_dict(plan: WorldPlan) -> dict[str, object]:
    return {
        "schema": WORLD_PLAN_SCHEMA,
        "version": WORLD_PLAN_VERSION,
        "project": {
            "name": plan.name,
            "targetVersion": plan.target_version,
        },
        "world": {
            "width": plan.width,
            "length": plan.length,
        },
        "creative": {
            "premise": plan.premise,
            "playerExperience": plan.player_experience,
        },
        "regions": [
            {
                "title": region.title,
                "kind": region.kind,
                "storyRole": region.story_role,
                "mood": region.mood,
                "notes": region.notes,
                "coveragePercent": region.coverage_percent,
                "bounds": {
                    "x": region.x,
                    "z": region.z,
                    "width": region.width,
                    "length": region.length,
                },
            }
            for region in plan.regions
        ],
    }


def format_world_plan(plan: WorldPlan, output_path: Path | None = None) -> str:
    lines = [
        f"WorldPlan: {plan.name}",
        f"Target: {plan.target_version}",
        f"World size: {plan.width} x {plan.length}",
    ]
    if output_path is not None:
        lines.append(f"Output: {output_path}")
    if plan.regions:
        lines.append("Regions:")
        for region in plan.regions:
            lines.append(
                f"- {region.title} [{region.kind}] "
                f"x={region.x} z={region.z} width={region.width} length={region.length} "
                f"coverage={region.coverage_percent}%"
            )
    else:
        lines.append("Regions: <none>")
    return "\n".join(lines)


def _parse_coverage_percent(value: str) -> float:
    cleaned = value.strip().replace("%", "")
    try:
        return max(0.0, float(cleaned))
    except ValueError:
        return 0.0
